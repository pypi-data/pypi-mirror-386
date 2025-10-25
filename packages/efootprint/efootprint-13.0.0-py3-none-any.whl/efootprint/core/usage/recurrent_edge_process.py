from typing import TYPE_CHECKING
import numpy as np

from pint import Quantity

from efootprint.abstract_modeling_classes.explainable_object_dict import ExplainableObjectDict
from efootprint.abstract_modeling_classes.explainable_recurrent_quantities import ExplainableRecurrentQuantities
from efootprint.abstract_modeling_classes.source_objects import SourceRecurrentValues
from efootprint.constants.units import u
from efootprint.core.hardware.edge_computer import EdgeComputer
from efootprint.core.usage.recurrent_edge_resource_needed import RecurrentEdgeResourceNeed

if TYPE_CHECKING:
    from efootprint.core.usage.edge_usage_pattern import EdgeUsagePattern


class RecurrentEdgeProcess(RecurrentEdgeResourceNeed):
    default_values = {
        "recurrent_compute_needed": SourceRecurrentValues(Quantity(np.array([1] * 168, dtype=np.float32), u.cpu_core)),
        "recurrent_ram_needed": SourceRecurrentValues(Quantity(np.array([1] * 168, dtype=np.float32), u.GB_ram)),
        "recurrent_storage_needed": SourceRecurrentValues(Quantity(np.array([0] * 168, dtype=np.float32), u.GB)),
    }

    def __init__(self, name: str, edge_device: EdgeComputer,
                 recurrent_compute_needed: ExplainableRecurrentQuantities,
                 recurrent_ram_needed: ExplainableRecurrentQuantities,
                 recurrent_storage_needed: ExplainableRecurrentQuantities):
        super().__init__(name, edge_device)
        self.unitary_hourly_compute_need_per_usage_pattern = ExplainableObjectDict()
        self.unitary_hourly_ram_need_per_usage_pattern = ExplainableObjectDict()
        self.unitary_hourly_storage_need_per_usage_pattern = ExplainableObjectDict()
        
        self.recurrent_compute_needed = recurrent_compute_needed.set_label(f"{self.name} recurrent compute needed")
        self.recurrent_ram_needed = recurrent_ram_needed.set_label(f"{self.name} recurrent ram needed").to(u.GB_ram)
        self.recurrent_storage_needed = recurrent_storage_needed.set_label(f"{self.name} recurrent storage needed")

    @property
    def calculated_attributes(self):
        return ["unitary_hourly_compute_need_per_usage_pattern", "unitary_hourly_ram_need_per_usage_pattern",
                "unitary_hourly_storage_need_per_usage_pattern"]

    def update_dict_element_in_unitary_hourly_compute_need_per_usage_pattern(self, usage_pattern: "EdgeUsagePattern"):
        unitary_hourly_compute_need = self.recurrent_compute_needed.generate_hourly_quantities_over_timespan(
            usage_pattern.nb_edge_usage_journeys_in_parallel, usage_pattern.country.timezone)
        self.unitary_hourly_compute_need_per_usage_pattern[usage_pattern] = unitary_hourly_compute_need.set_label(
            f"{self.name} unitary hourly compute need for {usage_pattern.name}")

    def update_unitary_hourly_compute_need_per_usage_pattern(self):
        self.unitary_hourly_compute_need_per_usage_pattern = ExplainableObjectDict()
        for usage_pattern in self.edge_usage_patterns:
            self.update_dict_element_in_unitary_hourly_compute_need_per_usage_pattern(usage_pattern)

    def update_dict_element_in_unitary_hourly_ram_need_per_usage_pattern(self, usage_pattern: "EdgeUsagePattern"):
        unitary_hourly_ram_need = self.recurrent_ram_needed.generate_hourly_quantities_over_timespan(
            usage_pattern.nb_edge_usage_journeys_in_parallel, usage_pattern.country.timezone)
        self.unitary_hourly_ram_need_per_usage_pattern[usage_pattern] = unitary_hourly_ram_need.set_label(
            f"{self.name} unitary hourly ram need for {usage_pattern.name}")

    def update_unitary_hourly_ram_need_per_usage_pattern(self):
        self.unitary_hourly_ram_need_per_usage_pattern = ExplainableObjectDict()
        for usage_pattern in self.edge_usage_patterns:
            self.update_dict_element_in_unitary_hourly_ram_need_per_usage_pattern(usage_pattern)

    def update_dict_element_in_unitary_hourly_storage_need_per_usage_pattern(self, usage_pattern: "EdgeUsagePattern"):
        unitary_hourly_storage_need = self.recurrent_storage_needed.generate_hourly_quantities_over_timespan(
            usage_pattern.nb_edge_usage_journeys_in_parallel, usage_pattern.country.timezone)
        # if usage_pattern.nb_edge_usage_journey_in_parallel.start_date doesn’t start on a Monday 00:00,
        # set the first values of the storage need to 0 until the first Monday 00:00, so that if storage need increases
        # during beginning of the week then decreases at the end of the week, it doesn’t go negative
        start_date_weekday = usage_pattern.nb_edge_usage_journeys_in_parallel.start_date.weekday()
        start_date_hour = usage_pattern.nb_edge_usage_journeys_in_parallel.start_date.hour
        if start_date_weekday != 0 or start_date_hour != 0:
            hours_until_first_monday_00 = (7 - start_date_weekday) * 24 - start_date_hour
            unitary_hourly_storage_need.magnitude[:hours_until_first_monday_00] = 0
        self.unitary_hourly_storage_need_per_usage_pattern[usage_pattern] = unitary_hourly_storage_need.set_label(
            f"{self.name} unitary hourly storage need for {usage_pattern.name}")

    def update_unitary_hourly_storage_need_per_usage_pattern(self):
        self.unitary_hourly_storage_need_per_usage_pattern = ExplainableObjectDict()
        for usage_pattern in self.edge_usage_patterns:
            self.update_dict_element_in_unitary_hourly_storage_need_per_usage_pattern(usage_pattern)
