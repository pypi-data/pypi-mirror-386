from abc import abstractmethod
from typing import List

from efootprint.abstract_modeling_classes.empty_explainable_object import EmptyExplainableObject
from efootprint.abstract_modeling_classes.explainable_quantity import ExplainableQuantity
from efootprint.abstract_modeling_classes.modeling_object import ModelingObject


class HardwareBase(ModelingObject):
    # Mark the class as abstract but not its children when they define a default_values class attribute
    @classmethod
    @abstractmethod
    def default_values(cls):
        pass

    def __init__(self, name: str, carbon_footprint_fabrication: ExplainableQuantity, power: ExplainableQuantity,
                 lifespan: ExplainableQuantity, fraction_of_usage_time: ExplainableQuantity):
        super().__init__(name)
        self.carbon_footprint_fabrication = carbon_footprint_fabrication.set_label(
            f"Carbon footprint fabrication of {self.name}")
        self.power = power.set_label(f"Power of {self.name}")
        self.lifespan = lifespan.set_label(f"Lifespan of {self.name}")
        self.fraction_of_usage_time = fraction_of_usage_time.set_label(f"{self.name} fraction of usage time")

    @property
    def modeling_objects_whose_attributes_depend_directly_on_me(self) -> List[ModelingObject]:
        return self.modeling_obj_containers


class InsufficientCapacityError(Exception):
    def __init__(
            self, overloaded_object: HardwareBase, capacity_type: str,
            available_capacity: ExplainableQuantity|EmptyExplainableObject,
            requested_capacity: ExplainableQuantity|EmptyExplainableObject):
        self.overloaded_object = overloaded_object
        self.capacity_type = capacity_type
        self.available_capacity = available_capacity
        self.requested_capacity = requested_capacity

        message = (f"{self.overloaded_object.name} has available {capacity_type} capacity of "
                   f"{available_capacity.value} but is asked for {requested_capacity.value}")
        super().__init__(message)
