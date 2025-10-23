import pytest
from fractal_specifications.generic.operators import EqualsSpecification

from fractal_projections import (
    FieldProjection,
    MongoProjectionBuilder,
    ProjectionList,
    QueryProjection,
)


class TestMongoBuilder:
    """Integration tests for MongoProjectionBuilder"""

    def test_build_without_collection_name_raises_error(self):
        """Test that build() raises error if no collection name provided"""
        builder = MongoProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="collection_name is required"):
            builder.build(query)

    def test_build_count_without_collection_name_raises_error(self):
        """Test that build_count() raises error if no collection name provided"""
        builder = MongoProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="collection_name is required"):
            builder.build_count(query)

    def test_build_simple_pipeline(self):
        """Test building simple aggregation pipeline"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("email"),
                ]
            )
        )

        builder = MongoProjectionBuilder("users")
        pipeline, _ = builder.build(query)

        assert isinstance(pipeline, list)
        assert len(pipeline) == 1
        assert "$project" in pipeline[0]

    def test_build_pipeline_with_filter(self):
        """Test building pipeline with $match stage"""
        query = QueryProjection(
            filter=EqualsSpecification("status", "active"),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = MongoProjectionBuilder("users")
        pipeline, _ = builder.build(query)

        assert len(pipeline) >= 1
        assert "$match" in pipeline[0]
        assert "status" in pipeline[0]["$match"]

    def test_build_count_pipeline(self):
        """Test building COUNT pipeline"""
        query = QueryProjection()

        builder = MongoProjectionBuilder("users")
        pipeline, _ = builder.build_count(query)

        assert isinstance(pipeline, list)
        assert {"$count": "count"} in pipeline

    def test_build_count_with_filter(self):
        """Test building COUNT pipeline with filter"""
        query = QueryProjection(filter=EqualsSpecification("status", "active"))

        builder = MongoProjectionBuilder("users")
        pipeline, _ = builder.build_count(query)

        assert "$match" in pipeline[0]
        assert "status" in pipeline[0]["$match"]
        assert {"$count": "count"} in pipeline
