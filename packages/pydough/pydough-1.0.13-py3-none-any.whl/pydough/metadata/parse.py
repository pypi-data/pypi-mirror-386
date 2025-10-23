"""
The logic used to parse PyDough metadata from a JSON file.
"""

__all__ = ["parse_json_metadata_from_file"]

import json

from pydough.errors import PyDoughMetadataException
from pydough.errors.error_utils import (
    HasPropertyWith,
    HasType,
    NoExtraKeys,
    extract_array,
    extract_bool,
    extract_object,
    extract_string,
    is_json_object,
    is_string,
)

from .collections import CollectionMetadata, SimpleTableMetadata
from .graphs import GraphMetadata
from .properties import (
    CartesianProductMetadata,
    GeneralJoinMetadata,
    PropertyMetadata,
    ReversiblePropertyMetadata,
    SimpleJoinMetadata,
)


def parse_json_metadata_from_file(file_path: str, graph_name: str) -> GraphMetadata:
    """
    Reads a JSON file to obtain a specific PyDough metadata graph.

    Args:
        `file_path`: the path to the file containing the PyDough metadata for
        the desired graph. This should be a JSON file.
        `graph_name`: the name of the graph from the metadata file that is
        being requested. This should be a key in the JSON file.

    Returns:
        The metadata for the PyDough graph, including all of the collections
        and properties defined within.

    Raises:
        `PyDoughMetadataException`: if the file is malformed in any way that
        prevents parsing it to obtain the desired graph.
    """
    with open(file_path) as f:
        as_json = json.load(f)
    if not isinstance(as_json, list):
        raise PyDoughMetadataException(
            "PyDough metadata expected to be a JSON file containing a JSON "
            + f"array of JSON objects representing metadata graphs, received: {as_json.__class__.__name__}."
        )
    for graph_json in as_json:
        HasType(dict).verify(graph_json, "metadata for PyDough graph")
        HasPropertyWith("name", is_string).verify(
            graph_json, "metadata for PyDough graph"
        )
        name: str = extract_string(graph_json, "name", "metadata for PyDough graph")
        if name == graph_name:
            version: str = extract_string(
                graph_json, "version", "metadata for PyDough graph"
            )
            match version:
                case "V2":
                    return parse_graph_v2(name, graph_json)
                case _:
                    raise PyDoughMetadataException(
                        f"Unrecognized PyDough metadata version: {version!r}"
                    )
    # If we reach this point, then the graph was not found in the file
    raise PyDoughMetadataException(
        f"PyDough metadata file located at {file_path!r} does not "
        + f"contain a graph named {graph_name!r}"
    )


def parse_graph_v2(graph_name: str, graph_json: dict) -> GraphMetadata:
    """
    Parses the JSON object for a PyDough graph in version 2 of the
    PyDough metadata format.

    Args:
        `graph_name`: the name of the graph being parsed.
        `graph_json`: the JSON object containing the metadata for the graph.

    Returns:
        The metadata for the PyDough graph, including all of the collections
        and properties defined within.

    Raises:
        `PyDoughMetadataException`: if the JSON does not meet the necessary
        structure properties.
    """
    verified_analysis: list[dict] = []
    additional_definitions: list[str] = []
    graph: GraphMetadata = GraphMetadata(
        graph_name,
        additional_definitions,
        verified_analysis,
        None,
        None,
        {},
    )

    # Parse and extract the metadata for all of the collections in the graph.
    collections_json: list = extract_array(graph_json, "collections", graph.error_name)
    for collection_json in collections_json:
        is_json_object.verify(
            collection_json,
            f"metadata for collection descriptions inside {graph.error_name}",
        )
        assert isinstance(collection_json, dict)
        parse_collection_v2(graph, collection_json)

    # Parse and extract the metadata for all of the relationships in the graph.
    relationships_json: list = extract_array(
        graph_json, "relationships", graph.error_name
    )
    for relationship_json in relationships_json:
        is_json_object.verify(
            relationship_json,
            f"metadata for relationship descriptions inside {graph.error_name}",
        )
        assert isinstance(relationship_json, dict)
        parse_relationship_v2(graph, relationship_json)

    # If it exists, parse the additional definitions and verified analysis
    # within the graph to verify they are well-formed.
    if "additional definitions" in graph_json:
        additional_definitions_json: list = extract_array(
            graph_json, "additional definitions", graph.error_name
        )
        for defn in additional_definitions_json:
            is_string.verify(
                defn,
                f"metadata for additional definitions inside {graph.error_name}",
            )
    if "verified pydough analysis" in graph_json:
        verified_analysis_json: list = extract_array(
            graph_json, "verified pydough analysis", graph.error_name
        )
        for verified_json in verified_analysis_json:
            is_json_object.verify(
                verified_json,
                f"metadata for verified pydough analysis inside {graph.error_name}",
            )
            assert isinstance(verified_json, dict)
            HasPropertyWith("question", is_string).verify(
                verified_json, "metadata for verified pydough analysis"
            )
            HasPropertyWith("code", is_string).verify(
                verified_json, "metadata for verified pydough analysis"
            )

    # Add all of the UDF definitions to the graph.
    if "functions" in graph_json:
        udf_definitions: list = extract_array(graph_json, "functions", graph.error_name)
        for udf_definition in udf_definitions:
            is_json_object.verify(
                udf_definition,
                f"metadata for UDF definitions inside {graph.error_name}",
            )
            assert isinstance(udf_definition, dict)
            parse_function_v2(graph, udf_definition)

    NoExtraKeys(GraphMetadata.allowed_fields).verify(graph_json, graph.error_name)
    for collection in graph.collections.values():
        assert isinstance(collection, CollectionMetadata)
        collection.verify_complete()
    return graph


