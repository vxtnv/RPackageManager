import os
import sys
import shutil
from pathlib import Path

# --- MAC SILICON SETUP ---
# Wir setzen R_HOME, damit rpy2 das Homebrew-R findet
if sys.platform == "darwin":
    homebrew_r = Path("/opt/homebrew/lib/R")
    if homebrew_r.exists():
        os.environ["R_HOME"] = str(homebrew_r)

# Versuche Imports; bei Fehler wird eine klare Exception geworfen,
# aber sys.exit() wird vermieden, damit Tools nicht abstürzen.
try:
    import rpy2.robjects as robjects
    from rpy2.robjects.packages import importr
    from rpy2.robjects.vectors import StrVector
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.conversion import localconverter
except ImportError as e:
    raise ImportError(f"CRITICAL: rpy2 fehlt. Fehler: {e}. \n"
                      "TIPP: Falls 'Library not loaded' erscheint, prüfe die brew-Installation.") from e

class RPackageManager:
    def __init__(self, lib_dirname="r_libs"):
        # 1. Pfad im venv definieren
        self.venv_path = os.environ.get("VIRTUAL_ENV")
        if self.venv_path:
            self.lib_path = Path(self.venv_path) / lib_dirname
        else:
            self.lib_path = Path.cwd() / lib_dirname

        # 2. Ordner erstellen
        self.lib_path.mkdir(parents=True, exist_ok=True)
        self.lib_path_str = str(self.lib_path.absolute())
        
        # 3. R mitteilen: "Nutze diesen Ordner zuerst!"
        robjects.r(f'.libPaths(c("{self.lib_path_str}", .libPaths()))')
        
        print(f"📦 R-Manager bereit. Library: {self.lib_path_str}")

    def install(self, package_name):
        """Installiert Paket ZWINGEND in den lokalen Ordner."""
        
        # --- ÄNDERUNG: Strikter Check auf lokalen Ordner ---
        local_pkg_path = self.lib_path / package_name
        
        if local_pkg_path.exists():
            print(f"✅ Paket '{package_name}' ist bereits LOKAL vorhanden.")
            return

        print(f"⏳ Installiere '{package_name}' nach {self.lib_path_str} ...")
        
        utils = importr('utils')
        # Verwende einen stabilen Mirror
        mirror = "https://cloud.r-project.org"
        
        try:
            # Versuch 1: Standard Installation in den lokalen Pfad
            utils.install_packages(
                StrVector([package_name]),
                lib=self.lib_path_str,
                repos=mirror,
                type="source",
                dependencies=True
            )
        except Exception:
            # Versuch 2: Fallback (Checks ignorieren)
            print("⚠️ Standard-Install fehlgeschlagen. Nutze Fallback...")
            robjects.r(f'''
                install.packages("{package_name}", 
                 lib="{self.lib_path_str}", 
                 repos="{mirror}", 
                 type="source",
                checkBuilt=FALSE)
            ''')

        # Check: Ist es jetzt im lokalen Ordner?
        if local_pkg_path.exists():
            print(f"✅ '{package_name}' erfolgreich im venv installiert.")
        else:
            raise RuntimeError(f"❌ Fehler: '{package_name}' konnte nicht lokal installiert werden.")

    def get_auto_data(self):
        """Lädt Auto-Daten aus ISLR2 und gibt Pandas DataFrame zurück."""
        pkg_name = "ISLR2"
        self.install(pkg_name)
        
        print(f"Lade Daten aus {pkg_name}...")
        # Daten in den R-Workspace laden
        robjects.r(f'data(Auto, package="{pkg_name}")')
        r_data = robjects.globalenv["Auto"]
        
        # Konvertierung zu Pandas
        with localconverter(robjects.default_converter + pandas2ri.converter):
            pd_df = robjects.conversion.rpy2py(r_data)
            
        return pd_df
