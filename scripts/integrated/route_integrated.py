#!/usr/bin/env python3
"""
Routeur maze (Lee) sur grille, 2 couches (F.Cu / B.Cu) avec vias.

v5 -- corrige deux bugs reels trouves par le DRC officiel de KiCad (le
"maison" check_clearance_v3b.py ne les detectait pas) :

1. BUG DE COUCHE D'ARRIVEE (cause de connexions ouvertes / "unconnected
   items") : la recherche BFS declarait un point "atteint" des que les
   coordonnees (i,j) correspondaient a la pastille cible, SANS verifier
   que la couche d'arrivee etait une couche ou cette pastille a du
   cuivre. Beaucoup de composants (R, C, D, Q -- tout le CMS) n'ont du
   cuivre que sur F.Cu (pastilles SMD) : si le chemin arrivait sur B.Cu
   "sous" la pastille sans via pour remonter sur F.Cu, KiCad voit une
   piste qui s'arrete dans le vide, pas une connexion. Corrige : le
   critere d'arrivee exige maintenant que la couche courante soit une
   couche ou la pastille cible a reellement du cuivre.

2. TROUS TROP PROCHES (hole_to_hole) : rien n'empechait deux vias (ou
   un via et une pastille percee) de se retrouver a quelques microns
   l'un de l'autre -- electriquement invisible pour mon verificateur de
   clearance (qui ne regarde que le cuivre), mais un vrai probleme de
   percage/fabrication. Corrige : un registre global de tous les trous
   deja perces (pastilles traversantes + vias, TOUS nets confondus, y
   compris le meme net) interdit maintenant de placer un via a moins de
   HOLE_TO_HOLE_MIN de n'importe quel autre trou existant.
"""
import pcbnew
import heapq

MM = pcbnew.FromMM
def to_mm(nm): return nm / 1e6

RES = 0.2            # pas de grille en mm
CLEAR = 0.20          # clearance minimum (cuivre)
TRACK_W = 0.35        # largeur de piste
VIA_DRILL = 0.4
VIA_SIZE = 0.8
HOLE_TO_HOLE_MIN = 0.30  # marge de securite (KiCad exige 0.2495mm reel -> on vise plus large)
OBSTACLE_MARGIN = CLEAR + TRACK_W / 2.0 + 0.2

UNROUTED = "RetroPower_Integrated_unrouted.kicad_pcb"
OUTFILE = "/tmp/claude-0/-home-claude/70a7dc23-3f6a-5437-afc9-6d2c7c5f03dd/scratchpad/retropower_pcb/RetroPower_Integrated.kicad_pcb"
W_MM, H_MM = 53.335, 32.75

board = pcbnew.LoadBoard(UNROUTED)

NX = int(W_MM / RES) + 1
NY = int(H_MM / RES) + 1

def gx(xmm): return int(round(xmm / RES))
def gy(ymm): return int(round(ymm / RES))
def mmx(i): return i * RES
def mmy(j): return j * RES

# ---------------------------------------------------------------------------
# Collect pads per net + registre global des trous (pastilles traversantes)
# ---------------------------------------------------------------------------
pads_by_net = {}
all_pads = []
existing_holes = []  # (x_mm, y_mm, hole_radius_mm) -- pastilles a trou uniquement

# CORRECTIF (trouve par le DRC officiel APRES cette premiere serie de
# correctifs) : plusieurs pastilles (pin1 des connecteurs/du relais,
# pastilles SMD 0805/SOD-123...) sont RECTANGULAIRES, pas circulaires.
# Approximer une pastille rectangulaire par un cercle INSCRIT (rayon =
# plus grand cote / 2) sous-estime son extension reelle le long de sa
# diagonale -- exactement les violations de clearance de 0.12-0.19mm que
# le DRC a trouvees (les checkers maison les manquaient pour la meme
# raison). Corrige : pour ces formes, le routeur utilise le cercle
# CIRCONSCRIT (demi-diagonale) comme obstacle -- toujours sur quelle que
# soit la rotation de la pastille, meme si legerement pessimiste.
RECT_SHAPES = {pcbnew.PAD_SHAPE_RECT, pcbnew.PAD_SHAPE_TRAPEZOID,
               pcbnew.PAD_SHAPE_ROUNDRECT, pcbnew.PAD_SHAPE_CHAMFERED_RECT}

