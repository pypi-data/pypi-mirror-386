# tests/test_data.py
"""
Unit tests for the retire.data module.

Tests all data loading functions, error handling, and data validation
to ensure the package can properly load and process coal plant datasets.
"""

import pytest
import pandas as pd
import networkx as nx
import numpy as np
from pathlib import Path
from unittest.mock import patch, Mock, mock_open
import ast

from retire.data.data import (
    load_dataset,
    load_clean_dataset,
    load_projection,
    load_graph,
    load_generator_level_dataset,
    load_retired_plant_dataset,
    generate_target_matching_data,
    _most_frequent_string,
    _avg_ignore_nan,
    _average_lists,
)


class TestDataLoadingFunctions:
    """Test all data loading functions in the data module."""

    @pytest.mark.unit
    def test_load_dataset_success(self, sample_raw_df, mock_resources_path):
        """Test successful loading of the main coal plants dataset."""
        with patch("pandas.read_csv", return_value=sample_raw_df):
            result = load_dataset()

            assert isinstance(result, pd.DataFrame)
            assert len(result) > 0
            assert "Plant Name" in result.columns
            assert "ORISPL" in result.columns
            assert "ret_STATUS" in result.columns

    @pytest.mark.unit
    def test_load_clean_dataset_success(self, sample_clean_df, mock_resources_path):
        """Test successful loading of the cleaned dataset."""
        with patch("pandas.read_csv", return_value=sample_clean_df):
            result = load_clean_dataset()

            assert isinstance(result, pd.DataFrame)
            assert len(result) > 0
            # Clean dataset should have mostly numeric columns
            numeric_cols = result.select_dtypes(include=[np.number]).columns
            assert len(numeric_cols) > 0

    @pytest.mark.unit
    def test_load_projection_success(self, sample_raw_df, mock_resources_path):
        """Test successful loading of the projection dataset."""
        with patch("pandas.read_csv", return_value=sample_raw_df):
            result = load_projection()

            assert isinstance(result, pd.DataFrame)
            assert len(result) > 0

    @pytest.mark.unit
    def test_load_generator_level_dataset_success(
        self, sample_raw_df, mock_resources_path
    ):
        """Test successful loading of generator-level dataset."""
        with patch("pandas.read_csv", return_value=sample_raw_df):
            result = load_generator_level_dataset()

            assert isinstance(result, pd.DataFrame)
            assert len(result) > 0

    @pytest.mark.unit
    def test_load_retired_plant_dataset_success(
        self, sample_raw_df, mock_resources_path
    ):
        """Test successful loading of retired plants dataset."""
        with patch("pandas.read_csv", return_value=sample_raw_df):
            result = load_retired_plant_dataset()

            assert isinstance(result, pd.DataFrame)
            assert len(result) > 0

    @pytest.mark.unit
    def test_data_loading_file_not_found(self, mock_resources_path):
        """Test handling of missing data files."""
        with patch("pandas.read_csv", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError):
                load_dataset()

    @pytest.mark.unit
    def test_data_loading_empty_file(self, mock_resources_path):
        """Test handling of empty CSV files."""
        with patch("pandas.read_csv", side_effect=pd.errors.EmptyDataError("No data")):
            with pytest.raises(pd.errors.EmptyDataError):
                load_dataset()

    @pytest.mark.unit
    def test_data_loading_parse_error(self, mock_resources_path):
        """Test handling of CSV parsing errors."""
        with patch("pandas.read_csv", side_effect=pd.errors.ParserError("Parse error")):
            with pytest.raises(pd.errors.ParserError):
                load_dataset()


