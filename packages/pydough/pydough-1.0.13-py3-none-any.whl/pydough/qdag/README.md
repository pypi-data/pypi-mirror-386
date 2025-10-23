# PyDough QDAG Module

This module deals with the qualified DAG (QDAG) structure used as an intermediary representation after unqualified nodes and before the relational tree. The QDAG nodes represent collections and expressions in a structured manner that can be further processed and transformed.

## Available APIs

The QDAG module provides the following notable APIs:

### Base Classes

- `PyDoughQDAG`: Base class for all QDAG nodes, including collections and expressions. Contains information about how to compare QDAG nodes for equality & place them in hash sets.

### [Collection Nodes](collections/README.md)

The sub-module of the PyDough QDAG module class definitions for collections.

### [Expression Nodes](expressions/README.md)

The sub-module of the PyDough QDAG module class definitions for expressions.

### Errors

- `PyDoughQDAGException`: Exception class for errors related to QDAG nodes.

### Node Builder

- `AstNodeBuilder`: Utility class for building QDAG nodes.

## Usage

### Building QDAG Nodes

To build QDAG nodes, use the `AstNodeBuilder` class. These APIs are only intended for internal use when the qualifier converts unqualified nodes into QDAG nodes.

Examples of how to use the node builder to construct QDAG nodes:

```python
from pydough.qdag import AstNodeBuilder, ChildOperatorChildAccess
from pydough.metadata import parse_json_metadata_from_file
from pydough.types import NumericType, StringType

# Define the graph metadata & create a node builder
graph = parse_json_metadata_from_file(...)
builder = AstNodeBuilder(graph)

# Build a literal node
# Equivalent PyDough code: `1`
literal_node = builder.build_literal(1, NumericType())

# Build a column property node
# Equivalent PyDough code: `TPCH.Orders.order_date`
column_node = builder.build_column("Orders", "order_date")

# Build a back reference expression node
# Equivalent PyDough code: `BACK(1).region_key`
back_reference_node = builder.build_back_reference_expression(table_collection, "region_key", 1)

# Build a global context node
# Equivalent PyDough code: `TCPH`
global_context_node = builder.build_global_context()

# Build a table collection access
# Equivalent PyDough code: `TPCH.Nations`
table_collection = builder.build_child_access("Nations", global_context_node)

# Build a reference node
# Equivalent PyDough code: `TPCH.Nations.name`
ref_name = "name"
pydough_type = table_collection.get_expr(ref_name).pydough_type
reference_node = builder.build_reference(table_collection, ref_name, pydough_type)

# Build an expression function call node
# Equivalent PyDough code: `LOWER(TPCH.Nations.name)`
function_call_node = builder.build_expression_function_call("LOWER", [reference_node])

# Build a child reference expression node
# Equivalent PyDough code: `TPCH.Nations.region.name`
sub_collection = builder.build_child_access("region", table_collection)
child_collection = ChildOperatorChildAccess(sub_collection)
child_reference_node = builder.build_child_reference_expression([child_collection], 0, "name")

# Build a CALCULATE node
# Equivalent PyDough code: `TPCH.Nations.CALCULATE(region_name=region.name)`
calculate_node = builder.build_calc(table_collection, [child_collection], [("region_name", child_reference_node)])

# Build a WHERE node
# Equivalent PyDough code: `TPCH.Nations.WHERE(region.name == "ASIA")`
condition = builder.build_expression_function_call(
    "EQU",
    [child_reference_node, builder.build_literal("ASIA", StringType())]
)
where_node = builder.build_where(table_collection, [child_collection], condition)

# Build a SINGULAR node
# Equivalent PyDough code: `Regions.CALCULATE(n_4_nation=nations.WHERE(key == 4).SINGULAR().name)`
# Build base Regions collection
global_context_node = builder.build_global_context()
regions_collection = builder.build_child_access("Regions", global_context_node)
# Access nations sub-collection
nations_sub_collection = builder.build_child_access("nations", regions_collection)
# Create WHERE(key == 4) condition

ref_name = "key"
pydough_type = nations_sub_collection.get_expr(ref_name).pydough_type
key_ref = builder.build_reference(nations_sub_collection, ref_name, pydough_type)
literal_4 = builder.build_literal(4, NumericType())
condition = builder.build_expression_function_call("EQU", [key_ref, literal_4])
# Build WHERE node with condition
where_node = builder.build_where(nations_sub_collection, [], condition)
# Create SINGULAR node from filtered result
singular_node = builder.build_singular(where_node)
# Build reference node for name
ref_name = "name"
pydough_type = singular_node.get_expr(ref_name).pydough_type
reference_node = builder.build_reference(singular_node, ref_name, pydough_type)
# Build CALCULATE node with calculated term
calculate_node = builder.build_calc(regions_collection, [nations_sub_collection], [("n_4_nation", reference_node)])


# Build an ORDER BY node
# Equivalent PyDough code: `TPCH.Nations.ORDER_BY(name.ASC(na_pos='first'))`
collation_expression = builder.build_collation_expression(
    reference_node, True, False
)
order_by_node = builder.build_order(table_collection, [], [collation_expression])

# Build a TOP K node
# Equivalent PyDough code: `TPCH.Nations.TOP_K(5, by=name.ASC(na_pos='first'))`
top_k_node = builder.build_top_k(table_collection, [], 5 [collation_expression])

# Build a PARTITION BY node
# Equivalent PyDough code: `TPCH.PARTITION(Parts, name="p", by=part_type)`
part_collection = builder.build_child_access("Parts", global_context_node)
ref_name = "part_type"
pydough_type = part_collection.get_expr(ref_name).pydough_type
partition_key = builder.build_reference(part_collection, ref_name, pydough_type)
partition_by_node = builder.build_partition(part_collection, child_collection, "p", [partition_key])

# Build a child reference collection node
# Equivalent PyDough code: `Nations.CALCULATE(n_customers=COUNT(customers))`
customers_sub_collection = builder.build_child_access("customers", table_collection)
customers_child = ChildOperatorChildAccess(customers_sub_collection)
child_reference_collection_node = builder.build_child_reference_collection(
    table_collection, [customers_subcollection], 0
)
child_collection = 
count_call = builder.build_expression_function_call(
    "COUNT",
    [child_reference_collection_node]
)
calculate_node = builder.build_calc(table_collection, [customers_child], [("n_customers", count_call)])

# Build a window function call node
# Equivalent PyDough code: `RANKING(by=TPCH.Nations.name, levels=1, allow_ties=True)`
from pydough.operators import RANKING
window_call_node = builder.build_window_call(RANKING, [reference_node], 1, {"allow_ties": True})
```

