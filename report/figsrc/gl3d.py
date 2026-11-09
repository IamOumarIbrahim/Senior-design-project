"""Small offscreen OpenGL renderer used for the report's 3D figures.

Shadow-mapped Blinn-Phong with hemisphere ambient, MSAA, emissive parts,
translucent parts, textured quads and a cheap bloom in post. Units are cm, Y up.
"""
import os
os.environ.setdefault('SDL_VIDEO_WINDOW_POS', '-4000,-4000')
import ctypes
import numpy as np
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, HIDDEN
from OpenGL.GL import *
from OpenGL.GL import shaders
from PIL import Image, ImageFilter

# ----------------------------------------------------------------- math
def norm(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.where(n == 0, 1, n)

def T(x, y, z):
    m = np.eye(4); m[:3, 3] = (x, y, z); return m

def S(x, y=None, z=None):
    if y is None: y = z = x
    return np.diag([x, y, z, 1.0])

def R(axis, deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    m = np.eye(4)
    if axis == 'x': m[1:3, 1:3] = [[c, -s], [s, c]]
    elif axis == 'y': m[0, 0], m[0, 2], m[2, 0], m[2, 2] = c, s, -s, c
    else: m[0:2, 0:2] = [[c, -s], [s, c]]
    return m

def chain(*ms):
    out = np.eye(4)
    for m in ms: out = out @ m
    return out

def look_at(eye, target, up=(0, 1, 0)):
    eye, target, up = map(lambda v: np.asarray(v, float), (eye, target, up))
    f = norm(target - eye); s = norm(np.cross(f, up)); u = np.cross(s, f)
    m = np.eye(4)
    m[0, :3], m[1, :3], m[2, :3] = s, u, -f
    m[:3, 3] = -m[:3, :3] @ eye
    return m

def perspective(fovy, aspect, n, f):
    t = 1 / np.tan(np.radians(fovy) / 2)
    m = np.zeros((4, 4))
    m[0, 0], m[1, 1] = t / aspect, t
    m[2, 2], m[2, 3] = (f + n) / (n - f), 2 * f * n / (n - f)
    m[3, 2] = -1
    return m

def ortho(l, r, b, t, n, f):
    m = np.eye(4)
    m[0, 0], m[1, 1], m[2, 2] = 2 / (r - l), 2 / (t - b), -2 / (f - n)
    m[:3, 3] = (-(r + l) / (r - l), -(t + b) / (t - b), -(f + n) / (f - n))
    return m

# ----------------------------------------------------------------- meshes
class Mesh:
    def __init__(self, P, N, UV, I):
        self.P = np.asarray(P, np.float32); self.N = np.asarray(N, np.float32)
        self.UV = np.asarray(UV, np.float32) if UV is not None else np.zeros((len(self.P), 2), np.float32)
        self.I = np.asarray(I, np.uint32)
        self.vao = None

    def upload(self):
        data = np.hstack([self.P, self.N, self.UV]).astype(np.float32)
        self.vao = glGenVertexArrays(1); glBindVertexArray(self.vao)
        vbo = glGenBuffers(1); glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)
        ebo = glGenBuffers(1); glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.I.nbytes, self.I, GL_STATIC_DRAW)
        st = 8 * 4
        for loc, size, off in ((0, 3, 0), (1, 3, 12), (2, 2, 24)):
            glEnableVertexAttribArray(loc)
            glVertexAttribPointer(loc, size, GL_FLOAT, GL_FALSE, st, ctypes.c_void_p(off))
        glBindVertexArray(0)

def _grid_faces(nu, nv):
    I = []
    for i in range(nu):
        for j in range(nv):
            a = i * (nv + 1) + j; b = a + nv + 1
            I += [a, b, a + 1, a + 1, b, b + 1]
    return I

