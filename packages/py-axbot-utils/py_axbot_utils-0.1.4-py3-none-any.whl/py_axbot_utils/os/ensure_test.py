import re
import os

from .ensure import (
    ensure_comment_lines,
    ensure_del_file_content,
    ensure_file,
    ensure_modify_file,
    find_missing_packages,
    ensure_uncomment_lines,
    ensure_unlink_file,
    TextFileModifier,
)
from .ensure import ensure_user, ensure_lines_in_file, user_exists
from .exec import exec, exec_get_output


def file_content(filename: str):
    with open(filename, "r", encoding="utf8") as f:
        return f.read()


def test_find_missing_packages():
    assert not find_missing_packages([])
    assert not find_missing_packages(["zlib1g", "python3-pip"])
    assert find_missing_packages(["zlib1g", "python3-pip", "none-exist"]) == [
        "none-exist"
    ]


def test_ensure_file():
    ensure_file("test.txt", "abc\n" r"def\n$3")
    with open("test.txt", "r", encoding="utf8") as f:
        assert f.read() == "abc\ndef\\n$3"


def test_ensure_user():
    result = exec_get_output("whoami")

    # THIS TEST MUST BE RUN as ADMIN
    if result.stdout != "root\n":
        return

    assert result.stdout == "root\n"

    # remove abc
    if user_exists("abc"):
        exec("deluser abc")
        exec("rm /home/abc -rf")

    # test
    ensure_user("abc")
    ensure_lines_in_file(
        "/home/abc/.bashrc",
        [
            "export TEST1=1",
            "export TEST2=2",
        ],
    )
    with open("/home/abc/.bashrc", "r", encoding="utf8") as f:
        lines = f.read().splitlines()
        assert lines.index("export TEST1=1") != -1
        assert lines.index("export TEST2=2") != -1

    # cleanup
    exec("deluser abc")
    exec("rm /home/abc -rf")


def test_ensure_del_file_content():
    with open("test_delete.txt", "w", encoding="utf8") as f:
        f.write("1111\n2222\n3333\n4444")
    ensure_del_file_content("test_delete.txt", "\n".join(["2222", "3333\n"]))

    with open("test_delete.txt", "r", encoding="utf8") as f:
        assert f.read() == "1111\n4444"


def add_maxsize(m: re.Match):
    s = m[1]
    if s.find("maxsize") != -1:
        return m.group()
    else:
        return "{\n\tmaxsize 100M" + s + "}"


def modifier(content):
    new_content = re.sub(r"{(.+?)}", add_maxsize, content, flags=re.DOTALL)
    return new_content


def test_modifier():
    assert modifier(
        "\n".join(
            [
                "/var/log/syslog",
                "{",
                "	rotate 7",
                "	endscript",
                "}",
                "{",
                "	rotate 7",
                "	endscript",
                "}",
            ]
        )
    ) == "\n".join(
        [
            "/var/log/syslog",
            "{",
            "	maxsize 100M",
            "	rotate 7",
            "	endscript",
            "}",
            "{",
            "	maxsize 100M",
            "	rotate 7",
            "	endscript",
            "}",
        ]
    )

    assert modifier(
        "\n".join(
            [
                "/var/log/syslog",
                "{",
                "	maxsize 100M",
                "	rotate 7",
                "	endscript",
                "}",
                "{",
                "	maxsize 100M",
                "	rotate 7",
                "	endscript",
                "}",
            ]
        )
    ) == "\n".join(
        [
            "/var/log/syslog",
            "{",
            "	maxsize 100M",
            "	rotate 7",
            "	endscript",
            "}",
            "{",
            "	maxsize 100M",
            "	rotate 7",
            "	endscript",
            "}",
        ]
    )


