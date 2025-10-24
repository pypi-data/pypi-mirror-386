"""
Base App class for Gateway implementations in the Solace AI Connector.
"""

import logging
import uuid
from abc import abstractmethod
from typing import Any, Dict, List, Type

from solace_ai_connector.common.utils import deep_merge
from solace_ai_connector.flow.app import App
from solace_ai_connector.components.component_base import ComponentBase

from ...common.a2a import (
    get_discovery_topic,
    get_gateway_response_subscription_topic,
    get_gateway_status_subscription_topic,
)

log = logging.getLogger(__name__)


class BaseGatewayComponent(ComponentBase):
    pass


BASE_GATEWAY_APP_SCHEMA: Dict[str, List[Dict[str, Any]]] = {
    "config_parameters": [
        {
            "name": "namespace",
            "required": True,
            "type": "string",
            "description": "Absolute topic prefix for A2A communication (e.g., 'myorg/dev').",
        },
        {
            "name": "gateway_id",
            "required": False,
            "type": "string",
            "default": None,
            "description": "Unique ID for this gateway instance. Auto-generated if omitted.",
        },
        {
            "name": "artifact_service",
            "required": True,
            "type": "object",
            "description": "Configuration for the SHARED ADK Artifact Service.",
        },
        {
            "name": "enable_embed_resolution",
            "required": False,
            "type": "boolean",
            "default": True,
            "description": "Enable late-stage 'artifact_content' embed resolution in the gateway.",
        },
        {
            "name": "gateway_max_artifact_resolve_size_bytes",
            "required": False,
            "type": "integer",
            "default": 104857600,  # 100MB
            "description": "Maximum size of an individual artifact's raw content for 'artifact_content' embeds and max total accumulated size for a parent artifact after internal recursive resolution.",
        },
        {
            "name": "gateway_recursive_embed_depth",
            "required": False,
            "type": "integer",
            "default": 12,
            "description": "Maximum depth for recursively resolving 'artifact_content' embeds within files.",
        },
        {
            "name": "artifact_handling_mode",
            "required": False,
            "type": "string",
            "default": "reference",
            "description": (
                "How the gateway handles file parts from clients. "
                "'reference': Save inline file bytes to the artifact store and replace with a URI. "
                "'embed': Resolve file URIs and embed content as bytes. "
                "'passthrough': Send file parts to the agent as-is."
            ),
            "enum": ["reference", "embed", "passthrough"],
        },
        {
            "name": "gateway_max_message_size_bytes",
            "required": False,
            "type": "integer",
            "default": 10_000_000,  # 10MB
            "description": "Maximum allowed message size in bytes for messages published by the gateway.",
        },
        # --- Default User Identity Configuration ---
        {
            "name": "default_user_identity",
            "required": False,
            "type": "string",
            "description": "Default user identity to use when no user authentication is provided. WARNING: Only use in development environments with trusted access!",
        },
        {
            "name": "force_user_identity",
            "required": False,
            "type": "string",
            "description": "Override any provided user identity with this value. WARNING: Development only! This completely replaces authentication.",
        },
        # --- Identity Service Configuration ---
        {
            "name": "identity_service",
            "required": False,
            "type": "object",
            "default": None,
            "description": "Configuration for the pluggable Identity Service provider.",
        },
    ]
}


