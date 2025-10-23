"""
Implementations of the process for transforming unqualified nodes to PyDough
QDAG nodes.
"""

__all__ = ["qualify_node"]

from collections.abc import Iterable

import pydough
import pydough.pydough_operators as pydop
from pydough.configs import PyDoughSession
from pydough.errors import PyDoughUnqualifiedException
from pydough.metadata import GeneralJoinMetadata, GraphMetadata
from pydough.pydough_operators.expression_operators import (
    ExpressionFunctionOperator,
    ExpressionWindowOperator,
)
from pydough.qdag import (
    AstNodeBuilder,
    ChildOperatorChildAccess,
    ChildReferenceExpression,
    CollationExpression,
    ColumnProperty,
    ExpressionFunctionCall,
    GlobalContext,
    Literal,
    PartitionBy,
    PyDoughCollectionQDAG,
    PyDoughExpressionQDAG,
    PyDoughQDAG,
    Reference,
    SidedReference,
    SubCollection,
    WindowCall,
)
from pydough.types import PyDoughType

from .unqualified_node import (
    UnqualifiedAccess,
    UnqualifiedBest,
    UnqualifiedBinaryOperation,
    UnqualifiedCalculate,
    UnqualifiedCollation,
    UnqualifiedCross,
    UnqualifiedLiteral,
    UnqualifiedNode,
    UnqualifiedOperation,
    UnqualifiedOperator,
    UnqualifiedOrderBy,
    UnqualifiedPartition,
    UnqualifiedRoot,
    UnqualifiedSingular,
    UnqualifiedTopK,
    UnqualifiedWhere,
    UnqualifiedWindow,
)
from .unqualified_transform import transform_cell


