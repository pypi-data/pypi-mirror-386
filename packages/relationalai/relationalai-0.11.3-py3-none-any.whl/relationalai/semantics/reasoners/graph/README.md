# graphs

This library allows users to define simple graphs, compute relations (algorithms) over those graphs, and work with the results, all in query builder.

This guide assumes you have a functional PyRel environment; to set one up, please see [the README for the relationalai-python repository](https://github.com/RelationalAI/relationalai-python/blob/main/README.md). It also assumes that you are familiar with query builder syntax; if not, please see [this overview of query builder syntax](https://github.com/RelationalAI/relationalai-python/blob/main/examples/builder/examples.py).

For information beyond what exists in this document, every public method (algorithm) of this library's `Graph` class carries a docstring describing its behavior and providing at least one usage example.


# Development status

This library is still in the early stages of development. Please expect to encounter all manner of rough edges. Not all planned functionality is implemented. The graph constructors have only minimal guard rails. The interfaces of several algorithms _will_ change. Performance is appropriate only for exploring with toy graphs; there are known asymptotic catastrophes. For a rough sense of status and roadmap, please see [the Jira initiative tracking this library's development](https://relationalai.atlassian.net/browse/RAI-38809).


## Quick start guide

Let's start with an example of building a toy directed, weighted graph, and
compute something over it. Here we'll build that graph from literals; later
we'll build similar graphs from existing `Concept`s.

```python
# Import necessary query builder components.
from relationalai.semantics import Model
from relationalai.semantics import Integer, Float
from relationalai.semantics import define, select

# Import necessary graphs components.
from relationalai.semantics.reasoners.graph import Graph
# The library's main component is the `Graph` class. Construct instances
# of this class to build graphs, and call member methods of instances
# to compute over those graphs.

# Construct a model, in which to define the graph.
model = Model("toy_graph") # dry_run=False, use_lqp=False)

# Construct an unweighted, directed graph in `model`.
graph = Graph(model, directed=True, weighted=False)

# When the `Graph` constructor is invoked as above, it generates
# `Node` and `Edge` concepts, populating which defines the graph.
# (Later we'll see how to "bring your own" node and edge concepts.)
Node, Edge = graph.Node, graph.Edge

# Define four nodes from integer literals.
n1 = Node.new(id=1)
n2 = Node.new(id=2)
n3 = Node.new(id=3)
n4 = Node.new(id=4)
define(n1, n2, n3, n4)

# Define four edges between those nodes, forming a kite (a triangle with a tail).
define(
    # The triangle.
    Edge.new(src=n1, dst=n2),
    Edge.new(src=n2, dst=n3),
    Edge.new(src=n3, dst=n1),
    # Its tail.
    Edge.new(src=n3, dst=n4),
)

# Compute the outdegree of each node. Note that computations over graphs
# are nominally exposed as `Relationship`s containing the results of
# those computations. For example, here we retrieve the graph's
# `outdegree` `Relationship`, a binary relation mapping
# each node (`Node`) to its outdegree (`Integer`).
outdegree = graph.outdegree()
# Every public method such as `outdegree` has a docstring
# that provides more information, including at least one usage example.

# Query and inspect the contents of the `degree` `Relationship`.
select(Node.id, Integer).where(outdegree(Node, Integer)).inspect()
# The output will show the degree for each node, roughly:
#    id  int
# 0   1    1
# 1   2    1
# 2   3    2
# 3   4    0
```

Great, but our models consist of `Concept`s and `Relationship`s, not literals!
How do we define graphs from those?

If we have existing concepts implying a graph, for example

A) a `Person` concept, with instances considered nodes, and
    a `Person.knows` property with instances considered edges; or
B) a `Person` concept, with instances considered nodes, and
    a `Transaction` concept, with properties `Transaction.payer`,
    `Transaction.payee`, and `Transaction.amount` considered edges;

