# Disk MicroColor BASIC 2.4/2.5, système de fichiers et contrôleur MCX32-FDJ

Sources : S5 (commandes), S6 (API assembleur), S7 (matériel). Auteur du contrôleur et du logiciel : Darren Atkinson.
Les docs sont des scans DjVu lus par OCR puis relus ; les valeurs numériques ont été vérifiées visuellement pour les registres matériels.

## Format des disquettes [A, S5]

- Disquettes 3,5″ **720 Ko double densité**, **FAT12**, **clusters de 4 Ko (8 secteurs de 512 octets)**.
- **Répertoire racine uniquement** (112 fichiers max.), pas de noms longs.
- Nom de fichier (chaîne BASIC) : `lecteur:nom.extension`, lecteur `0` ou `1` (par défaut : `DRIVE`), nom 1-8 caractères, extension 1-3.
  Interdits : `/ * . " : < = > ? + , ; [ ]`.
- Extensions par défaut : programme `BAS`, binaire `BIN`, tableau `ARY`, données `DAT`.
- Secteurs logiques numérotés de **0 à 1439**.

## Commandes BASIC (résumé détaillé : `07-basic-microcolor.md`)

Fichiers de données : `OPEN "I"|"O"|"A", #n, "nom"` (n de 1 à 4, 4 fichiers ouverts max.), `PRINT #n`, `INPUT #n`, `CLOSE`, `EOF(n)`.
Ne jamais retirer la disquette avant `CLOSE` après une écriture (risque de corruption) **[A, S5]**.
Programmes : `LOAD, SAVE ["nom", A]` (A = texte ASCII), `RUN "nom"[,ligne]`, `CHAIN`, `MERGE`.
Binaires : `LOADM "nom"[,décalage]`, `SAVEM "nom",début,fin,exec`, `RUNM`, `CSAVEM` (cassette).
Gestion : `DIR`, `DIRI` (avec fichiers cachés), `KILL`, `RENAME "a" TO "b"`, `COPY`, `FREE(lecteur)`, `DSKINI lecteur[,Q][,V][,I n]["étiquette"]`, `BACKUP`, `SET FILE`/`RESET FILE` (attributs A=archive, I=invisible, P=protégé), `DOS` (charge le module d'amorçage du secteur 0).

## Appeler le système de fichiers en assembleur [A, S6]

Point d'entrée **`FILSYS = $0030`** : opération dans **B**, pointeur vers un **FCB** (File Control Block) dans **X**. X est préservé, A et B ne le sont pas. Retour : retenue positive (`BCS`/`BES`) si erreur, code dans l'octet 0 du FCB.

FCB de **34 octets** : les 8 premiers servent aux paramètres et au statut, le reste est interne (ne pas y toucher tant que le fichier est ouvert).

| Octet(s) | Nom | Sens |
|---|---|---|
| 0 | Status | **sortie** : code d'état (0 = succès) |
| 1 | Opcode | opération (valeur de B) |
| 2-3 | Name | pointeur vers le nom, chaîne terminée par 0 (aussi `DatPtr` pour read/write) |
| 4-5 | DefExt / Count / NewName | pointeur vers 3 caractères d'extension par défaut (0 = aucun) ; ou nombre d'octets ; ou nouveau nom |
| 6-7 | Buffer | pointeur vers un **tampon de 512 octets exclusif** à ce FCB |
| 3-5 (FSeek) | NewPos | position absolue sur 24 bits (octet 3 = poids fort) |
| 4, 5 (FAttrib) | Mask, Value | masque des attributs conservés, valeur à ajouter |

Opérations :

| Nom | Code | Rôle |
|---|---|---|
| `FClose` | `$00` | ferme le fichier (écrit les données en cache) |
| `FOpen` | `$02` | ouvre en lecture/écriture, position 0 |
| `FOpenR` | `$03` | ouvre en lecture seule |
| `FFlush` | `$04` | force l'écriture des caches |
| `FRead` | `$06` | lit `Count` octets à `DatPtr` ; code 48 si fin de fichier atteinte (le reste est quand même lu) |
| `FSeek` | `$08` | positionne ; code 48 si au-delà de la fin |
| `FSetEnd` | `$0A` | la position courante devient la fin du fichier (réduit seulement) |
| `FWrite` | `$0C` | écrit `Count` octets depuis `DatPtr` (agrandit le fichier si besoin) |
| `FRename` | `$0E` | renomme (`Name` → `NewName`, extension obligatoire dans les deux noms) |
| `FKill` | `$10` | supprime (extension obligatoire) |
| `FAttrib` | `$12` | attributs : lecture seule `$01`, caché `$02`, archive `$20` |
| `FCreate` | `$82` | comme `FOpen` mais crée le fichier s'il n'existe pas |

Codes d'état : 0 succès · 34 erreur E/S · 36 fichier en lecture seule · 38 mauvais numéro de lecteur · 40 fichier introuvable · 42 disque/fichier protégé en écriture · 44 nom incorrect · 46 erreur du système de fichiers · 48 lecture/positionnement après la fin · 52 déjà ouvert · 54 non ouvert · 58 le nouveau nom existe déjà · 60 disque plein.

Lecteur par défaut : variable **`DEFDRV = $BDCF`**.

Exemple (adapté de S6, ouvre/crée `TESTFILE.DAT` sur le lecteur 0) :

```asm
        ldx   #FCB
        ldd   #FName
        std   2,x          ; Name
        ldd   #0
        std   4,x          ; pas d'extension par défaut
        ldd   #FBuffr
        std   6,x          ; tampon de 512 octets
        ldab  #$82         ; FCreate
        jsr   $0030        ; FILSYS
        bcs   erreur       ; (bes dans la doc)
        ...
FName   fcc   '0:TESTFILE.DAT'
        fcb   0
FCB     rmb   34
FBuffr  rmb   512
```

## Pilote bas niveau [A, S6]

| Appel | Adresse | Description |
|---|---|---|
| `DSKCON` | `$0020` | pilote : paramètres dans le bloc `$BDC0-$BDC5`, statut dans `DCSTA = $BDC6`, retenue = 1 si statut ≠ 0 ; X, A, B préservés |
| `RDSEC` | `$0023` | lit le secteur logique **D** (0-1439) du lecteur `DCDRV` dans le tampon pointé par **X** |
| `WRSEC` | `$0026` | écrit le secteur logique D depuis le tampon pointé par X |

Bloc de paramètres de `DSKCON` :

| Adresse | Nom | Contenu |
|---|---|---|
| `$BDC0` | `DCOPC` | opération : 0 = restaurer (piste 0), 1 = état de protection, 2 = lire secteur, 3 = écrire secteur, 4 = avancer d'une piste, 5 = formater la piste |
| `$BDC1` | `DCDRV` | lecteur 0 ou 1 |
| `$BDC2` | `DCCYL` | cylindre (bits 0-6) et face (bit 7) |
| `$BDC3` | `DCSEC` | secteur |
| `$BDC4-5` | `DCBUF` | adresse du tampon |
| `$BDC6` | `DCSTA` | statut : `$04` données perdues, `$08` erreur CRC, `$10` enregistrement introuvable / erreur de positionnement, `$40` protégé en écriture, `$80` lecteur non prêt |

## Contrôleur MCX32-FDJ [A, S7]

Carte d'extension de Darren Atkinson : contrôleur **WD177x** (registres en `$BDFC-$BDFF` : commande/état, piste, secteur, données) + EEPROM de 32 Ko (2 banques de 16 Ko, chacune en 2 pages de 8 Ko).

- **Banque 0** : code d'amorçage + Disk BASIC pour Alice 32 (et 90) ; la banque 1 est réservée à un autre modèle (Alice 4K) et sans objet ici.
- Page haute de chaque banque (`$E000-$FFFF`) : version **patchée du MicroColor BASIC** ; page basse (vue en `$0000-$1FFF`) : pilote disque, système de fichiers, extensions BASIC. **La moitié basse de la ROM interne (`$C000-$DFFF`) n'est pas remplacée.**
- Carte mémoire : voir `02-carte-memoire.md`. Zone `$BC00-$BDFF` : motif de 256 octets × 2 : registres de contrôle `$BDF0-$BDFB`, WD177x `$BDFC-$BDFF`, copies de ces registres aux autres décalages, 16 à 32 octets de RAM par bloc ; **n'utiliser que `$BDF0-$BDFF`**.

### Registres de contrôle `$BDF0-$BDFB` [A, S7 ; relus sur l'image de la page]

`$BDF1-$BDF3` sont des copies de `$BDF0`, `$BDF5-$BDF7` de `$BDF4`, `$BDF9-$BDFB` de `$BDF8`. **`$BDF8` (bits 7 et 0 : 2 bits) sert de « page » et change le sens de `$BDF0` et `$BDF4`** :

| Page `$BDF8` (b7 b0) | `$BDF0` | `$BDF4` |
|---|---|---|
| `00` | L/E : b7 = moteurs (0 arrêt, 1 marche) ; b0 = lecteur sélectionné (0 ou 1) | **E** : b7 = NMI autorisée (1) ou non (0) ; b0 = face 0/1. **L** : état DRQ du WD177x |
| `01` | **E** : b0 = densité (0 = MFM double, 1 = FM simple) | inutilisé |
| `10` | L/E : b7 = `$E000-$FFFF` vers EEPROM (0) ou ROM interne (1) ; b0 = banque EEPROM 0/1 | **E** : b7 = RAM en `$5000-$AFFF` désactivée (0) / activée (1). **L** : b0 = état du cavalier HI/LO |
| `11` | inutilisé | **E** : b7 = écriture EEPROM interdite (0) / autorisée (1) ¹ |

¹ Pour écrire dans l'EEPROM il faut mettre b7 de `$BDF4` à 1 **et** régler `$BDF8` avec b7 = 1 et b0 = 0 : seule combinaison permise.

Autres informations utiles :

- La séquence de démarrage/DOS (`DOS` charge un secteur 0) n'est pas décrite en détail ; le programme `disk-asm-patch` du site (`ASMD.BIN`) n'a pas été étudié.

Attention : cette carte est **un périphérique d'extension** : une Alice 32 sans MCX32-FDJ n'a ni disque, ni `FILSYS`. Des variantes carte SD (`MCX32-SD`) et disquette (`MCX32-FDJ`) d'un même programme apparaissent dans l'archive de *Sokoban* (`sokoban_alice32sd.zip`, `sokoban_alice32dsk.zip`) ; le fonctionnement de l'interface SD n'est pas documenté dans l'archive.
