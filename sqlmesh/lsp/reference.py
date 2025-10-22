import typing as t
from pathlib import Path

from sqlmesh.core.audit import StandaloneAudit
from sqlmesh.core.linter.helpers import (
    TokenPositionDetails,
)
from sqlmesh.core.linter.rule import Range, Position
from sqlmesh.core.model.definition import SqlModel
from sqlmesh.lsp.context import LSPContext, ModelTarget, AuditTarget
from sqlglot import exp

from sqlmesh.lsp.uri import URI
from sqlmesh.utils.lineage import (
    MacroReference,
    CTEReference,
    Reference,
    ModelReference,
    extract_references_from_query,
)
import ast
from sqlmesh.core.model import Model
from sqlmesh import macro
import inspect


def by_position(position: Position) -> t.Callable[[Reference], bool]:
    """
    Filter reference to only filter references that contain the given position.
    指定された位置を含む参照のみをフィルターするフィルター参照。

    Args:
        position: The cursor position to check

    Returns:
        A function that returns True if the reference contains the position, False otherwise
        参照に位置が含まれている場合はTrueを返し、そうでない場合はFalseを返す関数
    """

    def contains_position(r: Reference) -> bool:
        return _position_within_range(position, r.range)

    return contains_position


def get_references(
    lint_context: LSPContext, document_uri: URI, position: Position
) -> t.List[Reference]:
    """
    Get references at a specific position in a document.
    ドキュメント内の特定の位置にある参照を取得します。

    Used for hover information.

    Args:
        lint_context: The LSP context
        document_uri: The URI of the document
        position: The position to check for references

    Returns:
        A list of references at the given position
        指定された位置の参照リスト
    """
    references = get_model_definitions_for_a_path(lint_context, document_uri)

    # Get macro references before filtering by position
    # 位置でフィルタリングする前にマクロ参照を取得する
    macro_references = get_macro_definitions_for_a_path(lint_context, document_uri)
    references.extend(macro_references)

    filtered_references = list(filter(by_position(position), references))
    return filtered_references


def get_model_definitions_for_a_path(
    lint_context: LSPContext, document_uri: URI
) -> t.List[Reference]:
    """
    Get the model references for a given path.
    指定されたパスのモデル参照を取得します。

    Works for models and standalone audits.
    Works for targeting sql and python models.
    モデルとスタンドアロン監査で機能します。
    SQL および Python モデルを対象に機能します。

    Steps:
    - Get the parsed query
    - Find all table objects using find_all exp.Table
        - Match the string against all model names
    - Need to normalize it before matching
    - Try get_model before normalization
    - Match to models that the model refers to
    - Also find CTE references within the query

    - 解析済みのクエリを取得する
    - find_all exp.Table を使用してすべてのテーブルオブジェクトを検索する
        - 文字列をすべてのモデル名と照合する
    - 照合前に正規化する必要がある
    - 正規化前に get_model を試す
    - モデルが参照するモデルと照合する
    - クエリ内の CTE 参照も検索する
    """
    path = document_uri.to_path()
    if path.suffix != ".sql":
        return []
    # Get the file info from the context map
    # コンテキストマップからファイル情報を取得する
    if path not in lint_context.map:
        return []

    file_info = lint_context.map[path]
    # Process based on whether it's a model or standalone audit
    # モデルかスタンドアロン監査かに基づくプロセス
    if isinstance(file_info, ModelTarget):
        # It's a model
        model = lint_context.context.get_model(
            model_or_snapshot=file_info.names[0], raise_if_missing=False
        )
        if model is None or not isinstance(model, SqlModel):
            return []

        query = model.query
        dialect = model.dialect
        depends_on = model.depends_on
        file_path = model._path
    elif isinstance(file_info, AuditTarget):
        # It's a standalone audit
        audit = lint_context.context.standalone_audits.get(file_info.name)
        if audit is None:
            return []
        query = audit.query
        dialect = audit.dialect
        depends_on = audit.depends_on
        file_path = audit._path
    else:
        return []

    if file_path is None:
        return []

    with open(file_path, "r", encoding="utf-8") as file:
        read_file = file.readlines()

    return extract_references_from_query(
        query=query,
        context=lint_context.context,
        document_path=document_uri.to_path(),
        read_file=read_file,
        depends_on=depends_on,
        dialect=dialect,
    )


