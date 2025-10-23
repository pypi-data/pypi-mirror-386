"""
Tests for the Paylm SDK client.
"""

import json
import logging
import unittest
from unittest.mock import Mock, patch, MagicMock

import requests

from paylm_sdk.client import Client
from paylm_sdk.models import UsageData, UsageDataWithStrings, APIRequest, ModelPricing, MODEL_PRICING


class TestClient(unittest.TestCase):
    """Test cases for the Client class."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test-api-key"
        self.base_url = "https://api.paylm.com"
        self.client = Client(self.api_key, self.base_url)

    def test_new_client(self):
        """Test creating a new client with default URL."""
        client = Client.new_client(self.api_key)
        self.assertIsNotNone(client)
        self.assertEqual(client.api_key, self.api_key)
        self.assertEqual(client.base_url, "https://api.paylm.com")

    def test_new_client_with_url(self):
        """Test creating a new client with custom URL."""
        custom_url = "https://custom-api.paylm.com"
        client = Client.new_client_with_url(self.api_key, custom_url)
        self.assertIsNotNone(client)
        self.assertEqual(client.api_key, self.api_key)
        self.assertEqual(client.base_url, custom_url)

    def test_calculate_cost_llama(self):
        """Test cost calculation for Llama model."""
        usage_data = UsageData(
            service_provider="openai",
            model="llama",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500
        )
        
        cost = self.client._calculate_cost("llama", usage_data)
        expected = 0.00015  # (1000/1000 + 500/1000) * 0.0001
        self.assertAlmostEqual(cost, expected, places=6)

    def test_calculate_cost_gpt4(self):
        """Test cost calculation for GPT-4 model."""
        usage_data = UsageData(
            service_provider="openai",
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500
        )
        
        cost = self.client._calculate_cost("gpt-4", usage_data)
        expected = 0.06  # (1000/1000) * 0.03 + (500/1000) * 0.06
        self.assertEqual(cost, expected)

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation for unknown model (default pricing)."""
        usage_data = UsageData(
            service_provider="custom",
            model="unknown-model",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500
        )
        
        cost = self.client._calculate_cost("unknown-model", usage_data)
        expected = 0.00015  # (1000/1000 + 500/1000) * 0.0001 (default pricing)
        self.assertAlmostEqual(cost, expected, places=6)

    @patch('paylm_sdk.client.requests.Session.post')
    def test_send_usage_success(self, mock_post):
        """Test successful usage data sending."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_post.return_value = mock_response

        usage_data = UsageData(
            service_provider="openai",
            model="llama",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500
        )

        # Should not raise any exception
        self.client.send_usage("agent-123", "customer-456", "test-indicator", usage_data)

        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Check URL
        self.assertEqual(call_args[0][0], "https://api.paylm.com/api/v1/usage")
        
        # Check headers
        headers = call_args[1]['headers']
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(headers['paylm-api-key'], 'test-api-key')
        
        # Check request data
        request_data = call_args[1]['json']
        self.assertEqual(request_data['agentId'], 'agent-123')
        self.assertEqual(request_data['customerId'], 'customer-456')
        self.assertEqual(request_data['indicator'], 'test-indicator')
        self.assertAlmostEqual(request_data['amount'], 0.00015, places=6)  # Expected cost for llama model
        self.assertEqual(request_data['inputToken'], 1000)  # prompt_tokens
        self.assertEqual(request_data['outputToken'], 500)  # completion_tokens
        self.assertEqual(request_data['model'], 'llama')  # model
        self.assertEqual(request_data['serviceProvider'], 'openai')  # service_provider

    @patch('paylm_sdk.client.requests.Session.post')
    def test_send_usage_http_error(self, mock_post):
        """Test handling of HTTP errors."""
        # Mock HTTP error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = requests.HTTPError("400 Bad Request")
        mock_post.return_value = mock_response

        usage_data = UsageData(
            service_provider="openai",
            model="llama",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500
        )

        # Should raise HTTPError
        with self.assertRaises(requests.HTTPError):
            self.client.send_usage("agent-123", "customer-456", "test-indicator", usage_data)

    @patch('paylm_sdk.client.requests.Session.post')
    def test_send_usage_network_error(self, mock_post):
        """Test handling of network errors."""
        # Mock network error
        mock_post.side_effect = requests.ConnectionError("Network error")

        usage_data = UsageData(
            service_provider="openai",
            model="llama",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500
        )

        # Should raise ConnectionError
        with self.assertRaises(requests.ConnectionError):
            self.client.send_usage("agent-123", "customer-456", "test-indicator", usage_data)

    def test_set_log_level(self):
        """Test setting log level."""
        self.client.set_log_level(logging.DEBUG)
        self.assertEqual(self.client.logger.level, logging.DEBUG)

    def test_get_logger(self):
        """Test getting logger instance."""
        logger = self.client.get_logger()
        self.assertIsNotNone(logger)
        self.assertEqual(logger, self.client.logger)

    @patch('paylm_sdk.client.requests.Session.post')
    def test_send_usage_with_token_string_success(self, mock_post):
        """Test successful usage data sending with token strings."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_post.return_value = mock_response

        usage_data = UsageDataWithStrings(
            service_provider="openai",
            model="llama",
            prompt_string="Hello, world!",
            output_string="Hi there!"
        )

        # Should not raise any exception
        self.client.send_usage_with_token_string("agent-123", "customer-456", "test-indicator", usage_data)

        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Check URL
        self.assertEqual(call_args[0][0], "https://api.paylm.com/api/v1/usage")
        
        # Check headers
        headers = call_args[1]['headers']
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(headers['paylm-api-key'], 'test-api-key')
        
        # Check request data
        request_data = call_args[1]['json']
        self.assertEqual(request_data['agentId'], 'agent-123')
        self.assertEqual(request_data['customerId'], 'customer-456')
        self.assertEqual(request_data['indicator'], 'test-indicator')
        self.assertIn('amount', request_data)  # Amount should be calculated
        self.assertIn('inputToken', request_data)  # inputToken should be present
        self.assertIn('outputToken', request_data)  # outputToken should be present
        self.assertIsInstance(request_data['inputToken'], int)  # inputToken should be integer
        self.assertIsInstance(request_data['outputToken'], int)  # outputToken should be integer
        self.assertEqual(request_data['model'], 'llama')  # model
        self.assertEqual(request_data['serviceProvider'], 'openai')  # service_provider


