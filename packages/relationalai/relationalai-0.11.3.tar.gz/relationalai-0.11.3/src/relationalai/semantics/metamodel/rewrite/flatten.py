from __future__ import annotations
from dataclasses import dataclass
from typing import cast, Optional, TypeVar
from typing import Tuple

from relationalai.semantics.metamodel import builtins, ir, factory as f, helpers, types, visitor
from relationalai.semantics.metamodel.compiler import Pass, group_tasks
from relationalai.semantics.metamodel.util import OrderedSet, ordered_set, NameCache
from relationalai.semantics.metamodel import dependency
from relationalai.semantics.metamodel.util import FrozenOrderedSet, filter_by_type
from relationalai.semantics.metamodel.typer.typer import to_type, is_primitive

class Flatten(Pass):
    """
    Traverses the model's root to flatten it as much as possible. The result of this pass is
    a Logical root where all nested tasks that represent a rule in Rel are extracted to the
    top level.

    - nested logical with updates becomes a top-level logical (a rule)

    From:
        Logical
            Logical
                lookup1   <- scope is spread
                Logical
                    lookup2
                    derive foo
                Logical
                    lookup3
                    derive bar
    To:
        Logical
            Logical
                lookup1
                lookup2
                derive foo
            Logical
                lookup1
                lookup3
                derive bar

    - nested logical with aggregates becomes a top-level logical (a rule representing an aggregation)

    From:
        Logical
            Logical
                lookup1
                Logical
                    lookup2
                    aggregate1
                Logical
                    lookup3
                    aggregate2
                output
    To:
        Logical
            Logical
                lookup1
                lookup2
                aggregate1
                derive tmp1
            Logical
                lookup1
                lookup3
                aggregate2
                derive tmp2
            Logical
                lookup1
                lookup tmp1
                lookup tmp2
                output

    - a union becomes a top-level logical for each branch, writing into a temporary relation,
    and a lookup from that relation.

    From:
        Logical
            Logical
                Union
                    Logical
                        lookup1
                    Logical
                        lookup2
                output
    To:
        Logical
            Logical
                lookup1
                derive tmp1
            Logical
                lookup2
                derive tmp1
            Logical
                lookup tmp1
                output

    - a match becomes a top-level logical for each branch, each writing into its own temporary
    relation and a lookup from the last relation. The top-level logical for a branch derives
    into the temporary relation negating the previous branch:

    From:
        Logical
            Logical
                Match
                    Logical
                        lookup1
                    Logical
                        lookup2
                output
    To:
        Logical
            Logical
                lookup1
                derive tmp1
            Logical
                Union            <- tmp1() or (not temp1() and lookup2())
                    lookup tmp1
                    Logical
                        Not
                            lookup tmp1
                        lookup2
                        derive tmp2
            Logical
                lookup tmp2
                output
    """

    def __init__(self, handle_outputs: bool=True):
        super().__init__()
        self.name_cache = NameCache(start_from_one=True)
        self._handle_outputs = handle_outputs


    #--------------------------------------------------
    # Public API
    #--------------------------------------------------
    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        # create the context
        ctx = Flatten.Context(model, options)

        # rewrite the root
        result = self.handle(model.root, ctx)

        # the new body contains the extracted top level logicals and maybe the rewritten root
        body = ctx.rewrite_ctx.top_level if result.replacement is None else ctx.rewrite_ctx.top_level + [result.replacement]

        # create the new model, updating relations and root
        return ir.Model(
            model.engines,
            OrderedSet.from_iterable(model.relations).update(ctx.rewrite_ctx.relations).frozen(),
            model.types,
            ir.Logical(model.root.engine, tuple(), tuple(body))
        )

    #--------------------------------------------------
    # IR handlers
    #--------------------------------------------------

    class Context():
        def __init__(self, model: ir.Model, options: dict):
            self.rewrite_ctx = helpers.RewriteContext()
            self.info = dependency.analyze(model.root)
            self.options = options
            # when we extract a nested logical (due to agg, match, union, etc), we also
            # extract together its dependencies, and we leave behind a different nested
            # logical as a reference, with a lookup to the extracted relation. This dict
            # keeps a map from the reference logical id to the set of tasks that where
            # extracted for it. This is used to optimize the resulting code, since we can
            # assume that the reference logical already includes those tasks.
            self.included: dict[int, OrderedSet[ir.Task]] = dict()
            # These are extra tasks to be added to the body of a logical when it is
            # extracted as a top-level logical. For example, when handling a match, we add
            # a couple of tasks here in case the branches have updates or aggregations that
            # cause the branch to be extracted, so that they include these tasks.
            self.extra_tasks = []


    @dataclass
    class HandleResult():
        replacement: Optional[ir.Task]

    def handle(self, task: ir.Task, ctx: Context) -> Flatten.HandleResult:
        if isinstance(task, ir.Logical):
            return self.handle_logical(task, ctx)
        elif isinstance(task, ir.Union):
            return self.handle_union(task, ctx)
        elif isinstance(task, ir.Match):
            return self.handle_match(task, ctx)
        elif isinstance(task, ir.Require):
            return self.handle_require(task, ctx)
        elif isinstance(task, ir.Not):
            return self.handle_not(task, ctx)
        else:
            return Flatten.HandleResult(task)


    def handle_logical(self, task: ir.Logical, ctx: Context):
        # keep track of what's the result of handling nested composites
        composites = group_tasks(task.body, {
            "composites": helpers.COMPOSITES
        })["composites"]
        all_composites_removed = len(composites) > 0

        # recursively handle children, collecting the replacements in the body
        body:OrderedSet[ir.Task] = ordered_set()
        for child in task.body:
            result = self.handle(child, ctx)
            if result.replacement is not None:
                ctx.info.replaced(child, result.replacement)
                extend_body(body, result.replacement)
                # nested composite was not completely removed
                if child in composites:
                    all_composites_removed = False

        # all children were extracted or all composites were removed without any effects
        # left and no outputs (so no way for outer dependencies), drop this logical
        if not body or (all_composites_removed and not any([isinstance(t, helpers.EFFECTS) for t in body]) and not ctx.info.task_outputs(task)):
            return Flatten.HandleResult(None)

        # now process the rewritten body
        groups = group_tasks(body.get_list(), {
            "outputs": ir.Output,
            "updates": ir.Update,
            "aggregates": ir.Aggregate,
            "ranks": ir.Rank,
        })

        # if there are outputs, adjust them (depending on the config for wide vs gnf)
        if groups["outputs"]:
            if self._handle_outputs:
                return self.adjust_outputs(task, body, groups, ctx)
            else:
                # When we do not handle outputs. For example, in SQL compiler. We need to leave output as a top-level element.
                ctx.rewrite_ctx.top_level.append(ir.Logical(task.engine, task.hoisted, tuple(body), task.annotations))
                return Flatten.HandleResult(None)

        # if there are updates, extract as a new top level rule
        if groups["updates"]:
            # add task dependencies to the body
            body.prefix(ctx.info.task_dependencies(task))
            # potentially add context extra tasks
            body.update(ctx.extra_tasks)
            ctx.rewrite_ctx.top_level.append(ir.Logical(task.engine, task.hoisted, tuple(body), task.annotations))
            return Flatten.HandleResult(None)

        if groups["aggregates"]:
            if len(groups["aggregates"]) > 1:
                # stop rewritting as we don't know how to handle this yet
                return Flatten.HandleResult(task)

            # there must be only one
            agg = cast(ir.Aggregate, groups["aggregates"].some())

            # add agg dependencies to the body
            body.prefix(ctx.info.task_dependencies(agg))

            # extract a new logical for the aggregate, exposing aggregate group-by and results
            exposed_vars = OrderedSet.from_iterable(list(agg.group) + helpers.aggregate_outputs(agg))
            name = helpers.create_task_name(self.name_cache, agg)
            connection = helpers.extract(agg, body, exposed_vars.get_list(), ctx.rewrite_ctx, name)

            # return a reference to the connection relation
            reference = f.logical([f.lookup(connection, exposed_vars.get_list())], task.hoisted)
            return Flatten.HandleResult(reference)

        if groups["ranks"]:
            if len(groups["ranks"]) > 1:
                # stop rewritting as we don't know how to handle this yet
                return Flatten.HandleResult(task)

            # there must be only one
            rank = cast(ir.Rank, groups["ranks"].some())

            # add rank dependencies to the body
            body.prefix(ctx.info.task_dependencies(rank))
            # for rank, we sort by the args, but the result includes the keys to preserve bag semantics.
            exposed_vars_raw = list(rank.projection) + list(rank.group) + list(rank.args) +[rank.result]
            # deduplicate vars
            exposed_vars = OrderedSet.from_iterable(exposed_vars_raw)
            name = helpers.create_task_name(self.name_cache, rank)
            connection = helpers.extract(rank, body, exposed_vars.get_list(), ctx.rewrite_ctx, name)

            # return a reference to the connection relation
            reference = f.logical([f.lookup(connection, exposed_vars.get_list())], task.hoisted)
            ctx.included[reference.id] = body
            return Flatten.HandleResult(reference)

        return Flatten.HandleResult(ir.Logical(task.engine, task.hoisted, tuple(body)))


    def handle_match(self, match: ir.Match, ctx: Context):
        # TODO: how to deal with malformed input like this?
        if not match.tasks:
            return Flatten.HandleResult(match)

        body = ctx.info.task_dependencies(match)
        exposed_vars = self.compute_exposed_vars(match, match.tasks, ctx)

        # negation len is the number of wildcards when negating a reference
        outputs = ctx.info.task_outputs(match)
        negation_len = len(outputs) if outputs else 0

        # collect the references to branch rules so that we union in the end
        references = []

        # a negated reference to the previous branch (e.g. "not branch1(...)")
        negated_reference = None

        # number of negated references currently in context (e.g. in the 3rd branch there
        # will be 2 negated references, "not branch1(...) and not branch2(...)")
        negated_references = 0
        for branch in match.tasks:
            # if there's a previous connection, add the negation of it to extra tasks
            if negated_reference:
                ctx.extra_tasks.append(negated_reference)
                negated_references += 1

            # the connection relation to be used for this branch
            name = helpers.create_task_name(self.name_cache, branch, "_match")
            relation = helpers.create_connection_relation(branch, exposed_vars, ctx.rewrite_ctx, name)
            branch_update = f.derive(relation, exposed_vars)
            ctx.extra_tasks.append(branch_update)

            # handle the branch
            result = self.handle(branch, ctx)

            # if there's no replacement, the branch was already extracted (e.g. by an update),
            # otherwise, we need to extract the branch as a rule writing into the connection
            if result.replacement:
                ctx.info.replaced(branch, result.replacement)

                branch_body: OrderedSet[ir.Task] = OrderedSet.from_iterable(body)
                extend_body(branch_body, result.replacement)
                # potentially add context extra tasks (negations of previous branches + derive into this branch)
                branch_body.update(ctx.extra_tasks)
                # extract the body
                ctx.rewrite_ctx.top_level.append(ir.Logical(match.engine, tuple(), tuple(branch_body)))

            # cleanup the branch update from context (but keep the negations)
            ctx.extra_tasks.pop()

            # record a reference to the branch connection and adjust the negated_reference
            reference = f.lookup(relation, exposed_vars)
            negated_reference = negate(reference, negation_len)
            references.append(reference)

        # we accumulate negations, in the end we remove them all
        for x in range(negated_references):
            ctx.extra_tasks.pop()

        # return a union of the references to the branches
        return Flatten.HandleResult(f.union(references, match.hoisted))


    def handle_union(self, union: ir.Union, ctx: Context):
        # TODO: how to deal with malformed input like this?
        if not union.tasks:
            return Flatten.HandleResult(union)

        body = ctx.info.task_dependencies(union)
        exposed_vars = self.compute_exposed_vars(union, union.tasks, ctx)

        name = helpers.create_task_name(self.name_cache, union)
        relation = helpers.create_connection_relation(union, exposed_vars, ctx.rewrite_ctx, name)
        for branch in union.tasks:

            # add an update to the context in case the branch is extracted
            branch_update = f.derive(relation, exposed_vars)
            ctx.extra_tasks.append(branch_update)

            # handle the branch
            result = self.handle(branch, ctx)

            # cleanup the branch update from context
            ctx.extra_tasks.pop()

            # if there's no replacement, the branch was already extracted (e.g. by an update),
            # otherwise, we need to extract the branch as a rule writing into the connection
            if result.replacement:
                # the branch has some replacement, we have to extract it as a top-level rule
                ctx.info.replaced(branch, result.replacement)
                branch_body: OrderedSet[ir.Task] = OrderedSet.from_iterable(body)
                extend_body(branch_body, result.replacement)
                branch_body.add(branch_update)
                # extract the body
                ctx.rewrite_ctx.top_level.append(ir.Logical(union.engine, tuple(), tuple(branch_body)))

        # return a reference to the connection relation
        reference = f.logical([f.lookup(relation, exposed_vars)], exposed_vars)
        return Flatten.HandleResult(reference)


    def compute_exposed_vars(self, task: ir.Task, branches: Tuple[ir.Task, ...], ctx: Context) -> list:
        """ Helper to compute the set of exposed vars for handle_match and handle_union. """
        exposed_vars = set_union(ctx.info.task_inputs(task), ctx.info.task_outputs(task))
        if exposed_vars:
            return exposed_vars
        # no exposed vars, so we try to use the common vars across all branches as context
        common_vars = helpers.collect_vars(branches[0])
        for branch in branches:
            branch_vars = helpers.collect_vars(branch)
            for v in common_vars:
                if v not in branch_vars:
                    common_vars.remove(v)
        # TODO - we should raise an error here if the set is empty
        return common_vars.get_list()


    def handle_require(self, req: ir.Require, ctx: Context):
        # only extract the domain if it is a somewhat complex Logical and there's more than
        # one check, otherwise insert it straight into all checks
        domain = req.domain
        # only generate logic for not discharged requires
        if builtins.discharged_annotation not in req.annotations:
            if len(req.checks) > 1 and isinstance(domain, ir.Logical) and len(domain.body) > 1:
                body = OrderedSet.from_iterable(domain.body)
                vars = helpers.hoisted_vars(domain.hoisted)
                name = helpers.create_task_name(self.name_cache, req)
                connection = helpers.extract(req, body, vars, ctx.rewrite_ctx, name)
                domain = f.logical([f.lookup(connection, vars)], vars)

            for check in req.checks:
                # only generate logic for checks that have errors and not discharged
                if check.error and builtins.discharged_annotation not in check.annotations:
                    handled_check_result = self.handle(check.check, ctx)
                    if handled_check_result.replacement:
                        body = ordered_set()
                        body.add(domain)
                        body.add(ir.Not(req.engine, handled_check_result.replacement))
                        if (isinstance(check.error, ir.Logical)):
                            body.update(check.error.body)
                        else:
                            # this is more general but may trip the current splinter
                            body.add(check.error)
                        ctx.rewrite_ctx.top_level.append(ir.Logical(req.engine, tuple(), tuple(body)))

        # currently we just drop the Require, but we should keep it here and link the
        # extracted logicals to it
        return Flatten.HandleResult(None)


    def handle_not(self, task: ir.Not, ctx: Context):
        # handle the sub-task of the Not
        result = self.handle(task.task, ctx)
        # there must be a replacement
        assert(result.replacement)

        # if the sub-task was really not replaced, just return the task, otherwise a new Not
        if result.replacement is task.task:
            return Flatten.HandleResult(task)
        else:
            return Flatten.HandleResult(ir.Not(
                task.engine,
                result.replacement,
                task.annotations
            ))

    #--------------------------------------------------
    # GNF vs wide output support
    #--------------------------------------------------
    def adjust_outputs(self, task: ir.Logical, body: OrderedSet[ir.Task], groups: dict[str, OrderedSet[ir.Task]], ctx: Context):

        # for wide outputs, only adjust the output task to include the keys.
        if ctx.options.get("wide_outputs", False):
            for output in groups["outputs"]:
                assert(isinstance(output, ir.Output))
                if output.keys:
                    body.remove(output)
                    body.add(self.rewrite_wide_output(output))
            # self.remove_subsumptions(body, ctx)
            return Flatten.HandleResult(ir.Logical(task.engine, task.hoisted, tuple(body), task.annotations))

        # for GNF outputs we need to generate a rule for each "column" in the output
        else:
            # first split outputs in potentially multiple outputs, one for each "column"
            for output in groups["outputs"]:
                assert(isinstance(output, ir.Output))
                if output.keys:
                    # we will replace the output bellow,
                    body.remove(output)

                    is_export = builtins.export_annotation in output.annotations

                    # generate an output for each "column"
                    # output looks like def output(:cols, :col000, key0, key1, value):
                    original_cols = OrderedSet()
                    for idx, alias in enumerate(output.aliases):
                        # skip None values which are used as a placeholder for missing values
                        if alias[1] is None:
                            continue
                        original_cols.add(alias[1])
                        self._generate_output_column(body, output, idx, alias, is_export)

                    idx = len(output.aliases)
                    for key in output.keys:
                        if key not in original_cols:
                            self._generate_output_column(body, output, idx, (key.name, key), is_export)
                            idx += 1

            # analyse the resulting logical to be able to pull dependencies
            logical = ir.Logical(task.engine, task.hoisted, tuple(body), task.annotations)
            info = dependency.analyze(logical)

            # now extract a logical for each output, bringing together its dependencies
            for output in filter_by_type(body, ir.Output):
                deps = info.task_dependencies(output)
                # TODO: verify safety of doing this
                # self.remove_subsumptions(deps, ctx)

                deps.add(output)
                ctx.rewrite_ctx.top_level.append(ir.Logical(task.engine, tuple(), tuple(deps)))

            return Flatten.HandleResult(None)

    def _generate_output_column(self, body: OrderedSet[ir.Task], output: ir.Output, idx: int, alias: tuple[str, ir.Value], is_export: bool):
        if not output.keys:
            return output

        aliases = [("cols", f.literal("cols", types.Symbol))] if not is_export else []
        aliases.append(("col", f.literal(f"col{idx:03}", types.Symbol)))

        for k in output.keys:
            aliases.append((f"key_{k.name}_{idx}", k))

        if (is_export and
            isinstance(alias[1], ir.Var) and
            (not is_primitive(alias[1].type) or alias[1].type == types.Hash)):

            uuid = f.var(f"{alias[0]}_{idx}_uuid", types.String)
            body.add(f.lookup(builtins.uuid_to_string, [alias[1], uuid]))
            aliases.append((uuid.name, uuid))
        else:
            aliases.append(alias)

        body.add(ir.Output(
            output.engine,
            FrozenOrderedSet.from_iterable(aliases),
            output.keys,
            output.annotations
        ))


    def remove_subsumptions(self, body:OrderedSet[ir.Task], ctx: Context):
        # remove from the body all the tasks that are subsumed by some other task in the set;
        # this can be done because some tasks are references to extracted nested logical that
        # contain filters they dependend on, so we don't need those filters here if the
        # reference is present.
        for logical in filter_by_type(body, ir.Logical):
            if logical.id in ctx.included:
                # if the logical id is included, it means it's a reference to an extracted
                # rule, so remove all other items in the body that are already included in
                # the body referenced by it
                for item in body:
                    if item in ctx.included[logical.id]:
                        body.remove(item)


    def rewrite_wide_output(self, output: ir.Output):
        assert(output.keys)

        # only prefix keys that are not already in the output
        prefix_keys = []
        for key in output.keys:
            if all([val is not key for _, val in output.aliases]):
                prefix_keys.append(key)

        aliases: OrderedSet[Tuple[str, ir.Value]] = ordered_set()
        # add the keys to the output
        for key in prefix_keys:
            aliases.add((key.name, key))

        # add the remaining args, unless it is already a key
        for name, val in output.aliases:
            if not isinstance(val, ir.Var) or val not in prefix_keys:
                aliases.add((name, val))

        # TODO - we are assuming that the Rel compiler will translate nullable lookups
        # properly, returning a `Missing` if necessary, like this:
        # (nested_192(_adult, _adult_name) or (not nested_192(_adult, _) and _adult_name = Missing)) and
        return ir.Output(
            output.engine,
            aliases.frozen(),
            output.keys,
            output.annotations
        )

        # TODO: in the rel compiler, see if we can do this outer join
        # 1. number of keys
        # 2. each relation
        # 3. each variable, starting with the keys
        # 4. tag output with @arrow

        # @arrow def output(_book, _book_title, _author_name):
        #   rel_primitive_outer_join(#1, book_title, author_name, _book, _book_title, _author_name)
        # def output(p, n, c):
        #     rel_primitive_outer_join(#1, name, coolness, p, n, c)

