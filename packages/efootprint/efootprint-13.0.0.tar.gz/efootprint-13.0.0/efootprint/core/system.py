from datetime import timedelta
from typing import Dict, List, Optional

from efootprint.abstract_modeling_classes.explainable_object_dict import ExplainableObjectDict
from efootprint.abstract_modeling_classes.modeling_object import ModelingObject
from efootprint.constants.units import u
from efootprint.core.hardware.edge_computer import EdgeComputer
from efootprint.core.hardware.edge_device_base import EdgeDeviceBase
from efootprint.core.hardware.edge_storage import EdgeStorage
from efootprint.core.hardware.network import Network
from efootprint.core.hardware.server import Server
from efootprint.core.hardware.storage import Storage
from efootprint.core.usage.edge_usage_journey import EdgeUsageJourney
from efootprint.core.usage.edge_usage_pattern import EdgeUsagePattern
from efootprint.core.usage.usage_pattern import UsagePattern
from efootprint.core.usage.usage_journey import UsageJourney
from efootprint.abstract_modeling_classes.explainable_hourly_quantities import ExplainableHourlyQuantities
from efootprint.abstract_modeling_classes.explainable_quantity import ExplainableQuantity
from efootprint.abstract_modeling_classes.empty_explainable_object import EmptyExplainableObject
from efootprint.logger import logger
from efootprint.utils.tools import format_co2_amount, display_co2_amount