def pad_radius_mm(p):
    size = p.GetSize()
    w, h = to_mm(size.x), to_mm(size.y)
    if p.GetShape() in RECT_SHAPES:
        return ((w / 2.0) ** 2 + (h / 2.0) ** 2) ** 0.5
    return max(w, h) / 2.0

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
        nc = p.GetNetCode()
        entry = (to_mm(pos.x), to_mm(pos.y), r, layers, f"{ref}.{p.GetNumber()}")
        all_pads.append((nc, entry))
        pads_by_net.setdefault(nc, []).append(entry)
        drill = p.GetDrillSize()
        if drill.x > 0:
            existing_holes.append((to_mm(pos.x), to_mm(pos.y), to_mm(drill.x) / 2.0))

# vias places pendant ce run -- alimente au fur et a mesure, verifie pour
# TOUS les nets (y compris le meme net que celui en cours de routage)
placed_vias = []  # (x_mm, y_mm)

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

def new_grid():
    return [[False] * NY for _ in range(NX)]

def mark_circle_obstacle(grid, xmm, ymm, rad_mm):
    # CORRECTIF (meme bug que dans fix_net2.py -- trouve en diagnostiquant
    # une violation de clearance residuelle apres une reroute au fallback
    # de marge le plus strict) : cx, cy = gx(xmm), gy(ymm) arrondissait le
    # centre du cercle a la case de grille la plus proche AVANT de calculer
    # les distances, decalant l'obstacle de jusqu'a RES/2 (~0.1mm) par
    # rapport a la vraie position de la pastille -- absorbe sans risque a
    # marge large, mais pas a marge stricte. Corrige : distance calculee
    # depuis la position REELLE (xmm, ymm), jamais depuis un centre arrondi.
    r_cells = int(rad_mm / RES) + 1
    cx, cy = gx(xmm), gy(ymm)
    for di in range(-r_cells, r_cells + 1):
        for dj in range(-r_cells, r_cells + 1):
            i, j = cx + di, cy + dj
            if 0 <= i < NX and 0 <= j < NY:
                ddx = i * RES - xmm
                ddy = j * RES - ymm
                if ddx * ddx + ddy * ddy <= rad_mm ** 2:
                    grid[i][j] = True

def mark_edge_obstacles(gF, gB):
    margin_cells = int(1.0 / RES)
    for i in range(NX):
        for j in range(NY):
            if i < margin_cells or j < margin_cells or i >= NX - margin_cells or j >= NY - margin_cells:
                gF[i][j] = True
                gB[i][j] = True

def build_base_obstacles_with_margin(exclude_net, margin):
    # CORRECTIF #3 (trouve en verifiant le clearance APRES coup) : une via
    # a un rayon de VIA_SIZE/2=0.4mm, bien plus large que le demi-largeur
    # d'une piste (TRACK_W/2=0.175mm). Utiliser la MEME marge pour placer
    # une via que pour tracer une piste ne garantit le clearance CLEAR que
    # pour une piste -- une via placee au ras de cette meme limite se
    # retrouve avec un clearance reel de seulement (margin - VIA_SIZE/2),
    # soit ~0.13-0.19mm ici, sous le seuil de 0.2mm. On construit donc
    # AUSSI une grille d'obstacles dediee au placement des vias, avec une
    # marge elargie pour tenir compte du rayon de la via elle-meme.
    gF, gB = new_grid(), new_grid()
    gFv, gBv = new_grid(), new_grid()
    via_margin = max(margin, CLEAR + VIA_SIZE / 2.0)
    for nc2, (x, y, r, layers, name) in all_pads:
        if nc2 == exclude_net and nc2 != 0:
            continue
        rad = r + margin
        rad_v = r + via_margin
        if 0 in layers:
            mark_circle_obstacle(gF, x, y, rad)
            mark_circle_obstacle(gFv, x, y, rad_v)
        if 1 in layers:
            mark_circle_obstacle(gB, x, y, rad)
            mark_circle_obstacle(gBv, x, y, rad_v)
    return gF, gB, gFv, gBv

