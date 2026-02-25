"""A refund processing agent that follows a multi-step workflow."""


def refund_agent(input: str, tools: dict) -> str:
    """Process a refund request through a multi-step workflow.

    Steps:
    1. Look up the order
    2. Check refund eligibility
    3. Process the refund if eligible
    """
    order_id = _extract_order_id(input)
    if not order_id:
        return "Please provide an order ID to process a refund."

    order = tools["lookup_order"]({"order_id": order_id})
    if not order:
        return f"Order {order_id} not found."

    eligibility = tools["check_eligibility"](
        {"order_id": order_id, "status": order.get("status", "unknown")}
    )

    if not eligibility.get("eligible"):
        return (
            f"Order {order_id} is not eligible for a refund. "
            f"Reason: {eligibility.get('reason', 'unknown')}"
        )

    refund = tools["process_refund"]({
        "order_id": order_id,
        "amount": order.get("amount", 0),
    })

    return (
        f"Refund {refund['confirmation']} for ${order['amount']:.2f} "
        f"has been processed for order {order_id}."
    )


def batch_refund_agent(input: str, tools: dict) -> str:
    """Process refund status checks for multiple orders."""
    order_ids = [oid.strip() for oid in input.split(",")]
    results = []

    for oid in order_ids:
        status = tools["check_status"]({"order_id": oid})
        results.append(f"Order {oid}: {status['status']}")

    return "\n".join(results)


def _extract_order_id(text: str) -> str | None:
    """Extract an order ID from user input."""
    import re

    match = re.search(r"(?:order\s*#?\s*|ORD-?)(\w+)", text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None
