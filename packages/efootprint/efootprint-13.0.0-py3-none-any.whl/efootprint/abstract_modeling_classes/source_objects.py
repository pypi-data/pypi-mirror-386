from datetime import datetime

from pint import Quantity

from efootprint.abstract_modeling_classes.explainable_object_base_class import ExplainableObject, Source
from efootprint.abstract_modeling_classes.explainable_hourly_quantities import ExplainableHourlyQuantities
from efootprint.abstract_modeling_classes.explainable_quantity import ExplainableQuantity
from efootprint.abstract_modeling_classes.explainable_recurrent_quantities import ExplainableRecurrentQuantities
from efootprint.abstract_modeling_classes.explainable_timezone import ExplainableTimezone
from efootprint.constants.sources import Sources


SOURCE_VALUE_DEFAULT_NAME = "unnamed source"


class SourceObject(ExplainableObject):
    def __init__(self, value: object, source: Source = Sources.HYPOTHESIS, label: str = SOURCE_VALUE_DEFAULT_NAME):
        super().__init__(value, label=label, source=source)

class SourceTimezone(ExplainableTimezone):
    def __init__(self, value: object, source: Source = Sources.HYPOTHESIS, label: str = SOURCE_VALUE_DEFAULT_NAME):
        super().__init__(value, label=label, source=source)

class SourceValue(ExplainableQuantity):
    def __init__(self, value: Quantity, source: Source = Sources.HYPOTHESIS, label: str = SOURCE_VALUE_DEFAULT_NAME):
        super().__init__(value, label=label, source=source)

class SourceHourlyValues(ExplainableHourlyQuantities):
    def __init__(self, value: Quantity, start_date: datetime, source: Source = Sources.HYPOTHESIS,
                 label: str = SOURCE_VALUE_DEFAULT_NAME):
        super().__init__(value, start_date=start_date, label=label, source=source)

class SourceRecurrentValues(ExplainableRecurrentQuantities):
    def __init__(self, value: Quantity, source: Source = Sources.HYPOTHESIS, label: str = SOURCE_VALUE_DEFAULT_NAME):
        super().__init__(value, label=label, source=source)
