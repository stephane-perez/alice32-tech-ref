# ROM de l'Alice 32 : contenu, routines appelables, variables système

Sources : source commentée de la ROM V0.70 (**S19**, communauté Alice / system-cfg.com) **assemblée avec DASM : le résultat est identique octet par octet à `alice32.rom` (16 384 octets)** ; *Les Astuces d'Alice* (S20) ; programmes qui tournent (S8-S12).
Les noms de routines et de variables ci-dessous sont ceux de cette source commentée (ils n'existent pas dans la ROM d'origine) ; **les adresses, elles, sont celles de la ROM**.
Ce dépôt **ne contient ni la ROM ni son désassemblage complet** (droits d'auteur : voir `README.md`) ; ce document en donne les points d'entrée utiles.
Légende : **[A]** documenté dans un livre ou un programme ; **[B]** lu dans la ROM commentée.

## 1. Découpage de la ROM `$C000-$FFFF`

| Adresses | Contenu |
|---|---|
| `$C000-$D268` | **assembleur / éditeur résident Matra** (« ASSEMBLEUR ALICE REV 1.00 ») ; entrée `ASS_MAIN_ENTRY = $C000` (`EXEC 49152`) |
| `$D270-$DFFF` | routines graphiques (EF9345), cassette, éditeur de ligne ; table de sauts vidéo en `$D400` ; routine d'écriture cassette `K7WRT` en `$DF90`, de lecture `K7REA` en `$DFAC` |
| `$E000-$FFD1` | **MicroColor BASIC** (Microsoft, environ 8 Ko) : table des commandes `$E000`, opérateurs `$E030`, fonctions `$E0EE`, messages d'erreur `$E18A`… |
| `$FFD2-$FFDB` | un œuf de Pâques (nom d'un co-auteur Microsoft écrit à l'envers) |
| `$FFDC-$FFFF` | table de sauts système, puis vecteurs d'interruption `$FFF0-$FFFF` |

Zones libres (inutilisées) dans la ROM : `$D27C-$D3FC`, `$D432-$D43F`, `$D691-$D69F`, `$DACB-$DADF`, `$DD93-$DF8F`, `$DFF3-$DFFF`, `$F9BE-$F9C5` : ce sont des suppositions sur ce qu'un clone ou une ROM modifiée pourrait réutiliser.

## 2. Table de sauts vidéo `$D400` : l'interface « BIOS » graphique [B]

Chaque entrée est un `JMP` ; on peut donc appeler **`JSR $D4xx`** sans connaître l'adresse réelle de la routine.

| Entrée | Rôle | Routine réelle |
|---|---|---|
| `$D400` | initialise l'EF9345 en mode 40 colonnes | `initVIDEO_mode40` `$D465` |
| `$D403` | recopie le jeu de caractères d'Alice (semi-graphique) dans la mémoire vidéo | `initCarSemiGraph_EF9345` `$D56D` |
| `$D406` | **efface l'écran** (selon `TECRAN`) | `GR_CLRSCR` `$D524` |
| `$D409` | **défilement vers le haut** | `GR_SCROLLUP` `$D5C5` |
| `$D40C` | affiche un caractère (écran) | `OS_PRINT` `$D61D` |
| `$D40F` | lit le code ASCII sous le curseur | `GR_READ_ASCII` `$D4D6` |
| `$D412` | avance le curseur, défile si nécessaire | `GR_doincX_AND_SCROLLUP` `$D754` |
| `$D415` | recule le curseur | `GR_decCursor` `$D772` |
| `$D418` | avance le curseur | `GR_incCursor` `$D75C` |
| `$D41B` | efface une ligne | `GR_ClrLine` `$D608` |
| `$D41E` | initialise l'écran 80 colonnes normal | `GR_initVIDEO_mode80_NORM` `$DAD5` |
| `$D429` | efface une ligne selon le mode | `OS_clrLineByMode` `$D5ED` |
| **`$D42C`** | **initialise l'écran selon `TECRAN`** (`$301A` : 0 = 80 × 25, 1 = 40 × 25, 2 = 32 × 16) et recharge le jeu de caractères | `INASS` → `$D65F` |

`$D421-$D428` ne sont pas du code : ce sont les 4 adresses de tables clavier (voir `05`). `TECRAN = $301A` ; un programme BASIC peut faire `POKE 12314,1 : EXEC 54316` (`$D42C`) : c'est ce que fait *Castle Attack* **[A]**.

## 3. Autres routines utiles

| Adresse | Nom | Entrée → sortie |
|---|---|---|
| `$F72E` | `doRESET` | initialisation complète ; vecteur RESET |
| `$F868` | `OS_getKey` (« KDINP ») | attend une touche → A |
| `$F883` | `OS_POLCA` | touche ou 0 (Z) → A ; préserve B, X |
| `$F9C6` | `OS_printCHAR` (« OUTCA ») | A → écran (ou imprimante si `$E8` ≠ 0) ; appelle d'abord le crochet `$3288` |
| `$E7A8` | `OS_OUTTX` (« OUTTX ») | X + 1 → chaîne terminée par 0 (s'arrête sur `"`) |
| `$F419` | `LIPTR` (« LIPRT ») | D → affiche en décimal |
| **`$FBD4`** | `GRNCH` | **efface l'écran** avec la couleur de `$FC` ; `$FBD6` : entrée avec un caractère graphique dans B (l'ouvrage donne `$F8D4`/`$F8D6` par erreur) **[A, S20]** |
| `$FFA5` / `$FFAB` | `romSOUND` / `initRomSound` | SOUND : voir `05` |
| `$F62A` | `romRND` | fonction RND |
| `$E274` | `printOK` | affiche `OK` et attend une ligne (fin du démarrage BASIC) |
| `$DF90` / `$DFAC` | `K7WRT` / `K7REA` | écriture / lecture cassette en langage machine (le livre S20 donne `$DFA0`/`$DFBC` par erreur) |
| `$C000` | `ASS_MAIN_ENTRY` | assembleur résident |
| `$D748` | `OS_HardReset` | démarrage à froid sans passer par le test `$EA` |

## 4. Variables système

### 4.1 Page 0 (RAM interne du 6803) [B]

`$0000-$007F` : registres du 6803 (ports, timer, série) — voir `03-registres-et-ports.md`. `$0080-$00FF` : variables du BASIC. Principales :

| Adresse | Nom | Rôle |
|---|---|---|
| `$93` | `TXTAB` | début du programme BASIC (pointeur) |
| `$95` / `$97` / `$99` | `VARTAB` / `ARYTAB` / `STREND` | variables simples / tableaux / fin |
| `$9D` / `$A1` | `FRETOP` / `MEMSIZ` | chaînes, fin de mémoire |
| `$C9` | `ACC1` | accumulateur flottant 1 |
| `$E2` | `CURLIN` | ligne BASIC courante |
| `$E8` | `DEVNU` | sortie : 0 écran, ≠ 0 imprimante |
| `$EA` | `fCOLDWARN` | = `$55` : un RESET conserve la mémoire (démarrage à chaud) ; sinon test mémoire (détruit la RAM) |
| `$EB`/`$F3`/`$F4` | `CHRGET`/`CHRGOT`/`TXTPTR` | lecture du texte BASIC (routine copiée en RAM) |
| `$F9` | `Attribute_HIRES` | attribut en mode 80 colonnes |
| **`$FA`** | `ColorBG_SCR_LINE` | couleur de fond des lignes insérées par le défilement |
| **`$FB`** | `ColorFGBG_CAR` | couleurs courantes des caractères (fond/premier plan) : `POKE 251,n` en BASIC |
| **`$FC`** | `ColorCLS` | couleur d'effacement de l'écran : `POKE 252,240 : EXEC 64468` efface en couleur **[A, S11]** |

### 4.2 `$3000-$3345` [B]

| Adresse | Nom | Rôle |
|---|---|---|
| `$3008` | `fAUTOREPEAT` | répétition automatique des touches |
| `$3009` | `TABAD` | pointeur vers les tables clavier |
| `$3010-$3011` | `SCR_LGY`, `SCR_LGX` | dimensions de l'écran |
| `$3012-$3018` | `SCR_MARGEXY`… `MARGIN_SCR` | marges, taille de l'écran en pixels |
| **`$301A`** | `TECRAN` | type d'écran (0, 1, 2) |
| `$301B-$301C` | `HOME_YX` | origine du curseur |
| `$301D-$3026` | `POINT_YX_HIRES`, `dataR1/R4_EF9345`… | variables du mode graphique |
| `$3030-$3032` | `POS_BUFFERKEYB`, `fFLASHCAR`… | clavier / clignotement du curseur |
| `$3040-$30CF` | `ASS_*` | variables de l'assembleur (tampon de ligne `$3052`, symboles, ORG courant `$30CE`…) |
| `$30F0-$3103` | `*_K7` | en-tête et paramètres de cassette |
| `$3200-$3214` | `vectSCI`, `vectTOF` (`$3203`), `vectOCF` (`$3206`), `vectICF`, `doIRQ1`, `doSWI`, `doNMI` (`$3212`) | **trampolines d'interruption** (un `RTI` par défaut, espacés de 3 octets) |
| `$3215` | `doUSER` | (nom de la source ; rôle : vecteur utilisateur, non vérifié) |
| `$321F` / `$3221` | `pEXEC`, `pCOLD` | pointeurs nommés ainsi dans la source ; `$3221` intervient dans le test de démarrage à chaud (§5) |
| `$3223` | `PR_BAUDRATE` | vitesse de l'imprimante (2 octets) |
| `$3231` | `ROLTB` | table (rôle non précisé) |
| **`$3280`** | `CURAD_YX` | position courante du curseur (Y, X) |
| `$3282` | `COLOR_CARGRA` | couleur des caractères graphiques |
| `$3285-$32AC` | `vHOOK1_KBD` … `vHOOK14_FREE` | **14 crochets de 3 octets** (voir plus bas) |
| `$32B2` | `BUFFERKEYB` | tampon de saisie |
| `$3346` | — | **début du programme BASIC** ; `$4F94` : début de la pile système |

### 4.3 Crochets (hooks) [B]

Ce sont des emplacements de 3 octets en RAM, appelés (`JSR`) au début de routines de la ROM : on peut y écrire un `JMP` vers sa propre routine pour **étendre** le BASIC (technique du BASIC Microsoft, que le Disk BASIC utilise aussi **[B]**). Le contenu initial n'est pas détaillé ici.

| Adresse | Rôle |
|---|---|
| `$3285` | `vHOOK1_KBD` : clavier |
| `$3288` | `vHOOK2_PRINTCHAR` : au début de `OUTCA` |
| `$328B` | `vHOOK3_INITPRMSCCR` : initialisation de l'écran |
| `$328E` | `vHOOK4_CLEAR` : `CLEAR` |
| `$3291` | `vHOOK5_KBD` : clavier (2) |
| `$3294` | `vHOOK6_EVAL` : évaluation d'expression |
| `$3297`, `$329A` | `vHOOK7/8_ERROR` : erreurs |
| `$329D` | `vHOOK9_PARSENUMBER` : lecture d'un nombre |
| `$32A0` | `vHOOK10_EXECSTMT` : exécution d'une instruction |
| `$32A3` | `vHOOK11_PARSE_INPUT_LINE` : analyse de la ligne saisie |
| `$32A6` | `vHOOK12_EDITLINE` : éditeur de ligne |
| `$32A9`, `$32AC` | libres |

## 5. Démarrage (`$F72E`) [B + A]

1. Ports : DDR1 = `$FF` (port 1 en sortie), DDR2 = `$01`, port 2 = `$01`.
2. Si `$EA` = `$55` **et** `$3221` pointe un 1 → saut au programme résident (démarrage « à chaud » : le BASIC et la RAM sont conservés). Sinon → démarrage « à froid » `$D748`.
3. `$D748` : pile en `$4800`, initialisation de la vidéo, remise à zéro de `$0080-$00FF`, puis test de la taille mémoire en écrivant à partir de `$3000`. À la fin `$EA` vaut `$55`. Pour forcer un démarrage complet au prochain RESET : `CLR $EA`.
4. Le RESET ne peut pas être détourné ; les autres vecteurs le peuvent par les trampolines `$3200-$3212`.

## 6. Reproduire le désassemblage

Le source commenté (« rom_ALICE32_V0.70.asm », publié par la communauté, voir `00-sources.md`) s'assemble avec **DASM** : `dasm rom_ALICE32_V0.70_CLEAN_ALL.asm -f3 -ores`. Il donne un binaire **identique** à `alice32.rom` : c'est la meilleure référence pour comprendre la ROM. Pour étudier en direct : le débogueur de DCAlice (désassemblage, points d'arrêt, S2) ; MAME (pilote `alice32`) ; ou `DESASSEM.BAS` (S15) qui désassemble en BASIC.
