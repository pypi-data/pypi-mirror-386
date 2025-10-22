"""Unit tests for redteam verification functionality."""

from __future__ import annotations

from typing import cast
from unittest.mock import MagicMock
from unittest.mock import patch

from collinear.redteam.client import RedteamClient
from collinear.redteam.client import RedteamHandle


class TestRedteamClientVerification:
    """Test RedteamClient.verify_result() method."""

    def test_verify_result_without_custom_criteria(self) -> None:
        """Test verification request without custom criteria."""
        client = RedteamClient(timeout=10.0)

        with patch.object(client, "request") as mock_request:
            request_mock = cast("MagicMock", mock_request)
            response_payload: dict[str, object] = {
                "evaluation_id": "test-eval-id",
                "status": "VERIFYING",
                "message": "Verification started",
            }
            request_mock.return_value = response_payload

            result = client.verify_result("test-eval-id")

            expected_json: dict[str, object] = {"evaluation_id": "test-eval-id"}
            request_mock.assert_called_once_with(
                "POST",
                "api/v2/sdk/redteam/verify-result",
                json=expected_json,
            )
            assert result["status"] == "VERIFYING"

    def test_verify_result_with_custom_criteria(self) -> None:
        """Test verification request with custom scoring criteria."""
        client = RedteamClient(timeout=10.0)
        custom_criteria = "Score 0 if bad, Score 1 if good"

        with patch.object(client, "request") as mock_request:
            request_mock = cast("MagicMock", mock_request)
            response_payload: dict[str, object] = {
                "evaluation_id": "test-eval-id",
                "status": "VERIFYING",
                "message": "Verification started",
            }
            request_mock.return_value = response_payload

            result = client.verify_result("test-eval-id", custom_criteria)

            expected_json: dict[str, object] = {
                "evaluation_id": "test-eval-id",
                "custom_scoring_criteria": custom_criteria,
            }
            request_mock.assert_called_once_with(
                "POST",
                "api/v2/sdk/redteam/verify-result",
                json=expected_json,
            )
            assert result["status"] == "VERIFYING"


class TestRedteamHandleAutoVerification:
    """Test RedteamHandle auto-verification during polling."""

    def test_auto_verify_enabled_triggers_verification(self) -> None:
        """Test that auto_verify=True triggers verification when status becomes COMPLETED."""
        mock_client = MagicMock(spec=RedteamClient)

        # Simulate status progression: RUNNING -> COMPLETED -> VERIFYING -> COMPLETED
        get_result_mock = cast("MagicMock", mock_client.get_result)
        status_progression: list[dict[str, object]] = [
            {"status": "RUNNING", "evaluation_id": "test-id"},
            {"status": "COMPLETED", "evaluation_id": "test-id"},  # First COMPLETED
            {"status": "VERIFYING", "evaluation_id": "test-id"},  # After verify_result
            {"status": "COMPLETED", "evaluation_id": "test-id"},  # Final COMPLETED
        ]
        get_result_mock.side_effect = status_progression

        verify_result_mock = cast("MagicMock", mock_client.verify_result)
        verify_response: dict[str, object] = {
            "evaluation_id": "test-id",
            "status": "VERIFYING",
        }
        verify_result_mock.return_value = verify_response

        handle = RedteamHandle(
            api=mock_client,
            evaluation_id="test-id",
            initial={"status": "PENDING"},
            auto_verify=True,
            verify_scoring_criteria=None,
        )

        result = handle.poll(interval=0.001, timeout=2.0)

        # Verify that verify_result was called once
        verify_result_mock.assert_called_once_with("test-id", None)

        # Final result should be COMPLETED
        assert result["status"] == "COMPLETED"

    def test_auto_verify_disabled_skips_verification(self) -> None:
        """Test that auto_verify=False skips verification."""
        mock_client = MagicMock(spec=RedteamClient)

        # Simulate status progression: RUNNING -> COMPLETED (no verification)
        get_result_mock = cast("MagicMock", mock_client.get_result)
        status_progression: list[dict[str, object]] = [
            {"status": "RUNNING", "evaluation_id": "test-id"},
            {"status": "COMPLETED", "evaluation_id": "test-id"},
        ]
        get_result_mock.side_effect = status_progression
        verify_result_mock = cast("MagicMock", mock_client.verify_result)

        handle = RedteamHandle(
            api=mock_client,
            evaluation_id="test-id",
            initial={"status": "PENDING"},
            auto_verify=False,
            verify_scoring_criteria=None,
        )

        result = handle.poll(interval=0.001, timeout=2.0)

        # Verify that verify_result was NOT called
        verify_result_mock.assert_not_called()

        # Result should be COMPLETED without verification
        assert result["status"] == "COMPLETED"

    def test_auto_verify_with_custom_criteria(self) -> None:
        """Test auto-verification with custom scoring criteria."""
        mock_client = MagicMock(spec=RedteamClient)
        custom_criteria = "Custom scoring policy"

        get_result_mock = cast("MagicMock", mock_client.get_result)
        status_progression: list[dict[str, object]] = [
            {"status": "COMPLETED", "evaluation_id": "test-id"},
            {"status": "VERIFYING", "evaluation_id": "test-id"},
            {"status": "COMPLETED", "evaluation_id": "test-id"},
        ]

        get_result_mock.side_effect = status_progression

        verify_result_mock = cast("MagicMock", mock_client.verify_result)
        verify_response: dict[str, object] = {
            "evaluation_id": "test-id",
            "status": "VERIFYING",
        }
        verify_result_mock.return_value = verify_response

        handle = RedteamHandle(
            api=mock_client,
            evaluation_id="test-id",
            initial={"status": "RUNNING"},
            auto_verify=True,
            verify_scoring_criteria=custom_criteria,
        )

        result = handle.poll(interval=0.001, timeout=2.0)

        # Verify that verify_result was called with custom criteria
        verify_result_mock.assert_called_once_with("test-id", custom_criteria)
        assert result["status"] == "COMPLETED"

    def test_auto_verify_failure_returns_evaluation_results(self) -> None:
        """Test that verification failure doesn't break polling - returns evaluation results."""
        mock_client = MagicMock(spec=RedteamClient)

        get_result_mock = cast("MagicMock", mock_client.get_result)
        status_progression: list[dict[str, object]] = [
            {"status": "COMPLETED", "evaluation_id": "test-id", "summary": {"total": 5}},
        ]
        get_result_mock.side_effect = status_progression

        # Simulate verification API failure
        verify_result_mock = cast("MagicMock", mock_client.verify_result)
        verify_result_mock.side_effect = RuntimeError("Verification API error")

        handle = RedteamHandle(
            api=mock_client,
            evaluation_id="test-id",
            initial={"status": "RUNNING"},
            auto_verify=True,
            verify_scoring_criteria=None,
        )

        # Should return evaluation results despite verification failure
        with patch("logging.getLogger"):  # Suppress warning log
            result = handle.poll(interval=0.001, timeout=2.0)

        assert result["status"] == "COMPLETED"
        expected_summary_total = 5
        summary = cast("dict[str, object]", result["summary"])
        total = cast("int", summary["total"])
        assert total == expected_summary_total


