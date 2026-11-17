from __future__ import annotations

"""
Unified LLM client: supports 15 cloud and local providers with native multimodal
(vision, audio, video, PDF, thinking) capabilities.

Provides a consistent interface regardless of backend.
"""

from dataclasses import dataclass, field
import logging
import os
import time
from typing import TYPE_CHECKING, Generator, Optional

if TYPE_CHECKING:
    from tcm.models.multimodal import MediaAttachment

logger = logging.getLogger("tcm.llm")


@dataclass
class LLMResponse:
    """Standardized response from any LLM backend."""

    content: str
    model: str
    usage: dict = None
    raw: object = None
    content_blocks: list = None


# ─── Model catalog ────────────────────────────────────────────


@dataclass
class ModelInfo:
    """Metadata for a supported LLM model."""

    id: str
    provider: str
    display_name: str
    context_window: int
    input_price: float   # USD per million tokens
    output_price: float  # USD per million tokens
    description: str = ""
    modalities: tuple[str, ...] = ("text",)
    max_output: int = 8192
    tier: str = "flagship"
    tcm_strengths: tuple[str, ...] = ()

    def supports_modality(self, modality: str) -> bool:
        return modality.lower() in self.modalities

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "provider": self.provider,
            "display_name": self.display_name,
            "context_window": self.context_window,
            "input_price": self.input_price,
            "output_price": self.output_price,
            "description": self.description,
            "modalities": list(self.modalities),
            "max_output": self.max_output,
            "tier": self.tier,
            "tcm_strengths": list(self.tcm_strengths),
        }


MODEL_CATALOG: dict[str, ModelInfo] = {}


def _register(*models: ModelInfo):
    for m in models:
        MODEL_CATALOG[m.id] = m


