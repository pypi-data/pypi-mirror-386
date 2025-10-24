"""Data Visualization and Analysis Plots for Cosmic Ray Data.

This module creates interactive and static visualizations of cosmic ray event data,
environmental measurements, and analysis results. It helps researchers understand
patterns and trends in the detector measurements.

**What Does This Module Do?**

The postprocessing module:
1. Generates plots of event rates over time
2. Shows environmental conditions (temperature, pressure, humidity)
3. Creates overlaid visualizations for multi-variable analysis
4. Produces S-curves for threshold analysis
5. Generates statistical summaries and reports

**Visualization Types**

- **Event Rate Plots**: Shows cosmic ray detection frequency vs time
- **Environmental Plots**: Temperature, pressure, humidity trends
- **Overlay Plots**: Multiple variables on shared or separate axes
- **S-Curves**: Threshold scan analysis with error functions
- **Statistical Summary**: Histograms, distributions, and statistics

**Key Functions**

event_rate() : Create event rate vs time visualization
environmental_data() : Plot temperature, pressure, humidity
overlay_plots() : Combine multiple datasets on one chart
threshold_curve() : Visualize S-curve fitting results

**Libraries Used**

This module uses Altair for interactive visualizations. Charts can be:
- Displayed in Jupyter notebooks
- Saved to HTML files
- Exported as images (PNG, SVG)

**Example Usage**

```python
import pandas as pd
from haniwers.postprocess import event_rate

data = pd.read_csv("processed_data.csv")
chart = event_rate(data)
chart.show()  # Display in browser or notebook
chart.save("event_rate.html")  # Save as HTML
```

**Note**

This module is under active development. More visualization types
and analysis tools will be added in future versions.
"""

import pandas as pd
import altair as alt


def event_rate(data: pd.DataFrame):
    # イベントレート
    hbars = (
        alt.Chart(data)
        .mark_bar(opacity=0.5, color="grey")
        .encode(
            alt.X("time"),
            alt.Y("event_rate").title("イベントレート [Hz]"),
        )
        .properties(width=1200, height=500)
    )

    # 気温
    marks = (
        alt.Chart(data)
        .mark_point(color="blue")
        .encode(
            alt.X("time"),
            alt.Y("tmp").title("気温 [degC]").scale(domain=[20, 35]),
        )
        .properties(width=1200, height=500)
    )

    layers = alt.layer(hbars, marks).resolve_scale(
        y="independent",
    )
    return layers
