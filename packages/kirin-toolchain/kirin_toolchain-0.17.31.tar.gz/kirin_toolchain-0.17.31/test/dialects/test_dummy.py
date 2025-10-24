import pytest

from kirin import ir, types, lowering
from kirin.decl import info, statement
from kirin.prelude import basic

dialect = ir.Dialect("dummy")


@statement(dialect=dialect)
class DummyStmt(ir.Statement):
    name = "dummy"
    traits = frozenset({lowering.FromPythonCall()})
    value: ir.SSAValue = info.argument(types.Int)
    option: ir.PyAttr[str] = info.attribute()
    result: ir.ResultValue = info.result(types.Int)


def test_attribute_lowering():
    @basic.add(dialect)
    def test(x: int):
        return DummyStmt(x, option=ir.PyAttr("attr"))  # type: ignore

    option = test.code.body.blocks[0].stmts.at(0).option  # type: ignore
    assert isinstance(option, ir.PyAttr) and option.data == "attr"

    with pytest.raises(lowering.BuildError):

        @basic.add(dialect)
        def not_working(x: int):
            return DummyStmt(x, option=x)  # type: ignore
