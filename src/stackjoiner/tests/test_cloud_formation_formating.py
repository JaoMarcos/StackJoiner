import os
from pathlib import Path
from unittest import TestCase
import yaml

from src.stackjoiner.stackjoiner import StackJoiner, CFTag
from stackjoiner.yaml_loader import YamlLoader


class TestCloudFormationTemplate(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.text_ref = """
        k1: !Ref v1
        k2: 
            Ref: v2
        """

        cls.text_get_att = """
                k1: !GetAtt v1.a1
                k2: 
                    Fn::GetAtt: [v1,a1]
                """

        cls.text_both = """
                        k1: !GetAtt v1.a1
                        k2: 
                            Fn::GetAtt: [v1,a1]
                        """

    def test_ref(self):
        data = YamlLoader.load(self.text_ref)
        assert 'k1' in data
        assert 'k1' in data
        assert isinstance(data['k1'], CFTag)
        assert isinstance(data['k2'], CFTag)

        assert data['k1'].tag == '!Ref'
        assert data['k1'].value == 'v1'

        assert data['k2'].tag == '!Ref'
        assert data['k2'].value == 'v2'

    def test_get_att(self):
        data = YamlLoader.load(self.text_get_att)
        assert 'k1' in data
        assert 'k1' in data
        assert isinstance(data['k1'], CFTag)
        assert isinstance(data['k2'], CFTag)

        assert data['k1'].tag == '!GetAtt'
        assert data['k1'].value == ['v1', 'a1']

        assert data['k2'].tag == '!GetAtt'
        assert data['k2'].value == ['v1', 'a1']

        assert YamlLoader.dump(data['k2']) == YamlLoader.dump(data['k1'])

    def test_get_att2(self):

        text = """
        Outputs:
          VPC:
            Description: "VPC"
            Value: !GetAtt VPCStack.Outputs.VPC"""
        data = YamlLoader.load(text)
        print(data)
        data_str = YamlLoader.dump(data)
        assert '- VPCStack' in data_str

    def test_list(self):
        text ="""
        k1: 
            - Ref: v1
            - !Ref v2
            - !GetAtt v3.a1
            - Fn::GetAtt: [v4,a1]
            
        """
        data = YamlLoader.load(text)
        assert 'k1' in data

        for i in data['k1']:
            assert isinstance(i, CFTag)

    def test_join1(self):
        text = """
           k3: !Join 
                   - ":"
                   -   - a
                       - !Ref b
                       - Fn::GetAtt: [c,d]
           """
        data = YamlLoader.load(text)
        print(data)
        data_str = YamlLoader.dump(data)
        assert 'Fn::GetAtt' in data_str


    def test_join(self):
        text = """
        k3: !Join 
            - ":"
            -   - a
                - !Ref b
                - Fn::GetAtt: 
                    - c
                    - d
        """
        data = YamlLoader.load(text)
        print(data)

        text = """
        k1: 
            "Fn::Join" : [ ":", [ "a", !Ref "b", "c" ] ]
        k2: !Join [ ":", [ a, !Ref b, c ] ]
        k3: !Join 
                - ":"
                -   - a
                    - !Ref b
                    - c
        """
        data = YamlLoader.load(text)

        assert YamlLoader.dump(data['k2']) == YamlLoader.dump(data['k1'])
        assert YamlLoader.dump(data['k3']) == YamlLoader.dump(data['k1'])

        text2 = """
                k1: 
                    "Fn::Join" : [ ":", [ "a", !Ref "b", !GetAtt c.d ] ]
                k2: !Join [ ":", [ a, !Ref b, !GetAtt c.d ] ]
                k3: !Join 
                        - ":"
                        -   - a
                            - !Ref b
                            - Fn::GetAtt: 
                                - c
                                - d
                """
        data = YamlLoader.load(text2)
        # assert YamlLoader.dump(data['k2']) == YamlLoader.dump(data['k1'])
        assert YamlLoader.dump(data['k3']) == YamlLoader.dump(data['k1'])

