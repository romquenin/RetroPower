#!/usr/bin/env python3
"""
RetroPower - version INTEGREE : le module ESP32-C3-Zero (Waveshare, 18
broches castellees, pas 2.54mm) est soude DIRECTEMENT sur le PCB (plus de
J1 ni de fils volants vers l'ESP32). Carte allongee de 23.5mm sur la
gauche pour l'accueillir, module tourne a 90 deg (USB-C vers la droite,
antenne vers la gauche -- le nouveau bord exterieur de la carte, le plus
degage possible de tout cuivre/metal).

Tout le reste (K1, Q1/Q2, D1-D3, R1-R4, C1/C2, J2-J6) est repris a
l'identique de RetroPower_Compact_v3 (version finalisee, DRC 0/0), juste
decale de +23.5mm en X pour laisser la place au module.

ATTENTION -- ecartement des 2 rangees de broches du module : la fiche
Waveshare ne donne que la largeur totale du module (18mm), pas la cote
exacte entre les deux rangees une fois les broches soudees sur les
demi-trous. ROW_SPACING ci-dessous est une estimation (18.0mm, la
largeur du module) -- A VERIFIER par un essai d'ajustement physique
(souder la barrette sur le module, mesurer l'ecartement reel des deux
rangees au pied a coulisse) avant la soudure definitive sur la carte.
"""
import pcbnew

MM = pcbnew.FromMM
FP_LIB = "/usr/share/kicad/footprints"

board = pcbnew.BOARD()

net_names = [
    "3V3", "GND",
    "SET_CTRL", "RESET_CTRL", "SENSE",
    "Q1_GATE", "Q2_GATE",
    "COIL_SET_B", "COIL_RESET_B",
    "SW_COM", "SW_NC", "SW_NO",
    "SW2_COM", "SW2_NC", "SW2_NO",
    "RAW_IN", "SENSE_TAP", "SENSE_MID",
]
nets = {}
for n in net_names:
    ni = pcbnew.NETINFO_ITEM(board, n)
    board.Add(ni)
    nets[n] = ni

def load_fp(lib, name):
    fp = pcbnew.FootprintLoad(f"{FP_LIB}/{lib}", name)
    if fp is None:
        raise RuntimeError(f"Footprint not found: {lib}/{name}")
    board.Add(fp)
    return fp

# Decalage global applique a tous les placements, pour resserrer le contour
# de la carte au plus juste autour des pastilles (calcule apres une premiere
# passe de placement : voir le calcul de bounding-box fait separement).
OFFSET_X = -0.875
OFFSET_Y = -0.025

def place(fp, x_mm, y_mm, rot_deg=0):
    fp.SetPosition(pcbnew.VECTOR2I(MM(x_mm + OFFSET_X), MM(y_mm + OFFSET_Y)))
    if rot_deg:
        fp.SetOrientationDegrees(rot_deg)

