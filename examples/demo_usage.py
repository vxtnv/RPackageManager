# 1. Ensure R base is present (usually there, but better safe than sorry)
# !apt-get update -qq
# !apt-get install -y -qq r-base

# 2. Explicitly install rpy2 (a reinstall often helps to find the paths to R)
# !pip install --upgrade rpy2

# 3. Install the RPackageManager (if not already done or to update)
# !pip install --force-reinstall git+https://github.com/vxtnv/RPackageManager.gitfrom 

from RPackageManager import RPackageManager
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr

def main():
    print("🚀 Starting RPackageManager Demo...")

    # 1. Initialize
    # Automatically creates 'r_libs' in the current directory or venv
    # Initialize manager (sets .libPaths to .venv/r_libs)
    r = RPackageManager()

    # 2. Install 'forecast' package
    # Note: This may take a few minutes the first time, 
    # as 'forecast' has many dependencies (Rcpp, colorspace, etc.).
    print("Installing 'forecast' (this may take a while)...")
    r.install_packages("forecast")

    # 3. Load package
    forecast = importr("forecast")

    # --- PROOF: Where does the package come from? ---
    # Fix: Make query outside of f-string
    pkg_path = robjects.r('system.file(package="forecast")')[0]
    print(f"✅ Load location of forecast: {pkg_path}")

    # 4. Prepare data (AirPassengers example)
    print("Loading AirPassengers data...")
    robjects.r('data(AirPassengers)')
    air_passengers = robjects.globalenv['AirPassengers']

    # 5. Execute auto.arima
    print("\n--- Starting auto.arima ---")
    model = forecast.auto_arima(air_passengers)

    # Display result
    print("\n--- Model Result ---")
    print(model)

if __name__ == "__main__":
    main()