then we can define our graph from these concepts and relationships.
We can of course do that by calling the graph constructor as above
```
graph = Graph(model, directed=..., weighted=...)
```
and then define the generated `Node` and `Edge` concepts
from the existing concepts, for example roughly via
```
define(graph.Node.new(person=Person))
define(graph.Edge.new(
    src=graph.Node.new(person=Person),
    dst=graph.Node.new(person=Person.knows),
))
```
but the `Graph` class allows us to do this more gracefully by providing
the existing concepts to the `Graph` constructor. There are two cases:

1) similar to situation (A) above, where we have a concept (`Person`)
    that can serve as the `Graph` class's `Node` concept, but no concept
    that conforms to its `Edge` concept; and
2) similar to situation (B) above, where we have concepts (`Person`, `Transaction`)
    that can serve as both the `Graph` class's `Node` and `Edge` concepts.

Let's modify our example above to illustrate the first case,
building a graph from an existing concept that can serve as
the graph's node concept.

```python
from relationalai.semantics import Model
from relationalai.semantics import Integer, Float
from relationalai.semantics import define, select

from relationalai.semantics.reasoners.graph import Graph

model = Model("toy_graph") # dry_run=False, use_lqp=False)

# Let's suppose we have a knows-network defined via a `Person` `Concept`
# and a `Person.knows` `Relationship`.
Person = model.Concept("Person")
Person.knows = model.Relationship("{Person} knows {Person}")

# Let's suppose our knows-network involves four people.
joe = Person.new(name="Joe")
jane = Person.new(name="Jane")
james = Person.new(name="James")
jennie = Person.new(name="Jennie")
define(joe, jane, james, jennie)

# Somehow their knows-relationship forms a kite!
define(
    # A knows triangle.
    joe.knows(jane),
    jane.knows(james),
    james.knows(joe),
    # The knows-triangle tail.
    james.knows(jennie),
)

# Let's build an unweighted graph from our knows-network, but supposing that
# "know"ing is symmetric, let's make the graph undirected this time.
graph = Graph(model, directed=False, weighted=False, node_concept=Person)
# By passing `Person` via `node_concept`, `graph.Node is Person`,
# but the `Graph` class still generates an `Edge` concept that needs population.
assert graph.Node is Person
Edge = graph.Edge

# Define the graph's edges from the knows-network's `Person.knows` `Relationship`.
define(Edge.new(src=Person, dst=Person.knows))

# Compute the number of other people each person knows,
# or in other words the degree of each node.
degree = graph.degree()

# Query and inspect the contents of the `degree` `Relationship`.
select(Person.name, Integer).where(degree(Person, Integer)).inspect()
# The output will show the degree for each person, roughly:
#      name  int
# 0   James    3
# 1    Jane    2
# 2  Jennie    1
# 3     Joe    2
```

Finally let's spice this up by trying the second case, bringing both
our own node and edge concepts.

```python
from relationalai.semantics import Model
from relationalai.semantics import Integer, Float
from relationalai.semantics import define, select

from relationalai.semantics.reasoners.graph import Graph

model = Model("toy_graph") # dry_run=False, use_lqp=False)

# Let's suppose again that we have a `Person` `Concept`...
Person = model.Concept("Person")

# ...with the usual suspects.
joe = Person.new(name="Joe")
jane = Person.new(name="Jane")
james = Person.new(name="James")
jennie = Person.new(name="Jennie")
define(joe, jane, james, jennie)

# But instead of a knows-network between those people,
# we will have a `Transaction` network:
Transaction = model.Concept("Transaction")
Transaction.payer = model.Relationship("{transaction:Transaction} has payer {payer:Person}")
Transaction.payee = model.Relationship("{transaction:Transaction} has payee {payee:Person}")
Transaction.amount = model.Relationship("{transaction:Transaction} has amount {amount:Float}")

# Amazingly, `Transaction`s between the usual suspects form a kite!
define(
    # A triangle.
    Transaction.new(payer=joe, payee=jane, amount=100.0),
    Transaction.new(payer=jane, payee=james, amount=200.0),
    Transaction.new(payer=james, payee=joe, amount=150.0),
    # Its tail.
    Transaction.new(payer=james, payee=jennie, amount=75.0)
)

# Let's build a directed, weighted graph from our transaction network.
graph = Graph(model, directed=True, weighted=True,
    node_concept=Person,
    edge_concept=Transaction,
    edge_src_relationship=Transaction.payer,
    edge_dst_relationship=Transaction.payee,
    edge_weight_relationship=Transaction.amount,
)
# By passing `Person` via `node_concept`, `graph.Node is Person`,
# and by passing `Transaction` via `edge_concept`, `graph.Edge is `Transaction`.
assert graph.Node is Person
assert graph.Edge is Transaction

