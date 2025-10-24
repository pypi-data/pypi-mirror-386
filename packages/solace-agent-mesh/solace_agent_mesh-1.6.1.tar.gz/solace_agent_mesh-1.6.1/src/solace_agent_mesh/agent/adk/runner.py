"""
Manages the asynchronous execution of the ADK Runner.
"""

import logging
import asyncio

from google.adk.agents.invocation_context import LlmCallsLimitExceededError
from litellm.exceptions import BadRequestError


class TaskCancelledError(Exception):
    """Raised when an ADK task is cancelled via external signal."""

    pass


from typing import TYPE_CHECKING, Any

from google.adk.agents import RunConfig
from google.adk.events import Event as ADKEvent
from google.adk.events.event_actions import EventActions
from google.adk.sessions import Session as ADKSession
from google.genai import types as adk_types

from ...common import a2a

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..sac.component import SamAgentComponent
    from ..sac.task_execution_context import TaskExecutionContext


async def run_adk_async_task_thread_wrapper(
    component: "SamAgentComponent",
    adk_session: ADKSession,
    adk_content: adk_types.Content,
    run_config: RunConfig,
    a2a_context: dict[str, Any],
):
    """
    Wrapper to run the async ADK task.
    Calls component finalization methods upon completion or error.

    Args:
        component: The SamAgentComponent instance.
        adk_session: The ADK session to use (from component.session_service).
        adk_content: The input content for the ADK agent.
        run_config: The ADK run configuration.
        a2a_context: The context dictionary for this specific A2A request.
    """
    logical_task_id = a2a_context.get("logical_task_id", "unknown_task")
    is_paused = False
    exception_to_finalize_with = None
    task_context = None
    try:
        with component.active_tasks_lock:
            task_context = component.active_tasks.get(logical_task_id)

        if not task_context:
            log.error(
                "%s TaskExecutionContext not found for task %s. Cannot start ADK runner.",
                component.log_identifier,
                logical_task_id,
            )
            return

        task_context.flush_streaming_buffer()
        log.debug(
            "%s Cleared streaming text buffer before starting ADK task %s.",
            component.log_identifier,
            logical_task_id,
        )

        if adk_session and component.session_service:
            context_setting_invocation_id = logical_task_id
            original_message = a2a_context.pop("original_solace_message", None)
            try:
                context_setting_event = ADKEvent(
                    invocation_id=context_setting_invocation_id,
                    author="A2A_Host_System",
                    content=adk_types.Content(
                        parts=[
                            adk_types.Part(
                                text="Initializing A2A context for task run."
                            )
                        ]
                    ),
                    actions=EventActions(state_delta={"a2a_context": a2a_context}),
                    branch=None,
                )
                await component.session_service.append_event(
                    session=adk_session, event=context_setting_event
                )
                log.debug(
                    "%s Appended context-setting event to ADK session %s (via component.session_service) for task %s.",
                    component.log_identifier,
                    adk_session.id,
                    logical_task_id,
                )
            except Exception as e_append:
                log.error(
                    "%s Failed to append context-setting event for task %s: %s.",
                    component.log_identifier,
                    logical_task_id,
                    e_append,
                    exc_info=True,
                )
            finally:
                if original_message:
                    a2a_context["original_solace_message"] = original_message
        else:
            log.warning(
                "%s Could not inject a2a_context into ADK session state via event for task %s (session or session_service invalid). Tool scope filtering might not work.",
                component.log_identifier,
                logical_task_id,
            )

        is_paused = await run_adk_async_task(
            component,
            task_context,
            adk_session,
            adk_content,
            run_config,
            a2a_context,
        )

        log.debug(
            "%s ADK task %s awaited and completed (Paused: %s).",
            component.log_identifier,
            logical_task_id,
            is_paused,
        )

    except TaskCancelledError as tce:
        exception_to_finalize_with = tce
        log.info(
            "%s Task %s was cancelled. Propagating to peers before scheduling finalization. Message: %s",
            component.log_identifier,
            logical_task_id,
            tce,
        )
        sub_tasks_to_cancel = task_context.active_peer_sub_tasks if task_context else {}

        if sub_tasks_to_cancel:
            log.info(
                "%s Propagating cancellation to %d peer sub-task(s) for main task %s.",
                component.log_identifier,
                len(sub_tasks_to_cancel),
                logical_task_id,
            )
            for sub_task_id, sub_task_info in sub_tasks_to_cancel.items():
                try:
                    target_peer_agent_name = sub_task_info.get("peer_agent_name")
                    if not sub_task_id or not target_peer_agent_name:
                        log.warning(
                            "%s Incomplete sub-task info found for sub-task %s, cannot cancel: %s",
                            component.log_identifier,
                            sub_task_id,
                            sub_task_info,
                        )
                        continue

                    task_id_for_peer = sub_task_id.replace(
                        component.CORRELATION_DATA_PREFIX, "", 1
                    )
                    peer_cancel_request = a2a.create_cancel_task_request(
                        task_id=task_id_for_peer
                    )
                    peer_cancel_user_props = {"clientId": component.agent_name}
                    peer_request_topic = component._get_agent_request_topic(
                        target_peer_agent_name
                    )
                    component.publish_a2a_message(
                        payload=peer_cancel_request.model_dump(exclude_none=True),
                        topic=peer_request_topic,
                        user_properties=peer_cancel_user_props,
                    )
                except Exception as e_peer_cancel:
                    log.error(
                        "%s Failed to send CancelTaskRequest for sub-task %s: %s",
                        component.log_identifier,
                        sub_task_id,
                        e_peer_cancel,
                        exc_info=True,
                    )
    except LlmCallsLimitExceededError as llm_limit_e:
        exception_to_finalize_with = llm_limit_e
        log.warning(
            "%s LLM call limit exceeded for task %s: %s. Scheduling finalization.",
            component.log_identifier,
            logical_task_id,
            llm_limit_e,
        )
    except BadRequestError as e:
        log.error(
            "%s Bad Request for task %s: %s.",
            component.log_identifier,
            logical_task_id,
            e.message
        )
        raise
    except Exception as e:
        exception_to_finalize_with = e
        log.exception(
            "%s Exception in ADK runner for task %s: %s. Scheduling finalization.",
            component.log_identifier,
            logical_task_id,
            e,
        )

    loop = component.get_async_loop()
    if loop and loop.is_running():
        log.debug(
            "%s Scheduling finalize_task_with_cleanup for task %s.",
            component.log_identifier,
            logical_task_id,
        )
        asyncio.run_coroutine_threadsafe(
            component.finalize_task_with_cleanup(
                a2a_context, is_paused, exception_to_finalize_with
            ),
            loop,
        )
    else:
        log.error(
            "%s Async loop not available. Cannot schedule finalization for task %s.",
            component.log_identifier,
            logical_task_id,
        )

        log.debug(
            "%s ADK runner for task %s finished.",
            component.log_identifier,
            logical_task_id,
        )


