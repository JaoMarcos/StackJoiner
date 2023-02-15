import os
from pathlib import Path
from unittest import TestCase

from src.stackjoiner.stackjoiner import StackJoiner


class TestLoadTemplate(TestCase):

    @classmethod
    def setUpClass(cls):
        current_path = Path(os.path.dirname(os.path.realpath(__file__)))
        cls.file_path = current_path / "resources" / "single_nested_template.yaml"

    def test_load_file(self):
        stack = StackJoiner(self.file_path )
        assert stack.template is not None

    def test_load_children(self):
        stack = StackJoiner(self.file_path )
        assert 'SecondBucket' in stack.children
        assert isinstance(stack.children['SecondBucket'], StackJoiner)

    def test_merge_children(self):
        stack = StackJoiner(self.file_path)
        stack.merge()
        assert 'SecondBucketS3Bucket' in stack.resources