_register(
    # ── Anthropic (SOTA Nov 2026 + Production) ─────────────
    ModelInfo(
        id="claude-fable-5-2",
        provider="anthropic",
        display_name="Claude Fable 5.2",
        context_window=1_000_000,
        input_price=8.00,
        output_price=40.00,
        description="Frontier adaptive reasoning & long-horizon multimodal research",
        modalities=("text", "vision", "pdf", "thinking"),
        max_output=128_000,
        tier="frontier",
        tcm_strengths=("network_pharmacology", "clinical_safety"),
    ),
    ModelInfo(
        id="claude-opus-5-5",
        provider="anthropic",
        display_name="Claude Opus 5.5",
        context_window=1_000_000,
        input_price=4.00,
        output_price=20.00,
        description="Flagship multimodal synthesis, pharmacology & knowledge work",
        modalities=("text", "vision", "pdf", "thinking"),
        max_output=128_000,
        tier="frontier",
        tcm_strengths=("clinical_safety", "network_pharmacology", "tongue_vision", "bilingual_synthesis"),
    ),
    ModelInfo(
        id="claude-sonnet-5-5",
        provider="anthropic",
        display_name="Claude Sonnet 5.5",
        context_window=1_000_000,
        input_price=2.00,
        output_price=10.00,
        description="High-speed multimodal clinical & research reasoning",
        modalities=("text", "vision", "pdf", "thinking"),
        max_output=128_000,
        tier="flagship",
        tcm_strengths=("general", "herb_identification"),
    ),
    ModelInfo(
        id="claude-haiku-5-5",
        provider="anthropic",
        display_name="Claude Haiku 5.5",
        context_window=1_000_000,
        input_price=0.10,
        output_price=0.50,
        description="Ultra-low-latency multimodal triage & extraction",
        modalities=("text", "vision", "pdf"),
        max_output=128_000,
        tier="fast",
    ),
    ModelInfo(
        id="claude-sonnet-4-5-20250929",
        provider="anthropic",
        display_name="Claude Sonnet 4.5",
        context_window=200_000,
        input_price=3.00,
        output_price=15.00,
        description="Best balance of speed and intelligence",
        modalities=("text", "vision", "pdf", "thinking"),
        max_output=64_000,
        tier="flagship",
    ),
    ModelInfo(
        id="claude-haiku-4-5-20251001",
        provider="anthropic",
        display_name="Claude Haiku 4.5",
        context_window=200_000,
        input_price=0.80,
        output_price=4.00,
        description="Fastest and most affordable",
        modalities=("text", "vision", "pdf"),
        max_output=64_000,
        tier="fast",
    ),
    ModelInfo(
        id="claude-opus-4-6",
        provider="anthropic",
        display_name="Claude Opus 4.6",
        context_window=200_000,
        input_price=15.00,
        output_price=75.00,
        description="Most capable for complex research",
        modalities=("text", "vision", "pdf", "thinking"),
        max_output=64_000,
        tier="frontier",
    ),
    # ── OpenAI (SOTA Nov 2026 + Production) ────────────────
    ModelInfo(
        id="gpt-6-astra",
        provider="openai",
        display_name="GPT-6 Astra",
        context_window=1_050_000,
        input_price=10.00,
        output_price=50.00,
        description="Most capable OpenAI frontier model for complex multimodal reasoning",
        modalities=("text", "vision", "audio", "pdf", "thinking"),
        max_output=128_000,
        tier="frontier",
        tcm_strengths=("network_pharmacology", "clinical_safety"),
    ),
    ModelInfo(
        id="gpt-6.1-sol",
        provider="openai",
        display_name="GPT-6.1 Sol",
        context_window=1_050_000,
        input_price=2.00,
        output_price=10.00,
        description="Near-Astra intelligence & cost efficiency for multi-step TCM research",
        modalities=("text", "vision", "pdf", "thinking"),
        max_output=128_000,
        tier="flagship",
        tcm_strengths=("general", "network_pharmacology"),
    ),
    ModelInfo(
        id="gpt-6.1-terra",
        provider="openai",
        display_name="GPT-6.1 Terra",
        context_window=1_050_000,
        input_price=1.00,
        output_price=5.00,
        description="Precision visual reasoning for tongue & herb specimen diagnostics",
        modalities=("text", "vision", "pdf"),
        max_output=128_000,
        tier="balanced",
        tcm_strengths=("tongue_vision", "herb_identification"),
    ),
    ModelInfo(
        id="gpt-6-luna",
        provider="openai",
        display_name="GPT-6 Luna",
        context_window=1_050_000,
        input_price=0.10,
        output_price=0.50,
        description="High-throughput multimodal screening & literature parsing",
        modalities=("text", "vision"),
        max_output=128_000,
        tier="fast",
    ),
    ModelInfo(
        id="gpt-5.4",
        provider="openai",
        display_name="GPT-5.4",
        context_window=1_000_000,
        input_price=1.75,
        output_price=7.00,
        description="Structured biomedical reasoning & tool orchestration",
        modalities=("text", "vision", "thinking"),
        max_output=64_000,
        tier="flagship",
    ),
    ModelInfo(
        id="gpt-rosalind-research",
        provider="openai",
        display_name="GPT-Rosalind",
        context_window=1_000_000,
        input_price=6.00,
        output_price=24.00,
        description="Purpose-built life sciences, ADMET & molecular target reasoning",
        modalities=("text", "vision", "thinking"),
        max_output=64_000,
        tier="specialized",
        tcm_strengths=("network_pharmacology", "clinical_safety"),
    ),
    ModelInfo(
        id="gpt-4o",
        provider="openai",
        display_name="GPT-4o",
        context_window=128_000,
        input_price=2.50,
        output_price=10.00,
        description="High-intelligence flagship model",
        modalities=("text", "vision", "audio"),
        max_output=16_384,
        tier="flagship",
    ),
    ModelInfo(
        id="gpt-4o-mini",
        provider="openai",
        display_name="GPT-4o Mini",
        context_window=128_000,
        input_price=0.15,
        output_price=0.60,
        description="Fast and affordable small model",
        modalities=("text", "vision"),
        max_output=16_384,
        tier="fast",
    ),
    ModelInfo(
        id="o3-mini",
        provider="openai",
        display_name="o3-mini",
        context_window=200_000,
        input_price=1.10,
        output_price=4.40,
        description="Reasoning model, good for analysis",
        modalities=("text", "thinking"),
        max_output=65_536,
        tier="balanced",
    ),
    ModelInfo(
        id="gpt-4.1",
        provider="openai",
        display_name="GPT-4.1",
        context_window=1_047_576,
        input_price=2.00,
        output_price=8.00,
        description="Latest flagship with 1M context",
        modalities=("text", "vision", "pdf"),
        max_output=32_768,
        tier="flagship",
    ),
    ModelInfo(
        id="gpt-4.1-mini",
        provider="openai",
        display_name="GPT-4.1 Mini",
        context_window=1_047_576,
        input_price=0.40,
        output_price=1.60,
        description="Balanced speed and intelligence",
        modalities=("text", "vision", "pdf"),
        max_output=32_768,
        tier="balanced",
    ),
    ModelInfo(
        id="gpt-4.1-nano",
        provider="openai",
        display_name="GPT-4.1 Nano",
        context_window=1_047_576,
        input_price=0.10,
        output_price=0.40,
        description="Fastest, most cost-effective",
        modalities=("text", "vision"),
        max_output=32_768,
        tier="fast",
    ),
    # ── Google (Gemini SOTA Nov 2026 + Production) ─────────
    ModelInfo(
        id="gemini-3.6-flash",
        provider="google",
        display_name="Gemini 3.6 Flash",
        context_window=1_048_576,
        input_price=0.20,
        output_price=0.80,
        description="Native omni-modal Flash for tongue vision, pulse/cough audio & video",
        modalities=("text", "vision", "audio", "video", "pdf", "thinking"),
        max_output=65_536,
        tier="flagship",
        tcm_strengths=("tongue_vision", "herb_identification", "general"),
    ),
    ModelInfo(
        id="gemini-3.5-flash-lite",
        provider="google",
        display_name="Gemini 3.5 Flash-Lite",
        context_window=1_048_576,
        input_price=0.08,
        output_price=0.32,
        description="High-efficiency native multimodal model",
        modalities=("text", "vision", "audio", "pdf"),
        max_output=65_536,
        tier="fast",
    ),
    ModelInfo(
        id="gemini-3.1-pro-preview",
        provider="google",
        display_name="Gemini 3.1 Pro Preview",
        context_window=1_048_576,
        input_price=2.00,
        output_price=12.00,
        description="Frontier Gemini 3.1 Pro omni-modal reasoning",
        modalities=("text", "vision", "audio", "video", "pdf", "thinking"),
        max_output=65_536,
        tier="frontier",
        tcm_strengths=("classical_ocr", "tongue_vision"),
    ),
    ModelInfo(
        id="gemini-3-pro-preview",
        provider="google",
        display_name="Gemini 3 Pro Preview",
        context_window=1_048_576,
        input_price=0.00,
        output_price=0.00,
        description="Frontier Gemini 3 Pro, early access",
        modalities=("text", "vision", "audio", "video", "pdf", "thinking"),
        max_output=65_536,
        tier="frontier",
    ),
    ModelInfo(
        id="gemini-3-flash-preview",
        provider="google",
        display_name="Gemini 3 Flash Preview",
        context_window=1_048_576,
        input_price=0.00,
        output_price=0.00,
        description="Frontier Gemini 3 Flash, early access",
        modalities=("text", "vision", "audio", "video", "pdf", "thinking"),
        max_output=65_536,
        tier="flagship",
    ),
    ModelInfo(
        id="gemini-2.5-pro",
        provider="google",
        display_name="Gemini 2.5 Pro",
        context_window=1_048_576,
        input_price=1.25,
        output_price=10.00,
        description="Most capable Gemini, best for complex reasoning",
        modalities=("text", "vision", "audio", "video", "pdf", "thinking"),
        max_output=65_536,
        tier="flagship",
    ),
    ModelInfo(
        id="gemini-2.5-flash",
        provider="google",
        display_name="Gemini 2.5 Flash",
        context_window=1_048_576,
        input_price=0.15,
        output_price=0.60,
        description="Fast mid-size multimodal model",
        modalities=("text", "vision", "audio", "video", "pdf", "thinking"),
        max_output=65_536,
        tier="balanced",
    ),
    ModelInfo(
        id="gemini-2.5-flash-lite",
        provider="google",
        display_name="Gemini 2.5 Flash-Lite",
        context_window=1_048_576,
        input_price=0.075,
        output_price=0.30,
        description="Cost-efficient Gemini 2.5 model",
        modalities=("text", "vision", "audio", "video", "pdf"),
        max_output=65_536,
        tier="fast",
    ),
    ModelInfo(
        id="gemini-2.0-flash",
        provider="google",
        display_name="Gemini 2.0 Flash",
        context_window=1_048_576,
        input_price=0.10,
        output_price=0.40,
        description="Fast, versatile next-gen multimodal model",
        modalities=("text", "vision", "audio", "video", "pdf"),
        max_output=8_192,
        tier="balanced",
    ),
    ModelInfo(
        id="gemini-2.0-flash-lite",
        provider="google",
        display_name="Gemini 2.0 Flash-Lite",
        context_window=1_048_576,
        input_price=0.075,
        output_price=0.30,
        description="Most cost-efficient Gemini 2.0 model",
        modalities=("text", "vision", "audio", "video", "pdf"),
        max_output=8_192,
        tier="fast",
    ),
    ModelInfo(
        id="gemini-pro-latest",
        provider="google",
        display_name="Gemini Pro Latest",
        context_window=1_048_576,
        input_price=0.00,
        output_price=0.00,
        description="Alias to latest stable Gemini Pro",
        modalities=("text", "vision", "audio", "video", "pdf", "thinking"),
        max_output=65_536,
        tier="flagship",
    ),
    ModelInfo(
        id="gemini-flash-latest",
        provider="google",
        display_name="Gemini Flash Latest",
        context_window=1_048_576,
        input_price=0.00,
        output_price=0.00,
        description="Alias to latest stable Gemini Flash",
        modalities=("text", "vision", "audio", "video", "pdf", "thinking"),
        max_output=65_536,
        tier="balanced",
    ),
    # ── DeepSeek ───────────────────────────────────────────
    ModelInfo(
        id="deepseek-v4-pro",
        provider="deepseek",
        display_name="DeepSeek V4 Pro",
        context_window=1_000_000,
        input_price=0.66,
        output_price=1.98,
        description="1.6T MoE frontier reasoning for classical TCM & network pharmacology",
        modalities=("text", "thinking"),
        max_output=128_000,
        tier="frontier",
        tcm_strengths=("network_pharmacology", "bilingual_synthesis"),
    ),
    ModelInfo(
        id="deepseek-v4.1-flash",
        provider="deepseek",
        display_name="DeepSeek V4.1 Flash",
        context_window=1_000_000,
        input_price=0.15,
        output_price=0.60,
        description="552B MoE with native vision, 1M context & bilingual medical fluency",
        modalities=("text", "vision", "thinking"),
        max_output=384_000,
        tier="flagship",
        tcm_strengths=("general", "classical_ocr", "bilingual_synthesis"),
    ),
    ModelInfo(
        id="deepseek-v3.2",
        provider="deepseek",
        display_name="DeepSeek V3.2",
        context_window=128_000,
        input_price=0.00,
        output_price=0.00,
        description="Latest general model",
        modalities=("text",),
        max_output=16_384,
        tier="balanced",
    ),
    ModelInfo(
        id="deepseek-r1",
        provider="deepseek",
        display_name="DeepSeek R1",
        context_window=128_000,
        input_price=0.00,
        output_price=0.00,
        description="Reasoning model",
        modalities=("text", "thinking"),
        max_output=32_768,
        tier="flagship",
    ),
    # ── Qwen (DashScope) ───────────────────────────────────
    ModelInfo(
        id="qwen3.8-max",
        provider="qwen",
        display_name="Qwen 3.8 Max",
        context_window=1_000_000,
        input_price=0.80,
        output_price=2.40,
        description="SOTA Chinese & classical Materia Medica philology",
        modalities=("text", "vision", "thinking"),
        max_output=64_000,
        tier="frontier",
        tcm_strengths=("bilingual_synthesis", "classical_ocr"),
    ),
    ModelInfo(
        id="qwen-vl-max",
        provider="qwen",
        display_name="Qwen-VL Max",
        context_window=1_000_000,
        input_price=0.40,
        output_price=1.20,
        description="High-resolution Chinese woodblock OCR, prescription & tongue vision",
        modalities=("text", "vision", "pdf"),
        max_output=32_000,
        tier="specialized",
        tcm_strengths=("classical_ocr", "tongue_vision", "herb_identification"),
    ),
    ModelInfo(
        id="qwen3.8-27b",
        provider="qwen",
        display_name="Qwen 3.8 27B",
        context_window=262_144,
        input_price=0.15,
        output_price=0.45,
        description="High-reliability open-weight agentic model",
        modalities=("text", "thinking"),
        max_output=32_000,
        tier="balanced",
    ),
    ModelInfo(
        id="qwen3-max",
        provider="qwen",
        display_name="Qwen3-Max",
        context_window=1_000_000,
        input_price=0.00,
        output_price=0.00,
        description="Flagship Qwen model",
        modalities=("text",),
        max_output=32_768,
        tier="flagship",
    ),
    ModelInfo(
        id="qwen-plus",
        provider="qwen",
        display_name="Qwen-Plus",
        context_window=200_000,
        input_price=0.00,
        output_price=0.00,
        description="Balanced speed/cost",
        modalities=("text",),
        max_output=16_384,
        tier="balanced",
    ),
    # ── Moonshot Kimi ──────────────────────────────────────
    ModelInfo(
        id="kimi-k3.1-pro",
        provider="kimi",
        display_name="Kimi K3.1 Pro",
        context_window=1_000_000,
        input_price=0.90,
        output_price=2.80,
        description="Long-context classical canon synthesis & multimodal reasoning",
        modalities=("text", "vision", "thinking"),
        max_output=64_000,
        tier="frontier",
        tcm_strengths=("classical_ocr", "bilingual_synthesis"),
    ),
    ModelInfo(
        id="kimi-k3",
        provider="kimi",
        display_name="Kimi K3",
        context_window=1_000_000,
        input_price=0.50,
        output_price=1.80,
        description="2.8T MoE open-weight bilingual model",
        modalities=("text", "vision"),
        max_output=64_000,
        tier="flagship",
    ),
    ModelInfo(
        id="kimi-k2.5",
        provider="kimi",
        display_name="Kimi K2.5",
        context_window=200_000,
        input_price=0.00,
        output_price=0.00,
        description="Flagship Kimi model",
        modalities=("text", "vision"),
        max_output=16_384,
        tier="flagship",
    ),
    # ── Zhipu GLM ──────────────────────────────────────────
    ModelInfo(
        id="glm-5.3",
        provider="glm",
        display_name="GLM-5.3",
        context_window=1_000_000,
        input_price=0.50,
        output_price=1.50,
        description="Bilingual Chinese clinical reasoning & syndrome differentiation",
        modalities=("text", "thinking"),
        max_output=64_000,
        tier="frontier",
        tcm_strengths=("bilingual_synthesis", "clinical_safety"),
    ),
    ModelInfo(
        id="glm-5.3-flash",
        provider="glm",
        display_name="GLM-5.3 Flash",
        context_window=1_000_000,
        input_price=0.08,
        output_price=0.25,
        description="Fast Chinese medical lookup & extraction",
        modalities=("text",),
        max_output=32_000,
        tier="fast",
    ),
    ModelInfo(
        id="glm-4v-plus",
        provider="glm",
        display_name="GLM-4V Plus",
        context_window=128_000,
        input_price=0.35,
        output_price=1.05,
        description="Chinese clinical imaging, tongue & prescription vision",
        modalities=("text", "vision"),
        max_output=16_384,
        tier="specialized",
        tcm_strengths=("tongue_vision", "classical_ocr"),
    ),
    # ── MiniMax ────────────────────────────────────────────
    ModelInfo(
        id="minimax-m3",
        provider="minimax",
        display_name="MiniMax M3",
        context_window=1_000_000,
        input_price=0.40,
        output_price=1.20,
        description="1M-context multimodal Chinese/English reasoning",
        modalities=("text", "vision", "audio"),
        max_output=64_000,
        tier="flagship",
    ),
    ModelInfo(
        id="minimax-m3.1-flash",
        provider="minimax",
        display_name="MiniMax M3.1 Flash",
        context_window=1_000_000,
        input_price=0.10,
        output_price=0.30,
        description="High-speed multimodal assistant",
        modalities=("text", "vision"),
        max_output=32_000,
        tier="fast",
    ),
    ModelInfo(
        id="minimax-m2.5",
        provider="minimax",
        display_name="MiniMax M2.5",
        context_window=200_000,
        input_price=0.00,
        output_price=0.00,
        description="Flagship MiniMax model",
        modalities=("text",),
        max_output=16_384,
        tier="flagship",
    ),
    # ── xAI (Grok) ─────────────────────────────────────────
    ModelInfo(
        id="grok-4.8",
        provider="xai",
        display_name="Grok 4.8",
        context_window=1_000_000,
        input_price=3.00,
        output_price=15.00,
        description="xAI frontier scientific reasoning & multimodal analysis",
        modalities=("text", "vision", "thinking"),
        max_output=128_000,
        tier="frontier",
    ),
    ModelInfo(
        id="grok-4-vision",
        provider="xai",
        display_name="Grok 4 Vision",
        context_window=256_000,
        input_price=2.00,
        output_price=10.00,
        description="High-precision visual inspection & biomedical synthesis",
        modalities=("text", "vision"),
        max_output=64_000,
        tier="flagship",
    ),
    # ── Mistral ────────────────────────────────────────────
    ModelInfo(
        id="mistral-large-latest",
        provider="mistral",
        display_name="Mistral Large",
        context_window=256_000,
        input_price=2.00,
        output_price=6.00,
        description="Flagship multilingual reasoning & tool synthesis",
        modalities=("text",),
        max_output=32_000,
        tier="flagship",
    ),
    ModelInfo(
        id="pixtral-large-latest",
        provider="mistral",
        display_name="Pixtral Large",
        context_window=128_000,
        input_price=2.00,
        output_price=6.00,
        description="Multimodal document & specimen vision",
        modalities=("text", "vision"),
        max_output=32_000,
        tier="specialized",
        tcm_strengths=("herb_identification",),
    ),
    # ── Groq ───────────────────────────────────────────────
    ModelInfo(
        id="llama-3.3-70b-versatile",
        provider="groq",
        display_name="Llama 3.3 70B Versatile",
        context_window=128_000,
        input_price=0.59,
        output_price=0.79,
        description="Ultra-low-latency LPU inference on Groq",
        modalities=("text",),
        max_output=32_768,
        tier="fast",
    ),
    ModelInfo(
        id="llama-3.1-70b-versatile",
        provider="groq",
        display_name="Llama 3.1 70B Versatile",
        context_window=128_000,
        input_price=0.59,
        output_price=0.79,
        description="High-speed LPU inference on Groq",
        modalities=("text",),
        max_output=32_768,
        tier="fast",
    ),
    # ── Cohere ─────────────────────────────────────────────
    ModelInfo(
        id="command-a-03-2025",
        provider="cohere",
        display_name="Command A",
        context_window=256_000,
        input_price=2.50,
        output_price=10.00,
        description="Enterprise RAG & grounded citation synthesis",
        modalities=("text",),
        max_output=8_192,
        tier="flagship",
    ),
    ModelInfo(
        id="command-r-plus",
        provider="cohere",
        display_name="Command R+",
        context_window=128_000,
        input_price=2.50,
        output_price=10.00,
        description="Grounded retrieval & multilingual synthesis",
        modalities=("text",),
        max_output=4_096,
        tier="balanced",
    ),
    # ── OpenRouter, Together AI & Local Ollama ─────────────
    ModelInfo(
        id="openrouter/auto",
        provider="openrouter",
        display_name="OpenRouter Auto SOTA",
        context_window=1_000_000,
        input_price=0.00,
        output_price=0.00,
        description="Dynamic routing across 200+ cloud & open-weight models",
        modalities=("text", "vision"),
        max_output=32_000,
        tier="balanced",
    ),
    ModelInfo(
        id="together/deepseek-v4-pro",
        provider="together",
        display_name="DeepSeek V4 Pro (Together)",
        context_window=1_000_000,
        input_price=0.80,
        output_price=2.40,
        description="Hosted open-weight frontier MoE",
        modalities=("text", "thinking"),
        max_output=64_000,
        tier="flagship",
    ),
    ModelInfo(
        id="ollama/qwen3:32b",
        provider="ollama",
        display_name="Qwen3 32B (Local Ollama)",
        context_window=131_072,
        input_price=0.00,
        output_price=0.00,
        description="Private on-premise TCM reasoning",
        modalities=("text", "thinking"),
        max_output=16_384,
        tier="local",
        tcm_strengths=("offline_local",),
    ),
    ModelInfo(
        id="ollama/medgemma:27b",
        provider="ollama",
        display_name="MedGemma 27B Multimodal (Local)",
        context_window=131_072,
        input_price=0.00,
        output_price=0.00,
        description="Local medical imaging & clinical decision support",
        modalities=("text", "vision"),
        max_output=8_192,
        tier="local",
        tcm_strengths=("offline_local", "tongue_vision"),
    ),
    ModelInfo(
        id="ollama/huatuogpt-vision:7b",
        provider="ollama",
        display_name="HuatuoGPT-Vision 7B (Local)",
        context_window=32_768,
        input_price=0.00,
        output_price=0.00,
        description="Specialized Chinese medical & tongue diagnosis local VLM",
        modalities=("text", "vision"),
        max_output=4_096,
        tier="local",
        tcm_strengths=("offline_local", "tongue_vision"),
    ),
)

