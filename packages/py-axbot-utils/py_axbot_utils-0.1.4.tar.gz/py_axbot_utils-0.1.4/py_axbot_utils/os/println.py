import os
import sys

from .termcolor import colored


def check_supports_color():
    """
    Returns True if the running system's terminal supports color, and False
    otherwise.
    """
    plat = sys.platform
    supported_platform = plat != "Pocket PC" and (plat != "win32" or "ANSICON" in os.environ)
    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    return supported_platform and is_a_tty


support_color = check_supports_color()


def println(msg: str):
    color = "white"
    if msg.startswith("error:"):
        color = "red"
    elif msg.startswith("warning:"):
        color = "yellow"
    elif (
        msg.startswith("=== ")
        or msg.startswith("====")
        or msg.startswith("--- ")
        or msg.startswith("#")
        or msg.startswith(">>> ")
    ):
        color = "green"
    elif msg.startswith("info: "):
        color = "green"
        msg = msg[6:]
    elif msg.startswith("debug: "):
        color = "cyan"
        msg = msg[7:]

    if support_color:
        print(colored(msg, color))
    else:
        print(msg)


class Unbuffered:
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


sys.stdout = Unbuffered(sys.stdout)
