"""Unit tests for CLI utility functions.

Task T032: Tests for retry/backoff, compatibility checking, and logging path resolution.
"""

import json
import logging
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from core.retry import retry, exponential_backoff
from core.compat import check_compat, SemVer
from core.logging_utils import (
    resolve_logs_path,
    setup_project_logging,
    log_cli_request,
    log_cli_response,
    with_logging
)


class TestRetryLogic:
    """Tests for retry and backoff functionality."""

    def test_retry_success_first_attempt(self):
        """Test successful operation on first attempt."""
        mock_func = Mock(return_value="success")

        success, result = retry(mock_func, attempts=3)

        assert success is True
        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_success_after_failures(self):
        """Test successful operation after initial failures."""
        mock_func = Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])

        success, result = retry(mock_func, attempts=3)

        assert success is True
        assert result == "success"
        assert mock_func.call_count == 3

    def test_retry_all_attempts_fail(self):
        """Test when all retry attempts fail."""
        mock_func = Mock(side_effect=Exception("always fails"))

        success, result = retry(mock_func, attempts=3)

        assert success is False
        assert isinstance(result, Exception)
        assert str(result) == "always fails"
        assert mock_func.call_count == 3

    def test_retry_timeout(self):
        """Test retry with timeout."""
        def slow_func():
            time.sleep(0.2)
            return "success"

        # Timeout shorter than function execution
        success, result = retry(slow_func, attempts=3, timeout_s=0.1)

        assert success is False
        # Should have tried once before timeout
        assert result is not None

    def test_exponential_backoff_sequence(self):
        """Test exponential backoff delay sequence."""
        delays = []
        for i in range(4):
            delay = exponential_backoff(i)
            delays.append(delay)

        # Check exponential growth: 0.2, 0.4, 0.8, 1.6
        assert delays[0] == pytest.approx(0.2, rel=0.1)
        assert delays[1] == pytest.approx(0.4, rel=0.1)
        assert delays[2] == pytest.approx(0.8, rel=0.1)
        assert delays[3] == pytest.approx(1.6, rel=0.1)

    def test_exponential_backoff_max_delay(self):
        """Test exponential backoff respects max delay."""
        # Attempt 10 should hit max delay
        delay = exponential_backoff(10, max_delay=1.0)

        assert delay <= 1.0


class TestCompatibility:
    """Tests for version compatibility checking."""

    def test_semver_parse_valid(self):
        """Test parsing valid semantic version strings."""
        v = SemVer.parse("2.3.4")

        assert v.major == 2
        assert v.minor == 3
        assert v.patch == 4

    def test_semver_parse_with_prerelease(self):
        """Test parsing version with prerelease suffix."""
        v = SemVer.parse("1.0.0-beta.1")

        assert v.major == 1
        assert v.minor == 0
        assert v.patch == 0
        # Prerelease info is ignored in simple implementation

    def test_check_compat_same_major_compatible(self):
        """Test same major version is compatible."""
        compatible, message = check_compat("2.0.0", "2.1.0")

        assert compatible is True
        assert message is None

    def test_check_compat_different_major_incompatible(self):
        """Test different major versions are incompatible."""
        compatible, message = check_compat("2.0.0", "3.0.0")

        assert compatible is False
        assert "incompatible" in message.lower()

    def test_check_compat_minor_skew_warning(self):
        """Test minor version skew produces warning."""
        compatible, message = check_compat("2.0.0", "2.2.0")

        assert compatible is True
        assert message is not None
        assert "restricted" in message.lower()

    def test_check_compat_invalid_version(self):
        """Test handling of invalid version strings."""
        compatible, message = check_compat("invalid", "2.0.0")

        # Should be lenient with invalid versions
        assert compatible is True


