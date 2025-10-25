from typing import List, Dict

import matplotlib.pyplot as plt
import numpy as np

from efootprint.abstract_modeling_classes.empty_explainable_object import EmptyExplainableObject
from efootprint.constants.units import u
from efootprint.abstract_modeling_classes.explainable_quantity import ExplainableQuantity


class EmissionPlotter:
    def __init__(self, ax, formatted_input_dicts__old: List[Dict[str, ExplainableQuantity]],
                 formatted_input_dicts__new: List[Dict[str, ExplainableQuantity]], rounding_value: int,
                 legend_labels: List[str] = ("Electricity consumption", "Fabrication")):
        self.ax = ax
        self.formatted_input_dicts__old = formatted_input_dicts__old
        self.formatted_input_dicts__new = formatted_input_dicts__new
        self.rounding_value = rounding_value
        self.legend_labels = legend_labels
        all_elements = ["Servers", "Storage", "Network", "Devices", "EdgeComputers", "EdgeStorage"]
        elements = []
        for elt in all_elements:
            for dict in formatted_input_dicts__old + formatted_input_dicts__new:
                if elt in dict and dict[elt] != EmptyExplainableObject() and elt not in elements:
                    elements.append(elt)
        self.elements = elements
        self.index = np.arange(len(self.elements))
        self.bar_width = 0.4
        self.total_emissions_in_kg__new = self.calculate_total_emissions(formatted_input_dicts__new)
        self.total_emissions_in_kg__old = self.calculate_total_emissions(formatted_input_dicts__old)
        self.colors = ["#6372f2", "#de5f46"]
        if self.total_emissions_in_kg__new < 501:
            self.unit = "kg"
            self.dividing_number = 1
        else:
            self.unit = "tonne"
            self.dividing_number = 1000


    @staticmethod
    def calculate_total_emissions(formatted_input_dicts):
        total_emissions_in_kg = 0
        for input_dict in formatted_input_dicts:
            total_emissions_in_kg += sum(input_dict.values()).to(u.kg).magnitude
        return total_emissions_in_kg

    def get_values(self, input_dict):
        return [(input_dict.get(element, 0 * u(self.unit))).to(u(self.unit)).magnitude
                for element in self.elements]

    def plot_common_values(self, common_values, i, color):
        return self.ax.bar(self.index + i * self.bar_width, common_values, self.bar_width, color=color, alpha=1.0)

    def plot_difference_values(self, diff_values, common_values, i, color):
        return self.ax.bar(
            self.index + i * self.bar_width, diff_values, self.bar_width, bottom=common_values, color=color, alpha=0.1)

    def plot_positive_diff(self, positive_diffs, common_values, i, color):
        return self.ax.bar(
            self.index + i * self.bar_width, positive_diffs, self.bar_width, bottom=common_values, color=color,
            alpha=0.7)

    def add_annotations_and_text(self, rects_common, diffs, values_old, values_new):
        arrowprops = dict(facecolor='black', shrink=0.05, width=2, headwidth=8)

        figure_height = self.ax.get_ylim()[1]
        for rect, diff, value_old, value_new in zip(rects_common, diffs, values_old, values_new):
            if value_old != value_new:
                if diff < -1:
                    if abs(value_old - value_new) > figure_height / 10:
                        self.ax.annotate(
                            "", xy=(rect.get_x() + rect.get_width() / 2 - 0.06,
                                    min(value_old, value_new) + figure_height / 20),
                            xytext=(rect.get_x() + rect.get_width() / 2 - 0.06, max(value_old, value_new)),
                            arrowprops=arrowprops)
                    self.ax.text(
                        rect.get_x() + rect.get_width() / 2 + 0.06, (value_old + value_new) / 2, f"{diff:.0f}%",
                        ha="center", va="center")
                elif diff > 1:
                    if abs(value_old - value_new) > figure_height / 10:
                        self.ax.annotate(
                            "", xy=(rect.get_x() + rect.get_width() / 2 - 0.06, max(value_old, value_new)),
                            xytext=(rect.get_x() + rect.get_width() / 2 - 0.06, min(value_old, value_new)),
                            arrowprops=arrowprops)
                    self.ax.text(
                        rect.get_x() + rect.get_width() / 2 + 0.06, (value_old + value_new) / 2, f"+{diff:.0f}%",
                        ha="center", va="center")

            proportion = (value_new / (self.total_emissions_in_kg__new / self.dividing_number)) * 100
            self.ax.text(rect.get_x() + rect.get_width() / 2, value_new, f"{proportion:.0f}%", ha="center", va="bottom")

    def set_axes_labels(self):
        self.ax.set_xlabel("Category")
        self.ax.set_ylabel(f"{self.unit}s CO2 emissions".replace("1 ", ""))

        self.ax.set_xticks(self.index + self.bar_width / 2)
        self.ax.set_xticklabels(self.elements, rotation=0, ha="center")

        ax2 = self.ax.twinx()
        max_value = max(
            [max(input_dict.values())
             for input_dict in self.formatted_input_dicts__new + self.formatted_input_dicts__old]
        ).to(u(self.unit)).magnitude

        max_value_margin = 1.1
        ax2.set_ylim(0, 100 * max_value_margin * (max_value / (self.total_emissions_in_kg__new / self.dividing_number)))
        ax2.set_ylabel("Proportions (%)")

        self.ax.set_ylim(0, max_value_margin * max_value)

    def set_titles(self):
        rounded_total__new = round(self.total_emissions_in_kg__new / self.dividing_number, self.rounding_value)
        if self.rounding_value == 0:
            rounded_total__new = int(rounded_total__new)

        rounded_total__old = round(self.total_emissions_in_kg__old / self.dividing_number, self.rounding_value)
        if self.rounding_value == 0:
            rounded_total__old = int(rounded_total__old)

        if rounded_total__old != rounded_total__new:
            plus_sign = ""
            if rounded_total__new - rounded_total__old > 0:
                plus_sign = "+"
            subtitle_text = f"From {rounded_total__old} to {rounded_total__new} {self.unit}s of CO2 emissions " \
                            f"({plus_sign}{int(100 * (rounded_total__new - rounded_total__old) / rounded_total__old)}%)"
        else:
            subtitle_text = f"{rounded_total__new} {self.unit}s of CO2 emissions"

        self.ax.text(
            0.5, 1.1, subtitle_text,
            transform=self.ax.transAxes, fontsize=16, va="top", ha="center")

    def plot_emission_diffs(self):
        for i, (input_dict_old, input_dict_new) in enumerate(
                zip(self.formatted_input_dicts__old, self.formatted_input_dicts__new)):
            values_old = self.get_values(input_dict_old)
            values_new = self.get_values(input_dict_new)

            diffs = [(new - old) / old * 100 if old != 0 else 0 for old, new in zip(values_old, values_new)]
            common_values = [min(old, new) for old, new in zip(values_old, values_new)]
            diff_values = [abs(new - old) for old, new in zip(values_old, values_new)]

            rects_common = self.plot_common_values(common_values, i, self.colors[i])
            self.plot_difference_values(diff_values, common_values, i, self.colors[i])
            self.plot_positive_diff(
                [max(new - old, 0) for old, new in zip(values_old, values_new)], common_values, i, self.colors[i])

            self.add_annotations_and_text(rects_common, diffs, values_old, values_new)
            self.set_axes_labels()
            self.add_legend()
            self.set_titles()

    def add_legend(self):
        handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in self.colors]
        self.ax.legend(handles, self.legend_labels)
