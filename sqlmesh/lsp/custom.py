from lsprotocol import types
import typing as t

from sqlmesh.core.linter.rule import Range
from sqlmesh.utils.pydantic import PydanticModel


class CustomMethodRequestBaseClass(PydanticModel):
    pass


class CustomMethodResponseBaseClass(PydanticModel):
    # Prefixing, so guaranteed not to collide
    # プレフィックスを付けることで衝突が起こらないことが保証される
    response_error: t.Optional[str] = None


ALL_MODELS_FEATURE = "sqlmesh/all_models"


class AllModelsRequest(CustomMethodRequestBaseClass):
    """
    Request to get all the models that are in the current project.
    現在のプロジェクトにあるすべてのモデルを取得するように要求します。
    すべてと言いつつ、一つ
    """

    textDocument: types.TextDocumentIdentifier


class MacroCompletion(PydanticModel):
    """Information about a macro for autocompletion.
    自動補完のマクロに関する情報。"""

    name: str
    description: t.Optional[str] = None


class ModelCompletion(PydanticModel):
    """Information about a model for autocompletion.
    自動補完のモデルに関する情報。"""

    name: str
    description: t.Optional[str] = None


class AllModelsResponse(CustomMethodResponseBaseClass):
    """Response to get all models that are in the current project.
    現在のプロジェクトにあるすべてのモデルを取得するための応答。"""

    #: Deprecated: use ``model_completions`` instead
    models: t.List[str]
    model_completions: t.List[ModelCompletion]
    keywords: t.List[str]
    macros: t.List[MacroCompletion]


RENDER_MODEL_FEATURE = "sqlmesh/render_model"


class RenderModelRequest(CustomMethodRequestBaseClass):
    textDocumentUri: str


class RenderModelEntry(PydanticModel):
    """
    An entry in the rendered model.
    レンダリングされたモデル内のエントリ。
    """

    name: str
    fqn: str
    description: t.Optional[str] = None
    rendered_query: str


class RenderModelResponse(CustomMethodResponseBaseClass):
    """
    Response to render a model.
    モデルをレンダリングするための応答。
    """

    models: t.List[RenderModelEntry]


ALL_MODELS_FOR_RENDER_FEATURE = "sqlmesh/all_models_for_render"


class ModelForRendering(PydanticModel):
    """
    A model that is available for rendering.
    レンダリングに使用できるモデル。
    """

    name: str
    fqn: str
    description: t.Optional[str] = None
    uri: str


class AllModelsForRenderRequest(CustomMethodRequestBaseClass):
    pass


class AllModelsForRenderResponse(CustomMethodResponseBaseClass):
    """
    Response to get all the models that are in the current project for rendering purposes.
    レンダリングの目的で現在のプロジェクトにあるすべてのモデルを取得するための応答。
    """

    models: t.List[ModelForRendering]


SUPPORTED_METHODS_FEATURE = "sqlmesh/supported_methods"


class SupportedMethodsRequest(PydanticModel):
    """
    Request to get all supported custom LSP methods.
    サポートされているすべてのカスタム LSP メソッドを取得するための要求。
    """

    pass


class CustomMethod(PydanticModel):
    """
    Information about a custom LSP method.
    カスタム LSP メソッドに関する情報。
    """

    name: str


class SupportedMethodsResponse(CustomMethodResponseBaseClass):
    """
    Response containing all supported custom LSP methods.
    サポートされているすべてのカスタム LSP メソッドを含む応答。
    """

    methods: t.List[CustomMethod]


FORMAT_PROJECT_FEATURE = "sqlmesh/format_project"


class FormatProjectRequest(CustomMethodRequestBaseClass):
    """
    Request to format all models in the current project.
    現在のプロジェクト内のすべてのモデルをフォーマットするよう要求します。
    """

    pass


class FormatProjectResponse(CustomMethodResponseBaseClass):
    """
    Response to format project request.
    フォーマットプロジェクト要求への応答。
    """

    pass


LIST_WORKSPACE_TESTS_FEATURE = "sqlmesh/list_workspace_tests"


class ListWorkspaceTestsRequest(CustomMethodRequestBaseClass):
    """
    Request to list all tests in the current project.
    現在のプロジェクト内のすべてのテストを一覧表示する要求。
    """

    pass


GET_ENVIRONMENTS_FEATURE = "sqlmesh/get_environments"


class GetEnvironmentsRequest(CustomMethodRequestBaseClass):
    """
    Request to get all environments in the current project.
    現在のプロジェクト内のすべての環境を取得するよう要求します。
    """

    pass


class TestEntry(PydanticModel):
    """
    An entry representing a test in the workspace.
    ワークスペース内のテストを表すエントリ。
    """

    name: str
    uri: str
    range: Range


class ListWorkspaceTestsResponse(CustomMethodResponseBaseClass):
    tests: t.List[TestEntry]


LIST_DOCUMENT_TESTS_FEATURE = "sqlmesh/list_document_tests"


class ListDocumentTestsRequest(CustomMethodRequestBaseClass):
    textDocument: types.TextDocumentIdentifier


class ListDocumentTestsResponse(CustomMethodResponseBaseClass):
    tests: t.List[TestEntry]


RUN_TEST_FEATURE = "sqlmesh/run_test"


class RunTestRequest(CustomMethodRequestBaseClass):
    textDocument: types.TextDocumentIdentifier
    testName: str


class RunTestResponse(CustomMethodResponseBaseClass):
    success: bool
    error_message: t.Optional[str] = None


class EnvironmentInfo(PydanticModel):
    """
    Information about an environment.
    環境に関する情報。
    """

    name: str
    snapshots: t.List[str]
    start_at: str
    plan_id: str


class GetEnvironmentsResponse(CustomMethodResponseBaseClass):
    """
    Response containing all environments in the current project.
    現在のプロジェクト内のすべての環境を含む応答。
    """

    environments: t.Dict[str, EnvironmentInfo]
    pinned_environments: t.Set[str]
    default_target_environment: str


GET_MODELS_FEATURE = "sqlmesh/get_models"


class GetModelsRequest(CustomMethodRequestBaseClass):
    """
    Request to get all models available for table diff.
    テーブル差分に使用可能なすべてのモデルを取得するよう要求します。
    """

    pass


class ModelInfo(PydanticModel):
    """
    Information about a model for table diff.
    テーブル diff のモデルに関する情報。
    """

    name: str
    fqn: str
    description: t.Optional[str] = None


class GetModelsResponse(CustomMethodResponseBaseClass):
    """
    Response containing all models available for table diff.
    テーブル diff に使用可能なすべてのモデルを含む応答。
    """

    models: t.List[ModelInfo]
