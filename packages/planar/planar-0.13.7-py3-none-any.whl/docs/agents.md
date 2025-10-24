# Agents

Agent steps let a workflow call an LLM through a first-class `Agent` object. Each agent bundles its prompts, model choice, validation, and optional tool integrations so you can reuse it across many workflows while keeping the workflow code itself focused on business logic.

## Create an Agent

```python
from pydantic import BaseModel, Field
from planar.ai import Agent


class OrderInput(BaseModel):
    order_id: str
    customer_tier: str


class PricingDecision(BaseModel):
    final_price: float = Field(description="Price after discounts")
    reasoning: str


pricing_agent = Agent(
    name="order_pricing",
    system_prompt="you decide the right price given our pricing policy.",
    user_prompt="Order details:\n\n{input}",
    input_type=OrderInput,
    output_type=PricingDecision,
    model="anthropic:claude-3-5-sonnet",
    model_parameters={"temperature": 0.2},
)
```

- `input_type` and `output_type` are optional but recommended. When omitted, the agent expects and returns strings.
- Prompts are regular Python format strings. `{input}` expands to the serialized `input_type`. You can also refer to individual fields (for example `{input.customer_tier}`).
- Use `model_parameters` for provider-specific tuning such as temperature or top_p.

## Call an Agent inside a Workflow

```python
from planar.workflows import workflow


@workflow()
async def price_order(order: OrderInput) -> PricingDecision:
    result = await pricing_agent(order)
    return result.output
```

Agent calls return `AgentRunResult[TOutput]`, which always contains the `.output`. Future releases may add telemetry fields, so prefer accessing data through the result object.

## Tool-Enabled Agents

Add async callables to the `tools` argument to let the model inspect or update external systems during the run. Each tool must accept and return JSON-serializable types (Pydantic models are supported).

```python
from planar.ai import Agent, get_tool_context


async def fetch_customer(customer_id: str) -> dict:
    return await crm_client.get_customer(customer_id)


async def record_discount(order_id: str, amount: float) -> None:
    await billing_client.store_discount(order_id, amount)


ops_agent = Agent(
    name="reprice_with_tools",
    system_prompt="use the tools to justify each discount.",
    user_prompt="Order:\n{input}",
    input_type=OrderInput,
    output_type=PricingDecision,
    tools=[fetch_customer, record_discount],
    model="openai:gpt-4o",
    max_turns=4,
)
```

### Tool Context

If tools need shared state (for example, database clients or API credentials), define a context schema with `tool_context_type` and pass the matching object when you call the agent. Access it inside tools with `planar.ai.get_tool_context()`.

```python
from dataclasses import dataclass


@dataclass
class OpsContext:
    crm_client: CRMClient
    billing_client: BillingClient


@workflow()
async def reprice(order: OrderInput) -> PricingDecision:
    ctx = OpsContext(crm_client=create_crm(), billing_client=create_billing())
    result = await ops_agent(order, tool_context=ctx)
    return result.output
```

Keep the context limited to durable resources or immutable data. Ephemeral counters and other transient state will not survive partial replays.

## File and Image Inputs

`PlanarFile` instances can be part of the agent input model. The agent runtime streams file content to the provider with no extra code. This also works when the file is nested deeper inside the Pydantic model.

## Runtime Overrides

Planar stores the agent defaults in code, but the CoPlane UI/API can override prompts, models, and model parameters at runtime. Overrides are merged with the defaults just before execution. Use this to let business users iterate on prompts without redeploying code.

## Recommendations

- Keep agent prompts focused and consistent with the workflow purpose.
- Provide structured outputs whenever the workflow needs to branch or make decisions based on the agent response.
- Limit `max_turns` to the minimum needed to control cost and latency.
- Treat tool functions like regular workflow steps: make them idempotent and safe to replay.
