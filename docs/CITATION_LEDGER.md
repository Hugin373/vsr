# Citation Ledger — Lab Presentation (verified 2026-07-16 against arXiv full texts)

Every number on a slide traces to a row here. Corrections found during verification are marked ⚠.

## P1 Kang et al. 2601.12626 (ICLR 2026) — Linear Mechanisms for Spatiotemporal Reasoning in VLMs
- Spatial IDs: mean-centered activation differences, 4×4 grid ✓
- 11 VLMs, ≤14B ✓
- Rank-3 fit of encoder positional basis, R² ≳ 0.85 (LLaVA 0.854, LLaMA3.2V 0.869, Qwen2.5VL 0.903) ✓
- Steering: median 64.4% (Fig.2 caption) / 64.6% (§3 text) vs 29.5% noise ⚠ quote as "≈64.5% (median)" or the range; above-chance +43.6%
- Patching: image patches early, object-word tokens middle band, text late ✓
- Faithfulness (LLaVA & LLaMA): wrong IDs ↔ wrong answers; linguistic stage faithful ✓
- LLaVA1.5-7B: above≈front, below≈behind (word embeddings nearly identical) ⚠ pairing direction
- Fig 1: html/2601.12626v1/images/realistic_no_fm_full_process_with_grids_v2.drawio.png
- Fig 2: html/2601.12626v1/images/all_models_syringe_gemma_sandy.drawio.png

## P2 DepthCues 2411.17385 (CVPR 2025)
- Six cues: elevation, light & shadow, occlusion, perspective, size, texture gradient ✓
- 20 pre-trained vision models ✓
- Correlation with depth estimation: qualitative only ⚠ no single ρ in text — do not print a number
- Fig 1: html/2411.17385v2/_page_0_Figure_9.jpeg (v1: x1.png); Fig 2: _page_2_Figure_0.jpeg; Fig 4: _page_6_Figure_5.jpeg

## P3 Wang & Gao 2605.07148 — Latent Representation of 3D Scene Topology
- SynSpat3D: 1,000 scenes, 5,000 video-question pairs ✓
- Qwen2.5-VL-7B + InternVL3-8B (LLaVA-OV-7B in Fig.7 curves) ✓
- x R² = −0.09 ± 0.01, z R² = +0.28 ± 0.02 (L17, Qwen) ✓ ⚠ their Fig.4 prints "+0.09" for x — appendix confirms negative
- 3D-distance RSA ρ = +0.01 ± 0.01 ✓
- Shape = 1.00 ⚠ it is k-NN classification ACCURACY, not R²
- Topological subspace at middle layers post cross-scene residualization; Dirichlet vs 1,000-permutation null ✓
- LoRA 500 steps: Qwen +6.3 VSI-Bench (29.3→35.6), +7.0 MindCube (41.3→48.3) vs naive LoRA ⚠ attribute to Qwen; InternVL +5.7/+6.5; their headline "up to 12.1%"
- Steering: 54/60 = 90.0% sign-correct on PROBE readout (v⊥ 48.3% ≈ chance); never on verbalized answers ✓
- Fig 2: html/2605.07148v1/x2.png; Fig 4: x4.png

## P4 Ill-Posed by Design 2606.24335 (TAU + IBM)
- Six channels: category priors, target pixels, target identity, local context, apparent image size, global scene geometry ✓
- Metric VQA: 10,813 queries; 331 tape-measured in-the-wild on 70 photos; 12 VLMs (3–397B) ✓
- Identity most load-bearing (8/12 models; largest −20.3 pp); apparent size direction-inconsistent (expected ratio 2.33, median paired ratio 1.00 for all 12); geometry: only 1/12 reacts to lens distortion ✓
- Text-only frontier LLM beats every open VLM on in-the-wild split ✓
- LoRA: gains +11.6/+9.9/+2.1 pp without new apparent-size/perspective sensitivity ✓
- Fig 1: html/2606.24335v1/_page_1_Figure_2.jpeg; Fig 2: _page_5_Figure_0.jpeg

