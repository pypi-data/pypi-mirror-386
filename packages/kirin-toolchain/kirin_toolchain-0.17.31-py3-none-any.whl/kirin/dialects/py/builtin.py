"""builtin dialect for python builtins

This dialect provides implementations for builtin functions like abs and sum.

- Statements: `Abs`, `Sum`.
- The lowering pass for the builtin functions.
- The concrete implementation of the builtin functions.
- The type inference implementation of the builtin functions.

This dialect maps `ast.Call` nodes of builtin functions to the `Abs` and `Sum` statements.
"""

from ast import Call

from kirin import ir, types, interp, lowering
from kirin.decl import info, statement

dialect = ir.Dialect("py.builtin")

T = types.TypeVar("T", bound=types.Int | types.Float)


@statement(dialect=dialect)
class Abs(ir.Statement):
    name = "abs"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    value: ir.SSAValue = info.argument(T, print=False)
    result: ir.ResultValue = info.result(T)


@statement(dialect=dialect)
class Sum(ir.Statement):
    name = "sum"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    value: ir.SSAValue = info.argument(types.Any, print=False)
    result: ir.ResultValue = info.result(types.Any)


@dialect.register
class Lowering(lowering.FromPythonAST):

    @lowering.akin(abs)
    def lower_Call_abs(self, state: lowering.State, node: Call) -> lowering.Result:
        return state.current_frame.push(Abs(state.lower(node.args[0]).expect_one()))

    @lowering.akin(sum)
    def lower_Call_sum(self, state: lowering.State, node: Call) -> lowering.Result:
        return state.current_frame.push(Sum(state.lower(node.args[0]).expect_one()))


@dialect.register
class Concrete(interp.MethodTable):

    @interp.impl(Abs)
    def abs(self, interp, frame: interp.Frame, stmt: Abs):
        return (abs(frame.get(stmt.value)),)

    @interp.impl(Sum)
    def _sum(self, interp, frame: interp.Frame, stmt: Sum):
        return (sum(frame.get(stmt.value)),)


@dialect.register(key="typeinfer")
class TypeInfer(interp.MethodTable):

    @interp.impl(Abs, types.Int)
    def absi(self, interp, frame, stmt):
        return (types.Int,)

    @interp.impl(Abs, types.Float)
    def absf(self, interp, frame, stmt):
        return (types.Float,)


dialect.register_py_type(float)
dialect.register_py_type(int)
dialect.register_py_type(bool)
dialect.register_py_type(str)
dialect.register_py_type(type(None))
dialect.register_py_type(list)
dialect.register_py_type(dict)
dialect.register_py_type(tuple)
dialect.register_py_type(set)
dialect.register_py_type(frozenset)
dialect.register_py_type(slice)
