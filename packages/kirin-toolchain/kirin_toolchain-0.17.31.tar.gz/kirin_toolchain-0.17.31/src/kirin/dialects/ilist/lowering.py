import ast
from dataclasses import dataclass

from kirin import types, lowering
from kirin.dialects import py

from . import stmts as ilist
from ._dialect import dialect


@dialect.register
class PythonLowering(lowering.FromPythonAST):

    def lower_List(self, state: lowering.State, node: ast.List) -> lowering.Result:
        elts = tuple(state.lower(each).expect_one() for each in node.elts)

        if len(elts):
            typ = elts[0].type
            for each in elts:
                typ = typ.join(each.type)
        else:
            typ = types.Any

        return state.current_frame.push(ilist.New(values=tuple(elts), elem_type=typ))

    @lowering.akin(ilist.IList)
    def lower_Call_IList(
        self, state: lowering.State, node: ast.Call
    ) -> lowering.Result:
        if len(node.args) != 1:
            raise lowering.BuildError("IList constructor only takes one argument")
        value = node.args[0]
        if not isinstance(value, ast.List):
            raise lowering.BuildError("IList constructor only takes a list")

        if len(node.keywords) > 1:
            raise lowering.BuildError(
                "IList constructor only takes one keyword argument"
            )

        if len(node.keywords) == 1:
            kw = node.keywords[0]
            if kw.arg != "elem":
                raise lowering.BuildError(
                    "IList constructor only takes elem keyword argument"
                )
            elem = self.get_hint(state, kw.value)
            elts = tuple(state.lower(each).expect_one() for each in value.elts)
            stmt = ilist.New(values=tuple(elts), elem_type=elem)
            return state.current_frame.push(stmt)
        else:
            return self.lower_List(state, value)


@dataclass(frozen=True)
class SortedLowering(lowering.FromPythonCall["ilist.Sorted"]):
    """
    Custom lowering for Sorted to deal with optional arguments `key=None` and `reverse=False`
    """

    def lower(
        self, stmt: type["ilist.Sorted"], state: lowering.State[ast.AST], node: ast.Call
    ) -> lowering.Result:
        args = node.args

        if len(args) != 1:
            raise lowering.BuildError(
                f"Expected single argument in sorted, got {len(args)}"
            )
        collection = state.lower(args[0]).expect_one()

        key = None
        reverse = None
        for kwarg in node.keywords:
            if kwarg.arg == "key":
                key = state.lower(kwarg.value).expect_one()
            elif kwarg.arg == "reverse":
                reverse = state.lower(kwarg.value).expect_one()
            else:
                raise lowering.BuildError(
                    f"Got unexpected keyword argument in sorted {kwarg.arg}"
                )

        if key is None:
            key = state.current_frame.push(py.Constant(None)).result

        if reverse is None:
            reverse = state.current_frame.push(py.Constant(False)).result

        return state.current_frame.push(
            stmt(collection=collection, key=key, reverse=reverse)
        )
