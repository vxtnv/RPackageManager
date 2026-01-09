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

import sys

class rpackagemanager:
    def __init__(self, lib_dirname="r_libs"):
        self.venv_path = os.environ.get("VIRTUAL_ENV")
        if self.venv_path:
            self.lib_path = Path(self.venv_path) / lib_dirname
        else:
            self.lib_path = Path.cwd() / lib_dirname

        self.lib_path.mkdir(parents=True, exist_ok=True)
        self.lib_path_str = str(self.lib_path.absolute())

        robjects.r(f'.libPaths(c("{self.lib_path_str}", .libPaths()))')

        print(f"📦 R-Manager ready. Library: {self.lib_path_str}")

    def install_packages(self, package_name: str):
        """Installs package MANDATORILY into the local folder."""

        local_pkg_path = self.lib_path / package_name

        if local_pkg_path.exists():
            print(f"✅ Package '{package_name}' already exists LOCALLY.")
            return

        print(f"⏳ Installing '{package_name}' to {self.lib_path_str} ...")

        utils = importr("utils")
        mirror = "https://cloud.r-project.org"

        try:
            # Attempt 1: Standard installation to the local path
            install_kwargs = dict(
                lib=self.lib_path_str,
                repos=mirror,
                dependencies=True,
            )

            # Auf Linux: Source-Build explizit erzwingen, sonst Binary zulassen
            if sys.platform.startswith("linux"):
                install_kwargs["type"] = "source"

            utils.install_packages(
                StrVector([package_name]),
                **install_kwargs,
            )

        except Exception as e:
            msg = str(e)

            # Spezielle Behandlung für Arrow / libarrow-Probleme
            if package_name == "arrow" and (
                "arrow/api.h" in msg
                or "Arrow C++ libraries" in msg
                or "issue preparing the Arrow C++ libraries" in msg
            ):
                if sys.platform == "darwin":
                    # macOS (inkl. Apple Silicon)
                    raise RuntimeError(
                        "R‑Paket 'arrow' konnte nicht installiert werden, weil die "
                        "C++‑Bibliothek (libarrow) fehlt.\n\n"
                        "Bitte führe EINMAL im Terminal aus:\n"
                        "    brew update\n"
                        "    brew install apache-arrow\n\n"
                        "Danach das Python‑Environment neu starten und den Code erneut ausführen."
                    ) from e

                elif sys.platform.startswith("linux"):
                    raise RuntimeError(
                        "R‑Paket 'arrow' konnte nicht installiert werden, weil die "
                        "C++‑Bibliothek (libarrow) fehlt.\n\n"
                        "Auf Linux musst du libarrow und seine Dev‑Pakete über den "
                        "Paketmanager deiner Distribution installieren, z.B.:\n"
                        "  • Debian/Ubuntu:   sudo apt-get install -y libarrow-dev\n"
                        "  • RHEL/CentOS:     sudo yum install -y arrow-devel\n"
                        "  • Arch/Manjaro:    sudo pacman -S arrow\n\n"
                        "Siehe auch:\n"
                        "    https://arrow.apache.org/docs/r/articles/install.html\n\n"
                        "Danach R bzw. dein Python‑Environment neu starten und den Code erneut ausführen."
                    ) from e

                elif sys.platform.startswith("win"):
                    raise RuntimeError(
                        "R‑Paket 'arrow' konnte nicht installiert werden, weil die "
                        "C++‑Bibliothek (libarrow) nicht verfügbar ist.\n\n"
                        "Unter Windows solltest du sicherstellen, dass:\n"
                        "  • Eine aktuelle Rtools‑Version installiert ist\n"
                        "  • 'install.packages(\"arrow\")' einmal direkt in R funktioniert\n\n"
                        "Wenn das in einer normalen R‑Session klappt, sollte auch "
                        "der rpackagemanager danach funktionieren. Starte dann dein "
                        "Python‑Environment neu und führe den Code erneut aus.\n\n"
                        "Details:\n"
                        "    https://arrow.apache.org/docs/r/articles/install.html"
                    ) from e

                else:
                    raise RuntimeError(
                        "R‑Paket 'arrow' konnte nicht installiert werden, weil die "
                        "C++‑Bibliothek (libarrow) fehlt.\n\n"
                        "Bitte siehe die offizielle Installationsanleitung und erfülle "
                        "die dort beschriebenen System‑Abhängigkeiten:\n"
                        "    https://arrow.apache.org/docs/r/articles/install.html\n\n"
                        "Danach R bzw. dein Python‑Environment neu starten und den Code erneut ausführen."
                    ) from e

            # Für alle anderen Fehler optional dein bisheriger Fallback:
            print("⚠️ Standard install failed:", e)
            print("⚠️ Trying fallback with checkBuilt = FALSE...")
            robjects.r(f'''
            tryCatch(
              install.packages(
                "{package_name}",
                lib = "{self.lib_path_str}",
                repos = "{mirror}",
                dependencies = TRUE,
                checkBuilt = FALSE
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
            raise RuntimeError(
                f"❌ Error: '{package_name}' could not be installed locally."
            )