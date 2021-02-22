import unittest

from ..helpers import config, std_objects

config = config.TestsConfig()

class SharedObjects:
    """The class is used to speed up testing"""
    def __init__(self):
        model = std_objects.get_model()
        self.mod_manager = std_objects.get_model_manager(model)
        self.val_dataset = std_objects.get_val_dataset()
        self.validator = std_objects.get_validator()

shared_objs = SharedObjects()

class TestValidator(unittest.TestCase):
    def test_evaluate_one_metric(self):
        eval_res = shared_objs.validator.eval(shared_objs.mod_manager, shared_objs.val_dataset)
        self.assertIsInstance(eval_res, float)
