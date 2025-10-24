from typing import Tuple
from relationalai.semantics.lqp import ir as lqp
from relationalai.semantics.metamodel.ir import sanitize

def mk_and(args: list[lqp.Formula]) -> lqp.Formula:
    # Flatten nested conjunctions
    if any(isinstance(arg, lqp.Conjunction) for arg in args):
        final_args = []
        for arg in args:
            if isinstance(arg, lqp.Conjunction):
                final_args.extend(arg.args)
            else:
                final_args.append(arg)
        args = final_args

    if len(args) == 1:
        return args[0]

    return lqp.Conjunction(args=args, meta=None)

def mk_or(args: list[lqp.Formula]) -> lqp.Formula:
    # Flatten nested disjunctions
    if any(isinstance(arg, lqp.Disjunction) for arg in args):
        final_args = []
        for arg in args:
            if isinstance(arg, lqp.Disjunction):
                final_args.extend(arg.args)
            else:
                final_args.append(arg)
        args = final_args

    if len(args) == 1:
        return args[0]

    return lqp.Disjunction(args=args, meta=None)

def mk_abstraction(vars: list[Tuple[lqp.Var, lqp.Type]], value: lqp.Formula) -> lqp.Abstraction:
    return lqp.Abstraction(vars=vars, value=value, meta=None)

def mk_exists(vars: list[Tuple[lqp.Var, lqp.Type]], value: lqp.Formula) -> lqp.Formula:
    if len(vars) == 0:
        return value
    abstr = mk_abstraction(vars, value)
    return lqp.Exists(body=abstr, meta=None)

def mk_specialized_value(value) -> lqp.SpecializedValue:
    return lqp.SpecializedValue(value=value, meta=None)

def mk_value(value) -> lqp.Value:
    return lqp.Value(value=value, meta=None)

def mk_var(name: str) -> lqp.Var:
    _name = '_' if name == '_' else sanitize(name)
    return lqp.Var(name=_name, meta=None)

def mk_type(typename: lqp.TypeName, parameters: list[lqp.Value]=[]) -> lqp.Type:
    return lqp.Type(type_name=typename, parameters=parameters, meta=None)

def mk_primitive(name: str, terms: list[lqp.RelTerm]) -> lqp.Primitive:
    return lqp.Primitive(name=name, terms=terms, meta=None)

def mk_pragma(name: str, terms: list[lqp.Var]) -> lqp.Pragma:
    return lqp.Pragma(name=name, terms=terms, meta=None)

def mk_attribute(name: str, args: list[lqp.Value]) -> lqp.Attribute:
    return lqp.Attribute(name=name, args=args, meta=None)
