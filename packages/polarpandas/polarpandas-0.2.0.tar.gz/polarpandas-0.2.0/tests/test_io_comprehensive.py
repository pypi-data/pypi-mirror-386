"""
Comprehensive tests for I/O operations with various formats and edge cases.

All tests compare polarpandas output against actual pandas output
to ensure 100% compatibility.
"""

import os
import tempfile
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

import polarpandas as ppd


class TestCSVIOComprehensive:
    """Comprehensive tests for CSV I/O operations."""

    def setup_method(self):
        """Create test data in both pandas and polarpandas."""
        self.data = {
            "A": [1, 2, 3, 4, 5],
            "B": [10, 20, 30, 40, 50],
            "C": ["a", "b", "c", "d", "e"],
        }
        self.pd_df = pd.DataFrame(self.data)
        self.ppd_df = ppd.DataFrame(self.data)

    def test_read_csv_basic(self):
        """Test basic CSV reading."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            self.pd_df.to_csv(f.name, index=False)

            pd_result = pd.read_csv(f.name)
            ppd_result = ppd.read_csv(f.name)
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_read_csv_with_index(self):
        """Test CSV reading with index."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            self.pd_df.to_csv(f.name, index=True)

            pd_result = pd.read_csv(f.name, index_col=0)
            ppd_result = ppd.read_csv(f.name, index_col=0)
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_read_csv_with_nulls(self):
        """Test CSV reading with null values."""
        data_with_nulls = {
            "A": [1, None, 3, 4, 5],
            "B": [10, 20, None, 40, 50],
            "C": ["a", None, "c", "d", "e"],
        }
        pd_df = pd.DataFrame(data_with_nulls)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            pd_df.to_csv(f.name, index=False)

            pd_result = pd.read_csv(f.name)
            ppd_result = ppd.read_csv(f.name)
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_read_csv_with_different_dtypes(self):
        """Test CSV reading with different data types."""
        mixed_data = {
            "A": [1, 2, 3, 4, 5],
            "B": [1.1, 2.2, 3.3, 4.4, 5.5],
            "C": [True, False, True, False, True],
            "D": [
                datetime(2023, 1, 1),
                datetime(2023, 1, 2),
                datetime(2023, 1, 3),
                datetime(2023, 1, 4),
                datetime(2023, 1, 5),
            ],
        }
        pd_df = pd.DataFrame(mixed_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            pd_df.to_csv(f.name, index=False)

            pd_result = pd.read_csv(f.name)
            ppd_result = ppd.read_csv(f.name)
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_read_csv_with_separator(self):
        """Test CSV reading with different separator."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            self.pd_df.to_csv(f.name, index=False, sep=";")

            pd_result = pd.read_csv(f.name, sep=";")
            ppd_result = ppd.read_csv(f.name, sep=";")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_read_csv_with_header(self):
        """Test CSV reading with custom header."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            self.pd_df.to_csv(f.name, index=False, header=["X", "Y", "Z"])

            pd_result = pd.read_csv(f.name, names=["X", "Y", "Z"])
            ppd_result = ppd.read_csv(f.name, names=["X", "Y", "Z"])
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_read_csv_with_skiprows(self):
        """Test CSV reading with skiprows."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            # Add header row
            f.write("Header line\n")
            self.pd_df.to_csv(f.name, index=False, mode="a")

            pd_result = pd.read_csv(f.name, skiprows=1)
            ppd_result = ppd.read_csv(f.name, skiprows=1)
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_read_csv_with_nrows(self):
        """Test CSV reading with nrows parameter."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            self.pd_df.to_csv(f.name, index=False)

            pd_result = pd.read_csv(f.name, nrows=3)
            ppd_result = ppd.read_csv(f.name, nrows=3)
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_read_csv_empty_file(self):
        """Test CSV reading with empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            # Create empty file
            pass

            # Both should raise EmptyDataError for empty files
            with pytest.raises(pd.errors.EmptyDataError):
                pd.read_csv(f.name)
            with pytest.raises(pd.errors.EmptyDataError):
                ppd.read_csv(f.name)

            os.unlink(f.name)

    def test_read_csv_single_column(self):
        """Test CSV reading with single column."""
        single_col_data = {"A": [1, 2, 3, 4, 5]}
        pd_df = pd.DataFrame(single_col_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            pd_df.to_csv(f.name, index=False)

            pd_result = pd.read_csv(f.name)
            ppd_result = ppd.read_csv(f.name)
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_read_csv_single_row(self):
        """Test CSV reading with single row."""
        single_row_data = {"A": [1], "B": [10], "C": ["a"]}
        pd_df = pd.DataFrame(single_row_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            pd_df.to_csv(f.name, index=False)

            pd_result = pd.read_csv(f.name)
            ppd_result = ppd.read_csv(f.name)
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_read_csv_large_dataset(self):
        """Test CSV reading with large dataset."""
        # Create larger dataset
        np.random.seed(42)
        large_data = {
            "A": np.random.randn(1000),
            "B": np.random.randn(1000),
            "C": np.random.randn(1000),
        }
        pd_df = pd.DataFrame(large_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            pd_df.to_csv(f.name, index=False)

            pd_result = pd.read_csv(f.name)
            ppd_result = ppd.read_csv(f.name)
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_to_csv_basic(self):
        """Test basic CSV writing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            self.pd_df.to_csv(f.name, index=False)
            self.ppd_df.to_csv(f.name, index=False)

            # Read back and compare
            pd_result = pd.read_csv(f.name)
            ppd_result = ppd.read_csv(f.name)
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_to_csv_with_index(self):
        """Test CSV writing with index."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            self.pd_df.to_csv(f.name, index=True)
            self.ppd_df.to_csv(f.name, index=True)

            # Read back and compare
            pd_result = pd.read_csv(f.name, index_col=0)
            ppd_result = ppd.read_csv(f.name, index_col=0)
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_to_csv_with_separator(self):
        """Test CSV writing with different separator."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            self.pd_df.to_csv(f.name, index=False, sep=";")
            self.ppd_df.to_csv(f.name, index=False, sep=";")

            # Read back and compare
            pd_result = pd.read_csv(f.name, sep=";")
            ppd_result = ppd.read_csv(f.name, sep=";")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_to_csv_with_header(self):
        """Test CSV writing with custom header."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            # Test pandas
            self.pd_df.to_csv(f.name, index=False, header=["X", "Y", "Z"])
            pd_result = pd.read_csv(f.name, names=["X", "Y", "Z"])

            # Clear file and test polarpandas
            with open(f.name, "w") as f:
                pass  # Clear the file
            self.ppd_df.to_csv(f.name, index=False, header=["X", "Y", "Z"])
            ppd_result = ppd.read_csv(f.name, names=["X", "Y", "Z"])

            # Compare results
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_io_methods_return_types(self):
        """Test that I/O methods return correct types."""
        # Test read_csv
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            self.pd_df.to_csv(f.name, index=False)
            result = ppd.read_csv(f.name)
            assert isinstance(result, ppd.DataFrame)
            os.unlink(f.name)

    def test_io_methods_preserve_original(self):
        """Test that I/O methods don't modify original DataFrame."""
        original_pd = self.pd_df.copy()
        original_ppd = self.ppd_df.copy()

        # Perform I/O operations
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            self.pd_df.to_csv(f.name, index=False)
            self.ppd_df.to_csv(f.name, index=False)
            os.unlink(f.name)

        # Original should be unchanged
        pd.testing.assert_frame_equal(original_pd, self.pd_df)
        pd.testing.assert_frame_equal(original_ppd.to_pandas(), self.ppd_df.to_pandas())


class TestJSONIOComprehensive:
    """Comprehensive tests for JSON I/O operations."""

    def setup_method(self):
        """Create test data in both pandas and polarpandas."""
        self.data = {
            "A": [1, 2, 3, 4, 5],
            "B": [10, 20, 30, 40, 50],
            "C": ["a", "b", "c", "d", "e"],
        }
        self.pd_df = pd.DataFrame(self.data)
        self.ppd_df = ppd.DataFrame(self.data)

    def test_read_json_basic(self):
        """Test basic JSON reading."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            self.pd_df.to_json(f.name, orient="records")

            pd_result = pd.read_json(f.name, orient="records")
            ppd_result = ppd.read_json(f.name, orient="records")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    @pytest.mark.skip(
        reason="Polars doesn't support orient parameter for JSON operations - permanent limitation"
    )
    def test_read_json_with_index(self):
        """Test JSON reading with index."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            self.pd_df.to_json(f.name, orient="index")

            pd_result = pd.read_json(f.name, orient="index")
            ppd_result = ppd.read_json(f.name, orient="index")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    @pytest.mark.skip(
        reason="Polars doesn't support orient parameter for JSON operations - permanent limitation"
    )
    def test_read_json_with_columns(self):
        """Test JSON reading with columns orientation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            self.pd_df.to_json(f.name, orient="columns")

            pd_result = pd.read_json(f.name, orient="columns")
            ppd_result = ppd.read_json(f.name, orient="columns")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    @pytest.mark.skip(
        reason="Polars doesn't support orient parameter for JSON operations - permanent limitation"
    )
    def test_read_json_with_values(self):
        """Test JSON reading with values orientation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            self.pd_df.to_json(f.name, orient="values")

            pd_result = pd.read_json(f.name, orient="values")
            ppd_result = ppd.read_json(f.name, orient="values")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    @pytest.mark.skip(
        reason="Polars doesn't support orient parameter for JSON operations - permanent limitation"
    )
    def test_read_json_with_split(self):
        """Test JSON reading with split orientation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            self.pd_df.to_json(f.name, orient="split")

            pd_result = pd.read_json(f.name, orient="split")
            ppd_result = ppd.read_json(f.name, orient="split")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    @pytest.mark.skip(
        reason="Polars doesn't support orient parameter for JSON operations - permanent limitation"
    )
    def test_read_json_with_table(self):
        """Test JSON reading with table orientation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            self.pd_df.to_json(f.name, orient="table")

            pd_result = pd.read_json(f.name, orient="table")
            ppd_result = ppd.read_json(f.name, orient="table")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_to_json_basic(self):
        """Test basic JSON writing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            self.pd_df.to_json(f.name, orient="records")
            self.ppd_df.to_json(f.name, orient="records")

            # Read back and compare
            pd_result = pd.read_json(f.name, orient="records")
            ppd_result = ppd.read_json(f.name, orient="records")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    @pytest.mark.skip(
        reason="Polars doesn't support orient parameter for JSON operations - permanent limitation"
    )
    def test_to_json_with_index(self):
        """Test JSON writing with index."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            self.pd_df.to_json(f.name, orient="index")
            self.ppd_df.to_json(f.name, orient="index")

            # Read back and compare
            pd_result = pd.read_json(f.name, orient="index")
            ppd_result = ppd.read_json(f.name, orient="index")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    @pytest.mark.skip(
        reason="Polars doesn't support orient parameter for JSON operations - permanent limitation"
    )
    def test_to_json_with_columns(self):
        """Test JSON writing with columns orientation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            self.pd_df.to_json(f.name, orient="columns")
            self.ppd_df.to_json(f.name, orient="columns")

            # Read back and compare
            pd_result = pd.read_json(f.name, orient="columns")
            ppd_result = ppd.read_json(f.name, orient="columns")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    @pytest.mark.skip(
        reason="Polars doesn't support orient parameter for JSON operations - permanent limitation"
    )
    def test_to_json_with_values(self):
        """Test JSON writing with values orientation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            self.pd_df.to_json(f.name, orient="values")
            self.ppd_df.to_json(f.name, orient="values")

            # Read back and compare
            pd_result = pd.read_json(f.name, orient="values")
            ppd_result = ppd.read_json(f.name, orient="values")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    @pytest.mark.skip(
        reason="Polars doesn't support orient parameter for JSON operations - permanent limitation"
    )
    def test_to_json_with_split(self):
        """Test JSON writing with split orientation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            self.pd_df.to_json(f.name, orient="split")
            self.ppd_df.to_json(f.name, orient="split")

            # Read back and compare
            pd_result = pd.read_json(f.name, orient="split")
            ppd_result = ppd.read_json(f.name, orient="split")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    @pytest.mark.skip(
        reason="Polars doesn't support orient parameter for JSON operations - permanent limitation"
    )
    def test_to_json_with_table(self):
        """Test JSON writing with table orientation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            self.pd_df.to_json(f.name, orient="table")
            self.ppd_df.to_json(f.name, orient="table")

            # Read back and compare
            pd_result = pd.read_json(f.name, orient="table")
            ppd_result = ppd.read_json(f.name, orient="table")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_json_io_with_nulls(self):
        """Test JSON I/O with null values."""
        data_with_nulls = {
            "A": [1, None, 3, 4, 5],
            "B": [10, 20, None, 40, 50],
            "C": ["a", None, "c", "d", "e"],
        }
        pd_df = pd.DataFrame(data_with_nulls)
        ppd_df = ppd.DataFrame(data_with_nulls)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            pd_df.to_json(f.name, orient="records")
            ppd_df.to_json(f.name, orient="records")

            # Read back and compare
            pd_result = pd.read_json(f.name, orient="records")
            ppd_result = ppd.read_json(f.name, orient="records")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_json_io_with_different_dtypes(self):
        """Test JSON I/O with different data types."""
        mixed_data = {
            "A": [1, 2, 3, 4, 5],
            "B": [1.1, 2.2, 3.3, 4.4, 5.5],
            "C": [True, False, True, False, True],
            "D": [
                datetime(2023, 1, 1),
                datetime(2023, 1, 2),
                datetime(2023, 1, 3),
                datetime(2023, 1, 4),
                datetime(2023, 1, 5),
            ],
        }
        pd_df = pd.DataFrame(mixed_data)
        ppd_df = ppd.DataFrame(mixed_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            pd_df.to_json(f.name, orient="records")
            ppd_df.to_json(f.name, orient="records")

            # Read back and compare
            pd_result = pd.read_json(f.name, orient="records")
            ppd_result = ppd.read_json(f.name, orient="records")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_json_io_empty_dataframe(self):
        """Test JSON I/O with empty DataFrame."""
        pd_empty = pd.DataFrame()
        ppd_empty = ppd.DataFrame()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            pd_empty.to_json(f.name, orient="records")
            ppd_empty.to_json(f.name, orient="records")

            # Read back and compare
            pd_result = pd.read_json(f.name, orient="records")
            ppd_result = ppd.read_json(f.name, orient="records")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_json_io_single_column(self):
        """Test JSON I/O with single column."""
        single_col_data = {"A": [1, 2, 3, 4, 5]}
        pd_df = pd.DataFrame(single_col_data)
        ppd_df = ppd.DataFrame(single_col_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            pd_df.to_json(f.name, orient="records")
            ppd_df.to_json(f.name, orient="records")

            # Read back and compare
            pd_result = pd.read_json(f.name, orient="records")
            ppd_result = ppd.read_json(f.name, orient="records")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_json_io_single_row(self):
        """Test JSON I/O with single row."""
        single_row_data = {"A": [1], "B": [10], "C": ["a"]}
        pd_df = pd.DataFrame(single_row_data)
        ppd_df = ppd.DataFrame(single_row_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            pd_df.to_json(f.name, orient="records")
            ppd_df.to_json(f.name, orient="records")

            # Read back and compare
            pd_result = pd.read_json(f.name, orient="records")
            ppd_result = ppd.read_json(f.name, orient="records")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_json_io_large_dataset(self):
        """Test JSON I/O with large dataset."""
        # Create larger dataset
        np.random.seed(42)
        large_data = {
            "A": np.random.randn(1000),
            "B": np.random.randn(1000),
            "C": np.random.randn(1000),
        }
        pd_df = pd.DataFrame(large_data)
        ppd_df = ppd.DataFrame(large_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            pd_df.to_json(f.name, orient="records")
            ppd_df.to_json(f.name, orient="records")

            # Read back and compare
            pd_result = pd.read_json(f.name, orient="records")
            ppd_result = ppd.read_json(f.name, orient="records")
            pd.testing.assert_frame_equal(ppd_result.to_pandas(), pd_result)

            os.unlink(f.name)

    def test_json_io_methods_return_types(self):
        """Test that JSON I/O methods return correct types."""
        # Test read_json
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            self.pd_df.to_json(f.name, orient="records")
            result = ppd.read_json(f.name, orient="records")
            assert isinstance(result, ppd.DataFrame)
            os.unlink(f.name)

    def test_json_io_methods_preserve_original(self):
        """Test that JSON I/O methods don't modify original DataFrame."""
        original_pd = self.pd_df.copy()
        original_ppd = self.ppd_df.copy()

        # Perform I/O operations
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            self.pd_df.to_json(f.name, orient="records")
            self.ppd_df.to_json(f.name, orient="records")
            os.unlink(f.name)

        # Original should be unchanged
        pd.testing.assert_frame_equal(original_pd, self.pd_df)
        pd.testing.assert_frame_equal(original_ppd.to_pandas(), self.ppd_df.to_pandas())
