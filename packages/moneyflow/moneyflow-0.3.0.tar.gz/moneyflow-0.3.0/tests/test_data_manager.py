"""
Tests for DataManager operations including aggregation, filtering, and API integration.
"""

from datetime import datetime

import polars as pl

from moneyflow.data_manager import DataManager
from moneyflow.state import TransactionEdit


class TestDataFetching:
    """Test data fetching from API."""

    async def test_fetch_all_data(self, data_manager):
        """Test fetching all transactions and metadata."""
        df, categories, category_groups = await data_manager.fetch_all_data()

        assert df is not None
        assert len(df) > 0
        assert isinstance(df, pl.DataFrame)
        assert len(categories) > 0
        assert len(category_groups) > 0

    async def test_fetch_with_date_filter(self, data_manager):
        """Test fetching with date range."""
        df, _, _ = await data_manager.fetch_all_data(start_date="2024-10-01", end_date="2024-10-03")

        assert df is not None
        # Should have filtered transactions
        dates = df["date"].to_list()
        for d in dates:
            assert d.year == 2024
            assert d.month == 10
            assert 1 <= d.day <= 3


class TestAggregation:
    """Test data aggregation functions."""

    async def test_aggregate_by_merchant(self, loaded_data_manager):
        """Test merchant aggregation."""
        dm, df, _, _ = loaded_data_manager

        agg = dm.aggregate_by_merchant(df)

        assert len(agg) > 0
        assert "merchant" in agg.columns
        assert "count" in agg.columns
        assert "total" in agg.columns

        # Note: Sorting is now handled by app.py, not by aggregate methods
        # The aggregation just returns grouped data

    async def test_aggregate_by_category(self, loaded_data_manager):
        """Test category aggregation."""
        dm, df, _, _ = loaded_data_manager

        agg = dm.aggregate_by_category(df)

        assert len(agg) > 0
        assert "category" in agg.columns
        assert "count" in agg.columns
        assert "total" in agg.columns
        assert "group" in agg.columns

    async def test_aggregate_by_group(self, loaded_data_manager):
        """Test group aggregation."""
        dm, df, _, _ = loaded_data_manager

        agg = dm.aggregate_by_group(df)

        assert len(agg) > 0
        assert "group" in agg.columns
        assert "count" in agg.columns
        assert "total" in agg.columns

    async def test_aggregate_empty_dataframe(self, data_manager):
        """Test aggregation on empty DataFrame."""
        empty_df = pl.DataFrame()

        agg_merchant = data_manager.aggregate_by_merchant(empty_df)
        agg_category = data_manager.aggregate_by_category(empty_df)
        agg_group = data_manager.aggregate_by_group(empty_df)

        assert agg_merchant.is_empty()
        assert agg_category.is_empty()
        assert agg_group.is_empty()


class TestFiltering:
    """Test data filtering operations."""

    async def test_filter_by_merchant(self, loaded_data_manager):
        """Test filtering by merchant name."""
        dm, df, _, _ = loaded_data_manager

        # Filter by a merchant we know exists
        filtered = dm.filter_by_merchant(df, "Whole Foods")

        assert len(filtered) > 0
        merchants = filtered["merchant"].unique().to_list()
        assert merchants == ["Whole Foods"]

    async def test_filter_by_category(self, loaded_data_manager):
        """Test filtering by category name."""
        dm, df, _, _ = loaded_data_manager

        filtered = dm.filter_by_category(df, "Groceries")

        assert len(filtered) > 0
        categories = filtered["category"].unique().to_list()
        assert categories == ["Groceries"]

    async def test_filter_by_group(self, loaded_data_manager):
        """Test filtering by group name."""
        dm, df, _, _ = loaded_data_manager

        filtered = dm.filter_by_group(df, "Food & Dining")

        assert len(filtered) > 0
        groups = filtered["group"].unique().to_list()
        assert groups == ["Food & Dining"]

    async def test_search_transactions(self, loaded_data_manager):
        """Test search functionality."""
        dm, df, _, _ = loaded_data_manager

        # Search for "starbucks"
        results = dm.search_transactions(df, "starbucks")

        assert len(results) > 0
        # All results should contain "starbucks" in merchant, category, or notes
        for row in results.iter_rows(named=True):
            text = f"{row['merchant']} {row['category']} {row['notes']}".lower()
            assert "starbucks" in text

    async def test_search_empty_query(self, loaded_data_manager):
        """Test search with empty query returns all."""
        dm, df, _, _ = loaded_data_manager

        results = dm.search_transactions(df, "")

        assert len(results) == len(df)


