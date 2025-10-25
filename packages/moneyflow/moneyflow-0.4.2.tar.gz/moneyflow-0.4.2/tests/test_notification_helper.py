"""
Unit tests for NotificationHelper.

These tests verify that notification messages are consistent, well-formatted,
and return the correct severity/timeout values.
"""

from moneyflow.notification_helper import NotificationHelper


class TestCommitNotifications:
    """Test commit-related notifications."""

    def test_commit_starting(self):
        msg, severity, timeout = NotificationHelper.commit_starting(15)
        assert "15 change(s)" in msg
        assert "Committing" in msg
        assert severity == "information"
        assert timeout == 2

    def test_commit_success(self):
        msg, severity, timeout = NotificationHelper.commit_success(10)
        assert "10 change(s)" in msg
        assert "✅" in msg
        assert "successfully" in msg
        assert severity == "information"
        assert timeout == 3

    def test_commit_partial(self):
        msg, severity, timeout = NotificationHelper.commit_partial(success=8, failure=2)
        assert "8" in msg
        assert "2" in msg
        assert "failed" in msg
        assert severity == "warning"
        assert timeout == 8

    def test_commit_error(self):
        msg, severity, timeout = NotificationHelper.commit_error("Connection timeout")
        assert "Connection timeout" in msg
        assert "❌" in msg
        assert severity == "error"
        assert timeout == 5

    def test_no_pending_changes(self):
        msg, severity, timeout = NotificationHelper.no_pending_changes()
        assert "No pending changes" in msg
        assert severity == "information"
        assert timeout == 2


class TestSessionNotifications:
    """Test session/auth notifications."""

    def test_session_expired(self):
        msg, severity, timeout = NotificationHelper.session_expired()
        assert "expired" in msg.lower()
        assert "Refreshing" in msg
        assert severity == "warning"
        assert timeout == 2

    def test_session_refreshing(self):
        msg, severity, timeout = NotificationHelper.session_refreshing()
        assert "re-authenticating" in msg
        assert severity == "information"

    def test_session_refresh_success(self):
        msg, severity, timeout = NotificationHelper.session_refresh_success()
        assert "refreshed successfully" in msg
        assert severity == "information"

    def test_session_refresh_failed(self):
        msg, severity, timeout = NotificationHelper.session_refresh_failed("Invalid token")
        assert "Invalid token" in msg
        assert "Failed" in msg
        assert severity == "error"
        assert timeout == 5


class TestRetryNotifications:
    """Test retry logic notifications."""

    def test_retry_waiting(self):
        msg, severity, timeout = NotificationHelper.retry_waiting(
            attempt=1, wait_seconds=120.0, max_retries=5
        )
        assert "120s" in msg
        assert "attempt 2/5" in msg  # attempt is 0-indexed
        assert "Ctrl-C" in msg
        assert "abort" in msg
        assert severity == "warning"
        assert timeout == 120

    def test_retry_waiting_first_attempt(self):
        msg, severity, timeout = NotificationHelper.retry_waiting(0, 60.0)
        assert "attempt 1/5" in msg
        assert "60s" in msg

    def test_retry_cancelled(self):
        msg, severity, timeout = NotificationHelper.retry_cancelled()
        assert "cancelled" in msg
        assert "user" in msg
        assert severity == "warning"


class TestEditNotifications:
    """Test edit operation notifications."""

    def test_edit_queued(self):
        msg, severity, timeout = NotificationHelper.edit_queued(25)
        assert "25 edits" in msg
        assert "Press w" in msg
        assert severity == "information"

    def test_merchant_changed(self):
        msg, severity, timeout = NotificationHelper.merchant_changed()
        assert "Merchant changed" in msg
        assert "Press w" in msg
        assert severity == "information"

    def test_category_changed(self):
        msg, severity, timeout = NotificationHelper.category_changed()
        assert "Category changed" in msg
        assert "Press w" in msg

    def test_bulk_edit_category_queued(self):
        msg, severity, timeout = NotificationHelper.bulk_edit_category_queued(
            50, "Food & Dining", "Groceries"
        )
        assert "50 transactions" in msg
        assert "Food & Dining" in msg
        assert "Groceries" in msg
        assert "→" in msg

    def test_hide_toggled(self):
        msg, severity, timeout = NotificationHelper.hide_toggled("Hidden")
        assert "Hidden from reports" in msg
        assert "Press w" in msg

    def test_hide_toggled_bulk(self):
        msg, severity, timeout = NotificationHelper.hide_toggled_bulk(10)
        assert "10 transactions" in msg
        assert "Toggled" in msg


class TestNavigationNotifications:
    """Test navigation and view change notifications."""

    def test_view_changed(self):
        msg, severity, timeout = NotificationHelper.view_changed("Merchants")
        assert "Merchants" in msg
        assert "Viewing" in msg
        assert timeout == 1

    def test_sort_changed(self):
        msg, severity, timeout = NotificationHelper.sort_changed("Amount")
        assert "Amount" in msg
        assert "Sorting" in msg

    def test_sort_direction_changed(self):
        msg, severity, timeout = NotificationHelper.sort_direction_changed("Descending")
        assert "Descending" in msg
        assert "Sort" in msg

    def test_time_period_changed(self):
        msg, severity, timeout = NotificationHelper.time_period_changed("October 2025")
        assert "October 2025" in msg
        assert "Viewing" in msg

    def test_all_transactions_view(self):
        msg, severity, timeout = NotificationHelper.all_transactions_view()
        assert "all transactions" in msg.lower()
        assert "ungrouped" in msg.lower()
        assert severity == "information"


