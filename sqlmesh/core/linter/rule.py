from __future__ import annotations

import abc
from dataclasses import dataclass, field
from pathlib import Path

from sqlmesh.core.model import Model

from typing import Type

import typing as t

from sqlmesh.utils.pydantic import PydanticModel


if t.TYPE_CHECKING:
    from sqlmesh.core.context import GenericContext


class RuleLocation(PydanticModel):
    """The location of a rule in a file.
    ファイル内のルールの場所。"""

    file_path: str
    start_line: t.Optional[int] = None


@dataclass(frozen=True)
class Position:
    """The position of a rule violation in a file, the position follows the LSP standard.
    ファイル内のルール違反の位置。位置は LSP 標準に従います。"""

    line: int
    character: int


@dataclass(frozen=True)
class Range:
    """The range of a rule violation in a file. The range follows the LSP standard.
    ファイル内のルール違反の範囲。範囲はLSP標準に従います。"""

    start: Position
    end: Position


@dataclass(frozen=True)
class TextEdit:
    """A text edit to apply to a file.
    ファイルに適用するテキスト編集。"""

    path: Path
    range: Range
    new_text: str


@dataclass(frozen=True)
class CreateFile:
    """Create a new file with the provided text.
    指定されたテキストで新しいファイルを作成します。"""

    path: Path
    text: str


@dataclass(frozen=True)
class Fix:
    """A fix that can be applied to resolve a rule violation.
    ルール違反を解決するために適用できる修正。"""

    title: str
    edits: t.List[TextEdit] = field(default_factory=list)
    create_files: t.List[CreateFile] = field(default_factory=list)


class _Rule(abc.ABCMeta):
    def __new__(cls: Type[_Rule], clsname: str, bases: t.Tuple, attrs: t.Dict) -> _Rule:
        attrs["name"] = clsname.lower()
        return super().__new__(cls, clsname, bases, attrs)


class Rule(abc.ABC, metaclass=_Rule):
    """The base class for a rule.
    ルールの基本クラス。"""

    name = "rule"

    def __init__(self, context: GenericContext):
        self.context = context

    @abc.abstractmethod
    def check_model(
        self, model: Model
    ) -> t.Optional[t.Union[RuleViolation, t.List[RuleViolation]]]:
        """The evaluation function that'll check for a violation of this rule.
        このルールの違反をチェックする評価関数。"""

    @property
    def summary(self) -> str:
        """A summary of what this rule checks for.
        このルールがチェックする内容の概要。"""
        return self.__doc__ or ""

    def violation(
        self,
        violation_msg: t.Optional[str] = None,
        violation_range: t.Optional[Range] = None,
        fixes: t.Optional[t.List[Fix]] = None,
    ) -> RuleViolation:
        """Create a RuleViolation instance for this rule
        このルールのRuleViolationインスタンスを作成する"""
        return RuleViolation(
            rule=self,
            violation_msg=violation_msg or self.summary,
            violation_range=violation_range,
            fixes=fixes,
        )

    def get_definition_location(self) -> RuleLocation:
        """Return the file path and position information for this rule.
        このルールのファイル パスと位置情報を返します。

        This method returns information about where this rule is defined,
        which can be used in diagnostics to link to the rule's documentation.
        このメソッドは、このルールが定義されている場所に関する情報を返します。
        この情報は、診断でルールのドキュメントにリンクするために使用できます。

        Returns:
            A dictionary containing file path and position information.
            ファイル パスと位置情報を含む辞書。
        """
        import inspect

        # Get the file where the rule class is defined
        # ルールクラスが定義されているファイルを取得する
        file_path = inspect.getfile(self.__class__)

        try:
            # Get the source code and line number
            # ソースコードと行番号を取得する
            source_lines, start_line = inspect.getsourcelines(self.__class__)
            return RuleLocation(
                file_path=file_path,
                start_line=start_line,
            )
        except (IOError, TypeError):
            # Fall back to just returning the file path if we can't get source lines
            # ソース行を取得できない場合は、ファイルパスを返すだけにします。
            return RuleLocation(file_path=file_path)

    def __repr__(self) -> str:
        return self.name


class RuleViolation:
    def __init__(
        self,
        rule: Rule,
        violation_msg: str,
        violation_range: t.Optional[Range] = None,
        fixes: t.Optional[t.List[Fix]] = None,
    ) -> None:
        self.rule = rule
        self.violation_msg = violation_msg
        self.violation_range = violation_range
        self.fixes = fixes or []

    def __repr__(self) -> str:
        return f"{self.rule.name}: {self.violation_msg}"
