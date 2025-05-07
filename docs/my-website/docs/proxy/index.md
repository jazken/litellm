# LiteLLM Proxy

LiteLLM Proxy provides a unified interface to multiple LLM APIs, with features like routing, load balancing, caching, and guardrails.

## Key Features

- **Model Routing**: Route requests to different models based on rules
- **Load Balancing**: Distribute requests across multiple models or API keys
- **Caching**: Cache responses to reduce costs and latency
- **Guardrails**: Implement safety and security measures
- **Observability**: Monitor and log LLM usage

## Guardrails

LiteLLM Proxy includes several guardrail options to enhance security and safety:

- [**Prompt Guard**](./guardrails/prompt_guard.md): Detect and prevent prompt injection attacks
- **Content Moderation**: Filter inappropriate content
- **PII Detection**: Identify and mask personally identifiable information
- **Secret Detection**: Prevent leakage of API keys and secrets

See the [Guardrails documentation](./guardrails/README.md) for more details.

## Observability

LiteLLM Proxy provides observability features to monitor your LLM usage:

- **Request/Response Logging**: Log all requests and responses
- **Metrics Collection**: Track usage, latency, and costs
- **Integration with Monitoring Tools**: Export data to monitoring platforms

## Getting Started

To start using LiteLLM Proxy:

```bash
pip install litellm
litellm --config /path/to/config.yaml
```

Example configuration:

```yaml
model_list:
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: gpt-3.5-turbo
      api_key: ${OPENAI_API_KEY}

# Enable guardrails
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
      log_only: false

# Enable observability
litellm_settings:
  callbacks: ["prompt_guard_observability"]
  prompt_guard_observability:
    log_to_file: true
    log_file_path: "/tmp/prompt_guard_logs.jsonl"
```

## Learn More

- [Configuration Options](./config.md)
- [Load Balancing](./load_balancing.md)
- [Call Hooks](./call_hooks.md)
- [Virtual Keys](./virtual_keys.md)