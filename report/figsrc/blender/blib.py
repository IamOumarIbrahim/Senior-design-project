"""Small helpers for Cycles product renders (units: cm, z up)."""
import bpy, bmesh, math, json, os
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HDRI = os.environ.get("HDRI_DIR", "hdri")  # Poly Haven CC0: studio_small_08, kloofendal_48d_partly_cloudy_puresky (2k)


def reset(W, H, samples=160):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.scale_length = 0.01
    sc.render.engine = 'CYCLES'
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.film_transparent = True
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for kind in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            for d in prefs.devices:
                d.use = d.type != 'CPU'
            if any(d.use for d in prefs.devices):
                sc.cycles.device = 'GPU'
                print('GPU', kind)
                break
        except Exception as e:
            print('no', kind, e)
    return sc


def world_hdri(name, strength=1.0, rot=0.0, bg_white=False):
    w = bpy.data.worlds.new('W'); bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree; nt.nodes.clear()
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value[2] = math.radians(rot)
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(os.path.join(HDRI, name))
    bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs['Strength'].default_value = strength
    out = nt.nodes.new('ShaderNodeOutputWorld')
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
    nt.links.new(env.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])


_mats = {}


def mat(name, color, rough=0.5, metal=0.0, emit=None, emit_str=0.0, coat=0.0, trans=0.0, sss=0.0, alpha=1.0):
    key = (name,)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if coat:
        b.inputs['Coat Weight'].default_value = coat
    if trans:
        b.inputs['Transmission Weight'].default_value = trans
    if sss:
        b.inputs['Subsurface Weight'].default_value = sss
        b.inputs['Subsurface Radius'].default_value = (1.0, 0.35, 0.2)
        b.inputs['Subsurface Scale'].default_value = 0.4
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = emit_str
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
    _mats[key] = m
    return m


def _finish(o, m, bevel, smooth=False):
    if m:
        o.data.materials.append(m)
    if bevel:
        bm = o.modifiers.new('bev', 'BEVEL'); bm.width = bevel; bm.segments = 3
        bm.limit_method = 'ANGLE'
    if smooth:
        for p in o.data.polygons:
            p.use_smooth = True
    return o


def box(name, size, loc, m=None, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return _finish(o, m, bevel)


def cyl(name, r, h, loc, m=None, verts=48, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object; o.name = name
    _finish(o, m, bevel)
    for p in o.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    return o


def text(body, loc, size, m, rot=(0, 0, 0), extrude=0.002, align='CENTER'):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o = bpy.context.object; o.data.body = body; o.data.size = size
    o.data.extrude = extrude; o.data.align_x = align; o.data.align_y = 'CENTER'
    o.data.materials.append(m)
    return o


def boolean(target, cutter, op='DIFFERENCE'):
    md = target.modifiers.new('b', 'BOOLEAN'); md.object = cutter; md.operation = op
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join(); objs[0].name = name
    return objs[0]


def shadow_catcher(size=400, z=0.0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    o = bpy.context.object; o.name = 'catcher'; o.is_shadow_catcher = True
    return o


def camera(loc, target, lens=50, ortho=None):
    cam = bpy.data.cameras.new('cam'); cam.lens = lens
    if ortho:
        cam.type = 'ORTHO'; cam.ortho_scale = ortho
    o = bpy.data.objects.new('cam', cam); bpy.context.scene.collection.objects.link(o)
    d = Vector(target) - Vector(loc)
    o.location = loc; o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = o
    cam.clip_start = 0.5; cam.clip_end = 5000
    return o


def area_light(loc, target, size, power, color=(1, 1, 1)):
    l = bpy.data.lights.new('a', 'AREA'); l.size = size; l.energy = power; l.color = color
    o = bpy.data.objects.new('a', l); bpy.context.scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o


def anchors(points, path):
    bpy.context.view_layer.update()
    sc = bpy.context.scene; W, H = sc.render.resolution_x, sc.render.resolution_y
    out = {}
    for k, p in points.items():
        c = world_to_camera_view(sc, sc.camera, Vector(p))
        out[k] = (c.x * W, (1 - c.y) * H)
    json.dump(out, open(path, 'w'), indent=1)


def render(path):
    import sys
    if '--anchors-only' in sys.argv:
        return
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
