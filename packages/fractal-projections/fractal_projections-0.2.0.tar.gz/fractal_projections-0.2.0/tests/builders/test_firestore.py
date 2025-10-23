import pytest
from fractal_specifications.generic.operators import EqualsSpecification

from fractal_projections import (
    FieldProjection,
    FirestoreProjectionBuilder,
    ProjectionList,
    QueryProjection,
)


class TestFirestoreBuilder:
    """Integration tests for FirestoreProjectionBuilder"""

    def test_build_without_collection_name_raises_error(self):
        """Test that build() raises error if no collection name provided"""
        builder = FirestoreProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="collection_name is required"):
            builder.build(query)

    def test_build_count_without_collection_name_raises_error(self):
        """Test that build_count() raises error if no collection name provided"""
        builder = FirestoreProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="collection_name is required"):
            builder.build_count(query)

    def test_build_simple_config(self):
        """Test building simple query config"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("name"),
                    FieldProjection("email"),
                ]
            )
        )

        builder = FirestoreProjectionBuilder("users")
        config, _ = builder.build(query)

        assert isinstance(config, dict)
        assert "select_fields" in config
        assert "name" in config["select_fields"]

    def test_build_config_with_filter(self):
        """Test building config with filter"""
        query = QueryProjection(
            filter=EqualsSpecification("status", "active"),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = FirestoreProjectionBuilder("users")
        config, _ = builder.build(query)

        assert "where_clauses" in config

    def test_build_count_config(self):
        """Test building count config"""
        query = QueryProjection()

        builder = FirestoreProjectionBuilder("users")
        config, _ = builder.build_count(query)

        assert config["use_count_aggregation"] is True
        assert config["server_side_only"] is True
