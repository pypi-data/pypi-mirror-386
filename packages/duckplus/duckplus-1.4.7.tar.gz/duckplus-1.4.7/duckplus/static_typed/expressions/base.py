"""Base expression classes shared across typed operations."""

# pylint: disable=too-many-locals

from __future__ import annotations

from collections.abc import Iterable as IterableABC
from decimal import Decimal
from types import NotImplementedType
from typing import TYPE_CHECKING, Iterable, TypeVar, Union

from ..dependencies import (
    DependencyLike,
    ExpressionDependency,
    normalise_dependencies,
)
from ..types import BooleanType, DuckDBType, GenericType
from .utils import quote_identifier, quote_qualified_identifier

if TYPE_CHECKING:  # pragma: no cover - typing helper
    from .text import VarcharExpression


def _scalar_generic_namespace():
    from .._generated_function_namespaces import SCALAR_FUNCTIONS

    return SCALAR_FUNCTIONS.Generic


def _scalar_varchar_namespace():
    from .._generated_function_namespaces import SCALAR_FUNCTIONS

    return SCALAR_FUNCTIONS.Varchar

ExpressionT = TypeVar("ExpressionT", bound="TypedExpression")
ComparisonResult = Union["BooleanExpression", NotImplementedType]


class TypedExpression:
    """Representation of a typed SQL expression."""

    __slots__ = ("_sql", "duck_type", "_dependencies")

    def __init__(
        self,
        sql: str,
        *,
        duck_type: DuckDBType,
        dependencies: Iterable[DependencyLike] = (),
    ) -> None:
        self._sql = sql
        self.duck_type = duck_type
        self._dependencies = normalise_dependencies(dependencies)

    def render(self) -> str:
        return self._sql

    def __str__(self) -> str:  # pragma: no cover - delegation to ``render``
        return self.render()

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"{self.__class__.__name__}({self.render()!r}, {self.duck_type!r})"

    @property
    def dependencies(self) -> frozenset[ExpressionDependency]:
        return self._dependencies

    def alias(self, alias: str) -> "AliasedExpression":
        return AliasedExpression(base=self, alias=alias)

    def clone_with_sql(
        self,
        sql: str,
        *,
        dependencies: Iterable[DependencyLike],
    ) -> "TypedExpression":
        return type(self)(
            sql,
            duck_type=self.duck_type,
            dependencies=dependencies,
        )

    def cast(self, target: object) -> "TypedExpression":
        """Return a typed expression casting this expression to ``target``."""

        from . import casting as _casting  # pylint: disable=import-outside-toplevel

        return _casting.cast_expression(self, target, try_cast=False)

    def try_cast(self, target: object) -> "TypedExpression":
        """Return a typed expression attempting to cast to ``target``."""

        from . import casting as _casting  # pylint: disable=import-outside-toplevel

        return _casting.cast_expression(self, target, try_cast=True)

    def _comparison(self: ExpressionT, operator: str, other: object) -> "BooleanExpression":
        operand = self._coerce_operand(other)
        sql = f"({self.render()} {operator} {operand.render()})"
        dependencies = self.dependencies.union(operand.dependencies)
        return BooleanExpression(sql, dependencies=dependencies)

    def is_null(self) -> "BooleanExpression":
        """Return a boolean expression testing whether the value is ``NULL``."""

        sql = f"({self.render()} IS NULL)"
        return BooleanExpression(sql, dependencies=self.dependencies)

    def is_not_null(self) -> "BooleanExpression":
        """Return a boolean expression testing whether the value is not ``NULL``."""

        sql = f"({self.render()} IS NOT NULL)"
        return BooleanExpression(sql, dependencies=self.dependencies)

    def _coerce_operand(self: ExpressionT, other: object) -> ExpressionT:
        raise NotImplementedError

    def __eq__(self, other: object) -> ComparisonResult:  # type: ignore[override]
        if isinstance(
            other, (TypedExpression, str, int, float, bool, bytes, Decimal)
        ):
            return self._comparison("=", other)
        return NotImplemented

    def __ne__(self, other: object) -> ComparisonResult:  # type: ignore[override]
        if isinstance(
            other, (TypedExpression, str, int, float, bool, bytes, Decimal)
        ):
            return self._comparison("!=", other)
        return NotImplemented

    def __lt__(self, other: object) -> ComparisonResult:  # type: ignore[override]
        if isinstance(
            other, (TypedExpression, str, int, float, bool, bytes, Decimal)
        ):
            return self._comparison("<", other)
        return NotImplemented

    def __le__(self, other: object) -> ComparisonResult:  # type: ignore[override]
        if isinstance(
            other, (TypedExpression, str, int, float, bool, bytes, Decimal)
        ):
            return self._comparison("<=", other)
        return NotImplemented

    def __gt__(self, other: object) -> ComparisonResult:  # type: ignore[override]
        if isinstance(
            other, (TypedExpression, str, int, float, bool, bytes, Decimal)
        ):
            return self._comparison(">", other)
        return NotImplemented

    def __ge__(self, other: object) -> ComparisonResult:  # type: ignore[override]
        if isinstance(
            other, (TypedExpression, str, int, float, bool, bytes, Decimal)
        ):
            return self._comparison(">=", other)
        return NotImplemented

    def over(
        self,
        *,
        partition_by: Iterable[object] | object | None = None,
        order_by: Iterable[object] | object | None = None,
        frame: str | None = None,
    ) -> "TypedExpression":  # pylint: disable=too-many-locals
        """Wrap the expression in a DuckDB window clause."""

        partition_operands = self._normalise_window_operands(partition_by)
        order_operands = self._normalise_window_operands(order_by)

        dependencies = set(self.dependencies)
        partition_sql: list[str] = []
        for operand in partition_operands:
            sql, operand_dependencies = self._coerce_window_operand(operand)
            partition_sql.append(sql)
            dependencies.update(operand_dependencies)

        order_sql: list[str] = []
        for operand in order_operands:
            sql, operand_dependencies = self._coerce_window_order_operand(operand)
            order_sql.append(sql)
            dependencies.update(operand_dependencies)

        components: list[str] = []
        if partition_sql:
            components.append(f"PARTITION BY {', '.join(partition_sql)}")
        if order_sql:
            components.append(f"ORDER BY {', '.join(order_sql)}")
        if frame is not None:
            frame_sql = frame.strip()
            if not frame_sql:
                msg = "Window frame clause cannot be empty"
                raise ValueError(msg)
            components.append(frame_sql)

        window_spec = " ".join(components)
        window_clause = f"({window_spec})" if components else "()"
        sql = f"({self.render()} OVER {window_clause})"
        return self.clone_with_sql(sql, dependencies=dependencies)

    @classmethod
    def _normalise_window_operands(
        cls, operands: Iterable[object] | object | None
    ) -> list[object]:
        if operands is None:
            return []
        if isinstance(operands, (list, tuple, set)):
            return list(operands)
        if isinstance(operands, (TypedExpression, str)):
            return [operands]
        if isinstance(operands, IterableABC):
            return list(operands)
        return [operands]

    @classmethod
    def _coerce_window_operand(
        cls, operand: object
    ) -> tuple[str, frozenset[ExpressionDependency]]:
        if isinstance(operand, TypedExpression):
            return operand.render(), operand.dependencies
        if isinstance(operand, ExpressionDependency):
            column = operand.column_name
            if column is None:
                msg = "Window clauses require column-level dependencies"
                raise ValueError(msg)
            sql = quote_qualified_identifier(column, table=operand.table_name)
            return sql, frozenset({operand})
        if isinstance(operand, str):
            identifier = operand.strip()
            if not identifier:
                msg = "Column references in window clauses cannot be empty"
                raise ValueError(msg)
            dependency = ExpressionDependency.column(identifier)
            sql = quote_identifier(identifier)
            return sql, frozenset({dependency})
        msg = (
            "Window clauses accept column names or typed expressions; "
            f"got {type(operand)!r}"
        )
        raise TypeError(msg)

    @classmethod
    def _coerce_window_order_operand(
        cls, operand: object
    ) -> tuple[str, frozenset[ExpressionDependency]]:
        if isinstance(operand, tuple) and len(operand) == 2:
            expression_operand, direction = operand
            direction_sql = cls._normalise_sort_direction(direction)
            sql, dependencies = cls._coerce_window_operand(expression_operand)
            return f"{sql} {direction_sql}", dependencies
        return cls._coerce_window_operand(operand)

    @staticmethod
    def _normalise_sort_direction(direction: object) -> str:
        if not isinstance(direction, str):
            msg = "Window order direction must be a string"
            raise TypeError(msg)
        normalised = direction.strip().upper()
        if normalised not in {"ASC", "DESC"}:
            msg = "Window order direction must be 'ASC' or 'DESC'"
            raise ValueError(msg)
        return normalised