# The graph's edges are already defined via the combination of
# the `Transaction` concept and the `payer`, `payee`, and `amount` relationships.

# Compute the transaction volume each person has been involved in,
# or in other words the weighted degree of each node.
weighted_degree = graph.degree()

# Query and inspect the contents of the `weighted_degree` `Relationship`.
select(Person.name, Float).where(weighted_degree(Person, Float)).inspect()
# The output will show the weighted degree for each person, roughly:
#      name  float
# 0   James  425.0
# 1    Jane  300.0
# 2  Jennie   75.0
# 3     Joe  250.0
```

Now that you have a graph, and assuming it's relatively small,
if you would like to visualize it `graph.visualize(...)` should do the trick.

Next let's look briefly at handling of multi-edges, i.e. in the directed case,
multiple edges defined with the same orientation between the same pair of nodes,
and in the undirected case, multiple edges defined between the same pair of nodes.

The `Graph` constructor accepts an optional `aggregator` keyword argument that
controls this handling. There are two selections: the default `None`, which derives
an `Error` in the presence of multi-edges, and the `"sum"` aggregation mode,
which aggregates multi-edges into a single edge under the hood when
computing the internal simple un/directed, un/weighted edge/weight list
representation over which this library's various operations work.

First let's walk through the default `aggregator = None` mode. Any express
or implied multi-edges will lead to an `Error`:
```python
from relationalai.semantics import Model
from relationalai.semantics import Float, define, select
from relationalai.semantics.reasoners.graph import Graph

model = Model("aggregator_none")
graph = Graph(model, directed=True, weighted=True, aggregator=None)
Node, Edge = graph.Node, graph.Edge

# Four nodes forming a kite.
node_a = Node.new(name="A")
node_b = Node.new(name="B")
node_c = Node.new(name="C")
node_d = Node.new(name="D")
define(node_a, node_b, node_c, node_d)

# The edges constituting the kite's triangle.
edge_ab_1 = Edge.new(src=node_a, dst=node_b, weight=867.0)
edge_bc = Edge.new(src=node_b, dst=node_c, weight=2.0)
edge_ca = Edge.new(src=node_c, dst=node_a, weight=3.0)

# The edge constitute the kite's tail
edge_cd = Edge.new(src=node_c, dst=node_d, weight=4.0)

# Additional edges between nodes `A` and `B`, constituting an explicit multi-edge!
edge_ab_2 = Edge.new(src=node_a, dst=node_b, weight=0.53)
edge_ab_3 = Edge.new(src=node_a, dst=node_b, weight=0.0009)

define(edge_ab_1, edge_bc, edge_ca, edge_cd, edge_ab_2, edge_ab_3)

# This demand will produce an `Error` surfacing the multi-edge
# and noting that multi-edges are disallowed when `aggregator=None`.
weighted_degree = graph.degree()
select(Node.name, Float).where(weighted_degree(Node, Float)).inspect()
```

What happens in `aggregator = "sum"` mode?
```python
from relationalai.semantics import Model
from relationalai.semantics import Float, Integer, define, select
from relationalai.semantics.reasoners.graph import Graph

