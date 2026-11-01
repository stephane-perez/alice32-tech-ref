# MicroColor BASIC 1.0 (Microsoft) et extensions

> Confiance : **A** = documenté dans une source citée · **B** = déduit du désassemblage de la ROM (à vérifier sur émulateur) · **C** = hypothèse.

## Version et origine

- La ROM de l'Alice 32 contient la chaîne `MICROCOLOR BASIC 1.0` / `COPYRIGHT 1982 MICROSOFT` (à l'adresse $F810) **[B]**. C'est le MicroColor BASIC de Microsoft, adapté par Matra.
- Le BASIC occupe $E000-$FFFF ; la moitié basse de la ROM ($C000-$DFFF) contient l'assembleur résident Matra (voir `06-rom-et-points-d-entree.md`).
- Le point d'entrée « prêt » (affichage de `OK` puis attente d'une ligne) est $E274 **[B]** ; il est aussi utilisé comme point d'arrêt par le script MAME de *Tuiles curieuses* pour détecter la fin du démarrage **[A]**.
- Les extensions du **Disk MicroColor BASIC 2.4/2.5** (disquette, `ELSE`, `ON ERROR`, `RENUM`, etc.) sont décrites dans `08-disk-basic-et-systeme-de-fichiers.md`.

## Mots-clés du BASIC de base (table de la ROM, $E045-$E146) [B]

Les jetons sont attribués dans l'ordre de la table, à partir de $80 (numérotation standard du BASIC Microsoft pour ce type de machine).
Les fonctions sont des **jetons d'un seul octet, de $B1 (`SGN`) à $C8 (`MEM`)** : il n'y a pas de préfixe $FF sur l'Alice 32 (vérifié sur les constantes `cBAS_TOKEN_*` de la ROM commentée).

### Instructions

| Jeton | Mot-clé | Jeton | Mot-clé | Jeton | Mot-clé |
|---|---|---|---|---|---|
| $80 | `FOR` | $81 | `GOTO` | $82 | `GOSUB` |
| $83 | `REM` | $84 | `IF` | $85 | `DATA` |
| $86 | `PRINT` | $87 | `ON` | $88 | `INPUT` |
| $89 | `END` | $8A | `NEXT` | $8B | `DIM` |
| $8C | `READ` | $8D | `LET` | $8E | `RUN` |
| $8F | `RESTORE` | $90 | `RETURN` | $91 | `STOP` |
| $92 | `POKE` | $93 | `CONT` | $94 | `LIST` |
| $95 | `CLEAR` | $96 | `NEW` | $97 | `CLOAD` |
| $98 | `CSAVE` | $99 | `LLIST` | $9A | `LPRINT` |
| $9B | `SET` | $9C | `RESET` | $9D | `CLS` |
| $9E | `SOUND` | $9F | `EXEC` | $A0 | `SKIPF` |

### Mots secondaires et opérateurs

| Jeton | Mot | Jeton | Mot | Jeton | Mot | Jeton | Mot |
|---|---|---|---|---|---|---|---|
| $A1 | `TAB(` | $A2 | `TO` | $A3 | `THEN` | $A4 | `NOT` |
| $A5 | `STEP` | $A6 | `OFF` | $A7 | `+` | $A8 | `-` |
| $A9 | `*` | $AA | `/` | $AB | `^` | $AC | `AND` |
| $AD | `OR` | $AE | `>` | $AF | `=` | $B0 | `<` |

### Fonctions (jetons $B1 à $C8)

| Code | Fonction | Code | Fonction | Code | Fonction | Code | Fonction |
|---|---|---|---|---|---|---|---|
| $B1 | `SGN` | $B2 | `INT` | $B3 | `ABS` | $B4 | `USR` |
| $B5 | `RND` | $B6 | `SQR` | $B7 | `LOG` | $B8 | `EXP` |
| $B9 | `SIN` | $BA | `COS` | $BB | `TAN` | $BC | `PEEK` |
| $BD | `LEN` | $BE | `STR$` | $BF | `VAL` | $C0 | `ASC` |
| $C1 | `CHR$` | $C2 | `LEFT$` | $C3 | `RIGHT$` | $C4 | `MID$` |
| $C5 | `POINT` | $C6 | `VARPTR` | $C7 | `INKEY$` | $C8 | `MEM` |

Remarques :

