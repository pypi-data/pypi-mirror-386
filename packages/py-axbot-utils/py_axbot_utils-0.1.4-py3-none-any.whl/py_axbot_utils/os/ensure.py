import filecmp
import json
import os
import re
import shutil
import stat
import sys
from typing import List, Union

from .exec import exec, exec_get_output
from .println import println

__ENSURE_DEBUG = False


def enable_ensure_debug():
    # pylint: disable=global-statement
    global __ENSURE_DEBUG
    __ENSURE_DEBUG = True


def ensure_dirs(path: str):
    println(f"# ensure dir '{path}/'")
    if not os.path.isdir(path):
        println(f"creating directory: '{path}'")
        if not __ENSURE_DEBUG:
            os.makedirs(path)


def ensure_comment_lines(filename: str, starters: Union[List[str], str]):
    lines = None
    with open(filename, "r", encoding="utf8") as f:
        lines = f.read().splitlines()

    if isinstance(starters, str):
        starters = [starters]

    updated = False
    for i, line in enumerate(lines):
        for start in starters:
            striped_line = line.strip()
            if striped_line.startswith(start):
                lines[i] = line[: len(line) - len(striped_line)] + f"# {striped_line}"
                updated = True

    new_content = "\n".join(lines)
    if updated and not __ENSURE_DEBUG:
        with open(filename, "w", encoding="utf8") as f:
            f.write(new_content)

    return updated


def ensure_uncomment_lines(filename: str, starters: Union[List[str], str]):
    lines = None
    with open(filename, "r", encoding="utf8") as f:
        lines = f.read().splitlines()

    if isinstance(starters, str):
        starters = [starters]

    updated = False
    for i, line in enumerate(lines):
        for start in starters:
            striped_line = line.strip()
            if striped_line.startswith("#"):
                target_content = striped_line[1:].strip()
                if target_content.startswith(start):
                    lines[i] = line[: len(line) - len(striped_line)] + f"{target_content}"
                    updated = True

    if updated:
        with open(filename, "w", encoding="utf8") as f:
            f.write("\n".join(lines))

    return updated


def ensure_access(path: str, permission: str = "ax:ax"):
    println(f"# ensure access of '{path}/'")
    if not os.path.isdir(path):
        println(f"error: directory not exists: '{path}'")
        sys.exit(1)

    exec(f"chown -R {permission} {path}")
    exec(f"find -L {path} -type d -print0 | sudo xargs -0 chmod ug+sw")

    rtn = exec_get_output(f"find -L {path} -type f  | grep .", checked=False)
    if rtn.returncode == 0:
        exec(f"find -L {path} -type f -print0 | sudo xargs -0 chmod ug+w", debug=__ENSURE_DEBUG)


def ensure_link_file(src: str, dest: str) -> bool:
    if not os.path.isfile(src):
        raise Exception(f"Failed to create link: source file doesn't exist: {src}")

    should_recreate_link = (not os.path.islink(dest)) or (os.readlink(dest) != src)

    if should_recreate_link:
        if os.path.isfile(dest) or os.path.islink(dest):
            println(f"debug: remove old link {dest}")
            exec(f"unlink {dest}", debug=__ENSURE_DEBUG)
        println(f"create link: {dest} -> {src}")
        exec(f"ln -s {src} {dest}", debug=__ENSURE_DEBUG)

    return should_recreate_link


def ensure_unlink_file(filename: str, verbose=True):
    try:
        if verbose:
            println(f"# ensure unlink {filename}")
        mode = os.lstat(filename).st_mode
        if stat.S_ISREG(mode) or stat.S_ISLNK(mode):
            if verbose:
                print(f"> unlink {filename}")
            os.unlink(filename)
            return True
    except FileNotFoundError:
        pass

    return False


def copyfile_if_different(src: str, dest: str):
    if not os.path.exists(dest) or not filecmp.cmp(src, dest):
        shutil.copyfile(src, dest)
        return True

    return False


def copy2_if_different(src: str, dest: str):
    """
    Copy data and metadata.
    """
    if not os.path.exists(dest) or not filecmp.cmp(src, dest):
        shutil.copy2(src, dest)
        return True

    return False


def ensure_enable_service(file):
    println(f"# enable service {file}")
    if not os.path.isfile(file):
        raise Exception(f"Failed to enable service: File not found {file}")
    basename = os.path.basename(file)
    if copyfile_if_different(file, f"/etc/systemd/system/{basename}"):
        exec("systemctl daemon-reload", debug=__ENSURE_DEBUG)
        exec(f"systemctl enable {basename}", debug=__ENSURE_DEBUG)


def ensure_enable_os_service(service_name):
    println(f"# enable service {service_name}")
    exec(f"systemctl enable {service_name}", debug=__ENSURE_DEBUG)


def ensure_disable_service(name):
    println(f"# disable service {name}")
    rtn = exec_get_output(f"systemctl is-enabled {name}", checked=False)
    if rtn.returncode == 0:
        exec(f"systemctl disable {name}", debug=__ENSURE_DEBUG)


