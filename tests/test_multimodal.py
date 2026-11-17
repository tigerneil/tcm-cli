"""Tests for SOTA multimodal model catalog, attachments, CIE L*a*b* biometrics, and routing."""
from __future__ import annotations

import base64
import struct
import zlib

import pytest

from tcm.agent.config import Config, VALID_LLM_PROVIDERS
from tcm.models.llm import MODEL_CATALOG, list_models, resolve_provider
from tcm.models.multimodal import (
    MediaAttachment,
    SUPPORTED_RECOMMENDATION_TASKS,
    build_anthropic_messages,
    build_google_contents,
    build_openai_messages,
    extract_image_biometrics,
    load_attachment,
    recommend_models_for_task,
)


def _make_rgb_png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    """Create a minimal valid 8-bit RGB PNG image in memory."""
    r, g, b = rgb
    row = b"\x00" + bytes([r, g, b]) * width
    raw_scanlines = row * height

    def _chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(raw_scanlines)
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")


class TestSOTAModelsAndProviders:
    def test_sota_models_registered(self):
        sota_ids = [
            "claude-fable-5-2",
            "claude-opus-5-5",
            "claude-sonnet-5-5",
            "claude-haiku-5-5",
            "gpt-6-astra",
            "gpt-6.1-sol",
            "gpt-6.1-terra",
            "gpt-6-luna",
            "gpt-5.4",
            "gpt-rosalind-research",
            "gemini-3.6-flash",
            "gemini-3.5-flash-lite",
            "deepseek-v4-pro",
            "deepseek-v4.1-flash",
            "qwen3.8-max",
            "qwen-vl-max",
            "kimi-k3.1-pro",
            "glm-5.3",
            "glm-4v-plus",
            "minimax-m3",
            "grok-4.8",
            "pixtral-large-latest",
            "ollama/medgemma:27b",
            "ollama/huatuogpt-vision:7b",
        ]
        for mid in sota_ids:
            assert mid in MODEL_CATALOG, f"Missing SOTA model {mid}"

    def test_modality_filtering(self):
        vision_models = list_models(modality="vision")
        assert len(vision_models) >= 20
        assert all(m.supports_modality("vision") for m in vision_models)

        audio_models = list_models(modality="audio")
        assert len(audio_models) >= 4
        assert all(m.supports_modality("audio") for m in audio_models)

        frontier_models = list_models(tier="frontier")
        assert len(frontier_models) >= 6
        assert all(m.tier == "frontier" for m in frontier_models)

    def test_new_providers_supported_in_config(self):
        for prov in ("glm", "xai", "together", "openrouter", "ollama"):
            assert prov in VALID_LLM_PROVIDERS

        cfg = Config()
        cfg.set("llm.model", "glm-5.3")
        assert cfg.get("llm.provider") == "glm"

        cfg.set("llm.model", "grok-4.8")
        assert cfg.get("llm.provider") == "xai"

        cfg.set("llm.model", "ollama/huatuogpt-vision:7b")
        assert cfg.get("llm.provider") == "ollama"

        cfg.set("agent.profile", "studio")
        assert cfg.get("agent.profile") == "studio"

    def test_prefix_resolution_for_new_providers(self):
        assert resolve_provider("glm-future") == "glm"
        assert resolve_provider("grok-5-preview") == "xai"
        assert resolve_provider("ollama/custom-tcm:latest") == "ollama"
        assert resolve_provider("openrouter/anthropic/claude-opus-5-5") == "openrouter"


class TestAttachmentsAndBiometrics:
    def test_load_attachment_from_file_and_data_uri(self, tmp_path):
        png_bytes = _make_rgb_png(24, 24, (215, 110, 115))
        img_file = tmp_path / "tongue_sample.png"
        img_file.write_bytes(png_bytes)

        att = load_attachment(img_file)
        assert isinstance(att, MediaAttachment)
        assert att.kind == "image"
        assert att.mime_type == "image/png"
        assert att.size_bytes() == len(png_bytes)
        assert att.to_data_uri().startswith("data:image/png;base64,")

        att_from_uri = load_attachment(att.to_data_uri())
        assert att_from_uri.kind == "image"
        assert att_from_uri.to_bytes() == png_bytes

    def test_load_attachment_remote_url(self):
        att = load_attachment("https://example.org/specimen.jpg")
        assert att.kind == "image"
        assert att.url == "https://example.org/specimen.jpg"

    def test_biometrics_crimson_vs_pale_tongue(self):
        crimson_png = _make_rgb_png(32, 32, (210, 45, 55))
        pale_png = _make_rgb_png(32, 32, (230, 205, 205))

        crimson_bio = extract_image_biometrics(crimson_png)
        pale_bio = extract_image_biometrics(pale_png)

        assert crimson_bio["format"] == "PNG"
        assert crimson_bio["width"] == 32
        assert crimson_bio["height"] == 32
        assert "tip" in crimson_bio["zones"]
        assert "center" in crimson_bio["zones"]
        assert "sides" in crimson_bio["zones"]
        assert "root" in crimson_bio["zones"]

        # Crimson tongue must have significantly higher CIE a* redness than pale tongue
        assert crimson_bio["lab_approx"]["a"] > pale_bio["lab_approx"]["a"] + 20
        assert crimson_bio["redness_index"] > pale_bio["redness_index"]
        assert len(crimson_bio["tcm_visual_hints"]) >= 1


class TestPayloadFormattersAndRouting:
    def test_provider_message_builders(self):
        png_bytes = _make_rgb_png(8, 8, (180, 90, 90))
        att = MediaAttachment(
            kind="image",
            mime_type="image/png",
            data_b64=base64.b64encode(png_bytes).decode("ascii"),
            filename="tongue.png",
        )
        base_msgs = [{"role": "user", "content": "Analyze this tongue coating."}]

        anth = build_anthropic_messages(base_msgs, [att])
        assert isinstance(anth[-1]["content"], list)
        assert any(block.get("type") == "image" for block in anth[-1]["content"])

        oai = build_openai_messages("You are a TCM clinician.", base_msgs, [att])
        assert oai[0]["role"] == "system"
        assert isinstance(oai[-1]["content"], list)
        assert any(part.get("type") == "image_url" for part in oai[-1]["content"])

        g_contents = build_google_contents("System prompt", base_msgs, [att])
        assert len(g_contents) >= 1

    @pytest.mark.parametrize("task", sorted(SUPPORTED_RECOMMENDATION_TASKS))
    def test_recommend_models_for_all_tasks(self, task):
        recs = recommend_models_for_task(task)
        assert 1 <= len(recs) <= 5
        top = recs[0]
        assert "id" in top and "provider" in top and "reason" in top
        if task in ("tongue_vision", "herb_identification", "classical_ocr"):
            assert "vision" in top["modalities"]
        if task == "offline_local":
            assert top["provider"] == "ollama"
