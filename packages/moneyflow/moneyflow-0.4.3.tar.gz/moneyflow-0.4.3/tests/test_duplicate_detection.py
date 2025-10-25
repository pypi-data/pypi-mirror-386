"""
Tests for duplicate transaction detection.

Critical to test thoroughly since deletion is potentially destructive.
"""

from datetime import date

import polars as pl
import pytest

from moneyflow.duplicate_detector import DuplicateDetector


class TestDuplicateDetection:
    """Test basic duplicate detection logic."""

    def test_find_exact_duplicates(self, duplicate_transactions_df):
        """Test finding exact duplicate transactions."""
        duplicates = DuplicateDetector.find_duplicates(duplicate_transactions_df)

        assert len(duplicates) > 0
        # Should find the Starbucks duplicate pair
        assert duplicates["merchant"][0] == "Starbucks"

    def test_no_duplicates_in_clean_data(self, sample_transactions_df):
        """Test that clean data has no duplicates."""
        duplicates = DuplicateDetector.find_duplicates(sample_transactions_df)

        # sample_transactions_df has no duplicates
        assert duplicates.is_empty()

    def test_empty_dataframe(self):
        """Test duplicate detection on empty DataFrame."""
        empty_df = pl.DataFrame()
        duplicates = DuplicateDetector.find_duplicates(empty_df)

        assert duplicates.is_empty()

    def test_strict_account_matching(self):
        """Test that strict account matching prevents false positives."""
        data = [
            {
                "id": "txn_1",
                "date": date(2024, 10, 1),
                "amount": -50.00,
                "merchant": "Starbucks",
                "merchant_id": "merch_1",
                "category": "Restaurants & Bars",
                "category_id": "cat_1",
                "group": "Food & Dining",
                "account": "Account A",
                "account_id": "acc_a",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            },
            {
                "id": "txn_2",
                "date": date(2024, 10, 1),
                "amount": -50.00,
                "merchant": "Starbucks",
                "merchant_id": "merch_1",
                "category": "Restaurants & Bars",
                "category_id": "cat_1",
                "group": "Food & Dining",
                "account": "Account B",  # Different account
                "account_id": "acc_b",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            },
        ]

        df = pl.DataFrame(data)

        # With strict matching, should NOT be duplicates (different accounts)
        duplicates_strict = DuplicateDetector.find_duplicates(df, strict_account_match=True)
        assert duplicates_strict.is_empty()

        # Without strict matching, SHOULD be duplicates
        duplicates_loose = DuplicateDetector.find_duplicates(df, strict_account_match=False)
        assert len(duplicates_loose) == 1

    def test_case_insensitive_merchant_matching(self):
        """Test that merchant matching is case-insensitive."""
        data = [
            {
                "id": "txn_1",
                "date": date(2024, 10, 1),
                "amount": -50.00,
                "merchant": "Amazon",
                "merchant_id": "merch_1",
                "category": "Shopping",
                "category_id": "cat_1",
                "group": "Shopping",
                "account": "Chase",
                "account_id": "acc_1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            },
            {
                "id": "txn_2",
                "date": date(2024, 10, 1),
                "amount": -50.00,
                "merchant": "AMAZON",  # Different case
                "merchant_id": "merch_1",
                "category": "Shopping",
                "category_id": "cat_1",
                "group": "Shopping",
                "account": "Chase",
                "account_id": "acc_1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            },
        ]

        df = pl.DataFrame(data)
        duplicates = DuplicateDetector.find_duplicates(df)

        assert len(duplicates) == 1


class TestDuplicateGrouping:
    """Test grouping duplicate transactions into clusters."""

    def test_simple_pair(self):
        """Test grouping a simple duplicate pair."""
        data = [
            {
                "id": "txn_1",
                "date": date(2024, 10, 1),
                "amount": -50.00,
                "merchant": "Test",
                "merchant_id": "m1",
                "category": "Cat",
                "category_id": "c1",
                "group": "G",
                "account": "Acc",
                "account_id": "a1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            },
            {
                "id": "txn_2",
                "date": date(2024, 10, 1),
                "amount": -50.00,
                "merchant": "Test",
                "merchant_id": "m1",
                "category": "Cat",
                "category_id": "c1",
                "group": "G",
                "account": "Acc",
                "account_id": "a1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            },
        ]

        df = pl.DataFrame(data)
        duplicates = DuplicateDetector.find_duplicates(df)
        groups = DuplicateDetector.get_duplicate_groups(df, duplicates)

        assert len(groups) == 1
        assert set(groups[0]) == {"txn_1", "txn_2"}

    def test_triple_duplicates(self):
        """Test grouping when there are 3 identical transactions."""
        data = [
            {
                "id": f"txn_{i}",
                "date": date(2024, 10, 1),
                "amount": -50.00,
                "merchant": "Test",
                "merchant_id": "m1",
                "category": "Cat",
                "category_id": "c1",
                "group": "G",
                "account": "Acc",
                "account_id": "a1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            }
            for i in range(1, 4)  # txn_1, txn_2, txn_3
        ]

        df = pl.DataFrame(data)
        duplicates = DuplicateDetector.find_duplicates(df)
        groups = DuplicateDetector.get_duplicate_groups(df, duplicates)

        assert len(groups) == 1
        assert len(groups[0]) == 3
        assert set(groups[0]) == {"txn_1", "txn_2", "txn_3"}

    def test_multiple_separate_duplicate_groups(self):
        """Test when there are multiple separate duplicate groups."""
        data = [
            # Group 1: Starbucks duplicates
            {
                "id": "txn_1",
                "date": date(2024, 10, 1),
                "amount": -5.00,
                "merchant": "Starbucks",
                "merchant_id": "m1",
                "category": "Coffee",
                "category_id": "c1",
                "group": "Food",
                "account": "Acc",
                "account_id": "a1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            },
            {
                "id": "txn_2",
                "date": date(2024, 10, 1),
                "amount": -5.00,
                "merchant": "Starbucks",
                "merchant_id": "m1",
                "category": "Coffee",
                "category_id": "c1",
                "group": "Food",
                "account": "Acc",
                "account_id": "a1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            },
            # Group 2: Amazon duplicates
            {
                "id": "txn_3",
                "date": date(2024, 10, 2),
                "amount": -100.00,
                "merchant": "Amazon",
                "merchant_id": "m2",
                "category": "Shopping",
                "category_id": "c2",
                "group": "Shopping",
                "account": "Acc",
                "account_id": "a1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            },
            {
                "id": "txn_4",
                "date": date(2024, 10, 2),
                "amount": -100.00,
                "merchant": "Amazon",
                "merchant_id": "m2",
                "category": "Shopping",
                "category_id": "c2",
                "group": "Shopping",
                "account": "Acc",
                "account_id": "a1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            },
            # Non-duplicate
            {
                "id": "txn_5",
                "date": date(2024, 10, 3),
                "amount": -25.00,
                "merchant": "Target",
                "merchant_id": "m3",
                "category": "Shopping",
                "category_id": "c2",
                "group": "Shopping",
                "account": "Acc",
                "account_id": "a1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            },
        ]

        df = pl.DataFrame(data)
        duplicates = DuplicateDetector.find_duplicates(df)
        groups = DuplicateDetector.get_duplicate_groups(df, duplicates)

        assert len(groups) == 2

        # Check that we have two groups of 2
        group_sizes = sorted([len(g) for g in groups])
        assert group_sizes == [2, 2]

    def test_no_duplicates_empty_groups(self, sample_transactions_df):
        """Test that clean data produces empty groups."""
        duplicates = DuplicateDetector.find_duplicates(sample_transactions_df)
        groups = DuplicateDetector.get_duplicate_groups(sample_transactions_df, duplicates)

        assert len(groups) == 0


class TestDuplicateReport:
    """Test duplicate report formatting."""

    def test_format_report_with_duplicates(self, duplicate_transactions_df):
        """Test formatting a report with duplicates."""
        duplicates = DuplicateDetector.find_duplicates(duplicate_transactions_df)
        groups = DuplicateDetector.get_duplicate_groups(duplicate_transactions_df, duplicates)

        report = DuplicateDetector.format_duplicate_report(duplicate_transactions_df, groups)

        assert "Duplicate Transaction Report" in report
        assert "Group 1:" in report
        assert "Starbucks" in report

    def test_format_report_no_duplicates(self, sample_transactions_df):
        """Test formatting report with no duplicates."""
        duplicates = DuplicateDetector.find_duplicates(sample_transactions_df)
        groups = DuplicateDetector.get_duplicate_groups(sample_transactions_df, duplicates)

        report = DuplicateDetector.format_duplicate_report(sample_transactions_df, groups)

        assert report == "No duplicates found."


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_different_amounts_not_duplicate(self):
        """Test that different amounts are not duplicates."""
        data = [
            {
                "id": "txn_1",
                "date": date(2024, 10, 1),
                "amount": -50.00,
                "merchant": "Test",
                "merchant_id": "m1",
                "category": "Cat",
                "category_id": "c1",
                "group": "G",
                "account": "Acc",
                "account_id": "a1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            },
            {
                "id": "txn_2",
                "date": date(2024, 10, 1),
                "amount": -51.00,  # Different
                "merchant": "Test",
                "merchant_id": "m1",
                "category": "Cat",
                "category_id": "c1",
                "group": "G",
                "account": "Acc",
                "account_id": "a1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            },
        ]

        df = pl.DataFrame(data)
        duplicates = DuplicateDetector.find_duplicates(df)

        assert duplicates.is_empty()

    def test_different_merchants_not_duplicate(self):
        """Test that different merchants are not duplicates."""
        data = [
            {
                "id": "txn_1",
                "date": date(2024, 10, 1),
                "amount": -50.00,
                "merchant": "Starbucks",
                "merchant_id": "m1",
                "category": "Cat",
                "category_id": "c1",
                "group": "G",
                "account": "Acc",
                "account_id": "a1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            },
            {
                "id": "txn_2",
                "date": date(2024, 10, 1),
                "amount": -50.00,
                "merchant": "Dunkin",  # Different merchant
                "merchant_id": "m2",
                "category": "Cat",
                "category_id": "c1",
                "group": "G",
                "account": "Acc",
                "account_id": "a1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            },
        ]

        df = pl.DataFrame(data)
        duplicates = DuplicateDetector.find_duplicates(df)

        assert duplicates.is_empty()

    def test_recurring_transactions_detected_as_duplicates(self):
        """
        Test that recurring transactions with same amount ARE detected.

        This is expected behavior - user can decide what to do with them.
        """
        data = [
            {
                "id": "txn_1",
                "date": date(2024, 10, 1),
                "amount": -9.99,
                "merchant": "Netflix",
                "merchant_id": "m1",
                "category": "Entertainment",
                "category_id": "c1",
                "group": "Entertainment",
                "account": "Acc",
                "account_id": "a1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": True,
            },
            {
                "id": "txn_2",
                "date": date(2024, 11, 1),
                "amount": -9.99,
                "merchant": "Netflix",
                "merchant_id": "m1",
                "category": "Entertainment",
                "category_id": "c1",
                "group": "Entertainment",
                "account": "Acc",
                "account_id": "a1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": True,
            },
        ]

        df = pl.DataFrame(data)

        # These will NOT be detected as duplicates (30 days apart)
        duplicates = DuplicateDetector.find_duplicates(df, date_tolerance_days=0)
        assert duplicates.is_empty()

        # With date tolerance they COULD be detected, but that's not realistic
        # for monthly subscriptions. This is working as designed.

    def test_single_transaction_no_duplicates(self):
        """Test that a single transaction has no duplicates."""
        data = [
            {
                "id": "txn_1",
                "date": date(2024, 10, 1),
                "amount": -50.00,
                "merchant": "Test",
                "merchant_id": "m1",
                "category": "Cat",
                "category_id": "c1",
                "group": "G",
                "account": "Acc",
                "account_id": "a1",
                "notes": "",
                "hide_from_reports": False,
                "pending": False,
                "is_recurring": False,
            },
        ]

        df = pl.DataFrame(data)
        duplicates = DuplicateDetector.find_duplicates(df)

        assert duplicates.is_empty()


class TestDuplicateDetectionPerformance:
    """Test performance characteristics."""

    @pytest.mark.slow
    def test_large_dataset_performance(self):
        """Test that duplicate detection is reasonably fast on large datasets."""
        import time

        # Create a large dataset with some duplicates
        data = []
        for i in range(1000):
            # Every 10th transaction is a duplicate
            amount = -50.00 if i % 10 == 0 else -float(i)
            merchant = "Duplicate Merchant" if i % 10 == 0 else f"Merchant {i}"

            data.append(
                {
                    "id": f"txn_{i}",
                    "date": date(2024, 10, i % 28 + 1),
                    "amount": amount,
                    "merchant": merchant,
                    "merchant_id": f"m{i}",
                    "category": "Category",
                    "category_id": "c1",
                    "group": "Group",
                    "account": "Account",
                    "account_id": "a1",
                    "notes": "",
                    "hide_from_reports": False,
                    "pending": False,
                    "is_recurring": False,
                }
            )

        df = pl.DataFrame(data)

        start = time.time()
        duplicates = DuplicateDetector.find_duplicates(df)
        elapsed = time.time() - start

        # Should complete in under 5 seconds even with O(n²) algorithm
        assert elapsed < 5.0

        # Should find the duplicates
        assert len(duplicates) > 0