## P5 Cui et al. 2603.22278 v2 — Dual Mechanisms of Spatial Variable Binding
- Strips incl. background carry ordering; object-token-only patching fails ✓
- LM backup mechanism, middle layers ✓
- Amplification corrects 40.2–54.5% vs 9.6–13.1% random null ⚠ (not "10–13"); up to +22 pp ✓
- COCO-spatial 2,687 images ✓
- Two-ordering evaluation ✓ ⚠ "strict both-orders + 25% chance" NOT stated in paper — say "evaluated under both option orders"
- Fig 1: html/2603.22278v2/x1..x4.png + x5.jpg; Fig 7: figures_main/qwen_criss_cross_strips_squares_all_directions.png

## P6 Deccan AI 2605.20448 — Do VLMs Understand 3D Scenes or Just Catalogue Objects?
- 17 sites: ViT {0,6,12,18,23}, main merger + 3 deep-stack mergers, LM {0,4,8,12,16,20,24,27} ✓
- Model: Qwen3-VL-8B-Thinking ⚠ (say "-Thinking")
- Counterfactuals: T1 single-object removal, T2 multi-object removal, T3 transparency ✓
- Recovery ≈1.0 through ViT → collapses to 0.15–0.30 across merger stage → snaps back to 1.0 at LM L0 ✓ (163 failure cases)
- 3,034 human-curated samples ✓
- Attention finding: depth-correct region gets <5% of visual attention; "Attention Dispersed" explains 100% of failures ✓
- Fig 3: html/2605.20448v1/figures/fig_causal_tracing.png; Fig 1: figures/fig9_dgar_region_breakdown.png

## P7 Anchored, Not Graded 2606.06714 v2 — Slant-from-Texture
- Continuous slant; factorial 10 slant × 10 FOV × 2 curvature ✓
- 4 VLMs: Qwen2.5-VL(-3B), LLaVA-1.5-7B, PaliGemma-3B, Chameleon-7B ✓
- LM-input R²: 0.696 (Qwen2.5-VL-3B), 0.857 (LLaVA), 0.880 (PaliGemma) ⚠ low end 0.696 not 0.70
- Output anchors to 0°, ±25°, ±45°; blames representation-to-output interface; LM-internal tracing = declared future work ✓
- Fig 1: html/2606.06714v2/_page_1_Figure_2.jpeg; Fig 10: _page_11_Figure_2.jpeg

## P8 MindEdit-Bench 2607.00491
- Pure-depth 7.4% vs pure-lateral 18.0% ✓
- VLM task-wise mean 8–31% vs human majority-vote 81–97% ✓
- 120 private indoor scenes, three-photo smartphone triplets ✓
- Adjacent 45° bin 1.7× random; 180° reversals 0.6× ✓

## P9 ReVSI 2604.24300
- 381 scenes / 5,365 objects re-annotated (5 datasets) ✓
- Black videos, object size MRA: InternVL3.5-8B 50.3, -38B 48.6 ✓
- Spatial-MLLM dummy videos: 820k → 0.0/0.0/0.0; 135k → 0.2/0.9/0.0 ⚠ one cell 0.9%
- Counting: always "2" → 62% ("2" = 53% of GT) ✓
- SFT 135k→820k ≈ +3% ✓

## P10 CausalSpatial 2601.13304 ⚠ (ID corrected; was unlisted in our docs)
- Humans 84% vs GPT-5 54% ✓
- NSR 18.77% (Qwen3-4B-I) → 0.10% (Qwen3-30B-A3B-T), accuracy flat ✓
- Qwen3 plateau: 44.76 / 43.53 / 45.80% ⚠ range 43.5–45.8, not 44–46
- Paper taxonomy: Collision, Occlusion, Compatibility, TRAJECTORY ⚠ (no "physics"/"realworld" in the paper's taxonomy — those are repo folder names)

## Ours (internal, reports/m3_reproduction.md + PROJECT_MEMORY)
- Kang reproduction: patching profile exact; rank-3 R² 0.87 (LLaVA) / 0.84 (Qwen); steering 31.3% vs 0.0% noise (α=5), peak +43.3 above chance; dose-response monotone 10→23→31→43% (α 1→10)
- v0 leak: mask geometry alone x R²=0.942 (centroid alone 0.943), z 0.972; probes 0.997/0.990; shape-only strategy 55.1%→50.2% after balancing
- What'sUp-B: 204 front/behind items (102/102); CV-Bench 3D: Depth 600 + Distance 600, sources 400/400/400
