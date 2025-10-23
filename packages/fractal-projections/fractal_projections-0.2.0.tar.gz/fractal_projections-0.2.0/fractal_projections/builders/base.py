"""
Abstract Base Class for Projection Builders

Defines the interface that all database-specific builders must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Tuple

from fractal_projections.projections.query import QueryProjection


class ProjectionBuilder(ABC):
    """
    Abstract base class for database-specific projection builders

    Each database backend (PostgreSQL, MongoDB, Firestore, Elasticsearch)
    implements this interface to convert QueryProjection objects into
    native database queries.
    """

    def __init__(self, collection_name: str = None):
        """
        Initialize builder with a collection/table name

        Args:
            collection_name: Name of the collection/table to query.
                           Can be None if using only static methods for individual clauses.
        """
        self.collection_name = collection_name

    @abstractmethod
    def build(self, query_projection: QueryProjection) -> Tuple[Any, Any]:
        """
        Build a complete query from QueryProjection

        Args:
            query_projection: The query projection to convert

        Returns:
            Tuple of (query, parameters/context)
            - For SQL: (sql_string, params_list)
            - For MongoDB: (pipeline, None)
            - For Elasticsearch: (query_dict, None)
            - For Firestore: (query_config, None)

        Raises:
            ValueError: If collection_name is required but not set
        """
        pass

    @abstractmethod
    def build_count(self, query_projection: QueryProjection) -> Tuple[Any, Any]:
        """
        Build an optimized count query from QueryProjection

        This should return a query optimized for counting results,
        typically ignoring SELECT/projection clauses, ordering, and limiting.

        Args:
            query_projection: The query projection to convert

        Returns:
            Tuple of (count_query, parameters/context) in the same format as build()

        Raises:
            ValueError: If collection_name is required but not set
        """
        pass

    def _require_collection_name(self, method_name: str):
        """
        Helper to enforce that collection_name is set

        Args:
            method_name: Name of the calling method (for error message)

        Raises:
            ValueError: If collection_name is not set
        """
        if not self.collection_name:
            class_name = self.__class__.__name__
            raise ValueError(
                f"collection_name is required for {method_name}(). "
                f"Initialize with {class_name}(collection_name)"
            )