def parse_collection_v2(graph: GraphMetadata, collection_json: dict) -> None:
    """
    Parses the JSON object for a PyDough collection in version 2 of the
    PyDough metadata format.

    Args:
        `graph`: the metadata for the graph that the collection would be
        added to. The collection will be added to this graph in-place.
        `collection_json`: the JSON object containing the metadata for the
        collection.

    Raises:
        `PyDoughMetadataException`: if the JSON does not meet the necessary
        structure properties.
    """
    # Extract the collection name and type from the JSON.
    collection_name: str = extract_string(
        collection_json, "name", f"metadata for collections within {graph.error_name}"
    )
    collection_type: str = extract_string(
        collection_json, "type", f"metadata for collections within {graph.error_name}"
    )
    # Dispatch to the appropriate collection type based on the type
    # specified in the JSON.
    match collection_type:
        case "simple table":
            SimpleTableMetadata.parse_from_json(graph, collection_name, collection_json)
        case _:
            raise PyDoughMetadataException(
                f"Unrecognized PyDough collection type for collection {collection_name!r}: {collection_type!r}"
            )


def parse_relationship_v2(graph: GraphMetadata, relationship_json: dict):
    """
    Parses the JSON object for a PyDough relationship in version 2 of the
    PyDough metadata format.

    Args:
        `graph`: the metadata for the graph that the relationship would be
        added to. The relationship will be added to one of the collections of
        the graph in-place.
        `relationship_json`: the JSON object containing the metadata for the
        relationship.

    Raises:
        `PyDoughMetadataException`: if the JSON does not meet the necessary
        structure properties.
    """
    # Extract the relationship name and type from the JSON.
    relationship_name: str = extract_string(
        relationship_json,
        "name",
        f"metadata for relationships within {graph.error_name}",
    )
    relationship_type: str = extract_string(
        relationship_json,
        "type",
        f"metadata for relationships within {graph.error_name}",
    )
    # Dispatch to the appropriate relationship type based on the type
    # specified in the JSON.
    match relationship_type:
        case "cartesian product":
            CartesianProductMetadata.parse_from_json(
                graph, relationship_name, relationship_json
            )
        case "simple join":
            SimpleJoinMetadata.parse_from_json(
                graph, relationship_name, relationship_json
            )
        case "general join":
            GeneralJoinMetadata.parse_from_json(
                graph, relationship_name, relationship_json
            )
        case "reverse":
            create_reverse_relationship(graph, relationship_name, relationship_json)
        case "custom":
            raise NotImplementedError("Custom relationships are not yet supported.")
        case _:
            raise PyDoughMetadataException(
                f"Unrecognized PyDough relationship type for relationship {relationship_name!r}: {relationship_type!r}"
            )


