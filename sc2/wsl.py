import subprocess
import re
from pathlib import Path, PureWindowsPath

## This file is used for compatibility with WSL and shouldn't need to be
## accessed directly by any bot clients

def win_path_to_wsl_path(path):
    """Convert a path like C:\\foo to /mnt/c/foo"""
    return Path('/mnt') / PureWindowsPath(re.sub('^([A-Z]):', lambda m: m.group(1).lower(), path))

def wsl_path_to_win_path(path):
    """Convert a path like /mnt/c/foo to C:\\foo"""
    return PureWindowsPath(re.sub('^/mnt/([a-z])', lambda m: m.group(1).upper() + ":", path))

def get_wsl_home():
    """Get home directory of from Windows, even if run in WSL"""
    proc = subprocess.run(['powershell.exe','-Command','Write-Host -NoNewLine $HOME'], capture_output = True)

    if proc.returncode != 0: return None

    return win_path_to_wsl_path(proc.stdout.decode('utf-8'))

RUN_SCRIPT = """$proc = Start-Process -NoNewWindow -PassThru "%s" "%s"
if ($proc) {
    Write-Host $proc.id
    exit $proc.ExitCode
} else {
    exit 1
}"""

def run(popen_args, sc2_cwd):
    """Run SC2 in Windows and get the pid so that it can be killed later."""
    path = wsl_path_to_win_path(popen_args[0])
    args = " ".join(popen_args[1:])

    return subprocess.Popen(
        ["powershell.exe", "-Command", RUN_SCRIPT % (path, args)],
        cwd = sc2_cwd,
        stdout = subprocess.PIPE,
        universal_newlines = True,
        bufsize = 1
    )

def kill(wsl_process):
    """Needed to kill a process started with WSL. Returns true if killed successfully."""
    # HACK: subprocess and WSL1 appear to have a nasty interaction where
    # any streams are never closed and the process is never considered killed,
    # despite having an exit code (this works on WSL2 as well, but isn't
    # necessary). As a result,
    # 1: We need to read using readline (to make sure we block long enough to
    #    get the exit code in the rare case where the user immediately hits ^C)
    out = wsl_process.stdout.readline().rstrip()
    # 2: We need to use __exit__, since kill() calls send_signal(), which thinks
    #    the process has already exited!
    wsl_process.__exit__(None, None, None)
    proc = subprocess.run(["taskkill.exe", "-f", "-pid", out], capture_output = True)
    return proc.returncode == 0 # Returns 128 on failure
