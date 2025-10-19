"""
Property-Based Filtering for Broadlistening Analysis

Enables filtering of opinions and clusters by demographic properties
such as gender, region, age group, or custom attributes.

Example:
    >>> from filtering import PropertyFilter
    >>> filter = PropertyFilter(opinions)
    >>>
    >>> # Filter by single property
    >>> female_opinions = filter.filter(gender="女性")
    >>>
    >>> # Filter by multiple values (OR)
    >>> tokyo_osaka = filter.filter(region=["東京都", "大阪府"])
    >>>
    >>> # Filter by multiple properties (AND)
    >>> tokyo_females = filter.filter(gender="女性", region="東京都")
    >>>
    >>> # Get property distribution
    >>> gender_dist = filter.get_property_distribution("gender")
    >>> # {"女性": 15, "男性": 10, "その他": 3, "未回答": 2}
"""

from typing import Any

from pipeline import Opinion  # Import Opinion model


class PropertyFilter:
    """Filter opinions/clusters by demographic properties

    This class provides flexible filtering capabilities for analyzing
    opinions by demographic segments (gender, region, age_group, etc.)

    Attributes:
        opinions: List of Opinion objects to filter
    """

    def __init__(self, opinions: list[Opinion]):
        """Initialize filter with opinions

        Args:
            opinions: List of Opinion objects with properties
        """
        self.opinions = opinions

    def filter(
        self,
        gender: str | list[str] | None = None,
        region: str | list[str] | None = None,
        age_group: str | list[str] | None = None,
        custom: dict[str, str | list[str]] | None = None,
    ) -> list[Opinion]:
        """Filter opinions by properties

        All filters are combined with AND logic. Within each filter,
        multiple values are combined with OR logic.

        Args:
            gender: Gender value(s) to filter by
                   Single value: "女性"
                   Multiple values: ["女性", "その他"]
            region: Region value(s) to filter by
            age_group: Age group value(s) to filter by
            custom: Custom property filters
                   Example: {"occupation": "会社員"}
                           {"occupation": ["会社員", "公務員"]}

        Returns:
            Filtered list of Opinion objects

        Examples:
            >>> # Single filter
            >>> female_ops = filter.filter(gender="女性")
            >>>
            >>> # Multiple values (OR)
            >>> tokyo_osaka = filter.filter(region=["東京都", "大阪府"])
            >>>
            >>> # Multiple filters (AND)
            >>> tokyo_females_30s = filter.filter(
            ...     gender="女性",
            ...     region="東京都",
            ...     age_group="30代"
            ... )
            >>>
            >>> # Custom properties
            >>> workers = filter.filter(custom={"occupation": "会社員"})
        """
        filtered = self.opinions

        # Apply standard property filters
        if gender:
            filtered = self._filter_by_property(filtered, "gender", gender)
        if region:
            filtered = self._filter_by_property(filtered, "region", region)
        if age_group:
            filtered = self._filter_by_property(filtered, "age_group", age_group)

        # Apply custom property filters
        if custom:
            for key, value in custom.items():
                filtered = self._filter_by_property(filtered, key, value)

        return filtered

    def _filter_by_property(
        self, opinions: list[Opinion], property_name: str, value: str | list[str]
    ) -> list[Opinion]:
        """Filter opinions by a single property

        Args:
            opinions: Opinions to filter
            property_name: Name of property to filter by
            value: Value(s) to match (OR logic for multiple values)

        Returns:
            Filtered opinions
        """
        # Normalize to list
        values = [value] if isinstance(value, str) else value

        # Filter opinions where property matches any of the values
        filtered = [
            op for op in opinions if op.properties.get(property_name) in values
        ]

        return filtered

    def get_property_distribution(
        self, property_name: str, opinions: list[Opinion] | None = None
    ) -> dict[str, int]:
        """Calculate distribution of property values

        Args:
            property_name: Name of property to analyze
            opinions: Opinions to analyze (default: all opinions)

        Returns:
            Dictionary mapping property value to count

        Example:
            >>> dist = filter.get_property_distribution("gender")
            >>> # {"女性": 15, "男性": 10, "その他": 3, "未回答": 2}
        """
        opinions = opinions or self.opinions
        distribution: dict[str, int] = {}

        for op in opinions:
            value = op.properties.get(property_name, "未回答")
            distribution[value] = distribution.get(value, 0) + 1

        return distribution

    def get_all_property_distributions(
        self, opinions: list[Opinion] | None = None
    ) -> dict[str, dict[str, int]]:
        """Calculate distributions for all properties

        Args:
            opinions: Opinions to analyze (default: all opinions)

        Returns:
            Dictionary mapping property name to distribution

        Example:
            >>> dists = filter.get_all_property_distributions()
            >>> # {
            >>> #     "gender": {"女性": 15, "男性": 10, ...},
            >>> #     "region": {"東京都": 12, "大阪府": 8, ...},
            >>> #     "age_group": {"30代": 10, "40代": 8, ...}
            >>> # }
        """
        opinions = opinions or self.opinions

        # Get all unique property names
        all_properties: set[str] = set()
        for op in opinions:
            all_properties.update(op.properties.keys())

        # Calculate distribution for each property
        distributions = {
            prop: self.get_property_distribution(prop, opinions)
            for prop in all_properties
        }

        return distributions

    def get_property_values(self, property_name: str) -> list[str]:
        """Get all unique values for a property

        Args:
            property_name: Name of property

        Returns:
            Sorted list of unique values

        Example:
            >>> regions = filter.get_property_values("region")
            >>> # ["大阪府", "東京都", "神奈川県"]
        """
        values = {
            op.properties.get(property_name, "未回答") for op in self.opinions
        }
        return sorted(values)

    def summary(self) -> dict[str, Any]:
        """Generate summary statistics

        Returns:
            Dictionary with:
            - total_opinions: Total number of opinions
            - property_names: List of property names
            - distributions: Property distributions
            - completeness: Percentage of non-"未回答" for each property

        Example:
            >>> summary = filter.summary()
            >>> print(summary["total_opinions"])  # 30
            >>> print(summary["completeness"]["gender"])  # 0.933 (28/30 answered)
        """
        distributions = self.get_all_property_distributions()
        total = len(self.opinions)

        # Calculate completeness (% answered)
        completeness = {}
        for prop, dist in distributions.items():
            answered = total - dist.get("未回答", 0)
            completeness[prop] = answered / total if total > 0 else 0.0

        return {
            "total_opinions": total,
            "property_names": list(distributions.keys()),
            "distributions": distributions,
            "completeness": completeness,
        }

    def filter_clusters(
        self,
        clusters: list[Any],  # List of Cluster objects
        min_opinions: int = 1,
        property_filter: dict[str, str | list[str]] | None = None,
    ) -> list[Any]:
        """Filter clusters by criteria

        Args:
            clusters: List of Cluster objects
            min_opinions: Minimum number of opinions in cluster
            property_filter: Property filters to apply to opinions
                           Example: {"gender": "女性", "region": "東京都"}

        Returns:
            Filtered clusters

        Example:
            >>> # Filter clusters with at least 5 female opinions from Tokyo
            >>> tokyo_female_clusters = filter.filter_clusters(
            ...     clusters,
            ...     min_opinions=5,
            ...     property_filter={"gender": "女性", "region": "東京都"}
            ... )
        """
        filtered_clusters = []

        for cluster in clusters:
            # Apply property filter to cluster opinions
            cluster_opinions = cluster.opinions

            if property_filter:
                # Filter opinions in this cluster
                opinion_filter = PropertyFilter(cluster_opinions)
                filtered_ops = opinion_filter.filter(**property_filter)
            else:
                filtered_ops = cluster_opinions

            # Check if cluster meets minimum opinion threshold
            if len(filtered_ops) >= min_opinions:
                filtered_clusters.append(cluster)

        return filtered_clusters