class TestCommitEdits:
    """Test committing pending edits to the API."""

    async def test_commit_single_edit(self, data_manager, mock_mm):
        """Test committing a single edit."""
        edits = [TransactionEdit("txn_1", "merchant", "Old Name", "New Name", datetime.now())]

        success, failure = await data_manager.commit_pending_edits(edits)

        assert success == 1
        assert failure == 0
        assert len(mock_mm.update_calls) == 1

        # Verify the update call
        call = mock_mm.update_calls[0]
        assert call["transaction_id"] == "txn_1"
        assert call["merchant_name"] == "New Name"

    async def test_commit_multiple_edits(self, data_manager, mock_mm):
        """Test committing multiple edits."""
        edits = [
            TransactionEdit("txn_1", "merchant", "A", "B", datetime.now()),
            TransactionEdit("txn_2", "category", "cat_old", "cat_new", datetime.now()),
            TransactionEdit("txn_3", "hide_from_reports", False, True, datetime.now()),
        ]

        success, failure = await data_manager.commit_pending_edits(edits)

        assert success == 3
        assert failure == 0
        assert len(mock_mm.update_calls) == 3

    async def test_commit_empty_edits(self, data_manager, mock_mm):
        """Test committing with no edits."""
        success, failure = await data_manager.commit_pending_edits([])

        assert success == 0
        assert failure == 0
        assert len(mock_mm.update_calls) == 0

    async def test_commit_merchant_rename(self, data_manager, mock_mm):
        """Test committing a merchant rename."""
        edits = [TransactionEdit("txn_1", "merchant", "Amazon.com", "Amazon", datetime.now())]

        await data_manager.commit_pending_edits(edits)

        # Verify the transaction was updated in mock backend
        txn = mock_mm.get_transaction_by_id("txn_1")
        assert txn is not None
        assert txn["merchant"]["name"] == "Amazon"

    async def test_commit_category_change(self, data_manager, mock_mm):
        """Test committing a category change."""
        edits = [
            TransactionEdit("txn_1", "category", "cat_groceries", "cat_shopping", datetime.now())
        ]

        await data_manager.commit_pending_edits(edits)

        # Verify the transaction was updated
        txn = mock_mm.get_transaction_by_id("txn_1")
        assert txn is not None
        assert txn["category"]["id"] == "cat_shopping"

    async def test_commit_hide_toggle(self, data_manager, mock_mm):
        """Test committing hide from reports toggle."""
        edits = [TransactionEdit("txn_1", "hide_from_reports", False, True, datetime.now())]

        await data_manager.commit_pending_edits(edits)

        # Verify the transaction was updated
        txn = mock_mm.get_transaction_by_id("txn_1")
        assert txn is not None
        assert txn["hideFromReports"] is True


class TestCategoryGroupMapping:
    """Test category to group mapping."""

    def test_category_mapping_exists(self, data_manager):
        """Test that category to group mapping is initialized."""
        assert len(data_manager.category_to_group) > 0

    def test_groceries_mapped_to_food(self, data_manager):
        """Test that Groceries maps to Food & Dining."""
        assert data_manager.category_to_group.get("Groceries") == "Food & Dining"

    def test_gas_mapped_to_automotive(self, data_manager):
        """Test that Gas maps to Automotive."""
        assert data_manager.category_to_group.get("Gas") == "Automotive"

    async def test_transactions_have_groups(self, loaded_data_manager):
        """Test that loaded transactions have group field."""
        dm, df, _, _ = loaded_data_manager

        assert "group" in df.columns
        groups = df["group"].unique().to_list()
        assert len(groups) > 0
        assert all(g is not None for g in groups)


