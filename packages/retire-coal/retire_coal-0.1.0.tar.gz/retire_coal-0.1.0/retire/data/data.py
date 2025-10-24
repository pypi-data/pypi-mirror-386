# retire/data.py

import ast
import numpy as np
import pandas as pd
import networkx as nx
from collections import Counter
from importlib.resources import files


def load_dataset():
    """
    Load the US coal plants dataset from the package resources.

    Returns
    -------
    pandas.DataFrame
        Complete US coal plants dataset containing plant characteristics,
        retirement status, contextual vulnerabilities, and associated metadata.
        Includes columns for plant location, capacity, age, retirement planning,
        economic factors, and environmental considerations.

    Raises
    ------
    FileNotFoundError
        If the dataset file does not exist at the specified path.
    pd.errors.EmptyDataError
        If the CSV file is empty.
    pd.errors.ParserError
        If the CSV file cannot be parsed.

    Examples
    --------
    >>> from retire.data import load_dataset
    >>> df = load_dataset()
    >>> print(df.shape)
    (914, 45)
    >>> print(df.columns[:5].tolist())
    ['Plant Name', 'ORISPL', 'State', 'County', 'LAT']
    """
    path = files("retire").joinpath("resources/us_coal_plants_dataset.csv")
    return pd.read_csv(path)


def load_clean_dataset():
    """
    Load the cleaned and scaled US coal plant dataset.

    This dataset has undergone preprocessing including missing value imputation,
    feature scaling, and normalization for use in machine learning models and
    statistical analysis.

    Returns
    -------
    pandas.DataFrame
        Cleaned and scaled coal plant dataset with standardized numerical
        features and processed categorical variables. All features are
        normalized to facilitate clustering and similarity analysis.

    Examples
    --------
    >>> from retire.data import load_clean_dataset
    >>> clean_df = load_clean_dataset()
    >>> print(clean_df.dtypes.value_counts())
    float64    42
    int64       3
    dtype: int64
    """
    path = files("retire").joinpath("resources/clean_scaled_us_coalplant_dataset.csv")
    return pd.read_csv(path)


def load_projection():
    """
    Load the projected US coal plant dataset with future scenario modeling.

    This dataset contains projections and forecasts for coal plant operations
    under various policy and economic scenarios, including retirement timing
    predictions and capacity factor estimates.

    Returns
    -------
    pandas.DataFrame
        Projected coal plant dataset with scenario-based forecasts for
        retirement timing, capacity utilization, and economic viability
        under different policy environments.

    Examples
    --------
    >>> from retire.data import load_projection
    >>> proj_df = load_projection()
    >>> scenario_cols = [col for col in proj_df.columns if 'scenario' in col.lower()]
    >>> print(f"Available scenarios: {len(scenario_cols)}")
    """
    path = files("retire").joinpath("resources/projected_us_coalplant_dataset.csv")
    return pd.read_csv(path)


def load_graph():
    """
    Load the coal plant network graph from package resources.

    Constructs a NetworkX graph representing relationships between coal plant
    clusters based on similarity metrics and contextual factors. Nodes represent
    plant clusters, and edges represent similarity relationships weighted by
    various plant characteristics.

    Returns
    -------
    networkx.Graph
        Network graph with nodes representing coal plant clusters and edges
        representing similarity relationships. Node attributes include:
        - membership: list of plant indices belonging to the cluster
        - cluster_id: unique identifier for the cluster
        Edge attributes include:
        - weight: similarity strength between clusters

    Raises
    ------
    FileNotFoundError
        If the graph node or edge CSV files do not exist.
    ValueError
        If the membership field cannot be parsed as a list.

    Examples
    --------
    >>> from retire.data import load_graph
    >>> G = load_graph()
    >>> print(f"Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    Graph has 314 nodes and 1247 edges
    >>> # Check node attributes
    >>> node_attrs = list(G.nodes(data=True))[0]
    >>> print(f"Node attributes: {list(node_attrs[1].keys())}")
    """

    node_path = files("retire").joinpath("resources/graph/graphnode_df.csv")
    edge_path = files("retire").joinpath("resources/graph/graphedge_df.csv")

    # Load dataframes
    node_df = pd.read_csv(node_path)
    edge_df = pd.read_csv(edge_path)

    # Initialize graph
    G = nx.Graph()

    # Add nodes with attributes (including parsing membership if needed)
    for _, row in node_df.iterrows():
        node_id = row["node"] if "node" in row else row[0]
        attrs = row.drop("node").to_dict() if "node" in row else row[1:].to_dict()

        # Safely parse membership field if it's a string
        if "membership" in attrs and isinstance(attrs["membership"], str):
            try:
                attrs["membership"] = ast.literal_eval(attrs["membership"])
            except (ValueError, SyntaxError):
                attrs["membership"] = []  # or raise an error if preferred

        G.add_node(node_id, **attrs)

    # Add edges with attributes
    G.add_edges_from(
        [
            (row["source"], row["target"], row.drop(["source", "target"]).to_dict())
            for _, row in edge_df.iterrows()
        ]
    )

    return G


