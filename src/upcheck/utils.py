# -*- coding: utf-8 -*-
import os
import re
import shutil
import time
from pathlib import Path
from typing import Sequence, Union

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


def delete_section_in_text_file(
    path: Union[str, Path],
    prefix: Sequence[str],
    postfix: Sequence[str],
    backup: bool = True,
) -> None:

    ensure_section_in_text_file(
        path=path,
        section_content="",
        prefix=prefix,
        postfix=postfix,
        backup=backup,
        add_pre_and_postfix=False,
    )


def ensure_section_in_text_file(
    path: Union[str, Path],
    section_content: str,
    prefix: Sequence[str],
    postfix: Sequence[str],
    backup: bool = True,
    add_pre_and_postfix: bool = True,
) -> None:
    """Makes sure a section of text is contained within a text file, between one or several lines of pre- and postfix content.

    The pre- and postfix content is used as a unique marker to signal to this function whether this or (a version of) this content
    was added before.
    """

    if isinstance(path, Path):
        path = path.resolve().as_posix()

    if not os.path.exists(path):
        content = ""
    else:
        with open(path, "r") as f:
            content = f.read() + "\n"

    pattern_string = ""
    content_string = ""
    for line in prefix[0:-1]:
        pattern_string = pattern_string + line + r"(?:\n|\r|\r\n?)"
        if add_pre_and_postfix:
            content_string = content_string + line + "\n"

    pattern_string = pattern_string + prefix[-1]
    if add_pre_and_postfix:
        content_string = content_string + prefix[-1] + "\n"

    pattern_string = pattern_string + r"[\s\S]*"
    content_string = content_string + section_content + "\n"

    for line in postfix:
        pattern_string = pattern_string + line + r"(?:\n|\r|\r\n?)"
        if add_pre_and_postfix:
            content_string = content_string + line + "\n"

    pattern = re.compile(pattern_string)
    result = re.search(pattern, content)

    if not result:
        if content_string:
            c = f"{content}{content_string}".strip() + "\n"
            with open(path, "w") as f:
                f.write(c)

    else:
        replaced = re.sub(pattern, content_string, content)

        if replaced == content:
            return

        if backup:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            backup_name = f"{path}.{timestamp}.bak"
            shutil.copy2(path, backup_name)

        with open(path, "w") as f:
            f.write(replaced.strip() + "\n")
