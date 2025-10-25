from collections import deque
from copy import copy
from typing import Type, Optional, TYPE_CHECKING
from dataclasses import dataclass
import os

from efootprint.abstract_modeling_classes.object_linked_to_modeling_obj import ObjectLinkedToModelingObj
from efootprint.constants.units import u
from efootprint.logger import logger
from efootprint.utils.calculus_graph import build_calculus_graph
from efootprint.utils.graph_tools import add_unique_id_to_mynetwork

if TYPE_CHECKING:
    from efootprint.abstract_modeling_classes.modeling_object import ModelingObject


@dataclass
class Source:
    @classmethod
    def from_json_dict(cls, d):
        if "name" not in d:
            raise ValueError("Source JSON must contain 'name' field")
        return cls(name=d["name"], link=d.get("link", None))
    name: str
    link: Optional[str]


def retrieve_update_function_from_mod_obj_and_attr_name(mod_obj: "ModelingObject", attr_name: str):
    update_func_name = f"update_{attr_name}"
    update_func = getattr(mod_obj, update_func_name, None)

    if update_func is None:
        raise AttributeError(f"No update function associated to {attr_name} in {mod_obj.id}, please create it.")

    return update_func


def retrieve_dict_element_update_function_from_mod_obj_and_attr_name(
        mod_obj: "ModelingObject", attr_name: str, key_in_dict: "ModelingObject"):
    update_func_name = f"update_dict_element_in_{attr_name}"
    update_func = getattr(mod_obj, update_func_name, None)

    if update_func is None:
        raise AttributeError(
            f"No dict element update function associated to {attr_name} in {mod_obj.id}, please create it.")

    return update_func


def optimize_attr_updates_chain(attr_updates_chain):
    initial_chain_len = len(attr_updates_chain)
    attr_to_update_ids = [attr.id for attr in attr_updates_chain]
    optimized_chain = []

    for index in range(len(attr_updates_chain)):
        attr_to_update = attr_updates_chain[index]
        is_not_recomputed_later = attr_to_update.id not in attr_to_update_ids[index + 1:]
        doesnt_belong_to_dict = attr_to_update.dict_container is None
        belongs_to_dict_and_dict_is_not_recomputed_later = (
            attr_to_update.dict_container is not None and
            attr_to_update.dict_container.id not in attr_to_update_ids[index + 1:]
        )

        if is_not_recomputed_later and (doesnt_belong_to_dict or belongs_to_dict_and_dict_is_not_recomputed_later):
            # Keep only last occurrence of each attribute to update
            optimized_chain.append(attr_to_update)

    optimized_chain_len = len(optimized_chain)

    if optimized_chain_len != initial_chain_len:
        logger.info(f"Optimized update function chain from {initial_chain_len} to {optimized_chain_len} calculations")

    return optimized_chain


def get_attribute_from_flat_obj_dict(attr_key: str, flat_obj_dict: dict):
    modeling_obj_container_id, attr_name_in_mod_obj_container, key_in_dict = eval(attr_key)
    if key_in_dict:
        return getattr(flat_obj_dict[modeling_obj_container_id], attr_name_in_mod_obj_container)[
            flat_obj_dict[key_in_dict]]
    else:
        return getattr(flat_obj_dict[modeling_obj_container_id], attr_name_in_mod_obj_container)


