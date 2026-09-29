"""Grid maze router for the V3.1-H1 board, driven by the DRC unconnected list.

Two routing layers (F.Cu, B.Cu). The inner layers stay as planes. Every
copper item on the board is rasterised as an obstacle with the clearance
plus half the track width, so a path found on the grid is DRC clean by
construction. Plane nets (GND, +12V_KIT) are routed from each pad to the
nearest spot where a via fits.
"""
import heapq, json, math, os, subprocess, sys
from array import array
from itertools import count
from kp import *

FM = pcbnew.FromMM
V = pcbnew.VECTOR2I
GRID = 0.5
CLEAR = 0.2
EDGE_CLEAR = 2.0
VIA_D, VIA_DRILL = 0.6, 0.3
PLANE_NETS = {'GND', '+12V_KIT'}
LAYERS = [pcbnew.F_Cu, pcbnew.B_Cu]
COST_STEP, COST_TURN, COST_VIA = 10, 30, 160
COST_PREFER = 3

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, '..', 'CREWLINE-PRIM-PCB-001.kicad_pcb')
SP = os.path.join(HERE, 'work')
os.makedirs(SP, exist_ok=True)


def net_via(name):
    """(diameter, drill) from the net class, matching the project setup."""
    w = net_width(name)
    return (1.0, 0.5) if w >= 2.5 else (0.8, 0.4) if w >= 1.0 else (VIA_D, VIA_DRILL)


def net_width(name):
    if name in ('+12V_BATT', '+12V_GATED', 'GND', '/BATTFUSE', '{slash}BATTFUSE'):
        return 2.5
    if name == '+12V_KIT' or name == 'STARLINK_PWR_P' or 'PWR' in name:
        return 1.0
    return 0.4


