"""Tests for the refund processing agent."""
from unitai.mock import MockToolkit

from agent import batch_refund_agent, refund_agent


def test_refund_calls_tools_in_order():
    """Agent must look up the order and check eligibility before processing."""
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"order_id": "123", "status": "delivered", "amount": 49.99})
    toolkit.mock("check_eligibility", return_value={"eligible": True})
    toolkit.mock("process_refund", return_value={"confirmation": "RF-001", "success": True})

    result = toolkit.run_callable(refund_agent, "Refund order 123")

    assert result.tool_called_before("lookup_order", "check_eligibility")
    assert result.tool_called_before("check_eligibility", "process_refund")
    assert result.call_order() == ["lookup_order", "check_eligibility", "process_refund"]


def test_refund_passes_correct_arguments():
    """Agent should pass the order ID and amount to the refund tool."""
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"order_id": "456", "status": "delivered", "amount": 29.99})
    toolkit.mock("check_eligibility", return_value={"eligible": True})
    toolkit.mock("process_refund", return_value={"confirmation": "RF-002", "success": True})

    result = toolkit.run_callable(refund_agent, "Refund order 456")

    call = result.get_call("process_refund", 0)
    assert call.args["order_id"] == "456"
    assert call.args["amount"] == 29.99


def test_refund_output_contains_confirmation():
    """Agent output should include the refund confirmation number and amount."""
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"order_id": "789", "status": "delivered", "amount": 99.00})
    toolkit.mock("check_eligibility", return_value={"eligible": True})
    toolkit.mock("process_refund", return_value={"confirmation": "RF-789", "success": True})

    result = toolkit.run_callable(refund_agent, "Refund order 789")

    assert result.output_contains("RF-789")
    assert result.output_contains("$99.00")


def test_ineligible_order_skips_refund():
    """Agent should not process a refund for ineligible orders."""
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"order_id": "111", "status": "pending", "amount": 15.00})
    toolkit.mock("check_eligibility", return_value={"eligible": False, "reason": "Order not yet delivered"})
    toolkit.mock("process_refund", return_value={"confirmation": "RF-000"})

    result = toolkit.run_callable(refund_agent, "Refund order 111")

    assert result.tool_was_called("lookup_order")
    assert result.tool_was_called("check_eligibility")
    assert result.tool_not_called("process_refund")
    assert result.output_contains("not eligible")


def test_batch_status_check_with_sequence():
    """Agent should check status for multiple orders using sequence mocks."""
    toolkit = MockToolkit()
    toolkit.mock("check_status", sequence=[
        {"order_id": "A1", "status": "shipped"},
        {"order_id": "A2", "status": "delivered"},
        {"order_id": "A3", "status": "processing"},
    ])

    result = toolkit.run_callable(batch_refund_agent, "A1, A2, A3")

    assert result.tool_call_count("check_status", 3)
    assert result.output_contains("shipped")
    assert result.output_contains("delivered")
    assert result.output_contains("processing")
