"""Standard canonicalizer plugin for accuralai-core."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from string import Template
from typing import Any, Iterable, Mapping, MutableMapping, Optional, Sequence

from pydantic import BaseModel, Field, ValidationError

from accuralai_core.contracts.models import GenerateRequest
from accuralai_core.contracts.protocols import Canonicalizer
from accuralai_core.config.schema import PluginSettings


def _normalize_tags(tags: Iterable[str]) -> list[str]:
    """Lowercase and deduplicate tags preserving sorted order."""
    normalized = sorted({tag.strip().lower() for tag in tags if tag.strip()})
    return normalized


def _stable_json(obj: Any) -> str:
    """Serialize to canonical JSON (sorted keys)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _generate_cache_key(request: GenerateRequest, *, extra_fields: Sequence[str]) -> str:
    """Generate a deterministic cache key for the request."""
    payload: dict[str, Any] = {
        "prompt": request.prompt,
        "system_prompt": request.system_prompt,
        "history": request.history,
        "parameters": request.parameters,
        "metadata": {field: request.metadata.get(field) for field in extra_fields},
        "tags": request.tags,
    }
    digest = hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()
    return f"req:{digest}"


class CanonicalizerOptions(BaseModel):
    """Configuration options for the standard canonicalizer."""

    prompt_template: Optional[str] = None
    prompt_whitespace: bool = True
    normalize_tags: bool = True
    default_tags: list[str] = Field(default_factory=list)
    metadata_defaults: dict[str, Any] = Field(default_factory=dict)
    auto_cache_key: bool = True
    cache_key_metadata_fields: list[str] = Field(default_factory=list)


@dataclass(slots=True)
class StandardCanonicalizer(Canonicalizer):
    """Default canonicalizer used by AccuralAI."""

    options: CanonicalizerOptions = field(default_factory=CanonicalizerOptions)

    async def canonicalize(self, request: GenerateRequest) -> GenerateRequest:
        """Normalize request data and derive cache keys if needed."""
        updated: dict[str, Any] = {}

        prompt = request.prompt
        if self.options.prompt_whitespace:
            prompt = " ".join(prompt.split())

        if self.options.prompt_template:
            prompt = Template(self.options.prompt_template).safe_substitute(
                prompt=prompt,
                system_prompt=request.system_prompt or "",
                tags=",".join(request.tags),
            )

        updated["prompt"] = prompt

        tags = list(request.tags)
        tags.extend(self.options.default_tags)
        if self.options.normalize_tags:
            tags = _normalize_tags(tags)
        updated["tags"] = tags

        metadata = dict(request.metadata)
        for key, value in self.options.metadata_defaults.items():
            metadata.setdefault(key, value)
        updated["metadata"] = metadata

        cache_key = request.cache_key
        if self.options.auto_cache_key and not cache_key:
            cache_key = _generate_cache_key(
                request.model_copy(update=updated),
                extra_fields=self.options.cache_key_metadata_fields,
            )
        updated["cache_key"] = cache_key

        return request.model_copy(update=updated)


async def build_standard_canonicalizer(
    *,
    config: PluginSettings | Mapping[str, Any] | None = None,
    **_: Any,
) -> Canonicalizer:
    """Factory entry point for registering the standard canonicalizer."""
    options_data: Mapping[str, Any] | None = None
    if isinstance(config, PluginSettings):
        options_data = config.options
    elif isinstance(config, Mapping):
        options_data = dict(config)

    try:
        options = CanonicalizerOptions.model_validate(options_data or {})
    except ValidationError as error:
        message = f"Invalid canonicalizer options: {error}"
        raise ValueError(message) from error
    return StandardCanonicalizer(options=options)