def load_generator_level_dataset():
    """
    Load the generator-level US coal plants dataset.

    Provides detailed information at the individual generator unit level,
    including technical specifications, operational history, and retirement
    planning for each coal-fired generating unit in the US fleet.

    Returns
    -------
    pandas.DataFrame
        Generator-level dataset with detailed technical and operational
        information for individual coal-fired generating units. Includes
        capacity, age, efficiency metrics, emissions data, and retirement
        status for each generator.

    Raises
    ------
    FileNotFoundError
        If the dataset file does not exist at the specified path.
    pd.errors.EmptyDataError
        If the CSV file is empty.
    pd.errors.ParserError
        If the CSV file cannot be parsed.

    Examples
    --------
    >>> from retire.data import load_generator_level_dataset
    >>> gen_df = load_generator_level_dataset()
    >>> print(f"Total generators: {len(gen_df)}")
    >>> # Group by plant to see generator counts per plant
    >>> gens_per_plant = gen_df.groupby('ORISPL').size()
    >>> print(f"Average generators per plant: {gens_per_plant.mean():.1f}")
    """
    path = files("retire").joinpath("resources/generator_level_dataset.csv")
    return pd.read_csv(path)


def load_retired_plant_dataset():
    """
    Load the 2020-2023 set of Retired US Coal Plants.

    Dataset Overview
    ----------------
    This dataset contains detailed information on U.S. coal plants that retired between 2020 and 2023.

    Because our analytical framework integrates static snapshots of political, demographic, public-opinion,
    and other contextual variables drawn from multiple data sources (see Supplemental Information A.1),
    we restrict the dataset to this recent four-year period. This window captures the most current wave
    of coal plant retirements while maintaining sufficient data coverage across sources.

    Not all variables are available for every plant. Some static datasets could not be applied uniformly
    because data for certain years were unavailable or incomplete. Compiling this dataset required
    cross-referencing and harmonizing data from numerous repositories, and additional work could extend
    this compilation further—such as incorporating older retirements for validation against plants that
    retired prior to 2020.

    Returns
    -------
    pd.DataFrame
        A structured dataset where each row represents a retired coal plant (2020–2023),
        and columns capture plant-level operational, policy, demographic, and contextual variables.

    Raises
    ------
    FileNotFoundError
        If the dataset file does not exist at the specified path.
    pd.errors.EmptyDataError
        If the CSV file is empty.
    pd.errors.ParserError
        If the CSV file cannot be parsed.

    Examples
    --------
    >>> from retire.data import load_generator_level_dataset
    >>> gen_df = load_generator_level_dataset()
    >>> print(f"Total generators: {len(gen_df)}")
    >>> # Group by plant to see generator counts per plant
    >>> gens_per_plant = gen_df.groupby('ORISPL').size()
    >>> print(f"Average generators per plant: {gens_per_plant.mean():.1f}")
    """
    path = files("retire").joinpath("resources/raw_2020-2023_retired_coalplants.csv")
    return pd.read_csv(path)


def generate_target_matching_data() -> pd.DataFrame:
    """
    Prepare a unified dataset combining active coal plants with retired plants,
    suitable for target matching within our mapper graph framework.

    This function performs several key steps:
    1. Loads the raw active coal plant dataset (`coal_raw`) and the retired plant dataset.
    2. Renames retired plant columns to align with our internal dataset conventions.
    3. Derives new variables:
       - Total Nameplate Capacity (MW)
       - Average Capacity Factor
       - Mapped Fuel Type
       - Retirement status (`ret_STATUS`)
       - Age (averaged where multiple generators exist)
    4. Aligns the retired plant dataset with the original dataset, keeping only shared columns.
    5. Concatenates the retired and active datasets into a single DataFrame.

    Notes
    -----
    - Because the retired plant dataset originates from 2020-2023, some static data sources
      cannot be applied consistently (data may be missing or unavailable for these years).
    - This preparation is necessary for mapping retired plants into our existing
      graph landscape: determining which component and node a new plant most strongly fits.

    Returns
    -------
    pd.DataFrame
        A combined dataset of active and retired coal plants with harmonized column names
        and derived variables ready for target matching.
    """
    coal_raw = load_dataset()
    new_data = load_retired_plant_dataset()
    new_data = new_data.rename(columns=COL_NAME_MAP)

    # Derive new columns
    new_data["Total Nameplate Capacity (MW)"] = new_data["NAMEPCAP"].apply(
        _avg_ignore_nan
    )

    new_data["Average Capacity Factor"] = new_data["CFACT"].apply(_avg_ignore_nan)
    new_data["Mapped Fuel Type"] = new_data["FUELG1"].apply(_most_frequent_string)
    new_data["ret_STATUS"] = new_data["Percent_Capacity_Retiring"] + 1
    new_data["Age"] = new_data["Age"].apply(_average_lists)

    # Align with original columns
    new_data = new_data[coal_raw.columns.intersection(new_data.columns)]
    new_data_aligned = new_data.reindex(columns=coal_raw.columns)
    combined = pd.concat([coal_raw, new_data_aligned], ignore_index=True)

    return combined


