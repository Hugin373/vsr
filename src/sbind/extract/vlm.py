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
        """Token positions of ``word`` in the prompt (the LAST subword token of each match).

        Kang bind spatial IDs to the object's WORD token; for a multi-token word the paper
        uses the final token, which carries the aggregated word representation under causal
        attention.

        Matching is done on WHITESPACE-STRIPPED text with a char -> token index map, because
        naive concatenation of per-token `decode()` output is not reliable: the LLaMA tokenizer
        renders "fire hydrant" as pieces that concatenate to "firehydrant", so a literal
        substring search for the object name found nothing and every multi-word COCO category
        ("fire hydrant", "traffic light", "baseball glove") raised.
        """
        tok = self.processor.tokenizer
        ids = self.token_ids(inputs)

        norm_chars: list[str] = []
        owner: list[int] = []  # norm_chars[k] came from token owner[k]
        for t_idx, t_id in enumerate(ids):
            for ch in tok.decode([t_id]):
                if ch.isspace():
                    continue
                norm_chars.append(ch.lower())
                owner.append(t_idx)
        hay = "".join(norm_chars)
        needle = "".join(word.split()).lower()
        if not needle:
            raise ValueError("empty word")

        hits: list[int] = []
        start = hay.find(needle)
        while start != -1:
            hits.append(owner[start + len(needle) - 1])  # LAST token of the match
            start = hay.find(needle, start + 1)
        if not hits:
            raise ValueError(f"word {word!r} not found in the tokenized prompt")
        # de-duplicate while preserving order (overlapping matches can land on one token)
        seen: set[int] = set()
        return [h for h in hits if not (h in seen or seen.add(h))]

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

    def option_first_tokens(self, option: str) -> list[int]:
        """First contentful token ids for every SURFACE FORM of an option ("left"/"Left"/...).

        Two traps, both of which silently produced a meaningless belief:

        1. Not ``encode(" left")[0]``. The LLaMA tokenizer emits a standalone whitespace token
           (id 29871) for the leading space, so ``encode(" left")[0] == encode(" right")[0]``:
           both options scored the IDENTICAL logit and every belief came out exactly 0.5/0.5,
           even under a zero-ablation. Skip whitespace-only tokens.
        2. Not lowercase only. Asked "…left or right? Answer with one word.", LLaVA answers
           **"Left"/"Right"** — capitalised, carrying essentially all the mass — while
           " left"/" right" sit at logprob ≈ −11 (p ≈ 2e-5). Scoring the lowercase form alone
           was reading the far TAIL of the distribution, so the belief barely moved even when
           the token it depends on was ablated.

        So we marginalise over casing variants: P(option) = Σ_forms P(first token of form).
        """
        tok = self.processor.tokenizer
        variants = {option, option.lower(), option.capitalize(), option.upper()}
        ids: list[int] = []
        for v in variants:
            for enc in (tok.encode(f" {v}", add_special_tokens=False),
                        tok.encode(v, add_special_tokens=False)):
                for i in enc:
                    if tok.decode([i]).strip():
                        ids.append(i)
                        break
        if not ids:
            raise ValueError(f"option {option!r} tokenizes to whitespace only")
        return sorted(set(ids))

    def option_logprobs(self, logits: torch.Tensor, options: Sequence[str]) -> dict[str, float]:
        """Log-prob mass of each option, marginalised over its surface forms.

        Reading a belief off these is only valid if the options' token sets are DISJOINT.
        Asserted, not assumed — it was silently false (see ``option_first_tokens``).
        """
        by_opt = {o: self.option_first_tokens(o) for o in options}
        seen: set[int] = set()
        for o, ids in by_opt.items():
            clash = seen & set(ids)
            if clash:
                raise ValueError(
                    f"option {o!r} shares first-token(s) {clash} with another option — a "
                    f"belief read off them would be meaningless."
                )
            seen |= set(ids)
        logprobs = torch.log_softmax(logits, dim=-1)
        return {
            o: float(torch.logsumexp(logprobs[torch.tensor(ids)], dim=0))
            for o, ids in by_opt.items()
        }


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
    # transformers 5.x: AutoModelForVision2Seq was renamed AutoModelForImageTextToText.
    from transformers import AutoModelForImageTextToText, AutoProcessor

    torch_dtype = getattr(torch, dtype)
    log.info("loading %s (%s)", checkpoint, dtype)
    processor = AutoProcessor.from_pretrained(checkpoint, trust_remote_code=True)
    model = AutoModelForImageTextToText.from_pretrained(
        checkpoint, dtype=torch_dtype, trust_remote_code=True
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
