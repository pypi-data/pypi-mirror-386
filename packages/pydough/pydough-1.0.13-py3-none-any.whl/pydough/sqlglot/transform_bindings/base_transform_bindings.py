"""
Definition of binding infrastructure that maps PyDough operators to
implementations of how to convert them to SQLGlot expressions
"""

__all__ = ["BaseTransformBindings"]

import re
from typing import TYPE_CHECKING

import sqlglot.expressions as sqlglot_expressions
from sqlglot import parse_one
from sqlglot.expressions import Concat
from sqlglot.expressions import Expression as SQLGlotExpression

import pydough.pydough_operators as pydop
from pydough.configs import DayOfWeek, PyDoughConfigs
from pydough.errors import PyDoughSQLException
from pydough.types import BooleanType, NumericType, PyDoughType, StringType

from .sqlglot_transform_utils import (
    DateTimeUnit,
    apply_parens,
    current_ts_pattern,
    offset_pattern,
    pad_helper,
    positive_index,
    trunc_pattern,
)

if TYPE_CHECKING:
    from pydough.sqlglot.sqlglot_relational_visitor import SQLGlotRelationalVisitor


class BaseTransformBindings:
    """
    The base class for converting function calls from relational expressions
    into the SQLGlot AST. This class is used for generic ANSI SQL, while
    subclasses can override its methods to provide dialect-specific changes.
    """

    def __init__(self, configs: PyDoughConfigs, visitor: "SQLGlotRelationalVisitor"):
        self._configs = configs
        self._visitor = visitor

    @property
    def configs(self) -> PyDoughConfigs:
        """
        The PyDough configuration settings used during the SQLGlot conversion.
        """
        return self._configs

    @property
    def dialect_start_of_week(self) -> DayOfWeek:
        """
        Which day of the week is considered the start of the week within the
        SQL dialect. Individual dialects may override this.
        """
        return DayOfWeek.SUNDAY

    @property
    def start_of_week_offset(self) -> int:
        """
        The number of days to add to the start of the week within the
        SQL dialect to obtain the start of week referenced by the configs.
        """
        dows: list[DayOfWeek] = list(DayOfWeek)
        dialect_index: int = dows.index(self.dialect_start_of_week)
        config_index: int = dows.index(self.configs.start_of_week)
        return (config_index - dialect_index) % 7

    @property
    def dialect_dow_mapping(self) -> dict[str, int]:
        """
        A mapping of each day of week string to its corresponding integer value
        in the dialect when converted to a day of week.
        """
        return {
            "Sunday": 0,
            "Monday": 1,
            "Tuesday": 2,
            "Wednesday": 3,
            "Thursday": 4,
            "Friday": 5,
            "Saturday": 6,
        }

    standard_func_bindings: dict[
        pydop.PyDoughExpressionOperator, sqlglot_expressions.Func
    ] = {
        pydop.AVG: sqlglot_expressions.Avg,
        pydop.MIN: sqlglot_expressions.Min,
        pydop.MAX: sqlglot_expressions.Max,
        pydop.ANYTHING: sqlglot_expressions.AnyValue,
        pydop.MEDIAN: sqlglot_expressions.Median,
        pydop.LOWER: sqlglot_expressions.Lower,
        pydop.UPPER: sqlglot_expressions.Upper,
        pydop.LENGTH: sqlglot_expressions.Length,
        pydop.ABS: sqlglot_expressions.Abs,
        pydop.DEFAULT_TO: sqlglot_expressions.Coalesce,
        pydop.POWER: sqlglot_expressions.Pow,
        pydop.IFF: sqlglot_expressions.If,
    }
    """
    A mapping of PyDough function operators to SQLGlot function expressions.
    The functions in these mappings can be invoked by simply invoking the
    `from_arg_list` method to create a function call instance from their
    arguments.
    """

    standard_binop_bindings: dict[
        pydop.PyDoughExpressionOperator, sqlglot_expressions.Func
    ] = {
        pydop.ADD: sqlglot_expressions.Add,
        pydop.SUB: sqlglot_expressions.Sub,
        pydop.MUL: sqlglot_expressions.Mul,
        pydop.DIV: sqlglot_expressions.Div,
        pydop.POW: sqlglot_expressions.Pow,
        pydop.BAN: sqlglot_expressions.And,
        pydop.BOR: sqlglot_expressions.Or,
        pydop.EQU: sqlglot_expressions.EQ,
        pydop.GRT: sqlglot_expressions.GT,
        pydop.GEQ: sqlglot_expressions.GTE,
        pydop.LEQ: sqlglot_expressions.LTE,
        pydop.LET: sqlglot_expressions.LT,
        pydop.NEQ: sqlglot_expressions.NEQ,
    }
    """
    Variant of `standard_func_bindings` for binary operators which have a
    slightly different (yet still mass-reproducible) pattern of invocation.
    """

    def convert_call_to_sqlglot(
        self,
        operator: pydop.PyDoughExpressionOperator,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """
        The main procedure for converting relational function calls to SQLGlot
        AST expressions.

        Args:
            `operator`: the PyDough operator of the function call being
            transformed into SQLGlot.
            `args`: The arguments to the arguments of the function call,
            already translated from relational expressions to SQLGlot AST
            expressions.
            `types`: The PyDough types of the arguments to the function call.

        Returns:
            The SQLGlot expression corresponding to invoking `operator` on the
            provided arguments.
        """
        func: sqlglot_expressions.Func
        if operator in self.standard_func_bindings:
            func = self.standard_func_bindings[operator]
            return func.from_arg_list(args)
        if operator in self.standard_binop_bindings:
            assert len(args) >= 2
            func = self.standard_binop_bindings[operator]
            # Note: SQLGlot explicit inserts parentheses for binary operations
            # during parsing.
            output_expr: SQLGlotExpression = apply_parens(args[0])
            for arg in args[1:]:
                # Build the expressions on the left since the operator is left-associative.
                output_expr = func(this=output_expr, expression=apply_parens(arg))
            return output_expr
        if isinstance(operator, pydop.SqlAliasExpressionFunctionOperator):
            # For user defined operators that are a 1:1 alias of a function in
            # the SQL dialect, map to a call of the corresponding function.
            return sqlglot_expressions.Anonymous(
                this=operator.sql_function_alias, expressions=args
            )
        if isinstance(
            operator,
            (
                pydop.MaskedExpressionFunctionOperator,
                pydop.SqlMacroExpressionFunctionOperator,
            ),
        ):
            # For user defined operators that are a macro for SQL text, convert
            # the arguments to SQL text strings then inject them into the macro
            # as a format string, then re-parse it. The same idea works for the
            # masking/unmasking operators
            arg_strings: list[str] = [arg.sql() for arg in args]
            fmt_string: str
            if isinstance(operator, pydop.MaskedExpressionFunctionOperator):
                fmt_string = operator.format_string
            else:
                fmt_string = operator.macro_text
            combined_string: str = fmt_string.format(*arg_strings)
            return parse_one(combined_string)
        match operator:
            case pydop.NOT:
                return sqlglot_expressions.Not(this=args[0])
            case pydop.NDISTINCT:
                return sqlglot_expressions.Count(
                    this=sqlglot_expressions.Distinct(expressions=[args[0]])
                )
            case pydop.STARTSWITH:
                return self.convert_startswith(args, types)
            case pydop.ENDSWITH:
                return self.convert_endswith(args, types)
            case pydop.CONTAINS:
                return self.convert_contains(args, types)
            case pydop.LIKE:
                return self.convert_like(args, types)
            case pydop.SLICE:
                return self.convert_slice(args, types)
            case pydop.JOIN_STRINGS:
                return self.convert_join_strings(args, types)
            case pydop.LPAD:
                return self.convert_lpad(args, types)
            case pydop.RPAD:
                return self.convert_rpad(args, types)
            case pydop.FIND:
                return self.convert_find(args, types)
            case pydop.STRIP:
                return self.convert_strip(args, types)
            case pydop.REPLACE:
                return self.convert_replace(args, types)
            case pydop.STRCOUNT:
                return self.convert_str_count(args, types)
            case pydop.SIGN:
                return self.convert_sign(args, types)
            case pydop.ROUND:
                return self.convert_round(args, types)
            case pydop.SUM:
                return self.convert_sum(args, types)
            case pydop.CEIL:
                return self.convert_ceil(args, types)
            case pydop.FLOOR:
                return self.convert_floor(args, types)
            case pydop.ISIN:
                return self.convert_isin(args, types)
            case pydop.PRESENT:
                return self.convert_present(args, types)
            case pydop.ABSENT:
                return self.convert_absent(args, types)
            case pydop.KEEP_IF:
                return self.convert_keep_if(args, types)
            case pydop.MONOTONIC:
                return self.convert_monotonic(args, types)
            case pydop.SQRT:
                return self.convert_sqrt(args, types)
            case pydop.POPULATION_VAR:
                return self.convert_variance(args, types, "population")
            case pydop.SAMPLE_VAR:
                return self.convert_variance(args, types, "sample")
            case pydop.POPULATION_STD:
                return self.convert_std(args, types, "population")
            case pydop.SAMPLE_STD:
                return self.convert_std(args, types, "sample")
            case pydop.YEAR:
                return self.convert_extract_datetime(args, types, DateTimeUnit.YEAR)
            case pydop.MONTH:
                return self.convert_extract_datetime(args, types, DateTimeUnit.MONTH)
            case pydop.QUARTER:
                return self.convert_extract_datetime(args, types, DateTimeUnit.QUARTER)
            case pydop.DAY:
                return self.convert_extract_datetime(args, types, DateTimeUnit.DAY)
            case pydop.HOUR:
                return self.convert_extract_datetime(args, types, DateTimeUnit.HOUR)
            case pydop.MINUTE:
                return self.convert_extract_datetime(args, types, DateTimeUnit.MINUTE)
            case pydop.SECOND:
                return self.convert_extract_datetime(args, types, DateTimeUnit.SECOND)
            case pydop.DATEDIFF:
                return self.convert_datediff(args, types)
            case pydop.DATETIME:
                return self.convert_datetime(args, types)
            case pydop.DAYOFWEEK:
                return self.convert_dayofweek(args, types)
            case pydop.DAYNAME:
                return self.convert_dayname(args, types)
            case pydop.INTEGER:
                return self.convert_integer(args, types)
            case pydop.FLOAT:
                return self.convert_float(args, types)
            case pydop.STRING:
                return self.convert_string(args, types)
            case pydop.SMALLEST:
                return self.convert_smallest_or_largest(args, types, False)
            case pydop.LARGEST:
                return self.convert_smallest_or_largest(args, types, True)
            case pydop.COUNT:
                return self.convert_count(args, types)
            case pydop.GETPART:
                return self.convert_get_part(args, types)
            case pydop.QUANTILE:
                return self.convert_quantile(args, types)
            case _:
                raise NotImplementedError(
                    f"Operator '{operator.function_name}' is unsupported with this database dialect."
                )

    def make_datetime_arg(self, expr: SQLGlotExpression) -> SQLGlotExpression:
        """
        Converts a SQLGlot expression to a datetime argument, if needed, including:
        - Converting a string literal for "now" or similar aliases into a call to
        get the current timestamp.
        - Converting a string literal for a datetime into a datetime expression.
        """
        if isinstance(expr, sqlglot_expressions.Literal) and expr.is_string:
            return self.handle_datetime_base_arg(expr)
        return expr

    def convert_sum(
        self, args: SQLGlotExpression, types: list[PyDoughType]
    ) -> SQLGlotExpression:
        """
        Converts a SUM function call to its SQLGlot equivalent.
        """
        return sqlglot_expressions.Sum.from_arg_list(args)

    def convert_find(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """
        Support for getting the index of the first occurrence of a substring
        within a string. The first argument is the string to search within,
        and the second argument is the substring to search for.

        Args:
            `args`: The operands to `FIND`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `FIND`.

        Returns:
            The SQLGlot expression matching the functionality of `FIND`
            by looking up the location and subtracting 1 so it is 0-indexed.
        """

        assert len(args) == 2
        answer: SQLGlotExpression = sqlglot_expressions.Sub(
            this=sqlglot_expressions.StrPosition(this=args[0], substr=args[1]),
            expression=sqlglot_expressions.Literal.number(1),
        )
        return answer

    def convert_strip(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """
        Support for removing all leading and trailing whitespace from a string.
        If a second argument is provided, it is used as the set of characters
        to remove from the leading and trailing ends of the first argument.

        Args:
            `args`: The operands to `STRIP`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `STRIP`.

        Returns:
        The SQLGlot expression matching the functionality of `STRIP(X, Y)`.
        In Python, this is equivalent to `X.strip(Y)`.
        """
        assert 1 <= len(args) <= 2
        to_strip: SQLGlotExpression = args[0]
        strip_char_glot: SQLGlotExpression
        if len(args) == 1:
            strip_char_glot = sqlglot_expressions.Literal.string("\n\t ")
        else:
            strip_char_glot = args[1]
        return sqlglot_expressions.Trim(
            this=to_strip,
            expression=strip_char_glot,
        )

    def convert_replace(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """Convert a `REPLACE` call expression to a SQLGlot expression.

        Args:
            `args` The operands to `REPLACE`, after they were
            converted to SQLGlot expressions.
            `types` The PyDough types of the arguments to `REPLACE`.

        Returns:
            The SQLGlot expression matching
            the functionality of `REPLACE`.
            In Python, this is equivalent to `X.replace(Y, Z)`.
        """
        assert 2 <= len(args) <= 3
        if len(args) == 2:
            # If only two arguments are provided, the third argument is set to an empty string
            args.append(sqlglot_expressions.Literal.string(""))
        return sqlglot_expressions.Anonymous(this="REPLACE", expressions=args)

    def convert_str_count(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """Convert a `STRCOUNT` call expression to a SQLGlot expression.
        It counts how many times the string Y appears in the string X.

        STRCOUNT(X, Y) =>
        CASE
            WHEN LENGTH(Y) = 0 THEN 0
            ELSE
            CAST((LENGTH(X) - LENGTH(REPLACE(X, Y, ''))) / LENGTH(Y), AS INTEGER)
        END

        Args:
            `args` The operands to `STRCOUNT`, after
            they were converted to SQLGlot expressions.
            `types` The PyDough types of the arguments to
            `STRCOUNT`.

        Returns:
            The SQLGlot expression matching
            the functionality of `STRCOUNT`.
            In Python, this is equivalent to `X.count(Y)`.
        """
        assert len(args) == 2

        string: SQLGlotExpression = args[0]
        substring_count: SQLGlotExpression = args[1]

        # eliminate the substring of the string: REPLACE(X, Y, "")
        string_replaced: SQLGlotExpression = self.convert_replace(
            [string, substring_count], types
        )

        # The length of the first string given: LENGH(X)
        len_string: SQLGlotExpression = sqlglot_expressions.Length(this=string)

        # The length of the replaced string: LENGH(REPLACE(X, Y, ""))
        len_string_replaced: SQLGlotExpression = sqlglot_expressions.Length(
            this=string_replaced
        )

        # The length of the Y string: LENGTH(Y)
        len_substring_count: SQLGlotExpression = sqlglot_expressions.Length(
            this=substring_count
        )

        # The length difference between string X and
        # replaced string: REPLACE(X, Y, "")
        difference: SQLGlotExpression = sqlglot_expressions.Sub(
            this=len_string, expression=len_string_replaced
        )

        # Take in count if LENGH(Y) > 1 dividing the difference by Y's length:
        # LENGTH(X) - LENGTH(REPLACE(X, Y, ''))) / LENGTH(Y)
        quotient: SQLGlotExpression = sqlglot_expressions.Div(
            this=apply_parens(difference), expression=len_substring_count
        )

        # Cast to Interger:
        # CAST((LENGTH(X) - LENGTH(REPLACE(X, Y, ''))) / LENGTH(Y), AS INTEGER)
        casted: SQLGlotExpression = sqlglot_expressions.Cast(
            this=quotient, to=sqlglot_expressions.DataType.build("BIGINT")
        )

        # CASE when LENGH(Y) == 0 THEN 0 else casted
        answer: SQLGlotExpression = (
            sqlglot_expressions.Case()
            .when(
                sqlglot_expressions.EQ(
                    this=len_substring_count,
                    expression=sqlglot_expressions.Literal.number(0),
                ),
                sqlglot_expressions.Literal.number(0),
            )
            .else_(casted)
        )

        return answer

    def convert_startswith(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """
        Convert a `STARTSWITH` call expression to a SQLGlot expression. This
        is done because SQLGlot does not automatically convert `STARTSWITH`
        to a LIKE expression for SQLite.

        Args:
            `args`: The operands to `STARTSWITH`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `STARTSWITH`.

        Returns:
            The SQLGlot expression matching the functionality of `STARTSWITH`
            by using `LIKE` where the pattern is the original STARTSWITH string,
            prepended with `'%'`.
        """
        column: SQLGlotExpression = args[0]
        pattern: SQLGlotExpression = self.convert_concat(
            [args[1], sqlglot_expressions.convert("%")],
            [types[1], StringType()],
        )
        return self.convert_like([column, pattern], types)

    def convert_endswith(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """
        Convert a `ENDSWITH` call expression to a SQLGlot expression. This
        is done because SQLGlot does not automatically convert `ENDSWITH`
        to a LIKE expression for SQLite.

        Args:
            `args`: The operands to `ENDSWITH`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `ENDSWITH`.

        Returns:
            The SQLGlot expression matching the functionality of `ENDSWITH`
            by using `LIKE` where the pattern is the original ENDSWITH string,
            prepended with `'%'`.
        """
        column: SQLGlotExpression = args[0]
        pattern: SQLGlotExpression = self.convert_concat(
            [sqlglot_expressions.convert("%"), args[1]], [StringType(), types[1]]
        )
        return self.convert_like([column, pattern], types)

    def convert_contains(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """
        Convert a `CONTAINS` call expression to a SQLGlot expression. This
        is done because SQLGlot does not automatically convert `CONTAINS`
        to a LIKE expression for SQLite.

        Args:
            `args`: The operands to `CONTAINS`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `CONTAINS`.

        Returns:
            The SQLGlot expression matching the functionality of `CONTAINS`
            by using `LIKE` where the pattern is the original contains string,
            sandwiched between `'%'` on either side.
        """
        # TODO: (gh #170) update to a different transformation for array/map containment
        column: SQLGlotExpression = args[0]
        pattern: SQLGlotExpression = self.convert_concat(
            [
                sqlglot_expressions.convert("%"),
                args[1],
                sqlglot_expressions.convert("%"),
            ],
            [StringType(), types[1], StringType()],
        )
        return self.convert_like([column, pattern], types)

    def convert_slice(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """
        Support for generating a `SLICE` expression from a list of arguments.
        It is expected that there are exactly four arguments:
        - The first argument is the string to slice.
        - The second argument is the `start` index.
        - The third argument is the `stop` index.
        - The fourth argument is the `step`.

        Outline of the logic:
        - Case 1: `(None, None)`
            - Returns the string as is.
        - Case 2: `(start, None)`
            - Positive `start`: Convert to 1-based indexing and slice from `start`.
            - Negative `start`: Compute `LENGTH(string) + start + 1`; clamp to `1` if less than `1`.
        - Case 3: `(None, stop)`
            - Positive `stop`: Slice from position `1` to `stop`.
            - Negative `stop`: Compute `LENGTH(string) + stop`; clamp to `0` if less than `0` (empty slice).
        - Case 4: `(start, stop)`
            - 1. Both `start` & `stop` >= 0:
                - Convert `start` to 1-based.
                - Set `length = stop - start`.
            - 2. `start < 0`, `stop >= 0`:
                - Convert `start` to 1 based index. If < 1, set to 1.
                - Compute `length = stop - start` (clamp to 0 if negative).
            - 3. `start >= 0`, `stop < 0`:
                - Convert `stop` & `start` to 1 based index.
                - If `stop` < 1, slice is empty (`length = 0`).
                - Else, `length = stop - start`.
            - 4. `start < 0`, `stop < 0`:
                - Convert `start` & `stop` to 1 based index. If `start` < 1, set to 1.
                - If `stop` < 1, slice is empty (`length = 0`).
                - Else, `length = stop - start`.

        Args:
            `args`: The operands to `SLICE`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `SLICE`.

        Returns:
            The SQLGlot expression matching the functionality of Python based string slicing
            with the caveat that it only supports a step of 1.
        """
        assert len(args) == 4
        string_expr, start, stop, step = args

        start_idx: int | None = None
        if not isinstance(start, sqlglot_expressions.Null):
            if isinstance(start, sqlglot_expressions.Literal):
                try:
                    start_idx = int(start.this)
                except ValueError:
                    raise PyDoughSQLException(
                        "SLICE function currently only supports the start index being integer literal or absent."
                    )
            else:
                raise PyDoughSQLException(
                    "SLICE function currently only supports the start index being integer literal or absent."
                )

        stop_idx: int | None = None
        if not isinstance(stop, sqlglot_expressions.Null):
            if isinstance(stop, sqlglot_expressions.Literal):
                try:
                    stop_idx = int(stop.this)
                except ValueError:
                    raise PyDoughSQLException(
                        "SLICE function currently only supports the stop index being integer literal or absent."
                    )
            else:
                raise PyDoughSQLException(
                    "SLICE function currently only supports the stop index being integer literal or absent."
                )

        step_idx: int | None = None
        if not isinstance(step, sqlglot_expressions.Null):
            if isinstance(step, sqlglot_expressions.Literal):
                try:
                    step_idx = int(step.this)
                    if step_idx != 1:
                        raise PyDoughSQLException(
                            "SLICE function currently only supports the step being integer literal 1 or absent."
                        )
                except ValueError:
                    raise PyDoughSQLException(
                        "SLICE function currently only supports the step being integer literal 1 or absent."
                    )
            else:
                raise PyDoughSQLException(
                    "SLICE function currently only supports the step being integer literal 1 or absent."
                )

        # SQLGlot expressions for 0 and 1 and empty string
        sql_zero = sqlglot_expressions.convert(0)
        sql_one = sqlglot_expressions.convert(1)
        sql_empty_str = sqlglot_expressions.convert("")

        match (start_idx, stop_idx):
            case (None, None):
                return string_expr
            case (_, None):
                assert start_idx is not None
                if start_idx > 0:
                    return sqlglot_expressions.Substring(
                        this=string_expr,
                        start=sqlglot_expressions.convert(start_idx + 1),
                    )
                else:
                    # Calculate the positive index equivalent for the negative index
                    # e.g., for string "hello" and index -2, converts to index 4 (LENGTH("hello") + (-2) + 1)
                    start_idx_glot = positive_index(string_expr, start_idx)

                    # Create a SUBSTRING expression with adjusted start position
                    answer = sqlglot_expressions.Substring(
                        this=string_expr,  # The original string to slice
                        start=self.convert_iff_case(
                            [
                                # Check if the calculated positive index is less than 1
                                sqlglot_expressions.LT(
                                    this=start_idx_glot, expression=sql_one
                                ),
                                sql_one,  # If true, use index 1 (start from beginning)
                                start_idx_glot,  # If false, use the calculated positive index
                            ],
                            [BooleanType(), NumericType(), NumericType()],
                        ),
                    )
                    return answer
            case (None, _):
                assert stop_idx is not None
                if stop_idx > 0:
                    return sqlglot_expressions.Substring(
                        this=string_expr,
                        start=sql_one,
                        length=sqlglot_expressions.convert(stop_idx),
                    )
                else:
                    # Convert negative stop index to positive index
                    # For example, with string "hello" and stop_idx=-2:
                    # LENGTH("hello") + (-2) = 3 when is_zero_based=True
                    # No +1 adjustment needed since we're using 0-based indexing
                    # to calculate the length, of which the higher bound is exclusive.
                    stop_idx_glot = positive_index(string_expr, stop_idx, True)

                    # Create a SUBSTRING expression that starts from beginning
                    return sqlglot_expressions.Substring(
                        this=string_expr,  # The original string to slice
                        start=sql_one,  # Always start from position 1
                        length=self.convert_iff_case(
                            [
                                # Check if the calculated stop position is less than 0
                                sqlglot_expressions.LT(
                                    this=stop_idx_glot, expression=sql_zero
                                ),
                                sql_zero,  # If true, length is 0 (empty string)
                                stop_idx_glot,  # If false, use index position as length
                            ],
                            [BooleanType(), NumericType(), NumericType()],
                        ),
                    )
            case _:
                assert start_idx is not None
                assert stop_idx is not None
                # Get the positive index if negative
                if start_idx >= 0 and stop_idx >= 0:
                    if start_idx > stop_idx:
                        return sql_empty_str
                    return sqlglot_expressions.Substring(
                        this=string_expr,
                        start=sqlglot_expressions.convert(start_idx + 1),
                        length=sqlglot_expressions.convert(stop_idx - start_idx),
                    )
                if start_idx < 0 and stop_idx >= 0:
                    # Calculate the positive index equivalent for the negative start index
                    # e.g., for string "hello" and start_idx=-2, converts to index 4 (LENGTH("hello") + (-2) + 1)
                    start_idx_glot = positive_index(string_expr, start_idx)

                    # Adjust start index to ensure it's not less than 1 (SQL's SUBSTRING is 1-based)
                    start_idx_adjusted_glot = self.convert_iff_case(
                        [
                            sqlglot_expressions.LT(
                                this=start_idx_glot, expression=sql_one
                            ),
                            sql_one,  # If calculated position < 1, use position 1
                            start_idx_glot,  # Otherwise use calculated position
                        ],
                        [BooleanType(), NumericType(), NumericType()],
                    )

                    # Convert positive stop_idx to 1-based indexing by adding 1
                    # e.g., for stop_idx=3 (0-based), converts to 4 (1-based)
                    stop_idx_adjusted_glot = sqlglot_expressions.convert(stop_idx + 1)

                    # Create the SUBSTRING expression
                    answer = sqlglot_expressions.Substring(
                        this=string_expr,  # The original string to slice
                        start=start_idx_adjusted_glot,  # Use adjusted start position
                        length=self.convert_iff_case(
                            [
                                # Check if the length (stop - start) is negative or zero
                                sqlglot_expressions.LTE(
                                    this=apply_parens(
                                        sqlglot_expressions.Sub(
                                            this=stop_idx_adjusted_glot,
                                            expression=start_idx_adjusted_glot,
                                        )
                                    ),
                                    expression=sql_zero,
                                ),
                                sql_zero,  # If length ≤ 0, return empty string
                                # Otherwise calculate actual length
                                sqlglot_expressions.Sub(
                                    this=stop_idx_adjusted_glot,
                                    expression=start_idx_adjusted_glot,
                                ),
                            ],
                            [BooleanType(), NumericType(), NumericType()],
                        ),
                    )
                    return answer
                if start_idx >= 0 and stop_idx < 0:
                    # Convert negative stop index to its positive equivalent
                    # e.g., for string "hello" and stop_idx=-2, converts to index 4 (LENGTH("hello") + (-2) + 1)
                    stop_idx_adjusted_glot = positive_index(string_expr, stop_idx)

                    # Convert start index to 1-based indexing (SQL's SUBSTRING is 1-based)
                    # e.g., for start_idx=1 (0-based), converts to 2 (1-based)
                    start_idx_adjusted_glot = sqlglot_expressions.convert(start_idx + 1)

                    # Create the SUBSTRING expression
                    answer = sqlglot_expressions.Substring(
                        this=string_expr,  # The original string to slice
                        start=start_idx_adjusted_glot,  # Use 1-based start position
                        length=self.convert_iff_case(
                            [
                                # First check: Is the calculated stop position less than 1?
                                sqlglot_expressions.LT(
                                    this=stop_idx_adjusted_glot, expression=sql_one
                                ),
                                sql_zero,  # If true, length becomes 0 (empty string)
                                self.convert_iff_case(
                                    [  # Second check: Is the length negative?
                                        sqlglot_expressions.LTE(
                                            this=apply_parens(
                                                sqlglot_expressions.Sub(
                                                    this=stop_idx_adjusted_glot,
                                                    expression=start_idx_adjusted_glot,
                                                )
                                            ),
                                            expression=sql_zero,
                                        ),
                                        sql_zero,  # If length ≤ 0, return empty string
                                        sqlglot_expressions.Sub(  # Otherwise calculate actual length
                                            this=stop_idx_adjusted_glot,
                                            expression=start_idx_adjusted_glot,
                                        ),
                                    ],
                                    [BooleanType(), NumericType(), NumericType()],
                                ),
                            ],
                            [BooleanType(), NumericType(), NumericType()],
                        ),
                    )
                    return answer
                if start_idx < 0 and stop_idx < 0:
                    # Early return if start index is greater than stop index
                    # e.g., "hello"[-2:-4] should return empty string
                    if start_idx >= stop_idx:
                        return sql_empty_str

                    # Convert negative start index to positive equivalent
                    # e.g., for string "hello" and start_idx=-2, converts to index 4 (LENGTH("hello") + (-2) + 1)
                    pos_start_idx_glot = positive_index(string_expr, start_idx)

                    # Adjust start index to ensure it's not less than 1 (SQL's SUBSTRING is 1-based)
                    start_idx_adjusted_glot = self.convert_iff_case(
                        [
                            sqlglot_expressions.LT(
                                this=pos_start_idx_glot, expression=sql_one
                            ),
                            sql_one,  # If calculated position < 1, use position 1
                            pos_start_idx_glot,  # Otherwise use calculated position
                        ],
                        [BooleanType(), NumericType(), NumericType()],
                    )

                    # Convert negative stop index to positive equivalent
                    stop_idx_adjusted_glot = positive_index(string_expr, stop_idx)

                    # Create the SUBSTRING expression
                    return sqlglot_expressions.Substring(
                        this=string_expr,  # The original string to slice
                        start=start_idx_adjusted_glot,  # Use adjusted start position
                        length=self.convert_iff_case(
                            [
                                # Check if the stop position is less than 1
                                sqlglot_expressions.LT(
                                    this=stop_idx_adjusted_glot, expression=sql_one
                                ),
                                sql_zero,  # Length becomes 0 if stop_idx is < 1
                                sqlglot_expressions.Sub(  # Else calculate length as (stop - start)
                                    this=stop_idx_adjusted_glot,
                                    expression=start_idx_adjusted_glot,
                                ),
                            ],
                            [BooleanType(), NumericType(), NumericType()],
                        ),
                    )

    def convert_like(
        self, args: list[SQLGlotExpression], types: list[PyDoughType]
    ) -> SQLGlotExpression:
        """
        Creates a SQLGlot expression for `A LIKE B`.

        Args:
            `args`: The operands to `LIKE`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `LIKE`.

        Returns:
            The SQLGlot expression matching the functionality of `LIKE`.
        """
        assert len(args) == 2
        column: SQLGlotExpression = apply_parens(args[0])
        pattern: SQLGlotExpression = apply_parens(args[1])
        return sqlglot_expressions.Like(this=column, expression=pattern)

    def convert_join_strings(
        self, args: list[SQLGlotExpression], types: list[PyDoughType]
    ) -> SQLGlotExpression:
        """
        Creates a SQLGlot expression for `CONCAT_WS(delim, A, B, ...)`.

        Args:
            `args`: The operands to `CONCAT_WS`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `CONCAT_WS`.

        Returns:
            The SQLGlot expression matching the functionality of `CONCAT_WS`.
        """
        assert len(args) > 2
        return sqlglot_expressions.ConcatWs(expressions=args)

    def convert_lpad(
        self, args: list[SQLGlotExpression], types: list[PyDoughType]
    ) -> SQLGlotExpression:
        """
        Converts and pads the string to the left till the string is the specified length.
        If length is 0, return an empty string.
        If length is negative, raise an error.
        If length is positive, pad the string on the left to the specified length.

        Args:
            `args`: The operands passed to the function after they were converted
            to SQLGlot expressions. The first operand is expected to be a string.
            `types`: The PyDough types of the arguments to `LPAD`.

        Returns:
            The SQLGlot expression matching the functionality of
            `LPAD(string, length, padding)`. With the caveat that if length is 0,
            it will return an empty string.
        """
        col_glot, col_len_glot, required_len_glot, pad_string_glot, required_len = (
            pad_helper("LPAD", args)
        )
        if required_len == 0:
            return sqlglot_expressions.convert("")

        answer = self.convert_iff_case(
            [
                sqlglot_expressions.GTE(
                    this=col_len_glot, expression=required_len_glot
                ),
                sqlglot_expressions.Substring(
                    this=col_glot,
                    start=sqlglot_expressions.convert(1),
                    length=required_len_glot,
                ),
                sqlglot_expressions.Substring(
                    this=self.convert_concat(
                        [pad_string_glot, col_glot], [StringType(), types[0]]
                    ),
                    start=apply_parens(
                        sqlglot_expressions.Mul(
                            this=required_len_glot,
                            expression=sqlglot_expressions.convert(-1),
                        )
                    ),
                ),
            ],
            [BooleanType(), StringType(), StringType()],
        )
        return answer

    def convert_rpad(
        self, args: list[SQLGlotExpression], types: list[PyDoughType]
    ) -> SQLGlotExpression:
        """
        Converts and pads the string to the right to the specified length.
        If length is 0, return an empty string.
        If length is negative, raise an error.
        If length is positive, pad the string on the right to the specified length.

        Args:
            `args`: The operands passed to the function after they were converted
            to SQLGlot expressions. The first operand is expected to be a string.
            `types`: The PyDough types of the arguments to `RPAD`.

        Returns:
            The SQLGlot expression matching the functionality of
            `RPAD(string, length, padding)`. With the caveat that if length is 0,
            it will return an empty string.
        """
        col_glot, _, required_len_glot, pad_string_glot, required_len = pad_helper(
            "RPAD", args
        )
        if required_len == 0:
            return sqlglot_expressions.convert("")

        answer = sqlglot_expressions.Substring(
            this=self.convert_concat(
                [col_glot, pad_string_glot], [types[0], StringType()]
            ),
            start=sqlglot_expressions.convert(1),
            length=required_len_glot,
        )
        return answer

    def convert_iff_case(
        self, args: list[SQLGlotExpression], types: list[PyDoughType]
    ) -> SQLGlotExpression:
        """
        Creates a SQLGlot expression for `CASE WHEN A THEN B ELSE C END`.

        Args:
            `args`: The operands to the `CASE`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to the `CASE`.

        Returns:
            The SQLGlot expression matching the specified `CASE` pattern.
        """
        assert len(args) == 3
        return sqlglot_expressions.Case().when(args[0], args[1]).else_(args[2])

    def convert_concat(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """

        Creates a SQLGlot expression for `A || B || C || ...`.

        Args:
            `args`: The operands to the concatenation, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to the concatenation.

        Returns:
            The SQLGlot expression matching the specified concatenation.
        """
        # Fast path for all arguments as string literals.
        if all(
            isinstance(arg, sqlglot_expressions.Literal) and arg.is_string
            for arg in args
        ):
            return sqlglot_expressions.convert("".join(arg.this for arg in args))
        else:
            inputs: list[SQLGlotExpression] = [apply_parens(arg) for arg in args]
            return Concat(expressions=inputs)

    def convert_absent(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """
        Creates a SQLGlot expression for `X IS NULL`.

        Args:
            `args`: The operands to `IS NULL`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `IS NULL`.

        Returns:
            The SQLGlot expression matching the functionality of `IS NULL`.
        """
        return sqlglot_expressions.Is(
            this=apply_parens(args[0]), expression=sqlglot_expressions.Null()
        )

    def convert_present(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """

        Creates a SQLGlot expression for `X IS NOT NULL`.

        Args:
            `args`: The operands to `IS NOT NULL`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `IS NOT NULL`.

        Returns:
            The SQLGlot expression matching the functionality of `IS NOT NULL`.
        """
        return sqlglot_expressions.Not(
            this=apply_parens(self.convert_absent(args, types))
        )

    def convert_keep_if(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """
        Creates a SQLGlot expression for `CASE WHEN Y THEN X END`.

        Args:
            `args`: The operands to the `CASE`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to the `CASE`.

        Returns:
            The SQLGlot expression matching the specified `CASE` pattern.
        """
        return self.convert_iff_case(
            [args[1], args[0], sqlglot_expressions.Null()],
            [types[1], types[0], types[0]],
        )

    def convert_monotonic(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """

        Creates a SQLGlot expression for `(A <= B) AND (B <= C) AND ...`.

        Args:
            `args`: The operands to the inequalities, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to the inequalities

        Returns:
            The SQLGlot expression matching the specified inequality pattern.
        """
        if len(args) < 2:
            return sqlglot_expressions.convert(True)

        exprs: list[SQLGlotExpression] = [apply_parens(expr) for expr in args]
        output_expr: SQLGlotExpression = apply_parens(
            sqlglot_expressions.LTE(this=exprs[0], expression=exprs[1])
        )
        for i in range(2, len(exprs)):
            new_expr: SQLGlotExpression = apply_parens(
                sqlglot_expressions.LTE(this=exprs[i - 1], expression=exprs[i])
            )
            output_expr = sqlglot_expressions.And(this=output_expr, expression=new_expr)
        return output_expr

    def convert_isin(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """

        Creates a SQLGlot expression for `A IN B`.

        Args:
            `args`: The operands to `IN`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `IN`.

        Returns:
            The SQLGlot expression matching the functionality of `IN`.
        """
        column: SQLGlotExpression = apply_parens(args[0])
        # Note: We only handle the case with multiple literals where all
        # literals are in the same literal expression. This code will need
        # to change when we support PyDough expressions like:
        # Collection.WHERE(ISIN(name, plural_subcollection.name))
        values = args[1]
        assert isinstance(values, sqlglot_expressions.Array)
        return sqlglot_expressions.In(this=column, expressions=values.expressions)

    def convert_sqrt(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """

        Creates a SQLGlot expression for `SQRT(X)`.

        Args:
            `args`: The operands to `SQRT`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `SQRT`.

        Returns:
            The SQLGlot expression matching the functionality of `SQRT`.
        """
        assert len(args) == 1
        return sqlglot_expressions.Pow(
            this=args[0], expression=sqlglot_expressions.Literal.number(0.5)
        )

    def convert_sign(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """

        Creates a SQLGlot expression that returns either 1, 0, or -1 depending
        on the sign of the input.

        Args:
            `args`: The operands to the sign operation, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to the sign operation.

        Returns:
            The SQLGlot expression matching the specified sign calculation.
        """
        assert len(args) == 1
        arg: SQLGlotExpression = args[0]
        zero_glot: SQLGlotExpression = sqlglot_expressions.Literal.number(0)
        one_glot: SQLGlotExpression = sqlglot_expressions.Literal.number(1)
        minus_one_glot: SQLGlotExpression = sqlglot_expressions.Literal.number(-1)
        answer: SQLGlotExpression = self.convert_iff_case(
            [
                sqlglot_expressions.EQ(this=arg, expression=zero_glot),
                zero_glot,
                apply_parens(
                    self.convert_iff_case(
                        [
                            sqlglot_expressions.LT(this=arg, expression=zero_glot),
                            minus_one_glot,
                            one_glot,
                        ],
                        [BooleanType(), NumericType(), NumericType()],
                    ),
                ),
            ],
            [BooleanType(), NumericType(), NumericType()],
        )
        return answer

    def convert_round(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """

        Creates a SQLGlot expression for `ROUND(X, Y)`.

        Args:
            `args`: The operands to `ROUND`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `ROUND`.

        Returns:
            The SQLGlot expression matching the functionality of `ROUND`.
        """
        assert len(args) == 1 or len(args) == 2
        precision_glot: SQLGlotExpression
        if len(args) == 1:
            precision_glot = sqlglot_expressions.Literal.number(0)
        else:
            # Check if the second argument is a integer literal.
            if (
                not isinstance(args[1], sqlglot_expressions.Literal)
                or args[1].is_string
            ):
                raise PyDoughSQLException(
                    f"Unsupported argument {args[1]} for ROUND."
                    "The precision argument should be an integer literal."
                )
            try:
                int(args[1].this)
            except ValueError:
                raise PyDoughSQLException(
                    f"Unsupported argument {args[1]} for ROUND."
                    "The precision argument should be an integer literal."
                )
            precision_glot = args[1]
        return sqlglot_expressions.Round(
            this=args[0],
            decimals=precision_glot,
        )

    def convert_ceil(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """
        Creates a SQLGlot expression for `CEIL(X)`.

        Args:
            `args`: The operands to `CEIL`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `CEIL`.

        Returns:
            The SQLGlot expression matching the functionality of `CEIL`.
        """
        assert len(args) == 1
        return sqlglot_expressions.Ceil(this=args[0], expressions=args)

    def convert_floor(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """
        Creates a SQLGlot expression for `FLOOR(X)`.

        Args:
            `args`: The operands to `FLOOR`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `FLOOR`.

        Returns:
            The SQLGlot expression matching the functionality of `FLOOR`.
        """
        assert len(args) == 1
        return sqlglot_expressions.Floor(this=args[0], expressions=args)

    def convert_datediff(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """
        Creates a SQLGlot expression for `DATEDIFF(unit, X, Y)`.

        Args:
            `args`: The operands to `DATEDIFF`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `DATEDIFF`.

        Returns:
            The SQLGlot expression matching the functionality of `DATEDIFF`.
        """
        assert len(args) == 3
        # Check if unit is a string.
        if not (isinstance(args[0], sqlglot_expressions.Literal) and args[0].is_string):
            raise PyDoughSQLException(
                f"Unsupported argument for DATEDIFF: {args[0]!r}. It should be a string literal."
            )
        x = self.make_datetime_arg(args[1])
        y = self.make_datetime_arg(args[2])
        unit: DateTimeUnit | None = DateTimeUnit.from_string(args[0].this)
        if unit is None:
            raise PyDoughSQLException(f"Unsupported argument '{unit}' for DATEDIFF.")
        answer = sqlglot_expressions.DateDiff(
            unit=sqlglot_expressions.Var(this=unit.value), this=y, expression=x
        )
        return answer

    def handle_datetime_base_arg(self, arg: SQLGlotExpression) -> SQLGlotExpression:
        """
        Handle the first argument to the DATETIME function, which can be a datetime
        column or a string indicating to fetch the current timestamp.

        Args:
            `arg`: The first argument to the DATETIME function.

        Returns:
            The SQLGlot expression corresponding to the first argument of the
            DATETIME function.
        """
        # If the argument is a string literal, check if it is one of the special
        # values (ignoring case & leading/trailing spaces) indicating the current
        # datetime should be used.
        if isinstance(arg, sqlglot_expressions.Literal) and arg.is_string:
            if current_ts_pattern.fullmatch(arg.this):
                return self.convert_current_timestamp()
        return self.coerce_to_timestamp(arg)

    def convert_current_timestamp(self) -> SQLGlotExpression:
        """
        Create a SQLGlot expression to obtain the current timestamp.
        """
        return sqlglot_expressions.CurrentTimestamp()

    def coerce_to_timestamp(self, base: SQLGlotExpression) -> SQLGlotExpression:
        """
        Create a SQLGlot expression that coerces an object to a timestamp.
        """
        return sqlglot_expressions.Cast(
            this=base, to=sqlglot_expressions.DataType.build("TIMESTAMP")
        )

    def apply_datetime_truncation(
        self, base: SQLGlotExpression, unit: DateTimeUnit
    ) -> SQLGlotExpression:
        """
        Applies a truncation operation to a date/time expression by a certain unit.

        Args:
            `base`: The base date/time expression to truncate.
            `unit`: The unit to truncate the date/time expression to.

        Returns:
            The SQLGlot expression to truncate `base`.
        """
        match unit:
            case DateTimeUnit.HOUR | DateTimeUnit.MINUTE | DateTimeUnit.SECOND:
                return sqlglot_expressions.TimestampTrunc(
                    this=self.make_datetime_arg(base),
                    unit=sqlglot_expressions.Var(this=unit.value.lower()),
                )
            case _:
                return sqlglot_expressions.DateTrunc(
                    this=self.make_datetime_arg(base),
                    unit=sqlglot_expressions.Var(this=unit.value.lower()),
                )

    def apply_datetime_offset(
        self, base: SQLGlotExpression, amt: int, unit: DateTimeUnit
    ) -> SQLGlotExpression:
        """
        Adds/subtracts a datetime interval to to a date/time expression.

        Args:
            `base`: The base date/time expression to add/subtract from.
            `amt`: The amount of the unit to add (if positive) or subtract
            (if negative).
            `unit`: The unit of the interval to add/subtract.

        Returns:
            The SQLGlot expression to add/subtract the specified interval to/from
            `base`.
        """
        new_expr: SQLGlotExpression | None = None
        if amt > 0:
            new_expr = sqlglot_expressions.DateAdd(
                this=base,
                expression=sqlglot_expressions.convert(amt),
                unit=sqlglot_expressions.Var(this=unit.value),
            )
        elif amt < 0:
            amt *= -1
            new_expr = sqlglot_expressions.DateSub(
                this=base,
                expression=sqlglot_expressions.convert(amt),
                unit=sqlglot_expressions.Var(this=unit.value),
            )
        else:
            new_expr = base
        return new_expr

    def convert_datetime(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ) -> SQLGlotExpression:
        """
        Creates a SQLGlot expression for the PyDough `DATETIME` function, which
        treats its first argument as a datetime expression and then applies a
        series of modifiers (passed in as string literals) to add/subtract
        various offsets and/or truncate to specified units.

        Args:
            `args`: The operands to `DATETIME`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `DATETIME`.

        Returns:
            The SQLGlot expression applying the specified `DATETIME` logic.
        """
        # Handle the first argument
        assert len(args) > 0
        result: SQLGlotExpression = self.handle_datetime_base_arg(args[0])

        # Accumulate the answer by using each modifier argument to build up
        # result via a sequence of truncation and offset operations.
        for i in range(1, len(args)):
            arg: SQLGlotExpression = args[i]
            if not (isinstance(arg, sqlglot_expressions.Literal) and arg.is_string):
                raise NotImplementedError(
                    f"DATETIME function currently requires all arguments after the first argument to be string literals, but received {arg.sql()!r}"
                )
            unit: DateTimeUnit | None
            trunc_match: re.Match | None = trunc_pattern.fullmatch(arg.this)
            offset_match: re.Match | None = offset_pattern.fullmatch(arg.this)
            if trunc_match is not None:
                # If the string is in the form `start of <unit>`, apply
                # truncation.
                unit = DateTimeUnit.from_string(str(trunc_match.group(1)))
                if unit is None:
                    raise PyDoughSQLException(
                        f"Unsupported DATETIME modifier string: {arg.this!r}"
                    )
                result = self.apply_datetime_truncation(result, unit)
            elif offset_match is not None:
                # If the string is in the form `±<amt> <unit>`, apply an
                # offset.
                amt = int(offset_match.group(2))
                if str(offset_match.group(1)) == "-":
                    amt *= -1
                unit = DateTimeUnit.from_string(str(offset_match.group(3)))
                if unit is None:
                    raise PyDoughSQLException(
                        f"Unsupported DATETIME modifier string: {arg.this!r}"
                    )
                result = self.apply_datetime_offset(result, amt, unit)
            else:
                raise PyDoughSQLException(
                    f"Unsupported DATETIME modifier string: {arg.this!r}"
                )
        return result

    def convert_extract_datetime(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
        unit: DateTimeUnit,
    ) -> SQLGlotExpression:
        """

        Creates a SQLGlot expression for `EXTRACT(unit FROM X)`.

        Args:
            `args`: The operands to `EXTRACT`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `EXTRACT`.

        Returns:
            The SQLGlot expression matching the functionality of `EXTRACT`.
        """
        assert len(args) == 1
        return sqlglot_expressions.Extract(
            this=sqlglot_expressions.Var(this=unit.value.upper()),
            expression=self.make_datetime_arg(args[0]),
        )

    def dialect_day_of_week(self, base: SQLGlotExpression) -> SQLGlotExpression:
        """
        Gets the day of the week, as an integer, for the `base` argument in
        terms of its dialect.

        Args:
            `base`: The base date/time expression to calculate the day of week
            from.

        Returns:
            The SQLGlot expression to calculating the day of week of `base` in
            terms of the dialect's start of week.
        """
        return sqlglot_expressions.DayOfWeek(this=base)

    def days_from_start_of_week(self, base: SQLGlotExpression) -> SQLGlotExpression:
        """
        Calculates the number of days between a given date and the start of its
        week. The start of week is configured via `start_of_week`. For example,
        if start of week is Monday and the date is Wednesday, this returns a
        SQLGlot expression that will return the number 2.

        The calculation uses the formula: (weekday + offset) % 7

        The default behavior assumes the underlying database follows POSIX
        conventions where:
        - Sunday is day 0
        - Days increment sequentially (Mon=1, Tue=2, etc.)

        Args:
            `base`: The base date/time expression to calculate the start of the week
            from.

        Returns:
            The SQLGlot expression to calculating the number of days from `base` to
            the start of the week. This number is always positive.
        """
        offset: int = (-self.start_of_week_offset) % 7
        dow_expr: SQLGlotExpression = self.dialect_day_of_week(base)
        if offset == 0:
            return dow_expr
        return sqlglot_expressions.Mod(
            this=apply_parens(
                sqlglot_expressions.Add(
                    this=dow_expr,
                    expression=sqlglot_expressions.Literal.number(offset),
                )
            ),
            expression=sqlglot_expressions.Literal.number(7),
        )

    def convert_dayofweek(
        self, args: list[SQLGlotExpression], types: list[PyDoughType]
    ) -> SQLGlotExpression:
        """

        Creates a SQLGlot expression for `DAYOFWEEK(X)`.

        Args:
            `args`: The operands to `DAYOFWEEK`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `DAYOFWEEK`.

        Returns:
            The SQLGlot expression matching the functionality of `DAYOFWEEK`.
        """
        # Expression for ((STRFTIME('%w', base) + offset) % 7)
        shifted_weekday: SQLGlotExpression = self.days_from_start_of_week(args[0])
        # If the week does not start at zero, we need to add 1 to the result
        if not self.configs.start_week_as_zero:
            shifted_weekday = sqlglot_expressions.Add(
                this=apply_parens(shifted_weekday),
                expression=sqlglot_expressions.Literal.number(1),
            )
        return apply_parens(shifted_weekday)

    def convert_dayname(
        self,
        args: list[SQLGlotExpression],
        types: list[PyDoughType],
    ):
        """
        Creates a SQLGlot expression for `DAYNAME(X)`.

        Args:
            `args`: The operands to `DAYNAME`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `DAYNAME`.

        Returns:
            The SQLGlot expression matching the functionality of `DAYNAME`.
        """
        assert len(args) == 1
        base = args[0]
        raw_day_of_week: SQLGlotExpression = self.dialect_day_of_week(base)
        answer: SQLGlotExpression = sqlglot_expressions.Case()
        for dayname, dow in self.dialect_dow_mapping.items():
            answer = answer.when(
                sqlglot_expressions.EQ(
                    this=raw_day_of_week,
                    expression=sqlglot_expressions.Literal.number(dow),
                ),
                sqlglot_expressions.Literal.string(dayname),
            )
        answer = apply_parens(answer)
        return answer

    def convert_integer(
        self, args: list[SQLGlotExpression], types: list[PyDoughType]
    ) -> SQLGlotExpression:
        """
        Creates a SQLGlot expression for `INTEGER(X)`.

        Args:
            `args`: The operands to `INTEGER`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `INTEGER`.

        Returns:
            The SQLGlot expression matching the functionality of `INTEGER(X)`.
        """
        return sqlglot_expressions.Cast(
            this=args[0], to=sqlglot_expressions.DataType.build("BIGINT")
        )

    def convert_float(
        self, args: list[SQLGlotExpression], types: list[PyDoughType]
    ) -> SQLGlotExpression:
        """
        Creates a SQLGlot expression for `FLOAT(X)`.

        Args:
            `args`: The operands to `FLOAT`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `FLOAT`.

        Returns:
            The SQLGlot expression matching the functionality of `FLOAT(X)`.
        """
        return sqlglot_expressions.Cast(
            this=args[0], to=sqlglot_expressions.DataType.build("DOUBLE")
        )

    def convert_string(
        self, args: list[SQLGlotExpression], types: list[PyDoughType]
    ) -> SQLGlotExpression:
        """
        Creates a SQLGlot expression for `STRING(X)`.

        Args:
            `args`: The operands to `STRING`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `STRING`.

        Returns:
            The SQLGlot expression matching the functionality of `STRING(X)`.
        """
        if len(args) == 1:
            return sqlglot_expressions.Cast(
                this=args[0], to=sqlglot_expressions.DataType.build("TEXT")
            )
        else:
            assert len(args) == 2
            if (
                not isinstance(args[1], sqlglot_expressions.Literal)
                or not args[1].is_string
            ):
                raise PyDoughSQLException(
                    f"STRING(X,Y) requires the second argument to be a string date format literal, but received {args[1]}"
                )
            return sqlglot_expressions.TimeToStr(this=args[0], format=args[1])

    def convert_smallest_or_largest(
        self, args: list[SQLGlotExpression], types: list[PyDoughType], largest: bool
    ) -> SQLGlotExpression:
        """
        Creates a SQLGlot expression for the PyDough `SMALLEST` or `LARGEST`
        function. Returns the largest value if `largest` is True, otherwise the
        smallest. For a single argument, returns that argument directly. For
        multiple arguments, builds a CASE statement where each WHEN clause
        compares one argument against all others using AND conditions to find
        the extreme value.

        Args:
            `args`: The operands to `SMALLEST` or `LARGEST`, after they were
            converted to SQLGlot expressions.
            `types`: The PyDough types of the arguments to `SMALLEST` or `LARGEST`.
            `largest`: A boolean indicating whether to return the largest
            or smallest value.

        Returns:
            The SQLGlot expression to calculate the smallest or largest value.
        """
        sqlglot_expr_func = (
            sqlglot_expressions.GTE if largest else sqlglot_expressions.LTE
        )
        if len(args) == 1:
            return args[0]

        def build_chained_and(
            args: list[SQLGlotExpression], idx: int
        ) -> SQLGlotExpression:
            conditions = []
            for i in range(len(args)):
                if i == idx:
                    continue
                conditions.append(sqlglot_expr_func(this=args[idx], expression=args[i]))
            ans = conditions[0]
            for i in range(1, len(conditions)):
                ans = sqlglot_expressions.And(this=ans, expression=conditions[i])
            return ans

        answer: SQLGlotExpression = sqlglot_expressions.Case()
        for i in range(len(args)):
            conditions = build_chained_and(args, i)
            answer = answer.when(conditions, args[i])
        return answer

    def convert_variance(
        self, args: list[SQLGlotExpression], types: list[PyDoughType], type: str
    ) -> SQLGlotExpression:
        """
        Converts a population variance calculation to an equivalent
        SQLGlot expression.

        Args:
            `args`: The arguments to the population variance function.
            `types`: The types of the arguments.
            `type`: The type of variance to calculate.

        Returns:
            The SQLGlot expression to calculate the population variance
            of the argument.
        """
        arg = args[0]
        if type == "population":
            return sqlglot_expressions.VariancePop(this=arg)
        elif type == "sample":
            return sqlglot_expressions.Variance(this=arg)

    def convert_std(
        self, args: list[SQLGlotExpression], types: list[PyDoughType], type: str
    ) -> SQLGlotExpression:
        """
        Converts a standard deviation calculation to an equivalent
        SQLGlot expression.

        Args:
            `args`: The arguments to the standard deviation function.
            `types`: The types of the arguments.
            `type`: The type of standard deviation to calculate.

        Returns:
            The SQLGlot expression to calculate the standard deviation
            of the argument.
        """
        if type == "population":
            return sqlglot_expressions.StddevPop(this=args[0])
        elif type == "sample":
            return sqlglot_expressions.Stddev(this=args[0])

    def convert_count(
        self, args: list[SQLGlotExpression], types: list[PyDoughType]
    ) -> SQLGlotExpression:
        """
        Converts a COUNT operation to an equivalent SQLGlot expression.
        Args:
            `args`: The arguments to the COUNT function.
            `types`: The PyDough types of the arguments to the function call.
        Returns:
            The SQLGlot expression to calculate the count of the argument.
        """
        # If COUNT is called with no arguments, make it COUNT(*).
        # since only some databases allow calling COUNT with no arguments.
        if len(args) == 0:
            return sqlglot_expressions.Count(this=sqlglot_expressions.Star())
        elif len(args) == 1:
            return sqlglot_expressions.Count(this=args[0])
        else:
            raise PyDoughSQLException(f"COUNT expects 0 or 1 argument, got {len(args)}")

    def convert_get_part(
        self, args: list[SQLGlotExpression], types: list[PyDoughType]
    ) -> SQLGlotExpression:
        """
        Converts a PyDough GETPART(string, delimiter, index) function call into a SQLGlot expression
        that extracts the N-th part from a delimited string.

        This function builds a SQL query using recursive common table expressions (CTEs) to:
        - Split the input string into parts based on the given delimiter.
        - Count the total number of parts.
        - Handle both positive and negative indices (negative indices count from the end).
        - Return the part at the specified index, or an empty string if the index is out of range.

        The overall format of the scalar subquery returned is as follows:

        ```sql
        (
            WITH RECURSIVE _s0 AS (
                SELECT
                    0 AS part_index,
                    '' AS part,
                    FIRST_ARGUMENT AS rest,
                    SECOND_ARGUMENT AS delim,
                    THIRD_ARGUMENT AS idx
                UNION ALL
                SELECT
                    part_index + 1 AS part_index,
                    CASE
                        WHEN INSTR(rest, delim) = 0 OR delim = ''
                        THEN rest
                        ELSE SUBSTRING(rest, 1, INSTR(rest, delim) - 1)
                    END AS part,
                    CASE
                        WHEN INSTR(rest, delim) = 0 OR delim = ''
                        THEN ''
                        ELSE SUBSTRING(rest, INSTR(rest, delim) + LENGTH(delim))
                    END AS rest,
                    delim,
                    idx
                FROM _s0
                WHERE
                    rest <> ''
            )
            SELECT _s0.part
            FROM _s0
            CROSS JOIN (
                SELECT COUNT(*) - 1 AS total_parts
                FROM _s0
            ) AS _s1
            WHERE
                _s0.part_index <> 0
                AND _s0.part_index = CASE
                    WHEN _s0.idx > 0
                    THEN _s0.idx
                    WHEN _s0.idx < 0
                    THEN _s1.total_parts + _s0.idx + 1
                    ELSE 1
                END
        )
        ```

        Args:
            args: A list of three SQLGlot expressions:
                - args[0]: The input string to split.
                - args[1]: The delimiter string.
                - args[2]: The index of the part to extract (can be negative).
            types: The PyDough types of the arguments.

        Returns:
            A SQLGlotExpression representing the SQL logic to extract the specified part from the string.
        """

        assert len(args) == 3

        split_parts_table_name: str = self._visitor._generate_table_alias()
        part_count_table_name: str = self._visitor._generate_table_alias()

        # Identifiers definitions
        split_parts: SQLGlotExpression = sqlglot_expressions.Identifier(
            this=split_parts_table_name, quoted=False
        )
        part_count: SQLGlotExpression = sqlglot_expressions.Identifier(
            this=part_count_table_name, quoted=False
        )
        part_identifier: SQLGlotExpression = sqlglot_expressions.Identifier(
            this="part", quoted=False
        )
        part_index: SQLGlotExpression = sqlglot_expressions.Identifier(
            this="part_index", quoted=False
        )
        idx: SQLGlotExpression = sqlglot_expressions.Identifier(
            this="idx", quoted=False
        )
        total_parts: SQLGlotExpression = sqlglot_expressions.Identifier(
            this="total_parts", quoted=False
        )
        delim: SQLGlotExpression = sqlglot_expressions.Identifier(
            this="delim", quoted=False
        )
        rest: SQLGlotExpression = sqlglot_expressions.Identifier(
            this="rest", quoted=False
        )

        # Literals definitions
        literal_0: SQLGlotExpression = sqlglot_expressions.Literal.number(0)
        literal_1: SQLGlotExpression = sqlglot_expressions.Literal.number(1)
        literal_empty: SQLGlotExpression = sqlglot_expressions.Literal.string("")

        # Columns and tables
        column_part: SQLGlotExpression = sqlglot_expressions.Column(
            this=part_identifier
        )
        column_part_index: SQLGlotExpression = sqlglot_expressions.Column(
            this=part_index
        )
        column_rest: SQLGlotExpression = sqlglot_expressions.Column(this=rest)
        column_idx: SQLGlotExpression = sqlglot_expressions.Column(
            this=idx, table=split_parts
        )

        # First half of the recursive CTE:
        # SELECT
        #   0 AS part_index,
        #   '' AS part,
        #   input AS rest,
        #   delim AS delim,
        #   idx AS idx
        select_union_params: SQLGlotExpression = sqlglot_expressions.Select(
            expressions=[
                sqlglot_expressions.Alias(this=literal_0, alias=part_index),
                sqlglot_expressions.Alias(this=literal_empty, alias=part_identifier),
                sqlglot_expressions.Alias(
                    this=args[0],  # the first string, the input
                    alias=rest,
                ),
                sqlglot_expressions.Alias(
                    this=args[1],  # the second string, the delimiter
                    alias=delim,
                ),
                sqlglot_expressions.Alias(
                    this=args[2],  # the third arg, the index
                    alias=idx,
                ),
            ]
        )

        # CASE
        #   WHEN INSTR(rest, delim) = 0 OR delim = '' THEN rest
        #   ELSE SUBSTRING(rest, 1, INSTR(rest, delim) - 1)
        # END
        delim_in_rest: SQLGlotExpression = sqlglot_expressions.StrPosition(
            this=column_rest, substr=delim
        )
        delim_cond: SQLGlotExpression = sqlglot_expressions.Or(
            this=sqlglot_expressions.EQ(this=delim_in_rest, expression=literal_0),
            expression=sqlglot_expressions.EQ(this=delim, expression=literal_empty),
        )
        new_part: SQLGlotExpression = sqlglot_expressions.Substring(
            this=column_rest,
            start=literal_1,
            length=sqlglot_expressions.Sub(
                this=delim_in_rest,
                expression=literal_1,
            ),
        )
        new_part_case: SQLGlotExpression = (
            sqlglot_expressions.Case().when(delim_cond, column_rest).else_(new_part)
        )

        # CASE
        #   WHEN INSTR(rest, delim) = 0 OR delim = '' THEN ''
        #   ELSE SUBSTRING(rest, 1, INSTR(rest, delim) - LENGTH(delim))
        # END
        new_rest: SQLGlotExpression = sqlglot_expressions.Substring(
            this=column_rest,
            start=sqlglot_expressions.Add(
                this=sqlglot_expressions.StrPosition(
                    this=column_rest,
                    substr=delim,
                ),
                expression=sqlglot_expressions.Length(this=delim),
            ),
        )
        new_rest_case: SQLGlotExpression = (
            sqlglot_expressions.Case().when(delim_cond, literal_empty).else_(new_rest)
        )

        # Second half of the recursive CTE:
        # SELECT
        #   part_index + 1 AS part_index,
        #   CASE WHEN INSTR(rest, delim) = 0 OR delim = '' THEN rest ELSE SUBSTRING(rest, 1, INSTR(rest, delim) - 1) END AS part,
        #   CASE WHEN INSTR(rest, delim) = 0 OR delim = '' THEN '' ELSE SUBSTRING(rest, INSTR(rest, delim) + LENGTH(delim)) END AS rest,
        #   delim,
        #   idx
        # FROM split_parts
        select_union_split_parts: SQLGlotExpression = (
            sqlglot_expressions.Select(
                expressions=[
                    sqlglot_expressions.Alias(
                        this=sqlglot_expressions.Add(
                            this=column_part_index, expression=literal_1
                        ),
                        alias=column_part_index,
                    ),
                    sqlglot_expressions.Alias(
                        this=new_part_case, alias=part_identifier
                    ),
                    sqlglot_expressions.Alias(this=new_rest_case, alias=rest),
                    delim,
                    idx,
                ],
            )
            .from_(split_parts_table_name)
            .where(sqlglot_expressions.NEQ(this=column_rest, expression=literal_empty))
        )

        # Union the two halves to create the recursive CTE:
        split_parts_union: SQLGlotExpression = sqlglot_expressions.Union(
            this=select_union_params,
            distinct=False,
            expression=select_union_split_parts,
        )

        # Subquery: SELECT COUNT(*) - 1 AS total_parts FROM split_parts
        part_count_select: SQLGlotExpression = sqlglot_expressions.Select(
            expressions=[
                sqlglot_expressions.Alias(
                    this=sqlglot_expressions.Sub(
                        this=sqlglot_expressions.Count(
                            this=sqlglot_expressions.Star(), big_int=True
                        ),
                        expression=literal_1,
                    ),
                    alias=total_parts,
                )
            ]
        ).from_(split_parts_table_name)

        # Final select:
        # SELECT part
        # FROM split_parts, (SELECT COUNT(*) - 1 AS total_parts FROM split_parts)
        # WHERE part_index != 0
        # AND part_index = CASE
        #   WHEN idx > 0 THEN idx
        #   WHEN idx < 0 THEN total_parts + idx + 1
        #   ELSE 1 END
        if_idx_greater_0: SQLGlotExpression = sqlglot_expressions.If(
            this=sqlglot_expressions.GT(this=column_idx, expression=literal_0),
            true=column_idx,
        )
        if_idx_lower_0: SQLGlotExpression = sqlglot_expressions.If(
            this=sqlglot_expressions.LT(
                this=column_idx,
                expression=literal_0,
            ),
            true=sqlglot_expressions.Add(
                this=sqlglot_expressions.Add(
                    this=sqlglot_expressions.Column(this=total_parts, table=part_count),
                    expression=column_idx,
                ),
                expression=literal_1,
            ),
        )
        case_idx: SQLGlotExpression = sqlglot_expressions.Case(
            ifs=[if_idx_greater_0, if_idx_lower_0], default=literal_1
        )
        result: SQLGlotExpression = (
            sqlglot_expressions.Select(expressions=[column_part])
            .from_(split_parts_table_name)
            .join(
                sqlglot_expressions.Subquery(
                    this=part_count_select,
                    alias=sqlglot_expressions.TableAlias(this=part_count_table_name),
                )
            )
            .where(
                sqlglot_expressions.And(
                    this=sqlglot_expressions.NEQ(
                        this=column_part_index, expression=literal_0
                    ),
                    expression=sqlglot_expressions.EQ(
                        this=column_part_index, expression=case_idx
                    ),
                )
            )
        )

        # Add the WITH clause as a recursive CTE, and wrap the final answer in
        # a subquery so the single column of the scalar subquery is used as the
        # answer.
        result = result.with_(split_parts_table_name, split_parts_union, recursive=True)
        result = sqlglot_expressions.Subquery(this=result)

        return result

    def convert_quantile(
        self, args: list[SQLGlotExpression], types: list[PyDoughType]
    ) -> SQLGlotExpression:
        """
        Converts a PyDough QUANTILE(X, p) function call to a SQLGlot expression
        representing the SQL standard PERCENTILE_DISC aggregate function.

        This produces an expression equivalent to:
            PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY X)

        Args:
            args: A list of two SQLGlot expressions, where args[0] is the column
            or expression to order by (X), and args[1] is the quantile value (p)
            between 0 and 1.
            types: The PyDough types of the arguments.

        Returns:
            A SQLGlotExpression representing the PERCENTILE_DISC(p) WITHIN GROUP
            (ORDER BY X)
            aggregate function.
        """

        assert len(args) == 2

        # Validate that the second argument is a number between 0 and 1 (inclusive)
        if (
            not isinstance(args[1], sqlglot_expressions.Literal)
            or args[1].is_string
            or not (0.0 <= float(args[1].this) <= 1.0)
        ):
            raise PyDoughSQLException(
                f"QUANTILE expected second argument to be a numeric literal between 0 and 1, got {args[1]}"
            )

        percentile_disc_function: SQLGlotExpression = (
            sqlglot_expressions.PercentileDisc(this=args[1])
        )

        ordered_column: SQLGlotExpression = sqlglot_expressions.Ordered(this=args[0])

        order: SQLGlotExpression = sqlglot_expressions.Order(
            expressions=[ordered_column]
        )

        within_group_clause: SQLGlotExpression = sqlglot_expressions.WithinGroup(
            this=percentile_disc_function, expression=order
        )

        return within_group_clause

    def convert_ordering(
        self, arg: SQLGlotExpression, data_type: PyDoughType
    ) -> SQLGlotExpression:
        """
        Post-processes a SQLGlot expression used as an ordering key, e.g. if it requires a collation
        Args:
            `arg`: The argument being used as an order key.
            `data_type`: The PyDough types of the order key.
        Returns:
            A SQLGlotExpression representing the order key transformed in any necessary way.
        """
        return arg
