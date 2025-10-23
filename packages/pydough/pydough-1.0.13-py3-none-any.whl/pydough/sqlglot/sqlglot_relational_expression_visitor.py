"""
Handle the conversion from the Relation Expressions inside
the relation Tree to a single SQLGlot query component.
"""

__all__ = ["SQLGlotRelationalExpressionVisitor"]

import datetime
import warnings
from typing import TYPE_CHECKING

import sqlglot.expressions as sqlglot_expressions
from sqlglot.expressions import Column, Identifier
from sqlglot.expressions import Expression as SQLGlotExpression
from sqlglot.expressions import Literal as SQLGlotLiteral
from sqlglot.expressions import Null as SQLGlotNull
from sqlglot.expressions import Star as SQLGlotStar

import pydough
import pydough.pydough_operators as pydop
from pydough.database_connectors import DatabaseDialect
from pydough.errors import PyDoughSQLException
from pydough.relational import (
    CallExpression,
    ColumnReference,
    CorrelatedReference,
    LiteralExpression,
    RelationalExpression,
    RelationalExpressionVisitor,
    WindowCallExpression,
)
from pydough.types import PyDoughType

from .sqlglot_helpers import normalize_column_name, set_glot_alias
from .transform_bindings import BaseTransformBindings, bindings_from_dialect

if TYPE_CHECKING:
    from .sqlglot_relational_visitor import SQLGlotRelationalVisitor


