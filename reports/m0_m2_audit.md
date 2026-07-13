# Retro-audit of M0 / M1 / M2 — 2026-07-14 (before opening M3)

*Second full audit, run after M1 and M2 were both closed "all checks green". Method: validate the
OUTPUT, never the fact that the pipeline ran. Full scans over every item; independent
re-derivation rather than re-use of the code that produced the data; every documented claim
re-measured against the artefact.*

**Headline: the DATA is clean. The CODE and the DOCS are not.**

Every count, id, file and answer-key in M1/M2 checks out under full scan. But six real code
bugs survive, two of which produce wrong data *today*, and five documented constants/claims are
false. Consistent with this project's history, none of them make anything fail loudly.

---

## 1. Verified CORRECT (measured, not assumed)

| Claim | How it was checked | Result |
|---|---|---|
| M2 count integrity, all 6 adapters | source records counted straight from pkl/parquet/json vs loaded items | **0 dropped** (whatsup 820, cvbench 2638, mindcube 1050/21154/10000, causalspatial 1541, revsi 4568/6158/6616, depthcues 19235) |
| M2 id uniqueness | full scan, every adapter, every split | **0 duplicates** |
| M2 media existence | every referenced image/video stat'd | **0 missing** |
| M2 MCQ scoreability | every MCQ answer resolved against its options | **0 unscoreable** |
| M2 extracted-image collisions | cvbench + causalspatial materialized paths | **0 shared files** (the 949-vs-1541 overwrite bug is genuinely fixed) |
| What'sUp "first option is correct" | re-derived from the *filename*-encoded relation, 718 matched records | **0 disagreements** — the upstream convention is real |
| M1 determinism | re-rendered 24 images from identical (config, seed) and byte-compared | annotations + masks **byte-identical**; 22/24 images byte-identical; residual **2 subpixels of 1.57 M at max delta 1/255** — the documented claim is honest and not overclaimed |
| M1 geometry | camera + projection re-implemented from scratch (not `stimuli.geometry`) | `pos_cam`, `depth_m`, `elevation_px`, `nearest_surface_m`: **0.0 error, worst case, over 1000 objects** |
| M1 masks | recomputed bbox / retinal_size / mask_area from the 1000 PNGs | **0.0 error**; masks vs analytic silhouettes worst IoU 0.989, never inflated → the ID-pass bleed bug is definitively gone |
| M1 frame-clipping / occlusion | both catastrophic-if-present, neither previously checked | **0 masks touch the border, 0 pairs overlap** |
| M1 area-congruence "structural" claim | area constants re-derived from the rendered images | true worst-case required ratio **1.1557** (config claims 1.158); min sampled **1.180** → **+2.1% headroom**. Genuinely structural, not luck |
| M1 balance | full scan | closer-object 250/250, ordinal 250/250, 0 identical pairs |
| M1 image↔annotation binding | mean RGB inside each mask vs annotated colour, all 1000 objects | **0 mismatches** |
| Schemas | all 500 annotations round-tripped through the frozen M0 dataclasses | **0 failures** |

## 2. BUGS — produce wrong data today

**B1 — CausalSpatial mislabels a real answer as an abstain (HIGH).**
`causalspatial.py:109` trusts upstream's `not_sure` column, which is the constant `'C'` for all
189 occlusion rows. But occlusion has two question shapes: 135 rows are genuine
`Yes / No / Not Sure` (3 options), and **54 rows have four *semantic* options** with no abstain at
all (`A. never occluded / B. initially occluded then revealed / C. initially not occluded, then
occluded, then revealed / D. …`). The adapter marks option **C** as the abstain on all 54 — and
**for 11 of them C is the GOLD answer**. Any scorer honouring the adapter's own documented
contract ("treat `not_sure_letter` as a non-answer, not a wrong answer") discards the correct
answer on 11 items and mis-handles C on 54. Nothing throws.
*Root cause: trusted upstream metadata — the same class as the non-unique upstream `id`.*
*Invariant that catches it: the option named by `not_sure` must read like an abstain option.*