model = Model("aggregator_sum_weighted")
graph = Graph(model, directed=True, weighted=True, aggregator="sum")
Node, Edge = graph.Node, graph.Edge

node_a = Node.new(name="A")
node_b = Node.new(name="B")
node_c = Node.new(name="C")
node_d = Node.new(name="D")
define(node_a, node_b, node_c, node_d)

edge_ab_1 = Edge.new(src=node_a, dst=node_b, weight=867.0)
edge_bc = Edge.new(src=node_b, dst=node_c, weight=2.0)
edge_ca = Edge.new(src=node_c, dst=node_a, weight=3.0)
edge_cd = Edge.new(src=node_c, dst=node_d, weight=4.0)

edge_ab_2 = Edge.new(src=node_a, dst=node_b, weight=0.53)
edge_ab_3 = Edge.new(src=node_a, dst=node_b, weight=0.0009)

define(edge_ab_1, edge_bc, edge_ca, edge_cd, edge_ab_2, edge_ab_3)

# The following demand will result in a single `A` to `B` edge under the hood,
# with weight the sum of the component edges: 867.5309.
weighted_degree = graph.degree()
select(Node.name, Float).where(weighted_degree(Node, Float)).inspect()
# Weighted degree sums incident edge weights per node, such that the
# above yields roughly the following:
#   name    float
# 0    A  870.5309   # (867.5309 from A→B, plus 3.0 from C→A)
# 1    B    869.53   # (867.5309 from A→B, plus 2.0 from B→C)
# 2    C      9.00   # (2.0 + 3.0 + 4.0)
# 3    D      4.00
```

Finally, what happes in `aggregator="sum"` mode if the graph is unweighted?

```python
from relationalai.semantics import Model
from relationalai.semantics import Integer, define, select
from relationalai.semantics.reasoners.graph import Graph

model = Model("aggregator_sum_unweighted")
graph = Graph(model, directed=False, weighted=False, aggregator="sum")
Node, Edge = graph.Node, graph.Edge

node_a = Node.new(name="A")
node_b = Node.new(name="B")
node_c = Node.new(name="C")
node_d = Node.new(name="D")
define(node_a, node_b, node_c, node_d)

edge_ab_1 = Edge.new(src=node_a, dst=node_b)
edge_bc = Edge.new(src=node_b, dst=node_c)
edge_ca = Edge.new(src=node_c, dst=node_a)
edge_cd = Edge.new(src=node_c, dst=node_d)

edge_ab_2 = Edge.new(src=node_a, dst=node_b)
edge_ab_3 = Edge.new(src=node_a, dst=node_b)

define(edge_ab_1, edge_ab_2, edge_ab_3, edge_bc, edge_ca, edge_cd)

# The following demand will result in a single `A` to `B` edge under the hood,
# with effective weight 1.0.
degree = graph.degree()
select(Node.name, Integer).where(degree(Node, Integer)).inspect()
# The above yields roughly the following. Notice that `A` and `B`
# are effectively connected once, not three times:
#   name  int
# 0    A    2
# 1    B    2
# 2    C    3
# 3    D    1
```

# Core concepts

## The `Graph` class

The library's central component is the `Graph` class. Define graphs by
constructing instances of this class, and call member methods on such instances
to compute over those graphs.

`Graph`s may be directed or undirected, and weighted or unweighted. The required
`model`, `directed`, and `weighted` keyword arguments respectively allow
specification of the model to build the graph in, whether the graph should
be un/directed, and whether the graph should be un/weighted.

For example, the following constructs a directed, weighted graph:
```
graph = Graph(directed=True, weighted=True)
```

When the `Graph` constructor is invoked as above, instances of the `Graph` class
contain generated `Node` and `Edge` concepts, population of which allows for rich,
high-level definition of property multigraphs, which are projected to
simple graphs under the hood:
```
Node, Edge = graph.Node, graph.Edge

