from kirin import types, lowering
from kirin.dialects import cf, py, func
from kirin.dialects.lowering import func as func_lowering

lower = lowering.Python([cf, func, py.base, py.list, py.assign, func_lowering])


def test_empty_list():

    def empty_list():
        x = []
        return x

    code = lower.python_function(empty_list)

    list_stmt = code.body.blocks[0].stmts.at(0)  # type: ignore

    assert isinstance(list_stmt, py.list.New)
    assert len(list_stmt._results) == 1

    res = list_stmt._results[0]
    assert res.type.is_subseteq(types.List)