**B2 — MindCube silently falls back to tinybench, and mislabels the result (HIGH).**
`mindcube.py:53` — `SPLITS.get(split, SPLITS["tinybench"])`. Measured:
`load("mindcube", cfg, split="val")` returns **1,050 tinybench items stamped `meta.split="val"`**.
Any typo silently loads the dev split and labels it as the requested one, propagating into every
downstream join. This **defeats the §2.5 "split is a parameter" rule that commit `b5db0fd`
claims to enforce in code**. Should be `SPLITS[split]` → KeyError.
Related: MindCube's split cannot be set from a config at all (kwarg only), unlike ReVSI — so
"state the split in the experiment config" is literally not implementable for it.

## 3. BUGS — real, currently latent or loud-but-broken

**B3 — What'sUp's gold answer is at position A for 100% of items, and nothing shuffles it.**
The convention is correct (verified above), but `meta.options` hands a scorer an ordered list
whose first entry is *always* the right one. A model with an A-bias scores 100%, and **the
qualitative positive control would pass for the wrong reason.** Must apply a seeded permutation
and record the shuffled `answer_index` before any eval. Load-bearing for M3.

**B4 — ReVSI `frame_budget='all'` is dead.** `revsi.py:73` does `int(row["num_frames"])`, but in
`all_frame/` that column is the **string `'all'`** (it is a budget *label*, not a count) →
`ValueError`. `'all'` is advertised in `BUDGETS`, the docstring, and `configs/datasets.yaml`. One
of the four documented settings of the dataset *whose entire thesis is budget-sensitivity* does
not load. (16/32/64 verified correct: every clip really does contain exactly budget-many frames.)

**B5 — `decode_frames` silently drops frames it cannot find** (`base.py:208`). Asking a 32-frame
clip for `[0,1,2,999]` returns 3 images — no exception, no count, no log. Already mislabels output
in `dataset_contact_sheet.py` (`zip(..., strict=False)` pairs images against *requested* indices,
so a dropped frame shifts every caption). Latent today.

**B6 — CausalSpatial truncated option list.** `Collision_Level_2_31` has upstream-corrupted text
(the `E. R` was eaten), so the strict A,B,C-run parser stops at D: `meta.options` has 4 entries,
the last a garbage blob, and `not_sure_letter='F'` names an option that does not exist. Gold is
`'A'` so every existing test passes. Chance level (1/len(options)) is wrong. No invariant ties
`len(options)` to the `not_sure` letter — which is the free cross-check available here.

**B7 — Uncounted silent `continue`s** in `whatsup.py:70,75` and `revsi.py:72`. All three fire
**0 times today** (verified), but they violate the rule that produced the worst M2 bug: count
skips, log them, raise if a subset yields zero. The only thing standing between a layout change
and a silently-empty subset is a hardcoded count list in the test suite.

## 4. M0 infra — the previous retro-audit's fix is incomplete

**B8 — `config.py` `strict_env` still has two holes**, i.e. the exact "forgotten export" bug it was
added to prevent can still happen two ways:
- `DATA_ROOT=""` (empty but *set*) → `root` resolves to **`/external`**, no raise.
- `$NOPE/external` (unbraced) → stays the literal string `'$NOPE/external'`, no raise
  (`_UNRESOLVED` only matches the `${...}` form, though the docstring advertises `$VAR`).

**B9 — `base.py:88` fabricates an absolute path**: `os.environ.get("DATA_ROOT","") + "/external"`
→ `dataset_root({}, "cvbench")` returns `/external/cvbench`. Should raise. (Only occurrence.)

**B10 — the GPU guard's foreign-compute-process check does not exist.** `ComputeApp` and
`--query-compute-apps` are declared in `gpu.py` with **zero call sites**; the guard is
memory-threshold-only. CLAUDE.md explicitly promises "*or a foreign compute process is
present*". **M3 is the first GPU milestone — this matters now.**

**B11 — `seeding.py:21` sets `PYTHONHASHSEED` after interpreter start**, which is a no-op.
`torch.use_deterministic_algorithms()` is also never set (only `cudnn.deterministic`), so M4's
CUDA extraction can be nondeterministic while appearing fully seeded.

**B12 — the test suite ERRORS (35 errors) rather than skips when `$DATA_ROOT` is unset**, and
`DATA_ROOT`/`HF_HOME` are exported in **no shell profile** — so a fresh shell is the broken
state. PROJECT_MEMORY claims the suite "stays green on a laptop"; it only does if the var is set
to a *nonexistent* path. M0's acceptance criterion ("pytest green on a GPU-less machine") is not
met in a clean environment.

