# tests/test_retire.py
"""
Unit tests for the main Retire class.

Tests the core functionality of the Retire class including initialization,
data loading, and access to manuscript results.
"""

import pytest
import pandas as pd
import networkx as nx
from unittest.mock import patch, Mock

from retire.retire import Retire


class TestRetireInitialization:
    """Test Retire class initialization and basic functionality."""

    @pytest.mark.unit
    def test_retire_init_success(self, sample_raw_df, sample_graph):
        """Test successful initialization of Retire object."""
        with patch("retire.retire.load_dataset", return_value=sample_raw_df):
            with patch("retire.retire.load_graph", return_value=sample_graph):
                retire_obj = Retire()

                assert isinstance(retire_obj.raw_df, pd.DataFrame)
                assert isinstance(retire_obj.graph, nx.Graph)
                assert len(retire_obj.raw_df) > 0
                assert retire_obj.graph.number_of_nodes() > 0

    @pytest.mark.unit
    def test_retire_init_data_loading_failure(self):
        """Test handling of data loading failures during initialization."""
        with patch(
            "retire.retire.load_dataset",
            side_effect=FileNotFoundError("Dataset not found"),
        ):
            with pytest.raises(FileNotFoundError):
                Retire()

        with patch("retire.retire.load_dataset", return_value=pd.DataFrame()):
            with patch(
                "retire.retire.load_graph",
                side_effect=FileNotFoundError("Graph not found"),
            ):
                with pytest.raises(FileNotFoundError):
                    Retire()

    @pytest.mark.unit
    def test_retire_attributes_exist(self, sample_raw_df, sample_graph):
        """Test that Retire object has expected attributes after initialization."""
        with patch("retire.retire.load_dataset", return_value=sample_raw_df):
            with patch("retire.retire.load_graph", return_value=sample_graph):
                retire_obj = Retire()

                assert hasattr(retire_obj, "raw_df")
                assert hasattr(retire_obj, "graph")
                assert retire_obj.raw_df is not None
                assert retire_obj.graph is not None


class TestRetireGroupReport:
    """Test the get_group_report method."""

    @pytest.mark.unit
    def test_get_group_report_success(
        self, sample_raw_df, sample_graph, sample_group_analysis
    ):
        """Test successful retrieval of group analysis report."""
        with patch("retire.retire.load_dataset", return_value=sample_raw_df):
            with patch("retire.retire.load_graph", return_value=sample_graph):
                with patch("pandas.read_csv", return_value=sample_group_analysis):
                    retire_obj = Retire()
                    result = retire_obj.get_group_report()

                    assert isinstance(result, pd.DataFrame)
                    assert len(result) > 0
                    # Check for expected columns in group analysis
                    expected_cols = ["Group", "Plant_Count", "Avg_Capacity_MW"]
                    for col in expected_cols:
                        if col in sample_group_analysis.columns:
                            assert col in result.columns

    @pytest.mark.unit
    def test_get_group_report_file_not_found(self, sample_raw_df, sample_graph):
        """Test handling when group analysis file is missing."""
        with patch("retire.retire.load_dataset", return_value=sample_raw_df):
            with patch("retire.retire.load_graph", return_value=sample_graph):
                with patch(
                    "pandas.read_csv",
                    side_effect=FileNotFoundError("Group analysis file not found"),
                ):
                    retire_obj = Retire()
                    with pytest.raises(FileNotFoundError):
                        retire_obj.get_group_report()

    @pytest.mark.unit
    def test_get_group_report_empty_file(self, sample_raw_df, sample_graph):
        """Test handling when group analysis file is empty."""
        with patch("retire.retire.load_dataset", return_value=sample_raw_df):
            with patch("retire.retire.load_graph", return_value=sample_graph):
                with patch("pandas.read_csv", return_value=pd.DataFrame()):
                    retire_obj = Retire()
                    result = retire_obj.get_group_report()

                    assert isinstance(result, pd.DataFrame)
                    assert len(result) == 0


class TestRetireTargetExplanations:
    """Test the get_target_explanations method."""

    @pytest.mark.unit
    def test_get_target_explanations_success(
        self, sample_raw_df, sample_graph, sample_target_explanations
    ):
        """Test successful retrieval of target explanations."""
        with patch("retire.retire.load_dataset", return_value=sample_raw_df):
            with patch("retire.retire.load_graph", return_value=sample_graph):
                with patch("pandas.read_csv", return_value=sample_target_explanations):
                    retire_obj = Retire()
                    result = retire_obj.get_target_explanations()

                    assert isinstance(result, pd.DataFrame)
                    assert len(result) > 0
                    # Check for expected columns
                    expected_cols = [
                        "ORISPL",
                        "Plant_Name",
                        "Priority",
                        "Explanation",
                    ]
                    for col in expected_cols:
                        if col in sample_target_explanations.columns:
                            assert col in result.columns

    @pytest.mark.unit
    def test_get_target_explanations_file_not_found(self, sample_raw_df, sample_graph):
        """Test handling when target explanations file is missing."""
        with patch("retire.retire.load_dataset", return_value=sample_raw_df):
            with patch("retire.retire.load_graph", return_value=sample_graph):
                with patch(
                    "pandas.read_csv",
                    side_effect=FileNotFoundError("Explanations file not found"),
                ):
                    retire_obj = Retire()
                    with pytest.raises(FileNotFoundError):
                        retire_obj.get_target_explanations()

    @pytest.mark.unit
    def test_get_target_explanations_data_structure(
        self, sample_raw_df, sample_graph, sample_target_explanations
    ):
        """Test that target explanations have expected data structure."""
        with patch("retire.retire.load_dataset", return_value=sample_raw_df):
            with patch("retire.retire.load_graph", return_value=sample_graph):
                with patch("pandas.read_csv", return_value=sample_target_explanations):
                    retire_obj = Retire()
                    result = retire_obj.get_target_explanations()

                    # Check that we have plant-level data
                    if "ORISPL" in result.columns:
                        assert (
                            result["ORISPL"].dtype == "object"
                        )  # Should be string IDs

                    # Check for scoring columns if they exist
                    score_cols = [col for col in result.columns if "Score" in col]
                    for col in score_cols:
                        assert pd.api.types.is_numeric_dtype(result[col])


