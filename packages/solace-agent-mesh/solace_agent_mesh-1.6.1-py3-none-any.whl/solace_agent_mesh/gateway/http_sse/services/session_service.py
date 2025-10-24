import logging
import uuid
from typing import TYPE_CHECKING, Optional, List, Dict, Any

from sqlalchemy.orm import Session as DbSession

from ..repository import (
    ISessionRepository,
    Session,
)
from ..repository.chat_task_repository import ChatTaskRepository
from ..repository.entities import ChatTask
from ..shared.enums import SenderType
from ..shared.types import SessionId, UserId
from ..shared import now_epoch_ms
from ..shared.pagination import PaginationParams, PaginatedResponse, get_pagination_or_default

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..component import WebUIBackendComponent


class SessionService:
    def __init__(
        self,
        component: "WebUIBackendComponent" = None,
    ):
        self.component = component

    def _get_repositories(self, db: DbSession):
        """Create session repository for the given database session."""
        from ..repository import SessionRepository
        session_repository = SessionRepository()
        return session_repository

    def is_persistence_enabled(self) -> bool:
        """Checks if the service is configured with a persistent backend."""
        return self.component and self.component.database_url is not None

    def get_user_sessions(
        self,
        db: DbSession,
        user_id: UserId,
        pagination: PaginationParams | None = None
    ) -> PaginatedResponse[Session]:
        """
        Get paginated sessions for a user with full metadata.

        Uses default pagination if none provided (page 1, size 20).
        Returns paginated response with pageNumber, pageSize, nextPage, totalPages, totalCount.
        """
        if not user_id or user_id.strip() == "":
            raise ValueError("User ID cannot be empty")

        pagination = get_pagination_or_default(pagination)
        session_repository = self._get_repositories(db)

        # Pass pagination params directly - repository will handle offset calculation
        sessions = session_repository.find_by_user(db, user_id, pagination)
        total_count = session_repository.count_by_user(db, user_id)

        return PaginatedResponse.create(sessions, total_count, pagination)

    def get_session_details(
        self, db: DbSession, session_id: SessionId, user_id: UserId
    ) -> Session | None:
        if not self._is_valid_session_id(session_id):
            return None

        session_repository = self._get_repositories(db)
        return session_repository.find_user_session(db, session_id, user_id)

    def create_session(
        self,
        db: DbSession,
        user_id: UserId,
        name: str | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
    ) -> Optional[Session]:
        if not self.is_persistence_enabled():
            log.debug("Persistence is not enabled. Skipping session creation in DB.")
            return None

        if not user_id or user_id.strip() == "":
            raise ValueError("User ID cannot be empty")

        if not session_id:
            session_id = str(uuid.uuid4())

        now_ms = now_epoch_ms()
        session = Session(
            id=session_id,
            user_id=user_id,
            name=name,
            agent_id=agent_id,
            created_time=now_ms,
            updated_time=now_ms,
        )

        session_repository = self._get_repositories(db)
        created_session = session_repository.save(db, session)
        log.info("Created new session %s for user %s", created_session.id, user_id)

        if not created_session:
            raise ValueError(f"Failed to save session for {session_id}")

        return created_session

    def update_session_name(
        self, db: DbSession, session_id: SessionId, user_id: UserId, name: str
    ) -> Session | None:
        if not self._is_valid_session_id(session_id):
            raise ValueError("Invalid session ID")

        if not name or len(name.strip()) == 0:
            raise ValueError("Session name cannot be empty")

        if len(name.strip()) > 255:
            raise ValueError("Session name cannot exceed 255 characters")

        session_repository = self._get_repositories(db)
        session = session_repository.find_user_session(db, session_id, user_id)
        if not session:
            return None

        session.update_name(name)
        updated_session = session_repository.save(db, session)

        log.info("Updated session %s name to '%s'", session_id, name)
        return updated_session

    def delete_session_with_notifications(
        self, db: DbSession, session_id: SessionId, user_id: UserId
    ) -> bool:
        if not self._is_valid_session_id(session_id):
            raise ValueError("Invalid session ID")

        session_repository = self._get_repositories(db)
        session = session_repository.find_user_session(db, session_id, user_id)
        if not session:
            log.warning(
                "Attempted to delete non-existent session %s by user %s",
                session_id,
                user_id,
            )
            return False

        agent_id = session.agent_id

        if not session.can_be_deleted_by_user(user_id):
            log.warning(
                "User %s not authorized to delete session %s", user_id, session_id
            )
            return False

        deleted = session_repository.delete(db, session_id, user_id)
        if not deleted:
            return False

        log.info("Session %s deleted successfully by user %s", session_id, user_id)

        if agent_id and self.component:
            self._notify_agent_of_session_deletion(session_id, user_id, agent_id)

        return True

    def save_task(
        self,
        db: DbSession,
        task_id: str,
        session_id: str,
        user_id: str,
        user_message: Optional[str],
        message_bubbles: str,  # JSON string (opaque)
        task_metadata: Optional[str] = None  # JSON string (opaque)
    ) -> ChatTask:
        """
        Save a complete task interaction.
        
        Args:
            db: Database session
            task_id: A2A task ID
            session_id: Session ID
            user_id: User ID
            user_message: Original user input text
            message_bubbles: Array of all message bubbles displayed during this task
            task_metadata: Task-level metadata (status, feedback, agent name, etc.)
            
        Returns:
            Saved ChatTask entity
            
        Raises:
            ValueError: If session not found or validation fails
        """
        # Validate session exists and belongs to user
        session_repository = self._get_repositories(db)
        session = session_repository.find_user_session(db, session_id, user_id)
        if not session:
            raise ValueError(f"Session {session_id} not found for user {user_id}")

        # Create task entity - pass strings directly
        task = ChatTask(
            id=task_id,
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            message_bubbles=message_bubbles,  # Already a string
            task_metadata=task_metadata,      # Already a string
            created_time=now_epoch_ms(),
            updated_time=None
        )

        # Save via repository
        task_repo = ChatTaskRepository()
        saved_task = task_repo.save(db, task)

        # Update session activity
        session.mark_activity()
        session_repository.save(db, session)
        
        log.info(f"Saved task {task_id} for session {session_id}")
        return saved_task

    def get_session_tasks(
        self,
        db: DbSession,
        session_id: str,
        user_id: str
    ) -> List[ChatTask]:
        """
        Get all tasks for a session.
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID
            
        Returns:
            List of ChatTask entities in chronological order
            
        Raises:
            ValueError: If session not found
        """
        # Validate session exists and belongs to user
        session_repository = self._get_repositories(db)
        session = session_repository.find_user_session(db, session_id, user_id)
        if not session:
            raise ValueError(f"Session {session_id} not found for user {user_id}")

        # Load tasks
        task_repo = ChatTaskRepository()
        return task_repo.find_by_session(db, session_id, user_id)

    def get_session_messages_from_tasks(
        self,
        db: DbSession,
        session_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get session messages by flattening task message_bubbles.
        This provides backward compatibility with the old message-based API.
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID
            
        Returns:
            List of message dictionaries flattened from tasks
            
        Raises:
            ValueError: If session not found
        """
        # Load tasks
        tasks = self.get_session_tasks(db, session_id, user_id)
        
        # Flatten message_bubbles from all tasks
        messages = []
        for task in tasks:
            import json
            message_bubbles = json.loads(task.message_bubbles) if isinstance(task.message_bubbles, str) else task.message_bubbles
            
            for bubble in message_bubbles:
                # Determine sender type from bubble type
                bubble_type = bubble.get("type", "agent")
                sender_type = "user" if bubble_type == "user" else "agent"
                
                # Get sender name
                if bubble_type == "user":
                    sender_name = user_id
                else:
                    # Try to get agent name from task metadata, fallback to "agent"
                    sender_name = "agent"
                    if task.task_metadata:
                        task_metadata = json.loads(task.task_metadata) if isinstance(task.task_metadata, str) else task.task_metadata
                        sender_name = task_metadata.get("agent_name", "agent")
                
                # Create message dictionary
                message = {
                    "id": bubble.get("id", str(uuid.uuid4())),
                    "session_id": session_id,
                    "message": bubble.get("text", ""),
                    "sender_type": sender_type,
                    "sender_name": sender_name,
                    "message_type": "text",
                    "created_time": task.created_time
                }
                messages.append(message)
        
        return messages

    def _is_valid_session_id(self, session_id: SessionId) -> bool:
        return (
            session_id is not None
            and session_id.strip() != ""
            and session_id not in ["null", "undefined"]
        )

    def _notify_agent_of_session_deletion(
        self, session_id: SessionId, user_id: UserId, agent_id: str
    ) -> None:
        try:
            log.info(
                "Publishing session deletion event for session %s (agent %s, user %s)",
                session_id,
                agent_id,
                user_id,
            )

            if hasattr(self.component, "sam_events"):
                success = self.component.sam_events.publish_session_deleted(
                    session_id=session_id,
                    user_id=user_id,
                    agent_id=agent_id,
                    gateway_id=self.component.gateway_id,
                )

                if success:
                    log.info(
                        "Successfully published session deletion event for session %s",
                        session_id,
                    )
                else:
                    log.warning(
                        "Failed to publish session deletion event for session %s",
                        session_id,
                    )
            else:
                log.warning(
                    "SAM Events not available for session deletion notification"
                )

        except Exception as e:
            log.warning(
                "Failed to publish session deletion event to agent %s: %s",
                agent_id,
                e,
            )