# ---------------------------------------------------------------------------
# BFS avec verification de la couche d'arrivee + hole-to-hole sur les vias
# ---------------------------------------------------------------------------
def route_two_points(gF, gB, gFv, gBv, start_mm, end_mm, end_layers, used):
    grids = [gF, gB]
    vgrids = [gFv, gBv]
    si, sj = gx(start_mm[0]), gy(start_mm[1])
    ei, ej = gx(end_mm[0]), gy(end_mm[1])
    si = min(max(si, 0), NX - 1); sj = min(max(sj, 0), NY - 1)
    ei = min(max(ei, 0), NX - 1); ej = min(max(ej, 0), NY - 1)

    def blocked(i, j, layer):
        if i < 0 or i >= NX or j < 0 or j >= NY:
            return True
        if grids[layer][i][j] and not used[layer][i][j]:
            return True
        return False

    def blocked_via(i, j, layer):
        if i < 0 or i >= NX or j < 0 or j >= NY:
            return True
        if vgrids[layer][i][j] and not used[layer][i][j]:
            return True
        return False

    start = (si, sj, 0)
    dist = {start: 0}
    prev = {}
    pq = [(0, start)]
    VIA_COST = 80
    while pq:
        d, (i, j, l) = heapq.heappop(pq)
        if d > dist.get((i, j, l), 1 << 30):
            continue
        # CORRECTIF #1 : n'accepte l'arrivee que si la pastille cible a du
        # cuivre sur la couche courante (sinon il faut un via en plus).
        if (i, j) == (ei, ej) and l in end_layers:
            return reconstruct(prev, (i, j, l)), l
        for di, dj, stepcost in ((1, 0, 10), (-1, 0, 10), (0, 1, 10), (0, -1, 10),
                                  (1, 1, 14), (1, -1, 14), (-1, 1, 14), (-1, -1, 14)):
            ni, nj = i + di, j + dj
            if blocked(ni, nj, l):
                continue
            if di != 0 and dj != 0:
                if blocked(i + di, j, l) or blocked(i, j + dj, l):
                    continue
            nd = d + stepcost
            key = (ni, nj, l)
            if nd < dist.get(key, 1 << 30):
                dist[key] = nd
                prev[key] = (i, j, l)
                heapq.heappush(pq, (nd, key))
        ol = 1 - l
        # CORRECTIF #3 : le trou lui-meme (couche d'arrivee ET couche de
        # depart) doit respecter la marge dediee aux vias, pas seulement
        # la marge d'une piste -- sinon la via peut finir trop pres d'un
        # pad d'un autre net (voir commentaire sur build_base_obstacles).
        if not blocked(i, j, ol) and not blocked_via(i, j, l) and not blocked_via(i, j, ol):
            # CORRECTIF #2 : un via ici n'est permis que si un trou existe
            # deja pile a cet endroit (on le reutilisera, pas de nouveau
            # perçage) OU si un nouveau trou y respecte l'espacement
            # trou-a-trou minimum vis-a-vis de TOUS les trous existants.
            xmm, ymm = mmx(i), mmy(j)
            if find_existing_via(xmm, ymm) is None and not hole_to_hole_ok(xmm, ymm):
                pass
            else:
                nd = d + VIA_COST
                key = (i, j, ol)
                if nd < dist.get(key, 1 << 30):
                    dist[key] = nd
                    prev[key] = (i, j, l)
                    heapq.heappush(pq, (nd, key))
    return None, None

