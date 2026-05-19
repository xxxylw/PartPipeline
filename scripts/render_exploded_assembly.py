from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def main() -> None:
    job = _load_job()
    frames_dir = Path(job["frames_dir"])
    frames_dir.mkdir(parents=True, exist_ok=True)

    _clear_scene()
    bpy.ops.import_scene.gltf(filepath=job["source_level_a"])
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not objects:
        raise RuntimeError(f"No mesh objects imported from {job['source_level_a']}")

    center, diagonal = _scene_bounds(objects)
    distance = max(diagonal, 1.0) * float(job["explode_scale"])
    frame_count = int(job["frame_count"])
    explode_frame = max(2, int(frame_count * 0.35))
    hold_frame = max(explode_frame + 1, int(frame_count * 0.65))
    rotation = math.radians(float(job["rotation_degrees"]))

    for index, obj in enumerate(objects):
        origin_location = obj.location.copy()
        origin_rotation = obj.rotation_euler.copy()
        obj_center = _object_center(obj)
        direction = obj_center - center
        if direction.length < 1e-6:
            angle = (index / max(len(objects), 1)) * math.tau
            direction = Vector((math.cos(angle), math.sin(angle), 0.25))
        direction.normalize()
        exploded_location = origin_location + direction * distance
        exploded_rotation = origin_rotation.copy()
        exploded_rotation.rotate_axis("Z", rotation * (1 if index % 2 == 0 else -1))
        exploded_rotation.rotate_axis("X", rotation * 0.35)

        _keyframe(obj, 1, origin_location, origin_rotation)
        _keyframe(obj, explode_frame, exploded_location, exploded_rotation)
        _keyframe(obj, hold_frame, exploded_location, exploded_rotation)
        _keyframe(obj, frame_count, origin_location, origin_rotation)

    _setup_camera(center, diagonal)
    _setup_lighting(center, diagonal)
    _setup_render(job)
    bpy.ops.render.render(animation=True)


def _load_job() -> dict:
    if "--" not in sys.argv:
        raise RuntimeError("Expected job JSON path after --")
    job_path = Path(sys.argv[sys.argv.index("--") + 1])
    return json.loads(job_path.read_text(encoding="utf-8"))


def _clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def _scene_bounds(objects: list) -> tuple[Vector, float]:
    points = []
    for obj in objects:
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    minimum = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    maximum = Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points)))
    center = (minimum + maximum) * 0.5
    diagonal = (maximum - minimum).length
    return center, diagonal


def _object_center(obj) -> Vector:
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    maximum = Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points)))
    return (minimum + maximum) * 0.5


def _keyframe(obj, frame: int, location: Vector, rotation) -> None:
    obj.location = location
    obj.rotation_euler = rotation
    obj.keyframe_insert(data_path="location", frame=frame)
    obj.keyframe_insert(data_path="rotation_euler", frame=frame)


def _setup_camera(center: Vector, diagonal: float) -> None:
    distance = max(diagonal, 1.0) * 2.6
    camera_data = bpy.data.cameras.new("Camera")
    camera = bpy.data.objects.new("Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = center + Vector((distance, -distance, distance * 0.72))
    direction = center - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera_data.lens = 55
    camera_data.dof.use_dof = False
    bpy.context.scene.camera = camera


def _setup_lighting(center: Vector, diagonal: float) -> None:
    bpy.context.scene.world.color = (1.0, 1.0, 1.0)
    light_data = bpy.data.lights.new("Key_Area", type="AREA")
    light = bpy.data.objects.new("Key_Area", light_data)
    bpy.context.collection.objects.link(light)
    distance = max(diagonal, 1.0) * 1.8
    light.location = center + Vector((distance, -distance * 0.7, distance))
    light_data.energy = 500
    light_data.size = max(diagonal, 1.0)


def _setup_render(job: dict) -> None:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.frame_start = 1
    scene.frame_end = int(job["frame_count"])
    scene.render.fps = int(job["fps"])
    scene.render.resolution_x = int(job["width"])
    scene.render.resolution_y = int(job["height"])
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(Path(job["frames_dir"]) / "frame_")


if __name__ == "__main__":
    main()
