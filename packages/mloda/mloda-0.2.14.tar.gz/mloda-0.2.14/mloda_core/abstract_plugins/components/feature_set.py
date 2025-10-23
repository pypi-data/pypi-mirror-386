from typing import Any, Optional, Set, Type
from uuid import UUID

from mloda_core.abstract_plugins.components.feature_name import FeatureName
from mloda_core.abstract_plugins.components.feature import Feature
from mloda_core.abstract_plugins.components.options import Options
from mloda_core.filter.filter_engine import BaseFilterEngine
from mloda_core.filter.single_filter import SingleFilter


class FeatureSet:
    def __init__(self) -> None:
        self.features: Set[Feature] = set()
        self.options: Optional[Options] = None
        # This is just one uuid for easier access
        self.any_uuid: Optional[UUID] = None
        self.filters: Optional[Set[SingleFilter]] = None
        self.name_of_one_feature: Optional[FeatureName] = None
        self.artifact_to_save: Optional[str] = None
        self.artifact_to_load: Optional[str] = None
        self.save_artifact: Optional[Any] = None
        self.filter_engine: Type[BaseFilterEngine] = BaseFilterEngine

    def add_artifact_name(self) -> None:
        if self.options is None:
            raise ValueError("No options set. Call this after adding a feature to ensure Options are initialized.")

        for feature_name in self.get_all_names():
            if feature_name in self.options.keys():
                self.artifact_to_load = feature_name
                return

        self.artifact_to_save = self.get_name_of_one_feature().name

    def add(self, feature: Feature) -> None:
        self.features.add(feature)
        self.name_of_one_feature = feature.name
        if self.options is None:
            self.options = feature.options
        if self.any_uuid is None:
            self.any_uuid = feature.uuid

    def remove(self, feature: Feature) -> None:
        self.features.discard(feature)

    def get_all_feature_ids(self) -> Set[UUID]:
        return {feature.uuid for feature in self.features}

    def get_all_names(self) -> Set[str]:
        return {feature.name.name for feature in self.features}

    def __str__(self) -> str:
        return f"{self.features}"

    def get_options_key(self, key: str) -> Any:
        """
        Get a value from the shared options across all features in this FeatureSet.

        This method validates that all features in the set have identical options before
        returning the requested value. If features have different options, it raises ValueError.

        Args:
            key: The option key to retrieve

        Returns:
            The value associated with the key, or None if not found

        Raises:
            ValueError: If options are not initialized or if features have different options

        Note:
            Prefer accessing options directly from individual features when possible.
            Only use this when you need to ensure all features share the same option value.
        """
        if self.options is None:
            raise ValueError("No options set. Call this after adding a feature to ensure Options are initialized.")
        self.validate_equal_options()
        return self.options.get(key)

    def validate_equal_options(self) -> None:
        """Checks if all features have the same options."""
        _options = None
        for feature in self.features:
            if _options:
                if _options != feature.options:
                    raise ValueError("All features must have the same options.")
            _options = feature.options

    def get_initial_requested_features(self) -> Set[FeatureName]:
        return {feature.name for feature in self.features if feature.initial_requested_data}

    def get_name_of_one_feature(self) -> FeatureName:
        if self.name_of_one_feature is None:
            raise ValueError("No feature added yet. Add a feature before calling this method.")
        return self.name_of_one_feature

    def add_filters(self, single_filters: Set[SingleFilter]) -> None:
        if self.filters is not None:
            raise ValueError("Filters already set. This should be called once during setup of the feature set.")

        if not isinstance(single_filters, Set):
            raise ValueError("Filters should be a set.")

        self.filters = single_filters

    def get_artifact(self, config: Options) -> Any:
        return None