def reconstruct(prev, node):
    path = [node]
    while node in prev:
        node = prev[node]
        path.append(node)
    path.reverse()
    return path

def mark_used(used, path, margin=None):
    m = (TRACK_W / 2.0 + CLEAR) if margin is None else margin
    r_cells = int(m / RES) + 1
    for (i, j, l) in path:
        for di in range(-r_cells, r_cells + 1):
            for dj in range(-r_cells, r_cells + 1):
                ni, nj = i + di, j + dj
                if 0 <= ni < NX and 0 <= nj < NY:
                    used[l][ni][nj] = True

def emit_segment(pts_mm, layer, net):
    """pts_mm: liste de (x_mm, y_mm) deja en coordonnees reelles (pas des
    indices de grille). Simplifie les points colineaires consecutifs."""
    if len(pts_mm) < 2:
        return
    simplified = [pts_mm[0]]
    for k in range(1, len(pts_mm) - 1):
        x0, y0 = pts_mm[k - 1]
        x1, y1 = pts_mm[k]
        x2, y2 = pts_mm[k + 1]
        d1 = (round(x1 - x0, 4), round(y1 - y0, 4))
        d2 = (round(x2 - x1, 4), round(y2 - y1, 4))
        # colineaire seulement si meme direction ET meme "pente" (produit
        # en croix nul) -- suffisant ici puisque les pas sont uniformes
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
    """Emet le chemin en pistes/vias.

    CORRECTIF (trouve APRES coup, via check_holes.py) : une version
    precedente ecrasait directement pts_mm[0]/pts_mm[-1] par la position
    EXACTE de la pastille avant de decouper en segments/vias. Si le tout
    premier (ou tout dernier) pas du chemin est justement un changement de
    couche, le via se retrouvait place A LA POSITION EXACTE DE LA PASTILLE
    plutot qu'a sa position de grille validee par hole_to_hole_ok pendant
    le BFS -- deux vias independants (l'un pour ce hop, l'un pour un hop
    voisin partageant presque le meme point) pouvaient alors atterrir a
    quelques centiemes de mm l'un de l'autre, sous le seuil hole_to_hole,
    sans que rien ne le revalide au moment de l'emission.
    Corrige : les vias restent TOUJOURS a leur position de grille (celle
    que le BFS a validee) ; seule l'extremite FINALE d'une piste (celle
    qui touche reellement la pastille) est ajustee a la position exacte,
    au besoin via un petit segment supplementaire entre le via et la
    pastille."""
    grid_pts = [(mmx(i), mmy(j)) for i, j, l in path]
    layers = [l for i, j, l in path]

    segments = []  # [(layer, [pts...]), ...] -- coordonnees de GRILLE
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

    # Ajuste l'extremite de DEPART a la position exacte de la pastille --
    # sans jamais deplacer un via, quitte a ajouter un point.
    first_layer, first_pts = segments[0]
    if len(first_pts) == 1:
        segments[0] = (first_layer, [exact_start, first_pts[0]])
    else:
        first_pts[0] = exact_start
    # Idem pour l'extremite d'ARRIVEE.
    last_layer, last_pts = segments[-1]
    if len(last_pts) == 1:
        segments[-1] = (last_layer, [last_pts[0], exact_end])
    else:
        last_pts[-1] = exact_end

    for layer, pts in segments:
        emit_segment(pts, layer, net)

# ---------------------------------------------------------------------------
# Ordonnancement des nets
# ---------------------------------------------------------------------------
def order_chain(pts):
    remaining = pts[1:]
    chain = [pts[0]]
    while remaining:
        last = chain[-1]
        remaining.sort(key=lambda p: (p[0] - last[0]) ** 2 + (p[1] - last[1]) ** 2)
        chain.append(remaining.pop(0))
    return chain

