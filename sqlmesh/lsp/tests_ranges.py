"""
Provides helper functions to get ranges of tests in SQLMesh LSP.
SQLMesh LSP でテストの範囲を取得するためのヘルパー関数を提供します。
"""

from pathlib import Path

from sqlmesh.core.linter.rule import Range, Position
from ruamel import yaml
from ruamel.yaml.comments import CommentedMap
import typing as t


def get_test_ranges(
    path: Path,
) -> t.Dict[str, Range]:
    """
    Test files are yaml files with a stucture of dict to test information. This returns a dictionary
    with the test name as the key and the range of the test in the file as the value.
    テストファイルは、テスト情報を格納した辞書構造のyamlファイルです。
    テスト名をキーとし、ファイル内のテスト範囲を値とする辞書を返します。
    """
    test_ranges: t.Dict[str, Range] = {}

    with open(path, "r", encoding="utf-8") as file:
        content = file.read()

    # Parse YAML to get line numbers
    # YAMLを解析して行番号を取得する
    yaml_obj = yaml.YAML()
    yaml_obj.preserve_quotes = True
    data = yaml_obj.load(content)

    if not isinstance(data, dict):
        raise ValueError("Invalid test file format: expected a dictionary at the top level.")

    # For each top-level key (test name), find its range
    # 各トップレベルキー（テスト名）の範囲を見つける
    for test_name in data:
        if isinstance(data, CommentedMap) and test_name in data.lc.data:
            # Get line and column info from ruamel yaml
            # ruamel yamlから行と列の情報を取得する
            line_info = data.lc.data[test_name]
            start_line = line_info[0]  # 0-based line number
            start_col = line_info[1]  # 0-based column number

            # Find the end of this test by looking for the next test or end of file
            # 次のテストまたはファイルの終わりを探して、このテストの終わりを見つけます
            lines = content.splitlines()
            end_line = start_line

            # Find where this test ends by looking for the next top-level key
            # or the end of the file
            # 次のトップレベルキーまたはファイルの末尾を探して、このテストの終了位置を見つけます。
            for i in range(start_line + 1, len(lines)):
                line = lines[i]
                # Check if this line starts a new top-level key (no leading spaces)
                # この行が新しいトップレベルキーを開始するかどうかを確認します（先頭にスペースはありません）
                if line and not line[0].isspace() and ":" in line:
                    end_line = i - 1
                    break
            else:
                # This test goes to the end of the file
                # このテストはファイルの最後まで行われます
                end_line = len(lines) - 1

            # Create the range
            # 範囲を作成する
            test_ranges[test_name] = Range(
                start=Position(line=start_line, character=start_col),
                end=Position(
                    line=end_line, character=len(lines[end_line]) if end_line < len(lines) else 0
                ),
            )

    return test_ranges
