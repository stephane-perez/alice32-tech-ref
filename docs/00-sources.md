# Sources, crédits et niveaux de confiance

Les chemins ci-dessous sont relatifs à l'archive `alice32.free.fr.zip` fournie (copie partielle du site de Daniel Coulom).

| Id | Source | Auteur / date | Usage ici | Remarque |
|---|---|---|---|---|
| S1 | `schemas/schema_alice32_corrige.png`, `schemas/alice32.html` (+ schémas MC-10, Alice 4K, Alice 90) | Daniel Coulom, corrigé le 9 mai 2020 | composants de la carte, câblage clavier | Image lue visuellement, résolution moyenne |
| S2 | `emulateur/prog/dcalice_20260504.zip` → notice HTML (historique des versions 2005-2026) | Daniel Coulom | nombreux détails matériels déduits des corrections | Le `.exe` Windows n'a pas été exécuté |
| S3 | `emulateur/prog/dcalicek7_201104.zip` → notice HTML | Daniel Coulom, 2011 | formats `.k7` et `.wav` | |
| S4 | `emulateur/rom/alice32.zip` (`alice32.rom`, 16 384 octets), `alice4k.zip`, `mc10.zip` | © Matra-Hachette / Microsoft | désassemblage, tables de jetons, vecteurs | non redistribuée ici |
| S5 | `programmes/disk-microcolor-basic/…_doc.zip` → `Alice_Disk_Basic_24.djvu` | Darren Atkinson (Disk MicroColor BASIC 2.4) | commandes, erreurs | DjVu lu par OCR, relu |
| S6 | idem → `Alice_File_System.djvu` | idem | API FILSYS, DSKCON, RDSEC, WRSEC | DjVu lu par OCR, relu |
| S7 | idem → `mcx32-fdj_hardware_info.djvu`, `mcx32-fdj_eeprom_addressing.djvu` | Darren Atkinson (contrôleur MCX32-FDJ) | carte mémoire, registres du contrôleur | OCR |
| S8 | `programmes/tuiles-curieuses/…_source.zip` | Sylvain Glaize (« mokona78 » sur itch.io), licence MIT, 2024 | EF9345, son, timer, clavier ROM, banques de cartouche | C + asm, compilateur CC6303 |
| S9 | `programmes/tetrice/tetrice_source.zip` | auteur non indiqué dans les fichiers lus | matrice clavier, accès direct EF9345, timer | C |
| S10 | `programmes/alicetel/alicetel_source.zip` (listing assembleur DjVu, 13 juin 1985) | J-F Gallet et C. Musset, pour Matra | points d'entrée ROM, EF9345, ACIA 6850 | OCR imparfait |
| S11 | `programmes/incrustation-video/…_doc.zip` | Matra Datasystème | incrustation vidéo (IVA), adresses de code machine | OCR |
| S12 | `programmes/castle-attack/castle-attack_source.txt` | Olipix, 2024 | exemples BASIC | |
| S13 | `programmes/in-the-dark/in-the-dark_doc.txt` | Duruti (game jam RPUOS) | assembleur 6803 en croisé avec **DASM** + DCAlice | |
| S14 | `programmes/invaders/invaders_doc.txt`, `flagon-bird_doc.txt` | VynZ ; adaptation de Steve Bamford | vitesse émulateur, formats | |
| S15 | `programmes/desassembleur/desassembleur_doc.zip` | P. Lapierre, 2007 | existence d'un désassembleur BASIC | |
| S16 | `programmes/edit/…` | — | non exploité (doc image) | |
| S17 | `documentation/…ef9345…datasheet` (DjVu) | SGS-Thomson, 1995 | registres, commandes, temps d'exécution du contrôleur vidéo EF9345 | OCR + relecture visuelle des tableaux |
| S18 | `documentation/…ef9345…` note d'application (AN325) | SGS-Thomson | exemples d'initialisation, écriture de tranches (UDC) | OCR |
| S19 | `documentation/rom_ALICE32_V0.70.asm` | communauté Alice (forum system-cfg.com) | source commenté de la ROM V0.70, 2575 symboles | assemblé avec DASM : **identique octet par octet** à `alice32.rom` ; non redistribué ici |
| S20 | *Les Astuces d'Alice* (DjVu) | Soracom / Matra | clavier, son, mémoire vidéo, annexes, errata | OCR ; erreurs relevées dans `12-questions-ouvertes.md` |
| S21 | Sokoban en FIG-Forth | Dominique Constant | codes bruts des manettes | |
| S22 | *Guide d'instructions de l'éditeur-assembleur* (DjVu) | Matra-Hachette, 1984 | éditeur, directives, erreurs | OCR ; les lettres des commandes CTRL sont des images perdues |
| S23 | Fiche technique MC6803E (DjVu) | Motorola | cycles, registres, vecteurs | OCR |
| S24 | `documentation/schema_electrique_alice32_corrige.png` | Daniel Coulom | câblage | non redistribué ici |

Documents du lot « documentation » **hors périmètre** (Alice d'origine à MC6847 ou autres machines) et donc non exploités : *Les Mystères d'Alice*, *Aller plus loin avec Alice*, document interne Matra, *Programmation en assembleur* (Alice d'origine).

Crédits : les documents ont été scannés par **Daniel Coulom** et les contributeurs au site web (<http://alice32.free.fr/>).

Crédits spéciaux : le site, l'émulateur DCAlice et la plupart des conversions sont l'œuvre de **Daniel Coulom**
(<http://alice32.free.fr/>). Le contrôleur de disquette MCX32-FDJ et le Disk BASIC sont de **Darren Atkinson**.

## Niveaux de confiance

- **[A]** : écrit dans une des sources S1-S24 (l'identifiant est donné ou évident).
- **[B]** : déduit de la ROM (S4) ou du schéma (S1) par l'auteur de ce dépôt.
- **[C]** : hypothèse.

## Méthodes utilisées pour les déductions [B]

- Référence principale : le **source commenté de la ROM (S19)**, dont l'assemblage avec DASM redonne `alice32.rom` octet pour octet. Les adresses, constantes et rôles de routines viennent de lui.
- Les codes de commande de l'EF9345 ont été lus visuellement sur les images de la fiche (S17) et recoupés avec les constantes de la ROM.
- Les OCR (DjVu → `ddjvu` + `tesseract`) comportent des erreurs : les valeurs critiques ont été relues sur l'image ou recoupées avec la ROM ; les cas non tranchés sont dans `12-questions-ouvertes.md`.
- Rien n'a été exécuté sur machine réelle ni sous émulateur.