def rbox(w, h, d, r=0.0, seg=5):
    """Rounded box centred at origin."""
    hs = np.array([w, h, d]) / 2.0
    r = min(r, *(hs * 0.999))
    def coords(hx):
        inner = hx - r
        pts = list(np.linspace(-inner, inner, 3)) if inner > 1e-6 else [0.0]
        band = list(np.linspace(inner, hx, seg + 1))[1:] if r > 0 else []
        return np.array(sorted(set([-b for b in band] + pts + band + ([-hx, hx] if r == 0 else []))))
    P, N, UV, I = [], [], [], []
    faces = [(0, 1, 2, 1), (0, 1, 2, -1), (1, 2, 0, 1), (1, 2, 0, -1), (2, 0, 1, 1), (2, 0, 1, -1)]
    for (ax, a1, a2, sgn) in faces:
        cu, cv = coords(hs[a1]), coords(hs[a2])
        base = len(P)
        for u in cu:
            for v in cv:
                p = np.zeros(3); p[ax] = sgn * hs[ax]; p[a1] = u; p[a2] = v
                inner = np.clip(p, -(hs - r), hs - r)
                dvec = p - inner
                if r > 0 and np.linalg.norm(dvec) > 1e-9:
                    n = dvec / np.linalg.norm(dvec); q = inner + n * r
                else:
                    n = np.zeros(3); n[ax] = sgn; q = p
                P.append(q); N.append(n)
                UV.append(((u / hs[a1] + 1) / 2, (v / hs[a2] + 1) / 2))
        fi = _grid_faces(len(cu) - 1, len(cv) - 1)
        if sgn < 0: fi = [fi[k + o] for k in range(0, len(fi), 3) for o in (0, 2, 1)]
        if ax == 1: fi = [fi[k + o] for k in range(0, len(fi), 3) for o in (0, 2, 1)]
        I += [base + x for x in fi]
    return Mesh(P, N, UV, I)

def cylinder(r, h, seg=40, caps=True, r2=None):
    """Along Y from 0 to h. r2 = top radius (cone)."""
    r2 = r if r2 is None else r2
    P, N, UV, I = [], [], [], []
    slope = (r - r2) / h
    for i in range(seg + 1):
        a = 2 * np.pi * i / seg; c, s = np.cos(a), np.sin(a)
        n = norm([c, slope, s])
        P += [[r * c, 0, r * s], [r2 * c, h, r2 * s]]; N += [n, n]; UV += [[i / seg, 0], [i / seg, 1]]
    for i in range(seg):
        a = 2 * i
        I += [a, a + 1, a + 2, a + 2, a + 1, a + 3]
    if caps:
        for y, rr, ny in ((0, r, -1), (h, r2, 1)):
            c0 = len(P); P.append([0, y, 0]); N.append([0, ny, 0]); UV.append([.5, .5])
            for i in range(seg + 1):
                a = 2 * np.pi * i / seg
                P.append([rr * np.cos(a), y, rr * np.sin(a)]); N.append([0, ny, 0])
                UV.append([.5 + .5 * np.cos(a), .5 + .5 * np.sin(a)])
            for i in range(seg):
                I += [c0, c0 + 1 + i, c0 + 2 + i] if ny < 0 else [c0, c0 + 2 + i, c0 + 1 + i]
    return Mesh(P, N, UV, I)

def sphere(r, seg=48, ring=32):
    P, N, UV = [], [], []
    for i in range(ring + 1):
        th = np.pi * i / ring
        for j in range(seg + 1):
            ph = 2 * np.pi * j / seg
            n = [np.sin(th) * np.cos(ph), np.cos(th), np.sin(th) * np.sin(ph)]
            P.append(np.array(n) * r); N.append(n); UV.append([j / seg, i / ring])
    I = []
    for i in range(ring):
        for j in range(seg):
            a = i * (seg + 1) + j; b = a + seg + 1
            I += [a, a + 1, b, a + 1, b + 1, b]
    return Mesh(P, N, UV, I)