def create_reverse_relationship(
    graph: GraphMetadata, relationship_name: str, relationship_json: dict
) -> None:
    """
    Creates a reverse relationship from the JSON object for a PyDough
    relationship in version 2 of the PyDough metadata format.

    Args:
        `graph`: the metadata for the graph that the relationship would be
        added to. The relationship will be added to one of the collections of
        the graph in-place.
        `relationship_json`: the JSON object containing the metadata for the
        relationship.

    Raises:
        `PyDoughMetadataException`: if the JSON does not meet the necessary
        structure properties.
    """
    # Identify the property to be reversed and the two collections it connects.
    original_collection_name: str = relationship_json["original parent"]
    original_property_name: str = relationship_json["original property"]
    original_collection = graph.get_collection(original_collection_name)
    assert isinstance(original_collection, CollectionMetadata)
    original_property = original_collection.get_property(original_property_name)
    assert isinstance(original_property, PropertyMetadata)
    is_singular: bool = extract_bool(
        relationship_json,
        "singular",
        f"metadata for reverse relationship {relationship_name!r} relationships within {graph.error_name}",
    )
    always_matches: bool = relationship_json.get("always matches", False)
    if not isinstance(original_property, ReversiblePropertyMetadata):
        raise PyDoughMetadataException(
            f"Property {original_property_name!r} in collection {original_collection_name!r} is not reversible."
        )
    reverse_collection: CollectionMetadata = original_property.child_collection
    description: str | None = relationship_json.get("description", None)
    synonyms: list[str] | None = relationship_json.get("synonyms", None)
    extra_semantic_info: dict | None = relationship_json.get(
        "extra semantic info", None
    )
    # Build the reverse relationship and add it to the child collection.
    reverse_property: ReversiblePropertyMetadata = (
        original_property.build_reverse_relationship(
            relationship_name,
            is_singular,
            always_matches,
            description,
            synonyms,
            extra_semantic_info,
        )
    )
    original_property.reverse = reverse_property
    reverse_property.reverse = original_property
    reverse_collection.add_property(reverse_property)


def parse_function_v2(graph: GraphMetadata, udf_definition: dict) -> None:
    """
    Parses the JSON object for a PyDough UDF definition in version 2 of the
    PyDough metadata format.

    Args:
        `graph`: the metadata for the graph that the UDF would be added to.
        The UDF will be added to this graph in-place.
        `udf_definition`: the JSON object containing the metadata for the UDF.

    Raises:
        `PyDoughMetadataException`: if the JSON does not meet the necessary
        structure properties.
    """
    from pydough.pydough_operators import (
        ExpressionFunctionOperator,
        SqlAliasExpressionFunctionOperator,
        SqlMacroExpressionFunctionOperator,
        SqlWindowAliasExpressionFunctionOperator,
    )

    # Extract the function name and type from the JSON.
    function_name: str = extract_string(
        udf_definition,
        "name",
        f"metadata for UDF definition within {graph.error_name}",
    )
    error_name: str = (
        f"metadata for definition of UDF {function_name!r} within {graph.error_name}"
    )

    function_type: str = extract_string(udf_definition, "type", error_name).lower()

    # Extract the optional description for the UDF, if it exists.
    description: str | None = None
    if "description" in udf_definition:
        description = extract_string(udf_definition, "description", error_name)

    # Extract the verifier and deducer, if they exist.
    verifier: dict | None = None
    deducer: dict | None = None
    if "input signature" in udf_definition:
        verifier = extract_object(udf_definition, "input signature", error_name)
    if "output signature" in udf_definition:
        deducer = extract_object(udf_definition, "output signature", error_name)

    standard_keys: set[str] = {
        "name",
        "type",
        "description",
        "input signature",
        "output signature",
    }

    # Create the appropriate function operator based on the type.
    func: ExpressionFunctionOperator
    is_aggregation: bool = False
    sql_alias: str
    match function_type:
        case "sql alias":
            NoExtraKeys(standard_keys | {"sql function", "aggregation"}).verify(
                udf_definition, error_name
            )
            sql_alias = extract_string(udf_definition, "sql function", error_name)
            if "aggregation" in udf_definition:
                is_aggregation = extract_bool(udf_definition, "aggregation", error_name)
            func = SqlAliasExpressionFunctionOperator(
                function_name,
                sql_alias,
                is_aggregation,
                verifier,
                deducer,
                description,
            )
        case "sql window alias":
            NoExtraKeys(
                standard_keys | {"sql function", "requires order", "allows frame"}
            ).verify(udf_definition, error_name)
            sql_alias = extract_string(udf_definition, "sql function", error_name)
            required_order: bool = extract_bool(
                udf_definition, "requires order", error_name
            )
            allows_frame: bool = extract_bool(
                udf_definition, "allows frame", error_name
            )
            func = SqlWindowAliasExpressionFunctionOperator(
                function_name,
                sql_alias,
                allows_frame,
                required_order,
                verifier,
                deducer,
                description,
            )
        case "sql macro":
            NoExtraKeys(standard_keys | {"macro text", "aggregation"}).verify(
                udf_definition, error_name
            )
            macro_text: str = extract_string(udf_definition, "macro text", error_name)
            if "aggregation" in udf_definition:
                is_aggregation = extract_bool(udf_definition, "aggregation", error_name)
            func = SqlMacroExpressionFunctionOperator(
                function_name,
                macro_text,
                is_aggregation,
                verifier,
                deducer,
                description,
            )
        case _:
            raise PyDoughMetadataException(
                f"Unrecognized PyDough function type for {error_name}: {function_type!r}"
            )
    graph.add_function(function_name, func)