async def run_adk_async_task(
    component: "SamAgentComponent",
    task_context: "TaskExecutionContext",
    adk_session: ADKSession,
    adk_content: adk_types.Content,
    run_config: RunConfig,
    a2a_context: dict[str, Any],
) -> bool:
    """
    Runs the ADK Runner asynchronously and calls component methods to process
    intermediate events and finalize the task.
    Returns:
        bool: True if the task is paused for a long-running tool, False otherwise.
    """
    logical_task_id = a2a_context.get("logical_task_id", "unknown_task")
    event_loop_stored = False
    current_loop = asyncio.get_running_loop()
    is_paused = False

    adk_event_generator = component.runner.run_async(
        user_id=adk_session.user_id,
        session_id=adk_session.id,
        new_message=adk_content,
        run_config=run_config,
    )

    try:
        while True:
            next_event_task = asyncio.create_task(adk_event_generator.__anext__())
            cancel_wait_task = asyncio.create_task(
                task_context.cancellation_event.wait()
            )

            done, pending = await asyncio.wait(
                {next_event_task, cancel_wait_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            if cancel_wait_task in done:
                next_event_task.cancel()
                try:
                    await next_event_task
                except asyncio.CancelledError:
                    log.debug(
                        "%s Suppressed CancelledError for next_event_task after signal.",
                        component.log_identifier,
                    )
                log.info(
                    "%s Task %s cancellation detected while awaiting ADK event.",
                    component.log_identifier,
                    logical_task_id,
                )
                raise TaskCancelledError(
                    f"Task {logical_task_id} was cancelled by signal."
                )

            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    log.debug(
                        "%s Suppressed CancelledError for lingering task after event.",
                        component.log_identifier,
                    )

            try:
                event = await next_event_task
            except StopAsyncIteration:
                break

            if event.long_running_tool_ids:
                is_paused = True

            if not event_loop_stored and event.invocation_id:
                task_context.set_event_loop(current_loop)
                a2a_context["invocation_id"] = event.invocation_id
                event_loop_stored = True

            try:
                await component.process_and_publish_adk_event(event, a2a_context)
            except Exception as process_err:
                log.exception(
                    "%s Error processing intermediate ADK event %s for task %s: %s",
                    component.log_identifier,
                    event.id,
                    logical_task_id,
                    process_err,
                )

            if task_context.is_cancelled():
                raise TaskCancelledError(
                    f"Task {logical_task_id} was cancelled after processing ADK event {event.id}."
                )

            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.function_response:
                        if part.function_response.name.startswith("peer_"):
                            pass

    except TaskCancelledError:
        raise
    except BadRequestError as e:
        log.error(
            "%s Bad Request for task %s: %s.",
            component.log_identifier,
            logical_task_id,
            e.message
        )
        raise
    except Exception as e:
        log.exception(
            "%s Unexpected error in ADK runner loop for task %s: %s",
            component.log_identifier,
            logical_task_id,
            e,
        )
        raise

    if task_context.is_cancelled():
        log.info(
            "%s Task %s cancellation detected before finalization.",
            component.log_identifier,
            logical_task_id,
        )
        raise TaskCancelledError(
            f"Task {logical_task_id} was cancelled before finalization."
        )

    if is_paused:
        log.info(
            "%s ADK run completed by invoking a long-running tool. Task %s will remain open, awaiting peer response.",
            component.log_identifier,
            logical_task_id,
        )
        return True

    log.debug(
        "%s ADK run_async completed for task %s. Returning to wrapper for finalization.",
        component.log_identifier,
        logical_task_id,
    )
    return False