class TestEdgeCases:
    """Test edge cases and malformed data handling."""

    async def test_transactions_to_dataframe_empty_list(self, data_manager):
        """Test converting empty transaction list to DataFrame."""
        df = data_manager._transactions_to_dataframe([], {})

        assert df is not None
        assert df.is_empty()

    async def test_transactions_to_dataframe_none_merchant(self, data_manager):
        """Test transaction with None merchant field."""
        transactions = [
            {
                "id": "txn_1",
                "date": "2024-10-01",
                "amount": -50.00,
                "merchant": None,  # None merchant
                "category": {"id": "cat_1", "name": "Groceries"},
                "account": {"id": "acc_1", "displayName": "Checking"},
                "notes": "test",
                "hideFromReports": False,
                "pending": False,
                "isRecurring": False,
            }
        ]

        df = data_manager._transactions_to_dataframe(transactions, {})

        assert len(df) == 1
        assert df["merchant"][0] == "Unknown"

    async def test_transactions_to_dataframe_empty_merchant_name(self, data_manager):
        """Test transaction with empty merchant name."""
        transactions = [
            {
                "id": "txn_1",
                "date": "2024-10-01",
                "amount": -50.00,
                "merchant": {"id": "merch_1", "name": ""},  # Empty name
                "category": {"id": "cat_1", "name": "Groceries"},
                "account": {"id": "acc_1", "displayName": "Checking"},
                "notes": None,
                "hideFromReports": False,
                "pending": False,
                "isRecurring": False,
            }
        ]

        df = data_manager._transactions_to_dataframe(transactions, {})

        assert len(df) == 1
        assert df["merchant"][0] == "Unknown"

    async def test_transactions_to_dataframe_none_category(self, data_manager):
        """Test transaction with None category field."""
        transactions = [
            {
                "id": "txn_1",
                "date": "2024-10-01",
                "amount": -50.00,
                "merchant": {"id": "merch_1", "name": "Store"},
                "category": None,  # None category
                "account": {"id": "acc_1", "displayName": "Checking"},
                "notes": "",
                "hideFromReports": False,
                "pending": False,
                "isRecurring": False,
            }
        ]

        df = data_manager._transactions_to_dataframe(transactions, {})
        # Apply grouping (now done separately)
        df = data_manager.apply_category_groups(df)

        assert len(df) == 1
        assert df["category"][0] == "Uncategorized"
        assert df["group"][0] == "Uncategorized"

    async def test_transactions_to_dataframe_empty_category_name(self, data_manager):
        """Test transaction with empty category name."""
        transactions = [
            {
                "id": "txn_1",
                "date": "2024-10-01",
                "amount": -50.00,
                "merchant": {"id": "merch_1", "name": "Store"},
                "category": {"id": "cat_1", "name": ""},  # Empty name
                "account": {"id": "acc_1", "displayName": "Checking"},
                "notes": "",
                "hideFromReports": False,
                "pending": False,
                "isRecurring": False,
            }
        ]

        df = data_manager._transactions_to_dataframe(transactions, {})

        assert len(df) == 1
        assert df["category"][0] == "Uncategorized"

    async def test_transactions_to_dataframe_none_account(self, data_manager):
        """Test transaction with None account field."""
        transactions = [
            {
                "id": "txn_1",
                "date": "2024-10-01",
                "amount": -50.00,
                "merchant": {"id": "merch_1", "name": "Store"},
                "category": {"id": "cat_1", "name": "Groceries"},
                "account": None,  # None account
                "notes": "",
                "hideFromReports": False,
                "pending": False,
                "isRecurring": False,
            }
        ]

        df = data_manager._transactions_to_dataframe(transactions, {})

        assert len(df) == 1
        assert df["account"][0] == ""

    async def test_transactions_to_dataframe_empty_account_name(self, data_manager):
        """Test transaction with empty account display name."""
        transactions = [
            {
                "id": "txn_1",
                "date": "2024-10-01",
                "amount": -50.00,
                "merchant": {"id": "merch_1", "name": "Store"},
                "category": {"id": "cat_1", "name": "Groceries"},
                "account": {"id": "acc_1", "displayName": ""},  # Empty name
                "notes": "",
                "hideFromReports": False,
                "pending": False,
                "isRecurring": False,
            }
        ]

        df = data_manager._transactions_to_dataframe(transactions, {})

        assert len(df) == 1
        assert df["account"][0] == ""

    async def test_transactions_to_dataframe_none_notes(self, data_manager):
        """Test transaction with None notes field."""
        transactions = [
            {
                "id": "txn_1",
                "date": "2024-10-01",
                "amount": -50.00,
                "merchant": {"id": "merch_1", "name": "Store"},
                "category": {"id": "cat_1", "name": "Groceries"},
                "account": {"id": "acc_1", "displayName": "Checking"},
                "notes": None,  # None notes
                "hideFromReports": False,
                "pending": False,
                "isRecurring": False,
            }
        ]

        df = data_manager._transactions_to_dataframe(transactions, {})

        assert len(df) == 1
        assert df["notes"][0] == ""

    async def test_transactions_to_dataframe_missing_optional_fields(self, data_manager):
        """Test transaction with missing optional fields."""
        transactions = [
            {
                "id": "txn_1",
                "date": "2024-10-01",
                "amount": -50.00,
                "merchant": {"id": "merch_1", "name": "Store"},
                "category": {"id": "cat_1", "name": "Groceries"},
                "account": {"id": "acc_1", "displayName": "Checking"},
                # Missing notes, hideFromReports, pending, isRecurring
            }
        ]

        df = data_manager._transactions_to_dataframe(transactions, {})

        assert len(df) == 1
        assert df["notes"][0] == ""
        assert df["hideFromReports"][0] is False
        assert df["pending"][0] is False
        assert df["isRecurring"][0] is False

    async def test_transactions_to_dataframe_unknown_category_group(self, data_manager):
        """Test transaction with category not in group mapping."""
        transactions = [
            {
                "id": "txn_1",
                "date": "2024-10-01",
                "amount": -50.00,
                "merchant": {"id": "merch_1", "name": "Store"},
                "category": {"id": "cat_unknown", "name": "Unknown Category XYZ"},
                "account": {"id": "acc_1", "displayName": "Checking"},
                "notes": "",
                "hideFromReports": False,
                "pending": False,
                "isRecurring": False,
            }
        ]

        df = data_manager._transactions_to_dataframe(transactions, {})
        # Apply grouping (now done separately)
        df = data_manager.apply_category_groups(df)

        assert len(df) == 1
        assert df["group"][0] == "Uncategorized"


