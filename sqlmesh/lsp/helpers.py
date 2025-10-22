from lsprotocol.types import Range, Position

from sqlmesh.core.linter.helpers import (
    Range as SQLMeshRange,
    Position as SQLMeshPosition,
)


def to_sqlmesh_position(position: Position) -> SQLMeshPosition:
    """
    Converts an LSP Position to a SQLMesh Position.
    LSP 位置を SQLMesh 位置に変換します。
    """
    return SQLMeshPosition(line=position.line, character=position.character)


def to_lsp_position(position: SQLMeshPosition) -> Position:
    """
    Converts a SQLMesh Position to an LSP Position.
    SQLMesh 位置を LSP 位置に変換します。
    """
    return Position(line=position.line, character=position.character)


def to_sqlmesh_range(range: Range) -> SQLMeshRange:
    """
    Converts an LSP Range to a SQLMesh Range.
    LSP 範囲を SQLMesh 範囲に変換します。
    """
    return SQLMeshRange(
        start=to_sqlmesh_position(range.start),
        end=to_sqlmesh_position(range.end),
    )


def to_lsp_range(range: SQLMeshRange) -> Range:
    """
    Converts a SQLMesh Range to an LSP Range.
    SQLMesh 範囲を LSP 範囲に変換します。
    """
    return Range(
        start=to_lsp_position(range.start),
        end=to_lsp_position(range.end),
    )
