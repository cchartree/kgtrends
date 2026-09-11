import glob
import json
import os
import re
import pandas as pd
import plotly.express as px

# 1. Find the Excel file in the repository root
excel_files = glob.glob("*.xlsx") + glob.glob("*.xls")
if not excel_files:
    raise FileNotFoundError("No Excel file found in the repository.")

latest_file = excel_files[0]
df = pd.read_excel(latest_file)

# 2. Clean date column (extracts format like "Aug.29 2026")
df["Clean_Date"] = pd.to_datetime(
    df["Date"].astype(str).str.extract(r"([A-Za-z]+\.\d+\s+\d{4})")[0],
    format="%b.%d %Y",
    errors="coerce",
)
df = df.dropna(subset=["Clean_Date"]).sort_values("Clean_Date")
df = df.rename(columns={'Weight': 'Weight (kg)', 'Body Fat': ' Body Fat (%)', 'Subcutaneous fat': 'Subcutaneous Fat (%)', 
                        'Body Water': 'Body Water (%)', 'Skeletal Muscle': ' Skeletal Muscle (%)', 'Muscle mass': 'Muscle Mass (kg)', 
                        'Bone Mass': 'Bone Mass (kg)', 'Protein': 'Protein (%)', 'BMR': 'BMR (kcal)', 'Fat mass': 'Fat Mass (kg)', 
                        'Water weight': 'Water Weight (kg)', 'Muscle rate': 'Muscle Rate (%)', 'Protein mass': 'Protein Mass (kg)', 
                        'Obesity': 'Obesity (%)', 'Fat-free Body Weight': 'Fat-free Body Weight (kg)', 'SMI': 'Skeletal Muscle Index (kg/m2)', 
                        'Recommended target weight': 'Recommended Target Weight (kg)', 'Weight control': 'Weight Control (kg)', 
                        'Fat control': 'Fat Control (kg)', 'Skeletal muscle': 'Skeletal Muscle (kg)'})

# 3. Keep the last 24 months of data so every filter button (up to "Last 24
#    months") has data available to display. The default on-page-load view is
#    set to "Last 180 days" via the filter bar below.
if not df.empty:
    latest_date = df["Clean_Date"].max()
    cutoff_date = latest_date - pd.DateOffset(months=24)
    df = df[df["Clean_Date"] >= cutoff_date]

# 4. Process each metric column and build HTML components

# Fixed pixel dimensions applied to every chart (no responsive resizing)
CHART_WIDTH = 400
CHART_HEIGHT = 300

# Font sizing: 10% smaller than Plotly's normal defaults (base=12, title=17)
BASE_FONT_SIZE = round(12 * 0.9, 1)    # 10.8
TITLE_FONT_SIZE = round(17 * 0.9, 1)   # 15.3

metrics = [col for col in df.columns if col not in ["Date", "Clean_Date"]]

# Filter bar definitions: (label, unit type, value)
FILTER_OPTIONS = [
    ("Last 7 days", "days", 7),
    ("Last 30 days", "days", 30),
    ("Last 60 days", "days", 60),
    ("Last 90 days", "days", 90),
    ("Last 180 days", "days", 180),
    ("Last 12 months", "months", 12),
    ("Last 18 months", "months", 18),
    ("Last 24 months", "months", 24),
]
DEFAULT_FILTER = ("days", 180)

filter_buttons_html = "".join(
    f'<button class="filter-btn" data-type="{unit}" data-value="{value}" '
    f'onclick="applyFilter(this)">{label}</button>'
    for label, unit, value in FILTER_OPTIONS
)

html_content = [
    "<html><head><title>Metric Trends</title>",
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
    "<style>",
    "body { font-family: -apple-system, sans-serif; padding: 10px; background: #f9f9f9; }",
    ".plotly-graph-div { margin: 0 auto 20px auto; }",
    ".charts-wrap { display: flex; flex-wrap: wrap; gap: 40px; justify-content: center; }",
    ".filter-bar { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; "
    "margin: 0 auto 20px auto; max-width: 900px; }",
    ".filter-btn { font-family: inherit; font-size: 12.6px; padding: 6px 12px; "
    "border: 1px solid #40E0D0; border-radius: 16px; background: white; color: #1a1a1a; "
    "cursor: pointer; transition: background 0.15s, color 0.15s; }",
    ".filter-btn:hover { background: #d4f7f2; }",
    ".filter-btn.active { background: #40E0D0; color: white; border-color: #40E0D0; }",
    "</style>",
    "</head><body>",
    "<h1 style='text-align:center;'>Metric Trends</h1>",
    f'<div class="filter-bar">{filter_buttons_html}</div>',
    '<div class="charts-wrap">',
]

chart_div_ids = []

