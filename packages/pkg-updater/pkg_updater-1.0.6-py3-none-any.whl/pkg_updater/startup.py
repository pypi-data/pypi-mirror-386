import sys
from pathlib import Path

from pkg_updater import logger


def create_startup_bat():
    logger.info("Creating startup bat...")
    startup_dir = (
        Path.home()
        / "AppData"
        / "Roaming"
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "Startup"
    )
    startup_bat_path = startup_dir / "pkg-updater.bat"
    with open(startup_bat_path, "w") as file:
        args = " ".join(sys.argv[1:])
        file.write(f"start pkg-updater.exe {args}\n")
