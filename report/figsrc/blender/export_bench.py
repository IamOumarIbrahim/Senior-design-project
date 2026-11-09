"""Export the OpenGL bench scene (latex_v3/figsrc/bench.py) as world-space meshes for Blender.

Runs bench.py up to its render call, so the parts, poses and camera stay identical.
Writes ../out/bench_scene.npz: per object vertices, faces, uvs, colour, spec, emissive, alpha, texture."""
import os, sys, json
import numpy as np

FIG = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../latex_v3/figsrc'))
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../out'))
os.chdir(FIG); sys.path.insert(0, FIG)
src = open('bench.py', encoding='utf8').read()
ns = {'__name__': 'bench_export'}
exec(compile(src.split('\nr = Renderer(')[0], 'bench.py', 'exec'), ns)


def dump(objs, name):
    data, meta = {}, []
    for k, o in enumerate(objs):
        m = o.mesh
        P = np.c_[m.P, np.ones(len(m.P))] @ np.asarray(o.M, float).T
        data[f'v{k}'] = P[:, :3].astype(np.float32)
        data[f'f{k}'] = m.I.reshape(-1, 3).astype(np.int32)
        data[f'u{k}'] = m.UV.astype(np.float32)
        meta.append(dict(color=[float(c) for c in o.color], spec=float(o.spec), shin=float(o.shin),
                         emissive=[float(c) for c in o.emissive], alpha=float(o.alpha),
                         tex=os.path.join(FIG, o.tex) if o.tex else None, cast=bool(o.cast)))
    data['meta'] = np.array(json.dumps(meta))
    np.savez_compressed(os.path.join(OUT, name), **data)
    print(name, len(objs), 'objects', sum(len(data[f'v{k}']) for k in range(len(objs))), 'vertices')


dump(ns['objs'], 'bench_scene.npz')
dump(ns['internals_exploded'](), 'bench_internals.npz')