class TestGetStats:
    """Test get_stats() method with various DataFrame states."""

    async def test_get_stats_with_none_df(self, data_manager):
        """Test get_stats when df is None."""
        data_manager.df = None

        stats = data_manager.get_stats()

        assert stats["total_transactions"] == 0
        assert stats["total_income"] == 0.0
        assert stats["total_expenses"] == 0.0
        assert stats["net_savings"] == 0.0
        assert stats["pending_changes"] == 0

    async def test_get_stats_with_empty_df(self, data_manager):
        """Test get_stats with empty DataFrame."""
        data_manager.df = pl.DataFrame()

        stats = data_manager.get_stats()

        assert stats["total_transactions"] == 0
        assert stats["total_income"] == 0.0
        assert stats["total_expenses"] == 0.0
        assert stats["net_savings"] == 0.0
        assert stats["pending_changes"] == 0

    async def test_get_stats_with_data(self, loaded_data_manager):
        """Test get_stats with actual data."""
        dm, df, _, _ = loaded_data_manager
        dm.df = df

        stats = dm.get_stats()

        assert stats["total_transactions"] == len(df)
        # Stats now return income/expenses/savings breakdown
        assert "total_income" in stats
        assert "total_expenses" in stats
        assert "net_savings" in stats
        assert stats["pending_changes"] == 0

    async def test_get_stats_with_pending_edits(self, loaded_data_manager):
        """Test get_stats with pending edits."""
        dm, df, _, _ = loaded_data_manager
        dm.df = df
        dm.pending_edits = [
            TransactionEdit("txn_1", "merchant", "A", "B", datetime.now()),
            TransactionEdit("txn_2", "category", "C", "D", datetime.now()),
        ]

        stats = dm.get_stats()

        assert stats["total_transactions"] == len(df)
        assert stats["pending_changes"] == 2