def pad(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == str(num):
            return p
    raise RuntimeError(f"pad {num} not found on {fp.GetReference()}")

def connect(fp, num, netname):
    p = pad(fp, num)
    p.SetNet(nets[netname])
    return p

# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

# K1 - relais Hongfa, DIP-16 (inchangé, pas d'alternative CMS)
K1 = load_fp("Package_DIP.pretty", "DIP-16_W7.62mm")
K1.SetReference("K1"); K1.SetValue("HFD2/003-M-L2-D")
# NOTE REPOSITIONNEMENT : K1/Q1/Q2/D2/C1/C2/J2/J4/J5/J6 utilisent maintenant
# un decalage EXT=12.885mm (au lieu de 23.5mm) -- U1, beaucoup plus compact
# en hauteur depuis la correction de ROW_SPACING, n'a plus besoin d'une
# bande pleine largeur sur toute la hauteur de la carte : seul K1 doit
# degager le bord droit de U1 en X (K1 et J3/D3/D1 restent chevauches en X
# mais separes en Y, exactement comme dans la disposition d'origine deja
# validee par le DRC). Carte raccourcie de 63.95mm a 53.335mm.
place(K1, 26.885, 7)
connect(K1, 1, "3V3")
connect(K1, 2, "3V3")
connect(K1, 16, "COIL_SET_B")
connect(K1, 15, "COIL_RESET_B")
connect(K1, 4, "SW_COM")
connect(K1, 6, "SW_NC")
connect(K1, 8, "SW_NO")
connect(K1, 13, "SW2_COM")
connect(K1, 11, "SW2_NC")
connect(K1, 9, "SW2_NO")

# Q1/Q2 - AO3400A SOT-23 (deja CMS)
Q1 = load_fp("Package_TO_SOT_SMD.pretty", "SOT-23")
Q1.SetReference("Q1"); Q1.SetValue("AO3400A")
place(Q1, 38.885, 9, rot_deg=90)
connect(Q1, 2, "GND")
connect(Q1, 3, "COIL_SET_B")
connect(Q1, 1, "Q1_GATE")

Q2 = load_fp("Package_TO_SOT_SMD.pretty", "SOT-23")
Q2.SetReference("Q2"); Q2.SetValue("AO3400A")
place(Q2, 38.885, 21, rot_deg=90)
connect(Q2, 2, "GND")
connect(Q2, 3, "COIL_RESET_B")
connect(Q2, 1, "Q2_GATE")

# D1/D2 - 1N4148WS (SOD-123, equivalent CMS du 1N4148 THT)
# pad1 = Anode, pad2 = Cathode (verifie sur le symbole F.Fab de l'empreinte)
# (CMS uniquement -- pas de double empreinte traversante : ca faisait
# grossir la carte pour rien, tu commandes des diodes CMS)
D1 = load_fp("Diode_SMD.pretty", "D_SOD-123")
D1.SetReference("D1"); D1.SetValue("1N4148WS (SOD-123)")
# D1/D3/J3/R1 : decalage individuel (18.885mm) superieur a celui du reste
# de la carte (12.885mm) -- ils doivent degager U1 en X, contrainte plus
# stricte que K1 (leur rangee Y=3.35-4 est tres proche du bord superieur,
# juste au-dessus de U1). Restent groupes entre eux exactement comme avant
# (memes ecarts relatifs), simplement toute la ligne recule vers la droite.
place(D1, 42.885, 4, rot_deg=0)
connect(D1, 2, "3V3")
connect(D1, 1, "COIL_SET_B")

D2 = load_fp("Diode_SMD.pretty", "D_SOD-123")
D2.SetReference("D2"); D2.SetValue("1N4148WS (SOD-123)")
# decalee vers le bas (27 -> 28.5) : le vrai DRC KiCad a trouve un
# chevauchement reel (0.000mm) entre le corps de D2 et la zone
# d'occupation (courtyard) de K1 -- le footprint DIP-16 standard utilise
# pour K1 a un corps bien plus long (~21mm) que le relais reel, et son
# bord bas venait justement taper dans D2. Ce decalage degage une vraie
# marge (~1mm) sans toucher au reste de la disposition.
place(D2, 36.885, 28.5, rot_deg=0)
connect(D2, 2, "3V3")
connect(D2, 1, "COIL_RESET_B")

# D3 - equivalent CMS du 1N5819 (SOD-123, ex: 1N5819WS)
# (remontee en haut, sur la meme ligne que D1/R1, a droite de J3)
#
# CORRECTIF CRITIQUE (trouve en recomparant ce PCB au schema valide
# d'origine) : D3 etait cablee par erreur en copiant le meme motif que
# D1/D2 (cathode vers 3V3) -- correct pour D1/D2 (diodes de roue libre
# sur une bobine de relais deja a 3.3V), mais DANGEREUX ici : RAW_IN est
# le 12V brut de la console, pas 3.3V. Avec la cathode sur 3V3, la diode
# aurait ete polarisee en direct EN PERMANENCE (12V > 3.3V), deversant le
# 12V brut (moins ~0.3V) directement sur le rail 3.3V regule -- ce qui
# aurait grille l'ESP32 des la mise sous tension. Corrige : la cathode va
# maintenant sur GND, ce qui en fait une diode de protection anti-
# inversion de polarite classique (bloquante/transparente en
# fonctionnement normal, ne conduit que si RAW_IN est branche a l'envers).
D3 = load_fp("Diode_SMD.pretty", "D_SOD-123")
D3.SetReference("D3"); D3.SetValue("1N5819WS (SOD-123)")
place(D3, 37.845, 4, rot_deg=0)
connect(D3, 2, "GND")
connect(D3, 1, "RAW_IN")

# R1/R2 - resistances serie grille (100R, valeur validee en vrai sur la SNES),
# R3/R4 - pulldown (10k, egalement validee), en 0805
R1 = load_fp("Resistor_SMD.pretty", "R_0805_2012Metric")
R1.SetReference("R1"); R1.SetValue("100R")
place(R1, 49.885, 4, rot_deg=90)  # aligne sur la meme ligne que D1
connect(R1, 1, "SET_CTRL")
connect(R1, 2, "Q1_GATE")

R3 = load_fp("Resistor_SMD.pretty", "R_0805_2012Metric")
R3.SetReference("R3"); R3.SetValue("10k")
place(R3, 43.885, 12, rot_deg=90)
connect(R3, 1, "Q1_GATE")
connect(R3, 2, "GND")

R2 = load_fp("Resistor_SMD.pretty", "R_0805_2012Metric")
R2.SetReference("R2"); R2.SetValue("100R")
place(R2, 43.885, 18, rot_deg=90)
connect(R2, 1, "RESET_CTRL")
connect(R2, 2, "Q2_GATE")

R4 = load_fp("Resistor_SMD.pretty", "R_0805_2012Metric")
R4.SetReference("R4"); R4.SetValue("10k")
place(R4, 43.885, 27, rot_deg=90)
connect(R4, 1, "Q2_GATE")
connect(R4, 2, "GND")

# C1 - CMS uniquement (le traversant C1' est supprime : il faisait grossir
# la carte pour rien, cf. demande). Decale sur la droite pour degager le
# coin bas-gauche (ou vont maintenant D3/J3).
C1_SMD = load_fp("Capacitor_SMD.pretty", "CP_Elec_6.3x5.4")
C1_SMD.SetReference("C1"); C1_SMD.SetValue("100uF/16V (CMS)")
place(C1_SMD, 20.085, 23.4, rot_deg=0)  # bord droit aligne sur celui de U1
connect(C1_SMD, 1, "3V3")
connect(C1_SMD, 2, "GND")

C2 = load_fp("Capacitor_SMD.pretty", "C_0805_2012Metric")
C2.SetReference("C2"); C2.SetValue("100nF")
place(C2, 28.885, 28, rot_deg=0)
connect(C2, 1, "3V3")
connect(C2, 2, "GND")

# (pas de pont diviseur R5/R6 -- inutile, POWER_SENSE est toujours tape sur
# un point deja a 3.3V, jamais directement sur du 5V+ brut)

# ---------------------------------------------------------------------------
# U1 -- Module ESP32-C3-Zero (Waveshare), SOUDE DIRECTEMENT (plus de J1 /
# fils volants). 18 broches castellees, pas 2.54mm, 9 par rangee.
#
# Module tourne a 90 deg par rapport a sa photo (USB-C normalement en
# haut) : ici USB-C pointe vers la DROITE (vers K1/le reste de la carte)
# et l'antenne se retrouve vers la GAUCHE, sur le nouveau bord exterieur
# de la carte -- le plus degage possible de tout cuivre/metal, comme
# demande.
#
# MONTAGE AU DOS DU PCB (et non pas cote composants) -- decide apres
# discussion sur l'orientation des broches. La photo officielle Waveshare
# qui donne le detail des broches (5V/GND/3V3/GP0../GP21) est une vue DE
# DOS du module (le cote oppose aux boutons BOOT/RESET et a la puce). Deux
# montages sont possibles :
#   - cote composants du module vers le haut (meme cote que K1, Q1...) :
#     il aurait fallu MIROITER cette vue de dos avant de placer les
#     pastilles (rangees inversees par rapport a ce qui suit).
#   - cote composants du module vers le BAS (soude au dos du PCB, cote
#     pistes) : la vue de dos peut etre utilisee TELLE QUELLE, sans miroir
#     -- c'est ce choix qui a ete fait ici. Avantage supplementaire : le
#     cote face-composants du PCB reste totalement degage sous l'antenne
#     (aucune piste ni pastille d'un autre composant a proximite), pour la
#     meilleure isolation RF possible.
# Brochage officiel Waveshare, vue de dos (cote 1, broches 1-9,
# "5V/GND/3V3/GP0../GP5", et cote 2, broches 10-18, "GP6../GP10../GP21") --
# une fois le module tourne a 90 deg (USB-C vers la droite), pris TEL QUEL
# (vue de dos, sans miroir -- coherent avec un montage au dos du PCB) :
#   rangee HAUT (broches 10->18)  : GP6 GP7 GP8 GP9 GP10 GP18 GP19 GP20 GP21
#   rangee BAS  (broches 9->1)    : GP5 GP4 GP3 GP2 GP1  GP0  3V3  GND  5V
#
# Broche 1 (5V, coin bas-droit, pres de l'USB-C) marquee par une pastille
# carree -- meme convention que tous les autres connecteurs de la carte.
#
# Pas de serigraphie au dos (evite un cout supplementaire JLCPCB) : U1 n'a
# ni contour ni texte sur B.SilkS. A la place, une note est imprimee sur la
# serigraphie AVANT (F.SilkS), pres de l'emplacement de U1, indiquant que
# le module se monte au dos (voir plus bas, apres la creation des pastilles).
#
# Alimentation : le buck 3.3V externe (net 3V3) est injecte directement
# sur la broche 3 ("3V3(OUT)" -- en realite la sortie du regulateur LDO
# embarque du module). C'est la methode standard et largement utilisee
# sur ce type de carte pour l'alimenter SANS passer par l'USB : on laisse
# la broche 5V (broche 1) non connectee. C'est exactement ce que faisait
# deja J1 sur la version precedente (fils volants 3V3/GND directement sur
# le module ESP32), donc aucun changement electrique -- seulement la
# methode de fixation qui change (soude au lieu de colle+fils volants).
U1 = pcbnew.FOOTPRINT(board)
U1.SetReference("U1")
U1.SetValue("ESP32-C3-Zero (Waveshare, 18br. 2.54mm)")
board.Add(U1)

ROW_SPACING = 15.24   # CORRIGE (etait 18.0, base sur la largeur totale du
# corps -- trop grand). Mesure par le client via superposition Photoshop a
# l'echelle (calibree sur le pas 2.54mm horizontal, verifiee croisee avec
# l'empreinte de K1) : ecart reel mesure ~15.43mm, tres proche de 15.24mm =
# 6 x 2.54mm (valeur "ronde" sur la meme grille que le pas horizontal,
# probablement la vraie cote constructeur). Utilise 15.24mm -- COMME
# TOUJOURS, A CONFIRMER par mesure directe une fois le PCB recu (nouvelle
# superposition Photoshop prevue par le client).
PIN_PITCH = 2.54
U1_X0 = 3.0           # broche la plus a gauche (cote antenne) de chaque rangee
U1_TOP_Y = 2.25        # rangee du haut (broches 10-18) -- remontee pres du
                       # bord superieur pour loger U1 au-dessus de C1
U1_BOT_Y = U1_TOP_Y + ROW_SPACING  # rangee du bas (broches 1-9) = 17.49

# (numero physique du module) -> (nom du signal, pour les connect() plus bas)
U1_TOP_PINS = [10, 11, 12, 13, 14, 15, 16, 17, 18]   # GP6..GP10,GP18..GP21
U1_BOT_PINS = [9, 8, 7, 6, 5, 4, 3, 2, 1]             # GP5..GP0,3V3,GND,5V

def add_u1_pad(fp, number, x_mm, y_mm, square=False):
    p = pcbnew.PAD(fp)
    fp.Add(p)  # ajouter AVANT de fixer la position : Add() recalcule sinon
               # la position a partir de pos0 (0,0 par defaut) et ecrase
               # tout SetPosition() fait avant coup (bug trouve ici meme --
               # tous les pads se retrouvaient empiles en (0,0) sur le rendu)
    p.SetNumber(str(number))
    p.SetShape(pcbnew.PAD_SHAPE_RECT if square else pcbnew.PAD_SHAPE_CIRCLE)
    p.SetSize(pcbnew.VECTOR2I(MM(1.7), MM(1.7)))
    p.SetDrillSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0)))
    p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    p.SetLayerSet(pcbnew.PAD.PTHMask())
    pos = pcbnew.VECTOR2I(MM(x_mm + OFFSET_X), MM(y_mm + OFFSET_Y))
    p.SetPosition(pos)
    p.SetPos0(pos)  # sans ca, Position() est juste en cache memoire mais
                     # pos0 (utilise a la sauvegarde/serialisation) reste a
                     # (0,0) -- tous les pads se retrouvaient empiles a
                     # l'origine une fois le fichier relu (bug trouve ici,
                     # confirme par sauvegarde+relecture avant de continuer)
    return p