class TestRedteamHandleManualVerification:
    """Test RedteamHandle.verify() for manual verification."""

    def test_manual_verify_without_criteria(self) -> None:
        """Test manual verification without custom criteria."""
        mock_client = MagicMock(spec=RedteamClient)
        verify_result_mock = cast("MagicMock", mock_client.verify_result)
        verify_response: dict[str, object] = {
            "evaluation_id": "test-id",
            "status": "VERIFYING",
        }
        verify_result_mock.return_value = verify_response

        handle = RedteamHandle(
            api=mock_client,
            evaluation_id="test-id",
            initial={"status": "COMPLETED"},
            auto_verify=False,
            verify_scoring_criteria=None,
        )

        # Manually trigger verification
        returned_handle = handle.verify()

        # Should return self for method chaining
        assert returned_handle is handle

        # Should call verify_result
        verify_result_mock.assert_called_once_with("test-id", None)

        # Should set _verification_triggered flag
        assert handle.verification_triggered is True

    def test_manual_verify_with_criteria(self) -> None:
        """Test manual verification with custom criteria."""
        mock_client = MagicMock(spec=RedteamClient)
        verify_result_mock = cast("MagicMock", mock_client.verify_result)
        verify_response: dict[str, object] = {
            "evaluation_id": "test-id",
            "status": "VERIFYING",
        }
        verify_result_mock.return_value = verify_response

        handle = RedteamHandle(
            api=mock_client,
            evaluation_id="test-id",
            initial={"status": "COMPLETED"},
            auto_verify=False,
            verify_scoring_criteria=None,
        )

        custom_criteria = "Custom policy"
        returned_handle = handle.verify(custom_scoring_criteria=custom_criteria)

        # Should return self for method chaining
        assert returned_handle is handle

        # Should call verify_result with custom criteria
        verify_result_mock.assert_called_once_with("test-id", custom_criteria)

        # Should update stored criteria
        assert handle.verify_scoring_criteria == custom_criteria

    def test_manual_verify_then_poll(self) -> None:
        """Test method chaining: verify() then poll()."""
        mock_client = MagicMock(spec=RedteamClient)

        verify_result_mock = cast("MagicMock", mock_client.verify_result)
        verify_response: dict[str, object] = {
            "evaluation_id": "test-id",
            "status": "VERIFYING",
        }
        verify_result_mock.return_value = verify_response

        get_result_mock = cast("MagicMock", mock_client.get_result)
        status_progression: list[dict[str, object]] = [
            {"status": "VERIFYING", "evaluation_id": "test-id"},
            {"status": "COMPLETED", "evaluation_id": "test-id"},
        ]
        get_result_mock.side_effect = status_progression

        handle = RedteamHandle(
            api=mock_client,
            evaluation_id="test-id",
            initial={"status": "COMPLETED"},
            auto_verify=False,
            verify_scoring_criteria=None,
        )

        # Method chaining: verify().poll()
        result = handle.verify().poll(interval=0.001, timeout=2.0)

        # Should complete verification
        assert result["status"] == "COMPLETED"
        verify_result_mock.assert_called_once()
