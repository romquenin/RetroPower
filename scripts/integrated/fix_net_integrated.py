#!/usr/bin/env python3
"""Rip up and re-route a single net's chain -- v2, avec les memes corrections
que route_grid_compact5.py :
  1. verification de la couche d'arrivee (evite les connexions ouvertes)
  2. respect de l'espacement trou-a-trou (hole_to_hole) contre TOUS les
     trous deja presents sur la carte (pastilles traversantes + vias de
     tous les nets, y compris ceux places par ce script lui-meme)
  3. deduplication des vias (pas de nouveau perçage si un via existe deja
     pile au meme endroit)
  4. les extremites du chemin epousent exactement la position de la
     pastille (pas de decalage lie a l'arrondi de grille)
"""
import pcbnew, heapq, math

MM = pcbnew.FromMM
def to_mm(nm): return nm / 1e6

RES = 0.2
# NOTE : dans un coin tres congestionne (ex. Q1_GATE pres de K1/3V3/GND, ou
# aucun chemin ne passe meme au repli de marge le plus strict), abaisser
# temporairement RES a 0.1 avant d'appeler fix_net() peut suffire a trouver
# un chemin qu'une grille plus grossiere ratait par simple effet
# d'arrondi -- sans jamais reduire la marge de securite reelle exigee.
CLEAR = 0.20
TRACK_W = 0.35
VIA_DRILL = 0.4
VIA_SIZE = 0.8
HOLE_TO_HOLE_MIN = 0.30
OBSTACLE_MARGIN = CLEAR + TRACK_W / 2.0 + 0.2
FLOOR = CLEAR + TRACK_W / 2.0 + RES / 2.0
HARD_FLOOR = CLEAR + TRACK_W / 2.0
FALLBACK_MARGINS = sorted({OBSTACLE_MARGIN, OBSTACLE_MARGIN * 0.7, FLOOR, HARD_FLOOR}, reverse=True)

BOARD_FILE = "RetroPower_Integrated.kicad_pcb"
W_MM, H_MM = 53.335, 32.75

# meme correctif que route_grid_compact5.py : pastilles rectangulaires ->
# cercle circonscrit (sinon sous-estimation le long de la diagonale).
RECT_SHAPES = {pcbnew.PAD_SHAPE_RECT, pcbnew.PAD_SHAPE_TRAPEZOID,
               pcbnew.PAD_SHAPE_ROUNDRECT, pcbnew.PAD_SHAPE_CHAMFERED_RECT}

def pad_radius_mm(p):
    size = p.GetSize()
    w, h = to_mm(size.x), to_mm(size.y)
    if p.GetShape() in RECT_SHAPES:
        return ((w / 2.0) ** 2 + (h / 2.0) ** 2) ** 0.5
    return max(w, h) / 2.0