for i, num in enumerate(U1_TOP_PINS):
    add_u1_pad(U1, num, U1_X0 + i * PIN_PITCH, U1_TOP_Y)
for i, num in enumerate(U1_BOT_PINS):
    add_u1_pad(U1, num, U1_X0 + i * PIN_PITCH, U1_BOT_Y, square=(num == 1))

connect(U1, 3, "3V3")           # 3V3(OUT)
connect(U1, 2, "GND")
connect(U1, 4, "SENSE_MID")     # GP0
connect(U1, 7, "SET_CTRL")      # GP3
connect(U1, 14, "RESET_CTRL")   # GP10
# broches 1(5V), 5,6,8,9,10,11,12,13,15,16,17,18 : non utilisees, laissees
# sans net (5V volontairement -- alimentation directe par la broche 3).

# Contour indicatif du corps du module (Cmts.User, non fabrique) --
# 18mm (large, haut-bas) x 23.5mm (long, gauche-droite), pour verifier
# visuellement le degagement avec K1/J2/l'antenne avant de commander.
U1_BODY_X0 = U1_X0 - 1.59
U1_BODY_X1 = U1_X0 + 8 * PIN_PITCH + 1.59
U1_BODY_Y0 = U1_TOP_Y - 0.75
U1_BODY_Y1 = U1_BOT_Y + 0.75
u1_pts = [(U1_BODY_X0, U1_BODY_Y0), (U1_BODY_X1, U1_BODY_Y0),
          (U1_BODY_X1, U1_BODY_Y1), (U1_BODY_X0, U1_BODY_Y1), (U1_BODY_X0, U1_BODY_Y0)]