def torus(Rr, r, seg=96, ring=24, arc=360):
    P, N, UV = [], [], []
    for i in range(seg + 1):
        u = np.radians(arc) * i / seg
        cu, su = np.cos(u), np.sin(u)
        for j in range(ring + 1):
            v = 2 * np.pi * j / ring
            n = np.array([np.cos(v) * cu, np.sin(v), np.cos(v) * su])
            P.append(np.array([Rr * cu, 0, Rr * su]) + r * n); N.append(n); UV.append([i / seg, j / ring])
    I = []
    for i in range(seg):
        for j in range(ring):
            a = i * (ring + 1) + j; b = a + ring + 1
            I += [a, b, a + 1, a + 1, b, b + 1]
    return Mesh(P, N, UV, I)

def tube(pts, r, ring=14, samples=None):
    """Cable along a polyline (smoothed with Catmull-Rom)."""
    pts = np.asarray(pts, float)
    if samples:
        out = []
        p = np.vstack([pts[0], pts, pts[-1]])
        for k in range(1, len(p) - 2):
            for t in np.linspace(0, 1, samples, endpoint=False):
                p0, p1, p2, p3 = p[k - 1], p[k], p[k + 1], p[k + 2]
                out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        out.append(pts[-1]); pts = np.array(out)
    tang = norm(np.gradient(pts, axis=0))
    ref = np.array([0, 1, 0]) if abs(tang[0][1]) < .9 else np.array([1, 0, 0])
    nrm = norm(np.cross(tang[0], ref)); P, N, UV = [], [], []
    for k, (p, t) in enumerate(zip(pts, tang)):
        nrm = norm(nrm - t * np.dot(nrm, t)); b = np.cross(t, nrm)
        for j in range(ring + 1):
            a = 2 * np.pi * j / ring
            n = np.cos(a) * nrm + np.sin(a) * b
            P.append(p + r * n); N.append(n); UV.append([k / len(pts), j / ring])
    I = []
    for k in range(len(pts) - 1):
        for j in range(ring):
            a = k * (ring + 1) + j; c = a + ring + 1
            I += [a, c, a + 1, a + 1, c, c + 1]
    return Mesh(P, N, UV, I)

def quad(w, h):
    """XY quad facing +Z, centred."""
    P = [[-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h / 2, 0], [-w / 2, h / 2, 0]]
    return Mesh(P, [[0, 0, 1]] * 4, [[0, 0], [1, 0], [1, 1], [0, 1]], [0, 1, 2, 0, 2, 3])

def frustum(apex, base_pts):
    """Pyramid side faces from apex to a polygon (for camera FOV)."""
    P, N, I = [], [], []
    apex = np.asarray(apex, float)
    for k in range(len(base_pts)):
        a, b = np.asarray(base_pts[k], float), np.asarray(base_pts[(k + 1) % len(base_pts)], float)
        n = norm(np.cross(a - apex, b - apex))
        base = len(P); P += [apex, a, b]; N += [n, n, n]; I += [base, base + 1, base + 2]
    return Mesh(P, N, None, I)