def get_macro_definitions_for_a_path(
    lsp_context: LSPContext, document_uri: URI
) -> t.List[Reference]:
    """
    Get macro references for a given path.
    指定されたパスのマクロ参照を取得します。

    This function finds all macro invocations (e.g., @ADD_ONE, @MULTIPLY) in a SQL file
    and creates references to their definitions in the Python macro files.
    この関数は、SQL ファイル内のすべてのマクロ呼び出し（例：@ADD_ONE、@MULTIPLY）を検索し、
    Python マクロファイル内にそれらの定義への参照を作成します。

    Args:
        lsp_context: The LSP context containing macro definitions
        document_uri: The URI of the document to search for macro invocations

    Returns:
        A list of Reference objects for each macro invocation found
        見つかったマクロ呼び出しごとの参照オブジェクトのリスト
    """
    path = document_uri.to_path()
    if path.suffix != ".sql":
        return []

    # Get the file info from the context map
    # コンテキストマップからファイル情報を取得する
    if path not in lsp_context.map:
        return []

    file_info = lsp_context.map[path]
    # Process based on whether it's a model or standalone audit
    # モデルかスタンドアロン監査かに基づくプロセス
    if isinstance(file_info, ModelTarget):
        # It's a model
        target: t.Optional[t.Union[Model, StandaloneAudit]] = lsp_context.context.get_model(
            model_or_snapshot=file_info.names[0], raise_if_missing=False
        )
        if target is None or not isinstance(target, SqlModel):
            return []
        query = target.query
        file_path = target._path
    elif isinstance(file_info, AuditTarget):
        # It's a standalone audit
        target = lsp_context.context.standalone_audits.get(file_info.name)
        if target is None:
            return []
        query = target.query
        file_path = target._path
    else:
        return []

    if file_path is None:
        return []

    references = []
    _, config_path = lsp_context.context.config_for_path(
        file_path,
    )

    with open(file_path, "r", encoding="utf-8") as file:
        read_file = file.readlines()

    for node in query.find_all(exp.Anonymous):
        macro_name = node.name.lower()
        reference = get_macro_reference(
            node=node,
            target=target,
            read_file=read_file,
            config_path=config_path,
            macro_name=macro_name,
        )
        if reference is not None:
            references.append(reference)

    return references


def get_macro_reference(
    target: t.Union[Model, StandaloneAudit],
    read_file: t.List[str],
    config_path: t.Optional[Path],
    node: exp.Expression,
    macro_name: str,
) -> t.Optional[Reference]:
    # Get the file path where the macro is defined
    # マクロが定義されているファイルパスを取得する
    try:
        # Get the position of the macro invocation in the source file first
        # まずソースファイル内のマクロ呼び出しの位置を取得します
        if hasattr(node, "meta") and node.meta:
            macro_range = TokenPositionDetails.from_meta(node.meta).to_range(read_file)

            # Check if it's a built-in method
            if builtin := get_built_in_macro_reference(macro_name, macro_range):
                return builtin
        else:
            # Skip if we can't get the position
            return None

        # Find the macro definition information
        # マクロ定義情報を見つける
        macro_def = target.python_env.get(macro_name)
        if macro_def is None:
            return None

        function_name = macro_def.name
        if not function_name:
            return None
        if not macro_def.path:
            return None
        if not config_path:
            return None
        path = Path(config_path).joinpath(macro_def.path)

        # Parse the Python file to find the function definition
        # Pythonファイルを解析して関数の定義を見つける
        with open(path, "r") as f:
            tree = ast.parse(f.read())
        with open(path, "r") as f:
            output_read_line = f.readlines()

        # Find the function definition by name
        # 名前で関数定義を見つける
        start_line = None
        end_line = None
        get_length_of_end_line = None
        docstring = None
        for ast_node in ast.walk(tree):
            if isinstance(ast_node, ast.FunctionDef) and ast_node.name == function_name:
                start_line = ast_node.lineno
                end_line = ast_node.end_lineno
                get_length_of_end_line = (
                    len(output_read_line[end_line - 1])
                    if end_line is not None and end_line - 1 < len(read_file)
                    else 0
                )
                # Extract docstring if present
                # 存在する場合はドキュメント文字列を抽出する
                docstring = ast.get_docstring(ast_node)
                break

        if start_line is None or end_line is None or get_length_of_end_line is None:
            return None

        # Create a reference to the macro definition
        # マクロ定義への参照を作成する

        return MacroReference(
            path=path,
            range=macro_range,
            target_range=Range(
                start=Position(line=start_line - 1, character=0),
                end=Position(line=end_line - 1, character=get_length_of_end_line),
            ),
            markdown_description=docstring,
        )
    except Exception:
        return None


