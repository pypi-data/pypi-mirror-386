import subprocess
import sys

from .println import println

__PRINT_ONLY = False


def set_print_only(print_only: bool):
    global __PRINT_ONLY
    __PRINT_ONLY = print_only


def exec(cmd: str, check=True):
    print("> " + cmd)
    if __PRINT_ONLY:
        return

    try:
        subprocess.run(cmd, shell=True, check=check)
    except subprocess.CalledProcessError as e:
        println("error: " + str(e))
        sys.exit(e.returncode)


def exec_in_background(cmd: str):
    if not cmd.strip().endswith("&"):
        cmd = cmd + " &"
    print("> " + cmd)
    if __PRINT_ONLY:
        return

    try:
        subprocess.Popen(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        println("error: " + str(e))
        sys.exit(e.returncode)


class ExecResult:
    def __init__(self, returncode: int, stdout: str, stderr: str) -> None:
        self.returncode: int = returncode
        self.stdout: str = stdout
        self.stderr: str = stderr


def exec_get_output(cmd, checked: bool = True) -> ExecResult:
    if __PRINT_ONLY:
        if isinstance(cmd, str):
            print(f"> {cmd}")
        else:
            print(f'> {" ".join(cmd)}')
        return

    try:
        rtn = subprocess.run(
            cmd,
            shell=True,
            check=checked,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return ExecResult(rtn.returncode, rtn.stdout, rtn.stderr)
    except subprocess.CalledProcessError as e:
        println("error: " + str(e))
        sys.exit(e.returncode)