# ----------------------------------------------------------------- shaders
VS = """
#version 330 core
layout(location=0) in vec3 aP; layout(location=1) in vec3 aN; layout(location=2) in vec2 aUV;
uniform mat4 M, VP, LVP;
out vec3 wP; out vec3 wN; out vec2 uv; out vec4 lP;
void main(){ vec4 w = M*vec4(aP,1); wP=w.xyz; wN=mat3(transpose(inverse(M)))*aN; uv=aUV; lP=LVP*w; gl_Position=VP*w; }
"""
FS = """
#version 330 core
in vec3 wP; in vec3 wN; in vec2 uv; in vec4 lP;
uniform vec3 color, emissive, eye, Ldir, sky, ground;
uniform float spec, shin, alpha, useTex, shadowOn, rim, emOnly;
uniform sampler2D tex; uniform sampler2DShadow smap;
out vec4 frag;
float shadow(){
  vec3 p = lP.xyz/lP.w*0.5+0.5; if(p.z>1.0) return 1.0;
  float s=0.0; vec2 ts=1.0/vec2(textureSize(smap,0));
  for(int x=-2;x<=2;x++) for(int y=-2;y<=2;y++) s+=texture(smap, vec3(p.xy+vec2(x,y)*ts*1.5, p.z-0.0015));
  return s/25.0;
}
void main(){
  if(emOnly>0.5){ frag = vec4(emissive*1.4, 1.0); return; }
  vec3 n = normalize(wN); vec3 v = normalize(eye-wP);
  if(dot(n,v)<0.0) n=-n;
  vec3 base = color;
  if(useTex>0.5){ vec4 t = texture(tex, uv); base = t.rgb; }
  vec3 L = normalize(-Ldir);
  float sh = shadowOn>0.5 ? shadow() : 1.0;
  float diff = max(dot(n,L),0.0);
  vec3 h = normalize(L+v); float sp = pow(max(dot(n,h),0.0), shin)*spec;
  vec3 L2 = normalize(vec3(0.6,0.35,0.7)); float diff2 = max(dot(n,L2),0.0)*0.25;
  vec3 amb = mix(ground, sky, n.y*0.5+0.5);
  float rimt = pow(1.0-max(dot(n,v),0.0), 3.0)*rim;
  vec3 c = base*(amb + vec3(1.0,0.97,0.92)*diff*sh*0.95 + diff2) + vec3(sp*sh) + rimt*vec3(0.6,0.7,0.8);
  if(useTex>0.5) c = mix(c, base, 0.75);
  c += emissive;
  c = pow(c, vec3(1.0/1.15));
  frag = vec4(c, alpha);
}
"""
SVS = """
#version 330 core
layout(location=0) in vec3 aP; uniform mat4 M, LVP;
void main(){ gl_Position = LVP*M*vec4(aP,1); }
"""
SFS = "#version 330 core\nvoid main(){}"

# ----------------------------------------------------------------- scene
class Obj:
    def __init__(self, mesh, M, color=(.7, .7, .7), spec=.25, shin=32, emissive=(0, 0, 0),
                 alpha=1.0, tex=None, shadow=True, rim=0.15, name=None):
        self.mesh, self.M = mesh, M
        self.color, self.spec, self.shin = np.array(color, float), spec, shin
        self.emissive, self.alpha, self.tex, self.cast = np.array(emissive, float), alpha, tex, shadow
        self.rim, self.name = rim, name