class Qualifier:
    def __init__(self, session: PyDoughSession):
        self._session: PyDoughSession = session
        assert session.metadata is not None
        self._builder: AstNodeBuilder = AstNodeBuilder(session.metadata)

    @property
    def graph(self) -> GraphMetadata:
        """
        The metadata for the PyDough graph in which is used to identify
        collections and properties.
        """
        assert self._session.metadata is not None
        return self._session.metadata

    @property
    def builder(self) -> AstNodeBuilder:
        """
        The builder used by the qualifier to create QDAG nodes.
        """
        return self._builder

    def qualify_literal(self, unqualified: UnqualifiedLiteral) -> PyDoughExpressionQDAG:
        """
        Transforms an `UnqualifiedLiteral` into a PyDoughExpressionQDAG node.

        Args:
            `unqualified`: the UnqualifiedLiteral instance to be transformed.
            `context`: the collection QDAG whose context the expression is being
            evaluated within.
            `children`: the list where collection nodes that must be derived
            as children of `context` should be appended.

        Returns:
            The PyDough QDAG object for the qualified expression node.

        Raises:
            `PyDoughUnqualifiedException` or `PyDoughQDAGException` if something
            goes wrong during the qualification process, e.g. a term cannot be
            qualified or is not recognized.
        """
        value: object = unqualified._parcel[0]
        data_type: PyDoughType = unqualified._parcel[1]
        if isinstance(value, (list, tuple)):
            literal_elems: list[object] = []
            for elem in value:
                assert isinstance(elem, UnqualifiedLiteral)
                expr: PyDoughExpressionQDAG = self.qualify_literal(elem)
                assert isinstance(expr, Literal)
                literal_elems.append(expr.value)
            return self.builder.build_literal(literal_elems, data_type)
        return self.builder.build_literal(value, data_type)

    def qualify_operation(
        self,
        unqualified: UnqualifiedOperation,
        context: PyDoughCollectionQDAG,
        children: list[PyDoughCollectionQDAG],
    ) -> PyDoughExpressionQDAG:
        """
        Transforms an `UnqualifiedOperation` into a PyDoughExpressionQDAG node.

        Args:
            `unqualified`: the UnqualifiedOperation instance to be transformed.
            `context`: the collection QDAG whose context the expression is being
            evaluated within.
            `children`: the list where collection nodes that must be derived
            as children of `context` should be appended.

        Returns:
            The PyDough QDAG object for the qualified expression node.

        Raises:
            `PyDoughUnqualifiedException` or `PyDoughQDAGException` if something
            goes wrong during the qualification process, e.g. a term cannot be
            qualified or is not recognized.
        """
        operation: ExpressionFunctionOperator = unqualified._parcel[0]
        unqualified_operands: list[UnqualifiedNode] = unqualified._parcel[1]
        qualified_operands: list[PyDoughQDAG] = []
        # Iterate across every operand to generate its qualified variant.
        # First, attempt to qualify it as an expression (the common case), but
        # if that fails specifically because the result would be a collection,
        # then attempt to qualify it as a collection.
        for node in unqualified_operands:
            operand: PyDoughQDAG = self.qualify_node(node, context, children, True)
            if isinstance(operand, PyDoughExpressionQDAG):
                qualified_operands.append(
                    self.qualify_expression(node, context, children)
                )
            else:
                assert isinstance(operand, PyDoughCollectionQDAG)
                # If the operand could be qualified as a collection, then
                # add it to the children list (if not already present) and
                # use a child reference collection as the argument.
                ref_num: int
                if operand in children:
                    ref_num = children.index(operand)
                else:
                    ref_num = len(children)
                    children.append(operand)
                child_collection_ref: PyDoughCollectionQDAG = (
                    self.builder.build_child_reference_collection(
                        context, children, ref_num
                    )
                )
                qualified_operands.append(child_collection_ref)
        return self.builder.build_expression_function_call(
            operation, qualified_operands
        )

    def qualify_binary_operation(
        self,
        unqualified: UnqualifiedBinaryOperation,
        context: PyDoughCollectionQDAG,
        children: list[PyDoughCollectionQDAG],
    ) -> PyDoughExpressionQDAG:
        """
        Transforms an `UnqualifiedBinaryOperation` into a PyDoughExpressionQDAG node.

        Args:
            `unqualified`: the UnqualifiedBinaryOperation instance to be transformed.
            `context`: the collection QDAG whose context the expression is being
            evaluated within.
            `children`: the list where collection nodes that must be derived
            as children of `context` should be appended.

        Returns:
            The PyDough QDAG object for the qualified expression node.

        Raises:
            `PyDoughUnqualifiedException` or `PyDoughQDAGException` if something
            goes wrong during the qualification process, e.g. a term cannot be
            qualified or is not recognized.
        """
        operator: pydop.BinaryOperator = unqualified._parcel[0]
        # Independently qualify the LHS and RHS arguments
        unqualified_lhs: UnqualifiedNode = unqualified._parcel[1]
        unqualified_rhs: UnqualifiedNode = unqualified._parcel[2]
        qualified_lhs: PyDoughExpressionQDAG = self.qualify_expression(
            unqualified_lhs, context, children
        )
        qualified_rhs: PyDoughExpressionQDAG = self.qualify_expression(
            unqualified_rhs, context, children
        )
        return self.builder.build_expression_function_call(
            operator, [qualified_lhs, qualified_rhs]
        )

    def extract_window_per_args(
        self,
        per: str,
        ancestral_names: list[str],
        context: PyDoughCollectionQDAG,
        window: UnqualifiedWindow,
    ) -> tuple[str, int | None]:
        """
        Extracts the arguments from the `per` string of a window function to
        identify the name of the ancestor, and the index of which ancestor
        with that name should be chosen (if an index is provided). For example:
        - `per="orders"` -> `("orders", None)`
        - `per="customers:2"` -> `("customers", 2)`

        Args:
            `per`: the string to be parsed.
            `ancestral_names`: the list of names of the ancestors of the
            current context, in order from closest to furthest.
            `context`: the collection QDAG whose context the expression is being
            evaluated within.
            `window`: the unqualified window function that the `per` string
            corresponds to, used for error reporting.

        Returns:
            The tuple in the desired format `(ancestor_name, ancestor_index)`.

        Raises:
            `PyDoughUnqualifiedException` if the `per` string is malformed
            or does not correspond to a valid ancestor of the current context.
        """
        ancestor_name: str
        ancestor_idx: int | None
        # Break down the per string into its components, which is either
        # `[name]`, or `[name, index]`, where `index` must be a positive
        # integer.
        components: list[str] = per.split(":")
        if len(components) == 1:
            ancestor_name = components[0]
            ancestor_idx = None
        elif len(components) == 2:
            ancestor_name = components[0]
            if not components[1].isdigit():
                raise pydough.active_session.error_builder.bad_window_per(
                    per, ancestral_names, context, window
                )
            ancestor_idx = int(components[1])
            if ancestor_idx <= 0:
                raise pydough.active_session.error_builder.bad_window_per(
                    per, ancestral_names, context, window
                )
        else:
            raise pydough.active_session.error_builder.bad_window_per(
                per, ancestral_names, context, window
            )
        # Verify that `name` corresponds to one of the ancestors of the
        # current context.
        if ancestor_name not in ancestral_names:
            raise pydough.active_session.error_builder.bad_window_per(
                per, ancestral_names, context, window
            )
        # Verify that `name` is only present exactly one time in the
        # ancestors of the current context, unless an index was provided.
        if ancestor_idx is None:
            if ancestral_names.count(ancestor_name) > 1:
                # TODO: potentially add a default value of 1?
                raise pydough.active_session.error_builder.bad_window_per(
                    per, ancestral_names, context, window
                )
        elif ancestral_names.count(ancestor_name) < ancestor_idx:
            # If an index was provided, ensure that there are that many
            # ancestors with that name.
            raise pydough.active_session.error_builder.bad_window_per(
                per, ancestral_names, context, window
            )
        return ancestor_name, ancestor_idx

    def qualify_window(
        self,
        unqualified: UnqualifiedWindow,
        context: PyDoughCollectionQDAG,
        children: list[PyDoughCollectionQDAG],
    ) -> PyDoughExpressionQDAG:
        """
        Transforms an `UnqualifiedWindow` into a PyDoughExpressionQDAG node.

        Args:
            `unqualified`: the UnqualifiedWindow instance to be transformed.
            `context`: the collection QDAG whose context the expression is being
            evaluated within.
            `children`: the list where collection nodes that must be derived
            as children of `context` should be appended.

        Returns:
            The PyDough QDAG object for the qualified window node.

        Raises:
            `PyDoughUnqualifiedException` or `PyDoughQDAGException` if something
            goes wrong during the qualification process, e.g. a term cannot be
            qualified or is not recognized.
        """
        window_operator: ExpressionWindowOperator = unqualified._parcel[0]
        unqualified_args: Iterable[UnqualifiedNode] = unqualified._parcel[1]
        unqualified_by: Iterable[UnqualifiedNode] = unqualified._parcel[2]
        unqualified_by = self._expressions_to_collations(unqualified_by)
        per: str | None = unqualified._parcel[3]
        kwargs: dict[str, object] = unqualified._parcel[4]
        # Qualify all of the function args, storing the children built along
        # the way.
        qualified_args: list[PyDoughExpressionQDAG] = []
        for arg in unqualified_args:
            qualified_args.append(self.qualify_expression(arg, context, children))
        # Qualify all of the collation terms, storing the children built along
        # the way.
        qualified_collations: list[CollationExpression] = []
        for term in unqualified_by:
            qualified_term: PyDoughExpressionQDAG = self.qualify_expression(
                term, context, children
            )
            assert isinstance(qualified_term, CollationExpression)
            qualified_collations.append(qualified_term)
        levels: int | None = None
        # If the per argument exists, parse it to identify which ancestor
        # of the current context the window function is being done with
        # regards to, and converting it to a `levels` integer (indicating
        # the number of ancestor levels to go up to).
        if per is not None:
            ancestral_names: list[str] = context.get_ancestral_names()
            ancestor_name, ancestor_idx = self.extract_window_per_args(
                per, ancestral_names, context, unqualified
            )
            # Find how many levels upward need to be traversed to find the
            # targeted ancestor by finding the nth ancestor matching the
            # name, at the end of the ancestral_names.
            levels = 1
            for i in range(len(ancestral_names) - 1, -1, -1):
                if ancestral_names[i] == ancestor_name:
                    if ancestor_idx is None or ancestor_idx == 1:
                        break
                    ancestor_idx -= 1
                levels += 1
        # Use the qualified children & collation to create a new ORDER BY node.
        return self.builder.build_window_call(
            window_operator, qualified_args, qualified_collations, levels, kwargs
        )

    def qualify_collation(
        self,
        unqualified: UnqualifiedCollation,
        context: PyDoughCollectionQDAG,
        children: list[PyDoughCollectionQDAG],
    ) -> PyDoughExpressionQDAG:
        """
        Transforms an `UnqualifiedCollation` into a PyDoughExpressionQDAG node.

        Args:
            `unqualified`: the UnqualifiedCollation instance to be transformed.
            `context`: the collection QDAG whose context the expression is being
            evaluated within.
            `children`: the list where collection nodes that must be derived
            as children of `context` should be appended.

        Returns:
            The PyDough QDAG object for the qualified expression node.

        Raises:
            `PyDoughUnqualifiedException` or `PyDoughQDAGException` if something
            goes wrong during the qualification process, e.g. a term cannot be
            qualified or is not recognized.
        """
        unqualified_expr: UnqualifiedNode = unqualified._parcel[0]
        asc: bool = unqualified._parcel[1]
        na_last: bool = unqualified._parcel[2]
        # Qualify the underlying expression, then wrap it in a collation.
        qualified_expr: PyDoughExpressionQDAG = self.qualify_expression(
            unqualified_expr, context, children
        )
        return CollationExpression(qualified_expr, asc, na_last)

    def parse_general_condition(self, access: SubCollection) -> None:
        """
        Parses a general join condition of a sub-collection access from a
        PyDough string into an unqualified node and then into a QDAG node
        containing sided references. Stores the answer inside the
        sub-collection access.

        Args:
            `access`: the sub-collection access containing the join condition
            that is being parsed.
        """
        assert isinstance(access.subcollection_property, GeneralJoinMetadata)
        property: GeneralJoinMetadata = access.subcollection_property
        self_name: str = property.self_name
        other_name: str = property.other_name
        # Wrap the rest of the logic in a try-except to better format the
        # error messages in case the join condition string is malformed.
        try:
            # Create Python code for deriving the join condition and storing it in
            # a variable called '_answer'.
            condition_statement = transform_cell(
                f"_answer = ({property.condition})",
                self.graph.name,
                {self_name, other_name},
            )
            # Execute the Python code in an environment containing the graph, as
            # well as having the prefixes `self` and `other` already defined as
            # unqualified access nodes.
            self_expr: UnqualifiedNode = UnqualifiedAccess(
                UnqualifiedRoot(self.graph), self_name
            )
            other_expr: UnqualifiedNode = UnqualifiedAccess(
                UnqualifiedRoot(self.graph), other_name
            )
            local_env: dict[str, object] = {
                self.graph.name: self.graph,
                self_name: self_expr,
                other_name: other_expr,
            }
            exec(condition_statement, {}, local_env)
            # Extract the answer from the local environment as an unqualified node.
            assert "_answer" in local_env
            value = local_env.get("_answer")
            assert isinstance(value, UnqualifiedNode), (
                "Expected the join condition to be a valid PyDough expression"
            )
            # Qualify the join condition and store it in the access.
            access.general_condition = self.qualify_join_condition(
                value, access, self_name, other_name
            )
        except Exception as e:
            raise PyDoughUnqualifiedException(
                f"Malformed general join condition: {property.condition!r} ({e})"
            ) from e

    def qualify_join_condition(
        self,
        condition: UnqualifiedNode,
        access: SubCollection,
        self_name: str,
        other_name: str,
    ) -> PyDoughExpressionQDAG:
        """
        Variant of `qualify_expression` specifically for qualifying the
        contents of a general join condition. These expressions can contain
        sided-references parent vs child collection, but cannot contain window
        functions or any collections/sub-collections, therefore the
        qualification path is slightly different and streamlined.

        Args:
            `condition`: the unqualified node to be qualified as part of a
            general join condition.
            `access`: the sub-collection access that the join condition
            corresponds to.
            `self_name`: the name used to reference the parent collection
            within the join.
            `other_name`: the name used to reference the child collection
            within the join.

        Returns:
            The PyDough QDAG object for the qualified expression node for
            `condition`.
        """
        raw_term: PyDoughQDAG
        term: PyDoughExpressionQDAG
        term_name: str
        match condition:
            case UnqualifiedLiteral():
                # Handle literals normally
                return self.qualify_literal(condition)
            case UnqualifiedBinaryOperation():
                # For binary operators, invoke the same logic as for normal
                # qualification of binary operators except with using
                # `qualify_join_condition` on the inputs instead of
                # `qualify_expression`.
                binop: pydop.BinaryOperator = condition._parcel[0]
                qualified_lhs: PyDoughExpressionQDAG = self.qualify_join_condition(
                    condition._parcel[1], access, self_name, other_name
                )
                qualified_rhs: PyDoughExpressionQDAG = self.qualify_join_condition(
                    condition._parcel[2], access, self_name, other_name
                )
                return self.builder.build_expression_function_call(
                    binop, [qualified_lhs, qualified_rhs]
                )
            case UnqualifiedOperation():
                # For function calls, invoke the same logic as for normal
                # qualification of function calls except with using
                # `qualify_join_condition` on the inputs instead of
                # `qualify_expression`.
                operator: pydop.PyDoughExpressionOperator = condition._parcel[0]
                unqualified_operands: list[UnqualifiedNode] = condition._parcel[1]
                qualified_operands: list[PyDoughQDAG] = []
                for node in unqualified_operands:
                    qualified_operands.append(
                        self.qualify_join_condition(node, access, self_name, other_name)
                    )
                return self.builder.build_expression_function_call(
                    operator, qualified_operands
                )
            case UnqualifiedAccess():
                # For accesses, verify that the access is in the form of
                # `root.xxx.expr_name` where `xxx` is either the "self name" or
                # the "other name" of the general join condition, and generate
                # an appropriate sided reference indicating whether the term
                # comes from the parent side or the child side. Also verify
                # that the term is an expression.
                if isinstance(condition._parcel[0], UnqualifiedAccess):
                    predecessor: UnqualifiedAccess = condition._parcel[0]
                    if isinstance(predecessor._parcel[0], UnqualifiedRoot):
                        if predecessor._parcel[1] in (self_name, other_name):
                            is_self = predecessor._parcel[1] == self_name
                            source: PyDoughCollectionQDAG = (
                                access.ancestor_context if is_self else access
                            )
                            raw_term = source.get_term(condition._parcel[1])
                            if not isinstance(raw_term, PyDoughExpressionQDAG):
                                raise PyDoughUnqualifiedException(
                                    "Accessing sub-collection terms is currently unsupported in PyDough general join conditions"
                                )
                            term = raw_term
                            assert isinstance(term, (Reference, ColumnProperty))
                            term_name = (
                                term.term_name
                                if isinstance(term, Reference)
                                else term.column_property.name
                            )
                            return SidedReference(term_name, access, is_self)
                raise PyDoughUnqualifiedException(
                    "Accessing sub-collection terms is currently unsupported in PyDough general join conditions"
                )
            case UnqualifiedWindow():
                raise PyDoughUnqualifiedException(
                    "Window functions are currently unsupported in PyDough general join conditions"
                )
            case (
                UnqualifiedCalculate()
                | UnqualifiedWhere()
                | UnqualifiedOrderBy()
                | UnqualifiedTopK()
            ):
                raise PyDoughUnqualifiedException(
                    "Collection accesses are currently unsupported in PyDough general join conditions"
                )
            case _:
                raise PyDoughUnqualifiedException(
                    f"Unsupported unqualified node in general join conditions: {condition.__class__.__name__}"
                )

    def qualify_access(
        self,
        unqualified: UnqualifiedAccess,
        context: PyDoughCollectionQDAG,
        children: list[PyDoughCollectionQDAG],
        is_child: bool,
    ) -> PyDoughQDAG:
        """
        Transforms an `UnqualifiedAccess` into a PyDough QDAG node, either as
        accessing a subcollection or an expression from the current context.

        Args:
            `unqualified`: the UnqualifiedAccess instance to be transformed.
            `builder`: a builder object used to create new qualified nodes.
            `context`: the collection QDAG whose context the collection is being
            evaluated within.
            `children`: the list where collection nodes that must be derived
            as children of `context` should be appended.
            `is_child`: whether the collection is being qualified as a child
            of a child operator context, such as CALCULATE or PARTITION.

        Returns:
            The PyDough QDAG object for the qualified collection or expression
            node.

        Raises:
            `PyDoughUnqualifiedException` or `PyDoughQDAGException` if something
            goes wrong during the qualification process, e.g. a term cannot be
            qualified or is not recognized.
        """
        unqualified_parent: UnqualifiedNode = unqualified._parcel[0]
        name: str = unqualified._parcel[1]
        term: PyDoughQDAG

        # First, qualify the parent collection.
        qualified_parent: PyDoughCollectionQDAG = self.qualify_collection(
            unqualified_parent, context, is_child
        )

        if (
            isinstance(qualified_parent, GlobalContext)
            and name == qualified_parent.graph.name
            and not is_child
        ) or (
            isinstance(qualified_parent, ChildOperatorChildAccess)
            and isinstance(qualified_parent.child_access, GlobalContext)
            and name == qualified_parent.child_access.graph.name
        ):
            # Special case: if the parent is the root context and the child
            # is named after the graph name, return the parent since the
            # child is just a de-sugared invocation of the global context.
            return qualified_parent
        else:
            # Identify whether the access is an expression or a collection
            term = qualified_parent.get_term(name)
            if isinstance(term, PyDoughCollectionQDAG):
                # If it is a collection that is not the special case,
                # access the child collection from the qualified parent
                # collection.
                answer: PyDoughCollectionQDAG = self.builder.build_child_access(
                    name, qualified_parent
                )
                # In the case that it is a general join condition access,
                # qualify the join condition at this time.
                if isinstance(answer, SubCollection) and isinstance(
                    answer.subcollection_property, GeneralJoinMetadata
                ):
                    self.parse_general_condition(answer)
                if isinstance(unqualified_parent, UnqualifiedRoot) and is_child:
                    answer = ChildOperatorChildAccess(answer)
                return answer
            else:
                assert isinstance(term, PyDoughExpressionQDAG)
                if isinstance(unqualified_parent, UnqualifiedRoot):
                    # If at the root, the access must be a reference to a scalar
                    # attribute accessible in the current context.
                    typ: PyDoughType = context.get_expr(name).pydough_type
                    return self.builder.build_reference(context, name, typ)
                else:
                    # Otherwise, the access is a reference to a scalar attribute of
                    # a child collection node of the current context. Add this new
                    # child to the list of children, unless already present, then
                    # return the answer as a reference to a field of the child.
                    ref_num: int
                    if qualified_parent in children:
                        ref_num = children.index(qualified_parent)
                    else:
                        ref_num = len(children)
                        children.append(qualified_parent)
                    return self.builder.build_child_reference_expression(
                        children, ref_num, name
                    )

    def qualify_calculate(
        self,
        unqualified: UnqualifiedCalculate,
        context: PyDoughCollectionQDAG,
        is_child: bool,
    ) -> PyDoughCollectionQDAG:
        """
        Transforms an `UnqualifiedCalculate` into a PyDoughCollectionQDAG node.

        Args:
            `unqualified`: the UnqualifiedCalculate instance to be transformed.
            `builder`: a builder object used to create new qualified nodes.
            `context`: the collection QDAG whose context the collection is being
            evaluated within.
            `is_child`: whether the collection is being qualified as a child
            of a child operator context, such as CALCULATE or PARTITION.

        Returns:
            The PyDough QDAG object for the qualified collection node.

        Raises:
            `PyDoughUnqualifiedException` or `PyDoughQDAGException` if something
            goes wrong during the qualification process, e.g. a term cannot be
            qualified or is not recognized.
        """
        unqualified_parent: UnqualifiedNode = unqualified._parcel[0]
        unqualified_terms: list[tuple[str, UnqualifiedNode]] = unqualified._parcel[1]
        qualified_parent: PyDoughCollectionQDAG = self.qualify_collection(
            unqualified_parent, context, is_child
        )
        # Qualify all of the CALCULATE terms, storing the children built along
        # the way.
        children: list[PyDoughCollectionQDAG] = []
        qualified_terms: list[tuple[str, PyDoughExpressionQDAG]] = []
        for name, term in unqualified_terms:
            qualified_term = self.qualify_expression(term, qualified_parent, children)
            qualified_terms.append((name, qualified_term))
        # Use the qualified children & terms to create a new CALCULATE node.
        return self.builder.build_calculate(qualified_parent, children, qualified_terms)

    def qualify_where(
        self,
        unqualified: UnqualifiedWhere,
        context: PyDoughCollectionQDAG,
        is_child: bool,
    ) -> PyDoughCollectionQDAG:
        """
        Transforms an `UnqualifiedWhere` into a PyDoughCollectionQDAG node.

        Args:
            `unqualified`: the UnqualifiedWhere instance to be transformed.
            `builder`: a builder object used to create new qualified nodes.
            `context`: the collection QDAG whose context the collection is being
            evaluated within.
            `is_child`: whether the collection is being qualified as a child
            of a child operator context, such as CALCULATE or PARTITION.

        Returns:
            The PyDough QDAG object for the qualified collection node.

        Raises:
            `PyDoughUnqualifiedException` or `PyDoughQDAGException` if something
            goes wrong during the qualification process, e.g. a term cannot be
            qualified or is not recognized.
        """
        unqualified_parent: UnqualifiedNode = unqualified._parcel[0]
        unqualified_cond: UnqualifiedNode = unqualified._parcel[1]
        qualified_parent: PyDoughCollectionQDAG = self.qualify_collection(
            unqualified_parent, context, is_child
        )
        # Qualify the condition of the WHERE clause, storing the children
        # built along the way.
        children: list[PyDoughCollectionQDAG] = []
        qualified_cond = self.qualify_expression(
            unqualified_cond, qualified_parent, children
        )
        # Use the qualified children & condition to create a new WHERE node.
        return self.builder.build_where(qualified_parent, children, qualified_cond)

    def _expressions_to_collations(
        self, terms: Iterable[UnqualifiedNode] | list[UnqualifiedNode]
    ) -> list[UnqualifiedNode]:
        """
        Coerces nodes to be collation terms if they are not already. For nodes
        that are not collation terms, uses configuration settings to determine
        if they should be ASC or DESC. The first term uses
        `collation_default_asc` config. If `propagate_collation` is True,
        subsequent terms use `propagate_collation` config to determine if they
        inherit the available collation from the previous term. If
        `propagate_collation` is False, terms without an explicit collation will
        use the default from `collation_default_asc`.

        Args:
            `terms`: the list of collation terms to be modified.

        Returns:
            The modified list of collation terms.
        """
        is_collation_propagated: bool = self._session.config.propagate_collation
        is_prev_asc: bool = self._session.config.collation_default_asc
        modified_terms: list[UnqualifiedNode] = []
        for idx, term in enumerate(terms):
            if isinstance(term, UnqualifiedCollation):
                modified_terms.append(term)
                if is_collation_propagated:
                    is_prev_asc = term._parcel[1]
            else:
                if is_prev_asc:
                    modified_terms.append(term.ASC())
                else:
                    modified_terms.append(term.DESC())
        return modified_terms

    def qualify_order_by(
        self,
        unqualified: UnqualifiedOrderBy,
        context: PyDoughCollectionQDAG,
        is_child: bool,
    ) -> PyDoughCollectionQDAG:
        """
        Transforms an `UnqualifiedOrderBy` into a PyDoughCollectionQDAG node.

        Args:
            `unqualified`: the UnqualifiedOrderBy instance to be transformed.
            `builder`: a builder object used to create new qualified nodes.
            `context`: the collection QDAG whose context the collection is being
            evaluated within.
            `is_child`: whether the collection is being qualified as a child
            of a child operator context, such as CALCULATE or PARTITION.

        Returns:
            The PyDough QDAG object for the qualified collection node.

        Raises:
            `PyDoughUnqualifiedException` or `PyDoughQDAGException` if something
            goes wrong during the qualification process, e.g. a term cannot be
            qualified or is not recognized.
        """
        unqualified_parent: UnqualifiedNode = unqualified._parcel[0]
        unqualified_terms: list[UnqualifiedNode] = unqualified._parcel[1]
        unqualified_terms = self._expressions_to_collations(unqualified_terms)

        qualified_parent: PyDoughCollectionQDAG = self.qualify_collection(
            unqualified_parent, context, is_child
        )
        # Qualify all of the collation terms, storing the children built along
        # the way.
        children: list[PyDoughCollectionQDAG] = []
        qualified_collations: list[CollationExpression] = []
        for term in unqualified_terms:
            qualified_term: PyDoughExpressionQDAG = self.qualify_expression(
                term, qualified_parent, children
            )
            assert isinstance(qualified_term, CollationExpression)
            qualified_collations.append(qualified_term)
        # Use the qualified children & collation to create a new ORDER BY node.
        if not qualified_collations:
            raise PyDoughUnqualifiedException(
                "ORDER BY requires a 'by' clause to be specified."
            )
        return self.builder.build_order(
            qualified_parent, children, qualified_collations
        )

    def qualify_top_k(
        self,
        unqualified: UnqualifiedTopK,
        context: PyDoughCollectionQDAG,
        is_child: bool,
    ) -> PyDoughCollectionQDAG:
        """
        Transforms an `UnqualifiedTopK` into a PyDoughCollectionQDAG node.

        Args:
            `unqualified`: the UnqualifiedTopK instance to be transformed.
            `builder`: a builder object used to create new qualified nodes.
            `context`: the collection QDAG whose context the collection is being
            evaluated within.
            `is_child`: whether the collection is being qualified as a child
            of a child operator context, such as CALCULATE or PARTITION.

        Returns:
            The PyDough QDAG object for the qualified collection node.

        Raises:
            `PyDoughUnqualifiedException` or `PyDoughQDAGException` if something
            goes wrong during the qualification process, e.g. a term cannot be
            qualified or is not recognized.
        """
        unqualified_parent: UnqualifiedNode = unqualified._parcel[0]
        records_to_keep: int = unqualified._parcel[1]
        # TODO: (gh #164) add ability to infer the "by" clause from a
        # predecessor
        assert unqualified._parcel[2] is not None, (
            "TopK does not currently support an implied 'by' clause."
        )
        unqualified_terms: list[UnqualifiedNode] = unqualified._parcel[2]
        unqualified_terms = self._expressions_to_collations(unqualified_terms)
        qualified_parent: PyDoughCollectionQDAG = self.qualify_collection(
            unqualified_parent, context, is_child
        )
        # Qualify all of the collation terms, storing the children built along
        # the way.
        children: list[PyDoughCollectionQDAG] = []
        qualified_collations: list[CollationExpression] = []
        for term in unqualified_terms:
            qualified_term: PyDoughExpressionQDAG = self.qualify_expression(
                term, qualified_parent, children
            )
            assert isinstance(qualified_term, CollationExpression)
            qualified_collations.append(qualified_term)
        if not qualified_collations:
            raise PyDoughUnqualifiedException(
                "TopK requires a 'by' clause to be specified."
            )
        # Use the qualified children & collation to create a new TOP K node.
        return self.builder.build_top_k(
            qualified_parent, children, records_to_keep, qualified_collations
        )

    def split_partition_ancestry(
        self, node: UnqualifiedNode, partition_ancestor: str | None = None
    ) -> tuple[UnqualifiedNode, UnqualifiedNode, list[str]]:
        """
        Divide the ancestry of the given node into two parts, returning a tuple
        of an ancestor node and a child node whose ancestry points to a ROOT
        node at the cutoff where it previously pointed to the ancestor, as well
        as a list of the ancestor names of the child node.

        Args:
            `node`: the node whose ancestry is to be split.
            `partition_ancestor`: the name of the ancestor to split at (
            only supports None, which means the split should occur just
            below the top-level ancestor).

        Returns:
            A tuple where the first element is the ancestor of all the data
            being partitioned, the second is the data being partitioned which
            now points to an root instead of the original ancestor, and the
            third is a list of the ancestor names.
        """

        # Base case: have reached the top of the ancestry tree.
        if isinstance(node, UnqualifiedRoot):
            return node, UnqualifiedRoot(self.graph), []

        new_ancestry: UnqualifiedNode
        new_child: UnqualifiedNode
        ancestry_names: list[str]

        # First, recursively handle the preceding node.
        match node:
            case (
                UnqualifiedAccess()
                | UnqualifiedCalculate()
                | UnqualifiedWhere()
                | UnqualifiedTopK()
                | UnqualifiedOrderBy()
                | UnqualifiedSingular()
                | UnqualifiedPartition()
                | UnqualifiedBest()
                | UnqualifiedCross()
            ):
                parent: UnqualifiedNode = node._parcel[0]
                new_ancestry, new_child, ancestry_names = self.split_partition_ancestry(
                    parent, partition_ancestor
                )
            case _:
                # Any other unqualified node would mean something is malformed.
                raise PyDoughUnqualifiedException(
                    f"Unsupported collection node for `split_partition_ancestry`: {node.__class__.__name__}"
                )

        # Identify whether the current node vs the previous node is the
        # splitting point for the partitioned data vs its ancestry.
        if (
            isinstance(new_child, UnqualifiedRoot)
            and (
                isinstance(node, UnqualifiedPartition)
                or (
                    isinstance(node, UnqualifiedAccess)
                    and node._parcel[1] != self.graph.name
                )
            )
            and ((partition_ancestor is None) or (partition_ancestor in ancestry_names))
        ):
            if isinstance(node, UnqualifiedAccess):
                new_child = UnqualifiedAccess(
                    UnqualifiedRoot(self.graph), *node._parcel[1:]
                )
            else:
                new_child = UnqualifiedPartition(
                    UnqualifiedRoot(self.graph), *node._parcel[1:]
                )
            ancestry_names.append(node._parcel[1])
            return new_ancestry, new_child, ancestry_names

        appending_to_ancestor: bool = isinstance(new_child, UnqualifiedRoot)

        build_node: list[UnqualifiedNode] = [
            new_ancestry if appending_to_ancestor else new_child
        ]

        # Append the current node either to the ancestry (if above the split
        # point) or the child node (if below the split point).
        match node:
            case UnqualifiedAccess():
                ancestry_names.append(node._parcel[1])
                build_node[0] = UnqualifiedAccess(build_node[0], *node._parcel[1:])
            case UnqualifiedPartition():
                ancestry_names.append(node._parcel[1])
                build_node[0] = UnqualifiedPartition(build_node[0], *node._parcel[1:])
            case UnqualifiedWhere():
                build_node[0] = UnqualifiedWhere(build_node[0], *node._parcel[1:])
            case UnqualifiedCalculate():
                build_node[0] = UnqualifiedCalculate(build_node[0], *node._parcel[1:])
            case UnqualifiedTopK():
                build_node[0] = UnqualifiedTopK(build_node[0], *node._parcel[1:])
            case UnqualifiedOrderBy():
                build_node[0] = UnqualifiedOrderBy(build_node[0], *node._parcel[1:])
            case UnqualifiedSingular():
                build_node[0] = UnqualifiedSingular(build_node[0], *node._parcel[1:])
            case UnqualifiedBest():
                build_node[0] = UnqualifiedBest(build_node[0], *node._parcel[1:])
            case UnqualifiedCross():
                build_node[0] = UnqualifiedCross(build_node[0], *node._parcel[1:])
            case _:
                # Any other unqualified node would mean something is malformed.
                raise PyDoughUnqualifiedException(
                    f"Unsupported collection node `split_partition_ancestry`: {node.__class__.__name__}"
                )

        if appending_to_ancestor:
            new_ancestry = build_node[0]
        else:
            new_child = build_node[0]

        return new_ancestry, new_child, ancestry_names

    def qualify_partition(
        self,
        unqualified: UnqualifiedPartition,
        context: PyDoughCollectionQDAG,
        is_child: bool,
    ) -> PyDoughCollectionQDAG:
        """
        Transforms an `UnqualifiedPartition` into a PyDoughCollectionQDAG node.

        Args:
            `unqualified`: the UnqualifiedPartition instance to be transformed.
            `builder`: a builder object used to create new qualified nodes.
            `context`: the collection QDAG whose context the collection is being
            evaluated within.
            `is_child`: whether the collection is being qualified as a child
            of a child operator context, such as CALCULATE or PARTITION.

        Returns:
            The PyDough QDAG object for the qualified collection node.

        Raises:
            `PyDoughUnqualifiedException` or `PyDoughQDAGException` if something
            goes wrong during the qualification process, e.g. a term cannot be
            qualified or is not recognized.
        """
        unqualified_parent: UnqualifiedNode = unqualified._parcel[0]
        child_name: str = unqualified._parcel[1]
        unqualified_terms: list[UnqualifiedNode] = unqualified._parcel[2]
        # Split the ancestor tree of unqualified nodes into the ancestor vs
        # child of the PARTITION, qualifying the former then the latter with
        # the former as its context.
        unqualified_parent, unqualified_child, _ = self.split_partition_ancestry(
            unqualified_parent, None
        )
        qualified_parent: PyDoughCollectionQDAG = self.qualify_collection(
            unqualified_parent, context, is_child
        )
        qualified_child: PyDoughCollectionQDAG = self.qualify_collection(
            unqualified_child, qualified_parent, True
        )
        # Qualify all of the partitioning keys (which, for now, can only be
        # references to expressions in the child), storing the children built
        # along the way (which should just be the child input).
        child_references: list[ChildReferenceExpression] = []
        children: list[PyDoughCollectionQDAG] = []
        for term in unqualified_terms:
            qualified_term: PyDoughExpressionQDAG = self.qualify_expression(
                term, qualified_child, children
            )
            assert isinstance(qualified_term, Reference), (
                "PARTITION currently only supports partition keys that are references to a scalar property of the collection being partitioned"
            )
            child_ref: ChildReferenceExpression = ChildReferenceExpression(
                qualified_child, 0, qualified_term.term_name
            )
            child_references.append(child_ref)
        # Use the qualified child & keys to create a new PARTITION node.
        partition: PartitionBy = self.builder.build_partition(
            qualified_parent, qualified_child, child_name, child_references
        )
        # Special case: if accessing as a child, wrap in a
        # ChildOperatorChildAccess term.
        if isinstance(unqualified_parent, UnqualifiedRoot) and is_child:
            return ChildOperatorChildAccess(partition)
        return partition

    def qualify_collection(
        self,
        unqualified: UnqualifiedNode,
        context: PyDoughCollectionQDAG,
        is_child: bool,
    ) -> PyDoughCollectionQDAG:
        """
        Transforms an `UnqualifiedNode` into a PyDoughCollectionQDAG node.

        Args:
            `unqualified`: the UnqualifiedNode instance to be transformed.
            `builder`: a builder object used to create new qualified nodes.
            `context`: the collection QDAG whose context the collection is being
            evaluated within.
            `is_child`: whether the collection is being qualified as a child
            of a child operator context, such as CALCULATE or PARTITION.

        Returns:
            The PyDough QDAG object for the qualified collection node.

        Raises:
            `PyDoughUnqualifiedException` or `PyDoughQDAGException` if something
            goes wrong during the qualification process, e.g. a term cannot be
            qualified or is not recognized.
        """
        answer: PyDoughQDAG = self.qualify_node(unqualified, context, [], is_child)
        if not isinstance(answer, PyDoughCollectionQDAG):
            raise pydough.active_session.error_builder.expected_collection(answer)
        return answer

    def qualify_expression(
        self,
        unqualified: UnqualifiedNode,
        context: PyDoughCollectionQDAG,
        children: list[PyDoughCollectionQDAG],
    ) -> PyDoughExpressionQDAG:
        """
        Transforms an `UnqualifiedNode` into a PyDoughExpressionQDAG node.

        Args:
            `unqualified`: the UnqualifiedNode instance to be transformed.
            `context`: the collection QDAG whose context the expression is being
            evaluated within.
            `children`: the list where collection nodes that must be derived
            as children of `context` should be appended.

        Returns:
            The PyDough QDAG object for the qualified expression node.

        Raises:
            `PyDoughUnqualifiedException` or `PyDoughQDAGException` if something
            goes wrong during the qualification process, e.g. a term cannot be
            qualified or is not recognized.
        """
        answer: PyDoughQDAG = self.qualify_node(unqualified, context, children, True)
        if not isinstance(answer, PyDoughExpressionQDAG):
            raise pydough.active_session.error_builder.expected_expression(answer)
        return answer

    def qualify_singular(
        self,
        unqualified: UnqualifiedSingular,
        context: PyDoughCollectionQDAG,
        is_child: bool,
    ) -> PyDoughCollectionQDAG:
        """
        Transforms an `UnqualifiedSingular` into a PyDoughCollectionQDAG node.

        Args:
            `unqualified`: the UnqualifiedSingular instance to be transformed.
            `context`: the collection QDAG whose context the singular is being
            evaluated within.
            `is_child`: whether the collection is being qualified as a child
            of a child operator context, such as CALCULATE or PARTITION.

        Returns:
            The PyDough QDAG object for the qualified singular node.
        """
        unqualified_parent: UnqualifiedNode = unqualified._parcel[0]
        answer: PyDoughCollectionQDAG = self.qualify_collection(
            unqualified_parent, context, is_child
        )
        return self.builder.build_singular(answer)

    def qualify_best(
        self,
        unqualified: UnqualifiedBest,
        context: PyDoughCollectionQDAG,
        is_child: bool,
    ) -> PyDoughCollectionQDAG:
        """
        Transforms an `UnqualifiedBEST` into a PyDoughCollectionQDAG node by
        expanding it into a WHERE call with RANKING, possibly followed by a
        SINGULAR call.

        Args:
            `unqualified`: the UnqualifiedBest instance to be transformed.
            `context`: the collection QDAG whose context the singular is being
            evaluated within.
            `is_child`: whether the collection is being qualified as a child
            of a child operator context, such as CALCULATE or PARTITION.

        Returns:
            The PyDough QDAG object for the qualified singular node.
        """

        unqualified_parent: UnqualifiedNode = unqualified._parcel[0]
        by: Iterable[UnqualifiedNode] = unqualified._parcel[1]
        per: str | None = unqualified._parcel[2]
        allow_ties: bool = unqualified._parcel[3]
        n_best: int = unqualified._parcel[4]

        # Qualify the parent context, then qualify the child data with regards
        # to the parent.
        qualified_parent: PyDoughCollectionQDAG = self.qualify_collection(
            unqualified_parent, context, is_child
        )

        # Generate the ranking/comparison call to append an appropriate WHERE
        # clause to the end of the result.
        kwargs: dict[str, object] = {"by": by, "allow_ties": allow_ties}
        if per:
            kwargs["per"] = per
        rank: UnqualifiedNode = UnqualifiedOperator(pydop.RANKING)(**kwargs)
        unqualified_cond: UnqualifiedNode = (
            (rank == n_best) if n_best == 1 else (rank <= n_best)
        )
        children: list[PyDoughCollectionQDAG] = []
        qualified_cond: PyDoughExpressionQDAG = self.qualify_expression(
            unqualified_cond, qualified_parent, children
        )

        # Build the final expanded window-based filter
        qualified_child: PyDoughCollectionQDAG = self.builder.build_where(
            qualified_parent, children, qualified_cond
        )

        # Extract the `levels` argument from the condition
        assert isinstance(qualified_cond, ExpressionFunctionCall)
        rank_call = qualified_cond.args[0]
        assert isinstance(rank_call, WindowCall)
        levels: int | None = rank_call.levels

        # Add `SINGULAR` if applicable (there is a levels argument and that
        # ancestor either is the context or is singular with regards to it).
        if n_best == 1 and not allow_ties and is_child:
            base: PyDoughCollectionQDAG = qualified_parent
            if levels is not None:
                for _ in range(levels):
                    assert base.ancestor_context is not None
                    base = base.ancestor_context
                relative_ancestor: PyDoughCollectionQDAG = context.starting_predecessor
                if (
                    base.starting_predecessor == relative_ancestor
                    or base.is_singular(relative_ancestor)
                    or base.is_ancestor(relative_ancestor)
                ):
                    qualified_child = self.builder.build_singular(qualified_child)
            else:
                # Do the same for a GLOBAL best.
                qualified_child = self.builder.build_singular(qualified_child)

        return qualified_child

    def qualify_cross(
        self,
        unqualified: UnqualifiedCross,
        context: PyDoughCollectionQDAG,
        is_child: bool,
    ) -> PyDoughCollectionQDAG:
        """Qualifies the UnqualifiedCross node into a PyDoughCollectionQDAG
        by transforming its parent and child nodes into their own
        qualified collections (Hybrid nodes).

        Args:
            `unqualified`: The unqualified cross node to qualify.
            `context`: The context in which the qualification is happening.
            `is_child`: Whether the node is being qualified as a child
            of a child operator context, such as CALCULATE or PARTITION.

        Returns:
            The qualified collection node.
        """
        unqualified_parent: UnqualifiedNode = unqualified._parcel[0]
        unqualified_child: UnqualifiedNode = unqualified._parcel[1]
        qualified_parent: PyDoughCollectionQDAG = self.qualify_collection(
            unqualified_parent, context, is_child
        )

        # Now build a GlobalContext pointing to the qualified parent as its
        # ancestor, and use this as the new context for the child.
        qualified_parent = GlobalContext(self.graph, qualified_parent)

        # If the parent is the root, then the child access is a child operator
        # child access.
        if isinstance(unqualified_parent, UnqualifiedRoot):
            qualified_parent = ChildOperatorChildAccess(qualified_parent)

        # Qualify the child collection with the (augmented) parent as its
        # context.
        qualified_child: PyDoughCollectionQDAG = self.qualify_collection(
            unqualified_child,
            qualified_parent,
            False,
        )

        return qualified_child

    def qualify_node(
        self,
        unqualified: UnqualifiedNode,
        context: PyDoughCollectionQDAG,
        children: list[PyDoughCollectionQDAG],
        is_child: bool,
    ) -> PyDoughQDAG:
        """
        Transforms an UnqualifiedNode into a PyDoughQDAG node that can be either
        a collection or an expression.

        Args:
            `unqualified`: the UnqualifiedNode instance to be transformed.
            `context`: the collection QDAG whose context the expression is being
            evaluated within.
            `children`: the list where collection nodes that must be derived
            as children of `context` should be appended.
            `is_child`: whether the collection is being qualified as a child
            of a child operator context, such as CALCULATE or PARTITION.

        Returns:
            The PyDough QDAG object for the qualified node. The result can be either
            an expression or a collection.

        Raises:
            `PyDoughUnqualifiedException` or `PyDoughQDAGException` if something
            goes wrong during the qualification process, e.g. a term cannot be
            qualified or is not recognized.
        """
        answer: PyDoughQDAG
        match unqualified:
            case UnqualifiedRoot():
                # Special case: when the root has been reached, it is assumed
                # to refer to the context variable that was passed in.
                answer = context
            case UnqualifiedAccess():
                answer = self.qualify_access(unqualified, context, children, is_child)

            case UnqualifiedCalculate():
                answer = self.qualify_calculate(unqualified, context, is_child)
            case UnqualifiedWhere():
                answer = self.qualify_where(unqualified, context, is_child)
            case UnqualifiedOrderBy():
                answer = self.qualify_order_by(unqualified, context, is_child)
            case UnqualifiedTopK():
                answer = self.qualify_top_k(unqualified, context, is_child)
            case UnqualifiedPartition():
                answer = self.qualify_partition(unqualified, context, is_child)
            case UnqualifiedLiteral():
                answer = self.qualify_literal(unqualified)
            case UnqualifiedOperation():
                answer = self.qualify_operation(unqualified, context, children)
            case UnqualifiedWindow():
                answer = self.qualify_window(unqualified, context, children)
            case UnqualifiedBinaryOperation():
                answer = self.qualify_binary_operation(unqualified, context, children)
            case UnqualifiedCollation():
                answer = self.qualify_collation(unqualified, context, children)
            case UnqualifiedSingular():
                answer = self.qualify_singular(unqualified, context, is_child)
            case UnqualifiedBest():
                answer = self.qualify_best(unqualified, context, is_child)
            case UnqualifiedCross():
                answer = self.qualify_cross(unqualified, context, is_child)
            case _:
                raise PyDoughUnqualifiedException(
                    f"Cannot qualify {unqualified.__class__.__name__}: {unqualified!r}"
                )
        return answer


