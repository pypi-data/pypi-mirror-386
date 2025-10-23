"""Tests for human-in-the-loop approval system."""

import asyncio

import pytest

from agenticfleet.core.approval import ApprovalDecision, ApprovalRequest, ApprovalResponse
from agenticfleet.core.approved_tools import set_approval_handler
from agenticfleet.core.cli_approval import CLIApprovalHandler, create_approval_request
from agenticfleet.core.code_execution_approval import (
    CodeApprovalOutcome,
    maybe_request_approval_for_code_execution,
)


class MockApprovalHandler(CLIApprovalHandler):
    """Mock approval handler for testing."""

    def __init__(self, decision: ApprovalDecision, modified_code: str | None = None):
        super().__init__(timeout_seconds=1, auto_reject_on_timeout=False)
        self.decision = decision
        self.modified_code = modified_code
        self.requests_received: list[ApprovalRequest] = []

    async def request_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        """Mock approval that returns predefined decision."""
        self.requests_received.append(request)
        response = ApprovalResponse(
            request_id=request.request_id,
            decision=self.decision,
            modified_code=self.modified_code,
            reason=f"Mock {self.decision.value}",
        )
        self._record_approval_history(request, response)
        return response


def test_create_approval_request() -> None:
    """Test creating an approval request."""
    request = create_approval_request(
        operation_type="code_execution",
        agent_name="coder",
        operation="Execute Python code",
        details={"language": "python"},
        code="print('hello')",
    )

    assert request.operation_type == "code_execution"
    assert request.agent_name == "coder"
    assert request.operation == "Execute Python code"
    assert request.details["language"] == "python"
    assert request.code == "print('hello')"
    assert request.request_id  # Should have a UUID


@pytest.mark.asyncio
async def test_mock_approval_handler_approve() -> None:
    """Test mock approval handler with approval decision."""
    handler = MockApprovalHandler(decision=ApprovalDecision.APPROVED)

    request = create_approval_request(
        operation_type="code_execution",
        agent_name="coder",
        operation="Test operation",
        code="print('test')",
    )

    response = await handler.request_approval(request)

    assert response.decision == ApprovalDecision.APPROVED
    assert response.request_id == request.request_id
    assert len(handler.requests_received) == 1


@pytest.mark.asyncio
async def test_mock_approval_handler_reject() -> None:
    """Test mock approval handler with rejection decision."""
    handler = MockApprovalHandler(decision=ApprovalDecision.REJECTED)

    request = create_approval_request(
        operation_type="code_execution",
        agent_name="coder",
        operation="Test operation",
        code="print('test')",
    )

    response = await handler.request_approval(request)

    assert response.decision == ApprovalDecision.REJECTED
    assert response.reason == "Mock rejected"


@pytest.mark.asyncio
async def test_mock_approval_handler_modify() -> None:
    """Test mock approval handler with modification decision."""
    modified_code = "print('modified')"
    handler = MockApprovalHandler(decision=ApprovalDecision.MODIFIED, modified_code=modified_code)

    request = create_approval_request(
        operation_type="code_execution",
        agent_name="coder",
        operation="Test operation",
        code="print('original')",
    )

    response = await handler.request_approval(request)

    assert response.decision == ApprovalDecision.MODIFIED
    assert response.modified_code == modified_code


def test_approval_handler_should_require_approval() -> None:
    """Test the should_require_approval logic."""
    handler = MockApprovalHandler(decision=ApprovalDecision.APPROVED)

    # Should require approval for configured operations
    assert handler.should_require_approval("code_execution", ["code_execution", "file_operations"])
    assert handler.should_require_approval("file_operations", ["code_execution", "file_operations"])

    # Should not require approval for non-configured operations
    assert not handler.should_require_approval("web_search", ["code_execution"])


def test_approval_history() -> None:
    """Test that approval history is tracked."""
    handler = MockApprovalHandler(decision=ApprovalDecision.APPROVED)

    # Initially empty
    assert len(handler.get_approval_history()) == 0

    # Add a request
    request = create_approval_request(operation_type="test", agent_name="test", operation="test")

    # Run async request
    loop = asyncio.get_event_loop()
    loop.run_until_complete(handler.request_approval(request))

    # Check history
    history = handler.get_approval_history()
    assert len(history) == 1
    assert history[0][0] == request
    assert history[0][1].decision == ApprovalDecision.APPROVED


def _reset_handler() -> None:
    """Utility to clear global handler state between tests."""
    set_approval_handler(None)


def test_code_execution_skips_when_not_required() -> None:
    """Code execution should bypass approval when not configured."""
    handler = MockApprovalHandler(decision=ApprovalDecision.APPROVED)
    try:
        set_approval_handler(handler, require_operations=["file_operations"])
        result = maybe_request_approval_for_code_execution("print('test')", "python")
        assert result.outcome == CodeApprovalOutcome.APPROVED
        assert handler.requests_received == []
    finally:
        _reset_handler()


def test_code_execution_requests_when_required() -> None:
    """Code execution should request approval when listed in configuration."""
    handler = MockApprovalHandler(decision=ApprovalDecision.APPROVED)
    try:
        set_approval_handler(handler, require_operations=["code_execution"])
        result = maybe_request_approval_for_code_execution("print('test')", "python")
        assert result.outcome == CodeApprovalOutcome.APPROVED
        assert len(handler.requests_received) == 1
    finally:
        _reset_handler()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