for i in range(len(u1_pts) - 1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(MM(u1_pts[i][0] + OFFSET_X), MM(u1_pts[i][1] + OFFSET_Y)))
    s.SetEnd(pcbnew.VECTOR2I(MM(u1_pts[i+1][0] + OFFSET_X), MM(u1_pts[i+1][1] + OFFSET_Y)))
    s.SetLayer(pcbnew.Cmts_User)
    s.SetWidth(MM(0.1))
    board.Add(s)
u1_txt = pcbnew.PCB_TEXT(board)
u1_txt.SetText("U1 corps indicatif -- USB-C -> / antenne <-")
u1_txt.SetPosition(pcbnew.VECTOR2I(MM(U1_BODY_X0 + 0.3 + OFFSET_X), MM(U1_BODY_Y0 - 1.0 + OFFSET_Y)))
u1_txt.SetLayer(pcbnew.Cmts_User)
u1_txt.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
u1_txt.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8)))
u1_txt.SetTextThickness(MM(0.1))
board.Add(u1_txt)

# Champs Reference/Valeur de U1 : jamais positionnes explicitement (footprint
# construite a la main, cf. plus haut) -- ils restaient par defaut a (0,0),
# c-a-d au coin superieur gauche du PCB, d'ou le texte tronque/moche vu sur
# le rendu JLCPCB (correspond aussi aux 3 avertissements silk_edge_clearance/
# silk_overlap du DRC officiel). Comme U1 se monte au DOS du PCB (pas de
# serigraphie au dos, cf. note plus haut), ces deux champs sont simplement
# masques plutot que repositionnes -- inutile de sortir une etiquette F.SilkS
# pour un composant qui n'est pas visible cote face avant une fois soude.
U1.Reference().SetVisible(False)
U1.Value().SetVisible(False)