def get_built_in_macro_reference(macro_name: str, macro_range: Range) -> t.Optional[Reference]:
    """
    Get a reference to a built-in macro by its name.
    組み込みマクロへの参照を名前で取得します。

    Args:
        macro_name: The name of the built-in macro (e.g., 'each', 'sql_literal')
            組み込みマクロの名前（例：'each'、'sql_literal'）
        macro_range: The range of the macro invocation in the source file
            ソースファイル内のマクロ呼び出しの範囲
    """
    built_in_macros = macro.get_registry()
    built_in_macro = built_in_macros.get(macro_name)
    if built_in_macro is None:
        return None

    func = built_in_macro.func
    filename = inspect.getfile(func)
    source_lines, line_number = inspect.getsourcelines(func)

    # Calculate the end line number by counting the number of source lines
    # ソース行数を数えて終了行番号を計算する
    end_line_number = line_number + len(source_lines) - 1

    return MacroReference(
        path=Path(filename),
        range=macro_range,
        target_range=Range(
            start=Position(line=line_number - 1, character=0),
            end=Position(line=end_line_number - 1, character=0),
        ),
        markdown_description=func.__doc__ if func.__doc__ else None,
    )


def get_model_find_all_references(
    lint_context: LSPContext, document_uri: URI, position: Position
) -> t.List[ModelReference]:
    """
    Get all references to a model across the entire project.
    プロジェクト全体にわたるモデルへのすべての参照を取得します。

    This function finds all usages of a model in other files by searching through
    all models in the project and checking their dependencies.
    この関数は、プロジェクト内のすべてのモデルを検索し、それらの依存関係をチェックすることで、
    他のファイルでのモデルの使用箇所をすべて見つけます。

    Args:
        lint_context: The LSP context
        document_uri: The URI of the document
        position: The position to check for model references

    Returns:
        A list of references to the model across all files
        すべてのファイルにわたるモデルへの参照のリスト
    """
    # Find the model reference at the cursor position
    # カーソル位置のモデル参照を見つける
    model_at_position = next(
        filter(
            lambda ref: isinstance(ref, ModelReference)
            and _position_within_range(position, ref.range),
            get_model_definitions_for_a_path(lint_context, document_uri),
        ),
        None,
    )

    if not model_at_position:
        return []

    assert isinstance(model_at_position, ModelReference)  # for mypy

    target_model_path = model_at_position.path

    # Start with the model definition
    # モデル定義から始める
    all_references: t.List[ModelReference] = [
        ModelReference(
            path=model_at_position.path,
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=0),
            ),
            markdown_description=model_at_position.markdown_description,
        )
    ]

    # Then add references from the current file
    # 次に現在のファイルから参照を追加します
    current_file_refs = filter(
        lambda ref: isinstance(ref, ModelReference) and ref.path == target_model_path,
        get_model_definitions_for_a_path(lint_context, document_uri),
    )

    for ref in current_file_refs:
        assert isinstance(ref, ModelReference)  # for mypy

        all_references.append(
            ModelReference(
                path=document_uri.to_path(),
                range=ref.range,
                markdown_description=ref.markdown_description,
            )
        )

    # Search through the models in the project
    # プロジェクト内のモデルを検索する
    for path, _ in lint_context.map.items():
        file_uri = URI.from_path(path)

        # Skip current file, already processed
        # 現在のファイルをスキップします。すでに処理済みです。
        if file_uri.value == document_uri.value:
            continue

        # Get model references that point to the target model
        # 対象モデルを指すモデル参照を取得する
        matching_refs = filter(
            lambda ref: isinstance(ref, ModelReference) and ref.path == target_model_path,
            get_model_definitions_for_a_path(lint_context, file_uri),
        )

        for ref in matching_refs:
            assert isinstance(ref, ModelReference)  # for mypy

            all_references.append(
                ModelReference(
                    path=path,
                    range=ref.range,
                    markdown_description=ref.markdown_description,
                )
            )

    return all_references


def get_cte_references(
    lint_context: LSPContext, document_uri: URI, position: Position
) -> t.List[CTEReference]:
    """
    Get all references to a CTE at a specific position in a document.
    ドキュメント内の特定の位置にある CTE へのすべての参照を取得します。

    This function finds both the definition and all usages of a CTE within the same file.
    この関数は、同じファイル内の CTE の定義とすべての使用箇所を検索します。

    Args:
        lint_context: The LSP context
        document_uri: The URI of the document
        position: The position to check for CTE references

    Returns:
        A list of references to the CTE (including its definition and all usages)
        CTE への参照リスト（定義とすべての使用法を含む）
    """

    # Filter to get the CTE references
    # CTE参照を取得するためのフィルター
    cte_references: t.List[CTEReference] = [
        ref
        for ref in get_model_definitions_for_a_path(lint_context, document_uri)
        if isinstance(ref, CTEReference)
    ]

    if not cte_references:
        return []

    target_cte_definition_range = None
    for ref in cte_references:
        # Check if cursor is on a CTE usage
        # カーソルがCTE使用箇所にあるかどうかを確認する
        if _position_within_range(position, ref.range):
            target_cte_definition_range = ref.target_range
            break
        # Check if cursor is on the CTE definition
        # カーソルがCTE定義上にあるかどうかを確認します
        elif _position_within_range(position, ref.target_range):
            target_cte_definition_range = ref.target_range
            break

    if target_cte_definition_range is None:
        return []

    # Add the CTE definition
    # CTE定義を追加する
    matching_references = [
        CTEReference(
            path=document_uri.to_path(),
            range=target_cte_definition_range,
            target_range=target_cte_definition_range,
        )
    ]

    # Add all usages
    for ref in cte_references:
        if ref.target_range == target_cte_definition_range:
            matching_references.append(
                CTEReference(
                    path=document_uri.to_path(),
                    range=ref.range,
                    target_range=ref.target_range,
                )
            )

    return matching_references


