import ast
from typing import Generic, TypeVar, Callable, Iterable, TypeAlias
from dataclasses import dataclass

from kirin import lowering
from kirin.ir.group import DialectGroup
from kirin.ir.nodes import Statement
from kirin.lowering import FromPythonAST
from kirin.interp.base import FrameABC, BaseInterpreter
from kirin.interp.impl import Signature
from kirin.interp.table import MethodTable
from kirin.interp.value import StatementResult
from kirin.ir.attrs.abc import Attribute
from kirin.lowering.python.dialect import LoweringTransform

MethodTableSelf = TypeVar("MethodTableSelf", bound="MethodTable")
InterpreterType = TypeVar("InterpreterType", bound="BaseInterpreter")
FrameType = TypeVar("FrameType", bound="FrameABC")
StatementType = TypeVar("StatementType", bound="Statement")
MethodFunction: TypeAlias = Callable[
    [MethodTableSelf, InterpreterType, FrameType, StatementType], StatementResult
]

@dataclass
class StatementImpl(Generic[InterpreterType, FrameType]):
    parent: "MethodTable"
    impl: MethodFunction["MethodTable", InterpreterType, FrameType, "Statement"]

    def __call__(
        self, interp: InterpreterType, frame: FrameType, stmt: "Statement"
    ) -> StatementResult: ...
    def __repr__(self) -> str: ...

@dataclass
class AttributeImpl:
    parent: "MethodTable"
    impl: Callable

    def __call__(self, interp, attr: "Attribute"): ...
    def __repr__(self) -> str: ...

@dataclass
class CallLoweringFunction:
    parent: "FromPythonAST"
    func: "LoweringTransform"

    def __call__(
        self, state: "lowering.State[ast.AST]", node: "ast.Call"
    ) -> "lowering.Result": ...

@dataclass
class LoweringRegistry:
    ast_table: dict[str, FromPythonAST]
    callee_table: dict[object, CallLoweringFunction]

@dataclass
class InterpreterRegistry:
    attributes: dict[type["Attribute"], "AttributeImpl"]
    statements: dict["Signature", "StatementImpl"]

@dataclass
class Registry:
    """Proxy class to build different registries from a dialect group."""

    dialects: "DialectGroup"
    """The dialect group to build the registry from."""

    def ast(self, keys: Iterable[str]) -> LoweringRegistry: ...
    def interpreter(self, keys: Iterable[str]) -> InterpreterRegistry: ...