class TestProgressCallbacks:
    """Test progress callback functionality."""

    async def test_fetch_all_data_with_progress_callback(self, data_manager):
        """Test fetch_all_data calls progress callback."""
        progress_messages = []

        def progress_callback(msg: str):
            progress_messages.append(msg)

        await data_manager.fetch_all_data(progress_callback=progress_callback)

        # Verify progress callbacks were made
        assert len(progress_messages) > 0
        assert any("Fetching categories" in msg for msg in progress_messages)
        assert any("Fetching transactions" in msg for msg in progress_messages)
        assert any("Processing transactions" in msg for msg in progress_messages)

    async def test_fetch_all_data_without_progress_callback(self, data_manager):
        """Test fetch_all_data works without progress callback."""
        df, categories, category_groups = await data_manager.fetch_all_data()

        assert df is not None
        assert len(df) > 0
        assert len(categories) > 0
        assert len(category_groups) > 0


class TestCommitEditsAdvanced:
    """Advanced tests for commit_pending_edits."""

    async def test_commit_multiple_edits_same_transaction(self, data_manager, mock_mm):
        """Test committing multiple edits to same transaction."""
        # Multiple edits to the same transaction should be grouped
        edits = [
            TransactionEdit("txn_1", "merchant", "A", "B", datetime.now()),
            TransactionEdit("txn_1", "category", "cat_old", "cat_new", datetime.now()),
            TransactionEdit("txn_1", "hide_from_reports", False, True, datetime.now()),
        ]

        success, failure = await data_manager.commit_pending_edits(edits)

        assert success == 1  # Only one transaction updated
        assert failure == 0
        assert len(mock_mm.update_calls) == 1

        # Verify all three fields were updated in single call
        call = mock_mm.update_calls[0]
        assert call["transaction_id"] == "txn_1"
        assert call["merchant_name"] == "B"
        assert call["category_id"] == "cat_new"
        assert call["hide_from_reports"] is True

    async def test_commit_with_api_failure(self, data_manager, mock_mm):
        """Test commit_pending_edits handles API failures gracefully."""
        # Create a mock that raises an exception
        original_update = mock_mm.update_transaction

        async def failing_update(*args, **kwargs):
            if kwargs.get("transaction_id") == "txn_2":
                raise Exception("API Error")
            return await original_update(*args, **kwargs)

        mock_mm.update_transaction = failing_update

        edits = [
            TransactionEdit("txn_1", "merchant", "A", "B", datetime.now()),
            TransactionEdit("txn_2", "merchant", "C", "D", datetime.now()),
            TransactionEdit("txn_3", "merchant", "E", "F", datetime.now()),
        ]

        success, failure = await data_manager.commit_pending_edits(edits)

        # Should have 2 successes and 1 failure
        assert success == 2
        assert failure == 1

    async def test_commit_mixed_edit_types(self, data_manager, mock_mm):
        """Test committing different types of edits together."""
        edits = [
            TransactionEdit("txn_1", "merchant", "Old", "New", datetime.now()),
            TransactionEdit("txn_2", "category", "cat_1", "cat_2", datetime.now()),
            TransactionEdit("txn_3", "hide_from_reports", False, True, datetime.now()),
            TransactionEdit("txn_4", "merchant", "X", "Y", datetime.now()),
        ]

        success, failure = await data_manager.commit_pending_edits(edits)

        assert success == 4
        assert failure == 0
        assert len(mock_mm.update_calls) == 4

        # Verify each update has correct field
        merchants = [c for c in mock_mm.update_calls if c["merchant_name"] is not None]
        categories = [c for c in mock_mm.update_calls if c["category_id"] is not None]
        hides = [c for c in mock_mm.update_calls if c["hide_from_reports"] is not None]

        assert len(merchants) == 2
        assert len(categories) == 1
        assert len(hides) == 1


