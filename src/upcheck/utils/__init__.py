# -*- coding: utf-8 -*-
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