def ensure_delete_service(name):
    rtn = exec_get_output(f"systemctl is-enabled {name}", checked=False)
    if rtn.returncode == 0:
        exec(f"systemctl stop {name}", debug=__ENSURE_DEBUG)
        exec(f"systemctl disable {name}", debug=__ENSURE_DEBUG)
    filename = f"/etc/systemd/system/{name}.service"
    ensure_unlink_file(filename)


def ensure_group(group_name):
    println(f"# ensure group '{group_name}'")
    rtn = exec_get_output(f'grep -q -E "^{group_name}:" /etc/group', checked=False)
    if rtn.returncode != 0:
        exec(f"groupadd {group_name}", debug=__ENSURE_DEBUG)


def user_exists(user_name) -> bool:
    rtn = exec_get_output(f'grep -q -E "^{user_name}:" /etc/passwd', checked=False)
    return rtn.returncode == 0


def ensure_user(user_name):
    println(f"# ensure user '{user_name}'")
    if not user_exists(user_name):
        exec(f'adduser --disabled-password --gecos "" --ingroup {user_name} {user_name}', debug=__ENSURE_DEBUG)


def ensure_user_in_groups(user_name, groups: str):
    """
    Add user to group

    ```
    ensure_user_in_groups("simba", "i2c,gpio,dialout,bluetooth,sudo,ax,systemd-journal")
    ```
    """
    println(f"# ensure user '{user_name}' in groups '{groups}'")
    rtn = exec_get_output(f"groups {user_name}")
    existing_groups = rtn.stdout.split(":")[1].strip().split(" ")
    missing_groups = set(groups.split(",")).difference(set(existing_groups))
    missing_groups = list(missing_groups)
    if len(missing_groups) != 0:
        println(f"debug: missing groups {missing_groups}")
        exec(f"usermod -aG {groups} {user_name}")


def ensure_file(filename, content: str, echo=True):
    """
    # pylint: disable=line-too-long
    ensure_file(
        "/etc/profile.d/ax-robot.sh",
        "\n".join(
            [
                "export PYTHONDONTWRITEBYTECODE=1",
                "[ -d /opt/ros/melodic ] && source /opt/ros/melodic/setup.sh",
                "[ -d /opt/ros/noetic ] && source /opt/ros/noetic/setup.sh",
                "source /opt/ax/platform/setup.sh",
                "",
            ]
        ),
    )
    """
    if echo:
        println(f"# ensure file {filename} has correct content")
        for line in content.splitlines():
            println("debug: " + line)
    existing_content = None
    try:
        with open(filename, "r", encoding="utf8") as f:
            existing_content = f.read()
    except FileNotFoundError as _e:
        pass

    if existing_content != content:
        print(f"Ensure file content {filename}\n{content}")
        with open(filename, "w", encoding="utf8") as f:
            f.write(content)


class TextFileModifier:
    def __init__(self, filename: str) -> None:
        self.__filename = filename
        self.__old_lines = []
        self.__lines = []
        try:
            with open(filename, "r", encoding="utf8") as f:
                self.__lines: str = f.readlines()
            self.__old_lines = [*self.__lines]
        except FileNotFoundError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, type, value, trace):
        self.save()

    @staticmethod
    def __convert_param_lines(line_or_lines: Union[List[str], str]):
        if isinstance(line_or_lines, str):
            lines = [line_or_lines]
        elif isinstance(line_or_lines, list):
            lines = line_or_lines
        else:
            raise TypeError("parameter must be `str` or `List[str]`")

        for i, line in enumerate(lines):
            lines[i] = line + "\n"

        return lines

    def set_content(self, line_or_lines: Union[List[str], str]):
        lines = TextFileModifier.__convert_param_lines(line_or_lines)
        self.__lines = lines

    def append_lines(self, line_or_lines: Union[List[str], str]):
        lines = TextFileModifier.__convert_param_lines(line_or_lines)

        if self.__lines and not self.__lines[-1].endswith("\n"):
            self.__lines[-1] += "\n"

        self.__lines.extend(lines)

    def replace_a_line(self, old_line: str, new_line: str):
        if not new_line.endswith("\n"):
            new_line += "\n"
        for i, line in enumerate(self.__lines):
            if line.rstrip() == old_line.rstrip():
                self.__lines[i] = new_line

    @property
    def modified(self):
        return self.__old_lines != self.__lines

    def save(self):
        if self.__old_lines != self.__lines:
            tmp = self.__filename + ".tmp"
            with open(tmp, "w", encoding="utf8") as f:
                f.writelines(self.__lines)
            os.rename(tmp, self.__filename)

    def delete_lines_with_pattern(self, pattern: str, echo=True):
        if echo:
            print(f"Removing lines in {self.__filename} with pattern '{pattern}'")

        regex = re.compile(pattern)
        new_lines = []
        for line in self.__lines:
            m = regex.match(line)
            if m:
                if echo:
                    print(f"  - {line}")
            else:
                new_lines.append(line)
        self.__lines = new_lines