# Note de montage sur la serigraphie AVANT (F.SilkS) -- U1 n'a pas de
# serigraphie a lui (pas de contour/texte au dos, cf. plus haut), donc
# rien n'indiquerait a l'assemblage qu'un composant se monte ici, de
# l'autre cote du PCB.
#
# CORRIGE (DRC officiel) : le premier essai (texte vertical de 0.6mm, dans
# l'etroit espace entre U1 et K1) violait la hauteur de texte minimale du
# PCB (0.8mm) ET debordait sur le masque de soudure de K1 -- cet espace
# est trop etroit (0.85mm) pour un texte, quelle que soit sa taille.
# Repositionne a l'horizontale, texte raccourci, dans l'espace degage
# SOUS U1 et AU-DESSUS de C1 (~1.585mm de haut, largement assez pour du
# 0.8mm) -- aucun autre composant n'occupe cette bande a cette hauteur.
u1_note = pcbnew.PCB_TEXT(board)
u1_note.SetText("U1 : MONTER AU DOS DU PCB")
u1_note.SetPosition(pcbnew.VECTOR2I(MM((U1_BODY_X0 + U1_BODY_X1) / 2 + OFFSET_X),
                                     MM(U1_BODY_Y1 + 0.79 + OFFSET_Y)))
u1_note.SetLayer(pcbnew.F_SilkS)
u1_note.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8)))
u1_note.SetTextThickness(MM(0.12))
u1_note.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
board.Add(u1_note)

