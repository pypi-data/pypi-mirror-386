# Step Types in Planar

## Overview

Planar workflows support several specialized step types to address different decision-making and waiting patterns:

* Human-in-the-loop interactions (`Human`)  
* AI agent-based decisions (`Agent`)  
* Rule-based logic (future: `@rule`)
* Event-based waiting (`wait_for_event()`)
* Condition-based waiting (`@wait`)

These step types are designed to be configurable both at development time through code and at runtime through UI interfaces, enabling a hybrid development model where engineers define the workflow structure and business users can customize decision logic.

## Workflow Structure

Planar workflows are defined as async functions decorated with `@workflow()`. Steps are also async functions decorated with specialized step decorators:

```python
from planar.workflows import workflow, step
from planar.workflows.contrib import wait_for_event

@workflow()
async def my_workflow(input_data: dict) -> dict:
    # Basic processing step
    result = await process_data(input_data)
    
    # Wait for an external event
    event_data = await wait_for_event("external_event")
    
    # Continue processing
    final_result = await finalize_data(result, event_data)
    
    return {"result": final_result}

@step()
async def process_data(data: dict):
    # Implementation
    return processed_data

@step()
async def finalize_data(result, event_data):
    # Implementation
    return final_result
```

## Decision Step Types

### Human-in-the-loop Steps

The `@human` decorator enables steps that capture structured input from users (e.g., "approve/reject" or "provide discount amount"). When a workflow reaches a human step, it suspends execution until user input is provided.

**Key Features:**

* **Typed inputs and outputs**: Uses Pydantic models for structured data
* **Configurable UI metadata**: Descriptive info or help text to guide the user
* **Durable state**: The workflow engine records inputs/outputs and resumes correctly
* **Observable**: Step transitions, input parameters, and results are traceable

**Example:**

```python
from pydantic import BaseModel, Field
from planar.workflows import workflow, step
from planar.workflows.decorators import human

class ApprovalRequest(BaseModel):
    order_id: str
    amount: float
    customer: str
    
class ApprovalResponse(BaseModel):
    approved: bool
    reason: str = ""

@workflow()
async def order_approval_workflow(order_data: dict):
    # Process the order
    order_details = await process_order(order_data)
    
    # Request human approval
    approval = await approve_order(
        order_id=order_details["id"],
        amount=order_details["total"],
        customer=order_details["customer_name"]
    )
    
    if approval.approved:
        return {"status": "approved", "reason": approval.reason}
    else:
        return {"status": "rejected", "reason": approval.reason}

@human(
    description="Approve or reject this order",
    ui_template="Order {order_id} for ${amount} from {customer} requires approval"
)
async def approve_order(order_id: str, amount: float, customer: str) -> ApprovalResponse:
    # This function body is only used as a fallback if the UI is not available
    # In normal operation, execution is suspended until human input is received
    return ApprovalResponse(approved=amount < 1000, reason="Automatic approval for small orders")
```

### Agent Steps

Agents provide a way to incorporate LLM-based decision making into workflows. Unlike other step types that use function decorators, agents are defined as objects that can be directly called within workflows.

**Key Features:**

* **Object-based definition**: Create agents as reusable objects
* **Configurable prompts**: System and user prompts with template formatting
* **Structured input/output**: Works with Pydantic models for typed data
* **Multi-turn capability**: Can use tools and have multiple interaction turns
* **Model selection**: Supports multiple LLM providers (OpenAI, Anthropic, etc.)
* **Observability**: Records prompts, completions, and tool usage for auditing
* **Tool context**: Optional `tool_context_type` lets workflows pass shared context or dependencies (e.g., API clients, config) and retrieve it inside tools with `planar.ai.get_tool_context()`

**Example:**

```python
from pydantic import BaseModel, Field
from planar.workflows import workflow
from planar.ai import Agent
from planar.ai.providers import Anthropic, OpenAI

# Define structured output model
class PricingDecision(BaseModel):
    price: float = Field(description="Calculated price in USD")
    discount_percent: float = Field(description="Applied discount percentage")
    discount_reason: str = Field(description="Justification for the discount")
    notes: str = Field(description="Additional pricing considerations")

# Define the pricing agent
pricing_agent = Agent(
    name="pricing_optimizer",
    system_prompt="You are a pricing specialist for our enterprise sales team.",
    user_prompt="""
    Calculate optimal pricing for the following order:
    
    {input}
    
    Determine appropriate pricing and any applicable discounts.
    """,
    output_type=PricingDecision,
    model=Anthropic.claude_3_sonnet
    # Can also use: OpenAI.gpt_4_1
)

@workflow()
async def order_pricing_workflow(order_data: dict):
    # Get customer data
    customer = await get_customer_data(order_data["customer_id"])
    
    # Use agent to determine pricing
    pricing_result = await pricing_agent(
        customer_name=customer.name,
        customer_tier=customer.tier,
        product_id=order_data["product_id"],
        quantity=order_data["quantity"],
        historical_spend=customer.total_spend
    )
    
    # Process the structured output
    return {
        "order_id": order_data["id"],
        "calculated_price": pricing_result.output.price,
        "discount": pricing_result.output.discount_percent,
        "notes": pricing_result.output.notes
    }
```

