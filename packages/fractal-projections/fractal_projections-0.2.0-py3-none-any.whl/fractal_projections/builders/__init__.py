"""
Projection Builders

Database-specific builders that convert generic projections into
optimized database queries (SQL, MongoDB aggregation pipelines, etc.).
"""

from fractal_projections.builders.base import ProjectionBuilder
from fractal_projections.builders.duckdb import DuckDBProjectionBuilder
from fractal_projections.builders.elasticsearch import ElasticsearchProjectionBuilder
from fractal_projections.builders.firestore import FirestoreProjectionBuilder
from fractal_projections.builders.mongo import MongoProjectionBuilder
from fractal_projections.builders.postgres import PostgresProjectionBuilder

__all__ = [
    "ProjectionBuilder",
    "PostgresProjectionBuilder",
    "DuckDBProjectionBuilder",
    "MongoProjectionBuilder",
    "FirestoreProjectionBuilder",
    "ElasticsearchProjectionBuilder",
]