def ensure_lines_in_file(filename, lines: List[str]):
    """
    ensure_lines_in_file("/boot/config.txt", ["dtparam=i2c_arm=on", "dtparam=ant2"])
    """
    println(f"# ensure lines in file {filename}:")
    with open(filename, "r", encoding="utf8") as f:
        existing_lines = f.read().splitlines()
    for line in lines:
        println(f"debug: {line}")
        if not line in existing_lines:
            exec(f'printf "{line}\\n" >> {filename}', debug=__ENSURE_DEBUG)


def find_missing_packages(packages: List[str], verbose=False) -> List[str]:
    if len(packages) == 0:
        return []

    # get installed packages
    rtn = exec_get_output("dpkg-query -l")
    lines = rtn.stdout.splitlines()
    # Like: ii  adduser                              3.118                               all          add and remove
    line_re = re.compile(r"^[^\s]+\s+([^\s]+)\s+.*")
    installed_packages = []
    for line in lines:
        m = line_re.match(line)
        if m:
            installed_packages.append(m[1])

    # remove tailing ARCH like "xxx:arm64"
    installed_packages = set(map(lambda x: x if x.find(":") == -1 else x[: x.find(":")], installed_packages))
    wanted_packages = set(map(lambda x: x if x.find(":") == -1 else x[: x.find(":")], packages))
    diff = wanted_packages.difference(set(installed_packages))
    if len(diff) == 0:
        if verbose:
            println("debug: All required packages found. Skip.")
            for pkg in packages:
                println(f"debug: skipped {pkg}")
    elif verbose:
        println("Some APT packages are missing: " + str(diff))

    return list(diff)


def check_apt_packages(packages: List[str]):
    """
    sys.exit(1) if packages are missing
    """
    println("# check APT packages")

    missing_ones = find_missing_packages(packages, verbose=True)

    if len(missing_ones) != 0:
        sys.exit(1)


def ensure_apt_install(packages: List[str]):
    """
    Install APT packages if not exist

    ```
    ensure_apt_install(
        [
            "python3-pip",
            "wiringpi",
            "liblog4cxx10v5",
        ]
    )
    ```

    """
    println("# ensure APT packages")

    missing_ones = find_missing_packages(packages, verbose=True)

    if len(missing_ones) != 0:
        exec("apt-get update --allow-releaseinfo-change")
        package_list = " ".join(missing_ones)
        exec(f"apt-get install -y {package_list}")


def __find_missing_pip3_packages(packages: List[str]):
    if len(packages) == 0:
        return False

    # get installed packages
    rtn = exec_get_output("pip3 --disable-pip-version-check list --format=json")
    installed_packages = json.loads(rtn.stdout)
    installed_packages = list(map(lambda x: x["name"], installed_packages))

    # ignore dash and underscore
    installed_packages = [package.replace("-", "_") for package in installed_packages]
    packages = [package.replace("-", "_") for package in packages]

    diff = set(packages).difference(set(installed_packages))
    if len(diff) == 0:
        println("debug: All required packages found. Skip.")
        for pkg in packages:
            println(f"debug: skipped {pkg}")
        return False

    println("Some PIP packages are missing: " + str(diff))

    return True


def check_pip3_packages(packages: List[str]):
    """
    sys.exit() if some packages are missing.
    """
    println("# check pip3 packages")

    if __find_missing_pip3_packages(packages):
        sys.exit(1)


def ensure_pip3_install(packages: List[str]):
    """
    Install pip3 packages if not exist

    ```
    ensure_pip3_install(
        [
            "termcolor",
            "psutil",
        ]
    )
    ```
    """
    println("# ensure pip3 packages")

    if __find_missing_pip3_packages(packages):
        package_list = " ".join(packages)
        exec(f"pip3 install --disable-pip-version-check {package_list}")


def ensure_no_pyc(path: str):
    println("# ensure no '*.pyc' exists")
    rtn = exec_get_output(f'find {path} -name "*.pyc" | grep .', checked=False)
    if rtn.returncode == 0:
        println("Python cache files found:")
        for line in rtn.stdout.splitlines():
            print("  " + line)
        exec("find -L " + path + ' -name "*.pyc" -exec rm {} \\;')


def ensure_del_file_content(filename, content: str, echo=True):
    if echo:
        println(f"# ensure file {filename} has correct content")
        for line in content.splitlines():
            println("debug: " + line)
    existing_content = None
    try:
        with open(filename, "r", encoding="utf8") as f:
            existing_content = f.read()
    except FileNotFoundError as _e:
        pass

    new_content = existing_content.replace(content, "")
    if existing_content != new_content:
        with open(filename, "w", encoding="utf8") as f:
            f.write(new_content)


def ensure_lock_user(user: str):
    println(f"# will lock user '{user}'")
    exec(f"usermod --lock {user}")


def ensure_modify_file(filename, modifier_func):
    with open(filename, "r", encoding="utf8") as f:
        existing_content = f.read()
    content = modifier_func(existing_content)
    if existing_content != content:
        print(f"Ensure modify file {filename}\n{content}")
        with open(filename, "w", encoding="utf8") as f:
            f.write(content)