class TestLoggingUtils:
    """Tests for logging utility functions."""

    def test_resolve_logs_path_default(self):
        """Test logs path resolution with default project root."""
        with patch('core.logging_utils.logs_dir') as mock_logs_dir:
            mock_logs_dir.return_value = Path("/project/.ipc/logs")

            path = resolve_logs_path()

            mock_logs_dir.assert_called_once_with(None)
            assert path == Path("/project/.ipc/logs")

    def test_resolve_logs_path_custom_root(self):
        """Test logs path resolution with custom project root."""
        custom_root = Path("/custom/project")

        with patch('core.logging_utils.logs_dir') as mock_logs_dir:
            mock_logs_dir.return_value = custom_root / ".ipc/logs"

            path = resolve_logs_path(custom_root)

            mock_logs_dir.assert_called_once_with(custom_root)
            assert path == custom_root / ".ipc/logs"

    @patch('core.logging_utils.logging.basicConfig')
    @patch('core.logging_utils.logs_dir')
    def test_setup_project_logging(self, mock_logs_dir, mock_basic_config):
        """Test project logging setup."""
        project_root = Path("/test/project")
        logs_path = project_root / ".ipc/logs"
        mock_logs_dir.return_value = logs_path

        setup_project_logging(project_root, level=logging.DEBUG)

        mock_logs_dir.assert_called_once_with(project_root)
        mock_basic_config.assert_called_once()

        # Check logging configuration
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs['level'] == logging.DEBUG
        assert 'handlers' in call_kwargs

    @patch('core.logging_utils.logger')
    def test_log_cli_request(self, mock_logger):
        """Test CLI request logging."""
        log_cli_request("init", {"verbose": True})

        mock_logger.info.assert_called_once()
        call_arg = mock_logger.info.call_args[0][0]

        # Check log contains required information
        assert "CLI Request" in call_arg
        assert "init" in call_arg
        assert "verbose" in call_arg

    @patch('core.logging_utils.logger')
    def test_log_cli_response_success(self, mock_logger):
        """Test CLI response logging for success."""
        log_cli_response(
            "status",
            success=True,
            duration_ms=15.5,
            result="exit_code=0"
        )

        mock_logger.info.assert_called_once()
        call_arg = mock_logger.info.call_args[0][0]

        assert "CLI Response" in call_arg
        assert "status" in call_arg
        assert "15.5" in str(call_arg)
        assert "exit_code=0" in call_arg

    @patch('core.logging_utils.logger')
    def test_log_cli_response_failure(self, mock_logger):
        """Test CLI response logging for failure."""
        log_cli_response(
            "ping",
            success=False,
            duration_ms=100.0,
            error="Connection timeout"
        )

        mock_logger.error.assert_called_once()
        call_arg = mock_logger.error.call_args[0][0]

        assert "CLI Response" in call_arg
        assert "ping" in call_arg
        assert "Connection timeout" in call_arg

    @patch('core.logging_utils.log_cli_response')
    @patch('core.logging_utils.log_cli_request')
    def test_with_logging_decorator_success(self, mock_request, mock_response):
        """Test logging decorator for successful command."""
        @with_logging("test_command")
        def dummy_command(arg1, arg2=None):
            return 0

        result = dummy_command("value1", arg2="value2")

        assert result == 0
        mock_request.assert_called_once_with("test_command", {"arg2": "value2"})
        mock_response.assert_called_once()

        # Check response call arguments
        response_call_args = mock_response.call_args[1]
        assert response_call_args['success'] is True
        assert response_call_args['result'] == "exit_code=0"

    @patch('core.logging_utils.log_cli_response')
    @patch('core.logging_utils.log_cli_request')
    def test_with_logging_decorator_exception(self, mock_request, mock_response):
        """Test logging decorator for command that raises exception."""
        @with_logging("failing_command")
        def failing_command():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_command()

        mock_request.assert_called_once_with("failing_command", {})
        mock_response.assert_called_once()

        # Check error was logged
        response_call_args = mock_response.call_args[1]
        assert response_call_args['success'] is False
        assert response_call_args['error'] == "Test error"

    def test_log_cli_response_truncates_large_result(self):
        """Test that large results are truncated in logs."""
        with patch('core.logging_utils.logger') as mock_logger:
            # Create a very large result string
            large_result = "x" * 1000

            log_cli_response("test", success=True, result=large_result)

            call_arg = mock_logger.info.call_args[0][0]
            parsed = json.loads(call_arg.replace("CLI Response: ", ""))

            # Check result was truncated
            assert len(parsed['result']) <= 500
            assert parsed['result'].endswith("...")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])