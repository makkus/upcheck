# -*- coding: utf-8 -*-
import os
import subprocess
from pathlib import Path
from typing import Optional

from deepdiff import DeepHash
from frtls.dicts import get_seeded_dict
from frtls.files import ensure_folder
from upcheck.defaults import upcheck_app_dirs


CACHE_DIR = os.path.join(upcheck_app_dirs.user_cache_dir, "doc_gen")
ensure_folder(CACHE_DIR)

os_env_vars = get_seeded_dict(os.environ, {"UPCHECK_CONSOLE_WIDTH": "100"})


def define_env(env):
    """
    This is the hook for defining variables, macros and filters

    - variables: the dictionary that contains the environment variables
    - macro: a decorator function, to declare a macro.
    """

    # env.variables["baz"] = "John Doe"

    @env.macro
    def cli(
        *command,
        print_command: bool = True,
        code_block: bool = True,
        max_height: Optional[int] = None,
    ):

        hashes = DeepHash(command)
        hash_str = hashes[command]

        cache_file: Path = Path(os.path.join(CACHE_DIR, hash_str))
        if cache_file.is_file():
            stdout = cache_file.read_text()
        else:
            try:
                result = subprocess.check_output(command, env=os_env_vars)
                stdout = result.decode()
                cache_file.write_text(stdout)
            except Exception as e:
                print(e)
                raise e

        if print_command:
            stdout = f"> {' '.join(command)}\n{stdout}"
        if code_block:
            stdout = "``` console\n" + stdout + "\n```\n"

        if max_height is not None and max_height > 0:
            stdout = f"<div style='max-height:{max_height}px;overflow:auto'>\n{stdout}\n</div>"

        return stdout

    @env.macro
    def inline_file_as_codeblock(path, format: str = ""):
        f = Path(path)
        return f"```{format}\n{f.read_text()}\n```"