class ExplainableObject(ObjectLinkedToModelingObj):
    _registry = []

    @classmethod
    def register_subclass(cls, matcher):
        def decorator(subclass):
            cls._registry.append((matcher, subclass))
            return subclass

        return decorator

    @classmethod
    def from_json_dict(cls, d):
        for matcher, subclass in cls._registry:
            if matcher(d):
                return subclass.from_json_dict(d)
        if "value" in d and isinstance(d["value"], str):
            source = Source.from_json_dict(d.get("source")) if d.get("source") else None
            return cls(d["value"], label=d.get("label", None), source=source)
        raise ValueError("No matching subclass found for data: {}".format(d))

    def initialize_calculus_graph_data_from_json(self, json_input: dict, flat_obj_dict: dict[str, "ModelingObject"]):
        if "direct_ancestors_with_id" in json_input:
            self._keys_of_direct_ancestors_with_id_loaded_from_json = json_input[
                "direct_ancestors_with_id"]
            self._keys_of_direct_children_with_id_loaded_from_json = json_input[
                "direct_children_with_id"]
            self.explain_nested_tuples_from_json = json_input["explain_nested_tuples"]
            self.flat_obj_dict = flat_obj_dict

    def __init__(
            self, value: object, label: str = None, left_parent: Type["ExplainableObject"] = None,
            right_parent: Type["ExplainableObject"] = None, operator: str = None, source: Source = None):
        super().__init__()
        self.simulation_twin = None
        self.baseline_twin = None
        self.simulation = None
        self.initial_modeling_obj_container = None
        self._value = value
        if not label and (left_parent is None and right_parent is None):
            raise ValueError(f"ExplainableObject without parent should have a label")
        self.source = source
        self.label = None
        self.set_label(label)
        self.left_parent = left_parent
        self.right_parent = right_parent
        self.operator = operator
        self._keys_of_direct_ancestors_with_id_loaded_from_json = None
        self._keys_of_direct_children_with_id_loaded_from_json = None
        self.flat_obj_dict = None
        self._direct_ancestors_with_id = []
        self._direct_children_with_id = []
        self.explain_nested_tuples_from_json = None
        self._explain_nested_tuples = None

        for parent in (self.left_parent, self.right_parent):
            if parent is not None:
                self.direct_ancestors_with_id += [
                    ancestor_with_id for ancestor_with_id in parent.return_direct_ancestors_with_id_to_child()
                    if ancestor_with_id.id not in self.direct_ancestor_ids]


    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    @value.deleter
    def value(self):
        self._value = None

    @property
    def explain_nested_tuples(self):
        if self._explain_nested_tuples is None and self.explain_nested_tuples_from_json is not None:
            def recursively_deserialize_explain_nested_tuple(explain_nested_tuple):
                if isinstance(explain_nested_tuple, list):
                    return (recursively_deserialize_explain_nested_tuple(explain_nested_tuple[0]),
                            explain_nested_tuple[1],
                            recursively_deserialize_explain_nested_tuple(explain_nested_tuple[2]))
                elif explain_nested_tuple is not None:
                    if isinstance(explain_nested_tuple, str):
                        return get_attribute_from_flat_obj_dict(explain_nested_tuple, self.flat_obj_dict)
                    elif isinstance(explain_nested_tuple, dict):
                        return ExplainableObject.from_json_dict(explain_nested_tuple)
                return None

            self._explain_nested_tuples = recursively_deserialize_explain_nested_tuple(
                self.explain_nested_tuples_from_json)

        return self._explain_nested_tuples

    @explain_nested_tuples.setter
    def explain_nested_tuples(self, new_explain_nested_tuples):
        self._explain_nested_tuples = new_explain_nested_tuples
        self.explain_nested_tuples_from_json = None

    @explain_nested_tuples.deleter
    def explain_nested_tuples(self):
        self._explain_nested_tuples = None
        self.explain_nested_tuples_from_json = None

    def load_ancestors_and_children_from_json(self):
        if (self._keys_of_direct_ancestors_with_id_loaded_from_json is not None
                and self._keys_of_direct_children_with_id_loaded_from_json is not None):
            self.direct_ancestors_with_id = [
                get_attribute_from_flat_obj_dict(direct_ancestor_key, self.flat_obj_dict) for direct_ancestor_key in
                self._keys_of_direct_ancestors_with_id_loaded_from_json
            ]
            self.direct_children_with_id = [
                get_attribute_from_flat_obj_dict(direct_child_key, self.flat_obj_dict) for direct_child_key in
                self._keys_of_direct_children_with_id_loaded_from_json
            ]

    @property
    def direct_ancestors_with_id(self):
        self.load_ancestors_and_children_from_json()

        return self._direct_ancestors_with_id

    @direct_ancestors_with_id.setter
    def direct_ancestors_with_id(self, value):
        self._direct_ancestors_with_id = value
        self._keys_of_direct_ancestors_with_id_loaded_from_json = None

    @property
    def direct_children_with_id(self):
        self.load_ancestors_and_children_from_json()

        return self._direct_children_with_id

    @direct_children_with_id.setter
    def direct_children_with_id(self, value):
        self._direct_children_with_id = value
        self._keys_of_direct_children_with_id_loaded_from_json = None

    def __copy__(self):
        cls = self.__class__
        new_instance = cls.__new__(cls)
        new_instance.__init__(
            value=copy(self.value), label=copy(self.label), source=copy(getattr(self, "source", None)))

        return new_instance

    def set_label(self, new_label):
        if self.source is not None and f"from {self.source.name}" not in new_label:
            self.label = f"{new_label} from {self.source.name}"
        else:
            self.label = new_label

        return self

    @property
    def has_parent(self):
        return self.left_parent is not None or self.right_parent is not None

    @property
    def direct_ancestor_ids(self):
        return [attr.id for attr in self.direct_ancestors_with_id]

    @property
    def direct_child_ids(self):
        return [attr.id for attr in self.direct_children_with_id]

    def replace_in_mod_obj_container_without_recomputation(self, new_value):
        value_to_set = new_value
        if isinstance(value_to_set, float) and self.dict_container is not None:
            from efootprint.abstract_modeling_classes.source_objects import SourceValue
            value_to_set = SourceValue(value_to_set * u.dimensionless)

        super().replace_in_mod_obj_container_without_recomputation(value_to_set)

    def set_modeling_obj_container(
            self, new_modeling_obj_container: Type["ModelingObject"] | None, attr_name: str | None):
        if not self.label:
            raise PermissionError(
                f"ExplainableObjects that are attributes of a ModelingObject should always have a label. "
                f"{self} doesn’t have one.")

        if self.modeling_obj_container is not None:
            for direct_ancestor_with_id in self.direct_ancestors_with_id:
                direct_ancestor_with_id.remove_child_from_direct_children_with_id(direct_child=self)
            for child in self.direct_children_with_id:
                # Rehydrate child calculus graph so that it now has live links to its ancestors
                child.load_ancestors_and_children_from_json()

        super().set_modeling_obj_container(new_modeling_obj_container, attr_name)

        if new_modeling_obj_container is not None:
            if self.initial_modeling_obj_container is None:
                self.initial_modeling_obj_container = new_modeling_obj_container
            for direct_ancestor_with_id in self.direct_ancestors_with_id:
                direct_ancestor_with_id.add_child_to_direct_children_with_id(direct_child=self)

            if self.left_parent is not None or self.right_parent is not None:
                self.explain_nested_tuples = self.compute_explain_nested_tuples()
                # Free up memory because left parent and right_parent aren’t needed anymore
                self.left_parent = None
                self.right_parent = None

    def return_direct_ancestors_with_id_to_child(self):
        if self.modeling_obj_container is not None:
            return [self]
        else:
            return [ancestor for ancestor in self.direct_ancestors_with_id
                    if ancestor.modeling_obj_container is not None]

    def add_child_to_direct_children_with_id(self, direct_child):
        if direct_child.id not in self.direct_child_ids:
            self.direct_children_with_id.append(direct_child)

    def remove_child_from_direct_children_with_id(self, direct_child):
        self.direct_children_with_id = [
            child for child in self.direct_children_with_id if child.id != direct_child.id]

    @property
    def all_descendants_with_id(self):
        all_descendants = []
        visited_ids = set()
        stack = [self]

        while stack:
            parent = stack.pop()
            for child in parent.direct_children_with_id:
                cid = child.id
                if cid not in visited_ids:
                    visited_ids.add(cid)
                    all_descendants.append(child)
                    stack.append(child)

        return all_descendants

    @property
    def all_ancestors_with_id(self):
        all_ancestors = []

        def retrieve_ancestors(expl_obj: ExplainableObject, ancestors_list):
            for parent in expl_obj.direct_ancestors_with_id:
                if parent.id not in [elt.id for elt in ancestors_list]:
                    ancestors_list.append(parent)
                retrieve_ancestors(parent, ancestors_list)

        retrieve_ancestors(self, all_ancestors)

        return all_ancestors

    @property
    def attr_updates_chain(self):
        attr_updates_chain = []
        descendants = self.all_descendants_with_id
        descendant_ids = {desc.id for desc in descendants if desc.id != self.id}
        has_been_added_to_chain_dict = {desc.id: False for desc in descendants if desc.id != self.id}

        # Use deque for efficient pops and removals
        parents_with_children_to_add = deque([self])

        # Precompute ancestor ids for each child
        ancestor_ids_map = {
            child.id: [ancestor.id for ancestor in child.direct_ancestors_with_id]
            for child in descendants
        }

        while parents_with_children_to_add:
            next_parents = deque()
            while parents_with_children_to_add:
                parent = parents_with_children_to_add.popleft()
                keep_for_next_iteration = False

                for child in parent.direct_children_with_id:
                    if not has_been_added_to_chain_dict[child.id]:
                        child_ancestor_ids = ancestor_ids_map.get(child.id, [])
                        all_child_ancestors_that_need_to_be_updated_are_already_in_chain = all(
                            has_been_added_to_chain_dict[ancestor_id] for ancestor_id in child_ancestor_ids if
                               ancestor_id in descendant_ids)
                        if all_child_ancestors_that_need_to_be_updated_are_already_in_chain:
                            attr_updates_chain.append(child)
                            has_been_added_to_chain_dict[child.id] = True

                            if child.direct_children_with_id:
                                next_parents.append(child)
                        else:
                            keep_for_next_iteration = True

                if keep_for_next_iteration:
                    next_parents.append(parent)

            parents_with_children_to_add = next_parents

        optimized_chain = optimize_attr_updates_chain(attr_updates_chain)
        return optimized_chain

    @property
    def update_function(self):
        if self.modeling_obj_container is None:
            raise ValueError(
                f"{self} doesn’t have a modeling_obj_container, hence it makes no sense "
                f"to look for its update function")
        dict_container = self.dict_container
        if dict_container is None:
            update_func = retrieve_update_function_from_mod_obj_and_attr_name(
                self.modeling_obj_container, self.attr_name_in_mod_obj_container)
        else:
            update_func = retrieve_dict_element_update_function_from_mod_obj_and_attr_name(
                self.modeling_obj_container, self.attr_name_in_mod_obj_container, self.key_in_dict)

        return update_func

    @property
    def update_function_chain(self):
        return [attribute.update_function for attribute in self.attr_updates_chain]
    
    def generate_explainable_object_with_logical_dependency(
            self, explainable_condition: Type["ExplainableObject"]):
        return self.__class__(value=self.value, label=self.label, left_parent=self, right_parent=explainable_condition,
                              operator="logically dependent on")

    def explain(self, pretty_print=True):
        element_value_to_print = str(self)

        if len(self.direct_ancestors_with_id) == 0:
            return f"{self.label} = {element_value_to_print}"

        flat_tuple_formula = self.compute_formula_as_flat_tuple(self.explain_nested_tuples)

        if pretty_print:
            return self.pretty_print_calculation(
                f"{self.label} = {self.print_flat_tuple_formula(flat_tuple_formula, print_values_instead_of_labels=False)}"
                f" = {self.print_flat_tuple_formula(flat_tuple_formula, print_values_instead_of_labels=True)}"
                f" = {element_value_to_print}")
        else:
            return f"{self.label} = {self.print_flat_tuple_formula(
                flat_tuple_formula, print_values_instead_of_labels=False)}" \
                f" = {self.print_flat_tuple_formula(flat_tuple_formula, print_values_instead_of_labels=True)}" \
                f" = {element_value_to_print}"

    def compute_explain_nested_tuples(self, return_self_if_self_has_mod_obj_container_or_no_ancestors=False):
        if (return_self_if_self_has_mod_obj_container_or_no_ancestors and
                (self.modeling_obj_container is not None or len(self.direct_ancestors_with_id) == 0)):
            return self

        left_explanation = None
        right_explanation = None

        if self.left_parent:
            left_explanation = self.left_parent.compute_explain_nested_tuples(
                return_self_if_self_has_mod_obj_container_or_no_ancestors=True)
        if self.right_parent:
            right_explanation = self.right_parent.compute_explain_nested_tuples(
                return_self_if_self_has_mod_obj_container_or_no_ancestors=True)

        if left_explanation is None and right_explanation is None:
            raise ValueError(f"{self} should have at least one parent to be explained")

        return left_explanation, self.operator, right_explanation

    def compute_formula_as_flat_tuple(self, tuple_element: object) -> tuple:
        if isinstance(tuple_element, ExplainableObject):
            return (tuple_element,)
        elif isinstance(tuple_element, str):
            return (tuple_element,)
        elif isinstance(tuple_element, tuple):
            a, op, b = tuple_element

            if op is None:
                return self.compute_formula_as_flat_tuple(a)

            # Handle unary ops like "X of (Y)"
            if b is None:
                if op is None or len(op) == 0:
                    return self.compute_formula_as_flat_tuple(a)
                return op, '(', *self.compute_formula_as_flat_tuple(a), ')'

            # Determine if we need parentheses
            left_parens = False
            right_parens = False

            if op == "/":
                if isinstance(b, tuple):
                    right_parens = True
                if isinstance(a, tuple) and a[1] != "*":
                    left_parens = True
            elif op == "*":
                if isinstance(a, tuple) and a[1] != "*":
                    left_parens = True
                if isinstance(b, tuple) and b[1] != "*":
                    right_parens = True
            elif op == "-":
                if isinstance(b, tuple) and b[1] in ["+", "-"]:
                    right_parens = True

            left = self.compute_formula_as_flat_tuple(a)
            right = self.compute_formula_as_flat_tuple(b)

            result = []
            if left_parens:
                result += ('(', *left, ')')
            else:
                result += left

            result += (op,)

            if right_parens:
                result += ('(', *right, ')')
            else:
                result += right

            return tuple(result)
        return ()

    @staticmethod
    def print_flat_tuple_formula(flat_formula_tuple: tuple, print_values_instead_of_labels: bool) -> str:
        result = ""

        for el in flat_formula_tuple:
            is_left_paren = el == "("
            is_right_paren = el == ")"
            is_explainable = isinstance(el, ExplainableObject)
            is_operator = not (is_left_paren or is_right_paren or is_explainable)

            if is_explainable:
                s = str(el) if print_values_instead_of_labels else el.label
            else:
                s = str(el)

            # Append with proper spacing rules
            if is_left_paren:
                result += "("
            elif is_right_paren:
                result += ")"
            elif is_operator:
                result += f" {s} "
            else:
                result += s

        return result.lstrip()

    @staticmethod
    def pretty_print_calculation(calc_str):
        return calc_str.replace(" = ", "\n=\n")

    def calculus_graph_to_file(
            self, filename=None, colors_dict=None, x_multiplier=150, y_multiplier=150, width="1800px", height="900px",
            notebook=False, max_depth=100):
        if colors_dict is None:
            colors_dict = {"user data": "gold", "default": "darkred"}
        calculus_graph = build_calculus_graph(
            self, colors_dict, x_multiplier, y_multiplier, width, height, notebook, max_depth=max_depth)

        if filename is None:
            filename = os.path.join(".", f"{self.label} calculus graph.html")

        calculus_graph.show(filename, notebook=notebook)

        add_unique_id_to_mynetwork(filename)

        if notebook:
            from IPython.display import HTML

            return HTML(filename)

        return None

    def serialize_explain_nested_tuples(self):
        localized_explainable_object_type = ExplainableObject  # Localize for faster isinstance

        def recurse(node):
            if node is None:
                return None
            if isinstance(node, tuple):
                left = recurse(node[0])
                right = recurse(node[2])
                return left, node[1], right

            if not isinstance(node, localized_explainable_object_type):
                raise TypeError(f"{node} should be an ExplainableObject but is of type {type(node)}")

            return node.full_str_tuple_id if node.modeling_obj_container is not None else node.to_json()

        return recurse(self.explain_nested_tuples)

    def to_json(self, save_calculated_attributes=False):
        output_dict = {}

        if isinstance(self._value, str):  # Case of technology in WebApplication
            output_dict["value"] = self.value

        output_dict["label"] = self.label

        if self.source is not None:
            output_dict["source"] = {"name": self.source.name, "link": self.source.link}

        if save_calculated_attributes:
            if self._keys_of_direct_ancestors_with_id_loaded_from_json is not None:
                output_dict["direct_ancestors_with_id"] = self._keys_of_direct_ancestors_with_id_loaded_from_json
                output_dict["direct_children_with_id"] = self._keys_of_direct_children_with_id_loaded_from_json
            else:
                output_dict["direct_ancestors_with_id"] = [
                    ancestor.full_str_tuple_id for ancestor in self.direct_ancestors_with_id]
                output_dict["direct_children_with_id"] = [
                    child.full_str_tuple_id for child in self.direct_children_with_id]

            if self.explain_nested_tuples_from_json is not None:
                output_dict["explain_nested_tuples"] = self.explain_nested_tuples_from_json
            else:
                output_dict["explain_nested_tuples"] = self.serialize_explain_nested_tuples()

        return output_dict

    def __repr__(self):
        return str(self)

    def __str__(self):
        self_as_str = str(self.value)
        if len(self_as_str) > 60:
            self_as_str = self_as_str[:60] + "..."

        return self_as_str

    def __eq__(self, other):
        if isinstance(other, ExplainableObject):
            return self.value == other.value

        return False

    def __hash__(self):
        return hash(self.value)