for i, col in enumerate(metrics):
    # Extract value prior to brackets and remove non-numeric chars except decimals
    clean_s = df[col].astype(str)
    clean_s = clean_s.apply(lambda x: re.split(r"\(", x)[0] if "(" in x else x)
    clean_s = clean_s.str.replace(r"[^\d.]", "", regex=True)

    df[col] = pd.to_numeric(clean_s, errors="coerce")

    if df[col].dropna().empty:
        continue

    div_id = f"chart_{i}"
    chart_div_ids.append(div_id)

    fig = px.area(
        df,
        x="Clean_Date",
        y=col,
        title=f"<b>{col}</b>",
        labels={"Clean_Date": "Date", col: col},
    )
    fig.update_layout(
        autosize=False,
        width=CHART_WIDTH,
        height=CHART_HEIGHT,
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified",
        font=dict(size=BASE_FONT_SIZE),   # All fonts 10% smaller than default
        title=dict(
            font=dict(size=TITLE_FONT_SIZE),  # Title font 10% smaller than default
            x=0,                              # Left-justify the title
            xanchor="left",
        ),
    )

    # 1. Update area traces: turquoise line + turquoise fill shading
    fig.update_traces(
        mode='lines',                       # Shows lines only (no markers/dots)
        line=dict(width=2.5, color='#40E0D0'),   # Turquoise line
        fillcolor='rgba(64, 224, 208, 0.35)',    # Turquoise shaded fill
    )

    # 2. Update layout for white background, horizontal gridlines only, and no X-axis title
    fig.update_layout(
        plot_bgcolor='white',      # Chart area background
        paper_bgcolor='white',     # Outer canvas background
        
        # X-Axis settings
        xaxis=dict(
            title_text='',         # Removes the X-axis title
            showgrid=False,        # Removes vertical gridlines
            showline=True,         # Shows bottom axis baseline
            linecolor='#e0e0e0'
        ),
        
        # Y-Axis settings: range is intentionally left on autorange here.
        # The filter bar's JS recomputes it per click, scoped to whichever
        # metric values fall inside the selected date window (see
        # `applyFilter` below: 20% padding above the visible max, 20% below
        # the visible min).
        yaxis=dict(
            showgrid=True,         # Keeps horizontal gridlines
            gridcolor='#f0f0f0',   # Light grey color for subtle gridlines
            showline=False,
            tickformat=',.1f',     # Thousand separators + 1 decimal place
        )
    )


    # Append standalone div with fixed pixel dimensions (no responsive autosize)
    html_content.append(
        fig.to_html(
            full_html=False,
            include_plotlyjs="cdn",
            config={"responsive": False},
            default_width=f"{CHART_WIDTH}px",
            default_height=f"{CHART_HEIGHT}px",
            div_id=div_id,
        )
    )

html_content.append("</div>")  # close .charts-wrap

# 5. Embed the cross-chart filter script: clicking a button relayouts every
#    chart's x-axis range to the selected window, anchored to the latest date.
latest_date_iso = df["Clean_Date"].max().strftime("%Y-%m-%d") if not df.empty else ""
filter_script = f"""
<script>
var CHART_IDS = {json.dumps(chart_div_ids)};
var LATEST_DATE = "{latest_date_iso}";

function applyFilter(btn) {{
    document.querySelectorAll('.filter-btn').forEach(function(b) {{ b.classList.remove('active'); }});
    btn.classList.add('active');

    var type = btn.getAttribute('data-type');
    var value = parseInt(btn.getAttribute('data-value'), 10);

    var latest = new Date(LATEST_DATE);
    var cutoff = new Date(LATEST_DATE);
    if (type === 'days') {{
        cutoff.setDate(cutoff.getDate() - value);
    }} else if (type === 'months') {{
        cutoff.setMonth(cutoff.getMonth() - value);
    }}

    var startISO = cutoff.toISOString().slice(0, 10);
    var endISO = latest.toISOString().slice(0, 10);
    var startTime = cutoff.getTime();
    var endTime = latest.getTime();

    CHART_IDS.forEach(function(id) {{
        var gd = document.getElementById(id);
        var update = {{'xaxis.range': [startISO, endISO]}};

        if (gd && gd.data && gd.data[0]) {{
            var xs = gd.data[0].x;
            var ys = gd.data[0].y;
            var visibleYs = [];
            for (var j = 0; j < xs.length; j++) {{
                var t = new Date(xs[j]).getTime();
                if (t >= startTime && t <= endTime) {{
                    var v = ys[j];
                    if (v !== null && v !== undefined && !isNaN(v)) {{
                        visibleYs.push(v);
                    }}
                }}
            }}
            if (visibleYs.length > 0) {{
                var yMin = Math.min.apply(null, visibleYs);
                var yMax = Math.max.apply(null, visibleYs);
                var yRange = yMax - yMin;
                // 20% below the visible minimum, 20% above the visible maximum
                var yPadding = yRange === 0
                    ? (yMax !== 0 ? Math.abs(yMax) * 0.2 : 1)
                    : yRange * 0.2;
                update['yaxis.range'] = [yMin - yPadding, yMax + yPadding];
                update['yaxis.autorange'] = false;
            }}
        }}

        Plotly.relayout(id, update);
    }});
}}

window.addEventListener('load', function() {{
    var defaultBtn = document.querySelector(
        '.filter-btn[data-type="{DEFAULT_FILTER[0]}"][data-value="{DEFAULT_FILTER[1]}"]'
    );
    if (defaultBtn) {{ applyFilter(defaultBtn); }}
}});

// Mobile Chrome/Safari (iOS) keep the tapped data label pinned on screen
// because a tap on a data point fires Plotly's hover but there is no
// corresponding "unhover" when tapping outside the chart. Explicitly clear
// the hover label on every chart whenever a tap/click lands outside all
// chart divs.
function dismissAllHoverLabels() {{
    CHART_IDS.forEach(function(id) {{
        var gd = document.getElementById(id);
        if (gd) {{ Plotly.Fx.hover(gd, []); }}
    }});
}}

document.addEventListener('touchstart', function(e) {{
    if (!(e.target.closest && e.target.closest('.plotly-graph-div'))) {{
        dismissAllHoverLabels();
    }}
}}, {{ passive: true }});

document.addEventListener('click', function(e) {{
    if (!(e.target.closest && e.target.closest('.plotly-graph-div'))) {{
        dismissAllHoverLabels();
    }}
}});
</script>
"""
html_content.append(filter_script)

html_content.append("</body></html>")

# 6. Save to build directory
os.makedirs("public", exist_ok=True)
with open("public/index.html", "w", encoding="utf-8") as f:
    f.writelines(html_content)