J2 = load_fp("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x02_P2.54mm_Vertical")
J2.SetReference("J2"); J2.SetValue("Buck 3V3 OUT")
place(J2, 18.885, 29.4, rot_deg=90)  # sous C1, espacement minimal
connect(J2, 1, "3V3")
connect(J2, 2, "GND")

# (remontee en haut, au-dessus de J1, parallele a J2, sur la meme ligne
# que D1/R1 -- D3 est a sa droite)
J3 = load_fp("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x02_P2.54mm_Vertical")
J3.SetReference("J3"); J3.SetValue("Tap alim brute (vers buck)")
place(J3, 30.815, 3.35, rot_deg=90)
connect(J3, 1, "RAW_IN")
connect(J3, 2, "GND")

J4 = load_fp("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x03_P2.54mm_Vertical")
J4.SetReference("J4"); J4.SetValue("Switch console (pole 1)")
place(J4, 50.885, 8, rot_deg=0)
connect(J4, 1, "SW_COM")
connect(J4, 2, "SW_NC")
connect(J4, 3, "SW_NO")

J5 = load_fp("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x03_P2.54mm_Vertical")
J5.SetReference("J5"); J5.SetValue("Pole 2 relais (libre/reserve)")
place(J5, 50.885, 17, rot_deg=0)
connect(J5, 1, "SW2_COM")
connect(J5, 2, "SW2_NC")
connect(J5, 3, "SW2_NO")

J6 = load_fp("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x02_P2.54mm_Vertical")
J6.SetReference("J6"); J6.SetValue("POWER_SENSE tap console (deja 3.3V)")
place(J6, 50.885, 26, rot_deg=0)
connect(J6, 1, "SENSE_MID")  # branche directement, sans pont diviseur
connect(J6, 2, "GND")

# ---------------------------------------------------------------------------
# Corrections de serigraphie (silk_overlap / silk_over_copper trouves par
# le DRC officiel de KiCad) : sur une carte aussi dense, le placement PAR
# DEFAUT du champ "reference" (au-dessus de chaque empreinte) tombe parfois
# en plein sur le corps serigraphie d'un composant VOISIN. On deplace ici
# les quelques champs concernes vers un espace degage -- purement cosmetique
# (etiquette de designation), aucune incidence electrique.
def move_ref(fp, x_mm, y_mm):
    fp.Reference().SetPosition(pcbnew.VECTOR2I(MM(x_mm + OFFSET_X), MM(y_mm + OFFSET_Y)))