- Le BASIC de base **n'a ni `ELSE`, ni `'`, ni `HEX$`, ni `INSTR`, ni `JOYSTK`, ni `TIMER`** : ces mots viennent du Disk BASIC (voir plus bas et `08-...`).
- `SKIPF`, `CSAVE`, `CLOAD`, `EXEC`, `SET`, `RESET`, `POINT`, `SOUND`, `CLS`, `LLIST`, `LPRINT`, `INKEY$`, `MEM`, `VARPTR` existent dans la ROM de base.
- `PRINT@` (utilisé par exemple dans *Castle Attack*, `PRINT@8*80+35,"..."`) est reconnu par l'analyseur de `PRINT` : il n'a pas de jeton propre **[B/A]**. Le calcul `8*80+35` suggère une position = ligne × 80 + colonne, donc un écran 80 colonnes pour ce programme (voir `04-ef9345-video.md`).
- Le dispatch des instructions se fait par une table de pointeurs en $E000 (indice = 2 × (jeton − $80)) ; l'entrée de `REM` pointe en RAM ($3215), ce qui permet à une extension d'intercepter cette instruction **[B, à vérifier]**. La table d'opérateurs (priorités + routines) commence en $E030.
- La table des fonctions (adresses des routines) commence en $E148 **[B]**.

## Messages et codes d'erreur

Table des abréviations dans la ROM (2 lettres, `$E18A…`) **[B]** : `NF SN RG OD FC OV OM UL BS DD /0 ID TM OS LS ST CN IO FM`, puis le suffixe ` ERROR`, le message ` IN `, le prompt `OK` et `BREAK`.

Codes numériques (valeurs de `ERRN`, `ERROR n`) donnés par la documentation du Disk BASIC **[A, S5]** :

| Abr. | N° | Signification | Abr. | N° | Signification |
|---|---|---|---|---|---|
| NF | 0 | NEXT without FOR | IO | 34 | Input/Output error |
| SN | 2 | Syntax error | FM | 36 | Wrong file mode |
| RG | 4 | RETURN without GOSUB | DN | 38 | Bad device number |
| OD | 6 | Out of DATA | NE | 40 | File does not exist |
| FC | 8 | Illegal function call | WP | 42 | Write protected |
| OV | 10 | Overflow | FN | 44 | Badly formed file name |
| OM | 12 | Out of memory | FS | 46 | File system error |
| UL | 14 | Undefined line number | IE | 48 | Input past end of file |
| BS | 16 | Bad subscript | FD | 50 | Unacceptable file data |
| DD | 18 | Doubly dimensioned array | AO | 52 | File already open |
| /0 | 20 | Division by zero | NO | 54 | File not open |
| ID | 22 | Illegal in direct mode | DS | 56 | Direct statement in file |
| TM | 24 | Type mismatch | AE | 58 | File already exists |
| OS | 26 | Out of string space | DF | 60 | Disk full |
| LS | 28 | String too long | | | |
| ST | 30 | String formula too complex | | | |
| CN | 32 | Can't continue | | | |

La ROM de base ne connaît que les 19 premiers codes (jusqu'à `FM`, n° 36) ; les codes à partir de 38 (`DN`…`DF`) sont ceux du Disk BASIC. Cette table provient d'un scan DjVu lu par OCR puis relu ; les noms sont ceux de la doc, les numéros suivent l'ordre croissant de 2 en 2 **[A]**.

## Particularités utiles pour programmer (observées dans des programmes réels)

| Élément | Détail | Source |
|---|---|---|
| `EXEC adr` | lance du code machine ; décimal ou `&H` (Disk BASIC) | doc Disk BASIC **[A]** |
| `CLOADM` puis `EXEC` | charge un binaire cassette ; *Tuiles curieuses* : `CLOADM` puis `EXEC 17500` | README tuiles **[A]** |
| `POKE 12314,n : EXEC 54316` | appelle la routine ROM $D42C (réinitialisation de l'écran texte ; $301A = drapeau de mode) | *Castle Attack* **[A]** + ROM **[B]** |
| `POKE 251,n` | écrit l'octet $FB, un attribut de couleur du texte (par ex. 114 = $72, 50 = $32) | *Castle Attack* **[A]** ; la ROM initialise $FA/$FB/$FC dans la routine $D684 **[B]** |
| `INKEY$` | lecture clavier non bloquante | programmes **[A]** |
| `SET(x,y,c)`, `RESET(x,y)`, `POINT(x,y)` | graphisme basse résolution ; *Castle Attack* teste `X>159` et `Y>124` comme limites (mode d'écran non précisé dans la source) | *Castle Attack* **[A]** |
| `SOUND hauteur,durée` | ex. `SOUND 200-Y,1` | *Castle Attack* **[A]** |
| `CLS 32`, `CLS 40`, `CLS 80` | change le mode d'écran (Alice 32/90 seulement) ; sans reset avec le Disk BASIC | doc Disk BASIC **[A]** |
| Vitesse | « Un jeu en BASIC est lent » ; l'émulateur permet de régler la fréquence du 6803 (×40, ×80) | doc *Invaders* **[A]** |

## Extensions du Disk MicroColor BASIC 2.4 (résumé)

Commandes de disque : `BACKUP, CHAIN, CLOSE, COPY, DIR, DIRI, DOS, DRIVE, DSKINI, EOF, FREE, INPUT#, KILL, LOAD, LOADM, LOAD*, MERGE, OPEN, PRINT#, RENAME, RUN, RUNM, SAVE, SAVEM, SAVE*, SET FILE, RESET FILE`.

Autres ajouts : `CLEAR ERROR, CSAVEM, DEFUSR=, DEL, ELSE, ERRL, ERRN, ERROR, HEX$, INSTR, JOYSTK, LINE INPUT, MAXVAL, MINVAL, MID$ (affectation), ON BREAK, ON ERROR, POS, RENUM, STRING$, SWAP, TIMER (lecture/écriture, 1/60 s), TRON, TROFF, WAIT ms, WPEEK, WPOKE`, constantes `&H`, `RESTORE ligne`, `VARPTR` corrigé (résultat toujours positif).

Raccourcis (Disk BASIC) : `Ctrl-3` = `SAVE`, `Ctrl-4` = `LOAD` ; `SHIFT+BREAK` efface l'écran ; `SHIFT+RESET` = redémarrage complet ; `CONTROL` maintenu à la mise sous tension = BASIC d'origine.

Détails complets : voir `08-disk-basic-et-systeme-de-fichiers.md`.