class Grid:
    def __init__(self, board):
        bb = board.GetBoardEdgesBoundingBox()
        self.x0, self.y0 = mm(bb.GetLeft()), mm(bb.GetTop())
        self.W = int(math.ceil(mm(bb.GetWidth()) / GRID)) + 1
        self.H = int(math.ceil(mm(bb.GetHeight()) / GRID)) + 1
        self.edge_x1, self.edge_y1 = mm(bb.GetRight()), mm(bb.GetBottom())
        self.widths = [0.4, 1.0, 2.5, VIA_D, 0.8, 1.0]
        # block[w][layer] -> bytearray; a cell is blocked for a track of width w.
        # block[w][layer][i]: 0 free, n>0 blocked only by net n, -1 blocked by several nets or by netless copper.
        self.block = {w: [array('i', [0]) * (self.W * self.H) for _ in LAYERS] for w in self.widths}
        self.net_cells = {}
        self.via_cells = {}

    def cell(self, xmm, ymm):
        return int(round((xmm - self.x0) / GRID)), int(round((ymm - self.y0) / GRID))

    def pos(self, cx, cy):
        return self.x0 + cx * GRID, self.y0 + cy * GRID

    def idx(self, cx, cy):
        return cy * self.W + cx

    def _stamp(self, layers, hit, bbox, margin_fn, netid=-1):
        """Mark cells: hit(px,py,margin)->bool for each width's margin."""
        x0, y0, x1, y1 = bbox
        if netid <= 0:
            netid = -1
        for w in self.widths:
            m = margin_fn(w)
            cx0, cy0 = self.cell(x0 - m, y0 - m)
            cx1, cy1 = self.cell(x1 + m, y1 + m)
            for cy in range(max(cy0, 0), min(cy1, self.H - 1) + 1):
                for cx in range(max(cx0, 0), min(cx1, self.W - 1) + 1):
                    px, py = self.pos(cx, cy)
                    if hit(px, py, m):
                        i = self.idx(cx, cy)
                        for l in layers:
                            cur = self.block[w][l][i]
                            self.block[w][l][i] = netid if cur in (0, netid) else -1

    def own_cells(self, hit, bbox):
        x0, y0, x1, y1 = bbox
        cx0, cy0 = self.cell(x0, y0)
        cx1, cy1 = self.cell(x1, y1)
        out = set()
        for cy in range(max(cy0, 0), min(cy1, self.H - 1) + 1):
            for cx in range(max(cx0, 0), min(cx1, self.W - 1) + 1):
                px, py = self.pos(cx, cy)
                if hit(px, py, 0.0):
                    out.add((cx, cy))
        return out

    # --- geometry helpers -------------------------------------------------
    @staticmethod
    def seg_dist(px, py, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay
        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

    def add_pad(self, pad, net):
        bb = pad.GetBoundingBox()
        bbox = (mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()))
        layers = [i for i, l in enumerate(LAYERS) if pad.IsOnLayer(l)]
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or not layers:
            layers = [0, 1]
            drill = pad.GetDrillSize()
            r = mm(max(drill.x, drill.y)) / 2
            c = pad.GetPosition(); cx, cy = mm(c.x), mm(c.y)
            self._stamp(layers, lambda px, py, m: math.hypot(px - cx, py - cy) <= r + m, bbox, lambda w: 0.25 + w / 2, -1)
            return
        def hit(px, py, m):
            if m == 0.0:
                return pad.HitTest(V(FM(px), FM(py)))
            # conservative: expanded bounding box
            return bbox[0] - m <= px <= bbox[2] + m and bbox[1] - m <= py <= bbox[3] + m
        self._stamp(layers, hit, bbox, lambda w: CLEAR + w / 2, pad.GetNetCode())

    def add_track(self, t, net):
        s, e = t.GetStart(), t.GetEnd()
        ax, ay, bx, by = mm(s.x), mm(s.y), mm(e.x), mm(e.y)
        hw = mm(t.GetWidth()) / 2
        layers = [i for i, l in enumerate(LAYERS) if t.IsOnLayer(l)]
        if not layers:
            return
        bbox = (min(ax, bx) - hw, min(ay, by) - hw, max(ax, bx) + hw, max(ay, by) + hw)
        hit = lambda px, py, m: self.seg_dist(px, py, ax, ay, bx, by) <= hw + m
        self._stamp(layers, hit, bbox, lambda w: CLEAR + w / 2, t.GetNetCode())
        if net == 'x':
            self.net_cells.setdefault(net, []).append((layers, self.own_cells(hit, bbox)))

    def add_via(self, v, net):
        c = v.GetPosition(); cx, cy = mm(c.x), mm(c.y)
        r = mm(v.GetWidth(pcbnew.F_Cu)) / 2
        bbox = (cx - r, cy - r, cx + r, cy + r)
        hit = lambda px, py, m: math.hypot(px - cx, py - cy) <= r + m
        self._stamp([0, 1], hit, bbox, lambda w: CLEAR + w / 2, v.GetNetCode())
        self.via_cells.setdefault(v.GetNetCode(), set()).add(self.cell(cx, cy))
        if net == 'x':
            self.net_cells.setdefault(net, []).append(([0, 1], self.own_cells(hit, bbox)))

    def add_shape(self, d, net):
        bb = d.GetBoundingBox()
        bbox = (mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()))
        layers = [i for i, l in enumerate(LAYERS) if d.IsOnLayer(l)]
        if not layers:
            return
        hit = lambda px, py, m: bbox[0] - m <= px <= bbox[2] + m and bbox[1] - m <= py <= bbox[3] + m
        self._stamp(layers, hit, bbox, lambda w: CLEAR + w / 2, d.GetNetCode())
        if net == 'x':
            self.net_cells.setdefault(net, []).append((layers, self.own_cells(hit, bbox)))

    def add_edge(self):
        for w in self.widths:
            m = EDGE_CLEAR + w / 2
            for cy in range(self.H):
                for cx in range(self.W):
                    px, py = self.pos(cx, cy)
                    if px < self.x0 + m or px > self.edge_x1 - m or py < self.y0 + m or py > self.edge_y1 - m:
                        i = self.idx(cx, cy)
                        for l in (0, 1):
                            self.block[w][l][i] = -1

    def own_mask(self, net):
        out = [set(), set()]
        for layers, cells in self.net_cells.get(net, []):
            for l in layers:
                out[l] |= cells
        return out