## 5. M1 — the data is right, but three documented claims about it are wrong

**B13 — `height_ratio_threshold: 1.016` is MEAN-derived.** This is *the exact rule-7 error the
project already fixed for area*, still live for height. Re-derived per-role from the rendered
images, the height constant swings far more than the config's single means (cube 383.6–449.9,
cylinder 383.4–430.8, sphere 399.0–411.8 vs the claimed 409.3 / 410.3 / 405.3), giving a true
worst-case required depth ratio of **1.0878, not 1.016**. Harmless *now* (the area floor of 1.18
dominates), but the config states these constants exist "for reuse by M4's CONFLICT designs" —
sizing a height inversion off 409.3 will be wrong by up to ±10%, and anyone lowering
`min_depth_ratio` below 1.088 trusting "height needs only 1.016" silently inverts the cue.

**B14 — `size_calibration.yaml` claims `_spread_px: 0.0`** (all three shapes render 90.0 px). In
the produced set that is false by up to **12.8%**: under the ~15.8° camera tilt a cube's/cylinder's
silhouette *height* grows as it moves low/near in frame (its top face comes into view), so its
height constant swings ±10% with image position while a sphere's swings ±1.5%. The calibration is
exact only at the single point it was measured at. Consequence: **shape partially predicts
apparent height** — a mild probe confound.

**B15 — category is not balanced against the near/far role → a 55.1% semantic prior.**
`balanced_on` covers only `closer_object` and `near_depth_bin`. Realized counts: sphere near
148/far 182, cube near 168/far 147, cylinder near 184/far 171 (χ² p = 0.068). The best
**shape-only constant strategy** scores **190/345 = 55.1%** on mixed-category pairs
("the cube is closer" wins 59.6% of cube-vs-sphere pairs). A language-only model gets 55% free on
"which is closer?", and a *z-probe can read depth off object identity* — in the very set whose
purpose is to decorrelate semantics from geometry. **This directly threatens M3.2's
interpretation** (semantics ≫ metric is the expected pattern; a semantics→depth leak inflates z).
Fix: add category × near/far role to `balanced_on` and re-render (~22 min).

**B16 — `scripts/validate_stimuli.py` would report ALL GREEN under several catastrophic failures.**
It never opens a single mask or image file (it validates the JSON against itself); it has no
count, id-uniqueness, or image-content-duplication check (the exact class that hit M2); no
frame-clipping and no occlusion check (both corrupt `retinal_size_px`/`mask_area_px`, the very
quantities the congruence checks read); and its geometry check calls
`sbind.stimuli.geometry.project` — **the same function that generated the annotations**, so a
wrong camera convention is invisible to it. It also counts violations but measures no margins,
which is precisely why B13 survived. Separately, none of the set-level invariants are in pytest,
so `uv run pytest` cannot catch a stimulus-construction regression.

## 6. Docs that no longer match reality

- **PROJECT_MEMORY records `depthcues 4373 (test)`. The truth is 19,235** — and 19,235 − 14,862
  (the occlusion subset) = **4,373**, i.e. the doc preserves the *pre-fix, broken* count as the
  state reached. The code and tests already carry 19,235.
- **Disk: documented 20 GB, actual 23 GB.** `cvbench` 394 M → **782 M** and `causalspatial`
  2.4 G → **4.8 G**, because both `materialize_image` their parquet-embedded images on first
  load. Worth stating plainly: **loading a dataset mutates `$DATA_ROOT`.**
- **CLAUDE.md and PROJECT_MEMORY both say the git remote is "deferred / local-only" and that the
  "server is never the only copy" rule is UNMET.** An `origin` exists
  (`git@github.com:Hugin373/vsr.git`) and `HEAD` is pushed (0 commits ahead). The rule is met.
- **CLAUDE.md's "a sphere is exactly as tall as it is wide" invariant is only valid on-axis.** At
  the eccentricities in this set a perspective-projected sphere is an *ellipse*: measured w/h
  ∈ [0.984, 1.037], and the exact perspective ellipse predicts [0.984, 1.040]. As literally
  written the invariant now yields a **false positive of up to 3.9%**. The correct general form is
  *measured == analytic*.
