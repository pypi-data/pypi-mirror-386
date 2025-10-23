"""
Basic usage example for the Paylm SDK.
"""

import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from paylm_sdk import Client, UsageData, ServiceProvider, MetaModels

def main():
    """Basic usage example."""
    # Create a new client with your API key
    client = Client.new_client_with_url(
        "pk_e0ea0d11bb7f0d174caf578d665454acff97bdb1f85c235af547ccd9a733ef35",
        "http://localhost:8080"
    )
    
    # Define usage data using constants
    usage_data = UsageData(
        service_provider=ServiceProvider.META,
        model=MetaModels.LLAMA,
        prompt_tokens=756,
        completion_tokens=244,
        total_tokens=1000
    )
    
    # Send usage data
    try:
        client.send_usage("agent-123", "customer-456", "email-sent", usage_data)
        print("Usage data sent successfully!")
    except Exception as e:
        print(f"Failed to send usage: {e}")

if __name__ == "__main__":
    main()