def build_grid(board):
    g = Grid(board)
    g.add_edge()
    for f in board.GetFootprints():
        for p in f.Pads():
            g.add_pad(p, p.GetNetname())
        if f.GetReference() == 'REF**':
            # Mounting hole: keep copper out of the whole washer area, not just the drill.
            c = f.GetCourtyard(pcbnew.F_CrtYd).BBox()
            cx, cy = mm(f.GetPosition().x), mm(f.GetPosition().y)
            r = mm(c.GetWidth()) / 2
            bbox = (cx - r, cy - r, cx + r, cy + r)
            g._stamp([0, 1], lambda px, py, m: math.hypot(px - cx, py - cy) <= r + m, bbox, lambda w: CLEAR + w / 2, -1)
    for t in tracks(board):
        if t.GetClass() == 'PCB_VIA':
            g.add_via(t, t.GetNetname())
        else:
            g.add_track(t, t.GetNetname())
    for d in drawings(board):
        if d.IsOnCopperLayer() and hasattr(d, 'GetShapeStr'):
            g.add_shape(d, d.GetNetname())
    return g


VIA_SIZE_FOR_ROUTE = (VIA_D, VIA_DRILL)


def route(g, netcode, width, starts, goals, to_via=False, prefer=None):
    """Dijkstra from start cells to goal cells. starts/goals: sets of (layer,cx,cy).
    Returns list of (layer,cx,cy) or None."""
    blk = g.block[width]
    blkv = g.block[VIA_SIZE_FOR_ROUTE[0]]
    W, H = g.W, g.H
    tick = count()

    def free(l, cx, cy):
        v = blk[l][cy * W + cx]
        return v == 0 or v == netcode

    def via_ok(cx, cy):
        i = cy * W + cx
        return blkv[0][i] in (0, netcode) and blkv[1][i] in (0, netcode)

    own_vias = g.via_cells.get(netcode, set())
    prefer = prefer or set()
    dist = {}
    prev = {}
    pq = []
    for s in starts:
        dist[(s, None)] = 0
        heapq.heappush(pq, (0, next(tick), s, None))
    goal_hit = None
    while pq:
        d, _, node, dirn = heapq.heappop(pq)
        key = (node, dirn)
        if dist.get(key, 1e18) < d:
            continue
        l, cx, cy = node
        if to_via and node not in starts and ((cx, cy) in own_vias or via_ok(cx, cy)):
            goal_hit = key
            break
        if not to_via and node in goals:
            goal_hit = key
            break
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + ddx, cy + ddy
            if 0 <= nx < W and 0 <= ny < H and free(l, nx, ny):
                nd = d + (COST_PREFER if (l, nx, ny) in prefer else COST_STEP) + (COST_TURN if dirn is not None and dirn != (ddx, ddy) else 0)
                nk = ((l, nx, ny), (ddx, ddy))
                if nd < dist.get(nk, 1e18):
                    dist[nk] = nd; prev[nk] = key
                    heapq.heappush(pq, (nd, next(tick), (l, nx, ny), (ddx, ddy)))
        if not to_via:
            ol = 1 - l
            if via_ok(cx, cy) and free(ol, cx, cy):
                nd = d + COST_VIA
                nk = ((ol, cx, cy), None)
                if nd < dist.get(nk, 1e18):
                    dist[nk] = nd; prev[nk] = key
                    heapq.heappush(pq, (nd, next(tick), (ol, cx, cy), None))
    if goal_hit is None:
        return None
    path = []
    k = goal_hit
    while k is not None:
        path.append(k[0]); k = prev.get(k)
    path.reverse()
    return path


