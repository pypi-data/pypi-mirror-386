from abc import ABC
from typing import cast
from dataclasses import field, dataclass

from kirin.ir import Pure, Block, IRNode, Region, MaybePure, Statement


@dataclass
class RewriteResult:
    terminated: bool = field(default=False, kw_only=True)
    has_done_something: bool = field(default=False, kw_only=True)
    exceeded_max_iter: bool = field(default=False, kw_only=True)

    def join(self, other: "RewriteResult") -> "RewriteResult":
        return RewriteResult(
            terminated=self.terminated or other.terminated,
            has_done_something=self.has_done_something or other.has_done_something,
            exceeded_max_iter=self.exceeded_max_iter or other.exceeded_max_iter,
        )


@dataclass(repr=False)
class RewriteRule(ABC):
    """A rewrite rule that matches and rewrites IR nodes.

    The rewrite rule is applied to an IR node by calling the instance with the node as an argument.
    The rewrite rule should mutate the node instead of returning a new node. A `RewriteResult` should
    be returned to indicate whether the rewrite rule has done something, whether the rewrite rule
    should terminate, and whether the rewrite rule has exceeded the maximum number of iterations.
    """

    def rewrite(self, node: IRNode) -> RewriteResult:
        if node.IS_REGION:
            return self.rewrite_Region(cast(Region, node))
        elif node.IS_BLOCK:
            return self.rewrite_Block(cast(Block, node))
        elif node.IS_STATEMENT:
            return self.rewrite_Statement(cast(Statement, node))
        else:
            return RewriteResult()

    def rewrite_Region(self, node: Region) -> RewriteResult:
        return RewriteResult()

    def rewrite_Block(self, node: Block) -> RewriteResult:
        return RewriteResult()

    def rewrite_Statement(self, node: Statement) -> RewriteResult:
        return RewriteResult()

    def is_pure(self, node: Statement):
        if node.has_trait(Pure):
            return True

        if (trait := node.get_trait(MaybePure)) and trait.is_pure(node):
            return True
        return False