def fix_net(net_name, chain):
    board = pcbnew.LoadBoard(BOARD_FILE)
    NX = int(W_MM / RES) + 1
    NY = int(H_MM / RES) + 1

    def gx(x): return min(max(int(round(x / RES)), 0), NX - 1)
    def gy(y): return min(max(int(round(y / RES)), 0), NY - 1)
    def mmx(i): return i * RES
    def mmy(j): return j * RES

    net = board.FindNet(net_name)
    nc = net.GetNetCode()

    # --- registre global des trous (pastilles traversantes) + vias existants
    # (TOUS nets, y compris le net qu'on va rerouter -- ses anciens vias
    # seront retires juste apres, donc ils ne comptent plus une fois enleves)
    existing_holes = []
    all_pads = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for p in fp.Pads():
            pos = p.GetPosition()
            r = pad_radius_mm(p)
            layers = set()
            if p.IsOnLayer(pcbnew.F_Cu):
                layers.add(0)
            if p.IsOnLayer(pcbnew.B_Cu):
                layers.add(1)
            all_pads.append((p.GetNetCode(), to_mm(pos.x), to_mm(pos.y), r, layers))
            drill = p.GetDrillSize()
            if drill.x > 0:
                existing_holes.append((to_mm(pos.x), to_mm(pos.y), to_mm(drill.x) / 2.0))

    placed_vias = []  # vias des AUTRES nets (les notres seront rajoutes au fur et a mesure)
    tracks = []
    for tr in board.GetTracks():
        if tr.GetNetCode() == nc:
            continue  # sera enleve
        if tr.Type() == pcbnew.PCB_VIA_T:
            pos = tr.GetPosition()
            placed_vias.append((to_mm(pos.x), to_mm(pos.y)))
            tracks.append(('via', tr.GetNetCode(), to_mm(pos.x), to_mm(pos.y), to_mm(tr.GetWidth())))
            continue
        s, e = tr.GetStart(), tr.GetEnd()
        layer = 0 if tr.GetLayer() == pcbnew.F_Cu else 1
        tracks.append(('trk', tr.GetNetCode(), layer, to_mm(s.x), to_mm(s.y), to_mm(e.x), to_mm(e.y), to_mm(tr.GetWidth())))

    removed = [tr for tr in board.GetTracks() if tr.GetNetCode() == nc]
    for tr in removed:
        board.Remove(tr)
    print("removed", len(removed), "items for", net_name)

    def hole_to_hole_ok(x, y):
        r_new = VIA_DRILL / 2.0
        for hx, hy, hr in existing_holes:
            d = ((hx - x) ** 2 + (hy - y) ** 2) ** 0.5
            if d < r_new + hr + HOLE_TO_HOLE_MIN:
                return False
        for vx, vy in placed_vias:
            d = ((vx - x) ** 2 + (vy - y) ** 2) ** 0.5
            if d < r_new + r_new + HOLE_TO_HOLE_MIN:
                return False
        return True

    def find_existing_via(x, y, tol=0.05):
        for vx, vy in placed_vias:
            if abs(vx - x) < tol and abs(vy - y) < tol:
                return (vx, vy)
        return None

    def new_grid(): return [[False] * NY for _ in range(NX)]

    def mark(g, x, y, rad):
        # CORRECTIF (trouve en diagnostiquant une violation de clearance
        # residuelle a 0.115-0.17mm apparue quand une reroute est tombee
        # sur la marge de repli la plus stricte, HARD_FLOOR, sans aucun
        # tampon) : cx, cy = gx(x), gy(y) arrondit le CENTRE du cercle a la
        # case de grille la plus proche AVANT de calculer les distances --
        # ce qui decale le cercle obstacle de jusqu'a RES/2 (~0.1mm) par
        # rapport a la vraie position de la pastille. A une marge genereuse
        # ce decalage est absorbe sans consequence, mais a la marge la plus
        # stricte il suffit a faire passer une piste plus pres du bord reel
        # de la pastille que prevu. Corrige : la distance est maintenant
        # calculee depuis la position REELLE (x, y) jusqu'a la coordonnee
        # reelle de chaque case (i*RES, j*RES), sans jamais arrondir le
        # centre du cercle.
        rc = int(rad / RES) + 1
        cx, cy = gx(x), gy(y)
        for di in range(-rc, rc + 1):
            for dj in range(-rc, rc + 1):
                i, j = cx + di, cy + dj
                if 0 <= i < NX and 0 <= j < NY:
                    ddx = i * RES - x
                    ddy = j * RES - y
                    if ddx * ddx + ddy * ddy <= rad * rad:
                        g[i][j] = True

    def build_grids(margin):
        # meme correctif que route_grid_compact5.py : une via (rayon
        # VIA_SIZE/2=0.4mm) est bien plus large qu'une demi-piste
        # (TRACK_W/2=0.175mm) -- utiliser la meme marge pour tracer une
        # piste et pour placer une via sous-dimensionne le clearance reel
        # autour des vias (viole le seuil de 0.2mm pres des pads d'un
        # autre net). On construit donc deux jeux de grilles : gF/gB pour
        # les pistes, gFv/gBv (marge elargie) pour le placement des vias.
        via_margin = max(margin, CLEAR + VIA_SIZE / 2.0)
        gF, gB = new_grid(), new_grid()
        gFv, gBv = new_grid(), new_grid()
        for ncc, x, y, r, layers in all_pads:
            if ncc == nc and ncc != 0:
                continue
            if 0 in layers:
                mark(gF, x, y, r + margin)
                mark(gFv, x, y, r + via_margin)
            if 1 in layers:
                mark(gB, x, y, r + margin)
                mark(gBv, x, y, r + via_margin)
        for t in tracks:
            if t[0] == 'via':
                _, ncc, x, y, w = t
                if ncc == nc and ncc != 0:
                    continue
                mark(gF, x, y, w / 2.0 + margin); mark(gB, x, y, w / 2.0 + margin)
                mark(gFv, x, y, w / 2.0 + via_margin); mark(gBv, x, y, w / 2.0 + via_margin)
            else:
                _, ncc, layer, x1, y1, x2, y2, w = t
                if ncc == nc and ncc != 0:
                    continue
                length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                steps = max(1, int(length / (RES / 2)))
                g = gF if layer == 0 else gB
                gv = gFv if layer == 0 else gBv
                for k in range(steps + 1):
                    t2 = k / steps
                    mark(g, x1 + (x2 - x1) * t2, y1 + (y2 - y1) * t2, w / 2.0 + margin)
                    mark(gv, x1 + (x2 - x1) * t2, y1 + (y2 - y1) * t2, w / 2.0 + via_margin)
        # CORRECTIF (trouve via le DRC officiel -- copper_edge_clearance) :
        # cette marge etait de 0.3mm, sous le seuil reel de 0.5mm exige par
        # les regles du PCB (contour Edge.Cuts).
        #
        # DEUXIEME CORRECTIF, plus subtil (trouve en re-verifiant apres la
        # premiere reroute) : cette bordure ne bloquait que le CENTRE de la
        # case de grille -- elle ne tenait pas compte du rayon propre de ce
        # qui est place a ce centre. Pour une piste, le cuivre reel depasse
        # le centre de TRACK_W/2 ; pour une via, de VIA_SIZE/2 (0.4mm, bien
        # plus que la demi-largeur d'une piste). Avec une seule marge de
        # 0.65mm pour les deux, un via ARRIVAIT a se placer a 0.75mm du
        # bord (autorise), mais son propre corps (rayon 0.4mm) ne laissait
        # alors que 0.35mm de clearance reel -- sous le seuil de 0.5mm.
        # Corrige : deux marges de bordure distinctes, chacune calculee
        # avec un plafond (math.ceil, jamais un troncage) pour garantir le
        # clearance reel demande, quel que soit l'arrondi de grille :
        #   - pistes (gF/gB)   : 0.5mm + demi-largeur piste
        #   - vias   (gFv/gBv) : 0.5mm + rayon de la via
        EDGE_CLEARANCE_REQUIRED = 0.5
        mc_track = math.ceil((EDGE_CLEARANCE_REQUIRED + TRACK_W / 2.0) / RES)
        mc_via = math.ceil((EDGE_CLEARANCE_REQUIRED + VIA_SIZE / 2.0) / RES)
        for i in range(NX):
            for j in range(NY):
                if i < mc_track or j < mc_track or i >= NX - mc_track or j >= NY - mc_track:
                    gF[i][j] = True; gB[i][j] = True
                if i < mc_via or j < mc_via or i >= NX - mc_via or j >= NY - mc_via:
                    gFv[i][j] = True; gBv[i][j] = True
        return gF, gB, gFv, gBv

    def route2(gF, gB, gFv, gBv, a, b, end_layers, used):
        grids = [gF, gB]
        vgrids = [gFv, gBv]

        def blocked(i, j, l):
            if i < 0 or i >= NX or j < 0 or j >= NY:
                return True
            if grids[l][i][j] and not used[l][i][j]:
                return True
            return False

        def blocked_via(i, j, l):
            if i < 0 or i >= NX or j < 0 or j >= NY:
                return True
            if vgrids[l][i][j] and not used[l][i][j]:
                return True
            return False

        start = (gx(a[0]), gy(a[1]), 0)
        ei, ej = gx(b[0]), gy(b[1])
        dist = {start: 0}; prev = {}
        pq = [(0, start)]
        VIA_COST = 80
        while pq:
            d, (i, j, l) = heapq.heappop(pq)
            if d > dist.get((i, j, l), 1 << 30):
                continue
            if (i, j) == (ei, ej) and l in end_layers:
                path = [(i, j, l)]
                node = (i, j, l)
                while node in prev:
                    node = prev[node]
                    path.append(node)
                path.reverse()
                return path
            for di, dj, sc in ((1, 0, 10), (-1, 0, 10), (0, 1, 10), (0, -1, 10),
                               (1, 1, 14), (1, -1, 14), (-1, 1, 14), (-1, -1, 14)):
                ni, nj = i + di, j + dj
                if blocked(ni, nj, l):
                    continue
                if di != 0 and dj != 0 and (blocked(i + di, j, l) or blocked(i, j + dj, l)):
                    continue
                nd = d + sc
                key = (ni, nj, l)
                if nd < dist.get(key, 1 << 30):
                    dist[key] = nd; prev[key] = (i, j, l); heapq.heappush(pq, (nd, key))
            ol = 1 - l
            if not blocked(i, j, ol) and not blocked_via(i, j, l) and not blocked_via(i, j, ol):
                xmm, ymm = mmx(i), mmy(j)
                if find_existing_via(xmm, ymm) is None and not hole_to_hole_ok(xmm, ymm):
                    pass
                else:
                    nd = d + VIA_COST
                    key = (i, j, ol)
                    if nd < dist.get(key, 1 << 30):
                        dist[key] = nd; prev[key] = (i, j, l); heapq.heappush(pq, (nd, key))
        return None

    def emit_segment(pts_mm, layer, net):
        if len(pts_mm) < 2:
            return
        simplified = [pts_mm[0]]
        for k in range(1, len(pts_mm) - 1):
            x0, y0 = pts_mm[k - 1]; x1, y1 = pts_mm[k]; x2, y2 = pts_mm[k + 1]
            d1 = (round(x1 - x0, 4), round(y1 - y0, 4))
            d2 = (round(x2 - x1, 4), round(y2 - y1, 4))
            if d1 != d2:
                simplified.append(pts_mm[k])
        simplified.append(pts_mm[-1])
        layer_id = pcbnew.F_Cu if layer == 0 else pcbnew.B_Cu
        for a, b in zip(simplified, simplified[1:]):
            if a == b:
                continue
            tr = pcbnew.PCB_TRACK(board)
            tr.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
            tr.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
            tr.SetWidth(MM(TRACK_W))
            tr.SetLayer(layer_id)
            tr.SetNet(net)
            board.Add(tr)

    def emit_path(path, net, exact_start, exact_end):
        # CORRECTIF (meme bug que route_grid_compact5.py, trouve via
        # check_holes.py) : un via ne doit JAMAIS etre deplace vers la
        # position exacte d'une pastille -- il reste a sa position de
        # grille validee par hole_to_hole_ok ; seule l'extremite de piste
        # qui touche reellement la pastille est ajustee (au besoin via un
        # petit segment supplementaire entre le via et la pastille).
        grid_pts = [(mmx(i), mmy(j)) for i, j, l in path]
        layers = [l for i, j, l in path]

        segments = []
        seg = [grid_pts[0]]
        cur_layer = layers[0]
        for k in range(1, len(grid_pts)):
            if layers[k] != cur_layer:
                segments.append((cur_layer, seg))
                vx, vy = seg[-1]
                if find_existing_via(vx, vy) is None:
                    via = pcbnew.PCB_VIA(board)
                    via.SetPosition(pcbnew.VECTOR2I(MM(vx), MM(vy)))
                    via.SetDrill(MM(VIA_DRILL))
                    via.SetWidth(MM(VIA_SIZE))
                    via.SetNet(net)
                    board.Add(via)
                    placed_vias.append((vx, vy))
                cur_layer = layers[k]
                seg = [(vx, vy), grid_pts[k]]
            else:
                seg.append(grid_pts[k])
        segments.append((cur_layer, seg))

        first_layer, first_pts = segments[0]
        if len(first_pts) == 1:
            segments[0] = (first_layer, [exact_start, first_pts[0]])
        else:
            first_pts[0] = exact_start
        last_layer, last_pts = segments[-1]
        if len(last_pts) == 1:
            segments[-1] = (last_layer, [last_pts[0], exact_end])
        else:
            last_pts[-1] = exact_end

        for layer, pts in segments:
            emit_segment(pts, layer, net)

    # pastilles du net (position -> couches disponibles), pour connaitre les
    # end_layers de chaque point de la chaine
    pad_layers_by_xy = {}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() != nc:
                continue
            pos = p.GetPosition()
            x, y = to_mm(pos.x), to_mm(pos.y)
            layers = set()
            if p.IsOnLayer(pcbnew.F_Cu):
                layers.add(0)
            if p.IsOnLayer(pcbnew.B_Cu):
                layers.add(1)
            pad_layers_by_xy[(round(x, 4), round(y, 4))] = layers

    def layers_for(pt):
        key = (round(pt[0], 4), round(pt[1], 4))
        return pad_layers_by_xy.get(key, {0, 1})

    all_ok = True
    used = [new_grid(), new_grid()]
    for a, b in zip(chain, chain[1:]):
        ok = False
        b_layers = layers_for(b)
        for m in FALLBACK_MARGINS:
            gF, gB, gFv, gBv = build_grids(m)
            path = route2(gF, gB, gFv, gBv, a, b, b_layers, used)
            if path is not None:
                emit_path(path, net, exact_start=a, exact_end=b)
                print("routed", a, "->", b, "margin", round(m, 3))
                ok = True
                break
        if not ok:
            print("FAILED", a, b)
            all_ok = False

    board.SetFileName(BOARD_FILE)
    pcbnew.SaveBoard(BOARD_FILE, board)
    print("saved,", net_name, "done, all_ok=", all_ok)
    return all_ok


if __name__ == "__main__":
    pass
