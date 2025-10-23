import pytest
from fractal_specifications.generic.operators import EqualsSpecification

from fractal_projections import (
    ElasticsearchProjectionBuilder,
    FieldProjection,
    ProjectionList,
    QueryProjection,
)


class TestElasticsearchBuilder:
    """Integration tests for ElasticsearchProjectionBuilder"""

    def test_build_without_index_name_raises_error(self):
        """Test that build() raises error if no index name provided"""
        builder = ElasticsearchProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="collection_name is required"):
            builder.build(query)

    def test_build_count_without_index_name_raises_error(self):
        """Test that build_count() raises error if no index name provided"""
        builder = ElasticsearchProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="collection_name is required"):
            builder.build_count(query)

    def test_build_simple_query(self):
        """Test building simple ES query"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("email"),
                ]
            )
        )

        builder = ElasticsearchProjectionBuilder("users")
        es_query, _ = builder.build(query)

        assert isinstance(es_query, dict)
        assert "_source" in es_query
        assert "name" in es_query["_source"]

    def test_build_query_with_filter(self):
        """Test building ES query with filter"""
        query = QueryProjection(
            filter=EqualsSpecification("status", "active"),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = ElasticsearchProjectionBuilder("users")
        es_query, _ = builder.build(query)

        assert "query" in es_query

    def test_build_count_query(self):
        """Test building ES count query"""
        query = QueryProjection()

        builder = ElasticsearchProjectionBuilder("users")
        es_query, _ = builder.build_count(query)

        assert isinstance(es_query, dict)

    def test_build_count_with_filter(self):
        """Test building ES count query with filter"""
        query = QueryProjection(filter=EqualsSpecification("status", "active"))

        builder = ElasticsearchProjectionBuilder("users")
        es_query, _ = builder.build_count(query)

        assert "query" in es_query