class TestGraphLoading:
    """Test the load_graph function and graph construction."""

    @pytest.mark.unit
    def test_load_graph_success(self, mock_resources_path):
        """Test successful graph loading with proper structure."""
        # Mock node data
        node_data = pd.DataFrame(
            {
                "node": ["cluster_0", "cluster_1", "cluster_2"],
                "membership": ["[0, 1]", "[2, 3]", "[4]"],
                "cluster_id": [0, 1, 2],
            }
        )

        # Mock edge data
        edge_data = pd.DataFrame(
            {
                "source": ["cluster_0", "cluster_1"],
                "target": ["cluster_1", "cluster_2"],
                "weight": [0.75, 0.60],
            }
        )

        with patch("pandas.read_csv", side_effect=[node_data, edge_data]):
            result = load_graph()

            assert isinstance(result, nx.Graph)
            assert result.number_of_nodes() == 3
            assert result.number_of_edges() == 2

            # Check node attributes
            assert "membership" in result.nodes["cluster_0"]
            assert "cluster_id" in result.nodes["cluster_0"]

            # Check that membership was parsed from string to list
            membership = result.nodes["cluster_0"]["membership"]
            assert isinstance(membership, list)
            assert membership == [0, 1]

    @pytest.mark.unit
    def test_load_graph_membership_parsing_error(self, mock_resources_path):
        """Test handling of malformed membership strings."""
        # Mock node data with bad membership string
        node_data = pd.DataFrame(
            {
                "node": ["cluster_0"],
                "membership": ["invalid_list"],
                "cluster_id": [0],
            }
        )

        edge_data = pd.DataFrame({"source": [], "target": [], "weight": []})

        with patch("pandas.read_csv", side_effect=[node_data, edge_data]):
            result = load_graph()

            # Should handle the error gracefully by setting membership to empty list
            assert result.nodes["cluster_0"]["membership"] == []

    @pytest.mark.unit
    def test_load_graph_missing_files(self, mock_resources_path):
        """Test error handling when graph files are missing."""
        with patch(
            "pandas.read_csv",
            side_effect=FileNotFoundError("Graph files not found"),
        ):
            with pytest.raises(FileNotFoundError):
                load_graph()


class TestTargetMatchingData:
    """Test the generate_target_matching_data function."""

    @pytest.mark.unit
    def test_generate_target_matching_data_success(self, sample_raw_df):
        """Test successful generation of target matching dataset."""
        # Mock the retired plant data
        retired_data = pd.DataFrame(
            {
                "PNAME": ["Retired Plant A", "Retired Plant B"],
                "NAMEPCAP": ["[400.0, 500.0]", "[600.0]"],
                "CFACT": ["[0.45, 0.50]", "[0.62]"],
                "FUELG1": ['["Coal", "Coal"]', '["Coal"]'],
                "Percent_Capacity_Retiring": [1.0, 1.0],
                "Age": ["[40, 42]", "[35]"],
            }
        )

        with patch("retire.data.data.load_dataset", return_value=sample_raw_df):
            with patch(
                "retire.data.data.load_retired_plant_dataset",
                return_value=retired_data,
            ):
                result = generate_target_matching_data()

                assert isinstance(result, pd.DataFrame)
                # Should have original data plus retired plants
                assert len(result) == len(sample_raw_df) + len(retired_data)

                # Check that derived columns were created
                retired_subset = result.iloc[len(sample_raw_df) :]
                assert "Total Nameplate Capacity (MW)" in retired_subset.columns
                assert "ret_STATUS" in retired_subset.columns
                assert "Mapped Fuel Type" in retired_subset.columns


class TestUtilityFunctions:
    """Test utility functions used in data processing."""

    @pytest.mark.unit
    def test_most_frequent_string(self):
        """Test the _most_frequent_string utility function."""
        # Test with list input
        assert _most_frequent_string(["coal", "coal", "gas"]) == "coal"
        assert _most_frequent_string(["gas", "coal", "gas"]) == "gas"
        assert _most_frequent_string(["single"]) == "single"

        # Test with empty list
        assert _most_frequent_string([]) is None

        # Test with non-list input
        assert _most_frequent_string("not_a_list") is None

    @pytest.mark.unit
    def test_avg_ignore_nan(self):
        """Test the _avg_ignore_nan utility function."""
        # Test with list as string
        assert np.isclose(_avg_ignore_nan("[1.0, 2.0, 3.0]"), 2.0)
        # When the string cannot be parsed (e.g., contains `np.nan`), the
        # implementation returns np.nan — check with np.isnan instead of
        # np.isclose (np.isclose(nan, nan) is False).
        assert np.isnan(_avg_ignore_nan("[5.0, np.nan, 7.0]"))

        # Test with actual list
        assert np.isclose(_avg_ignore_nan([1.0, 2.0, 3.0]), 2.0)
        assert np.isclose(_avg_ignore_nan([5.0, np.nan, 7.0]), 6.0)

        # Test with empty list
        assert np.isnan(_avg_ignore_nan([]))
        assert np.isnan(_avg_ignore_nan("[]"))

        # Test with invalid string
        assert np.isnan(_avg_ignore_nan("invalid"))

    @pytest.mark.unit
    def test_average_lists(self):
        """Test the _average_lists utility function."""
        # Test with list as string
        assert np.isclose(_average_lists("[10, 20, 30]"), 20.0)

        # Test with actual list
        assert np.isclose(_average_lists([10, 20, 30]), 20.0)

        # Test with single value
        assert _average_lists(42) == 42

        # Test with invalid string
        assert _average_lists("invalid") == "invalid"