# Define three `Node`s from string literals.
joe_node = Node.new(name="Joe")
jane_node = Node.new(name="Jane")
james_node = Node.new(name="James")
define(joe_node, jane_node, james_node)

# Define `Edge`s forming a directed, weighted triangle between those `Node`s.
define(
    Edge.new(src=joe_node, dst=jane_node, weight=1.0),
    Edge.new(src=jane_node, dst=james_node, weight=2.0),
    Edge.new(src=james_node, dst=joe_node, weight=3.0),
)
```
Every `Edge` must have a `src` and `dst`. If the graph is weighted, every edge
must have a `weight`; if the graph is unweighted, no edge may have a `weight`.
`Error`s are derived when these conditions don't hold. `Node`s and `Edge`s
may otherwise have any number and kind of properties attached to them; note that
all properties mentioned in `Node.new(...)` and `Edge.new(...)` get rolled into
the correspondingly defined `Node`'s / `Edge`'s identity, such that, e.g.,
```
define(
    Node.new(id=1, color="pink"),
    Node.new(id=1, color="sky blue"),
)
define(
    Edge.new(src=joe_node, dst=jane_node, weight=1.0, txid=1),
    Edge.new(src=joe_node, dst=jane_node, weight=1.0, txid=2),
)
```
defines two distinct `Node`s and two distinct `Edge`s (a multi-edge).

The `Graph` class constructor accepts an optional `aggregator` keyword argument,
which at this time accepts `None`  and `"sum"` values; this selection controls
handling of multi-edges:
- When `aggregator = None`, multi-edges, express or implied, result in derivation
of an `Error`.
- With `aggregator = sum`, when projecting from the rich, high-level graph
specification in terms of `Node` and `Edge` concepts to the underlying simple
un/directed, un/weighted (edge-/weight- list) graph representation over which
to compute, multi-edges are collapsed into single edges with (if the graph is
weighted) aggregated weights. Multi-edges in un/directed, weighted graphs result
in a single un/directed edge with sum-aggregated weight. Multi-edges in un/directed,
unweighted graphs result in a single un/directed edge with an effective weight of 1.0.

At this time, `weight`s must be non-negative (zero or positive) `Float`s,
and may not be `inf` or `NaN`. In the near future, `Error`s will be derived
when these conditions don't hold.

Alternatively, the `Graph` constructor also accepts a `node_concept` argument,
or that plus `edge_concept`, `edge_src_relationship`, `edge_dst_relationship`,
and (if the graph is weighted) `edge_weight_relationship` arguments.

For example, the following mode of construction
```
graph = Graph(model, directed=..., weighted=..., node_concept=Person)`
```
results in the existing `Person` concept serving as the graph's node concept:
```
assert graph.Node is Person
```
though it still generates an `Edge` concept that must be populated as above.

Another example, the following mode of construction:
```
graph = Graph(model, directed=True, weighted=True,
    node_concept=Person,
    edge_concept=Transaction,
    edge_src_relationship=Transaction.payer,
    edge_dst_relationship=Transaction.payee,
    edge_weight_relationship=Transaction.amount
)
```
results in the existing `Person` concept serving as the graph's node concept
```
assert graph.Node is Person
```
and the existing `Transaction` concept serving as the graph's edge concept
```
assert graph.Edge is Transaction
```
with the `Transaction.payer`, `Transaction.payee`, and `Transaction.weight`
relationships serving as the edge concept's source, destination, and weight
relationships.

(Please see the quick start guide above for more complete examples.)

If any of the edge concept and associated edge relationships are provided,
they must all be provided, as well as a node concept. (If the graph is weighted,
the edge weight relationship must be included in that cohort; if it is unweighted,
an edge weight relationship must _not_ be included in that cohort).

Each edge relationship must be binary, and must map from the edge concept to,
for the edge source and destination relationships, the node concept, and
for the weight relationship, the `Float` concept.

