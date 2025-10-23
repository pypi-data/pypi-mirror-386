"""
Example demonstrating the use of model constants in the Paylm SDK.
"""

from paylm_sdk import (
    Client,
    UsageData,
    UsageDataWithStrings,
    OpenAIModels,
    AnthropicModels,
    GoogleDeepMindModels,
    MetaModels,
    DeepSeekModels,
    ServiceProvider,
    is_model_supported,
)


def main():
    """Main function demonstrating model constants usage."""
    # Create a client
    client = Client.new_client("your-api-key-here")

    print("=== Model Constants Example ===\n")

    # Example 1: Using OpenAI model constants
    print("1. Using OpenAI Model Constants:")
    openai_usage = UsageData(
        service_provider=ServiceProvider.OPENAI,
        model=OpenAIModels.GPT_4O,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
    )

    print(f"   Model: {openai_usage.model}")
    print(f"   Provider: {openai_usage.service_provider}")
    print(f"   Tokens: {openai_usage.total_tokens}\n")

    # Example 2: Using Anthropic model constants
    print("2. Using Anthropic Model Constants:")
    anthropic_usage = UsageData(
        service_provider=ServiceProvider.ANTHROPIC,
        model=AnthropicModels.SONNET_4_5,
        prompt_tokens=200,
        completion_tokens=100,
        total_tokens=300,
    )

    print(f"   Model: {anthropic_usage.model}")
    print(f"   Provider: {anthropic_usage.service_provider}\n")

    # Example 3: Using Google DeepMind model constants
    print("3. Using Google DeepMind Model Constants:")
    gemini_usage = UsageData(
        service_provider=ServiceProvider.GOOGLE_DEEPMIND,
        model=GoogleDeepMindModels.GEMINI_2_5_PRO,
        prompt_tokens=150,
        completion_tokens=75,
        total_tokens=225,
    )

    print(f"   Model: {gemini_usage.model}")
    print(f"   Provider: {gemini_usage.service_provider}\n")

    # Example 4: Using Meta model constants
    print("4. Using Meta Model Constants:")
    llama_usage = UsageData(
        service_provider=ServiceProvider.META,
        model=MetaModels.LLAMA_4_MAVERICK,
        prompt_tokens=300,
        completion_tokens=150,
        total_tokens=450,
    )

    print(f"   Model: {llama_usage.model}")
    print(f"   Provider: {llama_usage.service_provider}\n")

    # Example 5: Using DeepSeek model constants
    print("5. Using DeepSeek Model Constants:")
    deepseek_usage = UsageData(
        service_provider=ServiceProvider.DEEPSEEK,
        model=DeepSeekModels.DEEPSEEK_R1_GLOBAL,
        prompt_tokens=250,
        completion_tokens=125,
        total_tokens=375,
    )

    print(f"   Model: {deepseek_usage.model}")
    print(f"   Provider: {deepseek_usage.service_provider}\n")

    # Example 6: Check if a model is supported
    print("6. Checking Model Support:")
    models_to_check = [
        OpenAIModels.GPT_5,
        OpenAIModels.O3,
        AnthropicModels.SONNET_4_5,
        "unknown-model",
    ]

    for model in models_to_check:
        supported = is_model_supported(model)
        status = "✓ Supported" if supported else "✗ Not Supported"
        print(f"   {model}: {status}")
    print()

    # Example 7: Service providers are explicit (user provides them)
    print("7. Service Providers (User-Provided):")
    print(f"   OpenAI models use: {ServiceProvider.OPENAI}")
    print(f"   Anthropic models use: {ServiceProvider.ANTHROPIC}")
    print(f"   Google DeepMind models use: {ServiceProvider.GOOGLE_DEEPMIND}")
    print(f"   Meta models use: {ServiceProvider.META}")
    print()

    # Example 8: Using constants with send_usage_with_token_string
    print("8. Using Constants with send_usage_with_token_string:")
    string_usage = UsageDataWithStrings(
        service_provider=ServiceProvider.OPENAI,
        model=OpenAIModels.GPT_4O_MINI,
        prompt_string="What is the capital of France?",
        output_string="The capital of France is Paris.",
    )

    print(f"   Model: {string_usage.model}")
    print(f"   Provider: {string_usage.service_provider}")
    print(f'   Prompt: "{string_usage.prompt_string}"')
    print(f'   Output: "{string_usage.output_string}"\n')

    print("=== All examples completed successfully! ===")
    print("\nNote: To actually send data to the API, uncomment the client.send_usage() calls below:\n")
    print('# client.send_usage("agent-123", "customer-456", "test", openai_usage)')
    print('# client.send_usage_with_token_string("agent-123", "customer-456", "test", string_usage)')


if __name__ == "__main__":
    main()
