# -*- coding: utf-8 -*-
import atexit
import os
import shutil
import tempfile
from pathlib import Path
from typing import Mapping

from ruamel import yaml as ruamel_yaml
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO


class StringYAML(YAML):
    """Wraps :class:~YAML to be able to dump a string from a yaml object.

    More details: http://yaml.readthedocs.io/en/latest/example.html#output-of-dump-as-a-string

    Args:
        **kwargs (dict): arguments for the underlying :class:~YAML class
    """

    def __init__(self, **kwargs):
        super(StringYAML, self).__init__(**kwargs)

    def dump(self, data, stream=None, split_multiline_strings=True, **kw):
        inefficient = False
        if stream is None:
            inefficient = True
            stream = StringIO()
        if split_multiline_strings:
            ruamel_yaml.scalarstring.walk_tree(data)

        YAML.dump(self, data, stream, **kw)
        if inefficient:
            return stream.getvalue()


def create_temp_dir_with_text_files(file_map: Mapping[str, str]) -> str:
    """Create a temp dir that will be deleted on application exit, and create text files using the provided arguments.

    Args:

        **file_map (str): a map with relative paths as key, and the file content as value

    Returns:
        str: the path to the temporary directory
    """

    temp_dir = tempfile.mkdtemp()

    def delete_temp_dir():
        shutil.rmtree(temp_dir)

    is_debug = (
        True if os.environ.get("UPCHECK_DEBUG", "false").lower() == "true" else False
    )

    if not is_debug:
        atexit.register(delete_temp_dir)

    for file_name, content in file_map.items():
        full_path = os.path.join(temp_dir, file_name)
        f = Path(full_path)
        os.makedirs(f.parent, mode=0o700, exist_ok=True)
        f.write_text(content)

    return temp_dir
