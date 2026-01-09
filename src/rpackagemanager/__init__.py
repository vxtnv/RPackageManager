import os
import sys
import shutil
from pathlib import Path

# --- MAC SILICON SETUP ---
# Sets R_HOME so that rpy2 finds the Homebrew-R installation
if sys.platform == "darwin":
    homebrew_r = Path("/opt/homebrew/lib/R")
    if homebrew_r.exists():
        os.environ["R_HOME"] = str(homebrew_r)

# Attempt imports; a clear Exception is thrown on error,
# but sys.exit() is avoided to prevent tools from crashing.
try:
    import rpy2.robjects as robjects
    from rpy2.robjects.packages import importr
    from rpy2.robjects.vectors import StrVector
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.conversion import localconverter
except ImportError as e:
    raise ImportError(f"CRITICAL: rpy2 missing. Error: {e}. \n"
                      "TIP: If 'Library not loaded' appears, check the brew installation.") from e

class rpackagemanager:
    def __init__(self, lib_dirname="r_libs"):
        # 1. Defines path within venv
        self.venv_path = os.environ.get("VIRTUAL_ENV")
        if self.venv_path:
            self.lib_path = Path(self.venv_path) / lib_dirname
        else:
            self.lib_path = Path.cwd() / lib_dirname

        # 2. Creates directory
        self.lib_path.mkdir(parents=True, exist_ok=True)
        self.lib_path_str = str(self.lib_path.absolute())
        
        # 3. Tell R: "Use this directory first!"
        robjects.r(f'.libPaths(c("{self.lib_path_str}", .libPaths()))')
        
        print(f"📦 R-Manager ready. Library: {self.lib_path_str}")

    def install_packages(self, package_name):
        """Installs package MANDATORILY into the local folder."""
        
        # Strict check for local folder ---
        local_pkg_path = self.lib_path / package_name
        
        if local_pkg_path.exists():
            print(f"✅ Package '{package_name}' already exists LOCALLY.")
            return

        print(f"⏳ Installing '{package_name}' to {self.lib_path_str} ...")
        
        utils = importr('utils')
        # Use a stable mirror
        mirror = "https://cloud.r-project.org"
        

        try:
            # Attempt 1: Standard installation to the local path
            utils.install_packages(
                StrVector([package_name]),
                lib=self.lib_path_str,
                repos=mirror,
                type="source",
                dependencies=True
            )
        except Exception as e:
            print("⚠️ Standard install failed:", e)
            print("⚠️ Trying fallback with checkBuilt = FALSE...")
            robjects.r(f'''
            tryCatch(
            install.packages("{package_name}",
                lib="{self.lib_path_str}",
                repos="[https://cloud.r-project.org](https://cloud.r-project.org)",
                type="source",
                checkBuilt=FALSE
            ),
            error = function(err) 
                message("R-install error: ", conditionMessage(err))
                stop(err)
            
            )
            ''')

        # Check: Is it now in the local folder?
        if local_pkg_path.exists():
            print(f"✅ '{package_name}' successfully installed in venv.")
        else:
            raise RuntimeError(f"❌ Error: '{package_name}' could not be installed locally.")