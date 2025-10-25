"""
Unit tests for ModalHelper.

These tests verify that modal parameter preparation logic is correct
and can be tested without requiring the UI to be running.
"""

from datetime import datetime

import polars as pl

from moneyflow.modal_helper import ModalHelper
from moneyflow.state import TransactionEdit


class TestEditMerchantParams:
    """Test parameters for Edit Merchant modal."""

    def test_basic_params(self):
        params = ModalHelper.edit_merchant_params(
            merchant_name="Amazon",
            transaction_count=5,
            all_merchants=["Amazon", "Walmart", "Target"],
        )

        assert params["current_merchant"] == "Amazon"
        assert params["transaction_count"] == 5
        assert params["all_merchants"] == ["Amazon", "Walmart", "Target"]
        assert "bulk_summary" not in params
        assert "txn_details" not in params

    def test_with_bulk_summary(self):
        params = ModalHelper.edit_merchant_params(
            merchant_name="Amazon",
            transaction_count=15,
            all_merchants=["Amazon"],
            bulk_summary={"total_amount": -250.50},
        )

        assert params["bulk_summary"]["total_amount"] == -250.50

    def test_with_txn_details(self):
        params = ModalHelper.edit_merchant_params(
            merchant_name="Amazon",
            transaction_count=1,
            all_merchants=["Amazon"],
            txn_details={"date": "2025-10-14", "amount": -42.99, "category": "Shopping"},
        )

        assert params["txn_details"]["date"] == "2025-10-14"
        assert params["txn_details"]["amount"] == -42.99
        assert params["txn_details"]["category"] == "Shopping"

    def test_both_bulk_and_details(self):
        """Can include both bulk summary and transaction details."""
        params = ModalHelper.edit_merchant_params(
            merchant_name="Test",
            transaction_count=1,
            all_merchants=["Test"],
            bulk_summary={"total_amount": -100.0},
            txn_details={"date": "2025-10-14", "amount": -100.0},
        )

        assert "bulk_summary" in params
        assert "txn_details" in params


class TestSelectCategoryParams:
    """Test parameters for Category Selection modal."""

    def test_basic_params(self):
        categories = {
            "cat_1": {"name": "Groceries", "group": "Food"},
            "cat_2": {"name": "Gas", "group": "Automotive"},
        }

        params = ModalHelper.select_category_params(categories)

        assert params["categories"] == categories
        assert params["current_category_id"] is None
        assert "txn_details" not in params

    def test_with_current_category(self):
        categories = {"cat_1": {"name": "Groceries"}}

        params = ModalHelper.select_category_params(categories, current_category_id="cat_1")

        assert params["current_category_id"] == "cat_1"

    def test_with_txn_details(self):
        params = ModalHelper.select_category_params(
            categories={},
            current_category_id="cat_1",
            txn_details={"date": "2025-10-14", "amount": -25.0, "merchant": "Safeway"},
        )

        assert params["txn_details"]["merchant"] == "Safeway"


class TestReviewChangesParams:
    """Test parameters for Review Changes modal."""

    def test_basic_params(self):
        edits = [
            TransactionEdit("txn_1", "merchant", "Old", "New", datetime.now()),
            TransactionEdit("txn_2", "category", "cat_1", "cat_2", datetime.now()),
        ]
        categories = {"cat_1": {"name": "Food"}, "cat_2": {"name": "Gas"}}

        params = ModalHelper.review_changes_params(edits, categories)

        assert params["edits"] == edits
        assert params["categories"] == categories


class TestDeleteConfirmationParams:
    """Test parameters for Delete Confirmation modal."""

    def test_default_single_transaction(self):
        params = ModalHelper.delete_confirmation_params()
        assert params["transaction_count"] == 1

    def test_multiple_transactions(self):
        params = ModalHelper.delete_confirmation_params(transaction_count=10)
        assert params["transaction_count"] == 10


class TestQuitConfirmationParams:
    """Test parameters for Quit Confirmation modal."""

    def test_with_unsaved_changes(self):
        params = ModalHelper.quit_confirmation_params(has_unsaved_changes=True)
        assert params["has_unsaved_changes"] is True

    def test_without_unsaved_changes(self):
        params = ModalHelper.quit_confirmation_params(has_unsaved_changes=False)
        assert params["has_unsaved_changes"] is False


class TestFilterParams:
    """Test parameters for Filter Settings modal."""

    def test_basic_params(self):
        params = ModalHelper.filter_params(show_transfers=True, show_hidden=False)

        assert params["show_transfers"] is True
        assert params["show_hidden"] is False