class TestFetchTransactionsPagination:
    """Test transaction fetching with pagination."""

    async def test_fetch_all_transactions_single_batch(self, data_manager):
        """Test fetching when all transactions fit in one batch."""
        transactions = await data_manager._fetch_all_transactions()

        assert len(transactions) > 0
        # Mock backend has 6 transactions, all fit in default batch

    async def test_fetch_with_progress_updates(self, data_manager):
        """Test progress updates during transaction fetching."""
        progress_messages = []

        def progress_callback(msg: str):
            progress_messages.append(msg)

        transactions = await data_manager._fetch_all_transactions(
            progress_callback=progress_callback
        )

        assert len(transactions) > 0
        assert len(progress_messages) > 0
        # Should see "Downloaded X transactions" messages
        assert any("Downloaded" in msg for msg in progress_messages)

    async def test_fetch_with_date_filters(self, data_manager):
        """Test fetching with start and end date filters."""
        transactions = await data_manager._fetch_all_transactions(
            start_date="2024-10-02", end_date="2024-10-03"
        )

        assert len(transactions) > 0
        # All transactions should be within date range
        for txn in transactions:
            assert "2024-10-02" <= txn["date"] <= "2024-10-03"

    async def test_fetch_alternative_results_format(self, mock_mm):
        """Test fetching with alternative results format (bare 'results' key)."""
        # Temporarily change mock to return bare 'results' format
        original_get_transactions = mock_mm.get_transactions

        async def alternate_format_get_transactions(*args, **kwargs):
            result = await original_get_transactions(*args, **kwargs)
            # Return in alternate format: {"results": [...]} instead of {"allTransactions": {"results": [...]}}
            if "allTransactions" in result:
                return {"results": result["allTransactions"]["results"]}
            return result

        mock_mm.get_transactions = alternate_format_get_transactions

        await mock_mm.login()
        dm = DataManager(mock_mm)

        transactions = await dm._fetch_all_transactions()

        assert len(transactions) > 0
        assert len(transactions) == 6  # All mock transactions

    async def test_fetch_empty_results(self, mock_mm):
        """Test fetching when API returns empty results."""
        # Clear all transactions
        mock_mm.transactions = []

        await mock_mm.login()
        dm = DataManager(mock_mm)

        transactions = await dm._fetch_all_transactions()

        assert len(transactions) == 0

    async def test_fetch_progress_without_total_count(self, mock_mm):
        """Test progress callback when total count is not available."""
        # Modify mock to not include totalCount
        original_get_transactions = mock_mm.get_transactions

        async def no_total_count_get_transactions(*args, **kwargs):
            result = await original_get_transactions(*args, **kwargs)
            # Remove totalCount from response
            if "allTransactions" in result:
                result["allTransactions"].pop("totalCount", None)
            return result

        mock_mm.get_transactions = no_total_count_get_transactions

        await mock_mm.login()
        dm = DataManager(mock_mm)

        progress_messages = []

        def progress_callback(msg: str):
            progress_messages.append(msg)

        transactions = await dm._fetch_all_transactions(progress_callback=progress_callback)

        assert len(transactions) > 0
        # Should have progress messages without percentage
        assert any("Downloaded" in msg and "%" not in msg for msg in progress_messages)
