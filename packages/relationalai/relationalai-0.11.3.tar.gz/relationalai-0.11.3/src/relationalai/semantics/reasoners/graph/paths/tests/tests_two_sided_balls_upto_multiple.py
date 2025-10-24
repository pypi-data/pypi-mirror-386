from relationalai.semantics import Model, Integer, define, select
from relationalai.semantics.reasoners.graph.paths.graph import Graph
from relationalai.semantics.reasoners.graph.paths.path_algorithms.two_sided_balls_upto import two_balls_upto


# Test with grid graph
model_grid = Model("test_two_balls_upto_single grid", dry_run=False)

grid = Graph.construct_grid(model_grid, 3)

n = Integer.ref()
u = grid.Node.ref()

source_1 = grid.Node.new(row = 1, col = 1)
target_1 = grid.Node.new(row = 3, col = 3)

Source_1 = model_grid.Concept("Source_1", extends=[grid.Node])
Target_1 = model_grid.Concept("Target_1", extends=[grid.Node])

define(Source_1(source_1))
define(Target_1(target_1))

source_ball_1, target_ball_1 = two_balls_upto(grid, Source_1, Target_1)
iter_source_1 = select(n, u.row, u.col).where(source_ball_1(n, u)).to_df()
set_source_ball_1 = set(row for row in iter_source_1.itertuples(index = False, name = None))
iter_target_1 = select(n, u.row, u.col).where(target_ball_1(n, u)).to_df()
set_target_ball_1 = set(row for row in iter_target_1.itertuples(index = False, name = None))

expected_source_ball_1 = {
    (0, 1, 1), (1, 1, 2), (1, 2, 1), (2, 1, 3), (2, 2, 2), (2, 3, 1)
}

expected_target_ball_1 = {
    (0, 3, 3), (1, 3, 2), (1, 2, 3), (2, 1, 3), (2, 2, 2), (2, 3, 1)
}

assert (
    set_source_ball_1 == expected_source_ball_1 and
    set_target_ball_1 == expected_target_ball_1
)


# First test with diamond graph
model_diamond = Model("test_two_balls_upto_single diamond", dry_run=False)

diamond = Graph.construct_diamond(model_diamond, 3)

v = diamond.Node.ref()

source_2 = diamond.Node.new(id = 2)
target_2 = diamond.Node.new(id = 8)

Source_2 = model_diamond.Concept("Source_2", extends=[diamond.Node])
Target_2 = model_diamond.Concept("Target_2", extends=[diamond.Node])

define(Source_2(source_2))
define(Target_2(target_2))

source_ball_2, target_ball_2 = two_balls_upto(diamond, Source_2, Target_2)
iter_source_2 = select(n, v.id).where(source_ball_2(n, v)).to_df()
set_source_ball_2 = set(row for row in iter_source_2.itertuples(index = False, name = None))
iter_target_2 = select(n, v.id).where(target_ball_2(n, v)).to_df()
set_target_ball_2 = set(row for row in iter_target_2.itertuples(index = False, name = None))

expected_source_ball_2 = {
    (0, 2), (1, 4), (2, 5), (2, 6)
}

expected_target_ball_2 = {
    (0, 8), (1, 7), (2, 5), (2, 6)
}

assert (
    set_source_ball_2 == expected_source_ball_2 and
    set_target_ball_2 == expected_target_ball_2
)