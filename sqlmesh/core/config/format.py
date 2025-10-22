from __future__ import annotations

import typing as t

from sqlmesh.core.config.base import BaseConfig


class FormatConfig(BaseConfig):
    """The format configuration for SQL code.
    SQL コードのフォーマット構成。

    Args:
        normalize: Whether to normalize the SQL code or not.
            SQL コードを正規化するかどうか。
        pad: The number of spaces to use for padding.
            パディングに使用するスペースの数。
        indent: The number of spaces to use for indentation.
            インデントに使用するスペースの数。
        normalize_functions: Whether or not to normalize all function names. Possible values are: 'upper', 'lower'
            すべての関数名を正規化するかどうか。可能な値は「upper」、「lower」です。
        leading_comma: Whether to use leading commas or not.
            先頭のコンマを使用するかどうか。
        max_text_width: The maximum text width in a segment before creating new lines.
            新しい行を作成する前のセグメント内の最大テキスト幅。
        append_newline: Whether to append a newline to the end of the file or not.
            ファイルの末尾に改行を追加するかどうか。
        no_rewrite_casts: Preserve the existing casts, without rewriting them to use the :: syntax.
            :: 構文を使用するように書き換えずに、既存のキャストを保持します。
    """

    normalize: bool = False
    pad: int = 2
    indent: int = 2
    normalize_functions: t.Optional[str] = None
    leading_comma: bool = False
    max_text_width: int = 80
    append_newline: bool = False
    no_rewrite_casts: bool = False

    @property
    def generator_options(self) -> t.Dict[str, t.Any]:
        """Options which can be passed through to the SQLGlot Generator class.
        SQLGlot ジェネレーター クラスに渡すことができるオプション。

        Returns:
            The generator options.
        """
        return self.dict(exclude={"append_newline", "no_rewrite_casts"})
