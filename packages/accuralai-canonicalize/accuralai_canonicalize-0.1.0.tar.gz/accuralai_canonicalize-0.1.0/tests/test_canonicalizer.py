import pytest

from accuralai_core.contracts.models import GenerateRequest

from accuralai_canonicalize.canonicalizer import (
    CanonicalizerOptions,
    StandardCanonicalizer,
    build_standard_canonicalizer,
)


@pytest.mark.anyio("asyncio")
async def test_standard_canonicalizer_generates_cache_key_and_normalizes():
    canonicalizer = StandardCanonicalizer(
        options=CanonicalizerOptions(
            default_tags=["Demo"],
            cache_key_metadata_fields=["topic"],
            metadata_defaults={"topic": "general"},
        )
    )

    request = GenerateRequest(prompt="  Hello   World  ", tags=["Test"])
    canonical = await canonicalizer.canonicalize(request)

    assert canonical.prompt == "Hello World"
    assert canonical.tags == ["demo", "test"]
    assert canonical.metadata["topic"] == "general"
    assert canonical.cache_key is not None


@pytest.mark.anyio("asyncio")
async def test_factory_uses_plugin_settings():
    canonicalizer = await build_standard_canonicalizer(
        config={"default_tags": ["One", "Two"], "normalize_tags": True}
    )

    request = GenerateRequest(prompt="hey", tags=["alpha"])
    canonical = await canonicalizer.canonicalize(request)

    assert canonical.tags == ["alpha", "one", "two"]
