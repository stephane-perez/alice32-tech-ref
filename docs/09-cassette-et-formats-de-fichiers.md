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

## Fichier `.k7` de DCAlice [A, S3 ; B, S3 code]

Sources : la notice de DCALICEK7 (S3) **[A]**, et le **code machine de `dcalicek7.exe` 2011.04** (même archive S3, compressé par UPX, décompressé et désassemblé pour ce dépôt) **[B]**. Une réécriture en Python se trouve dans `exemples/demo/outils/k7wav.py`.

Un `.k7` est une suite de blocs ; **chaque bloc est précédé d'un seul octet `$55`** (le vrai nombre d'octets de synchronisation n'est pas conservé) et suivi d'un autre `$55` :

```
[ en-tête $DC de 8 octets, facultatif ] $55 $3C type longueur données(longueur) somme $55
```

- **somme** = (type + longueur + données) modulo 256 ;
- **types** : `$00` en-tête de fichier, `$01` données (255 octets au plus), `$FF` fin. DCALICEK7 refuse un premier bloc d'un autre type que `$00`, et, après un `$00`, un bloc d'un autre type que `$01` **[B]** ;
- **en-tête de 8 octets** (fichiers produits par DCALICEK7), **poids faible d'abord [B]** :

| Octet | Contenu |
|---|---|
| 0 | `$DC` |
| 1 | nature du bloc (0 = bloc standard Alice ; sinon l'en-tête est ignoré) |
| 2-3 | nombre d'octets de synchronisation `$55` (16 bits) |
| 4-7 | durée du silence avant le bloc, en échantillons à 44 100 Hz (32 bits) |

- **sans en-tête**, valeurs par défaut :
  - silence : 882 000 échantillons (20 s) avant un bloc `$00`, 16 000 avant le bloc qui suit un `$00`, 128 sinon ;
  - synchronisation : **127** octets `$55` avant un bloc `$00` ou le bloc qui le suit (la notice dit 128), 1 sinon **[B]**.
- Le bloc d'en-tête de fichier (type `$00`) commence par le nom sur 8 caractères (DCALICEK7 l'affiche) ; la suite (type de fichier, adresses) n'est pas exploitée par DCALICEK7 **[B]**.
- **Vérifié sur Alice 32 réelle [A, S26]** : un fichier produit par `bin2k7.py` puis `k7wav.py` se charge par `CLOADM` et se lance par `EXEC 13312`. L'en-tête de fichier suit donc bien la disposition du Color BASIC / MC-10 (15 octets) : nom (8 caractères), type de fichier (2 = code machine), drapeau ASCII (0), drapeau d'intervalle (0), adresse d'exécution, adresse de chargement (poids fort d'abord). Le signal de DCALICEK7 (périodes carrées de 20 et 40 échantillons) est accepté par la machine.

## Fichier `.wav` [A, S3 ; B, S3 code]

**Écrit par DCALICEK7 (k7 → wav) [B]** :
- PCM 44 100 Hz, 8 bits, mono ; en-tête RIFF de 44 octets.
- Un octet = 8 bits, **poids faible d'abord**, sans bit de start ni de stop.
- Un bit = **une période carrée**, alternance haute (240) puis basse (16) :
  - **bit 1 = 10 + 10 échantillons**, soit 2 205 Hz ;
  - **bit 0 = 20 + 20 échantillons**, soit 1 102,5 Hz.
- Avant chaque bloc : le silence (niveau zéro, 128 par défaut), puis les octets `$55`, puis `$3C`, le type, la longueur, les données, la somme et `$55`.
- À la fin : 88 200 échantillons de silence (2 s).
- Particularité : la taille du bloc `data` inscrite dans l'en-tête vaut taille du fichier − 45 au lieu de − 44.

**Lu par DCALICEK7 (wav → k7) [A + B]** :
1. Il prend le canal droit d'un fichier stéréo et l'octet de poids fort d'un échantillon de 16 bits ; les données sont lues à partir de l'octet 48.
2. Il mesure les **alternances** entre deux passages par le niveau zéro, converties en échantillons à 44 100 Hz. Un passage dont l'amplitude crête à crête est inférieure au « bruit » (40 par défaut) est ignoré. Options : inversion de phase, et « amélioration des transitions » (une alternance négative proche de la positive précédente reçoit sa largeur).
3. **Synchronisation** : il cherche trois paires (bit 0, bit 1) de suite. Le seuil T (30 par défaut, en échantillons) classe une période comme bit 1 si elle est dans [T/2, T[, comme bit 0 si elle est dans [T, 3T/2]. Il suit ensuite les paires en ajustant le seuil : T ← (2T + période₀ + période₁ + 2) / 4.
4. Il glisse d'un bit jusqu'à lire `$3C`, puis lit le type, la longueur, les données, la somme et le `$55` final. Une période hors de [T/2, 3T/2] ou une somme fausse **arrêtent la conversion** ; les blocs déjà décodés restent dans le `.k7`.
5. Pour chaque bloc, il écrit l'en-tête `$DC` avec le nombre d'octets de synchronisation mesuré, (bits + 4) / 8, et la durée du silence qui précède.

Conseils de la notice : un fichier en 44 100 Hz, 8 bits, mono est le meilleur compromis ; 22 050 Hz au minimum.

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
