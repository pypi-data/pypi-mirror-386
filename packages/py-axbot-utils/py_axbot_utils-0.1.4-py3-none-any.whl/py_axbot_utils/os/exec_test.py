import time
import psutil

from .exec import exec, exec_get_output, exec_in_background


def test_exec_get_output():
    result = exec_get_output("echo 世界", checked=False)
    assert result.returncode == 0
    assert result.stdout == "世界\n"


def find_process(name: str = None, arg: str = None):
    """Kill all processes with a specified name"""
    for process in psutil.process_iter():
        if process.name() == name:
            for one_arg in process.cmdline():
                if one_arg == arg:
                    return True
    return False


def test_exec_in_background():
    exec_in_background('python3 -c "import time; time.sleep(1)"')

    time.sleep(0.1)
    assert find_process("python3", "import time; time.sleep(1)")

    time.sleep(1)
    assert find_process("python3", "import time; time.sleep(1)") == False