class TestSearchParams:
    """Test parameters for Search modal."""

    def test_default_empty_query(self):
        params = ModalHelper.search_params()
        assert params["current_query"] == ""

    def test_with_existing_query(self):
        params = ModalHelper.search_params(current_query="Amazon")
        assert params["current_query"] == "Amazon"


class TestCachePromptParams:
    """Test parameters for Cache Prompt modal."""

    def test_basic_params(self):
        params = ModalHelper.cache_prompt_params(
            age="2 hours ago", transaction_count=1500, filter_desc="All transactions"
        )

        assert params["age"] == "2 hours ago"
        assert params["transaction_count"] == 1500
        assert params["filter_desc"] == "All transactions"


class TestTransactionDetailParams:
    """Test parameters for Transaction Detail modal."""

    def test_basic_params(self):
        txn = {
            "id": "txn_123",
            "date": "2025-10-14",
            "merchant": "Starbucks",
            "amount": -5.75,
            "category": "Coffee Shops",
        }

        params = ModalHelper.transaction_detail_params(txn)

        assert params["transaction"] == txn


class TestDuplicatesParams:
    """Test parameters for Duplicates modal."""

    def test_basic_params(self):
        duplicates_df = pl.DataFrame(
            {
                "id": ["txn_1", "txn_2"],
                "amount": [-100.0, -100.0],
            }
        )

        all_txns_df = pl.DataFrame(
            {
                "id": ["txn_1", "txn_2", "txn_3"],
                "amount": [-100.0, -100.0, -50.0],
            }
        )

        groups = [["txn_1", "txn_2"]]

        params = ModalHelper.duplicates_params(duplicates_df, groups, all_txns_df)

        assert params["duplicates"].equals(duplicates_df)
        assert params["groups"] == groups
        assert params["all_transactions"].equals(all_txns_df)


class TestParameterTypeConsistency:
    """Test that parameter dictionaries have correct types."""

    def test_all_methods_return_dict(self):
        """All helper methods should return dictionaries."""
        test_cases = [
            (ModalHelper.edit_merchant_params, ("Amazon", 1, ["Amazon"])),
            (ModalHelper.select_category_params, ({"cat_1": {"name": "Food"}},)),
            (ModalHelper.delete_confirmation_params, ()),
            (ModalHelper.quit_confirmation_params, (True,)),
            (ModalHelper.filter_params, (True, False)),
            (ModalHelper.search_params, ()),
        ]

        for method, args in test_cases:
            result = method(*args)
            assert isinstance(result, dict), f"{method.__name__} didn't return dict"
            assert len(result) > 0, f"{method.__name__} returned empty dict"


class TestRealWorldScenarios:
    """Test modal params for real-world usage scenarios."""

    def test_bulk_merchant_edit_from_aggregate(self):
        """Scenario: User presses 'm' on merchant in aggregate view."""
        all_merchants = ["Amazon", "AMZN*123", "AMZ*456", "Walmart"]

        params = ModalHelper.edit_merchant_params(
            merchant_name="AMZN*123",
            transaction_count=25,
            all_merchants=all_merchants,
            bulk_summary={"total_amount": -1250.75},
        )

        # Should have all required fields for bulk edit
        assert params["current_merchant"] == "AMZN*123"
        assert params["transaction_count"] == 25
        assert params["bulk_summary"]["total_amount"] == -1250.75
        assert "Amazon" in params["all_merchants"]

    def test_single_transaction_edit_with_context(self):
        """Scenario: User presses 'm' on single transaction."""
        params = ModalHelper.edit_merchant_params(
            merchant_name="Starbucks",
            transaction_count=1,
            all_merchants=["Starbucks", "Starbucks Coffee"],
            txn_details={"date": "2025-10-14", "amount": -6.50, "category": "Coffee Shops"},
        )

        # Should provide context for single edit
        assert params["transaction_count"] == 1
        assert params["txn_details"]["amount"] == -6.50

    def test_review_before_commit(self):
        """Scenario: User presses 'w' to review 10 pending edits."""
        edits = [
            TransactionEdit(f"txn_{i}", "merchant", "Old", "New", datetime.now()) for i in range(10)
        ]
        categories = {"cat_1": {"name": "Groceries", "group": "Food"}}

        params = ModalHelper.review_changes_params(edits, categories)

        assert len(params["edits"]) == 10
        assert "cat_1" in params["categories"]

    def test_quit_with_pending_changes(self):
        """Scenario: User presses 'q' with 5 pending changes."""
        params = ModalHelper.quit_confirmation_params(has_unsaved_changes=True)

        # Should indicate unsaved changes
        assert params["has_unsaved_changes"] is True
