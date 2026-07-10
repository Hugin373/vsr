"""SceneSpec round-trip."""

from sbind.stimuli.scene_spec import CameraSpec, ObjectSpec, SceneSpec


def test_scene_spec_round_trip():
    spec = SceneSpec(
        id="t_00001",
        camera=CameraSpec(
            pos_world=[0.0, -4.0, 1.5],
            target_world=[0.0, 1.5, 0.5],
            f_mm=35.0,
            sensor_width_mm=36.0,
            res_x=512,
            res_y=512,
        ),
        objects=[
            ObjectSpec("red_cube", "cube", [0.8, 0.05, 0.05], 0.4, [-0.7, 1.5, 0.2]),
            ObjectSpec("blue_sphere", "sphere", [0.05, 0.2, 0.8], 0.4, [0.7, 3.0, 0.2]),
        ],
        factors={"closer_object": 0, "near_depth_bin": 0},
    )
    restored = SceneSpec.from_dict(spec.to_dict())
    assert restored == spec
    assert restored.camera.height_m == 1.5
    assert isinstance(restored.objects[0], ObjectSpec)
