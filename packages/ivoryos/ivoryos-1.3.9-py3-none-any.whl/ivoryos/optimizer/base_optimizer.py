### ivoryos/optimizers/base.py

from abc import ABC, abstractmethod



class OptimizerBase(ABC):
    def __init__(self, experiment_name:str, parameter_space: list, objective_config: dict, optimizer_config: dict, datapath:str=None):
        """
        :param experiment_name: arbitrary name
        :param parameter_space: list of parameter names
        [
            {"name": "param_1", "type": "range", "bounds": [1.0, 2.0], "value_type": "float"},
            {"name": "param_2", "type": "choice", "bounds": ["a", "b", "c"], "value_type": "str"},
            {"name": "param_3", "type": "range", "bounds": [0 10], "value_type": "int"},
        ]
        :param objective_config: objective configuration
                [
            {"name": "obj_1", "minimize": True, "weight": 1},
            {"name": "obj_2", "minimize": False, "weight": 1}
        ]
        :param optimizer_config: optimizer configuration
        optimizer_config={
            "step_1": {"model": "Random", "num_samples": 10},
            "step_2": {"model": "BOTorch"}
        }
        """
        self.experiment_name = experiment_name
        self.parameter_space = parameter_space
        self.objective_config = objective_config
        self.optimizer_config = optimizer_config
        self.datapath = datapath

    @abstractmethod
    def suggest(self, n=1):
        pass

    @abstractmethod
    def observe(self, results: dict):
        """
        observe
        :param results: {"objective_name": "value"}
        """
        pass

    @abstractmethod
    def append_existing_data(self, existing_data):
        pass

    @staticmethod
    def get_schema():
        """
        Returns a template for the optimizer configuration.
        """
        return {
            "parameter_types": ["range", "choice"],
            "multiple_objectives": True,
            # "objective_weights": True,
            "optimizer_config": {
                "step_1": {"model": [], "num_samples": 10},
                "step_2": {"model": []}
            },
        }



