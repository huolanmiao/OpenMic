"""Runtime patch for ChatTTS GPT cache length guard.

This stays inside the repo so users of this codebase get the fix without
needing to modify site-packages. It adds a safety check to avoid negative
length in attention mask narrowing when max_cache_length is zero/invalid.
"""
from __future__ import annotations

import torch
from typing import Optional, Tuple
from transformers.cache_utils import Cache

try:
    import ChatTTS
    from ChatTTS.model.gpt import GPT
except Exception as exc:  # pragma: no cover - patch is a best-effort helper
    ChatTTS = None  # type: ignore
    GPT = None  # type: ignore
    _import_error = exc
else:
    _import_error = None


_PATCH_FLAG = "_openmic_cache_guard_installed"


def _patched_prepare_generation_inputs(
    self: "GPT",
    input_ids: torch.Tensor,
    past_key_values: Optional[Tuple[Tuple[torch.FloatTensor]]] = None,
    attention_mask: Optional[torch.Tensor] = None,
    inputs_embeds: Optional[torch.Tensor] = None,
    cache_position: Optional[torch.Tensor] = None,
    position_ids: Optional[torch.Tensor] = None,
    use_cache: bool = True,
):
    # Largely mirrors the upstream implementation, but guards on max_cache_length > 0
    # before calling narrow, preventing RuntimeError: length must be non-negative.
    has_static_cache = False
    if past_key_values is None:
        if hasattr(self.gpt.layers[0], "self_attn"):
            past_key_values = getattr(self.gpt.layers[0].self_attn, "past_key_value", None)
        has_static_cache = past_key_values is not None

    past_length = 0
    if past_key_values is not None:
        if isinstance(past_key_values, Cache):
            past_length = int(cache_position[0]) if cache_position is not None else past_key_values.get_seq_length()
            try:
                max_cache_length = past_key_values.get_max_cache_shape()
            except Exception:
                max_cache_length = past_key_values.get_max_length()
            cache_length = past_length if max_cache_length is None else min(max_cache_length, past_length)
        else:
            cache_length = past_length = past_key_values[0][0].shape[2]
            max_cache_length = None

        if attention_mask is not None and attention_mask.shape[1] > input_ids.shape[1]:
            start = attention_mask.shape[1] - past_length
            input_ids = input_ids.narrow(1, -start, start)
        elif past_length < input_ids.shape[1]:
            input_ids = input_ids.narrow(1, past_length, input_ids.size(1) - past_length)

        if (
            max_cache_length is not None
            and max_cache_length > 0
            and attention_mask is not None
            and cache_length + input_ids.shape[1] > max_cache_length
        ):
            attention_mask = attention_mask.narrow(1, -max_cache_length, max_cache_length)

    if attention_mask is not None and position_ids is None:
        position_ids = attention_mask.long().cumsum(-1) - 1
        position_ids.masked_fill_(attention_mask.eq(0), 1)
        if past_key_values:
            position_ids = position_ids.narrow(1, -input_ids.shape[1], input_ids.shape[1])

    input_length = position_ids.shape[-1] if position_ids is not None else input_ids.shape[-1]
    if cache_position is None:
        cache_position = torch.arange(past_length, past_length + input_length, device=input_ids.device)
    else:
        cache_position = cache_position.narrow(0, -input_length, input_length)

    if has_static_cache:
        past_key_values = None

    model_inputs = GPT._GenerationInputs(
        position_ids=position_ids,
        cache_position=cache_position,
        use_cache=use_cache,
    )

    if inputs_embeds is not None and past_key_values is None:
        model_inputs.inputs_embeds = inputs_embeds
    else:
        model_inputs.input_ids = input_ids.contiguous()

    model_inputs.past_key_values = past_key_values
    model_inputs.attention_mask = attention_mask
    return model_inputs


def apply_chattts_patch() -> None:
    """Install the cache-length guard patch if ChatTTS is available."""
    if ChatTTS is None or GPT is None:
        return
    if getattr(GPT, _PATCH_FLAG, False):
        return
    GPT._prepare_generation_inputs = _patched_prepare_generation_inputs  # type: ignore[attr-defined]
    setattr(GPT, _PATCH_FLAG, True)


__all__ = ["apply_chattts_patch"]
