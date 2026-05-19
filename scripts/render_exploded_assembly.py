from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = [
    (0.10, 0.72, 0.95, 1.0),
    (0.94, 0.24, 0.55, 1.0),
    (0.28, 0.82, 0.38, 1.0),
    (1.00, 0.62, 0.12, 1.0),
    (0.55, 0.32, 0.95, 1.0),
    (0.95, 0.88, 0.22, 1.0),
    (0.12, 0.82, 0.76, 1.0),
    (0.95, 0.36, 0.22, 1.0),
    (0.63, 0.88, 0.30, 1.0),
    (0.28, 0.48, 0.98, 1.0),
]


def main() -> None:
    job = _load_job()
    frames_dir = Path(job["frames_dir"])
    preview_dir = Path(job.get("preview_dir", Path(job["package_dir"]) / "preview"))
    frames_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    _clear_scene()
    bpy.ops.import_scene.gltf(filepath=job["source_level_a"])
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not objects:
        raise RuntimeError(f"No mesh objects imported from {job['source_level_a']}")
    _assign_segmentation_materials(objects)

    display_objects = _display_objects(objects)
    center, diagonal = _scene_bounds(display_objects)
    span = _scene_span(display_objects)
    distance = max(span.x, span.y, span.z, 1.0) * float(job["explode_scale"])
    frame_count = int(job["frame_count"])
    move_start_frame = max(2, int(frame_count * 0.12))
    explode_frame = max(move_start_frame + 1, int(frame_count * 0.44))
    hold_frame = max(explode_frame + 1, int(frame_count * 0.64))
    return_frame = max(hold_frame + 1, int(frame_count * 0.96))
    rotation = math.radians(float(job["rotation_degrees"]))
    exploded_points = []

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
        if obj in display_objects:
            exploded_points.extend(_translated_bounds(obj, exploded_location - origin_location))

        _keyframe(obj, 1, origin_location, origin_rotation)
        _keyframe(obj, move_start_frame, origin_location, origin_rotation)
        _keyframe(obj, explode_frame, exploded_location, exploded_rotation)
        _keyframe(obj, hold_frame, exploded_location, exploded_rotation)
        _keyframe(obj, return_frame, origin_location, origin_rotation)
        _keyframe(obj, frame_count, origin_location, origin_rotation)
        _smooth_animation(obj)

    shot_center, shot_span = _shot_bounds(display_objects, exploded_points)
    _setup_camera(shot_center, shot_span, job)
    _setup_lighting(shot_center, shot_span.length)
    _setup_floor(center, display_objects)
    _setup_render(job)
    _render_preview(preview_dir / "segmented_front.png", 1)
    _render_preview(preview_dir / "exploded_view.png", hold_frame)
    bpy.context.scene.render.filepath = str(frames_dir / "frame_")
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
    points = _all_bounds(objects)
    return _bounds_from_points(points)


def _scene_span(objects: list) -> Vector:
    points = _all_bounds(objects)
    minimum = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    maximum = Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points)))
    return maximum - minimum


def _bounds_from_points(points: list[Vector]) -> tuple[Vector, float]:
    minimum = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    maximum = Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points)))
    return (minimum + maximum) * 0.5, (maximum - minimum).length


def _all_bounds(objects: list) -> list[Vector]:
    points = []
    for obj in objects:
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    return points


def _translated_bounds(obj, offset: Vector) -> list[Vector]:
    return [(obj.matrix_world @ Vector(corner)) + offset for corner in obj.bound_box]


def _display_objects(objects: list) -> list:
    ranked = sorted(
        objects,
        key=lambda obj: len(getattr(obj.data, "polygons", [])),
        reverse=True,
    )
    total_faces = sum(len(getattr(obj.data, "polygons", [])) for obj in ranked)
    if total_faces <= 0:
        return ranked[: max(1, min(len(ranked), 3))]

    selected = []
    selected_faces = 0
    for obj in ranked:
        face_count = len(getattr(obj.data, "polygons", []))
        if not selected or face_count >= total_faces * 0.03 or selected_faces < total_faces * 0.92:
            selected.append(obj)
            selected_faces += face_count
    return selected


