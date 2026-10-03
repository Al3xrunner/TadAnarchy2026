
import collections

import h3
import pyproj
from shapely.geometry import mapping, shape
from shapely.ops import transform

K_MIN = 3      
RING = 1       

_TO_M = pyproj.Transformer.from_crs(4326, 2180, always_xy=True).transform
_TO_LL = pyproj.Transformer.from_crs(2180, 4326, always_xy=True).transform
_cache = {}


def _rounded(geom, nd=5):
    def r(c):
        return [round(c[0], nd), round(c[1], nd)] if isinstance(c[0], float) else [r(x) for x in c]
    m = mapping(geom)
    return {"type": m["type"], "coordinates": r(m["coordinates"])}


def footprint(reports):
   
    dev10 = collections.defaultdict(set)
    for r in reports:
        dev10[r.cell10].add(r.device_id)
    key = frozenset((c, len(d)) for c, d in dev10.items())
    if key in _cache:
        return _cache[key]
    grown = collections.defaultdict(set)
    for c, devs in dev10.items():
        for n in h3.grid_disk(c, RING):
            grown[n] |= devs
    keep, seen = set(), set()
    for c in grown:                                 
        if c in seen:
            continue
        comp, stack = set(), [c]
        while stack:
            x = stack.pop()
            if x in seen or x not in grown:
                continue
            seen.add(x)
            comp.add(x)
            stack.extend(h3.grid_disk(x, 1))
        if len(set().union(*(grown[x] for x in comp))) >= K_MIN:
            keep |= comp
    if not keep:
        result = (set(), None)
    else:
        geom = shape(h3.cells_to_geo(list(keep)))
        smooth = transform(_TO_LL, transform(_TO_M, geom).buffer(25).buffer(-25).simplify(3))
        result = (keep, _rounded(smooth))
    if len(_cache) > 512:
        _cache.clear()
    _cache[key] = result
    return result
