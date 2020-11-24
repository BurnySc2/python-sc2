import subprocess
import re
from pathlib import Path, PureWindowsPath

## This file is used for compatibility with WSL and shouldn't need to be
## accessed directly by any bot clients

def win_path_to_wsl_path(path):
    """Convert a windows-style path to a WSL path"""
    # Substitute C:/ or equivalent with c/ or equivalent and prepend /mnt
    return Path('/mnt') / PureWindowsPath(re.sub('^([A-Z]):', lambda m: m.group(1).lower(), path))

def get_wsl_home():
    """Get home directory of from Windows, even if run in WSL"""
    proc = subprocess.run(['powershell.exe','-Command','Write-Host -NoNewLine $HOME'], capture_output = True)

    if proc.returncode != 0: return None

    return win_path_to_wsl_path(proc.stdout.decode('utf-8'))
