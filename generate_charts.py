import glob
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

# 3. Filter for only the last 180 days relative to the latest record
if not df.empty:
    latest_date = df["Clean_Date"].max()
    cutoff_date = latest_date - pd.Timedelta(days=180)
    df = df[df["Clean_Date"] >= cutoff_date]

# 4. Process each metric column and build HTML components

# Fixed pixel dimensions applied to every chart (no responsive resizing)
CHART_WIDTH = 700
CHART_HEIGHT = 400

metrics = [col for col in df.columns if col not in ["Date", "Clean_Date"]]
html_content = [
    "<html><head><title>Kg trends (180 Days)</title>",
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
    "<style>",
    "body { font-family: -apple-system, sans-serif; padding: 10px; background: #f9f9f9; }",
    ".plotly-graph-div { margin: 0 auto 20px auto; }",
    "</style>",
    "</head><body>",
    "<h1 style='text-align:center;'>Kg trends (180 Days)</h1>",
]

for col in metrics:
    # Extract value prior to brackets and remove non-numeric chars except decimals
    clean_s = df[col].astype(str)
    clean_s = clean_s.apply(lambda x: re.split(r"\(", x)[0] if "(" in x else x)
    clean_s = clean_s.str.replace(r"[^\d.]", "", regex=True)

    df[col] = pd.to_numeric(clean_s, errors="coerce")

    if df[col].dropna().empty:
        continue

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
        
        # Y-Axis settings
        yaxis=dict(
            showgrid=True,         # Keeps horizontal gridlines
            gridcolor='#f0f0f0',   # Light grey color for subtle gridlines
            showline=False,
            tickformat=',.1f'      # Thousand separators + 1 decimal place
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
        )
    )

html_content.append("</body></html>")

# 5. Save to build directory
os.makedirs("public", exist_ok=True)
with open("public/index.html", "w", encoding="utf-8") as f:
    f.writelines(html_content)
