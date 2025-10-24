# tests/test_explore.py
"""
Unit tests for the Explore class.

Tests the visualization and exploration functionality of the Explore class,
focusing on data manipulation and helper methods while avoiding actual
plotting/display that would require a graphics environment.
"""

import pytest
import pandas as pd
import networkx as nx
import numpy as np
from unittest.mock import patch, Mock, MagicMock
import matplotlib.pyplot as plt

from retire.explore.explore import Explore


class TestExploreInitialization:
    """Test Explore class initialization."""

    @pytest.mark.unit
    def test_explore_init_success(self, sample_graph, sample_raw_df):
        """Test successful initialization of Explore object."""
        explore = Explore(sample_graph, sample_raw_df)

        assert explore.G is sample_graph
        assert explore.raw_df is sample_raw_df
        assert isinstance(explore.G, nx.Graph)
        assert isinstance(explore.raw_df, pd.DataFrame)

    @pytest.mark.unit
    def test_explore_init_with_empty_graph(self, sample_raw_df):
        """Test initialization with empty graph."""
        empty_graph = nx.Graph()
        explore = Explore(empty_graph, sample_raw_df)

        assert explore.G.number_of_nodes() == 0
        assert explore.G.number_of_edges() == 0
        assert len(explore.raw_df) > 0

    @pytest.mark.unit
    def test_explore_init_with_empty_dataframe(self, sample_graph):
        """Test initialization with empty DataFrame."""
        empty_df = pd.DataFrame()
        explore = Explore(sample_graph, empty_df)

        assert explore.G.number_of_nodes() > 0
        assert len(explore.raw_df) == 0


class TestExploreDataAssignment:
    """Test data assignment and group mapping methods."""

    @pytest.mark.unit
    def test_assign_group_ids_to_rawdf(self, sample_graph, sample_raw_df):
        """Test assignment of group IDs to raw DataFrame."""
        explore = Explore(sample_graph, sample_raw_df)
        result = explore.assign_group_ids_to_rawdf()

        assert isinstance(result, pd.DataFrame)
        assert "Group" in result.columns
        assert len(result) == len(sample_raw_df)

        # Check that group assignments are valid
        unique_groups = result["Group"].dropna().unique()
        assert len(unique_groups) <= sample_graph.number_of_nodes()

        # Group IDs should be integers
        for group_id in unique_groups:
            assert isinstance(group_id, (int, np.integer))

    @pytest.mark.unit
    def test_assign_group_ids_to_cleandf(
        self, sample_graph, sample_raw_df, sample_clean_df
    ):
        """Test assignment of group IDs to clean DataFrame."""
        explore = Explore(sample_graph, sample_raw_df)
        result = explore.assign_group_ids_to_cleandf(sample_clean_df)

        assert isinstance(result, pd.DataFrame)
        assert "Group" in result.columns
        assert len(result) == len(sample_clean_df)

        # Should preserve original columns
        for col in sample_clean_df.columns:
            assert col in result.columns

    @pytest.mark.unit
    def test_group_assignment_consistency(self, sample_graph, sample_raw_df):
        """Test that group assignments are consistent across calls."""
        explore = Explore(sample_graph, sample_raw_df)

        result1 = explore.assign_group_ids_to_rawdf()
        result2 = explore.assign_group_ids_to_rawdf()

        pd.testing.assert_frame_equal(result1, result2)


class TestExploreTargetMethods:
    """Test target node identification and distance calculation methods."""

    @pytest.mark.unit
    def test_get_target_nodes(self, sample_graph, sample_raw_df):
        """Test target node identification based on threshold."""
        # Ensure sample data has the required column
        sample_raw_df["Percent Capacity Retiring"] = [0.0, 0.3, 0.8, 0.1]

        explore = Explore(sample_graph, sample_raw_df)
        targets = explore.get_target_nodes(component=0, threshold=0.5)

        assert isinstance(targets, dict)
        # Check that returned targets have values above threshold
        for node, value in targets.items():
            assert value > 0.5
            assert node in sample_graph.nodes()

    @pytest.mark.unit
    def test_get_target_nodes_no_targets(self, sample_graph, sample_raw_df):
        """Test target node identification when no nodes meet threshold."""
        # Set all values below threshold
        sample_raw_df["Percent Capacity Retiring"] = [0.1, 0.2, 0.3, 0.1]

        explore = Explore(sample_graph, sample_raw_df)
        targets = explore.get_target_nodes(component=0, threshold=0.5)

        assert isinstance(targets, dict)
        assert len(targets) == 0

    @pytest.mark.unit
    def test_get_shortest_distances_to_targets(self, sample_graph, sample_raw_df):
        """Test shortest distance calculation to target nodes."""
        explore = Explore(sample_graph, sample_raw_df)

        # Define some targets (use actual node names from sample_graph)
        targets = {"cluster_0": 0.8, "cluster_1": 0.6}

        distances = explore.get_shortest_distances_to_targets(
            component=0, targets=targets
        )

        assert isinstance(distances, dict)
        # All nodes in the component should have distances
        for node in distances:
            assert node in sample_graph.nodes()
            assert isinstance(distances[node], (int, float))
            assert distances[node] >= 0