class TestSelectionNotifications:
    """Test selection notifications."""

    def test_selected_count_single(self):
        msg, severity, timeout = NotificationHelper.selected_count(1)
        assert "1 transaction(s)" in msg
        assert "Selected" in msg

    def test_selected_count_multiple(self):
        msg, severity, timeout = NotificationHelper.selected_count(15)
        assert "15 transaction(s)" in msg


class TestSearchAndFilterNotifications:
    """Test search and filter notifications."""

    def test_search_results(self):
        msg, severity, timeout = NotificationHelper.search_results("Amazon", 42)
        assert "Amazon" in msg
        assert "42 results" in msg

    def test_search_cleared(self):
        msg, severity, timeout = NotificationHelper.search_cleared()
        assert "cleared" in msg

    def test_filters_applied(self):
        msg, severity, timeout = NotificationHelper.filters_applied(
            ["hidden items shown", "transfers excluded"]
        )
        assert "hidden items shown" in msg
        assert "transfers excluded" in msg


class TestDuplicateNotifications:
    """Test duplicate detection notifications."""

    def test_duplicates_found(self):
        msg, severity, timeout = NotificationHelper.duplicates_found(5)
        assert "5" in msg
        assert "duplicates" in msg

    def test_no_duplicates(self):
        msg, severity, timeout = NotificationHelper.no_duplicates()
        assert "✅" in msg
        assert "No duplicates" in msg

    def test_scanning_duplicates(self):
        msg, severity, timeout = NotificationHelper.scanning_duplicates()
        assert "Scanning" in msg

    def test_no_transactions_to_check(self):
        msg, severity, timeout = NotificationHelper.no_transactions_to_check()
        assert "No transactions" in msg


class TestErrorNotifications:
    """Test error and warning notifications."""

    def test_operation_not_available(self):
        msg, severity, timeout = NotificationHelper.operation_not_available(
            "Delete only works in transaction detail view"
        )
        assert "Delete only works" in msg
        assert severity == "information"

    def test_transaction_deleted(self):
        msg, severity, timeout = NotificationHelper.transaction_deleted()
        assert "deleted" in msg

    def test_delete_error(self):
        msg, severity, timeout = NotificationHelper.delete_error("Not found")
        assert "Not found" in msg
        assert severity == "error"

    def test_refresh_needed(self):
        msg, severity, timeout = NotificationHelper.refresh_needed()
        assert "Ctrl+L" in msg


class TestTupleStructure:
    """Test that all notifications return proper tuple structure."""

    def test_all_methods_return_three_element_tuple(self):
        """Ensure all notification methods return (str, str, int)."""
        # Get all static methods
        [
            getattr(NotificationHelper, method)
            for method in dir(NotificationHelper)
            if not method.startswith("_") and callable(getattr(NotificationHelper, method))
        ]

        # Test a few representative ones
        test_cases = [
            (NotificationHelper.commit_success, (10,)),
            (NotificationHelper.session_expired, ()),
            (NotificationHelper.retry_waiting, (1, 60.0)),
            (NotificationHelper.edit_queued, (5,)),
        ]

        for method, args in test_cases:
            result = method(*args)
            assert isinstance(result, tuple), f"{method.__name__} didn't return tuple"
            assert len(result) == 3, f"{method.__name__} didn't return 3-tuple"
            msg, severity, timeout = result
            assert isinstance(msg, str), f"{method.__name__} message not string"
            assert severity in ("information", "warning", "error"), (
                f"{method.__name__} invalid severity: {severity}"
            )
            assert isinstance(timeout, int), f"{method.__name__} timeout not int"
            assert timeout > 0, f"{method.__name__} timeout not positive"


class TestMessageQuality:
    """Test notification message quality and consistency."""

    def test_success_messages_use_checkmark(self):
        """Success messages should use ✅ emoji."""
        success_messages = [
            NotificationHelper.commit_success(1)[0],
            NotificationHelper.no_duplicates()[0],
        ]
        for msg in success_messages:
            assert "✅" in msg, f"Success message missing checkmark: {msg}"

    def test_error_messages_use_x(self):
        """Error messages should use ❌ emoji."""
        error_messages = [
            NotificationHelper.commit_error("test")[0],
            NotificationHelper.commit_partial(1, 1)[0],
        ]
        for msg in error_messages:
            assert "❌" in msg, f"Error message missing X: {msg}"

    def test_warning_messages_use_warning_emoji(self):
        """Warning messages should use ⚠ emoji when appropriate."""
        msg = NotificationHelper.retry_waiting(1, 60.0)[0]
        assert "⚠" in msg

    def test_action_prompts_mention_key(self):
        """Messages prompting action should mention the key."""
        action_messages = [
            NotificationHelper.merchant_changed()[0],
            NotificationHelper.edit_queued(1)[0],
            NotificationHelper.refresh_needed()[0],
        ]
        for msg in action_messages:
            # Should mention a key or keyboard shortcut
            assert any(key in msg for key in ["Press", "w", "Ctrl"]), (
                f"Action message doesn't mention key: {msg}"
            )