# Provider prefix patterns for auto-detection of unknown models
# NOTE: Do NOT add ("llama-", ...) — bare "llama-*" IDs are intentionally unresolved
# unless explicitly registered in MODEL_CATALOG (e.g. Groq's llama-3.3-70b-versatile).
_PROVIDER_PREFIXES = [
    ("claude-", "anthropic"),
    ("gpt-", "openai"),
    ("o1-", "openai"),
    ("o3-", "openai"),
    ("o4-", "openai"),
    ("deepseek-", "deepseek"),
    ("kimi-", "kimi"),
    ("minimax", "minimax"),
    ("qwen", "qwen"),
    ("gemini-", "google"),
    ("glm-", "glm"),
    ("grok-", "xai"),
    ("pixtral-", "mistral"),
    ("mistral-", "mistral"),
    ("command-", "cohere"),
    ("openrouter/", "openrouter"),
    ("together/", "together"),
    ("ollama/", "ollama"),
]


def resolve_provider(model: str) -> Optional[str]:
    """Resolve the provider for a model name.

    Returns the provider string, or None if unrecognizable.
    Checks the catalog first, then falls back to prefix matching.
    """
    if not model:
        return None
    info = MODEL_CATALOG.get(model)
    if info:
        return info.provider
    model_lower = model.lower()
    for prefix, provider in _PROVIDER_PREFIXES:
        if model_lower.startswith(prefix):
            return provider
    return None


