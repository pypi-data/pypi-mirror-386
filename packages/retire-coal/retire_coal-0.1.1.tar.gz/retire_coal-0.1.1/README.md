# Retire Coal

<p align="center">
  <a href="https://github.com/Krv-Analytics/retire/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/Krv-Analytics/retire?style=flat-square" alt="Contributors">
  </a>
  <a href="LICENSE.md">
    <img src="https://img.shields.io/badge/License-BSD%203--Clause-blue?style=flat-square" alt="License: BSD 3-Clause">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python" alt="Python 3.10+">
  </a>
  <a href="https://pypi.org/project/retire-coal/">
    <img src="https://img.shields.io/pypi/v/retire-coal?style=flat-square" alt="PyPI version">
  </a>
  <a href="docs/">
    <img src="https://img.shields.io/badge/docs-available-green?style=flat-square" alt="Documentation">
  </a>
  <br>
  <a href="https://krv.ai">
    <img src="https://img.shields.io/badge/web-krv.ai-black?style=flat-square&logo=vercel" alt="Website">
  </a>
  <a href="https://www.linkedin.com/company/krv-analytics">
    <img src="https://img.shields.io/badge/LinkedIn-Krv%20Analytics-blue?style=flat-square&logo=linkedin" alt="LinkedIn">
  </a>
  <a href="mailto:team@krv.ai">
    <img src="https://img.shields.io/badge/Email-team@krv.ai-fe2b27?style=flat-square&logo=gmail" alt="Email">
  </a>
  <br>
  <a href="https://www.nature.com/articles/s41560-025-01871-0">
    <img src="https://img.shields.io/badge/Nature%20Energy-Manuscript-darkgreen?style=flat-square&logo=bookstack" alt="Nature Energy Manuscript">
  </a>
  <a href="https://www.nature.com/articles/s41560-025-01872-z">
    <img src="https://img.shields.io/badge/Nature%20Energy-Research%20Briefing-darkgreen?style=flat-square&logo=bookstack" alt="Nature Energy Research Briefing">
  </a>
</p>

_By Krv Labs._

## Overview

