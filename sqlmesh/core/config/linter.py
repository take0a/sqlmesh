from __future__ import annotations

import typing as t

from sqlglot import exp
from sqlglot.helper import ensure_collection

from sqlmesh.core.config.base import BaseConfig

from sqlmesh.utils.pydantic import field_validator


class LinterConfig(BaseConfig):
    """Configuration for model linting
    モデルのリンティングの設定

    Args:
        enabled: Flag indicating whether the linter should run
            リンターを実行するかどうかを示すフラグ

        rules: A list of error rules to be applied on model
            モデルに適用されるエラールールのリスト
        warn_rules: A list of rules to be applied on models but produce warnings instead of raising errors.
            モデルに適用されるが、エラーを発生させる代わりに警告を生成するルールのリスト。
        ignored_rules: A list of rules to be excluded/ignored
            除外/無視するルールのリスト

    """

    enabled: bool = False

    rules: t.Set[str] = set()
    warn_rules: t.Set[str] = set()
    ignored_rules: t.Set[str] = set()

    @classmethod
    def _validate_rules(cls, v: t.Any) -> t.Set[str]:
        if isinstance(v, exp.Paren):
            v = v.unnest().name
        elif isinstance(v, (exp.Tuple, exp.Array)):
            v = [e.name for e in v.expressions]
        elif isinstance(v, exp.Expression):
            v = v.name

        return {name.lower() for name in ensure_collection(v)}

    @field_validator("rules", "warn_rules", "ignored_rules", mode="before")
    def rules_validator(cls, vs: t.Any) -> t.Set[str]:
        return cls._validate_rules(vs)