def list_models(
    provider: str | None = None,
    modality: str | None = None,
    tier: str | None = None,
) -> list[ModelInfo]:
    """List models from the catalog, optionally filtered by provider, modality, and tier."""
    models = list(MODEL_CATALOG.values())
    if provider:
        models = [m for m in models if m.provider == provider]
    if modality:
        mod_lower = modality.lower()
        models = [m for m in models if m.supports_modality(mod_lower)]
    if tier:
        tier_lower = tier.lower()
        models = [m for m in models if m.tier.lower() == tier_lower]
    return models


def list_google_models(api_key: str = None) -> list[dict]:
    """Query the Google Gemini API for all available models that support generateContent.

    Returns a list of dicts: {name, display_name, context_window, methods}.
    Requires a valid GOOGLE_API_KEY.
    """
    import os
    from google import genai as genai_sdk
    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise ValueError(
            "Google API key not configured. Run: tcm keys set -p google"
            " or export GOOGLE_API_KEY=..."
        )
    client = genai_sdk.Client(api_key=key)
    result = []
    for m in client.models.list():
        name = getattr(m, "name", "") or ""
        methods = list(getattr(m, "supported_actions", None) or [])
        # Prefer short id without "models/" prefix
        short_id = name.replace("models/", "")
        result.append({
            "id": short_id,
            "name": name,
            "display_name": getattr(m, "display_name", short_id),
            "description": getattr(m, "description", ""),
            "input_token_limit": getattr(m, "input_token_limit", None),
            "output_token_limit": getattr(m, "output_token_limit", None),
            "methods": methods,
        })
    # Sort: generateContent-capable first, then alpha
    result.sort(key=lambda x: ("generateContent" not in str(x["methods"]), x["id"]))
    return result