To share context across tool calls or workflow runs, declare a `tool_context_type`, pass a matching `tool_context` object when calling the agent, and read it inside your tools with `planar.ai.get_tool_context()`. Use the context to expose dependencies like API clients or configuration, and persist any mutable progress through those services rather than mutating the context so durable replays stay consistent.

For more complex agent interactions, you can provide tools and enable multi-turn conversations:

```python
from typing import List, Dict
from pydantic import BaseModel, Field
from planar.workflows import workflow
from planar.ai import Agent

# Define structured output model
class ContractAnalysis(BaseModel):
    risk_areas: List[Dict[str, str]] = Field(
        description="Identified contractual risk areas with clause reference and explanation"
    )
    suggested_changes: List[str] = Field(description="Recommended modifications")
    approval_recommendation: str = Field(
        description="Whether to approve, reject, or escalate the contract"
    )
    explanation: str = Field(description="Reasoning behind the recommendation")

# Tool definitions
def search_contract_clause(contract_id: str, keyword: str) -> List[Dict]:
    """Search for clauses in a contract containing the keyword."""
    # This would normally query a contract management system
    return [{"clause_id": "4.2", "text": "Sample clause text containing " + keyword}]

def get_precedent(clause_type: str) -> str:
    """Retrieve standard precedent language for a given clause type."""
    precedents = {
        "limitation_of_liability": "Liability shall not exceed fees paid in the preceding 12 months.",
        "termination": "Either party may terminate with 30 days written notice.",
    }
    return precedents.get(clause_type, "No precedent found.")

def get_company_requirements(requirement_type: str) -> Dict:
    """Get company requirements for specific contract terms."""
    requirements = {
        "payment_terms": {"min_days": 30, "preferred_days": 45},
        "indemnification": {"required": True, "mutual": "preferred"},
    }
    return requirements.get(requirement_type, {})

# Define multi-turn agent with tools
contract_agent = Agent(
    name="contract_analyzer",
    system_prompt="You are a legal contract analyst for our company.",
    user_prompt="Review the following contract and provide analysis: {contract_summary}",
    tools=[search_contract_clause, get_precedent, get_company_requirements],
    output_type=ContractAnalysis,
    model=OpenAI.gpt_4_turbo,  # Can also use OpenAI.model("gpt-4")
    max_turns=5
)

@workflow()
async def contract_review_workflow(contract_id: str):
    # Get contract data
    contract_data = await get_contract_details(contract_id)
    
    # Use multi-turn agent with tools to analyze contract
    result = await contract_agent(contract_summary=contract_data["summary"])
    
    # Process the analysis
    if result.output.approval_recommendation == "approve":
        return await approve_contract(contract_id, result.output.explanation)
    elif result.output.approval_recommendation == "reject":
        return await reject_contract(contract_id, result.output.explanation)
    else:
        return await escalate_contract(
            contract_id, 
            result.output.risk_areas, 
            result.output.suggested_changes
        )
```

### Rule Steps (Future)

The `@rule` decorator (planned for future releases) will integrate with rules engines to allow domain experts to define and update business rules independently from code.

**Key Features:**

* **External rule definition**: Rules defined in specialized formats (e.g., JDM)
* **Editable in UI**: Domain experts can modify rules through interfaces
* **Typed input/output**: Rules receive and return structured data
* **Versioning**: Support for rule versioning and history

**Planned Example:**

```python
from planar.workflows import workflow
from planar.decisions.decorator import rule

@workflow()
async def pricing_workflow(product_id: str, quantity: int, customer_tier: str):
    # Calculate base price
    base_price = await get_base_price(product_id)
    
    # Apply pricing rules
    final_price = await apply_pricing_rules(
        product_id=product_id,
        base_price=base_price,
        quantity=quantity,
        customer_tier=customer_tier
    )
    
    return {"final_price": final_price}

@rule(
    rules_path="pricing_rules.jdm",
    description="Apply discount rules based on quantity, customer tier, and product"
)
async def apply_pricing_rules(
    product_id: str, 
    base_price: float, 
    quantity: int, 
    customer_tier: str
) -> float:
    # Default implementation if rules engine is unavailable
    if customer_tier == "premium":
        return base_price * quantity * 0.9  # 10% discount
    return base_price * quantity
```