def net_priority(nc):
    net = board.FindNet(nc)
    name = net.GetNetname() if net else ""
    # COIL_SET_B / COIL_RESET_B relient K1 (bobines du relais) a des
    # composants situes aux deux extremites opposees de la carte -- ce
    # sont de longs trajets qui doivent traverser une zone dejà tres
    # dense pres de K1. Les router en meme temps que GND/3V3 (avant que
    # les autres nets ne s'approprient tout l'espace disponible) evite
    # de se retrouver, en fin de parcours, sans aucun chemin legal a
    # 0.2mm de clearance.
    prio = 0 if name in ("GND", "3V3", "COIL_SET_B", "COIL_RESET_B") else 1
    return (prio, len(pads_by_net[nc]))

net_order = sorted(pads_by_net.keys(), key=net_priority)
failed = []

committedF, committedB = new_grid(), new_grid()

def or_into(dst, src):
    for i in range(NX):
        di = dst[i]
        si = src[i]
        for j in range(NY):
            if si[j]:
                di[j] = True

# CORRECTIF (meme bug que celui deja corrige dans fix_net.py plus tot dans
# le projet, mais jamais reporte ici) : cette liste doit rester
# STRICTEMENT decroissante et ne jamais redescendre sous le plancher
# electrique reel (CLEAR + TRACK_W/2). L'ancienne liste retombait sur
# OBSTACLE_MARGIN*0.6 = 0.345mm, plus PETIT que le plancher 0.375mm : le
# routeur pouvait donc "reussir" en utilisant moins de marge que le
# minimum electrique garanti, produisant des pistes/vias a peine
# 0.12-0.19mm d'un pad d'un autre net -- sous le seuil de 0.2mm exige.
HARD_FLOOR = CLEAR + TRACK_W / 2.0
FLOOR = CLEAR + TRACK_W / 2.0 + RES / 2.0
FALLBACK_MARGINS = sorted({OBSTACLE_MARGIN, OBSTACLE_MARGIN * 0.75, FLOOR, HARD_FLOOR}, reverse=True)

for nc in net_order:
    if nc == 0:
        continue
    pts = pads_by_net[nc]
    if len(pts) < 2:
        continue
    net = board.FindNet(nc)
    used = [new_grid(), new_grid()]
    # chain d'après (x,y) mais on garde le lien vers les layers de chaque pad
    pts_by_xy = {(x, y): layers for x, y, r, layers, name in pts}
    chain = order_chain([(x, y) for x, y, r, layers, name in pts])
    net_paths = []
    for a, b in zip(chain, chain[1:]):
        b_layers = pts_by_xy[b]
        path = None
        for m in FALLBACK_MARGINS:
            gF, gB, gFv, gBv = build_base_obstacles_with_margin(nc, m)
            mark_edge_obstacles(gF, gB)
            mark_edge_obstacles(gFv, gBv)
            or_into(gF, committedF)
            or_into(gB, committedB)
            or_into(gFv, committedF)
            or_into(gBv, committedB)
            path, endlayer = route_two_points(gF, gB, gFv, gBv, a, b, b_layers, used)
            if path is not None:
                if m != OBSTACLE_MARGIN:
                    print(f"  (repli marge {m:.2f}mm pour {net.GetNetname()} {a}->{b})")
                break
        if path is None:
            failed.append((net.GetNetname(), a, b))
            continue
        mark_used(used, path)
        net_paths.append(path)
        emit_path(path, net, exact_start=a, exact_end=b)
    for path in net_paths:
        mark_used([committedF, committedB], path, margin=TRACK_W / 2.0 + OBSTACLE_MARGIN)

print("Nets en echec de routage:", len(failed))
for f in failed:
    print(" ", f)

board.SetFileName(OUTFILE)
pcbnew.SaveBoard(OUTFILE, board)
print("Saved:", OUTFILE)
print("Tracks:", len(list(board.GetTracks())))
