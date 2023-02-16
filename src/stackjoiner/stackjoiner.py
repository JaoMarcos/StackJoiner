import ast
import os
from string import Formatter
from typing import List, Dict

import yaml

import yaml

from stackjoiner.cf_tag import CFTag
from stackjoiner.yaml_loader import YamlLoader

# Required for safe_load
yaml.SafeLoader.add_constructor('!Ref', CFTag.from_yaml)
yaml.SafeLoader.add_constructor('!GetAtt', CFTag.from_yaml)
yaml.SafeLoader.add_constructor('!Join', CFTag.from_yaml)
yaml.SafeLoader.add_constructor('!Sub', CFTag.from_yaml)
yaml.SafeLoader.add_constructor('!Select', CFTag.from_yaml)
yaml.default_flow_style = None
# Required for safe_dump
yaml.SafeDumper.add_multi_representer(CFTag, CFTag.to_yaml)


# yaml.SafeDumper.add_multi_representer(GetAttTag, GetAttTag.to_yaml)
def noop(self, *args, **kw):
    pass


# yaml.emitter.Emitter.process_tag = noop

class StackJoiner:
    def __init__(self, template_path=None, load=True):
        self.template_path = template_path
        self.template_dir = os.path.dirname(template_path)
        self.tree = None
        self.parameters:Dict = {}
        self.resources:Dict = {}
        self.description = {}
        self.outputs:Dict = {}
        self.children:Dict[str,StackJoiner] = {}
        # self.ref_list: Dict[RefTag] = {}
        # self.get_att_list: Dict[GetAttTag] = {}
        self.tagger_elements: Dict[str, List[CFTag]] = {}
        self.template = None
        if load:
            self.load_file()

    def load_file(self):
        with open(self.template_path) as file:
            # The FullLoader parameter handles the conversion from YAML
            # scalar values to Python the dictionary format
            self.template = YamlLoader.load(file)

            self.tagger_elements: Dict[CFTag] = CFTag.tagger_elements
            CFTag.tagger_elements = {}
            # self.ref_list: Dict[RefTag] = RefTag.ref_list
            # RefTag.ref_list = {}
            # self.get_att_list: Dict[GetAttTag] = GetAttTag.get_att_list
            # GetAttTag.get_att_list = {}
            self.resources:Dict = self.template['Resources']
            self.parameters:Dict = self.template['Parameters']
            self.outputs:Dict = self.template['Outputs']
            self.children = self.get_children()

    def get_children(self):
        children = {}
        for resource_id, resource in self.resources.items():
            if resource['Type'] == 'AWS::CloudFormation::Stack':
                children_path = resource['Properties']['TemplateURL']
                children_path = children_path.replace('./', '')
                children_path = os.path.join(self.template_dir, children_path)
                children[resource_id] = StackJoiner(children_path)
        return children

    def replace_cf_tag(self, old_ref, new_value):
        elements = self.tagger_elements.get(old_ref, None)
        if elements:
            for e in elements:
                if isinstance(new_value, CFTag):
                    e.value = new_value.value
                    e.tag = new_value.tag
                else:
                    e.value = new_value

            if isinstance(new_value, CFTag):
                self.tagger_elements[str(new_value.value)] = list(self.tagger_elements[old_ref])
            else:
                self.tagger_elements[new_value] = list(self.tagger_elements[old_ref])
            del self.tagger_elements[old_ref]

    # def replace_ref(self, old_ref, new_value):
    #     r = self.ref_list.get(old_ref,None)
    #     if r:
    #         del self.ref_list[old_ref]
    #         if isinstance(new_value,RefTag):
    #             r.value = new_value.value
    #         else:
    #             r.value = new_value
    #         self.ref_list[new_value] = r


    def parse_child_parameter(self, child,child_id,new_parameters):
        new_resources_map = {}
        for p_id, p in child.parameters.items():
            # Check if we are passing a value for the parameter
            if p_id in new_parameters:
                new_p = new_parameters[p_id]
                if isinstance(new_p, CFTag):
                    child.replace_cf_tag(p_id, new_parameters[p_id])
                    new_resources_map[p_id] = new_p.value
                else:
                    p['Default'] = new_p
                    self.parameters[child_id + p_id] = p
                    new_resources_map[p_id] = child_id + p_id
            else:
                self.parameters[child_id + p_id] = p
                new_resources_map[p_id] = child_id + p_id
        return new_resources_map

    def remap_child_resource(self, child,child_id):
        new_resources_map = {}
        for r in child.resources:
            if r not in self.resources:
                self.resources[child_id + r] = child.resources[r]
                new_resources_map[r] = child_id + r
            else:
                print('element already exists')
                # rename elements for children if they already exist
                self.resources[child_id + r] = child.resources[r]
                new_resources_map[r] = child_id + r
        return new_resources_map

    def add_child_dependencies(self, child, child_id,resources_map):
        for resource_id, resource in self.resources.items():
            if 'DependsOn' in resource:
                dependencies = resource['DependsOn']

                dependencies_list = []
                if isinstance(dependencies, str):
                    dependencies_list.append(dependencies)
                elif isinstance(dependencies, list):
                    for d in dependencies:
                        dependencies_list.append(d)
                if child_id in dependencies_list:
                    resource['DependsOn'] = []
                    full_dependencies = []
                    for cr in child.resources:
                        full_dependencies.append(cr)
                    resource['DependsOn'] = [resources_map[d] for d in full_dependencies]
                    dependencies_list.remove(child_id)
                    resource['DependsOn'].extend(dependencies_list)
    def remap_dependencies(self, resource_map):
        for resource_id, resource in self.resources.items():
            if 'DependsOn' in resource:
                dependencies = resource['DependsOn']
                resource['DependsOn'] = []
                if isinstance(dependencies, str):
                    resource['DependsOn'].append(resource_map[dependencies])
                elif isinstance(dependencies, list):
                    for d in dependencies:
                        resource['DependsOn'].append(resource_map[d])

    def remap_resource(self, resource_map):
        new_d = self.tagger_elements.copy()
        for tag in new_d:
            if tag in resource_map:
                self.replace_cf_tag(tag, resource_map[tag])
            else:
                tag_str = new_d[tag][0].tag
                if tag_str == "!GetAtt":
                    values = ast.literal_eval(tag)
                    values[0] = resource_map[values[0]]
                    self.replace_cf_tag(tag, CFTag(tag_str, values))
                elif tag_str == "!Sub":
                    keys = [i[1] for i in Formatter().parse(tag) if i[1] is not None]
                    keys = [k for k in keys if k in resource_map]
                    if len(keys) > 0:
                        aux = tag
                        for k in keys:
                            aux = aux.replace(f'${{{k}}}', f'${{{resource_map[k]}}}')
                        self.replace_cf_tag(tag, aux)
    def merge(self):
        stacks_to_delete = []
        for child_id, child in self.children.items():
            child.merge()
            children_element = self.resources[child_id]
            new_parameters = children_element['Properties']['Parameters']
            new_resources_map = {}

            new_resources_map = self.parse_child_parameter(child,child_id,new_parameters)
            new_resources_map.update(self.remap_child_resource(child,child_id))

            stacks_to_delete.append(child_id)

            child.remap_resource(new_resources_map)


            # Check outputs
            new_d = self.tagger_elements.copy()
            for g, elements in new_d.items():
                # replace outputs ref
                if f"'{child_id}'" in g:
                    values = ast.literal_eval(g)
                    output_id = values[1].split('.')[-1]
                    e = child.outputs[output_id]['Value']
                    self.replace_cf_tag(g, e)
                elif f'{child_id}.' in g:
                    output_id = g.split('.')[0]
                    new_output_id = new_resources_map[output_id]
                    child.replace_cf_tag(g, new_output_id)

            # remap children dependencies:
            child.remap_dependencies(new_resources_map)
            # resolve stack dependencies
            self.add_child_dependencies(child,child_id,new_resources_map)

        for s in stacks_to_delete:
            del self.resources[s]
