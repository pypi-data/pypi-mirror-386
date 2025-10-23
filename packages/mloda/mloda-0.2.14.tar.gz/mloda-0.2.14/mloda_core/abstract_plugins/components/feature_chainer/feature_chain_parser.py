"""
Feature chain parser for handling feature name chaining across feature groups.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from mloda_core.abstract_plugins.components.feature import Feature
from mloda_core.abstract_plugins.components.feature_name import FeatureName
from mloda_core.abstract_plugins.components.options import Options
from mloda_plugins.feature_group.experimental.default_options_key import DefaultOptionKeys


class FeatureChainParser:
    """
    Mixin class for parsing feature names with chaining support.

    Feature chaining allows feature groups to be composed, where the output of one
    feature group becomes the input to another. This is reflected in the feature name
    using a double underscore pattern: prefix__mloda_source_features.

    For example:
    - max_aggr__sum_7_day_window__mean_imputed__price

    Each feature group in the chain extracts its relevant portion and passes the
    rest to the next feature group in the chain.
    """

    @classmethod
    def parse_feature_name(
        cls, feature_name: FeatureName | str, pattern: str, prefix_patterns: List[str]
    ) -> Tuple[str | None, str | None]:
        """Internal method for parsing feature names - used by match_configuration_feature_chain_parser."""
        _feature_name: str = feature_name.name if isinstance(feature_name, FeatureName) else feature_name

        parts = _feature_name.split("__", 1)
        itself = parts[0] + "__"  # Ensure we have the prefix part with double underscore

        remainder = ""
        if len(parts) > 1:
            remainder = parts[1]

        for prefix_pattern in prefix_patterns:
            if re.match(prefix_pattern, itself) is None:
                continue

            if len(parts) == 1:
                raise ValueError(f"Matches the pattern {pattern}, but has no source feature: {_feature_name}")

            source_feature = remainder
            has_prefix_configuration = itself.split(pattern, 1)[0]
            return has_prefix_configuration, source_feature

        return None, None

    @classmethod
    def _match_pattern_based_feature(
        cls, feature_name: str | FeatureName, pattern: str, prefix_patterns: List[str]
    ) -> bool:
        """Internal method for matching pattern-based features - used by match_configuration_feature_chain_parser."""
        _feature_name: FeatureName = FeatureName(feature_name) if isinstance(feature_name, str) else feature_name

        try:
            has_prefix_configuration, source_feature = cls.parse_feature_name(_feature_name, pattern, prefix_patterns)
            if has_prefix_configuration is None or source_feature is None:
                return False
        except ValueError:
            return False
        return True

    @classmethod
    def _has_default_value(cls, property_value: Any) -> bool:
        """Check if property has a default value defined."""
        return isinstance(property_value, dict) and DefaultOptionKeys.mloda_default in property_value

    @classmethod
    def _is_context_parameter(cls, property_value: Any) -> bool:
        """Check if property is marked as context parameter in mapping."""
        return isinstance(property_value, dict) and property_value.get(DefaultOptionKeys.mloda_context, False)

    @classmethod
    def _is_strict_validation(cls, property_value: Any) -> bool:
        """Check if property requires strict validation (values must be in mapping)."""
        return isinstance(property_value, dict) and property_value.get(DefaultOptionKeys.mloda_strict_validation, False)

    @classmethod
    def _get_validation_function(cls, property_value: Any) -> Any:
        """Get validation function from property mapping if present."""
        if isinstance(property_value, dict):
            return property_value.get(DefaultOptionKeys.mloda_validation_function, None)
        return None

    @classmethod
    def _validate_property_value(
        cls, found_property_val: Any, property_value: Any, property_name: str, original_property_config: Any
    ) -> None:
        """
        Unified validation function: if strict validation -> apply validation function OR check membership.

        Raises ValueError if validation fails, otherwise returns None.
        """
        if not cls._is_strict_validation(original_property_config):
            return  # No validation needed

        validation_function = cls._get_validation_function(original_property_config)

        if validation_function is not None:
            # Use validation function if available
            if not validation_function(found_property_val):
                raise ValueError(f"Property value '{found_property_val}' failed validation for '{property_name}'")
        else:
            # Fallback to membership check
            if found_property_val not in property_value:
                raise ValueError(f"Property value '{found_property_val}' not found in mapping for '{property_name}'")

    @classmethod
    def _determine_parameter_category(cls, property_name: str, property_value: Any, options: Options) -> str:
        """
        Determine whether a parameter should be in group or context category.

        Priority:
        1. User explicit override (if property exists in specific category)
        2. Property mapping default (mloda_context flag)
        3. Fallback to group

        Args:
            property_name: Name of the property
            property_value: Property configuration from mapping
            options: Options object containing user's parameter placement

        Returns:
            "group" or "context" indicating target category

        Raises:
            ValueError: If parameter exists in both group and context
        """

        if property_name in options.group and property_name in options.context:
            raise ValueError(
                f"Parameter '{property_name}' exists in both group and context. "
                "This is not allowed. Please choose one category."
            )

        if property_name in options.group:
            return DefaultOptionKeys.mloda_group.value
        elif property_name in options.context:
            return DefaultOptionKeys.mloda_context.value
        elif cls._is_context_parameter(property_value):
            return DefaultOptionKeys.mloda_context.value
        else:
            return DefaultOptionKeys.mloda_group.value

    @classmethod
    def _extract_property_values(cls, property_value: Any) -> Any:
        """Extract property values, removing metadata keys."""
        if isinstance(property_value, dict):
            # Remove metadata keys, keep only the actual valid values
            metadata_keys = {
                DefaultOptionKeys.mloda_default,
                DefaultOptionKeys.mloda_context,
                DefaultOptionKeys.mloda_group,
                DefaultOptionKeys.mloda_strict_validation,
                DefaultOptionKeys.mloda_validation_function,
            }
            return {k: v for k, v in property_value.items() if k not in metadata_keys}
        return property_value

    @classmethod
    def _process_found_property_value(
        cls, found_property_value: Any, property_value: Any, property_name: str, original_property_config: Any
    ) -> Set[str]:
        if not isinstance(found_property_value, frozenset):
            found_property_value = frozenset([found_property_value])

        collected_property_value = set()
        for found_property_val in found_property_value:
            if isinstance(found_property_val, Feature):
                found_property_val = found_property_val.get_name()

            if isinstance(found_property_val, tuple):
                # Convert tuple to string representation for hashability
                found_property_val = str(found_property_val)

            # Use unified validation function
            cls._validate_property_value(found_property_val, property_value, property_name, original_property_config)

            collected_property_value.add(found_property_val)

        return collected_property_value

    @classmethod
    def _validate_final_properties(
        cls, property_tracker: Dict[str, None | Set[str]], property_mapping: Dict[str, Any]
    ) -> bool:
        """Validate that all required properties have values."""
        for key, value in property_tracker.items():
            property_config = property_mapping[key]
            has_default = cls._has_default_value(property_config)

            if not value and not has_default:
                return False
        return True

    @classmethod
    def _validate_options_against_property_mapping(cls, options: Options, property_mapping: Dict[str, Any]) -> bool:
        """
        Shared validation logic for both string-based and configuration-based approaches.

        Args:
            options: Options object containing the parameters to validate
            property_mapping: Property mapping with validation rules

        Returns:
            True if validation passes, False otherwise
        """
        property_tracker: Dict[str, None | Set[str]] = {}
        for key in property_mapping:
            property_tracker[key] = None

        # Process each property in the mapping
        for property_name, property_value in property_mapping.items():
            found_property_value = options.get(property_name)
            has_default = cls._has_default_value(property_value)
            property_value = cls._extract_property_values(property_value)

            # Handle missing properties
            if found_property_value is None:
                if has_default:
                    # Property with default not present - mark as processed but empty
                    property_tracker[property_name] = set()
                    continue
                else:
                    # Required property not present - skip (will fail validation later)
                    continue

            collected_property_value = cls._process_found_property_value(
                found_property_value, property_value, property_name, property_mapping[property_name]
            )

            # We deal with this case for now like this as it is easier and we can add tuples later.
            if collected_property_value == "tuple_found":  # type: ignore
                return False

            if property_tracker[property_name] is not None:
                raise ValueError(f"Feature name has duplicate values for property '{property_name}'.")

            property_tracker[property_name] = collected_property_value
        return cls._validate_final_properties(property_tracker, property_mapping)

    @classmethod
    def match_configuration_feature_chain_parser(
        cls,
        feature_name: str | FeatureName,
        options: Options,
        property_mapping: Optional[Dict[str, Any]] = None,
        pattern: Optional[str] = None,
        prefix_patterns: Optional[List[str]] = None,
    ) -> bool:
        """
        Unified method for matching features using either configuration-based or pattern-based parsing.

        Args:
            feature_name: The feature name to match
            options: Options object containing configuration
            property_mapping: Optional property mapping for configuration-based parsing
            pattern: Optional pattern string for pattern-based parsing
            prefix_patterns: Optional prefix patterns for pattern-based parsing

        Returns:
            True if the feature matches either pattern-based or configuration-based parsing, False otherwise
        """

        # string based matching
        if pattern is not None and prefix_patterns is not None:
            if cls._match_pattern_based_feature(feature_name, pattern, prefix_patterns):
                return True

        # configuration-based

        if property_mapping is not None:
            return cls._validate_options_against_property_mapping(options, property_mapping)

        # If neither pattern-based nor configuration-based matching succeeded, return False
        return False

    @classmethod
    def extract_source_feature(cls, feature_name: str, prefix_pattern: str) -> str:
        """
        Extract the source feature from a feature name based on the prefix pattern.

        Args:
            feature_name: The feature name to parse
            prefix_pattern: Regex pattern for the prefix (e.g., r"^([w]+)_aggr__")

        Returns:
            The source feature part of the name

        Raises:
            ValueError: If the feature name doesn't match the expected pattern
        """
        match = re.match(prefix_pattern, feature_name)
        if not match:
            raise ValueError(f"Invalid feature name format: {feature_name}")

        # Extract the prefix part (everything before the double underscore)
        prefix_end = feature_name.find("__")
        if prefix_end == -1:
            raise ValueError(f"Invalid feature name format: {feature_name}. Missing double underscore separator.")

        # Return everything after the double underscore
        return feature_name[prefix_end + 2 :]