**Retire Coal** is a Python toolkit that enables researchers and policymakers to analyze US coal plant retirement strategies using advanced network analysis and contextual retirement vulnerabilities. Based on methodologies published in [_Nature Energy_](https://www.nature.com/articles/s41560-025-01871-0), this package provides curated datasets, graph-based analytical methods, and publication-ready visualizations to explore coal retirement pathways and their underlying drivers.

The toolkit combines operational, environmental, policy, and socio-demographic data to help understand which coal plants are most vulnerable to retirement and why, enabling evidence-based decision-making for energy transition planning.

## Citation

If you use this package in your research, please cite:

```bibtex
@article{Gathrid2025,
  author  = {Gathrid, Sidney and Wayland, Jeremy and Wayland, Stuart and Deshmukh, Ranjit and Wu, Grace C.},
  title   = {Strategies to accelerate US coal power phase-out using contextual retirement vulnerabilities},
  journal = {Nature Energy},
  year    = {2025},
  volume  = {10},
  number  = {10},
  pages   = {1274--1288},
  month   = {October},
  doi     = {10.1038/s41560-025-01871-0},
  url     = {https://doi.org/10.1038/s41560-025-01871-0},
  issn    = {2058-7546}
}
```

We extend our gratitude to our coauthors and mentors, **Dr. Grace Wu** and **Dr. Ranjit Deshmukh**, from UCSB Environmental Studies, for their invaluable guidance and collaboration.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [API Reference](#api-reference)
- [Development](#development)
- [Citation](#citation)
- [License](#license)

## Key Features

🔬 **Research-Grade Analysis**

- Network analysis to quantify contextual retirement vulnerability and plant similarity
- Graph-based methods for identifying strategic retirement targets
- Reproducible manuscript outputs with group-level summaries and plant-level explanations

📊 **Comprehensive Datasets**

- Ready-to-use plant and generator-level data with operational, policy, environmental, and socio-demographic context
- Scenario projections for different retirement pathways
- Pre-processed and cleaned datasets for immediate analysis

📈 **Publication-Quality Visualizations**

- Network graphs for plant similarity and vulnerability analysis
- Geographic maps showing spatial patterns
- Sankey diagrams, stacked bar charts, heatmaps, and dot plots
- Customizable styling for publications and presentations

🛠 **Developer-Friendly API**

- Pure Python implementation requiring no external services
- Works seamlessly in Jupyter notebooks and Python scripts
- Intuitive object-oriented interface
- Comprehensive data loading utilities

## Prerequisites

- Python 3.10 or higher
- Required packages are automatically installed with the toolkit

## Installation

## Installation

### Install from PyPI (Recommended)

```bash
pip install retire-coal
```

### Install from Source

For development or to access tutorial notebooks:

```bash
git clone git@github.com:Krv-Analytics/retire.git
cd retire
uv sync --all-extras
source .venv/bin/activate
```

## Quick Start

### Basic Analysis Workflow

```python
from retire import Retire, Explore

# Initialize the analysis toolkit
retire_obj = Retire()
explore = Explore(retire_obj.graph, retire_obj.raw_df)

# Visualize the coal plant network colored by retirement status
fig, ax = explore.drawGraph(col='ret_STATUS')

# Create a geographic map of coal plants
fig, ax = explore.drawMap()

# Generate manuscript-ready results
group_analysis = retire_obj.get_group_report()
explanations = retire_obj.get_target_explanations()
```

### Working with Individual Datasets

```python
from retire.data import (
    load_dataset,                # Main plant-level dataset
    load_clean_dataset,          # Cleaned/scaled features
    load_projection,             # Scenario projections
    load_graph,                  # Plant-similarity graph
    load_generator_level_dataset # Generator-level details
)

# Load the main dataset
plants_df = load_dataset()

# Load network graph for analysis
graph = load_graph()

# Load scenario projections
projections_df = load_projection()
```

### Creating Custom Visualizations

```python
from retire import Retire, Explore

retire_obj = Retire()
explore = Explore(retire_obj.graph, retire_obj.raw_df)

# Create a heatmap of plant characteristics
fig, ax = explore.create_heatmap(features=['capacity', 'age', 'emissions'])

# Generate dot plot for specific metrics
fig, ax = explore.create_dotplot(metric='retirement_vulnerability')

# Create Sankey diagram for retirement pathways
fig, ax = explore.create_sankey(source_col='current_status', target_col='projected_status')
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

### Core Documentation

- **[Usage Guide](https://krv-analytics.github.io/retire/usage_guide.html)** - Complete guide to using the toolkit
- **[Data Sources](https://krv-analytics.github.io/retire/data_sources.html)** - Detailed description of datasets and their sources
- **[Visualization Methods](https://krv-analytics.github.io/retire/visualization_methods.html)** - Guide to creating publication-quality visualizations
- **[Configuration](https://krv-analytics.github.io/retire/configuration.html)** - Customization and configuration options

### Tutorials

Interactive Jupyter notebooks in the `tutorials/` directory:

- **[Getting Started](https://github.com/Krv-Analytics/retire/blob/main/tutorials/using_retire.ipynb)** - Introduction to the basic workflow
- **[Using THEMA](https://github.com/Krv-Analytics/retire/blob/main/tutorials/1-using_thema.ipynb)** - Working with energy transition models
- **[Exploration Tools](https://github.com/Krv-Analytics/retire/blob/main/tutorials/2-using_explore.ipynb)** - Advanced visualization techniques
- **[Target Matching](https://github.com/Krv-Analytics/retire/blob/main/tutorials/3-target_matching.ipynb)** - Identifying strategic retirement targets

### Development Documentation

- **[Testing Guide](https://krv-analytics.github.io/retire/development/testing.html)** - Running and writing tests
- **[Data Processing](https://krv-analytics.github.io/retire/data.html)** - Understanding data pipelines
- **[Explorer Module](dhttps://krv-analytics.github.io/retire/explore.html)** - Extending visualization capabilities

## API Reference

### Core Classes

#### `Retire`

Main analysis class providing data access and manuscript results.

```python
from retire import Retire

retire_obj = Retire()
group_report = retire_obj.get_group_report()
explanations = retire_obj.get_target_explanations()
```

**Key Methods:**

- `get_group_report()` - Generate group-level analysis summaries
- `get_target_explanations()` - Create plant-level retirement explanations
- Access to `graph`, `raw_df`, and other core datasets

#### `Explore`

Visualization toolkit for networks and geographic data.

```python
from retire import Explore

explore = Explore(graph, dataframe)
fig, ax = explore.drawGraph(col='retirement_status')
fig, ax = explore.drawMap(color_by='vulnerability_score')
```

**Key Methods:**

- `drawGraph()` - Network visualization with customizable styling
- `drawMap()` - Geographic mapping of coal plants
- `create_heatmap()` - Correlation and feature heatmaps
- `create_dotplot()` - Dot plot visualizations
- `create_sankey()` - Flow diagrams for retirement pathways

### Data Loading Functions

```python
from retire.data import (
    load_dataset,                # Plant-level operational and contextual data
    load_clean_dataset,          # Preprocessed features for analysis
    load_projection,             # Scenario-based retirement projections
    load_graph,                  # Plant similarity network graph
    load_generator_level_dataset # Detailed generator-level information
)
```

## Development

### Setting Up a Development Environment

```bash
# Clone the repository
git clone git@github.com:Krv-Analytics/retire.git
cd retire

# Install development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks (optional)
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=retire

# Run specific test files
pytest tests/test_retire.py
```

### Contributing

We welcome contributions! This is currently a v0 WIP release. When contributing:

1. **Fork the Repository** - Create your own fork of the project
2. **Create a Feature Branch** - `git checkout -b feature/amazing-feature`
3. **Write Tests** - Ensure new functionality includes comprehensive tests
4. **Update Documentation** - Update relevant documentation for API changes
5. **Follow Code Style** - Maintain consistency with existing patterns and conventions
6. **Submit a Pull Request** - Provide a clear description of your changes

### Code Quality Standards

- **Test Coverage**: Write tests for new functionality
- **Documentation**: Update docs for API changes
- **Type Hints**: Use type hints for new functions and methods
- **Code Style**: Follow existing patterns and PEP 8 guidelines

## Citation

If you use this package in your research, please cite our _Nature Energy_ publication:

```bibtex
@article{Gathrid2025,
  author  = {Gathrid, Sidney and Wayland, Jeremy and Wayland, Stuart and Deshmukh, Ranjit and Wu, Grace C.},
  title   = {Strategies to accelerate US coal power phase-out using contextual retirement vulnerabilities},
  journal = {Nature Energy},
  year    = {2025},
  volume  = {10},
  number  = {10},
  pages   = {1274--1288},
  month   = {October},
  doi     = {10.1038/s41560-025-01871-0},
  url     = {https://doi.org/10.1038/s41560-025-01871-0},
  issn    = {2058-7546}
}
```

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE.md](LICENSE.md) file for details.

---

## Support and Contact

- **Documentation**: [Docs](https://krv-analytics.github.io/retire/)
- **Issues**: [GitHub Issues](https://github.com/Krv-Analytics/retire/issues)
- **Website**: [krv.ai](https://krv.ai)
- **Email**: [team@krv.ai](mailto:team@krv.ai)
- **LinkedIn**: [Krv Analytics](https://www.linkedin.com/company/krv-analytics)

## Acknowledgments

This work was partially supported by a Manalis Scholarship awarded to S.G. We thank D. Prull at the Sierra Club for his generosity in providing insights on analytical gaps to fill to achieve practical relevancy and data on announced retirements. In addition, we thank D. Khannan and J. Daniel at Rocky Mountain Institute (RMI) for helpful suggestions and J. Graham and C. Schneider at the Clean Air Task Force for access to coal cost and health impact data.

---
