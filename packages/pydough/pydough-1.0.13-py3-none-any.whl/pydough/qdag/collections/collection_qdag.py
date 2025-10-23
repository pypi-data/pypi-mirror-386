"""
Base definition of all PyDough QDAG collection types.
"""

__all__ = ["PyDoughCollectionQDAG"]


from abc import abstractmethod
from collections.abc import Iterable
from typing import Union

import pydough
from pydough.errors.error_utils import find_possible_name_matches
from pydough.qdag.abstract_pydough_qdag import PyDoughQDAG
from pydough.qdag.expressions.collation_expression import CollationExpression
from pydough.qdag.expressions.expression_qdag import PyDoughExpressionQDAG

from .collection_tree_form import CollectionTreeForm


class PyDoughCollectionQDAG(PyDoughQDAG):
    """
    The base class for QDAG nodes that represent a table collection accessed
    as a root.
    """

    def __repr__(self):
        return self.to_string()

    @property
    @abstractmethod
    def name(self) -> str:
        """
        The name of the collection.
        """

    def get_ancestral_names(self) -> list[str]:
        """
        The names of all ancestors of the collection, starting from the top.
        """
        if self.ancestor_context is None:
            return []
        return self.ancestor_context.get_ancestral_names() + [
            self.ancestor_context.name
        ]

    @property
    def ancestor_context(self) -> Union["PyDoughCollectionQDAG", None]:
        """
        The ancestor context from which this collection is derived. Returns
        None if there is no ancestor context because the collection is the top
        of the hierarchy.
        """

    @property
    @abstractmethod
    def preceding_context(self) -> Union["PyDoughCollectionQDAG", None]:
        """
        The preceding context from which this collection is derived, e.g. an
        ORDER BY term before a CALCULATE. Returns None if there is no preceding
        context, e.g. because the collection is the start of a pipeline
        within a larger ancestor context.
        """

    @property
    @abstractmethod
    def calc_terms(self) -> set[str]:
        """
        The list of expressions that would be retrieved if the collection
        were to have its results evaluated. This is the set of names in the
        most-recent CALCULATE, potentially with extra expressions added since
        then.
        """

    @property
    @abstractmethod
    def all_terms(self) -> set[str]:
        """
        The set of expression/subcollection names accessible by the context.
        """

    @property
    @abstractmethod
    def ancestral_mapping(self) -> dict[str, int]:
        """
        A mapping of names created by the current context and its ancestors
        describing terms defined inside a CALCULATE clause that are available
        to the current context & descendants to back-reference via that name
        to the number of ancestors up required to find the back-referenced
        term.
        """

    @property
    @abstractmethod
    def inherited_downstreamed_terms(self) -> set[str]:
        """
        A set of names created by indirect ancestors of the current context
        that can be used to back-reference. The specific index of the
        back-reference is handled during the hybrid conversion process, when
        implicit back-references are flushed to populate the base of the tree
        input to a PARTITION node.
        """

    @abstractmethod
    def is_singular(self, context: "PyDoughCollectionQDAG") -> bool:
        """
        Returns whether the collection is singular with regards to a
        context collection.

        Args:
            `context`: the collection that the singular/plural status of the
            current collection is being checked against.

        Returns:
            True if there is at most a single record of the current collection
            for each record of the context, and False otherwise.
        """

    def is_ancestor(self, collection: "PyDoughCollectionQDAG") -> bool:
        """
        Returns whether the current collection is an ancestor of the given
        collection.

        Args:
            `collection`: the collection that is being checked against.

        Returns:
            True if the current collection is an ancestor of `collection`,
            and False otherwise.
        """
        if collection.ancestor_context is self:
            return True
        if collection.ancestor_context is None:
            return False
        return self.is_ancestor(collection.ancestor_context)

    @property
    def starting_predecessor(self) -> "PyDoughCollectionQDAG":
        """
        Returns the predecessor at the start of the current chain of preceding
        collections, or `self` if this is the start of that chain. The process
        also unwraps any ChildOperatorChildAccess terms.
        """
        from pydough.qdag.collections import ChildOperatorChildAccess

        predecessor: PyDoughCollectionQDAG | None = self.preceding_context
        result: PyDoughCollectionQDAG
        if predecessor is None:
            result = self
        else:
            result = predecessor.starting_predecessor
        while isinstance(result, ChildOperatorChildAccess):
            result = result.child_access.starting_predecessor
        return result

    def verify_singular_terms(self, exprs: Iterable[PyDoughExpressionQDAG]) -> None:
        """
        Verifies that a list of expressions is singular with regards to the
        current collection, e.g. they can used as CALCULATE terms.

        Args:
            `exprs`: the list of expression to be checked.

        Raises:
            `PyDoughQDAGException` if any element of `exprs` is not singular with
            regards to the current collection.
        """
        relative_context: PyDoughCollectionQDAG = self.starting_predecessor
        for expr in exprs:
            if not expr.is_singular(relative_context):
                raise pydough.active_session.error_builder.cardinality_error(
                    collection=self, expr=expr
                )

    @abstractmethod
    def get_expression_position(self, expr_name: str) -> int:
        """
        Retrieves the ordinal position of an expression within the collection
        if it were to be printed.

        Args:
            `expr_name`: the name of the expression that is having its ordinal
            position derived.

        Returns:
            The position that the expression would be in, if the collection
            were printed.

        Raises:
            `PyDoughQDAGException` if `expr_name` is not a name of one of the
            expressions in `calc_terms`.
        """

    @abstractmethod
    def get_term(self, term_name: str) -> PyDoughQDAG:
        """
        Obtains an expression or collection accessible from the current context
        by name.

        Args:
            `term_name`: the name of the term that is being extracted.


        Returns:
            `PyDoughQDAGException` if `term_name` is not a name of one of the
            terms accessible in the context.
        """

    def get_expr(self, term_name: str) -> PyDoughExpressionQDAG:
        """
        Obtains an expression accessible from the current context by name.

        Args:
            `term_name`: the name of the term that is being extracted.


        Returns:
            `PyDoughQDAGException` if `term_name` is not a name of one of the
            terms accessible in the context, or is not an expression.
        """
        term = self.get_term(term_name)
        if not isinstance(term, PyDoughExpressionQDAG):
            raise pydough.active_session.error_builder.expected_expression(term)
        return term

    def get_collection(self, term_name: str) -> "PyDoughCollectionQDAG":
        """
        Obtains a collection accessible from the current context by name.

        Args:
            `term_name`: the name of the term that is being extracted.


        Returns:
            `PyDoughQDAGException` if `term_name` is not a name of one of the
            terms accessible in the context, or is not a collection.
        """
        term = self.get_term(term_name)
        if not isinstance(term, PyDoughCollectionQDAG):
            raise pydough.active_session.error_builder.expected_collection(term)
        return term

    @property
    @abstractmethod
    def ordering(self) -> list[CollationExpression] | None:
        """
        Returns the ordering collation used by the collection, or None if it is
        unordered.
        """

    @property
    @abstractmethod
    def unique_terms(self) -> list[str]:
        """
        Returns the list of names of terms that cause records of the collection
        to be uniquely identifiable.
        """

    @property
    @abstractmethod
    def standalone_string(self) -> str:
        """
        The string representation of the node within `to_string` without any
        context of its predecessors/ancestors.
        """

    @abstractmethod
    def to_string(self) -> str:
        """
        Returns a PyDough collection QDAG converted to a simple string
        reminiscent of the original PyDough code.
        """

    @abstractmethod
    def to_tree_form_isolated(self, is_last: bool) -> CollectionTreeForm:
        """
        Helper for `to_tree_form` that returns the `CollectionTreeForm` for
        the collection devoid of any information about its predecessors or
        ancestors.

        Args:
            `is_last`: boolean indicating if the current subtree is the last
            child of a ChildOperator node.
        """

    @abstractmethod
    def to_tree_form(self, is_last: bool) -> CollectionTreeForm:
        """
        Helper for `to_tree_string` that turns a collection into a
        CollectionTreeForm object which can be used to create a tree string.

        Args:
            `is_last`: boolean indicating if the current subtree is the last
            child of a ChildOperator node.
        """

    @property
    @abstractmethod
    def tree_item_string(self) -> str:
        """
        The string representation of the node on the single line that becomes
        the `item_str` in its `CollectionTreeForm`.
        """

    def to_tree_string(self) -> str:
        """
        Returns a PyDough collection QDAG converted into a tree-like string,
        structured. For example, consider the following PyDough snippet:

        ```
        Regions.CALCULATE(
            region_name=name,
        ).WHERE(
            ENDSWITH(name, 's')
        ).nations.WHERE(
            name != 'USA'
        ).CALCULATE(
            a=region_name,
            b=name,
            c=MAX(YEAR(suppliers.WHERE(STARTSWITH(phone, '415')).supply_records.lines.ship_date)),
            d=COUNT(customers.WHERE(acctbal > 0))
        ).WHERE(
            c > 1000
        ).ORDER_BY(
            d.DESC()
        )
        ```

        A valid string representation of this would be:

        ```
        ──┬─ TPCH
          ├─── TableCollection[Regions]
          ├─── Calculate[region_name=name]
          └─┬─ Where[ENDSWITH(name, 's')]
            ├─── SubCollection[nations]
            ├─── Where[name != 'USA']
            ├─┬─ Calculate[a=[region_name], b=[name], c=[MAX($2._expr1)], d=[COUNT($1)]]
            │ ├─┬─ AccessChild
            │ │ ├─ SubCollection[customers]
            │ │ └─── Where[acctbal > 0]
            │ └─┬─ AccessChild
            │   └─┬─ SubCollection[suppliers]
            │     ├─── Where[STARTSWITH(phone, '415')]
            │     └─┬─ SubCollection[supply_records]
            │       └─┬─ SubCollection[lines]
            │         └─── Calculate[_expr1=YEAR(ship_date)]
            ├─── Where[c > 1000]
            └─── OrderBy[d.DESC()]
        ```

        Returns:
            The tree-like string representation of `self`.
        """
        return "\n".join(self.to_tree_form(True).to_string_rows())

    def name_mismatch_error(
        self,
        term_name: str,
        atol: int = 2,
        rtol: float = 0.1,
        min_names: int = 3,
        insert_cost: float = 1.0,
        delete_cost: float = 1.0,
        substitution_cost: float = 1.0,
        capital_cost: float = 0.1,
    ) -> str:
        """
        Raises a name mismatch error with suggestions if possible.

        Args:
            `term_name`: The name of the term that caused the error.
            `atol`: The absolute tolerance for the minimum edit distance when
            determining whether to include a term as a suggestion; any term
            names with a minimum edit distance less than or equal to
            `closest_match + atol` will be included as a suggestion.
            `rtol`: The relative tolerance for the minimum edit distance when
            determining whether to include a term as a suggestion; any term
            names with a minimum edit distance less than or equal to
            `closest_match * (1 + rtol)` will be included as a suggestion.
            `min_names`: The minimum number of suggestions to include.
            `insert_cost`: The cost of inserting a character into the first
            string.
            `delete_cost`: The cost of deleting a character from the first
            string.
            `substitution_cost`: The cost of substituting a character.
            `capital_cost`: The cost of substituting a character with the same
            character with different capitalization.

        Returns:
            A string describing the error, including suggestions if available.
        """

        error_message: str = f"Unrecognized term of {self.to_string()}: {term_name!r}."
        suggestions: list[str] = find_possible_name_matches(
            term_name=term_name,
            candidates=self.all_terms,
            atol=atol,
            rtol=rtol,
            min_names=min_names,
            max_names=5,
            insert_cost=insert_cost,
            delete_cost=delete_cost,
            substitution_cost=substitution_cost,
            capital_cost=capital_cost,
        )

        # Check if there are any suggestions to add
        if len(suggestions) > 0:
            suggestions_str: str = ", ".join(suggestions)
            error_message += f" Did you mean: {suggestions_str}?"

        return error_message

    def verify_term_exists(self, term_name: str) -> None:
        """
        Verifies that a term exists in the collection, and raises an exception
        if it does not.

        Args:
            `term_name`: The name of the term to check whether it exists within
            the collection.

        Raises:
            `PyDoughException` if the term does not exist in the collection.
        """
        if term_name not in self.all_terms:
            raise pydough.active_session.error_builder.term_not_found(
                collection=self, term_name=term_name
            )