class TestExploreVisualizationHelpers:
    """Test visualization helper methods without actual plotting."""

    @pytest.mark.unit
    def test_generate_thema_graph_labels_average(self, sample_graph, sample_raw_df):
        """Test label generation using average method."""
        explore = Explore(sample_graph, sample_raw_df)

        color_dict, labels_dict = explore.generate_THEMAGrah_labels(
            G=sample_graph, col="ret_STATUS", color_method="average"
        )

        assert isinstance(color_dict, dict)
        assert isinstance(labels_dict, dict)
        assert len(color_dict) == sample_graph.number_of_nodes()
        assert len(labels_dict) == sample_graph.number_of_nodes()

        # Check that all nodes are represented
        for node in sample_graph.nodes():
            assert node in color_dict
            assert node in labels_dict

    @pytest.mark.unit
    def test_generate_thema_graph_labels_community(self, sample_graph, sample_raw_df):
        """Test label generation using community method."""
        explore = Explore(sample_graph, sample_raw_df)

        color_dict, labels_dict = explore.generate_THEMAGrah_labels(
            G=sample_graph, color_method="community"
        )

        assert isinstance(color_dict, dict)
        assert isinstance(labels_dict, dict)

        # Community IDs should be integers
        for node, community_id in color_dict.items():
            assert isinstance(community_id, int)
            assert community_id >= 0

    @pytest.mark.unit
    def test_generate_thema_graph_labels_invalid_method(
        self, sample_graph, sample_raw_df
    ):
        """Test label generation with invalid color method."""
        explore = Explore(sample_graph, sample_raw_df)

        with pytest.raises(ValueError, match="Invalid color_method"):
            explore.generate_THEMAGrah_labels(
                G=sample_graph, color_method="invalid_method"
            )


