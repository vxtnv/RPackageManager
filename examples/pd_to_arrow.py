# 1. Ensure R base is present (usually there, but better safe than sorry)
# !apt-get update -qq
# !apt-get install -y -qq r-base

# 2. Explicitly install rpy2 (a reinstall often helps to find the paths to R)
# !pip install --upgrade rpy2

# 3. Install RPackageManager (if not already done or to update)
# pip install --force-reinstall "git+https://github.com/vxtnv/RPackageManager.git"


# if installation of arrow fails:
# rm -rf /Users/marlons/Downloads/MS00MV04/.venv/r_libs/00LOCK-arrow
# brew update
# brew install apache-arrow


import time
import pandas as pd
import numpy as np
import pyarrow as pa
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter
from rpackagemanager import rpackagemanager

# ---------------------------------------------------------
# 1. SETUP
# ---------------------------------------------------------
print("--- 1. Setup ---")
r = rpackagemanager()
r.install_packages("arrow") # Important R Package for Method 2

# Only import the bridge now
import rpy2_arrow.pyarrow_rarrow as py2ra

# ---------------------------------------------------------
# 2. GENERATE BIG DATA
# ---------------------------------------------------------
ROWS = 10_000_000  # 10 million rows
print(f"\n--- 2. Generating {ROWS:_} rows of test data (approx. 1 GB) ---")

# generating a mix of numbers and text for realism
df = pd.DataFrame({
    'Metric_A': np.random.randn(ROWS),
    'Metric_B': np.random.rand(ROWS),
    'Category': np.random.choice(['Group A', 'Group B', 'Group C'], ROWS),
    'Timestamp': pd.date_range('2023-01-01', periods=ROWS, freq='T'),
})

print("Data created. Starting benchmark...")

# ---------------------------------------------------------
# 3. BENCHMARK: STANDARD (pandas2ri)
# ---------------------------------------------------------
print("\n🔴 Benchmark 1: Standard (Copy via pandas2ri)")
print("   Transferring...")
start_std = time.time()

# The classic way: Converting and Copying
with localconverter(robjects.default_converter + pandas2ri.converter):
    r_df_standard = robjects.conversion.py2rpy(df)
    robjects.globalenv["data_standard"] = r_df_standard

end_std = time.time()
duration_std = end_std - start_std
print(f"   ⏱️ Duration: {duration_std:.4f} seconds")

# ---------------------------------------------------------
# 4. BENCHMARK: ARROW (Zero-Copy)
# ---------------------------------------------------------
print("\n🟢 Benchmark 2: Arrow (Zero-Copy Transfer)")
print("   Transferring...")
start_arrow = time.time()

# Step A: Pandas -> Arrow Table (Python)
# This is extremely fast ("Low Cost")
pa_table = pa.Table.from_pandas(df)

# Step B: Transfer to R (Zero Copy)
r_arrow_table = py2ra.pyarrow_table_to_r_table(pa_table)
robjects.globalenv["data_arrow"] = r_arrow_table

end_arrow = time.time()
duration_arrow = end_arrow - start_arrow
print(f"   ⏱️ Duration: {duration_arrow:.4f} seconds")

# ---------------------------------------------------------
# 5. RESULT
# ---------------------------------------------------------
print("\n" + "="*40)
print(f"🏆 RESULTS FOR {ROWS:_} ROWS")
print("="*40)
print(f"Standard: {duration_std:.4f} s")
print(f"Arrow:    {duration_arrow:.4f} s")
print("-" * 20)

if duration_arrow > 0:
    speedup = duration_std / duration_arrow
    print(f"🚀 Arrow was {speedup:.1f}x faster!")
else:
    print("🚀 Arrow was virtually instantaneous (0.000s).")
print("="*40)

# ---------------------------------------------------------
# 6. USAGE IN R (lm & arima)
print("\n--- 5. Usage in R (lm & arima) ---")

# We execute R code that processes the Arrow data
robjects.r('''
    # 1. IMPORTANT: Load Arrow library (so R understands the object)
    library(arrow)
    library(forecast)

    # 2. Conversion: Arrow Table -> R Dataframe
    # This happens in R's RAM and is very fast
    df_r <- as.data.frame(data_arrow)

    # --- EXAMPLE A: Linear Regression (lm) ---
    print("Calculating Linear Regression...")
    # We say: "Predict Metric_A based on Metric_B"
    model_lm <- lm(Metric_A ~ Metric_B, data = df_r)
    print(summary(model_lm))

    # --- EXAMPLE B: ARIMA (Time Series) ---
    print("Calculating ARIMA...")

    # For ARIMA we need a 'ts' (Time Series) object
    # We assume 'Metric_A' is our time series
    ts_data <- ts(df_r$Metric_A, frequency = 12)
     
    # Since 10 million rows take too long for ARIMA, we only take the first 1000 here
    # (Just as a demo, so you don't wait forever)
    ts_small <- head(ts_data, 1000)
    
    model_arima <- auto.arima(ts_small)
    print(model_arima)
''')