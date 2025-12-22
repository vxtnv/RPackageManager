# 1. R-Basis sicherstellen (ist meist da, aber sicher ist sicher)
# !apt-get update -qq
# !apt-get install -y -qq r-base

# 2. rpy2 explizit installieren (oft hilft ein Reinstall, um die Pfade zu R zu finden)
# !pip install --upgrade rpy2

# 3. Dein Paket installieren (falls noch nicht geschehen oder zum Aktualisieren)
# !pip install --force-reinstall git+https://github.com/vxtnv/RPackageManager.git



from rpackagemanager import RPackageManager
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr

def main():
    print("🚀 Starte RPackageManager Demo...")

    # 1. Initialisieren
    # Erstellt automatisch 'r_libs' im aktuellen Verzeichnis oder venv
    # Manager initialisieren (setzt .libPaths auf .venv/r_libs)
    r = RPackageManager()

    # 2. 'forecast' Paket installieren
    # Hinweis: Das kann beim ersten Mal ein paar Minuten dauern, 
    # da 'forecast' viele Abhängigkeiten (Rcpp, colorspace, etc.) hat.
    print("Installiere 'forecast' (das kann dauern)...")
    r.install("forecast")

    # 3. Paket laden
    forecast = importr("forecast")

    # --- BEWEIS: Woher kommt das Paket? ---
    # Fix: Abfrage außerhalb des f-Strings machen
    pkg_path = robjects.r('system.file(package="forecast")')[0]
    print(f"✅ Ladeort von forecast: {pkg_path}")

    # 4. Daten vorbereiten (AirPassengers Beispiel)
    print("Lade AirPassengers Daten...")
    robjects.r('data(AirPassengers)')
    air_passengers = robjects.globalenv['AirPassengers']

    # 5. auto.arima ausführen
    print("\n--- Starte auto.arima ---")
    model = forecast.auto_arima(air_passengers)

    # Ergebnis anzeigen
    print("\n--- Modell Ergebnis ---")
    print(model)




if __name__ == "__main__":
    main()




    """







"""