class AliasedExpression(TypedExpression):
    """Adapter adding an alias to an expression during rendering."""

    __slots__ = ("base", "alias_name")

    def __init__(self, *, base: TypedExpression, alias: str) -> None:
        self.base = base
        self.alias_name = alias
        super().__init__(
            base.render(),
            duck_type=base.duck_type,
            dependencies=base.dependencies,
        )

    def render(self) -> str:
        return f"{self.base.render()} AS {quote_identifier(self.alias_name)}"

    def _coerce_operand(self, other: object) -> TypedExpression:  # type: ignore[override]
        return self.base._coerce_operand(other)  # pylint: disable=protected-access

    def clone_with_sql(
        self,
        sql: str,
        *,
        dependencies: Iterable[DependencyLike],
    ) -> "TypedExpression":
        cloned = self.base.clone_with_sql(sql, dependencies=dependencies)
        return cloned.alias(self.alias_name)

    def over(
        self,
        *,
        partition_by: Iterable[object] | object | None = None,
        order_by: Iterable[object] | object | None = None,
        frame: str | None = None,
    ) -> "TypedExpression":
        windowed = self.base.over(
            partition_by=partition_by,
            order_by=order_by,
            frame=frame,
        )
        return windowed.alias(self.alias_name)


class BooleanExpression(TypedExpression):
    """Boolean expressions support logical composition."""

    __slots__ = ()

    def __init__(
        self,
        sql: str,
        *,
        dependencies: Iterable[DependencyLike] = (),
        duck_type: DuckDBType | None = None,
    ) -> None:
        super().__init__(
            sql,
            duck_type=duck_type or BooleanType("BOOLEAN"),
            dependencies=dependencies,
        )

    def __and__(self, other: object) -> "BooleanExpression":
        operand = self._coerce_operand(other)
        sql = f"({self.render()} AND {operand.render()})"
        dependencies = self.dependencies.union(operand.dependencies)
        return BooleanExpression(sql, dependencies=dependencies)

    def __or__(self, other: object) -> "BooleanExpression":
        operand = self._coerce_operand(other)
        sql = f"({self.render()} OR {operand.render()})"
        dependencies = self.dependencies.union(operand.dependencies)
        return BooleanExpression(sql, dependencies=dependencies)

    def __invert__(self) -> "BooleanExpression":
        return BooleanExpression(f"(NOT {self.render()})", dependencies=self.dependencies)

    def _coerce_operand(self, other: object) -> "BooleanExpression":
        if isinstance(other, BooleanExpression):
            return other
        if isinstance(other, bool):
            sql = "TRUE" if other else "FALSE"
            return BooleanExpression(sql)
        msg = "Boolean expressions only accept other boolean expressions or bool literals"
        raise TypeError(msg)

    @classmethod
    def column(
        cls,
        name: str,
        *,
        table: str | None = None,
    ) -> "BooleanExpression":
        dependency = ExpressionDependency.column(name, table=table)
        return cls(
            quote_qualified_identifier(name, table=table),
            dependencies=(dependency,),
        )

    @classmethod
    def literal(cls, value: bool) -> "BooleanExpression":
        return cls("TRUE" if value else "FALSE")

    @classmethod
    def _raw(
        cls,
        sql: str,
        *,
        dependencies: Iterable[DependencyLike] = (),
    ) -> "BooleanExpression":
        return cls(sql, dependencies=dependencies)


