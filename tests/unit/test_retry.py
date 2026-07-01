"""Tests for retry decorator."""

import pytest

from cube_budget.utils.retry import retry


class TestRetry:
    def test_success_first_attempt(self):
        call_count = 0

        @retry(max_attempts=3, base_delay=0.01)
        def succeeds():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert succeeds() == "ok"
        assert call_count == 1

    def test_success_after_retry(self):
        call_count = 0

        @retry(max_attempts=3, base_delay=0.01, exceptions=(ValueError,))
        def fails_once():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("temporary")
            return "ok"

        assert fails_once() == "ok"
        assert call_count == 2

    def test_exhausted_retries(self):
        @retry(max_attempts=2, base_delay=0.01, exceptions=(RuntimeError,))
        def always_fails():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            always_fails()
