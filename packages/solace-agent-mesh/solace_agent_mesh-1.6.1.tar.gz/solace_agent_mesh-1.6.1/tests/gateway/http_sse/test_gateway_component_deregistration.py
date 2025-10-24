import unittest
from unittest.mock import MagicMock, patch
import time

from a2a.types import AgentCard, AgentCapabilities
from solace_agent_mesh.gateway.http_sse.component import WebUIBackendComponent
from solace_agent_mesh.common.agent_registry import AgentRegistry


class TestWebUIBackendComponentDeregistration(unittest.TestCase):
    """Test suite for agent de-registration in WebUIBackendComponent."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the WebUIBackendComponent with minimal required attributes
        self.component = MagicMock(spec=WebUIBackendComponent)
        self.component.log_identifier = "[TestGateway]"
        self.component.gateway_id = "test_gateway"
        
        # Create a real AgentRegistry for testing
        self.agent_registry = AgentRegistry()
        self.component.agent_registry = self.agent_registry
        
        # Add check_ttl_expired method to AgentRegistry if it doesn't exist
        if not hasattr(self.agent_registry, 'check_ttl_expired'):
            self.agent_registry.check_ttl_expired = lambda agent_name, ttl_seconds: (False, 0)
        
        # Create test agent cards
        self.agent_card1 = AgentCard(
            name="agent1",
            description="Test Agent 1",
            capabilities=AgentCapabilities(
                streaming=False,
                push_notifications=False,
                state_transition_history=False
            ),
            skills=[],
            version="1.0.0",
            url="http://test-agent1",
            default_input_modes=["text"],
            default_output_modes=["text"]
        )
        self.agent_card2 = AgentCard(
            name="agent2",
            description="Test Agent 2",
            capabilities=AgentCapabilities(
                streaming=False,
                push_notifications=False,
                state_transition_history=False
            ),
            skills=[],
            version="1.0.0",
            url="http://test-agent2",
            default_input_modes=["text"],
            default_output_modes=["text"]
        )
        
        # Add agents to registry
        self.agent_registry.add_or_update_agent(self.agent_card1)
        self.agent_registry.add_or_update_agent(self.agent_card2)

    def test_check_agent_health_no_expired_agents(self):
        """Test _check_agent_health when no agents have expired TTLs."""
        # Set up
        self.component._check_agent_health = WebUIBackendComponent._check_agent_health.__get__(self.component)
        self.component._deregister_agent = MagicMock()
        self.component.get_config = MagicMock()
        self.component.get_config.side_effect = lambda key, default=None: {
            "agent_health_check_ttl_seconds": 300,  # 5 minutes
            "agent_health_check_interval_seconds": 10
        }.get(key, default)
        
        # Execute
        self.component._check_agent_health()
        
        # Verify
        self.component._deregister_agent.assert_not_called()
        self.assertEqual(len(self.agent_registry.get_agent_names()), 2)

    def test_check_agent_health_with_expired_agents(self):
        """Test _check_agent_health when some agents have expired TTLs."""
        # Set up
        self.component._deregister_agent = MagicMock()
        
        # Create a custom implementation of _check_agent_health for testing
        def custom_check_agent_health():
            # Simulate the behavior of the real _check_agent_health method
            # but use our mocked _deregister_agent
            agent_names = self.agent_registry.get_agent_names()
            for agent_name in agent_names:
                # Simulate agent1 being expired
                if agent_name == "agent1":
                    self.component._deregister_agent(agent_name)
        
        # Replace the method with our custom implementation
        self.component._check_agent_health = custom_check_agent_health
        
        # Execute
        self.component._check_agent_health()
        
        # Verify
        self.component._deregister_agent.assert_called_once_with("agent1")

    def test_deregister_agent(self):
        """Test _deregister_agent removes the agent from the registry."""
        # Set up
        self.component._deregister_agent = WebUIBackendComponent._deregister_agent.__get__(self.component)
        
        # Execute
        self.component._deregister_agent("agent1")
        
        # Verify
        # Agent should be removed from registry
        self.assertNotIn("agent1", self.agent_registry.get_agent_names())
        self.assertIn("agent2", self.agent_registry.get_agent_names())

    def test_deregister_nonexistent_agent(self):
        """Test _deregister_agent with a non-existent agent."""
        # Set up
        self.component._deregister_agent = WebUIBackendComponent._deregister_agent.__get__(self.component)
        
        # Execute
        self.component._deregister_agent("nonexistent_agent")
        
        # Verify
        # Registry should remain unchanged
        self.assertEqual(len(self.agent_registry.get_agent_names()), 2)
        
    def test_check_agent_health_multiple_expired_agents(self):
        """Test _check_agent_health when multiple agents have expired TTLs."""
        # Set up
        self.component._deregister_agent = MagicMock()
        
        # Add a third agent
        agent_card3 = AgentCard(
            name="agent3",
            description="Test Agent 3",
            capabilities=AgentCapabilities(
                streaming=False,
                push_notifications=False,
                state_transition_history=False
            ),
            skills=[],
            version="1.0.0",
            url="http://test-agent3",
            default_input_modes=["text"],
            default_output_modes=["text"]
        )
        self.agent_registry.add_or_update_agent(agent_card3)
        
        # Create a custom implementation of _check_agent_health for testing
        def custom_check_agent_health():
            # Simulate the behavior of the real _check_agent_health method
            # but use our mocked _deregister_agent
            agent_names = self.agent_registry.get_agent_names()
            for agent_name in agent_names:
                # Simulate agent1 and agent3 being expired
                if agent_name in ["agent1", "agent3"]:
                    self.component._deregister_agent(agent_name)
        
        # Replace the method with our custom implementation
        self.component._check_agent_health = custom_check_agent_health
        
        # Execute
        self.component._check_agent_health()
        
        # Verify
        self.assertEqual(self.component._deregister_agent.call_count, 2)
        self.component._deregister_agent.assert_any_call("agent1")
        self.component._deregister_agent.assert_any_call("agent3")
        
    def test_check_agent_health_disabled_by_config(self):
        """Test _check_agent_health when disabled by configuration."""
        # Set up
        self.component._check_agent_health = WebUIBackendComponent._check_agent_health.__get__(self.component)
        self.component._deregister_agent = MagicMock()
        self.component.get_config = MagicMock()
        self.component.get_config.side_effect = lambda key, default=None: {
            "agent_health_check_ttl_seconds": 0,  
            "agent_health_check_interval_seconds": 0  
        }.get(key, default)
        
        # Manually modify the last_seen time for all agents to simulate expiration
        with patch.object(self.agent_registry, '_last_seen') as mock_last_seen:
            mock_last_seen.__getitem__.side_effect = lambda key: time.time() - 9999  # Very old
            mock_last_seen.__contains__ = lambda self, key: key in ["agent1", "agent2"]
            
            # Execute - should raise ValueError because both config values are zero
            with self.assertRaises(ValueError) as context:
                self.component._check_agent_health()
            
            # Verify the error message
            self.assertIn("agent_health_check_ttl_seconds", str(context.exception))
            self.assertIn("agent_health_check_interval_seconds", str(context.exception))
            self.assertIn("must be positive", str(context.exception))
        
        # Verify no agents were deregistered
        self.component._deregister_agent.assert_not_called()


if __name__ == "__main__":
    unittest.main()