def qualify_node(unqualified: UnqualifiedNode, session: PyDoughSession) -> PyDoughQDAG:
    """
    Transforms an UnqualifiedNode into a qualified node.

    Args:
        `unqualified`: the UnqualifiedNode instance to be transformed.
        `session`: the session whose information should be used to derive
        necessary information for the qualification, such as the graph and
        configurations.

    Returns:
        The PyDough QDAG object for the qualified node. The result can be either
        an expression or a collection.

    Raises:
        `PyDoughUnqualifiedException` or `PyDoughQDAGException` if something
        goes wrong during the qualification process, e.g. a term cannot be
        qualified or is not recognized.
    """
    qual: Qualifier = Qualifier(session)
    return qual.qualify_node(
        unqualified, qual.builder.build_global_context(), [], False
    )


def qualify_term(
    collection: PyDoughCollectionQDAG, term: UnqualifiedNode, session: PyDoughSession
) -> tuple[list[PyDoughCollectionQDAG], PyDoughQDAG]:
    """
    Transforms an UnqualifiedNode into a qualified node within the context of
    a collection, e.g. to learn about a subcollection or expression of a
    qualified PyDough collection..

    Args:
        `collection`: the qualified collection instance corresponding to the
        context in which the term is being qualified.
        `term`: the UnqualifiedNode instance to be transformed into a qualified
        node within the context of `collection`.
        `session`: the session whose information should be used to derive
        necessary information for the qualification, such as the graph and
        configurations.

    Returns:
        A tuple where the second entry is the PyDough QDAG object for the
        qualified term. The result can be either an expression or a collection.
        The first entry is a list of any additional children of `collection`
        that must be derived in order to evaluate `term`.

    Raises:
        `PyDoughUnqualifiedException` or `PyDoughQDAGException` if something
        goes wrong during the qualification process, e.g. a term cannot be
        qualified or is not recognized.
    """
    qual: Qualifier = Qualifier(session)
    children: list[PyDoughCollectionQDAG] = []
    return children, qual.qualify_node(term, collection, children, True)