class BaseGatewayApp(App):
    """
    Base class for Gateway applications.

    Handles common configuration, Solace broker setup, and instantiation
    of the gateway-specific component. It also automatically merges its
    base schema with specific schema parameters defined by subclasses.
    """

    app_schema: Dict[str, List[Dict[str, Any]]] = BASE_GATEWAY_APP_SCHEMA
    SPECIFIC_APP_SCHEMA_PARAMS_ATTRIBUTE_NAME = "SPECIFIC_APP_SCHEMA_PARAMS"

    def __init_subclass__(cls, **kwargs):
        """
        Automatically merges the base gateway schema with specific schema
        parameters defined in any subclass.
        """
        super().__init_subclass__(**kwargs)

        specific_params = getattr(
            cls, cls.SPECIFIC_APP_SCHEMA_PARAMS_ATTRIBUTE_NAME, []
        )

        if not isinstance(specific_params, list):
            log.warning(
                "Class attribute '%s' in %s is not a list. Schema merging might be incorrect.",
                cls.SPECIFIC_APP_SCHEMA_PARAMS_ATTRIBUTE_NAME,
                cls.__name__,
            )
            specific_params = []

        base_params = BaseGatewayApp.app_schema.get("config_parameters", [])

        merged_config_parameters = list(base_params)
        merged_config_parameters.extend(specific_params)

        cls.app_schema = {"config_parameters": merged_config_parameters}
        log.debug(
            "BaseGatewayApp.__init_subclass__ created merged app_schema for %s with %d params.",
            cls.__name__,
            len(merged_config_parameters),
        )

    def __init__(self, app_info: Dict[str, Any], **kwargs):
        """
        Initializes the BaseGatewayApp.

        Args:
            app_info: Configuration dictionary for the app, typically from YAML.
            **kwargs: Additional arguments for the parent App class.
        """
        log.debug(
            "Initializing BaseGatewayApp with app_info: %s",
            app_info.get("name", "Unnamed App"),
        )

        code_config_app_block = getattr(self.__class__, "app_config", {}).get(
            "app_config", {}
        )
        yaml_app_config_block = app_info.get("app_config", {})
        resolved_app_config_block = deep_merge(
            code_config_app_block, yaml_app_config_block
        )

        self.namespace: str = resolved_app_config_block.get("namespace")
        if not self.namespace:
            raise ValueError(
                "Namespace is required in app_config for BaseGatewayApp or its derivatives."
            )

        self.gateway_id: str = resolved_app_config_block.get("gateway_id")
        if not self.gateway_id:
            self.gateway_id = f"gdk-gateway-{uuid.uuid4().hex[:8]}"
            resolved_app_config_block["gateway_id"] = self.gateway_id
            log.info("Generated unique gateway_id: %s", self.gateway_id)

        self.artifact_service_config: Dict = resolved_app_config_block.get(
            "artifact_service", {}
        )
        self.enable_embed_resolution: bool = resolved_app_config_block.get(
            "enable_embed_resolution", True
        )

        new_size_limit_key = "gateway_max_artifact_resolve_size_bytes"
        default_new_size_limit = 104857600
        old_size_limit_key = "gateway_artifact_content_limit_bytes"

        new_value = resolved_app_config_block.get(new_size_limit_key)
        old_value = resolved_app_config_block.get(old_size_limit_key)

        app_name_for_log = app_info.get("name", "BaseGatewayApp")

        if new_value is not None:
            self.gateway_max_artifact_resolve_size_bytes = new_value
            if old_value is not None and new_value != old_value:
                log.warning(
                    f"[{app_name_for_log}] Both '{new_size_limit_key}' (value: {new_value}) and deprecated '{old_size_limit_key}' (value: {old_value}) are present. "
                    f"Using value from '{new_size_limit_key}'."
                )
        elif old_value is not None:
            self.gateway_max_artifact_resolve_size_bytes = old_value
            log.warning(
                f"[{app_name_for_log}] Configuration key '{old_size_limit_key}' (value: {old_value}) is deprecated. "
                f"Please use '{new_size_limit_key}'. Using value from old key."
            )
        else:
            self.gateway_max_artifact_resolve_size_bytes = default_new_size_limit

        self.gateway_recursive_embed_depth: int = resolved_app_config_block.get(
            "gateway_recursive_embed_depth", 12
        )
        self.artifact_handling_mode: str = resolved_app_config_block.get(
            "artifact_handling_mode", "reference"
        )
        self.gateway_max_message_size_bytes: int = resolved_app_config_block.get(
            "gateway_max_message_size_bytes", 10_000_000
        )

        modified_app_info = app_info.copy()
        modified_app_info["app_config"] = resolved_app_config_block

        subscriptions = [
            {"topic": get_discovery_topic(self.namespace)},
            {
                "topic": get_gateway_response_subscription_topic(
                    self.namespace, self.gateway_id
                )
            },
            {
                "topic": get_gateway_status_subscription_topic(
                    self.namespace, self.gateway_id
                )
            },
        ]

        # Add trust card subscription if trust manager is enabled
        trust_config = resolved_app_config_block.get("trust_manager")
        if trust_config and trust_config.get("enabled", False):
            from ...common.a2a.protocol import get_trust_card_subscription_topic

            trust_card_topic = get_trust_card_subscription_topic(self.namespace)
            subscriptions.append({"topic": trust_card_topic})
            log.info(
                "Trust Manager enabled for gateway '%s', added trust card subscription: %s",
                self.gateway_id,
                trust_card_topic,
            )

        log.info(
            "Generated Solace subscriptions for gateway '%s': %s",
            self.gateway_id,
            subscriptions,
        )

        gateway_component_class = self._get_gateway_component_class()
        if not gateway_component_class or not issubclass(
            gateway_component_class, ComponentBase
        ):
            raise TypeError(
                f"_get_gateway_component_class in {self.__class__.__name__} must return a valid ComponentBase subclass."
            )

        component_definition = {
            "name": f"{self.gateway_id}_component",
            "component_class": gateway_component_class,
            "component_config": {"app_config": resolved_app_config_block},
            "subscriptions": subscriptions,
        }
        modified_app_info["components"] = [component_definition]

        broker_config = modified_app_info.setdefault("broker", {})
        broker_config["input_enabled"] = True
        broker_config["output_enabled"] = True
        broker_config["queue_name"] = (
            f"{self.namespace.strip('/')}/q/gdk/gateway/{self.gateway_id}"
        )
        broker_config["temporary_queue"] = modified_app_info.get("broker", {}).get("temporary_queue", True)
        log.debug(
            "Injected broker settings for gateway '%s': %s",
            self.gateway_id,
            broker_config,
        )

        super().__init__(app_info=modified_app_info, **kwargs)
        log.info("BaseGatewayApp '%s' initialized successfully.", self.name)

    @abstractmethod
    def _get_gateway_component_class(self) -> Type[BaseGatewayComponent]:
        """
        Abstract method to be implemented by derived gateway applications.

        Returns:
            The specific gateway component class (e.g., WebUIBackendComponent).
        """
        pass