class TestDataValidation:
    """Test data validation and integrity checks."""

    @pytest.mark.unit
    def test_dataset_required_columns(self, sample_raw_df, mock_resources_path):
        """Test that loaded datasets contain required columns."""
        with patch("pandas.read_csv", return_value=sample_raw_df):
            df = load_dataset()

            required_cols = [
                "Plant Name",
                "ORISPL",
                "State",
                "LAT",
                "LON",
                "ret_STATUS",
                "Total Nameplate Capacity (MW)",
            ]

            missing_cols = set(required_cols) - set(df.columns)
            assert not missing_cols, f"Missing required columns: {missing_cols}"

    @pytest.mark.unit
    def test_dataset_data_types(self, sample_raw_df, mock_resources_path):
        """Test that loaded datasets have appropriate data types."""
        with patch("pandas.read_csv", return_value=sample_raw_df):
            df = load_dataset()

            # Test key numeric columns
            assert pd.api.types.is_numeric_dtype(df["LAT"])
            assert pd.api.types.is_numeric_dtype(df["LON"])
            assert pd.api.types.is_numeric_dtype(df["Total Nameplate Capacity (MW)"])
            assert pd.api.types.is_numeric_dtype(df["ret_STATUS"])

            # Test string columns
            assert pd.api.types.is_object_dtype(df["Plant Name"])
            assert pd.api.types.is_object_dtype(df["State"])

    @pytest.mark.unit
    def test_graph_node_attributes(self, mock_resources_path):
        """Test that graph nodes have required attributes."""
        node_data = pd.DataFrame(
            {
                "node": ["cluster_0", "cluster_1"],
                "membership": ["[0, 1]", "[2, 3]"],
                "cluster_id": [0, 1],
            }
        )

        edge_data = pd.DataFrame(
            {"source": ["cluster_0"], "target": ["cluster_1"], "weight": [0.75]}
        )

        with patch("pandas.read_csv", side_effect=[node_data, edge_data]):
            G = load_graph()

            for node in G.nodes():
                node_attrs = G.nodes[node]
                assert "membership" in node_attrs
                assert isinstance(node_attrs["membership"], list)

    @pytest.mark.unit
    def test_graph_edge_weights(self, mock_resources_path):
        """Test that graph edges have numeric weights."""
        node_data = pd.DataFrame(
            {"node": ["cluster_0", "cluster_1"], "membership": ["[0]", "[1]"]}
        )

        edge_data = pd.DataFrame(
            {"source": ["cluster_0"], "target": ["cluster_1"], "weight": [0.75]}
        )

        with patch("pandas.read_csv", side_effect=[node_data, edge_data]):
            G = load_graph()

            for source, target, attrs in G.edges(data=True):
                assert "weight" in attrs
                assert isinstance(attrs["weight"], (int, float))
                assert 0 <= attrs["weight"] <= 1  # Assuming normalized weights


class TestDataIntegration:
    """Integration tests for data loading workflow."""

    @pytest.mark.integration
    def test_data_graph_consistency(self, sample_raw_df, mock_resources_path):
        """Test that graph membership indices are consistent with dataset."""
        node_data = pd.DataFrame(
            {
                "node": ["cluster_0", "cluster_1"],
                "membership": ["[0, 1]", "[2, 3]"],
            }
        )

        edge_data = pd.DataFrame({"source": [], "target": [], "weight": []})

        with patch(
            "pandas.read_csv", side_effect=[sample_raw_df, node_data, edge_data]
        ):
            df = load_dataset()
            G = load_graph()

            # Check that all membership indices are valid
            for node in G.nodes():
                membership = G.nodes[node].get("membership", [])
                for idx in membership:
                    assert (
                        0 <= idx < len(df)
                    ), f"Invalid membership index {idx} for dataset of length {len(df)}"

    @pytest.mark.integration
    def test_target_matching_data_alignment(self, sample_raw_df):
        """Test that target matching data properly aligns original and retired plant data."""
        retired_data = pd.DataFrame(
            {
                "PNAME": ["Retired Plant"],
                "NAMEPCAP": ["[400.0]"],
                "CFACT": ["[0.45]"],
                "FUELG1": ['["Coal"]'],
                "Percent_Capacity_Retiring": [1.0],
                "Age": ["[40]"],
            }
        )

        with patch("retire.data.data.load_dataset", return_value=sample_raw_df):
            with patch(
                "retire.data.data.load_retired_plant_dataset",
                return_value=retired_data,
            ):
                result = generate_target_matching_data()

                # Check that columns are aligned
                original_cols = set(sample_raw_df.columns)
                result_cols = set(result.columns)
                assert original_cols.issubset(
                    result_cols
                ), "Some original columns missing from combined dataset"
