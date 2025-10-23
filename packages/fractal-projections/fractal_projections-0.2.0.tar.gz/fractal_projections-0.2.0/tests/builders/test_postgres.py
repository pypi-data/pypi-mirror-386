import pytest
from fractal_specifications.generic.collections import AndSpecification
from fractal_specifications.generic.operators import (
    EqualsSpecification,
    GreaterThanSpecification,
    InSpecification,
)

from fractal_projections import (
    AggregateFunction,
    AggregateProjection,
    FieldProjection,
    GroupingProjection,
    LimitProjection,
    OrderingList,
    OrderingProjection,
    PostgresProjectionBuilder,
    ProjectionList,
    QueryProjection,
)


class TestPostgresBuilder:
    """Integration tests for PostgresProjectionBuilder"""

    def test_build_without_table_name_raises_error(self):
        """Test that build() raises error if no table name provided"""
        builder = PostgresProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="table_name is required"):
            builder.build(query)

    def test_build_count_without_table_name_raises_error(self):
        """Test that build_count() raises error if no table name provided"""
        builder = PostgresProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="table_name is required"):
            builder.build_count(query)

    def test_explain_without_table_name_raises_error(self):
        """Test that explain() raises error if no table name provided"""
        builder = PostgresProjectionBuilder()
        query = QueryProjection()

        with pytest.raises(ValueError, match="table_name is required"):
            builder.explain(query)

    def test_build_simple_query_no_filter(self):
        """Test building a simple SELECT query without filter"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("id"),
                    FieldProjection("name"),
                ]
            )
        )

        builder = PostgresProjectionBuilder("users")
        sql, params = builder.build(query)

        assert sql == "SELECT id, name FROM users"
        assert params == []

    def test_build_query_with_filter(self):
        """Test building query with WHERE clause"""
        query = QueryProjection(
            filter=EqualsSpecification("status", "active"),
            projection=ProjectionList(
                [
                    FieldProjection("id"),
                    FieldProjection("name"),
                ]
            ),
        )

        builder = PostgresProjectionBuilder("users")
        sql, params = builder.build(query)

        assert "SELECT id, name FROM users WHERE status = %s" == sql
        assert params == ["active"]

    def test_build_query_with_complex_filter(self):
        """Test building query with complex AND filter"""
        query = QueryProjection(
            filter=AndSpecification(
                [
                    EqualsSpecification("status", "active"),
                    GreaterThanSpecification("age", 18),
                ]
            ),
            projection=ProjectionList([FieldProjection("name")]),
        )

        builder = PostgresProjectionBuilder("users")
        sql, params = builder.build(query)

        assert "WHERE" in sql
        assert "status = %s" in sql
        assert "age > %s" in sql
        assert "AND" in sql
        assert params == ["active", 18]

    def test_build_complete_query(self):
        """Test building complete query with all components"""
        query = QueryProjection(
            filter=EqualsSpecification("status", "active"),
            projection=ProjectionList(
                [
                    FieldProjection("id"),
                    FieldProjection("name"),
                    FieldProjection("created_at"),
                ]
            ),
            ordering=OrderingList([OrderingProjection("created_at", ascending=False)]),
            limiting=LimitProjection(10, offset=5),
        )

        builder = PostgresProjectionBuilder("users")
        sql, params = builder.build(query)

        assert (
            sql
            == "SELECT id, name, created_at FROM users WHERE status = %s ORDER BY created_at DESC LIMIT 10 OFFSET 5"
        )
        assert params == ["active"]

    def test_build_query_with_grouping(self):
        """Test building query with GROUP BY"""
        query = QueryProjection(
            projection=ProjectionList(
                [
                    FieldProjection("department"),
                    AggregateProjection(AggregateFunction.COUNT, alias="count"),
                ]
            ),
            grouping=GroupingProjection(["department"]),
        )

        builder = PostgresProjectionBuilder("employees")
        sql, params = builder.build(query)

        assert (
            "SELECT department, COUNT(*) AS count FROM employees GROUP BY department"
            == sql
        )
        assert params == []

    def test_build_count_simple(self):
        """Test building COUNT query"""
        query = QueryProjection()

        builder = PostgresProjectionBuilder("users")
        sql, params = builder.build_count(query)

        assert sql == "SELECT COUNT(*) FROM users"
        assert params == []

    def test_build_count_with_filter(self):
        """Test building COUNT query with WHERE clause"""
        query = QueryProjection(filter=InSpecification("status", ["active", "pending"]))

        builder = PostgresProjectionBuilder("users")
        sql, params = builder.build_count(query)

        assert "SELECT COUNT(*) FROM users WHERE status IN (%s,%s)" == sql
        assert params == ["active", "pending"]

    def test_explain_query(self):
        """Test building EXPLAIN query"""
        query = QueryProjection(
            projection=ProjectionList([FieldProjection("name")]),
            limiting=LimitProjection(10),
        )

        builder = PostgresProjectionBuilder("users")
        explain_sql, params = builder.explain(query)

        assert explain_sql.startswith("EXPLAIN (ANALYZE, BUFFERS)")
        assert "SELECT name FROM users LIMIT 10" in explain_sql
        assert params == []