def model_pricing(model: str) -> Optional[dict]:
    """Get pricing info for a model. Returns {input, output} or None."""
    info = MODEL_CATALOG.get(model)
    if info:
        return {"input": info.input_price, "output": info.output_price}
    return None


@dataclass
class UsageTracker:
    """Tracks cumulative token usage and cost across LLM calls."""
    calls: list = field(default_factory=list)

    @property
    def total_input_tokens(self) -> int:
        return sum(c.get("input", 0) for c in self.calls)

    @property
    def total_output_tokens(self) -> int:
        return sum(c.get("output", 0) for c in self.calls)

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    @property
    def total_cost(self) -> float:
        return sum(c.get("cost", 0.0) for c in self.calls)

    def record(self, model: str, usage: dict):
        """Record a single LLM call's usage."""
        if not usage:
            return
        cost = self._estimate_cost(model, usage)
        self.calls.append({
            "model": model,
            "input": usage.get("input", 0),
            "output": usage.get("output", 0),
            "cost": cost,
        })

    def _estimate_cost(self, model: str, usage: dict) -> float:
        pricing = model_pricing(model)
        if not pricing:
            return 0.0
        input_cost = (usage.get("input", 0) / 1_000_000) * pricing["input"]
        output_cost = (usage.get("output", 0) / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def summary(self) -> str:
        """Human-readable usage summary."""
        if not self.calls:
            return "No LLM calls made."
        models_used = set(c["model"] for c in self.calls)
        return (
            f"{len(self.calls)} LLM calls | "
            f"{self.total_input_tokens:,} in + {self.total_output_tokens:,} out tokens | "
            f"${self.total_cost:.4f} | "
            f"models: {', '.join(models_used)}"
        )

    def reset(self):
        self.calls.clear()


_OPENAI_COMPAT_PROVIDERS = frozenset({
    "openai",
    "deepseek",
    "kimi",
    "minimax",
    "qwen",
    "glm",
    "xai",
    "mistral",
    "groq",
    "together",
    "openrouter",
    "ollama",
})


class LLMClient:
    """Unified LLM client supporting 15 cloud and local providers with multimodal attachments."""

    _OPENAI_COMPAT_PROVIDERS = _OPENAI_COMPAT_PROVIDERS

    DEFAULT_MODELS = {
        "anthropic": "claude-sonnet-4-5-20250929",
        "openai": "gpt-4o",
        "deepseek": "deepseek-v3.2",
        "kimi": "kimi-k2.5",
        "minimax": "minimax-m2.5",
        "qwen": "qwen3-max",
        "google": "gemini-2.5-flash",
        "glm": "glm-5.3",
        "xai": "grok-4.8",
        "mistral": "mistral-large-latest",
        "groq": "llama-3.1-70b-versatile",
        "cohere": "command-r-plus",
        "together": "together/deepseek-v4-pro",
        "openrouter": "openrouter/auto",
        "ollama": "ollama/qwen3:32b",
    }

    DEFAULT_BASE_URLS = {
        "openai": None,
        "deepseek": "https://api.deepseek.com/v1",
        "kimi": "https://api.moonshot.cn/v1",
        "minimax": "https://api.minimax.chat/v1",
        "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "glm": "https://open.bigmodel.cn/api/paas/v4",
        "xai": "https://api.x.ai/v1",
        "mistral": "https://api.mistral.ai/v1",
        "groq": "https://api.groq.com/openai/v1",
        "together": "https://api.together.xyz/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "ollama": "http://localhost:11434/v1",
    }

    def __init__(
        self,
        provider: str = "anthropic",
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self.provider = provider
        self.model = model or self.DEFAULT_MODELS.get(provider)
        self.api_key = api_key
        self.base_url = base_url
        self._client = None
        self.usage = UsageTracker()

    def _wire_model_id(self) -> str:
        """Normalize catalog model ID for providers that strip namespace prefixes."""
        m = self.model or ""
        if self.provider == "ollama" and m.startswith("ollama/"):
            return m[len("ollama/"):]
        if self.provider == "together" and m.startswith("together/"):
            return m[len("together/"):]
        return m

    def _get_client(self):
        """Lazily initialize the appropriate client."""
        if self._client is not None:
            return self._client

        if self.provider == "anthropic":
            import anthropic

            self._client = anthropic.Anthropic(
                api_key=self.api_key or os.environ.get("ANTHROPIC_API_KEY")
            )
        elif self.provider in _OPENAI_COMPAT_PROVIDERS:
            import openai

            key = self.api_key
            if not key:
                env_fallbacks = {
                    "openai": "OPENAI_API_KEY",
                    "deepseek": "DEEPSEEK_API_KEY",
                    "kimi": "MOONSHOT_API_KEY",
                    "minimax": "MINIMAX_API_KEY",
                    "qwen": "DASHSCOPE_API_KEY",
                    "glm": "ZHIPUAI_API_KEY",
                    "xai": "XAI_API_KEY",
                    "mistral": "MISTRAL_API_KEY",
                    "groq": "GROQ_API_KEY",
                    "together": "TOGETHER_API_KEY",
                    "openrouter": "OPENROUTER_API_KEY",
                    "ollama": "OLLAMA_API_KEY",
                }
                env_name = env_fallbacks.get(self.provider, "OPENAI_API_KEY")
                key = os.environ.get(env_name)
                if not key and self.provider == "glm":
                    key = os.environ.get("GLM_API_KEY")
            if not key and self.provider == "ollama":
                key = "ollama"

            base_url = (
                self.base_url
                if self.base_url is not None
                else self.DEFAULT_BASE_URLS.get(self.provider)
            )
            if base_url:
                self._client = openai.OpenAI(api_key=key, base_url=base_url)
            else:
                self._client = openai.OpenAI(api_key=key)
        elif self.provider == "google":
            from google import genai as genai_sdk

            key = self.api_key or os.environ.get("GOOGLE_API_KEY")
            self._client = genai_sdk.Client(api_key=key)
        elif self.provider == "cohere":
            import cohere

            key = self.api_key or os.environ.get("COHERE_API_KEY")
            self._client = cohere.Client(api_key=key)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

        return self._client

    def chat(
        self,
        system: str,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        attachments: list[MediaAttachment] | None = None,
    ) -> LLMResponse:
        """Send a chat completion request (supports multimodal attachments)."""
        client = self._get_client()

        if self.provider == "anthropic":
            resp = self._chat_anthropic(
                client, system, messages, temperature, max_tokens, tools, attachments
            )
        elif self.provider in _OPENAI_COMPAT_PROVIDERS:
            resp = self._chat_openai(
                client, system, messages, temperature, max_tokens, attachments
            )
        elif self.provider == "google":
            resp = self._chat_google(
                client, system, messages, temperature, max_tokens, attachments
            )
        elif self.provider == "cohere":
            resp = self._chat_cohere(
                client, system, messages, temperature, max_tokens, attachments
            )
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

        if resp.usage:
            self.usage.record(resp.model, resp.usage)

        return resp

    def stream(
        self,
        system: str,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        attachments: list[MediaAttachment] | None = None,
    ) -> Generator[str, None, None]:
        """Stream a chat completion, yielding text chunks."""
        client = self._get_client()

        if self.provider == "anthropic":
            yield from self._stream_anthropic(
                client, system, messages, temperature, max_tokens, attachments
            )
        elif self.provider in _OPENAI_COMPAT_PROVIDERS:
            yield from self._stream_openai(
                client, system, messages, temperature, max_tokens, attachments
            )
        elif self.provider == "google":
            yield from self._stream_google(
                client, system, messages, temperature, max_tokens, attachments
            )
        elif self.provider == "cohere":
            resp = self.chat(
                system, messages, temperature, max_tokens, attachments=attachments
            )
            yield resp.content
        else:
            resp = self.chat(
                system, messages, temperature, max_tokens, attachments=attachments
            )
            yield resp.content

    def _retry(self, fn, max_retries: int = 3, base_delay: float = 2.0):
        """Retry with exponential backoff on transient errors."""
        for attempt in range(1, max_retries + 1):
            try:
                return fn()
            except Exception as e:
                err_str = str(e).lower()
                is_transient = any(w in err_str for w in (
                    "rate_limit", "rate limit", "429", "overloaded",
                    "529", "500", "502", "503", "connection", "timeout",
                ))
                if is_transient and attempt < max_retries:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "LLM call failed (attempt %d/%d): %s — retrying in %.1fs",
                        attempt, max_retries, e, delay,
                    )
                    time.sleep(delay)
                else:
                    raise

    def _chat_anthropic(
        self, client, system, messages, temperature, max_tokens, tools=None, attachments=None
    ):
        return self._retry(
            lambda: self._call_anthropic(
                client, system, messages, temperature, max_tokens, tools, attachments
            )
        )

    def _call_anthropic(
        self, client, system, messages, temperature, max_tokens, tools=None, attachments=None
    ):
        if attachments:
            from tcm.models.multimodal import build_anthropic_messages

            formatted_messages = build_anthropic_messages(messages, attachments)
        else:
            formatted_messages = messages

        kwargs = dict(
            model=self.model,
            system=system,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if tools:
            kwargs["tools"] = tools
        response = client.messages.create(**kwargs)
        if not response.content:
            content_text = ""
        else:
            text_parts = [b.text for b in response.content if hasattr(b, "text")]
            content_text = "\n".join(text_parts) if text_parts else ""
        return LLMResponse(
            content=content_text,
            model=self.model,
            usage={"input": response.usage.input_tokens, "output": response.usage.output_tokens},
            raw=response,
            content_blocks=list(response.content) if response.content else [],
        )

    def _stream_anthropic(
        self, client, system, messages, temperature, max_tokens, attachments=None
    ):
        """Stream from Anthropic API, yielding text deltas."""
        if attachments:
            from tcm.models.multimodal import build_anthropic_messages

            formatted_messages = build_anthropic_messages(messages, attachments)
        else:
            formatted_messages = messages

        with client.messages.stream(
            model=self.model,
            system=system,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ) as stream:
            try:
                for text in stream.text_stream:
                    yield text
            finally:
                try:
                    response = stream.get_final_message()
                    usage = {
                        "input": response.usage.input_tokens,
                        "output": response.usage.output_tokens,
                    }
                    self.usage.record(self.model, usage)
                except Exception:
                    pass

    def _chat_openai(self, client, system, messages, temperature, max_tokens, attachments=None):
        return self._retry(
            lambda: self._call_openai(
                client, system, messages, temperature, max_tokens, attachments
            )
        )

    def _chat_google(self, client, system, messages, temperature, max_tokens, attachments=None):
        return self._retry(
            lambda: self._call_google(
                client, system, messages, temperature, max_tokens, attachments
            )
        )

    def _call_google(self, client, system, messages, temperature, max_tokens, attachments=None):
        from google.genai import types as genai_types

        if attachments:
            from tcm.models.multimodal import build_google_contents

            contents = build_google_contents(system, messages, attachments)
        else:
            contents = []
            if system:
                contents.append(genai_types.Content(
                    role="user",
                    parts=[genai_types.Part(text=f"[System instructions]\n{system}")],
                ))
                contents.append(genai_types.Content(
                    role="model",
                    parts=[genai_types.Part(text="Understood. I will follow those instructions.")],
                ))
            for m in messages:
                role = m.get("role", "user")
                api_role = "model" if role == "assistant" else "user"
                contents.append(genai_types.Content(
                    role=api_role,
                    parts=[genai_types.Part(text=m.get("content", ""))],
                ))
        config = genai_types.GenerateContentConfig(
            temperature=float(temperature),
            max_output_tokens=int(max_tokens),
        )
        response = client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )
        text = response.text or ""
        usage = None
        meta = getattr(response, "usage_metadata", None)
        if meta:
            usage = {
                "input": getattr(meta, "prompt_token_count", 0),
                "output": getattr(meta, "candidates_token_count", 0),
            }
        return LLMResponse(content=text, model=self.model, usage=usage, raw=response)

    def _stream_google(self, client, system, messages, temperature, max_tokens, attachments=None):
        from google.genai import types as genai_types

        if attachments:
            from tcm.models.multimodal import build_google_contents

            contents = build_google_contents(system, messages, attachments)
        else:
            contents = []
            if system:
                contents.append(genai_types.Content(
                    role="user",
                    parts=[genai_types.Part(text=f"[System instructions]\n{system}")],
                ))
                contents.append(genai_types.Content(
                    role="model",
                    parts=[genai_types.Part(text="Understood. I will follow those instructions.")],
                ))
            for m in messages:
                role = m.get("role", "user")
                api_role = "model" if role == "assistant" else "user"
                contents.append(genai_types.Content(
                    role=api_role,
                    parts=[genai_types.Part(text=m.get("content", ""))],
                ))
        config = genai_types.GenerateContentConfig(
            temperature=float(temperature),
            max_output_tokens=int(max_tokens),
        )
        for chunk in client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=config,
        ):
            txt = chunk.text
            if txt:
                yield txt

    def _chat_cohere(self, client, system, messages, temperature, max_tokens, attachments=None):
        return self._retry(
            lambda: self._call_cohere(
                client, system, messages, temperature, max_tokens, attachments
            )
        )

    def _call_cohere(self, client, system, messages, temperature, max_tokens, attachments=None):
        parts = [f"[system]\n{system}"] if system else []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            parts.append(f"[{role}]\n{content}")
        if attachments:
            from tcm.models.multimodal import load_attachment

            for raw_att in attachments:
                att = load_attachment(raw_att)
                parts.append(
                    f"[attachment: {att.filename or att.kind} ({att.mime_type}, "
                    f"{att.size_bytes()} bytes)]"
                )
        prompt = "\n\n".join(parts)
        resp = client.chat(
            model=self.model,
            message=prompt,
            temperature=float(temperature),
            max_tokens=int(max_tokens),
        )
        text = getattr(resp, "text", None) or getattr(resp, "message", None) or ""
        usage = None
        try:
            tok = getattr(resp, "meta", {}).get("billed_units", {})
            usage = {"input": tok.get("input_tokens", 0), "output": tok.get("output_tokens", 0)}
        except Exception:
            pass
        return LLMResponse(content=text, model=self.model, usage=usage, raw=resp)

    def _call_openai(self, client, system, messages, temperature, max_tokens, attachments=None):
        # Normalize temperature for OpenAI-compatible providers
        # Kimi (Moonshot) only accepts temperature=1 for some models
        if self.provider == "kimi":
            temperature = 1.0
        if attachments:
            from tcm.models.multimodal import build_openai_messages

            oai_messages = build_openai_messages(system, messages, attachments)
        else:
            oai_messages = [{"role": "system", "content": system}] + messages

        wire_model = self._wire_model_id()
        response = client.chat.completions.create(
            model=wire_model,
            messages=oai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        usage_data = {}
        if response.usage:
            usage_data = {
                "input": response.usage.prompt_tokens,
                "output": response.usage.completion_tokens,
            }
        return LLMResponse(
            content=(getattr(choice, "message", None) and (choice.message.content or "")) or "",
            model=self.model,
            usage=usage_data,
            raw=response,
        )

    def _stream_openai(self, client, system, messages, temperature, max_tokens, attachments=None):
        """Stream from OpenAI-compatible APIs, yielding text deltas."""
        if self.provider == "kimi":
            temperature = 1.0
        if attachments:
            from tcm.models.multimodal import build_openai_messages

            oai_messages = build_openai_messages(system, messages, attachments)
        else:
            oai_messages = [{"role": "system", "content": system}] + messages

        wire_model = self._wire_model_id()
        stream = client.chat.completions.create(
            model=wire_model,
            messages=oai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            try:
                if getattr(chunk, "choices", None) and chunk.choices:
                    delta = getattr(chunk.choices[0], "delta", None)
                    if delta and getattr(delta, "content", None):
                        yield delta.content
            except Exception:
                continue
