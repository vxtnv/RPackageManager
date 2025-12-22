
# 1. R-Basis sicherstellen (ist meist da, aber sicher ist sicher)
# !apt-get update -qq
# !apt-get install -y -qq r-base

# 2. rpy2 explizit installieren (oft hilft ein Reinstall, um die Pfade zu R zu finden)
# !pip install --upgrade rpy2

# 3. Dein Paket installieren (falls noch nicht geschehen oder zum Aktualisieren)
# !pip install --force-reinstall git+https://github.com/vxtnv/RPackageManager.git



import time
import pandas as pd
import numpy as np
import pyarrow as pa
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter
from rpackagemanager import RPackageManager

# ---------------------------------------------------------
# 1. SETUP
# ---------------------------------------------------------
print("--- 1. Setup ---")
r = RPackageManager()
r.install("arrow") # Wichtig für Methode 2

# Erst jetzt die Bridge importieren
import rpy2_arrow.pyarrow_rarrow as py2ra

# ---------------------------------------------------------
# 2. BIG DATA GENERIEREN
# ---------------------------------------------------------
ROWS = 10_000_000  # 10 Millionen Zeilen
print(f"\n--- 2. Generiere {ROWS:_} Zeilen Testdaten (ca. 1 GB) ---")

# Wir erzeugen einen Mix aus Zahlen und Text für Realismus
df = pd.DataFrame({
    'Metric_A': np.random.randn(ROWS),
    'Metric_B': np.random.rand(ROWS),
    'Category': np.random.choice(['Group A', 'Group B', 'Group C'], ROWS),
    'Timestamp': pd.date_range('2023-01-01', periods=ROWS, freq='T'),


})
print("Daten erstellt. Start Benchmark...")

# ---------------------------------------------------------
# 3. BENCHMARK: STANDARD (pandas2ri)
# ---------------------------------------------------------
print("\n🔴 Benchmark 1: Standard (Kopieren via pandas2ri)")
print("   Transfer läuft...")
start_std = time.time()

# Der klassische Weg: Konvertieren und Kopieren
with localconverter(robjects.default_converter + pandas2ri.converter):
    r_df_standard = robjects.conversion.py2rpy(df)
    robjects.globalenv["data_standard"] = r_df_standard

end_std = time.time()
duration_std = end_std - start_std
print(f"   ⏱️ Dauer: {duration_std:.4f} Sekunden")

# ---------------------------------------------------------
# 4. BENCHMARK: ARROW (Zero-Copy)
# ---------------------------------------------------------
print("\n🟢 Benchmark 2: Arrow (Zero-Copy Transfer)")
print("   Transfer läuft...")
start_arrow = time.time()

# Schritt A: Pandas -> Arrow Table (Python)
# Das ist meist extrem schnell ("Low Cost")
pa_table = pa.Table.from_pandas(df)

# Schritt B: Transfer nach R (Zero Copy)
r_arrow_table = py2ra.pyarrow_table_to_r_table(pa_table)
robjects.globalenv["data_arrow"] = r_arrow_table

end_arrow = time.time()
duration_arrow = end_arrow - start_arrow
print(f"   ⏱️ Dauer: {duration_arrow:.4f} Sekunden")

# ---------------------------------------------------------
# 5. ERGEBNIS
# ---------------------------------------------------------
print("\n" + "="*40)
print(f"🏆 ERGEBNIS BEI {ROWS:_} ZEILEN")
print("="*40)
print(f"Standard: {duration_std:.4f} s")
print(f"Arrow:    {duration_arrow:.4f} s")
print("-" * 20)
if duration_arrow > 0:
    speedup = duration_std / duration_arrow
    print(f"🚀 Arrow war {speedup:.1f}x schneller!")
else:
    print("🚀 Arrow war quasi instantan (0.000s).")
print("="*40)






# ---------------------------------------------------------
# 6. NUTZUNG IN R (lm & arima)
print("\n--- 5. Nutzung in R (lm & arima) ---")

# Wir führen R-Code aus, der die Arrow-Daten verarbeitet
robjects.r('''
    # 1. WICHTIG: Arrow-Bibliothek laden (damit R das Objekt versteht)
    library(arrow)
    library(forecast)

    # 2. Umwandlung: Arrow Table -> R Dataframe
    # Das passiert im RAM von R und ist sehr schnell
    df_r <- as.data.frame(data_arrow)

    # --- BEISPIEL A: Lineare Regression (lm) ---
    print("Rechne Lineare Regression...")
    # Wir sagen: "Vorhersage Metric_A basierend auf Metric_B"
    model_lm <- lm(Metric_A ~ Metric_B, data = df_r)
    print(summary(model_lm))

    # --- BEISPIEL B: ARIMA (Zeitreihe) ---
    print("Rechne ARIMA...")
    # Für Arima brauchen wir ein 'ts' (Time Series) Objekt
    # Wir nehmen an, 'Metric_A' ist unsere Zeitreihe
    ts_data <- ts(df_r$Metric_A, frequency = 12) 
    
    # Da 10 Mio Zeilen für ARIMA zu lange dauern, nehmen wir hier nur die ersten 1000
    # (Nur als Demo, damit du nicht ewig wartest)
    ts_small <- head(ts_data, 1000)
    
    model_arima <- auto.arima(ts_small)
    print(model_arima)
''')