def commit_path(board, g, net_code, net, width, path, start_pt=None, end_pt=None, end_via=False):
    """Turn a cell path into tracks and vias on the board and into obstacles."""
    segs = []
    i = 0
    while i < len(path):
        j = i
        l = path[i][0]
        while j + 1 < len(path) and path[j + 1][0] == l:
            j += 1
        run = path[i:j + 1]
        # compress collinear runs
        k = 0
        while k < len(run) - 1:
            m = k + 1
            dx, dy = run[m][1] - run[k][1], run[m][2] - run[k][2]
            while m + 1 < len(run) and (run[m + 1][1] - run[m][1], run[m + 1][2] - run[m][2]) == (dx, dy):
                m += 1
            segs.append((l, run[k], run[m]))
            k = m
        if j + 1 < len(path):
            segs.append(('via', run[-1], None))
        i = j + 1
    layer_ids = [pcbnew.F_Cu, pcbnew.B_Cu]
    def add_track(l, a, b):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(V(FM(a[0]), FM(a[1]))); t.SetEnd(V(FM(b[0]), FM(b[1])))
        t.SetWidth(FM(width)); t.SetLayer(layer_ids[l]); t.SetNetCode(net_code)
        board.Add(t); g.add_track(t, net); CREATED.append(t.m_Uuid.AsString())
    def add_via(p, w=None, d=None):
        if w is None:
            w, d = net_via(net)
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(V(FM(p[0]), FM(p[1]))); v.SetDrill(FM(d)); v.SetNetCode(net_code)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        try:
            v.SetWidth(FM(w))
        except TypeError:
            v.SetWidth(pcbnew.F_Cu, FM(w))
        board.Add(v); g.add_via(v, net); CREATED.append(v.m_Uuid.AsString())
    first = path[0]
    if start_pt is not None:
        add_track(first[0], start_pt, g.pos(first[1], first[2]))
    for l, a, b in segs:
        if l == 'via':
            add_via(g.pos(a[1], a[2]))
        else:
            add_track(l, g.pos(a[1], a[2]), g.pos(b[1], b[2]))
    last = path[-1]
    if end_via and (last[1], last[2]) not in g.via_cells.get(net_code, set()):
        add_via(g.pos(last[1], last[2]))
    elif end_pt is not None:
        add_track(last[0], g.pos(last[1], last[2]), end_pt)


def uuid_index(board):
    idx = {}
    for f in board.GetFootprints():
        for p in f.Pads():
            idx[p.m_Uuid.AsString()] = p
    for t in tracks(board):
        idx[t.m_Uuid.AsString()] = t
    for d in drawings(board):
        idx[d.m_Uuid.AsString()] = d
    return idx


def item_cells(board, g, uuid_str, desc):
    """Cells (layer,cx,cy) covered by a DRC item, plus its anchor point."""
    item = UUIDS.get(uuid_str)
    if item is None:
        return None, None, None
    cls = item.GetClass()
    if cls == 'PAD':
        bb = item.GetBoundingBox()
        bbox = (mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()))
        cells = g.own_cells(lambda px, py, m: item.HitTest(V(FM(px), FM(py))), bbox)
        layers = [i for i, l in enumerate(LAYERS) if item.IsOnLayer(l)]
        c = item.GetPosition()
        return {(l, cx, cy) for l in layers for cx, cy in cells}, (mm(c.x), mm(c.y)), item
    if cls in ('PCB_TRACK', 'PCB_VIA', 'PCB_SHAPE'):
        # reuse the geometry already recorded for this net: rasterise this item alone
        tmp = Grid.__new__(Grid); tmp.__dict__.update(g.__dict__); tmp.net_cells = {}
        if cls == 'PCB_VIA':
            tmp.add_via(item, 'x')
        elif cls == 'PCB_TRACK':
            tmp.add_track(item, 'x')
        else:
            tmp.add_shape(item, 'x')
        cells = set()
        for layers, cs in tmp.net_cells.get('x', []):
            for l in layers:
                cells |= {(l, cx, cy) for cx, cy in cs}
        return cells, None, item
    return None, None, item


def run_drc():
    out = SP + '/drc-route.json'
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--severity-all', '--format', 'json', '-o', out, PCB], capture_output=True)
    return json.load(open(out))


CREATED = []


