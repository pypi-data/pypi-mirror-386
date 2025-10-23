"""
This file maintains the relevant code that converts an unqualified tree
into an actual "evaluated" format. This is effectively the "end-to-end"
translation because the unqualified tree is the initial representation
of the code and depending on API being used, the final evaluated output
is either SQL text or the actual result of the code execution.
"""

import pandas as pd

import pydough
from pydough.configs import PyDoughConfigs, PyDoughSession
from pydough.conversion import convert_ast_to_relational
from pydough.database_connectors import DatabaseContext
from pydough.errors import (
    PyDoughSessionException,
)
from pydough.metadata import GraphMetadata
from pydough.qdag import PyDoughCollectionQDAG, PyDoughQDAG
from pydough.relational import RelationalRoot
from pydough.sqlglot import (
    convert_relation_to_sql,
    execute_df,
)
from pydough.unqualified import UnqualifiedNode, qualify_node

__all__ = ["to_df", "to_sql"]


def _load_session_info(**kwargs) -> PyDoughSession:
    """
    Load the session information from the active session unless it is found
    in the keyword arguments. The following variants are accepted:
    - If `session` is found, it is used directly.
    - If `metadata`, `config` and/or `database` are found, they are used to
      construct a new session.
    - If none of these are found, the active session is used.

    Args:
        **kwargs: The keyword arguments to load the session information from.

    Returns:
      The metadata graph, configuration settings and Database context.
    """

    # If there are no keyword arguments, return the active session.
    if len(kwargs) == 0:
        return pydough.active_session

    # If the session is provided, use it directly. Verify it has a metadata
    # graph attached, and there are no other keyword arguments.
    if "session" in kwargs:
        session = kwargs.pop("session")
        if not isinstance(session, PyDoughSession):
            raise PyDoughSessionException(
                f"Expected `session` to be a PyDoughSession, got {session.__class__.__name__}."
            )
        if session.metadata is None:
            raise PyDoughSessionException(
                "Cannot evaluate Pydough without a metadata graph. "
                "Please use `session.load_metadata_graph` to attach a graph to the session."
            )
        if kwargs:
            raise ValueError(f"Unexpected keyword arguments: {kwargs}")
        return session

    # Otherwise, load the individual components and construct a session.
    # If any of the components are missing, use the active session's value. The
    # metadata graph is required, so if it is missing from both the keyword
    # arguments and the active session, raise an error.
    metadata: GraphMetadata
    if "metadata" in kwargs:
        metadata = kwargs.pop("metadata")
    else:
        if pydough.active_session.metadata is None:
            raise PyDoughSessionException(
                "Cannot evaluate Pydough without a metadata graph. "
                "Please call `pydough.active_session.load_metadata_graph()`."
            )
        metadata = pydough.active_session.metadata
    config: PyDoughConfigs
    if "config" in kwargs:
        config = kwargs.pop("config")
    else:
        config = pydough.active_session.config
    database: DatabaseContext
    if "database" in kwargs:
        database = kwargs.pop("database")
    else:
        database = pydough.active_session.database
    assert not kwargs, f"Unexpected keyword arguments: {kwargs}"

    # Construct the new session
    new_session: PyDoughSession = PyDoughSession()
    new_session._metadata = metadata
    new_session._config = config
    new_session._database = database
    return new_session


def _load_column_selection(kwargs: dict[str, object]) -> list[tuple[str, str]] | None:
    """
    Load the column selection from the keyword arguments if it is found.
    The column selection must be a keyword argument `columns` that is either a
    list of strings, or a dictionary mapping output column names to the column
    they correspond to in the collection.

    Args:
        kwargs: The keyword arguments to load the column selection from.

    Returns:
        The column selection if it is found, otherwise None.
    """
    columns_arg = kwargs.pop("columns", None)
    result: list[tuple[str, str]] = []
    if columns_arg is None:
        return None
    elif isinstance(columns_arg, list):
        for column in columns_arg:
            if not isinstance(column, str):
                raise pydough.active_session.error_builder.bad_columns(columns_arg)
            result.append((column, column))
    elif isinstance(columns_arg, dict):
        for alias, column in columns_arg.items():
            if not isinstance(column, str) and isinstance(alias, str):
                raise pydough.active_session.error_builder.bad_columns(columns_arg)
            result.append((alias, column))
    else:
        raise pydough.active_session.error_builder.bad_columns(columns_arg)
    if len(result) == 0:
        raise pydough.active_session.error_builder.bad_columns(columns_arg)
    return result


def to_sql(node: UnqualifiedNode, **kwargs) -> str:
    """
    Convert the given unqualified tree to a SQL string.

    Args:
        `node`: The node to convert to SQL.
        `**kwargs`: Additional arguments to pass to the conversion for testing.
            From a user perspective these values should always be derived from
            the active session, but to allow a simple + extensible testing
            infrastructure in the future, any of these can be passed in using
            the name of the field in session.py.

    Returns:
        The SQL string corresponding to the unqualified query.
    """
    column_selection: list[tuple[str, str]] | None = _load_column_selection(kwargs)
    session: PyDoughSession = _load_session_info(**kwargs)
    qualified: PyDoughQDAG = qualify_node(node, session)
    if not isinstance(qualified, PyDoughCollectionQDAG):
        raise pydough.active_session.error_builder.expected_collection(qualified)
    relational: RelationalRoot = convert_ast_to_relational(
        qualified, column_selection, session
    )
    return convert_relation_to_sql(relational, session)


def to_df(node: UnqualifiedNode, **kwargs) -> pd.DataFrame:
    """
    Execute the given unqualified tree and return the results as a Pandas
    DataFrame.

    Args:
        `node`: The node to convert to a DataFrame.
        `**kwargs`: Additional arguments to pass to the conversion for testing.
            From a user perspective these values should always be derived from
            the active session, but to allow a simple + extensible testing
            infrastructure in the future, any of these can be passed in using
            the name of the field in session.py.

    Returns:
        The DataFrame corresponding to the unqualified query.
    """
    column_selection: list[tuple[str, str]] | None = _load_column_selection(kwargs)
    display_sql: bool = bool(kwargs.pop("display_sql", False))
    session: PyDoughSession = _load_session_info(**kwargs)
    qualified: PyDoughQDAG = qualify_node(node, session)
    if not isinstance(qualified, PyDoughCollectionQDAG):
        raise pydough.active_session.error_builder.expected_collection(qualified)
    relational: RelationalRoot = convert_ast_to_relational(
        qualified, column_selection, session
    )
    return execute_df(relational, session, display_sql)