def _shot_bounds(objects: list, exploded_points: list[Vector]) -> tuple[Vector, Vector]:
    object_points = _all_bounds(objects)
    relevant_exploded = []
    for point in exploded_points:
        relevant_exploded.append(point)
    points = object_points + relevant_exploded
    minimum = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    maximum = Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points)))
    return (minimum + maximum) * 0.5, maximum - minimum


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


def _smooth_animation(obj) -> None:
    if obj.animation_data is None or obj.animation_data.action is None:
        return
    for curve in obj.animation_data.action.fcurves:
        for keyframe in curve.keyframe_points:
            keyframe.interpolation = "BEZIER"
            keyframe.easing = "EASE_IN_OUT"
            keyframe.handle_left_type = "AUTO_CLAMPED"
            keyframe.handle_right_type = "AUTO_CLAMPED"


def _assign_segmentation_materials(objects: list) -> None:
    for index, obj in enumerate(sorted(objects, key=lambda item: item.name)):
        material = bpy.data.materials.new(f"segmentation_part_{index + 1:03d}")
        material.use_nodes = True
        color = PALETTE[index % len(PALETTE)]
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            bsdf.inputs["Base Color"].default_value = color
            bsdf.inputs["Roughness"].default_value = 0.58
            bsdf.inputs["Alpha"].default_value = 1.0
        material.diffuse_color = color
        obj.data.materials.clear()
        obj.data.materials.append(material)


def _setup_camera(center: Vector, span: Vector, job: dict) -> None:
    dominant = max(span.x, span.y, span.z, 1.0)
    distance = dominant * 2.4
    camera_data = bpy.data.cameras.new("Camera")
    camera = bpy.data.objects.new("Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = center + Vector((distance, -distance * 1.15, distance * 0.70))
    direction = center - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    aspect = float(job["width"]) / max(float(job["height"]), 1.0)
    camera_data.ortho_scale = max(dominant * 0.72, 0.08) * (1.0 if aspect >= 1.0 else 1.15)
    camera_data.dof.use_dof = False
    bpy.context.scene.camera = camera


def _setup_lighting(center: Vector, diagonal: float) -> None:
    bpy.context.scene.world.color = (0.94, 0.94, 0.94)
    light_data = bpy.data.lights.new("Key_Area", type="AREA")
    light = bpy.data.objects.new("Key_Area", light_data)
    bpy.context.collection.objects.link(light)
    distance = max(diagonal, 1.0) * 1.2
    light.location = center + Vector((distance, -distance * 0.8, distance * 1.2))
    light_data.energy = 300
    light_data.size = max(diagonal * 0.9, 1.0)


def _setup_floor(center: Vector, objects: list) -> None:
    points = _all_bounds(objects)
    min_z = min(point.z for point in points)
    span = _scene_span(objects)
    bpy.ops.mesh.primitive_plane_add(size=max(span.x, span.y, 1.0) * 4.0, location=(center.x, center.y, min_z - 0.02))
    floor = bpy.context.object
    floor.name = "presentation_shadow_floor"
    material = bpy.data.materials.new("presentation_floor")
    material.diffuse_color = (0.90, 0.90, 0.88, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (0.90, 0.90, 0.88, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.8
    floor.data.materials.append(material)


def _setup_render(job: dict) -> None:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 12
    scene.frame_start = 1
    scene.frame_end = int(job["frame_count"])
    scene.render.fps = int(job["fps"])
    scene.render.resolution_x = int(job["width"])
    scene.render.resolution_y = int(job["height"])
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = -1.8
    scene.view_settings.gamma = 1.0
    scene.render.film_transparent = False


def _render_preview(path: Path, frame: int) -> None:
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
