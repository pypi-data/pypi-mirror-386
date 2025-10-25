# chatbot-eval-common

Shared domain models for the Chatbot Evaluation platform. The `chatbot_eval_common`
package provides the event schema consumed by the `evaluation-client` SDK and any
other services that need to parse run telemetry.

## Installation

```bash
pip install chatbot-eval-common
```

## Exposed modules

- `chatbot_eval_common.events` – Pydantic models for dataset progress, lifecycle
  events, and system messages emitted during evaluation runs.

The package ships with `py.typed`, so static type checkers can read the type
information directly from the wheel.
