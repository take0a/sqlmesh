"""
This module maps the LSP custom API calls to the SQLMesh web api.

Allowing the LSP to call the web api without having to know the details of the web api
and thus passing through the details of the web api to the LSP, so that both the LSP
and the web api can communicate with the same process, avoiding the need to have a
separate process for the web api.

このモジュールは、LSP カスタム API 呼び出しを SQLMesh Web API にマッピングします。

LSP が Web API の詳細を知らなくても Web API を呼び出せるようにし、
Web API の詳細を LSP に渡すことで、LSP と Web API の両方が同じプロセスで通信できるようになり、
Web API 用に別のプロセスを用意する必要がなくなります。
"""

import typing as t
from pydantic import field_validator
from sqlmesh.lsp.custom import (
    CustomMethodRequestBaseClass,
    CustomMethodResponseBaseClass,
)
from web.server.models import LineageColumn, Model, TableDiff

API_FEATURE = "sqlmesh/api"


class ApiRequest(CustomMethodRequestBaseClass):
    """
    Request to call the SQLMesh API.
    This is a generic request that can be used to call any API endpoint.
    SQLMesh API を呼び出すためのリクエストです。
    これは、任意の API エンドポイントを呼び出すために使用できる汎用リクエストです。
    """

    requestId: str
    url: str
    method: t.Optional[str] = "GET"
    params: t.Optional[t.Dict[str, t.Any]] = None
    body: t.Optional[t.Dict[str, t.Any]] = None


class BaseAPIResponse(CustomMethodResponseBaseClass):
    error: t.Optional[str] = None


class ApiResponseGetModels(BaseAPIResponse):
    """
    Response from the SQLMesh API for the get_models endpoint.
    get_models エンドポイントに対する SQLMesh API からの応答。
    """

    data: t.List[Model]

    @field_validator("data", mode="before")
    def sanitize_datetime_fields(cls, data: t.List[Model]) -> t.List[Model]:
        """
        Convert datetime objects to None to avoid serialization issues.
        シリアル化の問題を回避するため、datetime オブジェクトを None に変換します。
        """
        if isinstance(data, list):
            for model in data:
                if hasattr(model, "details") and model.details:
                    # Convert datetime fields to None to avoid serialization issues
                    for field in ["stamp", "start", "cron_prev", "cron_next"]:
                        if (
                            hasattr(model.details, field)
                            and getattr(model.details, field) is not None
                        ):
                            setattr(model.details, field, None)
        return data


class ApiResponseGetLineage(BaseAPIResponse):
    """
    Response from the SQLMesh API for the get_lineage endpoint.
    get_lineage エンドポイントに対する SQLMesh API からの応答。
    """

    data: t.Dict[str, t.List[str]]


class ApiResponseGetColumnLineage(BaseAPIResponse):
    """
    Response from the SQLMesh API for the get_column_lineage endpoint.
    get_column_lineage エンドポイントに対する SQLMesh API からの応答。
    """

    data: t.Dict[str, t.Dict[str, LineageColumn]]


class ApiResponseGetTableDiff(BaseAPIResponse):
    """
    Response from the SQLMesh API for the get_table_diff endpoint.
    get_table_diff エンドポイントに対する SQLMesh API からの応答。
    """

    data: t.Optional[TableDiff]