class GenericExpression(TypedExpression):
    """Representation of a DuckDB expression with unknown concrete type."""

    __slots__ = ()

    def __init__(
        self,
        sql: str,
        *,
        duck_type: DuckDBType | None = None,
        dependencies: Iterable[DependencyLike] = (),
    ) -> None:
        super().__init__(
            sql,
            duck_type=duck_type or GenericType("UNKNOWN"),
            dependencies=dependencies,
        )

    def _coerce_operand(self, other: object) -> "GenericExpression":
        if isinstance(other, TypedExpression):
            return GenericExpression(
                other.render(),
                duck_type=other.duck_type,
                dependencies=other.dependencies,
            )
        msg = "Generic expressions only accept other SQL expressions"
        raise TypeError(msg)

    def coalesce(self, *others: object) -> "GenericExpression":
        """Return the first non-null expression from the provided arguments."""

        if not others:
            return self

        operands = [self]
        dependencies = set(self.dependencies)
        for other in others:
            operand = self._coerce_operand(other)
            operands.append(operand)
            dependencies.update(operand.dependencies)

        sql = ", ".join(expression.render() for expression in operands)
        return type(self)(
            f"COALESCE({sql})",
            dependencies=dependencies,
            duck_type=self.duck_type,
        )

    def array_append(self, element: object) -> "GenericExpression":
        """Append ``element`` to the array represented by this expression."""

        namespace = _scalar_generic_namespace()
        return namespace.array_append(self, element)

    def array_intersect(self, other: object) -> "GenericExpression":
        """Return the intersection between this array and ``other``."""

        namespace = _scalar_generic_namespace()
        return namespace.array_intersect(self, other)

    def array_pop_back(self) -> "GenericExpression":
        """Remove the final element from the array expression."""

        namespace = _scalar_generic_namespace()
        return namespace.array_pop_back(self)

    def array_pop_front(self) -> "GenericExpression":
        """Remove the first element from the array expression."""

        namespace = _scalar_generic_namespace()
        return namespace.array_pop_front(self)

    def array_prepend(self, element: object) -> "GenericExpression":
        """Prepend ``element`` to the array represented by this expression."""

        namespace = _scalar_generic_namespace()
        return namespace.array_prepend(element, self)

    def array_push_back(self, element: object) -> "GenericExpression":
        """Push ``element`` onto the end of the array expression."""

        namespace = _scalar_generic_namespace()
        return namespace.array_push_back(self, element)

    def array_push_front(self, element: object) -> "GenericExpression":
        """Push ``element`` onto the front of the array expression."""

        namespace = _scalar_generic_namespace()
        return namespace.array_push_front(self, element)

    def array_reverse(self) -> "GenericExpression":
        """Reverse the order of the array expression."""

        namespace = _scalar_generic_namespace()
        return namespace.array_reverse(self)

    def array_to_string(self, separator: object) -> "VarcharExpression":
        """Join array elements into a string separated by ``separator``."""

        from .text import VarcharExpression as _VarcharExpression

        if isinstance(separator, str):
            separator = _VarcharExpression.coerce_literal(separator)
        namespace = _scalar_varchar_namespace()
        return namespace.array_to_string(self, separator)

    def array_to_string_comma_default(
        self, separator: object
    ) -> "VarcharExpression":
        """Join array elements using ``separator`` with comma fallback."""

        from .text import VarcharExpression as _VarcharExpression

        if isinstance(separator, str):
            separator = _VarcharExpression.coerce_literal(separator)
        namespace = _scalar_varchar_namespace()
        return namespace.array_to_string_comma_default(self, separator)

    @classmethod
    def column(
        cls,
        name: str,
        *,
        table: str | None = None,
    ) -> "GenericExpression":
        dependency = ExpressionDependency.column(name, table=table)
        return cls(
            quote_qualified_identifier(name, table=table),
            dependencies=(dependency,),
        )

    @classmethod
    def _raw(
        cls,
        sql: str,
        *,
        dependencies: Iterable[DependencyLike] = (),
    ) -> "GenericExpression":
        return cls(sql, dependencies=dependencies)

    def max_by(self, order: "TypedExpression") -> "GenericExpression":
        if not isinstance(order, TypedExpression):
            msg = "Generic max_by requires a typed expression for ordering"
            raise TypeError(msg)
        dependencies = self.dependencies.union(order.dependencies)
        sql = f"max_by({self.render()}, {order.render()})"
        return GenericExpression(sql, duck_type=self.duck_type, dependencies=dependencies)
