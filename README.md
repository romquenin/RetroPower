# RetroPower

Module de contrôle d'alimentation pour consoles rétro, piloté par Home Assistant via un ESP32-C3 — PCB 2 couches (KiCad), relais pour l'allumage/extinction à distance (émulation du bouton power).

## Deux versions de PCB

### `hardware/integrated/` — version intégrée (recommandée)
Le module ESP32-C3-Zero (Waveshare, 18 broches castellées) est **soudé directement au dos du PCB** — pas de fils volants. L'antenne se retrouve sur le bord extérieur de la carte, totalement dégagé de tout cuivre/métal sur les deux faces, pour la meilleure réception WiFi/Bluetooth possible.

- Dimensions : 53.335 x 32.75 mm
- DRC officiel KiCad : 0 erreur / 0 avertissement (v4)
- Voir `LISEZMOI.txt` dans ce dossier pour l'historique des correctifs et la procédure de vérification de l'écartement des broches avant soudure définitive.

### `hardware/compact/` — version compacte (de secours)
Le module ESP32-C3-Zero est relié par fils volants (pas soudé directement sur le PCB). Insensible aux variations de cotes entre modules, utile en secours si la version intégrée pose un souci de compatibilité physique.

- Dimensions : 40.45 x 32.75 mm
- DRC officiel KiCad : 0 erreur / 0 avertissement (v11)
- Voir `LISEZMOI.txt` et `BRANCHEMENTS.txt` dans ce dossier.

Chaque dossier contient : le fichier `.kicad_pcb`/`.kicad_pro`, les gerbers (dossier + zip), le fichier de position des composants (`_pos.csv`), la BOM (`BOM.csv`), un rendu visuel du routage et le fichier `LISEZMOI.txt` expliquant les choix de conception.

## Firmware

`firmware/retropower_template.yaml` — template ESPHome générique, à dupliquer pour chaque console (changer `device_name` / `friendly_name`). Brochage utilisé :

- GPIO0 — `POWER_SENSE` (lecture du rail 3V3 de la console)
- GPIO3 — `RELAY_SET` (impulsion → allume, via Q1)
- GPIO10 — `RELAY_RESET` (impulsion → éteint, via Q2)

## Scripts de génération (KiCad / Python)

`scripts/` contient les scripts Python (API `pcbnew`) utilisés pour générer et router chaque carte, ainsi que les scripts de vérification (clearance, trous, connectivité, bord de carte, sérigraphie, chevauchement de composants) utilisés en complément du DRC officiel de KiCad.

- `scripts/integrated/` : `build_integrated.py` (placement + footprints), `route_integrated.py` (routage initial), `fix_net_integrated.py` (correctifs de routage ciblés)
- `scripts/compact/` : `build_compact_v3.py`, `route_grid_compact5.py`
- `scripts/checks/` : scripts de vérification communs aux deux versions

Nécessite KiCad 7 (API `pcbnew` headless) et Python 3.

## Principe de fonctionnement

Le module émule l'appui sur le bouton power de la console via deux impulsions distinctes (SET/RESET) pilotées par deux MOSFET (Q1/Q2) qui commandent les deux bobines d'un relais bistable (K1) — le relais reste dans l'état choisi sans consommation continue. Un pont de sense (`POWER_SENSE`) permet à l'ESP32 de lire l'état réel d'allumage de la console pour Home Assistant.

## Alimentation

Le buck converter (12V/8V brut de la console → 3.3V régulé) est **externe**, non intégré au PCB. Voir les fichiers `LISEZMOI.txt`/`BRANCHEMENTS.txt` de chaque version pour le câblage exact (`J2` = entrée 3.3V régulé, `J3` = tap brut + protection anti-inversion).

## Avertissement

Ces fichiers sont fournis tels quels, sans garantie. Toujours vérifier le DRC officiel de KiCad avant de commander un lot de PCB, et tester le rail 3.3V au multimètre avant de souder un module ESP32 définitivement.