class TestExploreDrawingMethods:
    """Test drawing methods with mocked matplotlib to avoid display."""

    @pytest.mark.plotting
    @patch("matplotlib.pyplot.subplots")
    @patch("networkx.spring_layout")
    @patch("networkx.draw_networkx_nodes")
    @patch("networkx.draw_networkx_edges")
    def test_draw_graph_helper(
        self,
        mock_edges,
        mock_nodes,
        mock_layout,
        mock_subplots,
        sample_graph,
        sample_raw_df,
    ):
        """Test the draw_graph_helper method without actual plotting."""
        # Mock matplotlib objects
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)
        mock_layout.return_value = {"cluster_0": [0, 0], "cluster_1": [1, 1]}

        explore = Explore(sample_graph, sample_raw_df)
        fig, ax = explore.drawGraph_helper(sample_graph)

        # Check that matplotlib functions were called
        mock_subplots.assert_called_once()
        mock_layout.assert_called_once()
        mock_nodes.assert_called_once()
        mock_edges.assert_called_once()

        assert fig is mock_fig
        assert ax is mock_ax

    @pytest.mark.plotting
    @patch("matplotlib.pyplot.subplots")
    @patch("networkx.spring_layout")
    @patch("networkx.draw_networkx_nodes")
    @patch("networkx.draw_networkx_edges")
    def test_draw_graph_with_coloring(
        self,
        mock_edges,
        mock_nodes,
        mock_layout,
        mock_subplots,
        sample_graph,
        sample_raw_df,
    ):
        """Test graph drawing with node coloring."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)
        mock_layout.return_value = {"cluster_0": [0, 0], "cluster_1": [1, 1]}

        explore = Explore(sample_graph, sample_raw_df)
        fig, ax = explore.drawGraph_helper(
            sample_graph, col="ret_STATUS", show_colorbar=True
        )

        # Verify plotting functions were called
        mock_subplots.assert_called_once()
        mock_nodes.assert_called_once()
        mock_edges.assert_called_once()

    @pytest.mark.plotting
    @patch("matplotlib.pyplot.subplots")
    @patch("networkx.connected_components")
    def test_draw_component(
        self, mock_components, mock_subplots, sample_graph, sample_raw_df
    ):
        """Test drawing of specific graph component."""
        # Mock connected components
        component_nodes = [["cluster_0", "cluster_1"], ["cluster_2"]]
        mock_components.return_value = component_nodes

        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        explore = Explore(sample_graph, sample_raw_df)

        with patch.object(
            explore, "drawGraph_helper", return_value=(mock_fig, mock_ax)
        ) as mock_helper:
            fig, ax = explore.drawComponent(component=0)

            # Should call the helper with a subgraph
            mock_helper.assert_called_once()
            assert fig is mock_fig
            assert ax is mock_ax


class TestExploreMapMethods:
    """Test geographic mapping methods."""

    @pytest.mark.plotting
    @patch("plotly.express.scatter_geo")
    def test_draw_map(self, mock_scatter_geo, sample_graph, sample_raw_df):
        """Test geographic map creation."""
        # Mock plotly figure
        mock_fig = Mock()
        mock_fig.update_traces = Mock()
        mock_fig.update_geos = Mock()
        mock_fig.update_layout = Mock()
        mock_fig.show = Mock()
        mock_scatter_geo.return_value = mock_fig

        explore = Explore(sample_graph, sample_raw_df)
        fig, ax = explore.drawMap()

        # Check that plotly was called
        mock_scatter_geo.assert_called_once()
        assert fig is mock_fig
        assert ax is None  # Maps return None for ax


class TestExploreDataValidation:
    """Test data validation and error handling in Explore methods."""

    @pytest.mark.unit
    def test_explore_with_mismatched_graph_data(self, sample_raw_df):
        """Test behavior when graph membership indices don't match DataFrame."""
        # Create graph with invalid membership indices
        bad_graph = nx.Graph()
        bad_graph.add_node(
            "cluster_0", membership=[10, 11, 12]
        )  # Indices beyond DataFrame

        explore = Explore(bad_graph, sample_raw_df)

        # This should not crash but may produce unexpected results
        result = explore.assign_group_ids_to_rawdf()
        assert isinstance(result, pd.DataFrame)
        assert "Group" in result.columns

    @pytest.mark.unit
    def test_explore_with_missing_columns(self, sample_graph):
        """Test behavior when required columns are missing from DataFrame."""
        minimal_df = pd.DataFrame(
            {"Plant Name": ["Plant A", "Plant B"], "Some_Other_Col": [1, 2]}
        )

        explore = Explore(sample_graph, minimal_df)

        # Should not crash during initialization
        assert explore.raw_df is minimal_df

        # But may fail when trying to use specific columns
        with pytest.raises((KeyError, AttributeError)):
            explore.get_target_nodes(component=0, col="Missing_Column")

    @pytest.mark.unit
    def test_explore_empty_membership(self, sample_raw_df):
        """Test handling of nodes with empty membership lists."""
        graph_empty_membership = nx.Graph()
        graph_empty_membership.add_node("cluster_0", membership=[])
        graph_empty_membership.add_node("cluster_1", membership=[0, 1])

        explore = Explore(graph_empty_membership, sample_raw_df)

        # Should handle empty memberships gracefully
        targets = explore.get_target_nodes(component=0)
        assert isinstance(targets, dict)


class TestExploreIntegration:
    """Integration tests for Explore class workflow."""

    @pytest.mark.integration
    def test_typical_exploration_workflow(self, sample_graph, sample_raw_df):
        """Test a typical exploration workflow."""
        # Add required column for target identification
        sample_raw_df["Percent Capacity Retiring"] = [0.1, 0.7, 0.9, 0.2]

        explore = Explore(sample_graph, sample_raw_df)

        # Step 1: Assign group IDs
        df_with_groups = explore.assign_group_ids_to_rawdf()
        assert "Group" in df_with_groups.columns

        # Step 2: Identify targets
        targets = explore.get_target_nodes(component=0, threshold=0.5)
        assert isinstance(targets, dict)

        # Step 3: Calculate distances (if targets exist)
        if targets:
            distances = explore.get_shortest_distances_to_targets(
                component=0, targets=targets
            )
            assert isinstance(distances, dict)
            assert len(distances) > 0

    @pytest.mark.integration
    def test_data_consistency_across_methods(self, sample_graph, sample_raw_df):
        """Test that data remains consistent across different method calls."""
        explore = Explore(sample_graph, sample_raw_df)

        # Multiple calls should return consistent results
        groups1 = explore.assign_group_ids_to_rawdf()
        groups2 = explore.assign_group_ids_to_rawdf()

        pd.testing.assert_frame_equal(groups1, groups2)

        # Graph should remain unchanged
        initial_nodes = explore.G.number_of_nodes()
        initial_edges = explore.G.number_of_edges()

        # Perform various operations
        explore.assign_group_ids_to_rawdf()
        explore.get_target_nodes(component=0)

        # Graph should be unchanged
        assert explore.G.number_of_nodes() == initial_nodes
        assert explore.G.number_of_edges() == initial_edges
