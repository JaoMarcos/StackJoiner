from typing import Dict

import yaml
from yaml import ScalarNode

from .cf_tag import CFTag

yaml.SafeLoader.add_constructor("!Ref", CFTag.from_yaml)
yaml.SafeLoader.add_constructor("!GetAtt", CFTag.from_yaml)
yaml.SafeLoader.add_constructor("!Join", CFTag.from_yaml)
yaml.SafeLoader.add_constructor("!Sub", CFTag.from_yaml)
yaml.SafeLoader.add_constructor("!Select", CFTag.from_yaml)
yaml.default_flow_style = None
# Required for safe_dump
yaml.SafeDumper.add_multi_representer(CFTag, CFTag.to_yaml)


def load_json(data):
    data[1] = [YamlLoader.replace_keys(i) for i in data[1]]
    return data


def load_get_att(data):
    return ".".join(data)


class YamlLoader:
    replace_map = {
        "Ref": lambda x: ("!Ref", x),
        "Fn::GetAtt": lambda x: ("!GetAtt", load_get_att(x)),
        "Fn::Join": lambda x: ("!Join", load_json(x)),
    }

    @classmethod
    def load(cls, text):
        data = yaml.load(text, Loader=yaml.SafeLoader)
        cls.replace_keys(data)
        return data

    @classmethod
    def dump(cls, data, stream=None):
        return yaml.safe_dump(data, stream)

    @classmethod
    def replace_keys(cls, data: Dict):
        if not isinstance(data, dict):
            return data

        keys = data.keys()
        for k in keys:
            if k in cls.replace_map:
                tag, value = cls.replace_map[k](data[k])
                data = CFTag.from_yaml(None, ScalarNode(tag=tag, value=value))
            elif isinstance(data[k], dict):
                data[k] = cls.replace_keys(data[k])

            elif isinstance(data[k], list):
                for i, _ in enumerate(data[k]):
                    if isinstance(data[k][i], dict):
                        data[k][i] = cls.replace_keys(data[k][i])
            elif isinstance(data[k], CFTag) and data[k].tag == "!Join":
                for i, v in enumerate(data[k].value[1]):
                    data[k].value[1][i] = cls.replace_keys(data[k].value[1][i])

        return data
