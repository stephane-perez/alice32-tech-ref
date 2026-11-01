# Cassette et formats de fichiers

## Commandes BASIC de cassette [A, S5, S8, S14]

| Commande | Rôle |
|---|---|
| `CLOAD` / `CLOAD "nom"` | charge un programme BASIC (le prompt `$` clignote en haut à droite pendant la lecture ; puis `OK`) |
| `CSAVE "nom"` | sauvegarde un programme BASIC |
| `CLOADM` | charge un programme en code machine ; lancer ensuite avec `EXEC adresse` (ex. `EXEC 17500` pour *Tuiles curieuses*) |
| `CSAVEM "nom",début,fin,exec` | sauvegarde un bloc de mémoire (Disk BASIC) |
| `SKIPF` | saute un fichier sur la bande (jeton `$A0`, ROM de base) |

Mode d'emploi courant des éditeurs (S11, S15, Coloric) : brancher le magnétophone, rembobiner, `CLOAD` + ENTER, lancer la lecture, quand `OK` apparaît taper `RUN`.
Une face de cassette contient parfois plusieurs programmes (Coloric / La Marelle) ou un programme BASIC placé après le code machine (IVA).

## Fichier `.k7` de DCAlice [A, S3]

Un `.k7` est une suite de **blocs** :

```
[ en-tête de 8 octets, facultatif (dcalicek7) ] [ octets de synchro $55 ] [ bloc ] [ $55 ]
```

- Chaque bloc est précédé d'octets de synchronisation `$55` et suivi d'un autre `$55`.
- En-tête de 8 octets (fichiers créés par `dcalicek7`) : octet 1 = `$DC` ; octet 2 = nature du bloc (0 = bloc standard Alice) ; octets 3-4 = nombre d'octets de synchro (un seul est stocké pour simplifier) ; octets 5-8 = nombre d'échantillons du silence avant le bloc.
- Sans cet en-tête (fichier d'un autre outil), valeurs par défaut :
  - silence : 882 000 échantillons (bloc `$00`), 16 000 (premier bloc `$01`), 128 (blocs suivants) ;
  - synchro : 128 octets (bloc `$00`), 128 (premier bloc `$01`), 1 (blocs suivants).
- Le **contenu** des blocs (type, longueur, données, somme de contrôle) suit le format cassette Microsoft/MC-10 mais **n'est pas détaillé dans l'archive** [C].

## Fichier `.wav` [A, S3]

PCM, mono ou stéréo (seul le canal droit est décodé en stéréo), 8 ou 16 bits, 22 050 Hz ou plus ; **meilleur compromis : 44 100 Hz, 8 bits, mono**. `dcalicek7` convertit `.wav` ↔ `.k7`.
Un bit est une **période** du signal : la distinction 0/1 se fait en comparant la période à un seuil exprimé en échantillons à 44 100 Hz (exemple de l'outil : seuil 30 échantillons ≈ 680 µs). Les paramètres de décodage de l'outil (niveau zéro 128, bruit, inversion de phase, amélioration des transitions) sont expliqués dans S3.

## Autres formats rencontrés dans l'archive

| Extension | Signification | Source |
|---|---|---|
| `.k7` | image de cassette DCAlice | S3 |
| `.wav` | enregistrement audio de cassette | S3 |
| `.rom`, `.bin` | image de **cartouche** (`.bin` équivalent à `.rom` depuis la version 2024.03.19) ; jusqu'à 8 banques de 8 Ko dans `$1000-$2FFF` | S2, S8 |
| `.txt` (programme BASIC) | chargé « comme une cassette », converti automatiquement en `.k7` par DCAlice | S2 |
| `.c10` | fichier cassette produit par la chaîne CC6303 (`-tmc10`) ; renommé `.k7` pour DCAlice | S8 (Makefile) ; aussi `SOKOB.c10` |
| `.fd`, `.dsk` | image de disquette (`la-chenille-infernale_alice.fd`) | archive |
| `.bin` (disque/SD) | binaires `LOADM` sur disquette ou carte SD | archive (Sokoban) |
| `.djvu` | documentation scannée (visualiseur DjVu requis) | site |
| `.lep` | non identifié (produit par certaines entrées du catalogue) | **inconnu** |
| `.pxo` | fichier Pixelorama (graphismes de *Tuiles curieuses*) | S8 |

## Charger un programme dans DCAlice [A, S14]

1. Lancer l'émulateur, vérifier la machine (Options → Paramètres : Alice 32).
2. *Fichier → charger cassette* (`.k7`) ou charger une cartouche (`.rom`/`.bin`).
3. Taper `CLOAD"NOM"` puis `RUN` (BASIC) ou `CLOADM` puis `EXEC adresse` (code machine). Pour une cartouche : `EXEC 4096` après avoir choisi la zone `$1000-$2FFF` comme cartouche.
4. Pour accélérer un jeu BASIC : Options → Paramètres → Processeur 6803 : jusqu'à 4000 % ou 8000 % (S14).