class SQLGlotRelationalExpressionVisitor(RelationalExpressionVisitor):
    """
    The visitor pattern for creating SQLGlot expressions from
    the relational tree 1 node at a time.
    """

    def __init__(
        self,
        relational_visitor: "SQLGlotRelationalVisitor",
        correlated_names: dict[str, str],
    ) -> None:
        # Keep a stack of SQLGlot expressions so we can build up
        # intermediate results.
        self._stack: list[SQLGlotExpression] = []
        self._dialect: DatabaseDialect = relational_visitor._session.database.dialect
        self._correlated_names: dict[str, str] = correlated_names
        self._relational_visitor: SQLGlotRelationalVisitor = relational_visitor
        self._bindings: BaseTransformBindings = bindings_from_dialect(
            relational_visitor._session.database.dialect,
            relational_visitor._session.config,
            self._relational_visitor,
        )

    def reset(self) -> None:
        """
        Reset just clears our stack.
        """
        self._stack = []

    def visit_call_expression(self, call_expression: CallExpression) -> None:
        # Visit the inputs in reverse order so we can pop them off in order.
        for arg in reversed(call_expression.inputs):
            arg.accept(self)
        input_exprs: list[SQLGlotExpression] = [
            self._stack.pop() for _ in range(len(call_expression.inputs))
        ]
        input_types: list[PyDoughType] = [
            arg.data_type for arg in call_expression.inputs
        ]
        try:
            output_expr: SQLGlotExpression = self._bindings.convert_call_to_sqlglot(
                call_expression.op, input_exprs, input_types
            )
        except Exception as e:
            raise pydough.active_session.error_builder.sql_call_conversion_error(
                call_expression, e
            )
        self._stack.append(output_expr)

    @staticmethod
    def get_window_spec(
        kwargs: dict[str, object],
    ) -> sqlglot_expressions.WindowSpec | None:
        """
        Parses the keyword arguments to a window function to extract the window
        frame (if there is one). If `cumulative` is provided as a keyword
        argument and its value is True, the cumulative window frame (UNBOUNDED
        PRECEDING TO CURRENT ROW) is used. If `frame` is provided, it is
        expected to be a tuple of two values (lower, upper) which can be
        integers or None. These bounds have the following meaning:
        - None: `UNBOUNDED PRECEDING` (for lower) or `UNBOUNDED FOLLOWING` (for
        upper)
        - Zero: `CURRENT ROW`
        - `+N`: `N FOLLOWING`
        - `-N`: `N PRECEDING`

        Args:
            `kwargs`: The keyword arguments to parse, which may include a
            `frame` argument or a `cumulative` argument. It is assumed the
            keyword arguments are the correct types/formats.

        Returns:
            The window specification if applicable, otherwise None.
        """
        lower: int | None = None
        upper: int | None = None
        if kwargs.get("cumulative", False):
            # If cumulative=True, that is the same as the frame (None, 0)
            lower, upper = None, 0

        elif "frame" in kwargs:
            # If frame is provided, parse it to extract the lower and upper bounds
            # which are assumed to be correctly formatted
            frame = kwargs["frame"]
            assert isinstance(frame, tuple) and len(frame) == 2
            lower_raw, upper_raw = frame[0], frame[1]
            assert isinstance(lower_raw, (int, type(None))) and isinstance(
                upper_raw, (int, type(None))
            )
            lower, upper = lower_raw, upper_raw

        else:
            # Otherwise, the frame is from unbounded preceding to unbounded following.
            lower = upper = None

        spec_args: dict[str, str] = {"kind": "ROWS"}

        # Build the spec for the lower bound, where the `start` argument
        # is the magnitude of the lower value of the frame (or `CURRENT ROW` if
        # `0`) and the `start_side` indicates whether it is `PRECEDING` or
        # `FOLLOWING`.
        if lower is None:
            spec_args["start"] = "UNBOUNDED"
            spec_args["start_side"] = "PRECEDING"
        else:
            if lower == 0:
                spec_args["start"] = "CURRENT ROW"
            elif lower > 0:
                spec_args["start"] = str(lower)
                spec_args["start_side"] = "FOLLOWING"
            else:
                spec_args["start"] = str(abs(lower))
                spec_args["start_side"] = "PRECEDING"

        # Build the spec for the upper bound, where the `end` argument
        # is the magnitude of the upper value of the frame (or `CURRENT ROW` if
        # `0`) and the `end_side` indicates whether it is `PRECEDING` or
        # `FOLLOWING`.
        if upper is None:
            spec_args["end"] = "UNBOUNDED"
            spec_args["end_side"] = "FOLLOWING"
        else:
            if upper == 0:
                spec_args["end"] = "CURRENT ROW"
            elif upper > 0:
                spec_args["end"] = str(upper)
                spec_args["end_side"] = "FOLLOWING"
            else:
                spec_args["end"] = str(abs(upper))
                spec_args["end_side"] = "PRECEDING"

        # Combine the spec values to return the SQLGlot WindowSpec value
        return sqlglot_expressions.WindowSpec(**spec_args)

    def visit_window_expression(self, window_expression: WindowCallExpression) -> None:
        # Visit the inputs in reverse order so we can pop them off in order.
        for arg in reversed(window_expression.inputs):
            arg.accept(self)
        arg_exprs: list[SQLGlotExpression] = [
            self._stack.pop() for _ in range(len(window_expression.inputs))
        ]
        # Do the same with the partition expressions.
        for arg in reversed(window_expression.partition_inputs):
            arg.accept(self)
        partition_exprs: list[SQLGlotExpression] = [
            self._stack.pop() for _ in range(len(window_expression.partition_inputs))
        ]
        # Do the same with the order
        order_exprs: list[SQLGlotExpression] = []
        for order_arg in window_expression.order_inputs:
            order_arg.expr.accept(self)
            glot_expr: SQLGlotExpression = self._stack.pop()
            # Skip ordering keys that are literals or NULL.
            if isinstance(glot_expr, (SQLGlotLiteral, SQLGlotNull)):
                continue
            # Invoke the binding's conversion for ordering arguments to
            # postprocess as needed (e.g. adding collations).
            # For example, when a string column is sorted in MySQL, we add
            # collations
            glot_expr = self._bindings.convert_ordering(
                glot_expr, order_arg.expr.data_type
            )
            # Ignore non-default na first/last positions for SQLite dialect
            na_first: bool
            if self._dialect == DatabaseDialect.SQLITE:
                if order_arg.ascending:
                    if not order_arg.nulls_first:
                        warnings.warn(
                            "PyDough when using SQLITE dialect does not support ascending ordering with nulls last (changed to nulls first)"
                        )
                    na_first = True
                else:
                    if order_arg.nulls_first:
                        warnings.warn(
                            "PyDough when using SQLITE dialect does not support ascending ordering with nulls first (changed to nulls last)"
                        )
                    na_first = False
            else:
                na_first = order_arg.nulls_first
            if order_arg.ascending:
                glot_expr = glot_expr.asc(nulls_first=na_first)
            else:
                glot_expr = glot_expr.desc(nulls_first=na_first)
            order_exprs.append(glot_expr)
        # Special case: if we removed all of the order inputs, but the window
        # call originally had an order, add `ORDER BY 1` as a placeholder.
        if len(window_expression.order_inputs) > 0 and len(order_exprs) == 0:
            order_exprs.append(sqlglot_expressions.convert("1"))
        this: SQLGlotExpression
        window_spec: sqlglot_expressions.WindowSpec | None = None
        input_types: list[PyDoughType] = [
            arg.data_type for arg in window_expression.inputs
        ]
        match window_expression.op.function_name:
            case "PERCENTILE":
                # Extract the number of buckets to use for the percentile
                # operation (default is 100).
                n_buckets = window_expression.kwargs.get("n_buckets", 100)
                assert isinstance(n_buckets, int)
                this = sqlglot_expressions.Anonymous(
                    this="NTILE", expressions=[sqlglot_expressions.convert(n_buckets)]
                )
            case "RANKING":
                if window_expression.kwargs.get("allow_ties", False):
                    if window_expression.kwargs.get("dense", False):
                        this = sqlglot_expressions.Anonymous(this="DENSE_RANK")
                    else:
                        this = sqlglot_expressions.Anonymous(this="RANK")
                else:
                    this = sqlglot_expressions.RowNumber()
            case "PREV" | "NEXT":
                offset = window_expression.kwargs.get("n", 1)
                if not isinstance(offset, int):
                    raise PyDoughSQLException(
                        f"Invalid 'n' argument to {window_expression.op.function_name}: {offset!r} (expected an integer)"
                    )
                # By default, we use the LAG function. If doing NEXT, switch
                # to LEAD. If the offset is negative, switch again.
                func, other_func = sqlglot_expressions.Lag, sqlglot_expressions.Lead
                if window_expression.op.function_name == "NEXT":
                    func, other_func = other_func, func
                if offset < 0:
                    offset *= -1
                    func, other_func = other_func, func
                lag_args: dict[str, SQLGlotExpression] = {}
                lag_args["this"] = arg_exprs[0]
                lag_args["offset"] = sqlglot_expressions.convert(offset)
                if "default" in window_expression.kwargs:
                    lag_args["default"] = sqlglot_expressions.convert(
                        window_expression.kwargs.get("default")
                    )
                this = func(**lag_args)
            case "RELSUM":
                this = self._bindings.convert_call_to_sqlglot(
                    pydop.SUM, arg_exprs, input_types
                )
                window_spec = self.get_window_spec(window_expression.kwargs)
            case "RELAVG":
                this = sqlglot_expressions.Avg.from_arg_list(arg_exprs)
                window_spec = self.get_window_spec(window_expression.kwargs)
            case "RELCOUNT":
                this = sqlglot_expressions.Count.from_arg_list(arg_exprs)
                window_spec = self.get_window_spec(window_expression.kwargs)
            case "RELSIZE":
                this = sqlglot_expressions.Count.from_arg_list([SQLGlotStar()])
                window_spec = self.get_window_spec(window_expression.kwargs)
            case _ if isinstance(
                window_expression.op, pydop.SqlWindowAliasExpressionFunctionOperator
            ):
                this = sqlglot_expressions.Anonymous(
                    this=window_expression.op.sql_function_alias, expressions=arg_exprs
                )
                if window_expression.op.allows_frame:
                    window_spec = self.get_window_spec(window_expression.kwargs)
            case _:
                raise NotImplementedError(
                    f"Window operator {window_expression.op.function_name} not supported"
                )
        window_args: dict[str, object] = {"this": this}
        if partition_exprs:
            window_args["partition_by"] = partition_exprs
        if order_exprs:
            window_args["order"] = sqlglot_expressions.Order(
                this=None, expressions=order_exprs
            )
            if window_spec is not None:
                window_args["spec"] = window_spec
        self._stack.append(sqlglot_expressions.Window(**window_args))

    def visit_literal_expression(self, literal_expression: LiteralExpression) -> None:
        # Note: This assumes each literal has an associated type that can be parsed
        # and types do not represent implicit casts.
        literal: SQLGlotExpression
        if isinstance(literal_expression.value, (tuple, list)):
            # If the literal is a list or tuple, convert each element
            # individually and create an array literal.
            elements: list[SQLGlotExpression] = []
            for element in literal_expression.value:
                element_expr: SQLGlotExpression
                if isinstance(element, RelationalExpression):
                    element.accept(self)
                    element_expr = self._stack.pop()
                else:
                    element_expr = sqlglot_expressions.convert(element)
                elements.append(element_expr)
            literal = sqlglot_expressions.Array(expressions=elements)
        else:
            literal = sqlglot_expressions.convert(literal_expression.value)

        # Special handling: insert cast calls for ansi casting of date/time
        # instead of relying on SQLGlot conversion functions. This is because
        # the default handling in SQLGlot without a dialect is to produce a
        # nonsensical TIME_STR_TO_TIME or DATE_STR_TO_DATE function which each
        # specific dialect is responsible for translating into its own logic.
        # Rather than have that logic show up in the ANSI sql text, we will
        # instead create the CAST calls ourselves.
        if self._dialect == DatabaseDialect.ANSI:
            if isinstance(literal_expression.value, datetime.date):
                date: datetime.date = literal_expression.value
                literal = sqlglot_expressions.Cast(
                    this=sqlglot_expressions.convert(date.strftime("%Y-%m-%d")),
                    to=sqlglot_expressions.DataType.build("DATE"),
                )
            if isinstance(literal_expression.value, datetime.datetime):
                dt: datetime.datetime = literal_expression.value
                if dt.tzinfo is not None:
                    raise PyDoughSQLException(
                        "PyDough does not yet support datetime values with a timezone"
                    )
                literal = sqlglot_expressions.Cast(
                    this=sqlglot_expressions.convert(dt.isoformat(sep=" ")),
                    to=sqlglot_expressions.DataType.build("TIMESTAMP"),
                )
        self._stack.append(literal)

    def visit_correlated_reference(
        self, correlated_reference: CorrelatedReference
    ) -> None:
        full_name: str = f"{self._correlated_names[correlated_reference.correl_name]}.{correlated_reference.name}"
        self._stack.append(Identifier(this=full_name, quoted=False))

    @staticmethod
    def make_sqlglot_column(
        column_reference: ColumnReference,
    ) -> Column:
        """
        Generate an identifier for a column reference. This is split into a
        separate static method to ensure consistency across multiple visitors.
        Args:
            `column_reference`: The column reference to generate an identifier
            for.
        Returns:
            The output identifier.
        """
        assert column_reference.name is not None
        column_name: str = column_reference.name
        quoted, column_name = normalize_column_name(column_name)

        column_ident: Column = Identifier(this=column_name, quoted=quoted)

        if column_reference.input_name is not None:
            table_ident = Identifier(this=column_reference.input_name, quoted=False)
            return Column(this=column_ident, table=table_ident)

        return column_ident

    def visit_column_reference(self, column_reference: ColumnReference) -> None:
        self._stack.append(self.make_sqlglot_column(column_reference))

    def relational_to_sqlglot(
        self, expr: RelationalExpression, output_name: str | None = None
    ) -> SQLGlotExpression:
        """
        Interface to convert an entire relational expression to a SQLGlot expression
        and assign it the given alias.

        Args:
            `expr`: The relational expression to convert.
            `output_name`: The name to assign to the final SQLGlot expression
                or None if we should omit any alias.

        Returns:
            The final SQLGlot expression representing the entire
                relational tree.
        """
        self.reset()
        expr.accept(self)
        result = self.get_sqlglot_result()
        return set_glot_alias(result, output_name)

    def get_sqlglot_result(self) -> SQLGlotExpression:
        """
        Interface to get the current SQLGlot expression result based on the current state.

        Returns:
            The SQLGlot expression representing the tree we have already
                visited.
        """
        assert len(self._stack) == 1, "Expected exactly one expression on the stack"
        return self._stack[0]
