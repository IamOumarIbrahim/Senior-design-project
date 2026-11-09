"""In-car placement: realistic seated driver (Blender Studio CC0 base mesh, rigged here) plus the prototype parts."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion
from blib import *

OUT = sys.argv[sys.argv.index('--') + 1]
FAST = '--fast' in sys.argv
LIB = os.environ.get("HUMAN_BASE_MESHES", "human_base_meshes_bundle.blend")  # Blender Studio CC0 bundle v1.4.1
UI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Figures", "ui_tablet_light.png")
sc = reset(2400, 1700, 48 if FAST else 256)
sc.unit_settings.scale_length = 1.0
world_hdri('kloofendal_48d_partly_cloudy_puresky_2k.hdr', 1.0, rot=200)
sc.render.film_transparent = False

# ------------------------------------------------------------------ materials
skin = mat('skin', (0.40, 0.25, 0.17), 0.42, sss=0.25)
shirt = mat('shirt', (0.13, 0.20, 0.32), 0.85)
jeans = mat('jeans', (0.10, 0.12, 0.17), 0.9)
shoe = mat('shoe', (0.05, 0.04, 0.035), 0.5)
hair = mat('hair', (0.018, 0.012, 0.009), 0.78)
sclera = mat('sclera', (0.85, 0.83, 0.80), 0.15)
iris = mat('iris', (0.06, 0.035, 0.02), 0.1, coat=1.0)
leather = mat('leather', (0.035, 0.035, 0.038), 0.55, coat=0.15)
dash = mat('dash', (0.06, 0.062, 0.068), 0.75)
trim = mat('trim', (0.25, 0.26, 0.28), 0.35, 0.9)
headl = mat('headliner', (0.55, 0.53, 0.50), 0.9)
glass = mat('glass', (0.9, 0.95, 0.95), 0.0, trans=1.0)
blk = mat('blk', (0.015, 0.015, 0.017), 0.4)
chrome = mat('chrome', (0.9, 0.9, 0.92), 0.1, 1.0)
anod = mat('anod', (0.05, 0.055, 0.065), 0.35, 0.9)
copper = mat('copper', (0.75, 0.42, 0.22), 0.35, 1.0)
amber = mat('amber', (1, 0.6, 0.2), 0.3, emit=(1.0, 0.42, 0.05), emit_str=6)
lensg = mat('lens', (0.02, 0.02, 0.03), 0.02, coat=1.0)


def bump(m, scale, strength):
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = 8
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = strength
    nt.links.new(n.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])


for m_, s_, k_ in ((leather, 180, 0.15), (dash, 400, 0.12), (shirt, 900, 0.25), (jeans, 1200, 0.3),
                   (hair, 2500, 0.6), (skin, 600, 0.05), (headl, 600, 0.2)):
    bump(m_, s_, k_)

# ------------------------------------------------------------------ driver mesh
with bpy.data.libraries.load(LIB) as (src, dst):
    dst.objects = ['GEO-body_male_realistic', 'GEO-body_male_realistic.eye.L', 'GEO-body_male_realistic.eye.R']
body, eyeL, eyeR = dst.objects
for o in dst.objects:
    sc.collection.objects.link(o)
for e in (eyeL, eyeR):
    mw = e.matrix_world.copy(); e.parent = None; e.matrix_world = mw
body.location = (0, 0, 0)
bpy.context.view_layer.update()
for e in (eyeL, eyeR):
    e.location.x += 2.264
bpy.context.view_layer.update()
for mr in body.modifiers:
    if mr.type == 'MULTIRES':
        mr.levels = 1; mr.render_levels = 2 if FAST else 3

# clothes as smooth shader masks on the rest shape (Generated coords follow the undeformed mesh)
body.data.use_auto_texspace = False
body.data.texspace_location = (0, 0, 0.85); body.data.texspace_size = (0.5, 0.5, 0.9)


def body_material():
    bm_ = bpy.data.materials.new('body'); bm_.use_nodes = True; nt = bm_.node_tree; nt.nodes.clear()
    N = nt.nodes.new; Lk = nt.links.new
    out = N('ShaderNodeOutputMaterial')
    tc = N('ShaderNodeTexCoord')
    ma = N('ShaderNodeVectorMath'); ma.operation = 'MULTIPLY_ADD'
    ma.inputs[1].default_value = (1.0, 1.0, 1.8); ma.inputs[2].default_value = (-0.5, -0.5, -0.05)
    Lk(tc.outputs['Generated'], ma.inputs[0])
    sx = N('ShaderNodeSeparateXYZ'); Lk(ma.outputs[0], sx.inputs[0])
    ab = N('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; Lk(sx.outputs['X'], ab.inputs[0])

    def rng(sock, a, b):
        r = N('ShaderNodeMapRange'); r.interpolation_type = 'SMOOTHSTEP'; Lk(sock, r.inputs['Value'])
        r.inputs['From Min'].default_value = a; r.inputs['From Max'].default_value = b; return r.outputs['Result']

    def op(kind, a, b):
        m = N('ShaderNodeMath'); m.operation = kind
        (Lk(a, m.inputs[0]) if not isinstance(a, float) else m.inputs[0].__setattr__('default_value', a))
        (Lk(b, m.inputs[1]) if not isinstance(b, float) else m.inputs[1].__setattr__('default_value', b))
        return m.outputs[0]

    X, Y, Z = sx.outputs['X'], sx.outputs['Y'], sx.outputs['Z']
    arm = op('MULTIPLY', rng(ab.outputs[0], 0.19, 0.215), rng(Z, 1.34, 1.30))
    fore = op('MULTIPLY', arm, rng(Z, 1.17, 1.145))
    sh = op('MULTIPLY', op('MINIMUM', op('MAXIMUM', op('SUBTRACT', ab.outputs[0], 0.055), 0.0), 0.1), 1.2)
    sh = op('ADD', sh, op('MULTIPLY', op('MAXIMUM', op('SUBTRACT', Y, 0.02), 0.0), 1.5))
    head = rng(op('SUBTRACT', Z, sh), 1.398, 1.415)
    legs = op('MULTIPLY', rng(Z, 0.955, 0.935), op('SUBTRACT', 1.0, arm))
    shoem = op('MULTIPLY', rng(Z, 0.12, 0.10), op('SUBTRACT', 1.0, arm))
    skinm = op('MAXIMUM', fore, head)
    zy = op('ADD', Z, op('MULTIPLY', Y, 0.9))
    hairm = op('MULTIPLY', rng(zy, 1.540, 1.566), head)

    def bsdf(m_):
        src = m_.node_tree.nodes['Principled BSDF']; b = N('ShaderNodeBsdfPrincipled')
        for i in src.inputs:
            if hasattr(i, 'default_value') and i.name in b.inputs and not i.is_linked:
                try:
                    b.inputs[i.name].default_value = i.default_value
                except Exception:
                    pass
        no = N('ShaderNodeTexNoise'); no.inputs['Scale'].default_value = 900; no.inputs['Detail'].default_value = 8
        bp = N('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.15 if m_ is not skin else 0.04
        Lk(no.outputs['Fac'], bp.inputs['Height']); Lk(bp.outputs['Normal'], b.inputs['Normal'])
        return b.outputs[0]

    def mix(a, b, fac):
        m = N('ShaderNodeMixShader'); Lk(fac, m.inputs[0]); Lk(a, m.inputs[1]); Lk(b, m.inputs[2]); return m.outputs[0]

    s = bsdf(shirt)
    s = mix(s, bsdf(jeans), legs)
    s = mix(s, bsdf(skin), skinm)
    s = mix(s, bsdf(hair), hairm)
    s = mix(s, bsdf(shoe), shoem)
    Lk(s, out.inputs['Surface'])
    return bm_


body.data.materials.append(body_material())
for p in body.data.polygons:
    p.use_smooth = True
for e in (eyeL, eyeR):
    e.data.materials.clear(); e.data.materials.append(sclera)
    for p in e.data.polygons:
        p.use_smooth = True
    c = e.matrix_world.translation
    cyl('iris', 0.0062, 0.0015, (c.x, c.y - 0.0136, c.z), iris, 32, rot=(math.pi / 2, 0, 0))
irises = [o for o in sc.objects if o.name.startswith('iris')]

# ------------------------------------------------------------------ armature
J = {'pelvis': ((0, 0.0, 0.92), (0, 0.0, 1.05)), 'spine': ((0, 0, 1.05), (0, 0.01, 1.25)),
     'chest': ((0, 0.01, 1.25), (0, 0.0, 1.42)), 'neck': ((0, 0, 1.42), (0, -0.01, 1.52)),
     'head': ((0, -0.01, 1.52), (0, -0.01, 1.69))}
for s, sx in (('L', 1), ('R', -1)):
    J['shoulder.' + s] = ((sx * 0.03, 0.0, 1.39), (sx * 0.17, 0.01, 1.40))
    J['upperarm.' + s] = ((sx * 0.17, 0.01, 1.40), (sx * 0.288, 0.02, 1.10))
    J['forearm.' + s] = ((sx * 0.288, 0.02, 1.10), (sx * 0.375, -0.03, 0.86))
    Wr, Tp = Vector((sx * 0.375, -0.03, 0.86)), Vector((sx * 0.4403, -0.1296, 0.763))
    Kn, Mi = Wr + (Tp - Wr) * 0.46, Wr + (Tp - Wr) * 0.72
    J['hand.' + s] = (tuple(Wr), tuple(Kn))
    J['fing1.' + s] = (tuple(Kn), tuple(Mi))
    J['fing2.' + s] = (tuple(Mi), tuple(Tp))
    J['thigh.' + s] = ((sx * 0.09, 0.0, 0.90), (sx * 0.10, 0.0, 0.48))
    J['shin.' + s] = ((sx * 0.10, 0.0, 0.48), (sx * 0.11, 0.02, 0.08))
    J['foot.' + s] = ((sx * 0.11, 0.02, 0.08), (sx * 0.12, -0.12, 0.02))
PAR = {'spine': 'pelvis', 'chest': 'spine', 'neck': 'chest', 'head': 'neck'}
for s in 'LR':
    PAR.update({'shoulder.' + s: 'chest', 'upperarm.' + s: 'shoulder.' + s, 'forearm.' + s: 'upperarm.' + s,
                'hand.' + s: 'forearm.' + s, 'thigh.' + s: 'pelvis', 'shin.' + s: 'thigh.' + s,
                'foot.' + s: 'shin.' + s, 'fing1.' + s: 'hand.' + s, 'fing2.' + s: 'fing1.' + s})
ad = bpy.data.armatures.new('rig'); arm = bpy.data.objects.new('rig', ad); sc.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='EDIT')
for n, (h, t) in J.items():
    b = ad.edit_bones.new(n); b.head, b.tail = h, t
for n, p in PAR.items():
    ad.edit_bones[n].parent = ad.edit_bones[p]
    ad.edit_bones[n].use_connect = n.split('.')[0] in ('forearm', 'hand', 'shin', 'foot', 'upperarm', 'fing1', 'fing2')
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
md = body.modifiers['Armature'] if 'Armature' in body.modifiers else [m for m in body.modifiers if m.type == 'ARMATURE'][0]
print('vgroups', len(body.vertex_groups))
for e in irises:
    e.parent = [x for x in (eyeL, eyeR) if (x.matrix_world.translation - e.matrix_world.translation).length < 0.03][0]
    e.matrix_parent_inverse = e.parent.matrix_world.inverted()
bpy.context.view_layer.update()
for e in (eyeL, eyeR):
    mw = e.matrix_world.copy(); e.parent = arm; e.parent_type = 'BONE'; e.parent_bone = 'head'
    bpy.context.view_layer.update(); e.matrix_world = mw

# place the rig so the hip joints sit on the H-point
HP = Vector((0, 0.02, 0.40))
arm.location = HP - Vector((0, 0, 0.90))
bpy.context.view_layer.update()


def empty(name, loc):
    e = bpy.data.objects.new(name, None); e.location = loc; sc.collection.objects.link(e); return e


# wheel
WC, WR, TILT = Vector((-0.0, -0.36, 0.80)), 0.185, math.radians(62)
wn = Vector((0, math.cos(TILT), math.sin(math.radians(90) - TILT)))   # placeholder, rebuilt below
rotW = Matrix.Rotation(math.pi / 2 - TILT, 4, 'X')
grip = lambda ang: WC + rotW @ Vector((WR * math.cos(ang), 0, WR * math.sin(ang)))
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='POSE')
pb = arm.pose.bones
pb['spine'].rotation_mode = pb['chest'].rotation_mode = pb['neck'].rotation_mode = pb['head'].rotation_mode = 'XYZ'
pb['spine'].rotation_euler = (math.radians(-12), 0, 0)
pb['chest'].rotation_euler = (math.radians(-4), 0, 0)
pb['neck'].rotation_euler = (math.radians(10), 0, 0)
pb['head'].rotation_euler = (math.radians(6), 0, math.radians(4))
bpy.context.view_layer.update()
AO = arm.matrix_world.translation.copy()


def head_w(n):
    return AO + pb[n].matrix.translation


def aim(n, target_w):
    """Rotate pose bone n (armature space) so its axis points at a world point."""
    M = pb[n].matrix.copy(); h = M.translation.copy()
    cur = M.col[1].xyz.normalized(); want = (Vector(target_w) - AO - h).normalized()
    q = cur.rotation_difference(want)
    R = q.to_matrix() @ M.to_3x3()
    N_ = R.to_4x4(); N_.translation = h
    pb[n].matrix = N_
    bpy.context.view_layer.update()


def orient(n, d_w, nrm_w, n_rest):
    """Set bone n so its axis is d_w and its rest palm normal n_rest turns to nrm_w."""
    R0 = arm.data.bones[n].matrix_local.to_3x3()
    d0 = (R0 @ Vector((0, 1, 0))).normalized(); n0 = (n_rest - d0 * n_rest.dot(d0)).normalized()
    d1 = d_w.normalized(); n1 = (nrm_w - d1 * nrm_w.dot(d1)).normalized()
    B0 = Matrix((d0, n0, d0.cross(n0))).transposed(); B1 = Matrix((d1, n1, d1.cross(n1))).transposed()
    h = pb[n].matrix.translation.copy()
    N_ = (B1 @ B0.transposed() @ R0).to_4x4(); N_.translation = h
    pb[n].matrix = N_
    bpy.context.view_layer.update()


def two_bone(a, b, tip, target, hint):
    S = head_w(a); la = (Vector(J[a][1]) - Vector(J[a][0])).length; lb = (Vector(J[b][1]) - Vector(J[b][0])).length
    T = Vector(target); d = min((T - S).length, (la + lb) * 0.995); u = (T - S).normalized()
    x = (la * la - lb * lb + d * d) / (2 * d); h = math.sqrt(max(la * la - x * x, 0))
    hv = Vector(hint); hv = (hv - u * hv.dot(u)).normalized()
    E = S + u * x + hv * h
    aim(a, E); aim(b, S + u * d)
    return E


for s, sx in (('L', 1), ('R', -1)):
    G = grip(math.radians(28 if sx > 0 else 152))
    nW = (rotW @ Vector((0, 1, 0))).normalized()
    if nW.y < 0:
        nW = -nW
    ur = (G - WC).normalized()                       # radial, outward through the rim
    hdir = (ur + nW * 0.25).normalized()             # back of the palm rests on the driver side of the rim
    P = G + nW * 0.03                                # palm centre
    W_ = P - hdir * 0.05
    E = two_bone('upperarm.' + s, 'forearm.' + s, 'hand.' + s, W_, (sx * 0.8, 0.2, -1.0))
    nrest = Vector((-sx, 0.0, 0.0))                  # A-pose palms face the thighs
    orient('hand.' + s, hdir, -nW, nrest)
    hb = arm.data.bones['hand.' + s]; d0 = (hb.matrix_local.to_3x3() @ Vector((0, 1, 0))).normalized()
    n0 = (nrest - d0 * nrest.dot(d0)).normalized(); ax = d0.cross(n0)
    for k, ang in (('fing1.', 85), ('fing2.', 75)):
        b = arm.data.bones[k + s]; q = pb[k + s]; q.rotation_mode = 'QUATERNION'
        q.rotation_quaternion = Quaternion(b.matrix_local.to_3x3().inverted() @ ax, math.radians(ang))
    bpy.context.view_layer.update()
    K = two_bone('thigh.' + s, 'shin.' + s, 'foot.' + s, (sx * 0.15, -0.66, 0.13), (sx * 0.15, -0.3, 1.0))
    aim('foot.' + s, (sx * 0.16, -0.86, 0.02))
    print('pose', s, 'elbow', tuple(round(v, 3) for v in E), 'knee', tuple(round(v, 3) for v in K))
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()

# ------------------------------------------------------------------ car interior
def prof_mesh(name, prof, x0, x1, m, subsurf=2, solid=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    a = [bm.verts.new((x0, y, z)) for y, z in prof]; b = [bm.verts.new((x1, y, z)) for y, z in prof]
    for i in range(len(prof) - 1):
        bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
    bm.to_mesh(me); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    o.data.materials.append(m)
    if solid:
        s = o.modifiers.new('s', 'SOLIDIFY'); s.thickness = solid
    if subsurf:
        s = o.modifiers.new('ss', 'SUBSURF'); s.levels = s.render_levels = subsurf
    for p in o.data.polygons:
        p.use_smooth = True
    return o


# dashboard profile (y, z): lower knee panel -> binnacle hood -> top -> windshield base
prof_mesh('dash', [(-0.52, 0.30), (-0.50, 0.52), (-0.53, 0.66), (-0.60, 0.80), (-0.62, 0.90), (-0.70, 0.95),
                   (-0.90, 0.97), (-1.10, 0.95), (-1.18, 0.92)], -0.75, 1.0, dash, 2, 0.03)
prof_mesh('binnacle', [(-0.58, 0.83), (-0.56, 0.92), (-0.63, 0.99), (-0.78, 1.00)], -0.22, 0.22, dash, 2, 0.02)
box('cluster', (0.36, 0.01, 0.12), (0, -0.66, 0.86), mat('lcd', (0.02, 0.03, 0.05), 0.1, emit=(0.15, 0.3, 0.6),
                                                          emit_str=0.6), rot=(math.radians(-15), 0, 0))
prof_mesh('windshield', [(-1.16, 0.93), (-0.80, 1.15), (-0.40, 1.30)], -0.75, 1.0, glass, 1, 0.006)
prof_mesh('roof', [(-0.42, 1.31), (0.0, 1.34), (0.6, 1.33)], -0.75, 1.0, headl, 1, 0.02)
box('door', (0.06, 1.5, 0.65), (-0.72, -0.25, 0.55), leather, bevel=0.02)
box('door_top', (0.10, 1.4, 0.04), (-0.70, -0.25, 0.89), trim, bevel=0.01)
box('armrest', (0.12, 0.45, 0.06), (-0.64, -0.05, 0.66), leather, bevel=0.02)
pil = prof_mesh('pillar', [(-1.16, 0.93), (-0.80, 1.15), (-0.40, 1.31)], -0.76, -0.68, dash, 1, 0.0)
box('floor', (1.9, 2.2, 0.02), (0.1, -0.3, 0.0), mat('carpet', (0.04, 0.04, 0.045), 0.95))
cons = box('console', (0.26, 1.0, 0.42), (0.40, -0.25, 0.21), dash, bevel=0.04)
box('console_top', (0.24, 0.5, 0.03), (0.40, 0.0, 0.43), leather, bevel=0.01)
# passenger-side pillar and door so the cabin is closed on the camera side
prof_mesh('pillarR', [(-1.16, 0.93), (-0.80, 1.15), (-0.40, 1.31)], 0.99, 1.06, dash, 1, 0.0)
box('doorR', (0.06, 1.5, 0.65), (1.05, -0.25, 0.55), leather, bevel=0.02)
box('gear', (0.04, 0.05, 0.10), (0.40, -0.25, 0.48), leather, bevel=0.015)

# seat: cushion + backrest + bolsters + headrest (subdivided boxes)
def soft(name, size, loc, rot=(0, 0, 0)):
    o = box(name, size, loc, leather, rot=rot)
    b = o.modifiers.new('b', 'BEVEL'); b.width = 0.03; b.segments = 2
    s = o.modifiers.new('ss', 'SUBSURF'); s.levels = s.render_levels = 2
    for p in o.data.polygons:
        p.use_smooth = True
    return o


BR = math.radians(-14)
soft('cushion', (0.50, 0.52, 0.12), (0, -0.05, 0.31), (math.radians(6), 0, 0))
for sx in (-1, 1):
    soft('bolster', (0.08, 0.48, 0.10), (sx * 0.24, -0.05, 0.37), (math.radians(6), 0, 0))
    soft('bolsterb', (0.08, 0.12, 0.55), (sx * 0.24, 0.20, 0.70), (BR, 0, 0))
soft('back', (0.48, 0.12, 0.66), (0, 0.24, 0.70), (BR, 0, 0))
soft('headrest', (0.26, 0.09, 0.18), (0, 0.33, 1.17), (BR, 0, 0))
for sx in (-1, 1):
    cyl('hr_post', 0.006, 0.08, (sx * 0.07, 0.31, 1.06), chrome, 16, rot=(BR, 0, 0))
box('seatbase', (0.40, 0.45, 0.20), (0, -0.05, 0.12), blk, bevel=0.02)

# steering wheel + column
bpy.ops.mesh.primitive_torus_add(major_radius=WR, minor_radius=0.016, major_segments=96, minor_segments=24,
                                 location=WC, rotation=(-TILT, 0, 0))
rim = bpy.context.object; rim.data.materials.append(leather)
for p in rim.data.polygons:
    p.use_smooth = True
hub = cyl('hub', 0.065, 0.06, WC, leather, 48, rot=(-TILT, 0, 0), bevel=0.01)
for ang in (0, 180, 270):
    a = math.radians(ang)
    p1 = WC + rotW @ Vector((0.06 * math.cos(a), 0, 0.06 * math.sin(a)))
    p2 = WC + rotW @ Vector((WR * math.cos(a), 0, WR * math.sin(a)))
    v = p2 - p1; sp = cyl('spoke', 0.012, v.length, (p1 + p2) / 2, trim, 16)
    sp.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
col_dir = rotW @ Vector((0, -1, 0))
cyl('column', 0.045, 0.30, WC + col_dir * 0.17, dash, 32).rotation_euler = col_dir.to_track_quat('Z', 'Y').to_euler()
pedal = mat('pedal', (0.3, 0.3, 0.32), 0.4, 0.8)
for px in (-0.09, 0.12):
    box('pedal', (0.07 if px < 0 else 0.10, 0.015, 0.10), (px, -0.78, 0.12), pedal, 0.005, rot=(math.radians(-25), 0, 0))

# ------------------------------------------------------------------ prototype parts
CAM = Vector((-0.10, -0.64, 1.035))
box('c922_clip', (0.03, 0.04, 0.035), CAM - Vector((0, 0.0, 0.03)), blk, 0.008)
c922 = cyl('c922', 0.014, 0.094, CAM, blk, 48, rot=(0, math.pi / 2, 0), bevel=0.004)
cyl('c922_lens', 0.0095, 0.004, CAM + Vector((0, 0.0145, 0.0)), lensg, 48, rot=(math.pi / 2, 0, 0))
cyl('c922_ring', 0.011, 0.002, CAM + Vector((0, 0.0138, 0.0)), chrome, 48, rot=(math.pi / 2, 0, 0))
for dx in (-0.033, 0.033):
    cyl('c922_mic', 0.0025, 0.002, CAM + Vector((dx, 0.0142, 0.0)), chrome, 16, rot=(math.pi / 2, 0, 0))
box('bar', (0.62, 0.016, 0.014), (0.05, -1.02, 0.965), blk, 0.003)
box('bar_led', (0.60, 0.006, 0.004), (0.05, -1.012, 0.972), amber)
L = bpy.data.lights.new('barL', 'AREA'); L.size = 0.6; L.size_y = 0.02; L.shape = 'RECTANGLE'; L.energy = 6
L.color = (1, 0.5, 0.15); lo = bpy.data.objects.new('barL', L); sc.collection.objects.link(lo)
lo.location = (0.05, -1.0, 0.99); lo.rotation_euler = (math.radians(-110), 0, 0)
# 7-inch display on a stand beside the vents
D0 = Vector((0.36, -0.64, 1.03)); drot = (math.radians(-72), 0, math.radians(-14))
box('disp', (0.180, 0.112, 0.012), D0, blk, 0.004, rot=drot)
img = bpy.data.images.load(UI)
sm = bpy.data.materials.new('screen'); sm.use_nodes = True; nt = sm.node_tree
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img
em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.3
nt.links.new(tex.outputs['Color'], em.inputs['Color'])
nt.links.new(em.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface'])
bpy.ops.mesh.primitive_plane_add(size=1, location=D0, rotation=drot)
scr = bpy.context.object; scr.scale = (-0.165, -0.098, 1)
nrm = Matrix.Rotation(drot[2], 3, 'Z') @ Matrix.Rotation(drot[0], 3, 'X') @ Vector((0, 0, 1))
scr.location = D0 + nrm * 0.0065; scr.data.materials.append(sm)
cyl('stand', 0.008, 0.08, (0.36, -0.67, 0.97), anod, 16)
# Pebble V3 speaker and Pi case
SPK = Vector((0.60, -0.84, 1.02))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=SPK, segments=64, ring_count=32)
s = bpy.context.object; s.data.materials.append(mat('pebble', (0.02, 0.02, 0.022), 0.25, coat=0.6))
for p in s.data.polygons:
    p.use_smooth = True
cyl('drv', 0.022, 0.01, SPK + Vector((-0.012, 0.045, 0.0)), copper, 48, rot=(math.radians(80), 0, math.radians(-15)))
PI = Vector((0.40, -0.45, 0.46))
box('picase', (0.10, 0.07, 0.04), PI, anod, 0.006)
for i in range(6):
    box('vent', (0.004, 0.04, 0.002), PI + Vector((-0.025 + i * 0.01, 0, 0.0205)), blk)
box('led', (0.004, 0.002, 0.003), PI + Vector((0.04, -0.0355, 0.01)), mat('pwr', (0, 1, 0.2), 0.3, emit=(0.1, 1, 0.2),
                                                                      emit_str=20))

# camera field of view: translucent pyramid from the C922 to the driver
fov = bpy.data.materials.new('fov'); fov.use_nodes = True; fn = fov.node_tree
fn.nodes.clear(); tr = fn.nodes.new('ShaderNodeBsdfTransparent'); emi = fn.nodes.new('ShaderNodeEmission')
emi.inputs['Color'].default_value = (0.15, 0.45, 1.0, 1); emi.inputs['Strength'].default_value = 0.35
mx = fn.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = 0.16
o_ = fn.nodes.new('ShaderNodeOutputMaterial')
fn.links.new(tr.outputs[0], mx.inputs[1]); fn.links.new(emi.outputs[0], mx.inputs[2]); fn.links.new(mx.outputs[0], o_.inputs[0])
me = bpy.data.meshes.new('fov'); bm = bmesh.new()
apex = bm.verts.new(CAM + Vector((0, 0.016, 0)))
far_c = Vector((0.0, -0.10, 1.02)); hw, hh = 0.20, 0.19
cs = [bm.verts.new(far_c + Vector((dx, 0, dz))) for dx, dz in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
for i in range(4):
    bm.faces.new((apex, cs[i], cs[(i + 1) % 4]))
bm.to_mesh(me); fo = bpy.data.objects.new('fov', me); sc.collection.objects.link(fo); fo.data.materials.append(fov)
fo.visible_shadow = False
edge = mat('fovedge', (0.2, 0.5, 1.0), 0.5, emit=(0.2, 0.5, 1.0), emit_str=1.5)
for c_ in cs:
    v_ = Vector(c_.co) - Vector(apex.co); e_ = cyl('fov_e', 0.0009, v_.length, Vector(apex.co) + v_ / 2, edge, 8)
    e_.rotation_euler = v_.to_track_quat('Z', 'Y').to_euler(); e_.visible_shadow = False

sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.5; sun.angle = math.radians(2)
so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(55), 0, math.radians(200))
area_light((0.9, -0.2, 1.25), (0, -0.3, 0.9), 0.6, 18, (1.0, 0.95, 0.9))
_cc = [float(v) for v in os.environ.get('CAB_CAM', '0.98,-0.05,1.25,0.00,-0.50,0.85,18').split(',')]
camera(tuple(_cc[0:3]), tuple(_cc[3:6]), lens=_cc[6])
bpy.context.scene.camera.data.clip_start = 0.01
if '--hands' in sys.argv:
    camera((0.62, 0.05, 1.05), (0.08, -0.36, 0.84), lens=45)
    bpy.context.scene.camera.data.clip_start = 0.01
anchors({'cam': tuple(CAM), 'fov': (0.0, -0.25, 0.98), 'bar': (0.30, -1.02, 0.97), 'disp': tuple(D0),
         'spk': tuple(SPK), 'pi': tuple(PI), 'driver': (0, 0.0, 1.12)}, OUT.replace('.png', '.json'))
render(OUT)
