#!/usr/bin/env python3
"""
RetroPower - module central, version COMPACTE (CMS 0805 + SOD-123 + CP_Elec)
Meme netlist que RetroPower_Core, composants passifs en CMS pour reduire
la taille de la carte. K1 (relais) et les headers restent en traversant
(pas d'alternative CMS pour le relais ; les headers sont des points de
soudure de fils, mieux en traversant).
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
place(K1, 14, 7)
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
place(Q1, 26, 9, rot_deg=90)
connect(Q1, 2, "GND")
connect(Q1, 3, "COIL_SET_B")
connect(Q1, 1, "Q1_GATE")

Q2 = load_fp("Package_TO_SOT_SMD.pretty", "SOT-23")
Q2.SetReference("Q2"); Q2.SetValue("AO3400A")
place(Q2, 26, 21, rot_deg=90)
connect(Q2, 2, "GND")
connect(Q2, 3, "COIL_RESET_B")
connect(Q2, 1, "Q2_GATE")

# D1/D2 - 1N4148WS (SOD-123, equivalent CMS du 1N4148 THT)
# pad1 = Anode, pad2 = Cathode (verifie sur le symbole F.Fab de l'empreinte)
# (CMS uniquement -- pas de double empreinte traversante : ca faisait
# grossir la carte pour rien, tu commandes des diodes CMS)
D1 = load_fp("Diode_SMD.pretty", "D_SOD-123")
D1.SetReference("D1"); D1.SetValue("1N4148WS (SOD-123)")
place(D1, 24, 4, rot_deg=0)
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
place(D2, 24, 28.5, rot_deg=0)
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
place(D3, 18.96, 4, rot_deg=0)
connect(D3, 2, "GND")
connect(D3, 1, "RAW_IN")

# R1/R2 - resistances serie grille (100R, valeur validee en vrai sur la SNES),
# R3/R4 - pulldown (10k, egalement validee), en 0805
R1 = load_fp("Resistor_SMD.pretty", "R_0805_2012Metric")
R1.SetReference("R1"); R1.SetValue("100R")
place(R1, 31, 4, rot_deg=90)  # aligne sur la meme ligne que D1
connect(R1, 1, "SET_CTRL")
connect(R1, 2, "Q1_GATE")

R3 = load_fp("Resistor_SMD.pretty", "R_0805_2012Metric")
R3.SetReference("R3"); R3.SetValue("10k")
place(R3, 31, 12, rot_deg=90)
connect(R3, 1, "Q1_GATE")
connect(R3, 2, "GND")

R2 = load_fp("Resistor_SMD.pretty", "R_0805_2012Metric")
R2.SetReference("R2"); R2.SetValue("100R")
place(R2, 31, 18, rot_deg=90)
connect(R2, 1, "RESET_CTRL")
connect(R2, 2, "Q2_GATE")

R4 = load_fp("Resistor_SMD.pretty", "R_0805_2012Metric")
R4.SetReference("R4"); R4.SetValue("10k")
place(R4, 31, 27, rot_deg=90)
connect(R4, 1, "Q2_GATE")
connect(R4, 2, "GND")

# C1 - CMS uniquement (le traversant C1' est supprime : il faisait grossir
# la carte pour rien, cf. demande). Decale sur la droite pour degager le
# coin bas-gauche (ou vont maintenant D3/J3).
C1_SMD = load_fp("Capacitor_SMD.pretty", "CP_Elec_6.3x5.4")
C1_SMD.SetReference("C1"); C1_SMD.SetValue("100uF/16V (CMS)")
place(C1_SMD, 7.2, 23.4, rot_deg=0)  # suit le decalage de J1 (-2mm)
connect(C1_SMD, 1, "3V3")
connect(C1_SMD, 2, "GND")

C2 = load_fp("Capacitor_SMD.pretty", "C_0805_2012Metric")
C2.SetReference("C2"); C2.SetValue("100nF")
place(C2, 16, 28, rot_deg=0)
connect(C2, 1, "3V3")
connect(C2, 2, "GND")

# (pas de pont diviseur R5/R6 -- inutile, POWER_SENSE est toujours tape sur
# un point deja a 3.3V, jamais directement sur du 5V+ brut)

# ---------------------------------------------------------------------------
# Connecteurs (headers 2.54mm THT -- fils volants vers ESP32/buck/console)
# ---------------------------------------------------------------------------
J1 = load_fp("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x05_P2.54mm_Vertical")
J1.SetReference("J1"); J1.SetValue("ESP32 (fils volants)")
place(J1, 8, 7, rot_deg=0)  # broche 1 alignee sur la broche 1 de K1 (y=7)
connect(J1, 1, "3V3")
connect(J1, 2, "GND")
connect(J1, 3, "SENSE_MID")
connect(J1, 4, "SET_CTRL")
connect(J1, 5, "RESET_CTRL")

J2 = load_fp("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x02_P2.54mm_Vertical")
J2.SetReference("J2"); J2.SetValue("Buck 3V3 OUT")
place(J2, 6.0, 29.4, rot_deg=90)  # sous C1, espacement minimal
connect(J2, 1, "3V3")
connect(J2, 2, "GND")

# (remontee en haut, au-dessus de J1, parallele a J2, sur la meme ligne
# que D1/R1 -- D3 est a sa droite)
J3 = load_fp("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x02_P2.54mm_Vertical")
J3.SetReference("J3"); J3.SetValue("Tap alim brute (vers buck)")
place(J3, 11.93, 3.35, rot_deg=90)
connect(J3, 1, "RAW_IN")
connect(J3, 2, "GND")

J4 = load_fp("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x03_P2.54mm_Vertical")
J4.SetReference("J4"); J4.SetValue("Switch console (pole 1)")
place(J4, 38, 8, rot_deg=0)
connect(J4, 1, "SW_COM")
connect(J4, 2, "SW_NC")
connect(J4, 3, "SW_NO")

J5 = load_fp("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x03_P2.54mm_Vertical")
J5.SetReference("J5"); J5.SetValue("Pole 2 relais (libre/reserve)")
place(J5, 38, 17, rot_deg=0)
connect(J5, 1, "SW2_COM")
connect(J5, 2, "SW2_NC")
connect(J5, 3, "SW2_NO")

J6 = load_fp("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x02_P2.54mm_Vertical")
J6.SetReference("J6"); J6.SetValue("POWER_SENSE tap console (deja 3.3V)")
place(J6, 38, 26, rot_deg=0)
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
move_ref(K1, 17.81, 16.0)

# C2 : chevauchait la serigraphie de K1 (juste au-dessus de C2). Deplace en
# dessous de C2, cote degage.
move_ref(C2, 16.0, 30.2)

# C1 : chevauchait la serigraphie de J1 (juste au-dessus de C1). Un premier
# essai (a droite de C1) tombait en fait EN PLEIN sur la propre pastille
# negative de C1 (le pas entre les deux pattes d'un condensateur CP_Elec
# est trop petit pour decaler la reference sur le cote) -- signale par le
# DRC (silk_over_copper). Repositionne EN DESSOUS de C1 (les deux pattes de
# C1 sont cote a cote a la meme hauteur, donc au-dessus/en-dessous est
# degage), avec une marge confortable avant J2.
move_ref(C1_SMD, 8.075, 26.0)

# J5 : chevauchait la serigraphie de J4 (juste au-dessus). Deplace a
# gauche du connecteur, cote degage vers R2.
move_ref(J5, 34.6, 16.6)

# J6 : chevauchait la serigraphie de J5 (juste au-dessus). Deplace a
# gauche du connecteur, cote degage vers R4.
move_ref(J6, 34.6, 25.6)

# (pas de trous de fixation M2 -- pas necessaires, on gagne la place)

# Repere de placement pour le module ESP32 (collage/adhesif, PAS une
# empreinte a souder) -- dessine sur Cmts.User (calque de reference, non
# fabrique), dimension indicative pour un module 2x9 broches (le plus grand
# des deux, cf. carte bleue ESP32-C3-Zero), a verifier avec le module reel.
ESP_W, ESP_H = 23.0, 20.0  # indicatif : 8*2.54 (span pin-a-pin) + marges
ESP_X0 = 3.5  # suit le decalage de J1 vers la droite
ESP_Y0 = 7.0  # suit le decalage de J1 vers le haut (aligne sur K1 pin1)
esp_pts = [(ESP_X0, ESP_Y0), (ESP_X0 + ESP_W, ESP_Y0), (ESP_X0 + ESP_W, ESP_Y0 + ESP_H), (ESP_X0, ESP_Y0 + ESP_H), (ESP_X0, ESP_Y0)]
for i in range(len(esp_pts) - 1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(MM(esp_pts[i][0] + OFFSET_X), MM(esp_pts[i][1] + OFFSET_Y)))
    s.SetEnd(pcbnew.VECTOR2I(MM(esp_pts[i+1][0] + OFFSET_X), MM(esp_pts[i+1][1] + OFFSET_Y)))
    s.SetLayer(pcbnew.Cmts_User)
    s.SetWidth(MM(0.15))
    board.Add(s)
esp_txt = pcbnew.PCB_TEXT(board)
esp_txt.SetText("Zone ESP32 (collage)")
esp_txt.SetPosition(pcbnew.VECTOR2I(MM(ESP_X0 + 0.3 + OFFSET_X), MM(ESP_Y0 + 1.2 + OFFSET_Y)))
esp_txt.SetLayer(pcbnew.Cmts_User)
esp_txt.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
esp_txt.SetTextSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0)))
esp_txt.SetTextThickness(MM(0.12))
board.Add(esp_txt)

# ---------------------------------------------------------------------------
# Contour de la carte -- au plus juste, recalcule apres placement (voir plus bas)
# ---------------------------------------------------------------------------
W, H = 40.45, 32.75
seg_pts = [(0, 0), (W, 0), (W, H), (0, H), (0, 0)]
for i in range(len(seg_pts) - 1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(MM(seg_pts[i][0]), MM(seg_pts[i][1])))
    s.SetEnd(pcbnew.VECTOR2I(MM(seg_pts[i+1][0]), MM(seg_pts[i+1][1])))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(MM(0.15))
    board.Add(s)

board.SetFileName("/tmp/claude-0/-home-claude/70a7dc23-3f6a-5437-afc9-6d2c7c5f03dd/scratchpad/retropower_pcb/RetroPower_Compact_v3_unrouted.kicad_pcb")
pcbnew.SaveBoard(board.GetFileName(), board)
print("OK, unrouted compact board saved")
print("Footprints:", len(list(board.GetFootprints())))