class TestRetirePlantLevelAnalysis:
    """Test the get_plant_level_analysis method (currently not implemented)."""

    @pytest.mark.unit
    def test_get_plant_level_analysis_not_implemented(
        self, sample_raw_df, sample_graph
    ):
        """Test that get_plant_level_analysis correctly indicates it's not implemented."""
        with patch("retire.retire.load_dataset", return_value=sample_raw_df):
            with patch("retire.retire.load_graph", return_value=sample_graph):
                retire_obj = Retire()
                result = retire_obj.get_plant_level_analysis("12345")

                # Currently returns None as it's not implemented
                assert result is None

    @pytest.mark.unit
    def test_get_plant_level_analysis_with_invalid_orispl(
        self, sample_raw_df, sample_graph
    ):
        """Test plant-level analysis with invalid ORISPL input."""
        with patch("retire.retire.load_dataset", return_value=sample_raw_df):
            with patch("retire.retire.load_graph", return_value=sample_graph):
                retire_obj = Retire()

                # Test with various invalid inputs
                assert retire_obj.get_plant_level_analysis(None) is None
                assert retire_obj.get_plant_level_analysis("") is None
                assert retire_obj.get_plant_level_analysis("invalid_id") is None


class TestRetireDataConsistency:
    """Test consistency between raw data and graph."""

    @pytest.mark.integration
    def test_raw_df_graph_consistency(self, sample_raw_df, sample_graph):
        """Test that the graph membership indices are consistent with raw_df."""
        with patch("retire.retire.load_dataset", return_value=sample_raw_df):
            with patch("retire.retire.load_graph", return_value=sample_graph):
                retire_obj = Retire()

                # Check that graph membership indices are valid for the dataset
                for node in retire_obj.graph.nodes():
                    membership = retire_obj.graph.nodes[node].get("membership", [])
                    for idx in membership:
                        assert (
                            0 <= idx < len(retire_obj.raw_df)
                        ), f"Graph node {node} has invalid membership index {idx}"

    @pytest.mark.integration
    def test_raw_df_structure_validation(self, sample_raw_df, sample_graph):
        """Test that raw_df has the expected structure for analysis."""
        with patch("retire.retire.load_dataset", return_value=sample_raw_df):
            with patch("retire.retire.load_graph", return_value=sample_graph):
                retire_obj = Retire()

                df = retire_obj.raw_df

                # Check key columns exist
                key_columns = [
                    "Plant Name",
                    "ORISPL",
                    "ret_STATUS",
                    "Total Nameplate Capacity (MW)",
                    "LAT",
                    "LON",
                ]

                for col in key_columns:
                    assert col in df.columns, f"Missing key column: {col}"

                # Check data types
                assert pd.api.types.is_numeric_dtype(df["ret_STATUS"])
                assert pd.api.types.is_numeric_dtype(df["LAT"])
                assert pd.api.types.is_numeric_dtype(df["LON"])

    @pytest.mark.integration
    def test_graph_structure_validation(self, sample_raw_df, sample_graph):
        """Test that graph has the expected structure for analysis."""
        with patch("retire.retire.load_dataset", return_value=sample_raw_df):
            with patch("retire.retire.load_graph", return_value=sample_graph):
                retire_obj = Retire()

                G = retire_obj.graph

                # Basic graph properties
                assert G.number_of_nodes() > 0
                assert isinstance(G, nx.Graph)

                # Check node attributes
                for node in G.nodes():
                    node_attrs = G.nodes[node]
                    assert "membership" in node_attrs
                    assert isinstance(node_attrs["membership"], list)


class TestRetireUsagePatterns:
    """Test common usage patterns for the Retire class."""

    @pytest.mark.integration
    def test_typical_workflow(
        self,
        sample_raw_df,
        sample_graph,
        sample_group_analysis,
        sample_target_explanations,
    ):
        """Test a typical analysis workflow using the Retire class."""
        with patch("retire.retire.load_dataset", return_value=sample_raw_df):
            with patch("retire.retire.load_graph", return_value=sample_graph):
                with patch(
                    "pandas.read_csv",
                    side_effect=[
                        sample_group_analysis,
                        sample_target_explanations,
                    ],
                ):
                    # Initialize
                    retire_obj = Retire()

                    # Access data
                    raw_data = retire_obj.raw_df
                    graph = retire_obj.graph

                    assert len(raw_data) > 0
                    assert graph.number_of_nodes() > 0

                    # Get analysis results
                    group_report = retire_obj.get_group_report()
                    explanations = retire_obj.get_target_explanations()

                    assert len(group_report) > 0
                    assert len(explanations) > 0