#--------------------------------------------------
# Helpers
#--------------------------------------------------

T = TypeVar('T')
def set_union(s1: Optional[OrderedSet[T]], s2: Optional[OrderedSet[T]]) -> list:
    """ Return the union of s1 | s2, accounting for when any is None. """
    if s1 and s2:
        return (s1 | s2).get_list()
    if s1:
        return s1.get_list()
    if s2:
        return s2.get_list()
    return []

def extractable(t: ir.Task):
    """
    Whether this task is a Logical that will be extracted as a top level by this
    pass, because it has an aggregation, effects, match, union, etc.
    """
    extractable_types = (ir.Update, ir.Aggregate, ir.Match, ir.Union, ir.Rank)
    return isinstance(t, ir.Logical) and len(visitor.collect_by_type(extractable_types, t)) > 0

def extractables(composites: OrderedSet[ir.Task]):
    """ Filter the set of composites, keeping only the extractable ones. """
    return list(filter(extractable, composites))

def negate(lookup: ir.Lookup, values: int):
    """
    Return a negation of this reference, where the last `values` arguments are to
    be replaced by wildcards (i.e. len(reference.args) - values are keys so they need
    to be bound in the Not.)
    """
    args = []
    i = 0
    last = len(lookup.args) - values
    for arg in lookup.args:
        args.append(f.wild(to_type(arg))) if i >= last else args.append(arg)
        i += 1

    return ir.Not(lookup.engine, f.lookup(lookup.relation, args))

def merge_var_list(vars: list[ir.Var], hoisted: tuple[ir.VarOrDefault, ...]) -> list[ir.VarOrDefault]:
    """ Merge vars and hoisted, making sure that hoisted vars have precedence since they may have defaults. """
    r = []
    hoisted_vars = helpers.hoisted_vars(hoisted)
    for v in vars:
        if v not in hoisted_vars:
            r.append(v)
    r.extend(hoisted)
    return r

def extend_body(body: OrderedSet[ir.Task], extra: ir.Task):
    """ Add the extra task to the body, but if the extra is a simple logical, just
    inline its subtasks. """
    if isinstance(extra, ir.Logical):
        if extra.hoisted:
            # hoists, remove things that are already in the body to avoid duplicates
            logical_body = []
            for t in extra.body:
                if t not in body:
                    logical_body.append(t)
            if len(logical_body) == len(extra.body):
                # no duplicates
                body.add(extra)
            else:
                # some duplicate, remove them
                body.add(ir.Logical(
                    extra.engine,
                    extra.hoisted,
                    tuple(logical_body)
                ))
        else:
            # no hoists, just inline
            body.update(extra.body)
    else:
        body.add(extra)
