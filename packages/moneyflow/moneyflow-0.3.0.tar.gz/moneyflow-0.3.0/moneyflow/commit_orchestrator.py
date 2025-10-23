"""
Commit orchestration logic for applying edits to DataFrames.

This module contains the critical business logic for:
1. Applying committed edits to local DataFrames (instant UI update)
2. Updating category names and groups after category changes
3. Pure, testable DataFrame transformations

All functions are fully typed and have no UI dependencies.
"""

from typing import Callable

import polars as pl

from .state import TransactionEdit


class CommitOrchestrator:
    """
    Orchestrates commit workflow and DataFrame updates.

    This class handles the critical logic of applying edits to DataFrames
    after successful API commits, ensuring the UI shows updated data immediately
    without needing to re-fetch from the API.
    """

    @staticmethod
    def apply_merchant_edit(
        df: pl.DataFrame, transaction_id: str, new_merchant: str
    ) -> pl.DataFrame:
        """
        Apply merchant edit to DataFrame.

        Args:
            df: Transaction DataFrame
            transaction_id: ID of transaction to update
            new_merchant: New merchant name

        Returns:
            Updated DataFrame with merchant changed

        Examples:
            >>> df = pl.DataFrame({
            ...     "id": ["txn1", "txn2"],
            ...     "merchant": ["Amazon", "Starbucks"]
            ... })
            >>> updated = CommitOrchestrator.apply_merchant_edit(df, "txn1", "Whole Foods")
            >>> updated.filter(pl.col("id") == "txn1")["merchant"][0]
            'Whole Foods'
            >>> updated.filter(pl.col("id") == "txn2")["merchant"][0]
            'Starbucks'
        """
        return df.with_columns(
            pl.when(pl.col("id") == transaction_id)
            .then(pl.lit(new_merchant))
            .otherwise(pl.col("merchant"))
            .alias("merchant")
        )

    @staticmethod
    def apply_category_edit(
        df: pl.DataFrame,
        transaction_id: str,
        new_category_id: str,
        category_name: str,
        apply_groups_func: Callable[[pl.DataFrame], pl.DataFrame],
    ) -> pl.DataFrame:
        """
        Apply category edit to DataFrame and update groups.

        Args:
            df: Transaction DataFrame
            transaction_id: ID of transaction to update
            new_category_id: New category ID
            category_name: New category name (looked up from categories dict)
            apply_groups_func: Function to reapply category groups
                              (e.g., data_manager.apply_category_groups)

        Returns:
            Updated DataFrame with category_id, category, and group updated

        Examples:
            >>> df = pl.DataFrame({
            ...     "id": ["txn1"],
            ...     "category_id": ["cat1"],
            ...     "category": ["Old Category"],
            ...     "group": ["Old Group"]
            ... })
            >>> def mock_apply_groups(df):
            ...     return df.with_columns(pl.lit("New Group").alias("group"))
            >>> updated = CommitOrchestrator.apply_category_edit(
            ...     df, "txn1", "cat2", "New Category", mock_apply_groups
            ... )
            >>> updated["category"][0]
            'New Category'
        """
        # Update category_id
        df = df.with_columns(
            pl.when(pl.col("id") == transaction_id)
            .then(pl.lit(new_category_id))
            .otherwise(pl.col("category_id"))
            .alias("category_id")
        )

        # Update category name
        df = df.with_columns(
            pl.when(pl.col("id") == transaction_id)
            .then(pl.lit(category_name))
            .otherwise(pl.col("category"))
            .alias("category")
        )

        # Reapply category groups to update the 'group' column
        df = apply_groups_func(df)

        return df

    @staticmethod
    def apply_hide_from_reports_edit(
        df: pl.DataFrame, transaction_id: str, new_hide_value: bool
    ) -> pl.DataFrame:
        """
        Apply hide_from_reports edit to DataFrame.

        Args:
            df: Transaction DataFrame
            transaction_id: ID of transaction to update
            new_hide_value: New hide_from_reports value

        Returns:
            Updated DataFrame with hideFromReports changed

        Examples:
            >>> df = pl.DataFrame({
            ...     "id": ["txn1", "txn2"],
            ...     "hideFromReports": [False, False]
            ... })
            >>> updated = CommitOrchestrator.apply_hide_from_reports_edit(
            ...     df, "txn1", True
            ... )
            >>> updated.filter(pl.col("id") == "txn1")["hideFromReports"][0]
            True
            >>> updated.filter(pl.col("id") == "txn2")["hideFromReports"][0]
            False
        """
        return df.with_columns(
            pl.when(pl.col("id") == transaction_id)
            .then(pl.lit(new_hide_value))
            .otherwise(pl.col("hideFromReports"))
            .alias("hideFromReports")
        )

    @staticmethod
    def apply_edit_to_dataframe(
        df: pl.DataFrame,
        edit: TransactionEdit,
        categories: dict[str, dict],
        apply_groups_func: Callable[[pl.DataFrame], pl.DataFrame],
    ) -> pl.DataFrame:
        """
        Apply a single edit to DataFrame.

        Dispatcher function that calls the appropriate edit function
        based on edit.field.

        Args:
            df: Transaction DataFrame
            edit: Edit to apply
            categories: Category lookup dict (id -> {name, group, ...})
            apply_groups_func: Function to reapply category groups

        Returns:
            Updated DataFrame

        Raises:
            ValueError: If edit.field is unknown
        """
        if edit.field == "merchant":
            return CommitOrchestrator.apply_merchant_edit(df, edit.transaction_id, edit.new_value)
        elif edit.field == "category":
            # Lookup category name
            cat_name = categories.get(edit.new_value, {}).get("name", "Unknown")
            return CommitOrchestrator.apply_category_edit(
                df, edit.transaction_id, edit.new_value, cat_name, apply_groups_func
            )
        elif edit.field == "hide_from_reports":
            return CommitOrchestrator.apply_hide_from_reports_edit(
                df, edit.transaction_id, edit.new_value
            )
        else:
            raise ValueError(f"Unknown edit field: {edit.field}")

    @staticmethod
    def apply_edits_to_dataframe(
        df: pl.DataFrame,
        edits: list[TransactionEdit],
        categories: dict[str, dict],
        apply_groups_func: Callable[[pl.DataFrame], pl.DataFrame],
    ) -> pl.DataFrame:
        """
        Apply multiple edits to DataFrame.

        This is a pure function - it doesn't mutate the input DataFrame.

        Args:
            df: Transaction DataFrame
            edits: List of edits to apply
            categories: Category lookup dict
            apply_groups_func: Function to reapply category groups

        Returns:
            New DataFrame with all edits applied

        Examples:
            >>> df = pl.DataFrame({
            ...     "id": ["txn1", "txn2"],
            ...     "merchant": ["Amazon", "Starbucks"],
            ...     "category_id": ["cat1", "cat2"],
            ...     "category": ["Shopping", "Dining"],
            ...     "group": ["Retail", "Food"],
            ...     "hideFromReports": [False, False]
            ... })
            >>> edits = [
            ...     TransactionEdit("txn1", "merchant", "Amazon", "Whole Foods", ...),
            ...     TransactionEdit("txn2", "hide_from_reports", False, True, ...)
            ... ]
            >>> def mock_apply_groups(df): return df
            >>> updated = CommitOrchestrator.apply_edits_to_dataframe(
            ...     df, edits, {}, mock_apply_groups
            ... )
            >>> updated["merchant"][0]
            'Whole Foods'
            >>> updated["hideFromReports"][1]
            True
        """
        result_df = df

        for edit in edits:
            result_df = CommitOrchestrator.apply_edit_to_dataframe(
                result_df, edit, categories, apply_groups_func
            )

        return result_df
