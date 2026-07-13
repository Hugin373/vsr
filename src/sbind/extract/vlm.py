"""Generic HF vision-language-model wrapper with named hook sites. [GPU]

This is M4's `extract/` arriving early, because M3's Kang reproduction needs it. It is built
to be EXTENDED by M4 (more sites, mask-pooling, caching), not thrown away:

  * model loading is config-driven (any HF checkpoint of a supported architecture);
  * the LM decoder-layer list is LOCATED, not hardcoded per model, so a new checkpoint of the
    same family is a config change (CLAUDE.md hard rule);
  * one forward pass can simultaneously CAPTURE activations and APPLY interventions
    (patch / add), which is exactly what activation patching and steering need.

Sites (M3 uses the LM residual stream; M4 adds enc_out / proj_out):
  ``lm_L{k}``   residual stream at the output of LM decoder layer k.

Everything here is torch/GPU. Probing and analysis must run off cached tensors on a laptop.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import torch

from ..utils.logging import get_logger

log = get_logger("sbind.extract.vlm")


@dataclass
class Edit:
    """One activation intervention, applied during the forward pass.

    layer:    LM decoder layer index whose OUTPUT is edited.
    positions: token positions (into the sequence) to edit.
    vector:   [hidden] tensor.
    mode:     'add'     -> x[p] += vector                    (steering)
              'replace' -> x[p]  = vector                    (activation patching)
    """

    layer: int
    positions: Sequence[int]
    vector: torch.Tensor
    mode: str = "add"


@dataclass
class VLM:
    """A loaded VLM plus the hook machinery. Construct via ``load_vlm``."""

    name: str
    model: Any
    processor: Any
    layers: Any  # the nn.ModuleList of LM decoder layers
    dtype: torch.dtype
    device: str
    _captured: dict[int, torch.Tensor] = field(default_factory=dict)

    @property
    def n_layers(self) -> int:
        return len(self.layers)

    # --- prompting -------------------------------------------------------------------

    def build_inputs(self, image, prompt: str) -> dict:
        """Chat-template a single-image prompt into model inputs on the right device."""
        messages = [
            {
                "role": "user",
                "content": [{"type": "image"}, {"type": "text", "text": prompt}],
            }
        ]
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.processor(images=image, text=text, return_tensors="pt")
        return {k: (v.to(self.device) if hasattr(v, "to") else v) for k, v in inputs.items()}

    def token_ids(self, inputs: dict) -> list[int]:
        return inputs["input_ids"][0].tolist()

    def find_word_positions(self, inputs: dict, word: str) -> list[int]:
        """Token positions of ``word`` in the prompt (the LAST subword token of the word).

        Kang bind spatial IDs to the object's WORD token; for a multi-token word the paper
        uses the final token, which is the one that carries the aggregated word representation
        under causal attention. Tokenizers differ, so we decode-and-match rather than assume a
        single-token word.
        """
        tok = self.processor.tokenizer
        ids = self.token_ids(inputs)
        # decode each token, find the contiguous run whose concatenation contains `word`
        pieces = [tok.decode([i]) for i in ids]
        target = word.strip().lower()
        hits: list[int] = []
        for start in range(len(pieces)):
            acc = ""
            for end in range(start, min(start + 8, len(pieces))):
                acc += pieces[end]
                if target in acc.strip().lower():
                    hits.append(end)  # LAST subword token of the match
                    break
                if len(acc.strip()) > len(target) + 4:
                    break
        if not hits:
            raise ValueError(f"word {word!r} not found in the tokenized prompt")
        return hits

    # --- forward with capture + intervention ------------------------------------------

    def _hook(self, layer_idx: int, capture: bool, edits: list[Edit]):
        def fn(_module, _args, output):
            # decoder layers return a tuple (hidden_states, ...)
            hs = output[0] if isinstance(output, tuple) else output
            for e in edits:
                if e.layer != layer_idx:
                    continue
                v = e.vector.to(hs.dtype).to(hs.device)
                for p in e.positions:
                    if e.mode == "add":
                        hs[:, p, :] = hs[:, p, :] + v
                    elif e.mode == "replace":
                        hs[:, p, :] = v
                    else:
                        raise ValueError(f"unknown edit mode {e.mode!r}")
            if capture:
                self._captured[layer_idx] = hs.detach().float().cpu()
            if isinstance(output, tuple):
                return (hs, *output[1:])
            return hs

        return fn

    @torch.no_grad()
    def forward(
        self,
        inputs: dict,
        capture_layers: Sequence[int] | None = None,
        edits: Sequence[Edit] | None = None,
    ) -> tuple[torch.Tensor, dict[int, torch.Tensor]]:
        """One forward pass. Returns (next-token logits, {layer: [1, seq, hidden] activations}).

        Capture and intervention happen in the SAME pass, so a steered run reports the
        activations it actually produced.
        """
        self._captured = {}
        edits = list(edits or [])
        cap = set(capture_layers or [])
        touched = cap | {e.layer for e in edits}

        handles = []
        for idx in sorted(touched):
            h = self.layers[idx].register_forward_hook(
                self._hook(idx, capture=idx in cap, edits=edits)
            )
            handles.append(h)
        try:
            out = self.model(**inputs)
        finally:
            for h in handles:
                h.remove()

        logits = out.logits[0, -1, :].float().cpu()  # next-token distribution
        return logits, dict(self._captured)

    # --- reading a belief off the model -----------------------------------------------

    def option_logprobs(self, logits: torch.Tensor, options: Sequence[str]) -> dict[str, float]:
        """Log-probs of each option's FIRST token, renormalised over the option set.

        This is how a binary spatial "belief" is read out: P("left") vs P("right"). Comparing
        first-token probabilities is valid here only because the options are single distinct
        words — assert that rather than assume it.
        """
        tok = self.processor.tokenizer
        logprobs = torch.log_softmax(logits, dim=-1)
        out: dict[str, float] = {}
        for o in options:
            # leading space: the option follows "... is to the" in the generation position
            ids = tok.encode(f" {o}", add_special_tokens=False) or tok.encode(
                o, add_special_tokens=False
            )
            out[o] = float(logprobs[ids[0]])
        return out


def _find_decoder_layers(model) -> Any:
    """Locate the LM decoder-layer ModuleList without hardcoding a per-model path.

    HF moves these around between versions and architectures (LLaVA:
    ``language_model.model.layers``; Qwen2.5-VL: ``model.language_model.layers``; InternVL:
    ``language_model.model.layers``). Searching for the deepest ModuleList of decoder blocks
    is version-proof, and it fails LOUDLY rather than silently hooking the wrong thing.
    """
    candidates = []
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.ModuleList) and len(module) >= 8:
            # a decoder-layer list: its children have self_attn + mlp
            child = module[0]
            if hasattr(child, "self_attn") and hasattr(child, "mlp"):
                candidates.append((name, module))
    if not candidates:
        raise RuntimeError(
            f"could not locate the LM decoder layers in {type(model).__name__}. "
            f"Add an explicit path for this architecture rather than guessing."
        )
    # the LANGUAGE model is the longest such list (vision towers are shallower)
    name, layers = max(candidates, key=lambda kv: len(kv[1]))
    log.info("decoder layers: %s (%d layers)", name, len(layers))
    return layers


def load_vlm(checkpoint: str, dtype: str = "bfloat16", device: str = "cuda") -> VLM:
    """Load any HF VLM checkpoint. Call claim_gpu() BEFORE this — it initialises CUDA."""
    from transformers import AutoModelForVision2Seq, AutoProcessor

    torch_dtype = getattr(torch, dtype)
    log.info("loading %s (%s)", checkpoint, dtype)
    processor = AutoProcessor.from_pretrained(checkpoint, trust_remote_code=True)
    model = AutoModelForVision2Seq.from_pretrained(
        checkpoint, torch_dtype=torch_dtype, trust_remote_code=True
    ).to(device)
    model.eval()
    return VLM(
        name=checkpoint,
        model=model,
        processor=processor,
        layers=_find_decoder_layers(model),
        dtype=torch_dtype,
        device=device,
    )
