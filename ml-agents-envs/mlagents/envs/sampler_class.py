import numpy as np
from functools import *
from abc import ABC, abstractmethod

from .exception import SamplerException

class Sampler(ABC): 

    @abstractmethod
    def sample_parameter(self, *args, **kwargs):
        pass


class UniformSampler(Sampler):
    # kwargs acts as a sink for extra unneeded args
    def __init__(self, min_value, max_value, **kwargs):
        self.min_value = min_value
        self.max_value = max_value

    def sample_parameter(self):
        return np.random.uniform(self.min_value, self.max_value)
    

class MultiRangeUniformSampler(Sampler):
    def __init__(self, intervals, **kwargs):
        self.intervals = intervals
        # Measure the length of the intervals
        self.interval_lengths = list(map(lambda x: abs(x[1] - x[0]), self.intervals))
        # Cumulative size of the intervals
        self.cum_interval_length = reduce(lambda x,y: x + y, self.interval_lengths, 0)
        # Assign weights to an interval proportionate to the interval size
        self.interval_weights = list(map(lambda x: x/self.cum_interval_length, self.interval_lengths))
    
    
    def sample_parameter(self):
        cur_min, cur_max = self.intervals[np.random.choice(len(self.intervals), p=self.interval_weights)]
        return np.random.uniform(cur_min, cur_max)


class GaussianSampler(Sampler):
    def __init__(self, mean, var, **kwargs):
        self.mean = mean
        self.var = var
    
    def sample_parameter(self):
        return np.random.normal(self.mean, self.var)


# To introduce new sampling methods, just need to 'register' them to this sampler factory
class SamplerFactory:
    NAME_TO_CLASS = {
    "uniform": UniformSampler,
    "gaussian": GaussianSampler,
    "multirange_uniform": MultiRangeUniformSampler,
    }

    @staticmethod
    def register_sampler(name, sampler_cls):
        SamplerFactory.NAME_TO_CLASS[name] = sampler_cls
    
    @staticmethod
    def init_sampler_class(name, param_dict):
        if name not in SamplerFactory.NAME_TO_CLASS:
            raise SamplerException(
                name + " sampler is not registered in the SamplerFactory."
                " Use the register_sample method to register the string"
                " associated to your sampler in the SamplerFactory."
            )
        sampler_cls = SamplerFactory.NAME_TO_CLASS[name]
        return sampler_cls(**param_dict)


class SamplerManager:
    def __init__(self, reset_param_dict):
        self.reset_param_dict = reset_param_dict
        self.samplers = {}
        if reset_param_dict == None:
            return
        for param_name, cur_param_dict in self.reset_param_dict.items():
            if "sampler-type" not in cur_param_dict:
                raise SamplerException(
                    "'sampler_type' argument hasn't been supplied for the {0} parameter".format(param_name)
                )
            sampler_name = cur_param_dict.pop("sampler-type")
            param_sampler = SamplerFactory.init_sampler_class(sampler_name, cur_param_dict)

            self.samplers[param_name] = param_sampler

    def sample_all(self):
        res = {}
        if self.samplers == {}:
            pass
        else:
            for param_name, param_sampler in list(self.samplers.items()):
                res[param_name] = param_sampler.sample_parameter()
        return res