def test_ensure_modify_file():
    filename = "test_modify.txt"
    with open(filename, "w", encoding="utf8") as f:
        f.write(
            "\n".join(
                [
                    "/var/log/syslog",
                    "{",
                    "	rotate 7",
                    "	endscript",
                    "}",
                    "{",
                    "	rotate 7",
                    "	endscript",
                    "}",
                ]
            )
        )

    ensure_modify_file(filename, modifier)

    assert file_content(filename) == "\n".join(
        [
            "/var/log/syslog",
            "{",
            "	maxsize 100M",
            "	rotate 7",
            "	endscript",
            "}",
            "{",
            "	maxsize 100M",
            "	rotate 7",
            "	endscript",
            "}",
        ]
    )


def test_ensure_comment_lines():
    filename = "test_comment.txt"
    with open(filename, "w", encoding="utf8") as f:
        f.write("  name: abc\n  ip: 127.0.0.1")

    assert ensure_comment_lines(filename, "ip:") == True
    assert ensure_comment_lines(filename, "ip:") == False

    assert file_content(filename) == "  name: abc\n  # ip: 127.0.0.1"


def test_ensure_uncomment_lines():
    filename = "test2_comment.txt"
    with open(filename, "w", encoding="utf8") as f:
        f.write("  name: abc\n  # ip: 127.0.0.1\n#123\n #  432\n#432")

    assert (
        ensure_uncomment_lines(filename, ["432", "ip: 127.0.0.1"]) == True
    )  # modified
    assert (
        ensure_uncomment_lines(filename, ["432", "ip: 127.0.0.1"]) == False
    )  # not modified

    assert file_content(filename) == "  name: abc\n  ip: 127.0.0.1\n#123\n 432\n432"


def test_ensure_unlink_file():
    ensure_unlink_file("test_delete.txt")
    ensure_unlink_file("test_delete.link")
    exec("touch test_delete.txt && ln -s `pwd`/test_delete.txt test_delete.link")
    assert os.path.isfile("test_delete.txt")
    assert os.path.islink("test_delete.link")

    assert ensure_unlink_file("test_delete.txt") == True
    assert not os.path.exists("test_delete.txt")
    assert os.path.islink("test_delete.link")

    assert ensure_unlink_file("test_delete.link") == True
    assert not os.path.exists("test_delete.link")
    assert not os.path.exists("test_delete.txt")


def test_append_lines():
    filename = "test_append.txt"

    with open(filename, "w", encoding="utf8") as f:
        assert f.write("hello")  # without \n

    with TextFileModifier(filename) as mod:
        assert mod.modified == False
        mod.append_lines("world")
        assert mod.modified == True
        mod.save()

        assert file_content(filename) == "hello\nworld\n"

        mod.append_lines("of west")

    assert file_content(filename) == "hello\nworld\nof west\n"


def test_replace_line():
    filename = "test_replace.txt"

    with open(filename, "w", encoding="utf8") as f:
        assert f.write("line1\n  line2  \nline3")

    with TextFileModifier(filename) as mod:
        mod.replace_a_line("  line2", "  new_line2")
        mod.replace_a_line("line3", "new_line3")

    assert file_content(filename) == "line1\n  new_line2\nnew_line3\n"


def test_delete_lines_with_pattern():
    filename = "test_append.txt"
    ensure_file(
        filename, "hello\n127.0.0.1::  \tsimba.com\nworld\n127.0.0.1::  \tsimba.com\n"
    )

    with TextFileModifier(filename) as mod:
        mod.delete_lines_with_pattern(r"not exist")
        assert mod.modified == False
        mod.delete_lines_with_pattern(r"^([0-9a-zA-Z\.\:]+)\s+(.+)$")
        assert mod.modified == True
        mod.append_lines(
            [
                "192.168.10.1  x.com",
                "192.168.10.2  mi.com",
            ]
        )

    assert (
        file_content(filename)
        == "hello\nworld\n192.168.10.1  x.com\n192.168.10.2  mi.com\n"
    )


def test_set_content():
    filename = "test_append.txt"
    ensure_file(filename, "hello\nworld")

    with TextFileModifier(filename) as mod:
        mod.set_content(["abc\n", "", "def"])

    assert file_content(filename) == "abc\n\n\ndef\n"