# ---------- Target Matching Data Prep Utilities ----------


def _most_frequent_string(val_list):
    """Return the most frequent string in a list, or None if empty."""
    if isinstance(val_list, list):
        counter = Counter(val_list)
        return counter.most_common(1)[0][0] if counter else None
    return None


def _avg_ignore_nan(val):
    if isinstance(val, str):
        try:
            val = ast.literal_eval(val)
        except:
            return np.nan
    if isinstance(val, list) and val:
        return np.nanmean([float(v) for v in val])
    return np.nan


def _average_lists(val):
    if isinstance(val, str):
        try:
            val = ast.literal_eval(val)
        except:
            return val
    if isinstance(val, list) and val:
        return np.nanmean([float(v) for v in val])
    return val


# ╭──────────────────────────────────────────────────────────────────────────────────────────────────╮
# │    Fixed mappings from the retired plants dataset --> the study dataset from `load_dataset()`    |
# ╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

COL_NAME_MAP = {
    "PNAME": "Plant Name",
    "National percentile for Demographic Index (within 3 miles of plant)": "National percentile for Demographic Index",
    "National percentile for People of Color Population (within 3 miles of plant)": "National percentile for People of Color Population",
    "National percentile for Low Income Population (within 3 miles of plant)": "National percentile for Low Income Population",
    "National percentile for Population with Less Than High School Education (within 3 miles of plant)": "National percentile for Population with Less Than High School Education",
}

USED_COLUMNS = [
    "ret_STATUS",
    "Total Nameplate Capacity (MW)",
    "Retiring Capacity",
    "Average Capacity Factor",
    "Generator Size Weighted Capacity Factor (%)",
    "Age",
    "Generator Size Weighted Age",
    "Summed Generator annual net generation (MWh)",
    "Percent Capacity Retiring",
    "2022 SO2 Emissions (tons)",
    "2021 vs 2022 SO2 Emissions (%)",
    "2022 SO2 Emission Rate (lb/mmBtu)",
    "2022 NOX Emissions (tons)",
    "2022 NOX Emission Rate (lb/mmBtu)",
    "2022 CO2 Emissions (tons)",
    "2021 vs 2022 CO2 Emissions (%)",
    "2022 CO2 Emission Rate (lb/mmBtu)",
    "2022 Hg Emissions (lbs)",
    "2022 Hg Emission Rate (lb/TBtu)",
    "Facility has one or more low-emitting EGUs (LEE) units that do not report hourly emissions",
    "eGRID subregion coal generation percent (resource mix)",
    "eGRID subregion gas generation percent (resource mix)",
    "eGRID subregion wind generation percent (resource mix)",
    "eGRID subregion solar generation percent (resource mix)",
    "Hospital Admits, All Respiratory",
    "Infant Mortality",
    "Hospital Admits, Cardiovascular (except heart attacks)",
    "$ Work Loss Days",
    "$ Mortality (low estimate)",
    "$ Asthma Exacerbation",
    "total population (ACS2018)",
    "National percentile for Demographic Index",
    "National percentile for People of Color Population",
    "National percentile for Low Income Population",
    "National percentile for Population with Less Than High School Education",
    "PM 2.5 Emssions (tons)",
    "PM 2.5 Emission Rate (lb/MWh)",
    "Average PM Results (lb/mmBtu)",
    "Mapped Fuel Type",
    "Number of Coal Generators",
    "Total Cost of Emissions Control Equiptment Retrofits Installed since 2012 ($)",
    "Plant Coal Percentage (%)",
    "2020 Net Cashflow",
    "Average Cashflow",
    "Forward Costs",
    "Coal Debt Securitization Policy",
    "State coal generation percent (resource mix)",
    "State gas generation percent (resource mix)",
    "LAT",
    "LON",
    "Plant Name",
]
