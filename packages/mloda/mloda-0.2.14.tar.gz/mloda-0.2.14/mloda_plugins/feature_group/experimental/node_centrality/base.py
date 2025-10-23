"""
Base implementation for node centrality feature groups.
"""

from __future__ import annotations

from typing import Any, Optional, Set, Type, Union

from mloda_core.abstract_plugins.abstract_feature_group import AbstractFeatureGroup
from mloda_core.abstract_plugins.components.feature import Feature
from mloda_core.abstract_plugins.components.feature_chainer.feature_chain_parser import FeatureChainParser
from mloda_core.abstract_plugins.components.feature_name import FeatureName
from mloda_core.abstract_plugins.components.feature_set import FeatureSet
from mloda_core.abstract_plugins.components.options import Options
from mloda_plugins.feature_group.experimental.default_options_key import DefaultOptionKeys


class NodeCentralityFeatureGroup(AbstractFeatureGroup):
    # Option keys for centrality configuration
    CENTRALITY_TYPE = "centrality_type"
    GRAPH_TYPE = "graph_type"
    WEIGHT_COLUMN = "weight_column"
    """
    Base class for all node centrality feature groups.

    Node centrality feature groups calculate various centrality metrics for nodes in a graph.
    These metrics help identify important nodes in network data based on different definitions
    of importance.

    ## Feature Naming Convention

    Node centrality features follow this naming pattern:
    `{centrality_type}_centrality__{node_feature}`

    The node feature (mloda_source_features) is extracted from the feature name and used
    as the node identifier for centrality calculations. Note the double underscore before 
    the node feature.

    Examples:
    - `degree_centrality__user`: Degree centrality for user nodes
    - `betweenness_centrality__product`: Betweenness centrality for product nodes
    - `pagerank_centrality__website`: PageRank centrality for website nodes

    ## Configuration-Based Creation

    NodeCentralityFeatureGroup supports configuration-based. This allows features to be created
    from options rather than explicit feature names.

    To create a centrality feature using configuration:

    ```python
    feature = Feature(
        "PlaceHolder",  # Placeholder name, will be replaced
        Options({
            NodeCentralityFeatureGroup.CENTRALITY_TYPE: "degree",
            DefaultOptionKeys.mloda_source_features: "user"
        })
    )

    # The Engine will automatically parse this into a feature with name "degree_centrality__user"
    ```

    ### Important Note on Multiple Features

    When creating multiple features with different source features or options, each feature
    will be processed separately and may result in multiple DataFrames in the output. For example:

    ```python
    # These features will likely be processed into separate DataFrames
    degree_undirected = Feature(
        "placeholder",
        Options({
            NodeCentralityFeatureGroup.CENTRALITY_TYPE: "degree",
            DefaultOptionKeys.mloda_source_features: "source",
            NodeCentralityFeatureGroup.GRAPH_TYPE: "undirected",
        })
    )

    degree_directed = Feature(
        "placeholder",
        Options({
            NodeCentralityFeatureGroup.CENTRALITY_TYPE: "degree",
            DefaultOptionKeys.mloda_source_features: "target",  # Different source feature
            NodeCentralityFeatureGroup.GRAPH_TYPE: "directed",
        })
    )
    ```

    In this case, the result will contain two separate DataFrames: one with "degree_centrality__source"
    and another with "degree_centrality__target". This behavior occurs because features with different
    source features are processed by different feature groups.

    ## Supported Centrality Types

    - `degree`: Measures the number of connections a node has
    - `betweenness`: Measures how often a node lies on the shortest path between other nodes
    - `closeness`: Measures how close a node is to all other nodes
    - `eigenvector`: Measures the influence of a node in a network
    - `pagerank`: A variant of eigenvector centrality used by Google

    ## Graph Types

    - `directed`: A graph where edges have direction
    - `undirected`: A graph where edges have no direction (default)

    ## Requirements
    - The input data must contain edge information (source and target columns)
    - For weighted centrality calculations, a weight column can be specified
    
    ## Important Implementation Note
    
    When using configuration-based creation with different options,
    each feature will be processed separately and may result in multiple DataFrames in 
    the output. This is because feature groups are currently split by different options.
    """

    # Define supported centrality types
    CENTRALITY_TYPES = {
        "degree": "Measures the number of connections a node has",
        "betweenness": "Measures how often a node lies on the shortest path between other nodes",
        "closeness": "Measures how close a node is to all other nodes",
        "eigenvector": "Measures the influence of a node in a network",
        "pagerank": "A variant of eigenvector centrality used by Google",
    }

    # Define supported graph types
    GRAPH_TYPES = {
        "directed": "A graph where edges have direction",
        "undirected": "A graph where edges have no direction",
    }

    # Define the prefix pattern for this feature group
    PREFIX_PATTERN = r"^([\w]+)_centrality__"
    PATTERN = "__"

    # Property mapping for configuration-based feature creation
    PROPERTY_MAPPING = {
        # Context parameters (don't affect Feature Group resolution)
        CENTRALITY_TYPE: {
            **CENTRALITY_TYPES,  # All supported centrality types as valid options
            DefaultOptionKeys.mloda_context: True,
            DefaultOptionKeys.mloda_strict_validation: True,
        },
        GRAPH_TYPE: {
            **GRAPH_TYPES,  # All supported graph types as valid options
            DefaultOptionKeys.mloda_context: True,
            DefaultOptionKeys.mloda_strict_validation: True,
            DefaultOptionKeys.mloda_default: "undirected",
        },
        WEIGHT_COLUMN: {
            "explanation": "Column name for edge weights (optional)",
            DefaultOptionKeys.mloda_context: True,
            DefaultOptionKeys.mloda_default: None,
        },
        DefaultOptionKeys.mloda_source_features: {
            "explanation": "Source feature representing the nodes for centrality calculation",
            DefaultOptionKeys.mloda_context: True,
        },
    }

    def input_features(self, options: Options, feature_name: FeatureName) -> Optional[Set[Feature]]:
        """Extract source feature from either configuration-based options or string parsing."""

        source_feature: str | None = None

        # string based
        _, source_feature = FeatureChainParser.parse_feature_name(feature_name, self.PATTERN, [self.PREFIX_PATTERN])
        if source_feature is not None:
            return {Feature(source_feature)}

        # configuration based
        source_features = options.get_source_features()
        if len(source_features) != 1:
            raise ValueError(
                f"Expected exactly one source feature, but found {len(source_features)}: {source_features}"
            )
        return set(source_features)

    @classmethod
    def parse_centrality_prefix(cls, feature_name: str) -> str:
        """
        Parse the centrality prefix to extract the centrality type.

        Args:
            feature_name: The feature name to parse

        Returns:
            The centrality type

        Raises:
            ValueError: If the prefix doesn't match the expected pattern
        """
        # Extract the prefix part (everything before the double underscore)
        prefix_end = feature_name.find("__")
        if prefix_end == -1:
            raise ValueError(
                f"Invalid centrality feature name format: {feature_name}. Missing double underscore separator."
            )

        prefix = feature_name[:prefix_end]

        # Parse the prefix components
        parts = prefix.split("_")
        if len(parts) != 2 or parts[1] != "centrality":
            raise ValueError(
                f"Invalid centrality feature name format: {feature_name}. "
                f"Expected format: {{centrality_type}}_centrality__{{mloda_source_features}}"
            )

        centrality_type = parts[0]

        # Validate centrality type
        if centrality_type not in cls.CENTRALITY_TYPES:
            raise ValueError(
                f"Unsupported centrality type: {centrality_type}. "
                f"Supported types: {', '.join(cls.CENTRALITY_TYPES.keys())}"
            )

        return centrality_type

    @classmethod
    def get_centrality_type(cls, feature_name: str) -> str:
        """Extract the centrality type from the feature name."""
        return cls.parse_centrality_prefix(feature_name)

    @classmethod
    def match_feature_group_criteria(
        cls,
        feature_name: Union[FeatureName, str],
        options: Options,
        data_access_collection: Optional[Any] = None,
    ) -> bool:
        """Check if feature name matches the expected pattern for centrality features."""
        if isinstance(feature_name, FeatureName):
            feature_name = feature_name.name

        return FeatureChainParser.match_configuration_feature_chain_parser(
            feature_name,
            options,
            property_mapping=cls.PROPERTY_MAPPING,
            pattern=cls.PATTERN,
            prefix_patterns=[cls.PREFIX_PATTERN],
        )

    @classmethod
    def calculate_feature(cls, data: Any, features: FeatureSet) -> Any:
        """
        Calculate centrality metrics for nodes in a graph.

        Processes all requested features, determining the centrality type
        and source features from each feature name.

        Adds the centrality results directly to the input data structure.
        """
        # Process each feature
        for feature in features.features:
            centrality_type, source_feature_str = cls._extract_centrality_and_source_feature(feature)

            # Common parameter extraction (works for both approaches)
            graph_type = feature.options.get(cls.GRAPH_TYPE) or "undirected"
            weight_column = feature.options.get(cls.WEIGHT_COLUMN)

            # Validate graph type
            if graph_type not in cls.GRAPH_TYPES:
                raise ValueError(
                    f"Unsupported graph type: {graph_type}. Supported types: {', '.join(cls.GRAPH_TYPES.keys())}"
                )

            # Check if source feature exists
            cls._check_source_feature_exists(data, source_feature_str)

            # Calculate centrality
            result = cls._calculate_centrality(data, centrality_type, source_feature_str, graph_type, weight_column)

            # Add the result to the data
            data = cls._add_result_to_data(data, feature.get_name(), result)

        return data

    @classmethod
    def _extract_centrality_and_source_feature(cls, feature: Feature) -> tuple[str, str]:
        """
        Extract centrality type and source feature name from a feature.

        Tries string-based parsing first, falls back to configuration-based approach.

        Args:
            feature: The feature to extract parameters from

        Returns:
            Tuple of (centrality_type, source_feature_name)

        Raises:
            ValueError: If parameters cannot be extracted
        """
        centrality_type = None
        source_feature_name: str | None = None

        # Try string-based parsing first
        prefix_part, source_feature_name = FeatureChainParser.parse_feature_name(
            feature.name, cls.PATTERN, [cls.PREFIX_PATTERN]
        )
        if prefix_part is not None and source_feature_name is not None:
            # Extract centrality type from the prefix (e.g., "degree_centrality" -> "degree")
            if prefix_part.endswith("_centrality"):
                centrality_type = prefix_part[: -len("_centrality")]
                if centrality_type in cls.CENTRALITY_TYPES:
                    return centrality_type, source_feature_name

        # Fall back to configuration-based approach
        source_features = feature.options.get_source_features()
        if len(source_features) != 1:
            raise ValueError(
                f"Expected exactly one source feature, but found {len(source_features)}: {source_features}"
            )

        source_feature = next(iter(source_features))
        source_feature_name = source_feature.get_name()

        centrality_type = feature.options.get(cls.CENTRALITY_TYPE)

        if centrality_type is None or source_feature_name is None:
            raise ValueError(f"Could not extract centrality type and source feature from: {feature.name}")

        return centrality_type, source_feature_name

    @classmethod
    def _check_source_feature_exists(cls, data: Any, feature_name: str) -> None:
        """
        Check if the source feature exists in the data.

        Args:
            data: The input data
            feature_name: The name of the feature to check

        Raises:
            ValueError: If the feature does not exist in the data
        """
        raise NotImplementedError(f"_check_source_feature_exists not implemented in {cls.__name__}")

    @classmethod
    def _add_result_to_data(cls, data: Any, feature_name: str, result: Any) -> Any:
        """
        Add the result to the data.

        Args:
            data: The input data
            feature_name: The name of the feature to add
            result: The result to add

        Returns:
            The updated data
        """
        raise NotImplementedError(f"_add_result_to_data not implemented in {cls.__name__}")

    @classmethod
    def _calculate_centrality(
        cls,
        data: Any,
        centrality_type: str,
        node_feature: str,
        graph_type: str = "undirected",
        weight_column: Optional[str] = None,
    ) -> Any:
        """
        Method to calculate the centrality. Should be implemented by subclasses.

        Args:
            data: The input data
            centrality_type: The type of centrality to calculate
            node_feature: The feature representing the nodes
            graph_type: The type of graph (directed or undirected)
            weight_column: The column to use for edge weights (optional)

        Returns:
            The result of the centrality calculation
        """
        raise NotImplementedError(f"_calculate_centrality not implemented in {cls.__name__}")