The model to which these concepts and relationships are attached
must be consistent among them, and with the model passed explicitly
to the `Graph` constructor.

Additionally, equivalents of all of the constraints described above for
the generated `Node` and `Edge` constraints must hold for user-provided node
and edge concepts and relationships.


## Computing over `Graph`s

To compute over a graph, call member methods, for example:
```
degree = graph.degree()
```
Such methods return `Relationship`s that contain the result of the corresponding
computation. For example, in this case `degree` binds an arity-two `Relationship`
that maps from `Node`s to corresponding `Integer` degrees, conceptually:
```
Relationship("{node:Node} has {degree:Integer}")
```
Such `Relationship`s can be used like any other query builder `Relationship`.
For example, we could inspect that `Relationship`'s contents to see the
degrees of the `Node`s in the graph:
```
degree.inspect()
```

There are notable exceptions, namely `is_connected` at time of this writing,
that return a query builder logic `Fragment` instead of a `Relationship`.
In the case of `is_connected`, this `Fragment` is a condition (`where` clause)
that can be uesd as a filter on whether the graph is connected. In future,
other member methods may return other `Fragment`s, for example in-line logic
for relations such as `degree`, as an alternative to receiving a corresponding
`Relationship`.

Some member methods, corresponding to parameterized algorithms, accept
keyword arguments that provide algorithm configuration. (At time of this writing,
none of the relevant algorithms have landed, but all of them have been stubbed
out.) For example, to compute `pagerank` over a graph with given damping
factor and convergence tolerance:
```
pagerank = graph.pagerank(
    damping_factor=0.9,
    tolerance=1e-7
)
```

# Algorithm implementation status

This list is rapidly evolving; it may be out of date. The most up to date
reference is the set of member methods of the `Graph` class.

**NOTE!** Please note that the interface to some of this functionality _will_ change.
(Notably, as we work to remove demand transformation, the interface for any
relation that was/is on-demand will change. Practically speaking, that includes
any relation that produces more tuples than roughly a linear number
in the number of nodes in the graph. Other interfaces may change in that
process as well.)

As of this writing, the following algorithms are available:
- num_nodes
- num_edges
- neighbor
- inneighbor
- outneighbor
- common_neighbor
- degree
- indegree
- outdegree
- weighted_degree
- weighted_indegree
- weighted_outdegree
- distance
- diameter_range
- reachable_from
- is_connected
- weakly_connected_component
- adamic_adar
- cosine_similarity
- jaccard_similarity
- preferential_attachment
- local_clustering_coefficient
- average_clustering_coefficient
- degree_centrality
- triangle
- num_triangles
- triangle_count
- unique_triangle

The following algorithms are stubbed out, but not yet implemented
(will yield a `NotImplemented` exception when called):
- pagerank
- infomap
- louvain
- label_propagation
- eigenvector_centrality
- betweenness_centrality
- triangle_community


## Testing

For more details about testing (local and in CI), refer the graphs test
[README.md](../../../../../tests/early_access/graphs/README.md).

Please see the [README.md](tests/README.md) in this package's `tests` subdirectory for
explanation of this package's tests' present location, in
`relationalai-python/tests/early_access/graphs`.

### Local Testing

To run the tests locally, the relationalai-python repository's virtual environment
must be correctly set up (please see [the repository's README.md](../../../../../README.md)),
and assuming we are at that repository's top level:
```bash
cd relationalai-python # repository top level
pytest [-s] [--verbose] relationalai-python/tests/early-access/graphs/[test_${functionality}.py] [-k '${filter}']
```
where `-s`, `--verbose`, specification of a particular test file
`test_${functionality}.py` (e.g. `test_num_nodes.py`), and specification
of a test filter `-k ${filter}` (e.g. `-k 'multiple_self_loops`) are optional.


## Requirements [TODO]

- relationalai