class Renderer:
    _inited = False

    def __init__(self, W=2400, H=1500, ss=1):
        if not Renderer._inited:
            pygame.init()
            pygame.display.set_mode((64, 64), DOUBLEBUF | OPENGL | HIDDEN)
            Renderer._inited = True
        self.W, self.H = W, H
        self.prog = shaders.compileProgram(shaders.compileShader(VS, GL_VERTEX_SHADER),
                                           shaders.compileShader(FS, GL_FRAGMENT_SHADER))
        self.sprog = shaders.compileProgram(shaders.compileShader(SVS, GL_VERTEX_SHADER),
                                            shaders.compileShader(SFS, GL_FRAGMENT_SHADER))
        # MSAA target
        self.fbo = glGenFramebuffers(1); glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        cb = glGenRenderbuffers(1); glBindRenderbuffer(GL_RENDERBUFFER, cb)
        glRenderbufferStorageMultisample(GL_RENDERBUFFER, 16, GL_RGBA8, W, H)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, cb)
        db = glGenRenderbuffers(1); glBindRenderbuffer(GL_RENDERBUFFER, db)
        glRenderbufferStorageMultisample(GL_RENDERBUFFER, 16, GL_DEPTH_COMPONENT24, W, H)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, db)
        # resolve target
        self.rfbo = glGenFramebuffers(1); glBindFramebuffer(GL_FRAMEBUFFER, self.rfbo)
        rt = glGenRenderbuffers(1); glBindRenderbuffer(GL_RENDERBUFFER, rt)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_RGBA8, W, H)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, rt)
        # shadow map
        self.SM = 4096
        self.sfbo = glGenFramebuffers(1); self.stex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.stex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT32F, self.SM, self.SM, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
        for p, v in ((GL_TEXTURE_MIN_FILTER, GL_LINEAR), (GL_TEXTURE_MAG_FILTER, GL_LINEAR),
                     (GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER), (GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER),
                     (GL_TEXTURE_COMPARE_MODE, GL_COMPARE_REF_TO_TEXTURE), (GL_TEXTURE_COMPARE_FUNC, GL_LEQUAL)):
            glTexParameteri(GL_TEXTURE_2D, p, v)
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, [1, 1, 1, 1])
        glBindFramebuffer(GL_FRAMEBUFFER, self.sfbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.stex, 0)
        glDrawBuffer(GL_NONE); glReadBuffer(GL_NONE)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.texcache = {}

    def texture(self, path):
        if path in self.texcache: return self.texcache[path]
        img = Image.open(path).convert('RGBA').transpose(Image.FLIP_TOP_BOTTOM)
        t = glGenTextures(1); glBindTexture(GL_TEXTURE_2D, t)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img.tobytes())
        glGenerateMipmap(GL_TEXTURE_2D)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, 0x84FE, 16.0)  # anisotropy
        self.texcache[path] = t
        return t

    def render(self, objs, eye, target, fov=35, light_dir=(-0.45, -1.0, -0.55), light_span=120,
               light_center=(0, 0, 0), sky=(0.62, 0.66, 0.72), ground=(0.30, 0.28, 0.27),
               bloom=0.0, out=None, up=(0, 1, 0)):
        W, H = self.W, self.H
        for o in objs:
            if o.mesh.vao is None: o.mesh.upload()
        V = look_at(eye, target, up); Pm = perspective(fov, W / H, 2.0, 2000.0)
        VP = Pm @ V
        Ld = norm(light_dir); lc = np.array(light_center, float)
        LV = look_at(lc - Ld * 300, lc, (0, 0, 1) if abs(Ld[1]) > 0.99 else (0, 1, 0))
        LP = ortho(-light_span, light_span, -light_span, light_span, 1, 700)
        LVP = LP @ LV
        glEnable(GL_DEPTH_TEST)
        # shadow pass
        glBindFramebuffer(GL_FRAMEBUFFER, self.sfbo); glViewport(0, 0, self.SM, self.SM)
        glClear(GL_DEPTH_BUFFER_BIT); glUseProgram(self.sprog)
        glEnable(GL_POLYGON_OFFSET_FILL); glPolygonOffset(2.0, 4.0)
        for o in objs:
            if not o.cast or o.alpha < 0.99: continue
            glUniformMatrix4fv(glGetUniformLocation(self.sprog, 'M'), 1, GL_TRUE, o.M.astype(np.float32))
            glUniformMatrix4fv(glGetUniformLocation(self.sprog, 'LVP'), 1, GL_TRUE, LVP.astype(np.float32))
            glBindVertexArray(o.mesh.vao); glDrawElements(GL_TRIANGLES, len(o.mesh.I), GL_UNSIGNED_INT, None)
        glDisable(GL_POLYGON_OFFSET_FILL)
        imgs = []
        for em in ((0.0, 1.0) if bloom > 0 else (0.0,)):
            # main pass
            glBindFramebuffer(GL_FRAMEBUFFER, self.fbo); glViewport(0, 0, W, H)
            glClearColor(0, 0, 0, 0 if em == 0 else 1); glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glUseProgram(self.prog); p = self.prog
            u = lambda n: glGetUniformLocation(p, n)
            glUniformMatrix4fv(u('VP'), 1, GL_TRUE, VP.astype(np.float32))
            glUniformMatrix4fv(u('LVP'), 1, GL_TRUE, LVP.astype(np.float32))
            glUniform3f(u('eye'), *eye); glUniform3f(u('Ldir'), *Ld); glUniform3f(u('sky'), *sky); glUniform3f(u('ground'), *ground)
            glActiveTexture(GL_TEXTURE1); glBindTexture(GL_TEXTURE_2D, self.stex); glUniform1i(u('smap'), 1)
            glUniform1i(u('tex'), 0)
            glDisable(GL_CULL_FACE)
            opaque = [o for o in objs if o.alpha >= 0.99]
            trans = sorted([o for o in objs if o.alpha < 0.99],
                           key=lambda o: -np.linalg.norm(o.M[:3, 3] - np.array(eye)))
            for group, blend in ((opaque, False), (trans, True)):
                if blend:
                    glEnable(GL_BLEND); glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA); glDepthMask(GL_FALSE)
                for o in group:
                    glUniformMatrix4fv(u('M'), 1, GL_TRUE, o.M.astype(np.float32))
                    glUniform3f(u('color'), *o.color); glUniform3f(u('emissive'), *o.emissive)
                    glUniform1f(u('spec'), o.spec); glUniform1f(u('shin'), o.shin); glUniform1f(u('alpha'), o.alpha)
                    glUniform1f(u('rim'), o.rim); glUniform1f(u('shadowOn'), 1.0); glUniform1f(u('emOnly'), em)
                    if o.tex:
                        glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, self.texture(o.tex)); glUniform1f(u('useTex'), 1.0)
                    else:
                        glUniform1f(u('useTex'), 0.0)
                    glBindVertexArray(o.mesh.vao); glDrawElements(GL_TRIANGLES, len(o.mesh.I), GL_UNSIGNED_INT, None)
                if blend:
                    glDisable(GL_BLEND); glDepthMask(GL_TRUE)
            glBindFramebuffer(GL_READ_FRAMEBUFFER, self.fbo); glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.rfbo)
            glBlitFramebuffer(0, 0, W, H, 0, 0, W, H, GL_COLOR_BUFFER_BIT, GL_NEAREST)
            glBindFramebuffer(GL_READ_FRAMEBUFFER, self.rfbo)
            buf = glReadPixels(0, 0, W, H, GL_RGBA, GL_UNSIGNED_BYTE)
            img = Image.frombytes('RGBA', (W, H), buf).transpose(Image.FLIP_TOP_BOTTOM)
            imgs.append(img)
        img = imgs[0]
        if bloom > 0:
            a = np.asarray(img).astype(float)
            e = imgs[1].convert('RGB')
            b1 = np.asarray(e.filter(ImageFilter.GaussianBlur(W / 300))).astype(float)
            b2 = np.asarray(e.filter(ImageFilter.GaussianBlur(W / 90))).astype(float)
            b = (b1 * 0.6 + b2 * 0.9) * bloom
            a[..., :3] = np.clip(a[..., :3] + b, 0, 255)
            a[..., 3] = np.clip(a[..., 3] + b.max(-1), 0, 255)
            img = Image.fromarray(a.astype(np.uint8))
        self.VP = VP
        if out: img.save(out)
        return img

    def project(self, pts):
        pts = np.atleast_2d(np.asarray(pts, float))
        h = np.hstack([pts, np.ones((len(pts), 1))]) @ self.VP.T
        ndc = h[:, :3] / h[:, 3:4]
        return np.stack([(ndc[:, 0] + 1) / 2 * self.W, (1 - ndc[:, 1]) / 2 * self.H], 1)

def backdrop(img, top=(250, 251, 253), bottom=(226, 230, 236), shadow_floor=None):
    W, H = img.size
    y = np.linspace(0, 1, H)[:, None, None]
    g = (np.array(top) * (1 - y) + np.array(bottom) * y) * np.ones((1, W, 1))
    bg = Image.fromarray(g.astype(np.uint8)).convert('RGBA')
    bg.alpha_composite(img)
    return bg.convert('RGB')