class TestModels(unittest.TestCase):
    """Test cases for data models."""

    def test_usage_data(self):
        """Test UsageData model."""
        usage_data = UsageData(
            service_provider="openai",
            model="llama",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500
        )
        
        self.assertEqual(usage_data.service_provider, "openai")
        self.assertEqual(usage_data.model, "llama")
        self.assertEqual(usage_data.prompt_tokens, 1000)
        self.assertEqual(usage_data.completion_tokens, 500)
        self.assertEqual(usage_data.total_tokens, 1500)

    def test_api_request(self):
        """Test APIRequest model."""
        api_request = APIRequest(
            agent_id="agent-123",
            customer_id="customer-456",
            indicator="test-indicator",
            amount=0.15
        )
        
        self.assertEqual(api_request.agent_id, "agent-123")
        self.assertEqual(api_request.customer_id, "customer-456")
        self.assertEqual(api_request.indicator, "test-indicator")
        self.assertEqual(api_request.amount, 0.15)

    def test_model_pricing(self):
        """Test ModelPricing model."""
        pricing = ModelPricing(
            prompt_tokens_cost=0.0001,
            completion_tokens_cost=0.0001
        )
        
        self.assertEqual(pricing.prompt_tokens_cost, 0.0001)
        self.assertEqual(pricing.completion_tokens_cost, 0.0001)

    def test_model_pricing_constants(self):
        """Test that MODEL_PRICING contains expected models."""
        expected_models = [
            "llama", "gpt-3.5-turbo", "gpt-4", 
            "claude-3-sonnet", "claude-3-opus"
        ]
        
        for model in expected_models:
            self.assertIn(model, MODEL_PRICING)
            self.assertIsInstance(MODEL_PRICING[model], ModelPricing)


if __name__ == '__main__':
    unittest.main()
