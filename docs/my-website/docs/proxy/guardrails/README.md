# LiteLLM Guardrails

LiteLLM Proxy supports various guardrail integrations to enhance security, safety, and compliance of your LLM applications.

## Available Guardrails

| Guardrail | Description | Documentation |
|-----------|-------------|---------------|
| Prompt Guard | Detect and prevent prompt injection attacks | [Prompt Guard](./prompt_guard.md) |
| Lakera | Content moderation and safety | [Lakera](./lakera.md) |
| Aporia | Monitoring and guardrails | [Aporia](./aporia.md) |
| Bedrock | AWS Bedrock guardrails | [Bedrock](./bedrock.md) |
| Presidio | PII detection and masking | [Presidio](./presidio.md) |
| Hide Secrets | Detect and redact secrets | [Hide Secrets](./hide_secrets.md) |
| AIM | AI safety guardrails | [AIM](./aim.md) |
| Guardrails AI | Comprehensive guardrails | [Guardrails AI](./guardrails_ai.md) |

## Configuring Guardrails

You can configure guardrails in your LiteLLM Proxy config.yaml file:

```yaml
guardrails:
  - guardrail_name: "my-guardrail"
    litellm_params:
      guardrail: prompt_guard  # Choose from available guardrails
      mode: pre_call  # When to run the guardrail
      default_on: true  # Whether the guardrail is enabled by default
      # Additional parameters specific to the guardrail
```

## Observability

LiteLLM provides observability for guardrails through callback mechanisms. You can configure callbacks to log guardrail activities:

```yaml
litellm_settings:
  callbacks: ["prompt_guard_observability"]
  prompt_guard_observability:
    log_to_file: true
    log_file_path: "/tmp/prompt_guard_logs.jsonl"
```

## Creating Custom Guardrails

You can create custom guardrails by implementing a callback class that follows the LiteLLM callback interface. Your guardrail should implement at least:

- `async_pre_call_hook`: Run before the LLM call
- `async_post_call_hook`: Run after the LLM call

See the [Prompt Guard implementation](./prompt_guard.md) for an example.