## Waiting Step Types

### Event-based Waiting

The `wait_for_event()` function creates a step that suspends workflow execution until a specific event is emitted by an external system.

**Key Features:**

* **Non-polling**: Efficiently waits for events without consuming resources
* **Timeout support**: Can specify maximum wait time
* **Structured event data**: Events can carry payloads as structured data
* **Integration point**: Perfect for connecting workflows with external systems

**Example:**

```python
from planar.workflows import workflow, step
from planar.workflows.contrib import wait_for_event
from planar.workflows.events import emit_event

@workflow()
async def payment_processing_workflow(order_id: str, amount: float):
    # Initialize payment
    payment_id = await initialize_payment(order_id, amount)
    
    # Wait for payment confirmation
    payment_data = await wait_for_event("payment_confirmed")
    
    # Process payment result
    return await process_payment_result(payment_id, payment_data)

# This would be called from an external system or API endpoint
async def confirm_payment(payment_id: str, status: str):
    # Emit event to resume workflow
    await emit_event(
        event_key="payment_confirmed",
        payload={"payment_id": payment_id, "status": status}
    )
```

### Condition-based Waiting

The `@wait` decorator creates a polling-based waiting step that repeatedly checks a condition until it becomes true or times out.

**Key Features:**

* **Polling interval**: Configurable check frequency
* **Maximum wait time**: Can specify timeout duration
* **Condition function**: Custom logic to determine when to proceed

**Example:**

```python
from planar.workflows import workflow, step
from planar.workflows.contrib import wait

@workflow()
async def order_fulfillment_workflow(order_id: str):
    # Process order
    await process_order(order_id)
    
    # Wait for inventory to be available
    await check_inventory_available(order_id)
    
    # Fulfill order
    return await fulfill_order(order_id)

@wait(poll_interval=300, max_wait_time=86400)  # Check every 5 mins, up to 24 hours
async def check_inventory_available(order_id: str) -> bool:
    # Check if inventory is available
    inventory_status = await get_inventory_status(order_id)
    return inventory_status == "available"
```

## UI-Driven Step Configuration

Decision steps (`Human`, `Agent`, `@rule`) are designed to be editable by non-engineering users through UI interfaces:

1. **Developer-Coded Defaults**
   * Step decorators include default prompts, UI templates, or fallback logic
   * If no UI changes are made, workflows use these defaults

2. **User Overrides**
   * UI interfaces load step metadata (prompt text, UI templates, etc.)
   * Domain users can edit these configurations

3. **Config Persistence**
   * User configurations are persisted in the database
   * At runtime, the workflow engine checks for overrides

4. **Timing Considerations**
   * Developer code is deployed with default behavior
   * Business users configure steps through UI (stored in DB)
   * Next workflow execution applies the updated config
   * If no config is present, default behavior runs

By separating step logic from step configuration, domain users can adapt workflow decisions without redeploying code, while developers maintain typed contracts and stable fallback paths.

## Observability and Monitoring

All step types in Planar are designed to be observable:

* **Execution history**: Complete record of step executions
* **Input/output capture**: Parameters and return values are recorded
* **Timing information**: Duration of each step
* **Error handling**: Detailed error information for failed steps
* **Visual representation**: Timeline view of workflow execution

This observability enables debugging, auditing, and performance optimization of workflows.

## Combined Usage

Workflows often combine multiple step types for complex business processes:

```python
@workflow()
async def customer_onboarding_workflow(customer_data: dict):
    # Process initial data
    customer = await process_customer_data(customer_data)
    
    # Use agent to generate welcome message
    welcome_message = await generate_welcome_message(
        name=customer.name,
        account_type=customer.account_type
    )
    
    # Send welcome email
    email_id = await send_welcome_email(customer.email, welcome_message)
    
    # Wait for email open event
    open_data = await wait_for_event("email_opened")
    
    # Request human review for high-value accounts
    if customer.estimated_value > 10000:
        approval = await request_account_review(
            customer_id=customer.id,
            estimated_value=customer.estimated_value
        )
        if not approval.approved:
            return {"status": "rejected", "reason": approval.reason}
    
    # Complete onboarding
    return await complete_onboarding(customer.id)
```

This example combines basic steps, agent-based content generation, event-based waiting, and human approval in a single workflow.