def get_macro_find_all_references(
    lsp_context: LSPContext, document_uri: URI, position: Position
) -> t.List[MacroReference]:
    """
    Get all references to a macro at a specific position in a document.
    ドキュメント内の特定の位置にあるマクロへの参照をすべて取得します。

    This function finds all usages of a macro across the entire project.
    この関数は、プロジェクト全体にわたるマクロの使用箇所をすべて検索します。

    Args:
        lsp_context: The LSP context
        document_uri: The URI of the document
        position: The position to check for macro references

    Returns:
        A list of references to the macro across all files
        すべてのファイルにわたるマクロへの参照のリスト
    """
    # Find the macro reference at the cursor position
    # カーソル位置のマクロ参照を見つける
    macro_at_position = next(
        filter(
            lambda ref: isinstance(ref, MacroReference)
            and _position_within_range(position, ref.range),
            get_macro_definitions_for_a_path(lsp_context, document_uri),
        ),
        None,
    )

    if not macro_at_position:
        return []

    assert isinstance(macro_at_position, MacroReference)  # for mypy

    target_macro_path = macro_at_position.path
    target_macro_target_range = macro_at_position.target_range

    # Start with the macro definition
    # マクロ定義から始める
    all_references: t.List[MacroReference] = [
        MacroReference(
            path=target_macro_path,
            range=target_macro_target_range,
            target_range=target_macro_target_range,
            markdown_description=None,
        )
    ]

    # Search through all SQL and audit files in the project
    # プロジェクト内のすべてのSQLファイルと監査ファイルを検索する
    for path, _ in lsp_context.map.items():
        file_uri = URI.from_path(path)

        # Get macro references that point to the same macro definition
        # 同じマクロ定義を指すマクロ参照を取得する
        matching_refs = filter(
            lambda ref: isinstance(ref, MacroReference)
            and ref.path == target_macro_path
            and ref.target_range == target_macro_target_range,
            get_macro_definitions_for_a_path(lsp_context, file_uri),
        )

        for ref in matching_refs:
            assert isinstance(ref, MacroReference)  # for mypy
            all_references.append(
                MacroReference(
                    path=path,
                    range=ref.range,
                    target_range=ref.target_range,
                    markdown_description=ref.markdown_description,
                )
            )

    return all_references


def get_all_references(
    lint_context: LSPContext, document_uri: URI, position: Position
) -> t.Sequence[Reference]:
    """
    Get all references of a symbol at a specific position in a document.
    ドキュメント内の特定の位置にあるシンボルのすべての参照を取得します。

    This function determines the type of reference (CTE, model or macro) at the cursor
    position and returns all references to that symbol across the project.
    この関数は、カーソル位置の参照の種類（CTE、モデル、またはマクロ）を判別し、
    プロジェクト全体にわたってそのシンボルへのすべての参照を返します。


    Args:
        lint_context: The LSP context
        document_uri: The URI of the document
        position: The position to check for references

    Returns:
        A list of references to the symbol at the given position
        指定された位置のシンボルへの参照のリスト
    """
    # First try CTE references (within same file)
    # まずCTE参照を試してください（同じファイル内）
    if cte_references := get_cte_references(lint_context, document_uri, position):
        return cte_references

    # Then try model references (across files)
    # 次に、モデル参照（ファイル間）を試します。
    if model_references := get_model_find_all_references(lint_context, document_uri, position):
        return model_references

    # Finally try macro references (across files)
    # 最後にマクロ参照を試します（ファイル間）
    if macro_references := get_macro_find_all_references(lint_context, document_uri, position):
        return macro_references

    return []


def _position_within_range(position: Position, range: Range) -> bool:
    """Check if a position is within a given range.
    位置が指定された範囲内にあるかどうかを確認します。"""
    return (
        range.start.line < position.line
        or (range.start.line == position.line and range.start.character <= position.character)
    ) and (
        range.end.line > position.line
        or (range.end.line == position.line and range.end.character >= position.character)
    )
