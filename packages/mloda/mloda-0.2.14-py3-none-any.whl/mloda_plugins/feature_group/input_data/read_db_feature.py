from typing import Any, Optional

from mloda_core.abstract_plugins.abstract_feature_group import AbstractFeatureGroup
from mloda_core.abstract_plugins.components.feature_set import FeatureSet
from mloda_core.abstract_plugins.components.input_data.base_input_data import BaseInputData
from mloda_plugins.feature_group.input_data.read_db import ReadDB


class ReadDBFeature(AbstractFeatureGroup):
    @classmethod
    def input_data(cls) -> Optional[BaseInputData]:
        return ReadDB()

    @classmethod
    def calculate_feature(cls, data: Any, features: FeatureSet) -> Any:
        reader = cls.input_data()
        if reader is not None:
            return reader.load(features)
        raise ValueError(f"Reading file failed for feature {features.get_name_of_one_feature()}.")