### HAS/HASNOT Rewrite

The `has_hasnot_rewrite` function is used to transform `HAS` and `HASNOT` expressions in the QDAG. It is used in constructors of the various child operator classes to rewrite all `HAS(x)` into `COUNT(X) > 0` and all `HASNOT(X)` into `COUNT(X) == 0` unless they are in the conjunction of a `WHERE` clause.

Below are some examples of PyDough snippets that are/aren't affected by the rewrite.


```python
# Will be rewritten to `customers.CALCULATE(name, has_orders=COUNT(orders) > 0)`
customers.CALCULATE(name, has_orders=HAS(orders))

# Will be rewritten to `customers.CALCULATE(name, never_made_order=COUNT(orders) == 0)`
customers.CALCULATE(name, never_made_order=HASNOT(orders))

# Will not be rewritten
customers.WHERE(HAS(orders) & (nation.region.name == "EUROPE"))

# Will not be rewritten
customers.WHERE(HASNOT(orders))

# Will be rewritten to
# `customers.WHERE((COUNT(orders) > 0) | (nation.region.name == "EUROPE"))`
customers.WHERE(HAS(orders) | (nation.region.name == "EUROPE"))

# Will be rewritten to
# `customers.WHERE((COUNT(orders) == 0) | (acct_bal < 0))`
customers.WHERE(HASNOT(orders) | (acct_bal < 0))
```