# K1 : son champ reference (par defaut au-dessus, pres de D3) chevauchait a
# la fois la serigraphie de D3 (en haut) et celle de C2 (en bas), a cause du
# corps tres allonge (~21mm) du footprint DIP-16 generique. Un premier essai
# (x=14.0, milieu du corps) etait en fait tombe EN PLEIN sur la colonne de
# pastilles broches 4/5 (x local ~14.0) -- le DRC l'a signale (silk_over_
# copper, "propre" pastille de K1). Repositionne au milieu du corps mais
# dans l'ESPACE ENTRE les deux colonnes de broches (x local ~17.8, aucune
# pastille a cet endroit), loin de D3 (en haut) et C2 (en bas).
move_ref(K1, 30.695, 16.0)

# C2 : chevauchait la serigraphie de K1 (juste au-dessus de C2). Deplace en
# dessous de C2, cote degage.
move_ref(C2, 28.885, 30.2)

# C1 : chevauchait la serigraphie de J1 (juste au-dessus de C1). Un premier
# essai (a droite de C1) tombait en fait EN PLEIN sur la propre pastille
# negative de C1 (le pas entre les deux pattes d'un condensateur CP_Elec
# est trop petit pour decaler la reference sur le cote) -- signale par le
# DRC (silk_over_copper). Repositionne EN DESSOUS de C1 (les deux pattes de
# C1 sont cote a cote a la meme hauteur, donc au-dessus/en-dessous est
# degage), avec une marge confortable avant J2.
move_ref(C1_SMD, 20.96, 26.0)

# J5 : chevauchait la serigraphie de J4 (juste au-dessus). Deplace a
# gauche du connecteur, cote degage vers R2.
# J4 : son champ reference par defaut chevauchait le corps de R1, puis (un
# premier correctif juste au-dessus de J4) le corps de J4 lui-meme. Plutot
# que de la masquer, on reprend le meme traitement que J5/J6 juste en
# dessous : etiquette a gauche du connecteur (meme decalage X=-3.4,
# Y=-0.4 par rapport au connecteur), dans le couloir degage entre la
# colonne R1-R4 et la colonne J4-J6.
move_ref(J4, 47.485, 7.6)

move_ref(J5, 47.485, 16.6)

# J6 : chevauchait la serigraphie de J5 (juste au-dessus). Deplace a
# gauche du connecteur, cote degage vers R4.
move_ref(J6, 47.485, 25.6)

# (pas de trous de fixation M2 -- pas necessaires, on gagne la place)
# (l'ancienne "Zone ESP32 (collage)" indicative n'a plus lieu d'etre : U1
# est maintenant une vraie empreinte soudee, avec son propre contour
# indicatif Cmts.User cree plus haut au moment de sa creation)

# ---------------------------------------------------------------------------
# Contour de la carte -- au plus juste, recalcule apres placement (voir plus bas)
# ---------------------------------------------------------------------------
W, H = 53.335, 32.75  # raccourci de 63.95 -- U1 compact (ROW_SPACING corrige)
                       # ne necessite plus la bande pleine largeur d'origine
seg_pts = [(0, 0), (W, 0), (W, H), (0, H), (0, 0)]
for i in range(len(seg_pts) - 1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(MM(seg_pts[i][0]), MM(seg_pts[i][1])))
    s.SetEnd(pcbnew.VECTOR2I(MM(seg_pts[i+1][0]), MM(seg_pts[i+1][1])))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(MM(0.15))
    board.Add(s)

board.SetFileName("/tmp/claude-0/-home-claude/70a7dc23-3f6a-5437-afc9-6d2c7c5f03dd/scratchpad/retropower_pcb/RetroPower_Integrated_unrouted.kicad_pcb")
pcbnew.SaveBoard(board.GetFileName(), board)
print("OK, unrouted integrated board saved")
print("Footprints:", len(list(board.GetFootprints())))
print("Board size:", W, "x", H, "mm")
