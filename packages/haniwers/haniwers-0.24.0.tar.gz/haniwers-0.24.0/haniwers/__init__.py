"""Haniwers: Cosmic Ray Detection Analysis Tool.

Haniwers is a data acquisition and analysis toolkit for studying cosmic rays
using the OSECHI detector. It's designed to help researchers collect, process,
and analyze cosmic ray event data with ease.

**What is Haniwers?**

Haniwers provides tools for:
- Collecting raw cosmic ray detector data (Data Acquisition / DAQ)
- Preparing and cleaning the raw data (Preprocessing)
- Analyzing detector thresholds and event rates (Analysis)
- Visualizing cosmic ray patterns and trends (Visualization)

**Getting Started**

For first-time users:
1. Install: `pip install haniwers` or use Poetry
2. Configure: Create a TOML configuration file with detector settings
3. Collect: Run `haniwers daq` to collect data from the OSECHI detector
4. Process: Use `haniwers run2csv` to convert raw data to analyzable format
5. Analyze: Run `haniwers scan` for threshold analysis

**Main Modules**

- `config`: Configuration management and data structures
- `daq`: Data acquisition from the OSECHI cosmic ray detector
- `threshold`: Threshold scanning and optimization
- `preprocess`: Raw data parsing and cleaning
- `postprocess`: Data analysis and visualization
- `cli`: Command-line interface for all tools

**Documentation**

For detailed information, visit the online docs or use `haniwers docs`
"""

__version__ = "0.24.0"
