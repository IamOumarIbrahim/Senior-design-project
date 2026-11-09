"""Cycles render of an exported OpenGL scene with BlenderToolbox (HTDerekLiu/BlenderToolbox, Apache-2.0).

blender -b -P blender_render.py -- scene.npz out.png W H ex ey ez tx ty tz fov [skip_first]
GL coordinates (y up, cm) are mapped to Blender (z up) and scaled by 0.05."""
import os, sys, json, math
import numpy as np
import bpy

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, 'vendor'))
import blendertoolbox as bt

a = sys.argv[sys.argv.index('--') + 1:]
scene, out, W, H = a[0], a[1], int(a[2]), int(a[3])
eye, tgt, fov = [float(v) for v in a[4:7]], [float(v) for v in a[7:10]], float(a[10])
skip_first = len(a) > 11 and a[11] == '1'
K = 0.05
gl2b = lambda p: (p[0] * K, -p[2] * K, p[1] * K)
lin = lambda c: tuple(float(np.clip(x, 0, 1)) ** 2.2 for x in c)

try:
    bt.blenderInit(W, H, 160, 1.0, True)
except Exception as e:                           # older toolbox vs Blender 5: keep going with the same settings
    print('blenderInit fallback:', e)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.film_transparent = True; sc.cycles.samples = 160; sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'

D = np.load(scene, allow_pickle=False)
meta = json.loads(str(D['meta']))
for k, m in enumerate(meta):
    if (skip_first and k == 0) or m['alpha'] < 0.9:
        continue
    V = np.stack([D[f'v{k}'][:, 0], -D[f'v{k}'][:, 2], D[f'v{k}'][:, 1]], 1) * K
    F = D[f'f{k}']
    obj = bt.readNumpyMesh(V.tolist(), F.tolist(), (0, 0, 0), (0, 0, 0), (1, 1, 1))
    obj.data.polygons.foreach_set('use_smooth', [True] * len(obj.data.polygons))
    col = bt.colorObj(lin(m['color']) + (1,), 0.5, 1.0, 1.0, 0.0, 0.0)
    em = np.array(m['emissive'])
    if m['tex']:
        uv = obj.data.uv_layers.new(name='UV')
        UV = D[f'u{k}']
        loops = np.zeros(len(obj.data.loops) * 2, np.float32)
        vi = np.zeros(len(obj.data.loops), np.int32); obj.data.loops.foreach_get('vertex_index', vi)
        loops[0::2], loops[1::2] = UV[vi, 0], 1 - UV[vi, 1]
        uv.data.foreach_set('uv', loops)
        mat = bpy.data.materials.new('screen'); obj.data.materials.append(mat)
        try: mat.use_nodes = True
        except Exception: pass
        nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']
        img = nt.nodes.new('ShaderNodeTexImage'); img.image = bpy.data.images.load(m['tex'])
        nt.links.new(img.outputs['Color'], bsdf.inputs['Base Color'])
        nt.links.new(img.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 1.2; bsdf.inputs['Roughness'].default_value = 0.08
    elif em.max() > 0.05:
        bt.setMat_emission(obj, bt.colorObj(lin(em) + (1,), 0.5, 1.0, 1.0, 0.0, 0.0), 6.0)
    elif m['spec'] >= 0.85 and np.mean(m['color']) > 0.35:
        bt.setMat_metal(obj, col, 0.0, 0.95)
        obj.active_material.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.28
    else:
        bt.setMat_plastic(obj, col, 0.0)
        obj.active_material.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = float(np.clip(0.75 - 0.5 * m['spec'], 0.15, 0.8))

try:
    bt.invisibleGround(location=(0, 0, 0.001), groundSize=400, shadowBrightness=0.82)
except AttributeError:                           # same shadow catcher, Blender 5 attribute names
    for o in list(bpy.data.objects):
        if o.name.startswith('Plane'): bpy.data.objects.remove(o)
    bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0.001), size=400)
    bpy.context.object.is_shadow_catcher = True
cam = bt.setCamera(gl2b(eye), gl2b(tgt), 50)
cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(fov)
cam.data.clip_end = 1000
sc.camera = cam
try:
    sun = bt.setLight_sun((25, -35, -150), 3.2, 0.25)
except Exception as e:
    print('sun fallback:', e)
    bpy.ops.object.light_add(type='SUN', rotation=(math.radians(25), math.radians(-35), math.radians(-150)))
    bpy.context.object.data.energy = 3.2; bpy.context.object.data.angle = 0.25
bpy.ops.object.light_add(type='AREA', location=gl2b((40, 90, 80)))      # soft fill from the camera side
fill = bpy.context.object; fill.data.energy = 9000; fill.data.size = 60
fill.rotation_euler = (math.radians(50), 0, math.radians(20))
try:
    bt.setLight_ambient(color=(0.28, 0.28, 0.30, 1))
except Exception as e:
    print('ambient fallback:', e)
    w = bpy.data.worlds.new('w'); sc.world = w
sc.render.filepath = out; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
bpy.ops.render.render(write_still=True)
print('rendered', out)
