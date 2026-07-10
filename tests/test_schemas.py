"""Round-trip tests for the frozen §3 schemas (M0 acceptance)."""

from sbind.schemas import (
    BASE_SITES,
    POOL_OBJECT,
    POOL_STRIP,
    SITE_LM_TXT,
    SITE_LM_VIS,
    CacheMetaRow,
    Camera,
    ObjectAnnotation,
    PairRelation,
    ProbeResult,
    StimulusAnnotation,
    lm_site,
)
from sbind.utils.io import read_jsonl, write_jsonl


def _example_annotation() -> StimulusAnnotation:
    cam = Camera(
        K=[[500.0, 0.0, 320.0], [0.0, 500.0, 240.0], [0.0, 0.0, 1.0]],
        R=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        t=[0.0, 0.0, 0.0],
        height_m=1.5,
    )
    obj0 = ObjectAnnotation(
        name="red_cube",
        category="cube",
        size_m=0.3,
        pos_world=[1.0, 0.0, 2.1],
        pos_cam=[1.0, 0.0, 2.1],
        depth_m=2.1,
        bbox_px=[300.0, 220.0, 360.0, 280.0],
        retinal_size_px=88.2,
        elevation_px=312.0,
        mask="masks/set3_00142_obj0.png",
    )
    obj1 = ObjectAnnotation(
        name="blue_sphere",
        category="sphere",
        size_m=0.2,
        pos_world=[-0.5, 0.0, 3.9],
        pos_cam=[-0.5, 0.0, 3.9],
        depth_m=3.9,
        bbox_px=[120.0, 210.0, 160.0, 250.0],
        retinal_size_px=40.0,
        elevation_px=300.0,
        mask=None,
    )
    return StimulusAnnotation(
        id="set3_00142",
        image="images/set3_00142.png",
        camera=cam,
        objects=[obj0, obj1],
        factors={
            "depth_bin": 3,
            "elevation_condition": "conflict",
            "size_condition": "fixed_retinal",
        },
        pair_relations={
            "(0,1)": PairRelation(ordinal_depth="0_closer", dist_ratio=1.83, dist_m=1.2)
        },
    )


def test_stimulus_annotation_round_trip():
    ann = _example_annotation()
    restored = StimulusAnnotation.from_dict(ann.to_dict())
    assert restored == ann
    # nested types survive, not just top-level equality
    assert isinstance(restored.camera, Camera)
    assert isinstance(restored.objects[0], ObjectAnnotation)
    assert isinstance(restored.pair_relations["(0,1)"], PairRelation)
    assert restored.objects[1].mask is None


def test_annotation_jsonl_round_trip(tmp_path):
    anns = [_example_annotation(), _example_annotation()]
    path = tmp_path / "annotations.jsonl"
    n = write_jsonl((a.to_dict() for a in anns), path)
    assert n == 2
    loaded = [StimulusAnnotation.from_dict(d) for d in read_jsonl(path)]
    assert loaded == anns


def test_probe_result_round_trip():
    rec = ProbeResult(
        model="qwen2.5-vl-7b",
        site="lm_vis_L14",
        layer=14,
        target="ratio",
        axis="depth",
        stimulus_set="set3",
        seed=0,
        split=2,
        metric="spearman",
        value=0.61,
        n=500,
        control_value=0.02,
    )
    assert ProbeResult.from_dict(rec.to_dict()) == rec


def test_cache_meta_row_round_trip():
    row = CacheMetaRow(
        image_id="set3_00142",
        object_id=0,
        row_index=0,
        pool=POOL_OBJECT,
        targets={"depth_m": 2.1, "x": 1.0, "z": 2.1},
        factors={"depth_bin": 3},
    )
    assert CacheMetaRow.from_dict(row.to_dict()) == row
    strip = CacheMetaRow(
        image_id="set3_00142", object_id=-1, row_index=7, pool=POOL_STRIP
    )
    assert CacheMetaRow.from_dict(strip.to_dict()) == strip


def test_lm_site_formatting():
    assert lm_site(SITE_LM_VIS, 14) == "lm_vis_L14"
    assert lm_site(SITE_LM_TXT, 0) == "lm_txt_L0"
    assert len(BASE_SITES) == 4


def test_lm_site_rejects_non_layer_sites():
    import pytest

    with pytest.raises(ValueError):
        lm_site("enc_out", 3)