def main(limit_nets=None, pair_with=None):
    board = pcbnew.LoadBoard(PCB)
    # SWIG loses the collection wrappers once items are added or removed, so fetch them first.
    zone_list = zones(board)
    d = run_drc()
    todo = []
    for u in d['unconnected_items']:
        a, bb = u['items']
        net = a['description'].split('[')[1].split(']')[0]
        if limit_nets and net not in limit_nets:
            continue
        todo.append((net, a, bb))
    # wide nets first, then short connections first
    def keyf(t):
        net, a, bb = t
        L = math.hypot(a['pos']['x'] - bb['pos']['x'], a['pos']['y'] - bb['pos']['y'])
        return (-net_width(net), L)
    todo.sort(key=keyf)
    global UUIDS
    UUIDS = uuid_index(board)
    g = build_grid(board)
    nets = {n.GetNetname(): n.GetNetCode() for n in board.GetNetInfo().NetsByNetcode().values()} if hasattr(board.GetNetInfo(), 'NetsByNetcode') else {}
    def netcode(name):
        return board.GetNetInfo().GetNetItem(name).GetNetCode()
    prefer = set()
    if pair_with:
        # corridor beside the partner net's tracks: its cells and their neighbours
        code = netcode(pair_with)
        for t in tracks(board):
            if t.GetClass() == 'PCB_TRACK' and t.GetNetCode() == code:
                lay = 0 if t.IsOnLayer(pcbnew.F_Cu) else 1
                s0, e0 = t.GetStart(), t.GetEnd()
                a, bq = g.cell(mm(s0.x), mm(s0.y)), g.cell(mm(e0.x), mm(e0.y))
                n = max(abs(bq[0] - a[0]), abs(bq[1] - a[1]))
                for i in range(n + 1):
                    cx = a[0] + round((bq[0] - a[0]) * i / max(n, 1)); cy = a[1] + round((bq[1] - a[1]) * i / max(n, 1))
                    for dx in (-2, -1, 0, 1, 2):
                        for dy in (-2, -1, 0, 1, 2):
                            prefer.add((lay, cx + dx, cy + dy))
    ok = fail = 0
    global VIA_SIZE_FOR_ROUTE
    for net, a, bb in todo:
        width = net_width(net)
        VIA_SIZE_FOR_ROUTE = net_via(net)
        if net in PLANE_NETS:
            for it in (a, bb):
                cells, anchor, item = item_cells(board, g, it['uuid'], it['description'])
                if not cells or item.GetClass() != 'PAD' or item.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                    continue
                w = 0.4
                path = route(g, netcode(net), w, cells, set(), to_via=True)
                if path:
                    commit_path(board, g, netcode(net), net, w, path, start_pt=anchor, end_via=True); ok += 1
                else:
                    fail += 1; print('FAIL via', net, it['description'])
            continue
        ca, pa, ia = item_cells(board, g, a['uuid'], a['description'])
        cb, pb, ib = item_cells(board, g, bb['uuid'], bb['description'])
        if not ca or not cb:
            fail += 1; print('FAIL items', net, a['description'], bb['description']); continue
        w = width
        path = None
        while path is None and w >= 0.4:
            path = route(g, netcode(net), w, ca, cb, prefer=prefer)
            if path is None:
                w = {2.5: 1.0, 1.0: 0.4}.get(w, 0.0)
        if path is None:
            fail += 1; print('FAIL', net, a['description'][:50], '->', bb['description'][:50]); continue
        commit_path(board, g, netcode(net), net, w, path, start_pt=pa, end_pt=pb)
        ok += 1
        if w != width:
            print('narrowed', net, width, '->', w)
    pcbnew.ZONE_FILLER(board).Fill(zone_list)
    board.Save(PCB)
    # keep a record of what the router created, so a later pass can rip it up
    rec = SP + '/router-created.json'
    try:
        old = json.load(open(rec))
    except Exception:
        old = []
    json.dump(old + CREATED, open(rec, 'w'))
    print('routed', ok, 'failed', fail, 'items created', len(CREATED))


if __name__ == '__main__':
    args = sys.argv[1:]
    pair = None
    if args and args[0] == '--pair':
        pair = args[1]; args = args[2:]
    main(set(args) or None, pair_with=pair)
