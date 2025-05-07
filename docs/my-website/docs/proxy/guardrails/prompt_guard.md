# Prompt Guard

LiteLLM Proxy includes a built-in prompt guarding mechanism to detect and prevent prompt injection attacks and other security concerns.

## Overview

The Prompt Guard feature provides:

1. **Injection Detection**: Identifies common prompt injection patterns
2. **Sensitive Information Detection**: Flags prompts containing sensitive terms
3. **Length Validation**: Prevents excessively long prompts
4. **Observability**: Logs all prompt guarding activities for monitoring

## Configuration

You can configure Prompt Guard in your LiteLLM Proxy config.yaml file:

```yaml
guardrails:
  - guardrail_name: "prompt-injection-guard"
    litellm_params:
      guardrail: prompt_guard
      mode: pre_call
      default_on: true
      block_requests: true
      injection_patterns:
        - "ignore previous instructions"
        - "ignore all previous instructions"
        - "disregard previous instructions"
        - "forget your instructions"
        - "you are now"
      custom_patterns:
        - "system prompt:"
        - "new system prompt:"
      max_prompt_length: 10000
      sensitive_terms:
        - "password"
        - "credit card"
        - "social security"
      log_only: false  # Set to true to only log issues without blocking
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `guardrail` | string | Must be set to `prompt_guard` |
| `mode` | string | When to run the guardrail. Use `pre_call` to check before sending to the LLM |
| `default_on` | boolean | Whether the guardrail is enabled by default |
| `block_requests` | boolean | Whether to block requests that trigger the guardrail |
| `injection_patterns` | list | List of regex patterns to detect prompt injections |
| `custom_patterns` | list | List of custom regex patterns to detect |
| `max_prompt_length` | integer | Maximum allowed prompt length |
| `sensitive_terms` | list | List of sensitive terms to detect |
| `log_only` | boolean | If true, only log issues without blocking |

## Observability

You can enable observability for Prompt Guard to log all activities:

```yaml
litellm_settings:
  callbacks: ["prompt_guard_observability"]
  prompt_guard_observability:
    log_to_file: true
    log_file_path: "/tmp/prompt_guard_logs.jsonl"
    include_prompt_text: false  # Set to true to include full prompt text in logs
    log_to_cloud: false
    cloud_service: "datadog"  # Optional: "datadog" or "cloudwatch"
    cloud_api_key: "your-api-key"  # Required if log_to_cloud is true
```

### Observability Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `log_to_file` | boolean | Whether to log to a local file |
| `log_file_path` | string | Path to the log file |
| `include_prompt_text` | boolean | Whether to include the full prompt text in logs |
| `log_to_cloud` | boolean | Whether to log to a cloud service |
| `cloud_service` | string | Name of the cloud service (e.g., "datadog", "cloudwatch") |
| `cloud_api_key` | string | API key for the cloud service |
| `cloud_endpoint` | string | Endpoint for the cloud service |

## Example Log Output

When Prompt Guard detects an issue, it logs an entry like this:

```json
{
  "timestamp": "2025-05-07T10:15:30.123456",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "model": "gpt-3.5-turbo",
  "prompt_guard_analysis": {
    "is_safe": false,
    "issues": ["injection_detected"],
    "details": {
      "detected_patterns": ["ignore previous instructions"]
    }
  },
  "response_id": "chatcmpl-123456789",
  "response_model": "gpt-3.5-turbo"
}
```

## Programmatic Usage

You can also use Prompt Guard programmatically in your code:

```python
import litellm
from litellm.proxy.guardrails.guardrail_hooks.prompt_guard import PromptGuardCallback
from litellm.integrations.prompt_guard_observability import PromptGuardObservability

# Initialize the prompt guard
prompt_guard = PromptGuardCallback(
    guardrail_name="my-prompt-guard",
    event_hook="pre_call",
    default_on=True,
    block_requests=True,
    injection_patterns=["ignore previous instructions"],
    custom_patterns=["system prompt:"],
    max_prompt_length=10000,
    sensitive_terms=["password"],
    log_only=False,
)

# Add the prompt guard to LiteLLM
litellm.logging_callback_manager.add_litellm_callback(prompt_guard)

# Initialize observability (optional)
observability = PromptGuardObservability(
    log_to_file=True,
    log_file_path="/tmp/prompt_guard_logs.jsonl",
    include_prompt_text=False,
)

# Add observability to LiteLLM
litellm.callbacks.append(observability)

# Now use LiteLLM as usual
response = litellm.completion(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]
)
```

## Security Considerations

- Set `include_prompt_text: false` in production to avoid logging sensitive information
- Consider using `log_only: true` initially to monitor without blocking legitimate requests
- Regularly review logs to refine patterns and reduce false positives