from typing import Dict

import yaml
from yaml import ScalarNode


class CFTag(yaml.YAMLObject):
    tagger_elements: Dict = {}

    def __init__(self, tag, value):
        self.tag = tag
        self.value = value

    def get_tag(self):
        if self.tag == "!Ref":
            return f"{self.tag[1:]}"
        return f"Fn::{self.tag[1:]}"

    def __getstate__(self):
        return {f"{self.get_tag()}": self.value}

    def __repr__(self):
        return f"{self.tag[:]} {self.value}"

    def __eq__(self, other):
        return self.tag == other.tag and self.value == other.value

    @classmethod
    def get_data(cls, data):
        if isinstance(data, list):
            for i, d in enumerate(data):
                data[i] = cls.get_data(d)
        elif hasattr(data, "value"):
            if data.tag.startswith("!"):
                data = cls.from_yaml(None, data)
            elif data.tag.startswith("tag:yaml.org,2002:map"):
                data = {data.value[0][0].value: cls.get_data(data.value[0][1].value)}
            else:
                value = data.value
                data = cls.get_data(value)

        return data

    @classmethod
    def from_yaml(cls, loader, node):
        tag = CFTag(node.tag, node.value)
        if node.tag in ["!Ref", "!Sub"]:
            elements = cls.tagger_elements.get(str(node.value), [])
            elements.append(tag)
            cls.tagger_elements[str(node.value)] = elements
        elif node.tag in ["!GetAtt"]:
            value = node.value
            if isinstance(node.value, str):
                value = value.split(".")
                value = [value[0], ".".join(value[1:])]

            tag.value = value
            elements = cls.tagger_elements.get(str(value), [])
            elements.append(tag)
            cls.tagger_elements[str(value)] = elements

        elif node.tag in ["!Join","!Select"]:
            v = cls.get_data(node.value)
            tag = CFTag(node.tag, v)

        return tag

    @classmethod
    def to_yaml(cls, dumper, data):
        if data.tag == "!Join":
            if isinstance(data.value[0], ScalarNode):
                new_v = [data.value[0].value]
            else:
                new_v = [data.value[0]]
            second_list = []

            new_list = data.value[1]
            if not isinstance(new_list, list):
                new_list = new_list.value

            for v in new_list:
                if hasattr(v, "tag") and v.tag.startswith("!"):
                    second_list.append(CFTag(v.tag, v.value).__getstate__())
                else:
                    value = v.value if hasattr(v, "value") else v
                    second_list.append(value)
            new_v.append(second_list)

            return dumper.represent_sequence(data.tag, new_v)
        if data.tag == "!Select":
            new_v = []
            for v in data.value:
                if not hasattr(v,'tag'):
                    new_v.append(v)
                elif v.tag.startswith("!"):
                    new_v.append(v.__getstate__())
                else:
                    new_v.append(v.value)

            return dumper.represent_sequence(data.tag, new_v)
        elif data.tag == "!GetAtt":
            return dumper.represent_dict({data.get_tag(): data.value})
        return dumper.represent_scalar(data.tag, str(data.value))