class System(ModelingObject):
    def __init__(self, name: str, usage_patterns: List[UsagePattern], edge_usage_patterns: List[EdgeUsagePattern],):
        super().__init__(name)
        self.total_footprint = EmptyExplainableObject()
        self.usage_patterns = usage_patterns
        self.edge_usage_patterns = edge_usage_patterns
        self.check_no_object_to_link_is_already_linked_to_another_system()
        self.simulation = None
        self.set_initial_and_previous_footprints()

    def set_initial_and_previous_footprints(self):
        self.previous_change = None
        self.previous_total_energy_footprints_sum_over_period = ExplainableObjectDict()
        self.previous_total_fabrication_footprints_sum_over_period = ExplainableObjectDict()
        self.all_changes = []
        self.initial_total_energy_footprints_sum_over_period = ExplainableObjectDict()
        self.initial_total_fabrication_footprints_sum_over_period = ExplainableObjectDict()

    def compute_calculated_attributes(self):
        self.check_no_object_to_link_is_already_linked_to_another_system()
        super().compute_calculated_attributes()

    @property
    def calculated_attributes(self) -> List[str]:
        return ["total_footprint"]

    @property
    def attributes_that_shouldnt_trigger_update_logic(self):
        return (super().attributes_that_shouldnt_trigger_update_logic
                + ["all_changes", "previous_change", "previous_total_energy_footprints_sum_over_period",
                   "previous_total_fabrication_footprints_sum_over_period",
                   "initial_total_energy_footprints_sum_over_period",
                   "initial_total_fabrication_footprints_sum_over_period", "simulation"])

    def check_no_object_to_link_is_already_linked_to_another_system(self):
        for mod_obj in self.all_linked_objects:
            mod_obj_systems = mod_obj.systems
            if mod_obj_systems and mod_obj_systems[0].id != self.id:
                raise PermissionError(f"{mod_obj.name} is already linked to {mod_obj_systems[0].name}, so it is "
                                      f"impossible to link it to {self.name}")
            if len(mod_obj_systems) > 1:
                raise ValueError(f"{mod_obj.name} is linked to 2 systems, this should never happen, please report an"
                                 f" e-footprint bug at https://github.com/Boavizta/e-footprint/issues")

    @property
    def modeling_objects_whose_attributes_depend_directly_on_me(self):
        return self.usage_patterns + self.edge_usage_patterns

    @property
    def systems(self) -> List:
        return [self]

    def after_init(self):
        from time import time
        start = time()
        logger.info(f"Starting computing {self.name} modeling")
        mod_obj_computation_chain_excluding_self = self.mod_objs_computation_chain[1:]
        self.launch_mod_objs_computation_chain(mod_obj_computation_chain_excluding_self)
        self.compute_calculated_attributes()
        all_objects = self.all_linked_objects
        nb_of_calculated_attributes = sum([len(obj.calculated_attributes) for obj in all_objects])
        if nb_of_calculated_attributes > 0:
            compute_duration = round((time() - start), 3)
            logger.info(
                f"Computed {nb_of_calculated_attributes} calculated attributes over {len(all_objects)} objects in "
                f"{compute_duration} seconds or {round(1000 * compute_duration / nb_of_calculated_attributes, 2)} "
                f"ms per computation")
        self.initial_total_energy_footprints_sum_over_period = self.total_energy_footprint_sum_over_period
        self.initial_total_fabrication_footprints_sum_over_period = self.total_fabrication_footprint_sum_over_period
        self.trigger_modeling_updates = True

    def get_objects_linked_to_usage_patterns(
            self, usage_patterns: List[UsagePattern]) -> List[ModelingObject]:
        output_list =  self.storages + usage_patterns + self.networks
        usage_journeys = self.usage_journeys
        uj_steps = list(set(sum([uj.uj_steps for uj in usage_journeys], start=[])))
        jobs = list(set(sum([uj_step.jobs for uj_step in uj_steps], start=[])))
        devices = list(set(sum([up.devices for up in usage_patterns], start=[])))
        countries = list(set([up.country for up in usage_patterns]))
        servers = self.servers
        services = list(set(sum([server.installed_services for server in servers], start=[])))
        all_modeling_objects = output_list + usage_journeys + uj_steps + jobs + devices + countries + servers + services

        return all_modeling_objects

    def get_objects_linked_to_edge_usage_patterns(
            self, edge_usage_patterns: List[EdgeUsagePattern]) -> List[ModelingObject]:
        output_list = self.edge_storages + edge_usage_patterns
        edge_usage_journeys = self.edge_usage_journeys
        edge_functions = list(set(sum([euj.edge_functions for euj in edge_usage_journeys], start=[])))
        recurrent_edge_resource_needs = list(
            set(sum([ef.recurrent_edge_resource_needs for ef in edge_functions], start=[])))
        edge_devices = self.edge_devices
        countries = list(set([up.country for up in edge_usage_patterns]))
        all_modeling_objects = (output_list + edge_usage_journeys + edge_functions + recurrent_edge_resource_needs
                                + edge_devices + countries)

        return all_modeling_objects

    @property
    def all_linked_objects(self):
        return (self.get_objects_linked_to_usage_patterns(self.usage_patterns)
                + self.get_objects_linked_to_edge_usage_patterns(self.edge_usage_patterns))

    @property
    def usage_journeys(self) -> List[UsageJourney]:
        return list(set([up.usage_journey for up in self.usage_patterns]))

    @property
    def edge_usage_journeys(self) -> List[EdgeUsageJourney]:
        return list(set([eup.edge_usage_journey for eup in self.edge_usage_patterns]))

    @property
    def servers(self) -> List[Server]:
        return list(set(sum([usage_pattern.usage_journey.servers for usage_pattern in self.usage_patterns], start=[])))

    @property
    def edge_devices(self) -> List[EdgeDeviceBase]:
        return list(set(sum([euj.edge_devices for euj in self.edge_usage_journeys], start=[])))

    @property
    def edge_computers(self) -> List[EdgeComputer]:
        return [hw for hw in self.edge_devices if isinstance(hw, EdgeComputer)]

    @property
    def storages(self) -> List[Storage]:
        return list(set(sum([usage_pattern.usage_journey.storages for usage_pattern in self.usage_patterns], start=[])))

    @property
    def edge_storages(self) -> List[EdgeStorage]:
        return list(set([edge_computer.storage for edge_computer in self.edge_computers]))

    @property
    def networks(self) -> List[Network]:
        return list(set([up.network for up in self.usage_patterns]))

    @staticmethod
    def get_efootprint_obj_by_name(
            efootprint_obj_name: str, efootprint_obj_list: List[ModelingObject]) -> Optional[ModelingObject]:
        for efootprint_obj in efootprint_obj_list:
            if efootprint_obj.name == efootprint_obj_name:
                return efootprint_obj
        return None

    @property
    def fabrication_footprints(self) -> Dict[str, Dict[str, ExplainableHourlyQuantities]]:
        fab_footprints = {
            "Servers": {server: server.instances_fabrication_footprint for server in self.servers},
            "Storage": {storage: storage.instances_fabrication_footprint for storage in self.storages},
            "Network": {},
            "Devices": {usage_pattern: usage_pattern.instances_fabrication_footprint
                        for usage_pattern in self.usage_patterns},
            "EdgeDevices": {edge_device: edge_device.instances_fabrication_footprint
                            for edge_device in self.edge_devices},
            "EdgeStorage": {edge_storage: edge_storage.instances_fabrication_footprint
                             for edge_storage in self.edge_storages},
        }

        return fab_footprints

    @property
    def energy_footprints(self) -> Dict[str, Dict[str, ExplainableHourlyQuantities]]:
        energy_footprints = {
            "Servers": {server: server.energy_footprint for server in self.servers},
            "Storage": {storage: storage.energy_footprint for storage in self.storages},
            "Network": {network: network.energy_footprint for network in self.networks},
            "Devices": {usage_pattern: usage_pattern.energy_footprint
                        for usage_pattern in self.usage_patterns},
            "EdgeDevices": {edge_device: edge_device.energy_footprint
                            for edge_device in self.edge_devices},
            "EdgeStorage": {edge_storage: edge_storage.energy_footprint for edge_storage in self.edge_storages},
        }

        return energy_footprints

    @property
    def total_fabrication_footprints(self) -> Dict[str, ExplainableHourlyQuantities]:
        fab_footprints = {
            "Servers": sum([server.instances_fabrication_footprint for server in self.servers],
                           start=EmptyExplainableObject()).to(u.kg).set_label(
                "Servers total fabrication footprint"),
            "Storage": sum([storage.instances_fabrication_footprint for storage in self.storages],
                           start=EmptyExplainableObject()).to(u.kg).set_label(
                "Storage total fabrication footprint"),
            "Network": EmptyExplainableObject(),
            "Devices": sum([usage_pattern.instances_fabrication_footprint
                           for usage_pattern in self.usage_patterns], start=EmptyExplainableObject()).to(u.kg).set_label(
                "Devices total fabrication footprint"),
            "EdgeDevices": sum([edge_device.instances_fabrication_footprint for edge_device in self.edge_devices],
                               start=EmptyExplainableObject()).to(u.kg).set_label(
                "Edge devices total fabrication footprint"),
            "EdgeStorage": sum([edge_storage.instances_fabrication_footprint for edge_storage in self.edge_storages],
                                start=EmptyExplainableObject()).to(u.kg).set_label(
                "Edge storage total fabrication footprint")
        }

        return fab_footprints

    @property
    def total_energy_footprints(self) -> Dict[str, ExplainableHourlyQuantities]:
        energy_footprints = {
            "Servers": sum([server.energy_footprint for server in self.servers], start=EmptyExplainableObject()
                           ).to(u.kg).set_label("Servers total energy footprint"),
            "Storage": sum([storage.energy_footprint for storage in self.storages], start=EmptyExplainableObject()
                           ).to(u.kg).set_label("Storage total energy footprint"),
            "Network": sum([network.energy_footprint for network in self.networks], start=EmptyExplainableObject()
                           ).to(u.kg).set_label("Network total energy footprint"),
            "Devices": sum([usage_pattern.energy_footprint for usage_pattern in self.usage_patterns],
                           start=EmptyExplainableObject()).to(u.kg).set_label("Devices total energy footprint"),
            "EdgeDevices": sum([edge_device.energy_footprint for edge_device in self.edge_devices],
                               start=EmptyExplainableObject()).to(u.kg).set_label("Edge devices total energy footprint"),
            "EdgeStorage": sum([edge_storage.energy_footprint for edge_storage in self.edge_storages],
                               start=EmptyExplainableObject()).to(u.kg).set_label("Edge storage total energy footprint")
        }

        return energy_footprints

    @staticmethod
    def sum_and_remove_empty_explainable_object(expl_obj):
        tmp_sum = expl_obj.sum()
        if isinstance(tmp_sum, EmptyExplainableObject):
            tmp_sum = ExplainableQuantity(0 * u.kg, "null value")

        return tmp_sum

    @property
    def fabrication_footprint_sum_over_period(self) -> Dict[str, Dict[ModelingObject, ExplainableQuantity]]:
        fab_footprints_sum = {}
        for category_key, category_dict in self.fabrication_footprints.items():
            fab_footprints_sum[category_key] = {
                obj_key: self.sum_and_remove_empty_explainable_object(obj_value).to(u.kg).set_label(
                    f"{obj_key} fabrication footprints summed over modeling period")
                for obj_key, obj_value in category_dict.items()
            }

        return fab_footprints_sum

    @property
    def energy_footprint_sum_over_period(self) -> Dict[str, Dict[ModelingObject, ExplainableQuantity]]:
        energy_footprints_sum = {}
        for key, dict_value in self.energy_footprints.items():
            energy_footprints_sum[key] = {
                obj_key: self.sum_and_remove_empty_explainable_object(obj_value).to(u.kg).set_label(
                    f"{obj_key} energy footprints summed over modeling period")
                for obj_key, obj_value in dict_value.items()
            }

        return energy_footprints_sum

    @property
    def total_fabrication_footprint_sum_over_period(self) -> Dict[str, ExplainableQuantity]:
        fab_footprints = {
            object_category: self.sum_and_remove_empty_explainable_object(category_value).to(u.kg).set_label(
                f"{object_category} total fabrication footprints summed over modeling period")
            for object_category, category_value in self.total_fabrication_footprints.items()
        }

        return ExplainableObjectDict(fab_footprints)

    @property
    def total_energy_footprint_sum_over_period(self) -> Dict[str, ExplainableQuantity]:
        energy_footprints = {
            object_category: self.sum_and_remove_empty_explainable_object(category_value).to(u.kg).set_label(
                f"{object_category} total energy footprints summed over modeling period")
            for object_category, category_value in self.total_energy_footprints.items()
        }

        return ExplainableObjectDict(energy_footprints)

    def update_total_footprint(self):
        total_footprint = (
            sum(
                [sum(self.fabrication_footprints[key].values()) + sum(self.energy_footprints[key].values())
                for key in self.fabrication_footprints], start=EmptyExplainableObject()
            )
        ).to(u.kg).set_label(f"{self.name} total carbon footprint")

        self.total_footprint = round(total_footprint, 4)

    def plot_footprints_by_category_and_object(self, filename=None, height=400, width=800, notebook=True):
        import plotly.express as px
        import plotly

        fab_footprints = self.fabrication_footprint_sum_over_period
        energy_footprints = self.energy_footprint_sum_over_period

        rows_as_dicts = []
        value_colname = "tonnes CO2 emissions"

        for category in fab_footprints:
            fab_objects = sorted(fab_footprints[category].items(), key=lambda x: x[0].name)
            energy_objects = sorted(energy_footprints[category].items(), key=lambda x: x[0].name)

            for objs, color in zip([energy_objects, fab_objects], ["Electricity", "Fabrication"]):
                for object, quantity in objs:
                    magnitude_kg = quantity.magnitude
                    magnitude_tonnes = magnitude_kg / 1000
                    amount_str = display_co2_amount(format_co2_amount(magnitude_kg))

                    rows_as_dicts.append({
                        "Type": color, "Category": category, "Object": object.name, value_colname: magnitude_tonnes,
                        "Amount": amount_str})

        import pandas as pd
        df = pd.DataFrame.from_records(rows_as_dicts)

        total_co2 = df[value_colname].sum()
        total_footprint = self.total_footprint

        start_date = total_footprint.start_date
        end_date = start_date + timedelta(hours=len(total_footprint.value) - 1)

        fig = px.bar(
            df, x="Category", y=value_colname, color='Type', barmode='group',
            height=height, width=width,
            hover_data={"Type": False, "Category": False, "Object": True, value_colname: False, "Amount": True},
            template="plotly_white",
            title=f"Total CO2 emissions from {start_date.date()} to {end_date.date()}: "
                  f"{display_co2_amount(format_co2_amount(total_co2 * 1000, rounding_value=0))}"
        )

        # Legend placement logic
        total_energy_servers = sum(energy_footprints["Servers"].values(), start=0)
        total_fab_servers = sum(fab_footprints["Servers"].values(), start=0)
        total_energy_devices = sum(energy_footprints["Devices"].values(), start=0)
        total_fab_devices = sum(fab_footprints["Devices"].values(), start=0)

        if (total_energy_servers + total_fab_servers) > (total_energy_devices + total_fab_devices):
            legend_alignment = "right"
            legend_x = 0.98
        else:
            legend_alignment = "left"
            legend_x = 0.02

        fig.update_layout(
            legend={"orientation": "v", "yanchor": "top", "y": 1.02, "xanchor": legend_alignment, "x": legend_x,
                    "title": ""},
            title={"x": 0.5, "y": 0.9, "xanchor": 'center', "yanchor": 'top'}
        )

        # Add annotations (percentages per category and type)
        total_by_cat_type = df.groupby(["Category", "Type"])[value_colname].sum()

        for (category, source_type), height_val in total_by_cat_type.items():
            x_shift = 30 if source_type == 'Fabrication' else -30
            percentage = int((height_val / total_co2) * 100)

            fig.add_annotation(
                x=category, y=height_val,
                text=f"{percentage}%",
                showarrow=False,
                yshift=10,
                xshift=x_shift
            )

        if notebook:
            from IPython.display import HTML

            if filename is None:
                filename = f"{self.name} footprints.html"

            plotly.offline.plot(fig, filename=filename, auto_open=False)

            return HTML(filename)
        else:
            return fig

    def plot_emission_diffs(self, filepath=None, figsize=(10, 5), from_start=False, plt_show=False):
        from matplotlib import pyplot as plt

        if self.previous_change is None:
            raise ValueError(
                f"There has been no change to the system yet so no diff to plot.\n"
                f"Use System.plot_footprints_by_category_and_object() to visualize footprints")

        if from_start and len(self.all_changes) > 1:
            emissions_dict__old = [self.initial_total_energy_footprints_sum_over_period,
                                   self.initial_total_fabrication_footprints_sum_over_period]
        else:
            emissions_dict__old = [self.previous_total_energy_footprints_sum_over_period,
                                   self.previous_total_fabrication_footprints_sum_over_period]

        emissions_dict__new = [self.total_energy_footprint_sum_over_period,
                               self.total_fabrication_footprint_sum_over_period]

        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize)
        from efootprint.utils.plot_emission_diffs import EmissionPlotter
        EmissionPlotter(
            ax, emissions_dict__old, emissions_dict__new, rounding_value=0).plot_emission_diffs()

        if filepath is not None:
            plt.savefig(filepath, bbox_inches='tight')

        if plt_show:
            plt.show()

        return fig, ax
