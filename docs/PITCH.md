# PITCH.md — canonical short pitch (vetted 2026-07-16; updated same day after review rounds 3–6, Design Revision 3)

*Every abstract, deck, or verbal explanation derives from THIS text — do not re-derive the
pitch from memory (compression re-introduces retracted overclaims; it has happened three times,
the third in an AI-built deck). Changes to this file require the same adversarial review as a
doc change (rule 13).*

## 日本語（応募・ポスター用 / GenGA形式・約390字）

**題目：視覚言語モデルは奥行きをどの段階まで保持し，利用しているのか**

- 視覚言語モデル（VLM）は粗い定性的な空間関係には概ね正答し，「どちらが近いか」といった順序判断も相関する手がかりの下では正答しうる一方，「何倍遠いか」等の連続的な奥行き量の推定は依然として大幅に弱い．
  - さらに，奥行き課題の成績は画像内の高さ・見かけの大きさ等の相関する2D手がかりに交絡されており，正答率だけでは内部に奥行き表現が存在することを示せない．
- 本研究では，VLM内部の奥行き情報について「符号化されているか」「下流から利用可能か」「因果的に使われているか」を区別して検証する分析枠組みを提案する．
  - 正確な幾何情報を持つ合成画像により，奥行きと2D手がかりを独立に操作する（要因計画・手がかり矛盾条件）．
  - 視覚エンコーダ出力から物体参照トークン，回答生成に至る事前指定した機能的段階ごとに線形プローブと因果的介入を適用し，奥行き情報が保持・変換され，回復困難あるいは利用不能となる段階を同定する．
- 本枠組みにより，VLMが奥行きをどの段階まで保持・利用しているかを診断可能にし，遮蔽・因果的空間推論など高次の空間理解研究の基盤を与える．

キーワード：視覚言語モデル／空間推論／プロービング／機構的解釈可能性

## English (3-paragraph pitch — externally reviewed version)

Before studying occlusion and causal spatial reasoning, we first need to establish what kind of
depth information VLMs internally represent, where that information is preserved or degraded,
and whether it is actually used by downstream computation. Prior work suggests that VLMs can
perform well on some coarse qualitative spatial relations, and ordinal near/far judgments are
often answerable when familiar cue correlations hold — while continuous depth-magnitude
estimates remain substantially weaker. Moreover, reported depth performance is often confounded
by correlated 2D cues, including vertical image position, apparent size, perspective, and
occlusion structure, so task accuracy alone does not establish a genuine metric depth
representation.

Existing remedies largely pursue two strategies. Fine-tuning can improve answer accuracy, but
such gains do not by themselves show that the model has acquired a better spatial
representation; some evidence suggests improvements may instead reflect changes in answer
priors or task-specific readout behavior. External depth or 3D injection can also improve
performance, but it addresses an augmentation problem rather than diagnosing what the base VLM
already represents.

Our hypothesis is that metric depth information may exist at some internal sites but become
degraded, improperly bound to objects, inaccessible to downstream components, or simply not
causally selected during reasoning. We therefore separate three questions — whether depth is
encoded, whether it remains accessible, and whether it is causally used — and (1) trace depth
information across five prespecified functional stages — continuous depth as the probe target,
ordinal ordering as the behavioral anchor — to identify where it is preserved, transformed, or
becomes less recoverable or unusable, and (2) disentangle metric depth from correlated 2D cues
using controlled factorial and cue-conflict stimuli.

## Framing rules distilled (from SIX external-review rounds; DR3 + addenda r2–r6)

- Depth is the TOPIC; metric targets are the INSTRUMENT — the most shortcut-RESISTANT measure
  (they resist single-cue solutions; they are NOT immune to priors — never "shortcut-proof").
- **Two-level variable, in every claim sentence:** CONTINUOUS depth (z; Δz/ratio) = the probe
  target; ORDINAL ordering = the behavioral anchor. Never interchange them. Ordinal is NOT
  "near floor" — it is variable under familiar cue correlations; continuous magnitude is the
  consistently weak level.
- Never presuppose presence: "IF internal depth exists but is unused, utilizing it beats
  external injection" — presence-and-location is the question, utilization is the payoff.
- Three-question spine for COMMUNICATION: encoded / accessible / causally used. Evidential
  GRADING is five rungs: linearly decodable ⊂ image-grounded decodable ⊂ causally ALTERABLE ⊂
  object-specific mediated use ⊂ task-relevant causal use. "Accessible" claims require
  intervention evidence — never probes alone.
- "Unavailable or unusable", never "lost/destroyed/dies/killed".
- Scope competence claims: "coarse qualitative relations", "current-generation models",
  "across several recent benchmarks" (never "everywhere"), "the studies reviewed here"
  (never "no study" / "nobody has").
- **No "first …" claims pre-result.** Safe form: "a stage-wise, trivial-feature-controlled
  protocol for tracing object-specific depth across five prespecified functional stages"
  (never "the full chain").
- **Deccan (2605.20448) and Anchored (2606.06714) motivate COMPETING LOCALIZATION HYPOTHESES —
  their results are strictly compatible (different variables/methods); never "a published
  disagreement" and never "we adjudicate".**
- "Selection-leak-controlled (with nuisance baselines)" — never bare "leak-controlled"; "leak"
  is reserved for the selection mechanism; text-side controls are nuisance baselines. The
  position-leak result is a CANDIDATE contribution (6-item promotion checklist).
- Cues are legitimate depth evidence, not shortcuts by definition — a shortcut is single-cue
  reliance that fails under decorrelation; the construct is cue-responsive vs cue-integrated.
- Height is one of a CUE BUNDLE (height, size, perspective, occlusion, priors).
- Fine-tuning critique stays qualified ("some evidence suggests…"; scoped to tested setups).
- External 3D = augmentation problem, not diagnosis problem (neutral, not dismissive).
- Kang: "localized spatial-ID influence to object-word tokens, which they interpret as binding";
  our reproduction: "key qualitative signatures partially reproduced; the absolute effect did
  not" — cross-study effect comparisons are DESCRIPTIVE only.
- Rendering "enforces exact factorial control at a scale natural data rarely provides" — never
  "only rendering can decorrelate"; synthetic ≠ automatically shortcut-free.
- Contribution = stage-wise diagnosis + foundation for occlusion/causal research (no fix promises).
- **Baseline decomposition (ruling 3, verbatim): "The primary incremental test conditions on selection-derived geometry and semantic priors, while preserving monocular cues as legitimate image evidence; conditioning on monocular cues is reported separately as an integration diagnostic, not used as the primary gate."**
