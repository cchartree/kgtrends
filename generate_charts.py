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

# 3. Filter for only the last 180 days relative to the latest record
if not df.empty:
    latest_date = df["Clean_Date"].max()
    cutoff_date = latest_date - pd.Timedelta(days=180)
    df = df[df["Clean_Date"] >= cutoff_date]

# 4. Process each metric column and build HTML components
metrics = [col for col in df.columns if col not in ["Date", "Clean_Date"]]
html_content = [
    "<html><head><title>Body Metrics Dashboard (180 Days)</title>",
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
    "<style>body { font-family: -apple-system, sans-serif; padding: 10px; background: #f9f9f9; }</style>",
    "</head><body>",
    "<h1 style='text-align:center;'>Body Metrics (Last 180 Days)</h1>",
]

for col in metrics:
    # Extract value prior to brackets and remove non-numeric chars except decimals
    clean_s = df[col].astype(str)
    clean_s = clean_s.apply(lambda x: re.split(r"\(", x)[0] if "(" in x else x)
    clean_s = clean_s.str.replace(r"[^\d.]", "", regex=True)

    df[col] = pd.to_numeric(clean_s, errors="coerce")

    if df[col].dropna().empty:
        continue

    fig = px.line(
        df,
        x="Clean_Date",
        y=col,
        title=f"<b>{col}</b>",
        markers=True,
        labels={"Clean_Date": "Date", col: col},
    )
    fig.update_layout(
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified",
    )
    
    # 1. Update line traces to hide markers
    fig.update_traces(
        mode='lines',              # Shows lines only (no markers/dots)
        line=dict(width=2.5)       # Optional: Adjust line thickness
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
            showline=False
        )
    )

    # Append standalone div for mobile rendering
    html_content.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))

html_content.append("</body></html>")

# 5. Save to build directory
os.makedirs("public", exist_ok=True)
with open("public/index.html", "w", encoding="utf-8") as f:
    f.writelines(html_content)
