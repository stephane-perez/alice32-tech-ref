# Carte mémoire de l'Alice 32

Sources principales : tableau du contrôleur MCX32-FDJ (S7), notice DCAlice (S2), *Les Astuces d'Alice* annexe 2 (S20), source commentée de la ROM (S19), *Tuiles curieuses* (S8), schéma (S1).
Étiquettes : **[A]** documenté, **[B]** déduit, **[C]** hypothèse.

## Vue d'ensemble

| Adresses | Contenu | Remarques |
|---|---|---|
| `$0000-$0003` | ports d'E/S du 6803 | `$0002` (port 1) sert à choisir la colonne du clavier **[A, S9]** |
| `$0008-$000E` | timer du 6803 (TCSR, compteur, comparaison, capture) | **[A, S8]** |
| `$0010-$001F` | registres série et RAM-control du 6803 (RAMCR en `$0014`) | **[A, S7]** |
| `$0020-$007F` | utilisé par l'extension MCX32-FDJ pour son EEPROM ; sans cette extension, rien d'utile connu | **[A, S7]** |
| `$0080-$00FF` | RAM interne du 6803 (page directe). Les 32 premiers octets de cette zone sont réservés au système : le compilateur C de *Tuiles curieuses* place ses variables de page zéro à partir de `$90` | **[A, S7, S8]** |
| `$0100-$0FFF` | non utilisé sur la machine de base ; EEPROM de page basse avec le MCX32-FDJ | **[A, S7]** |
| `$1000-$2FFF` | **fenêtre cartouche / extension** : RAM, cartouche ou rien selon le matériel. DCAlice émule une cartouche de **8 banques de 8 Ko max** visibles ici ; on lance un jeu en cartouche avec `EXEC 4096` (`$1000`) | **[A, S2, S8]** |
| `$3000-$4FFF` | **RAM interne (8 Ko)** : variables système et BASIC en `$3000-$3345`, **programme BASIC à partir de `$3346`**, pile système à partir de `$4F94` | **[A, S7], [B, S19]** |
| `$5000-$AFFF` | RAM d'extension (16 Ko d'extension sur Alice 32) | **[A, S7, S8]** |
| `$B000-$BBFF` | RAM externe « avec exclusions » : motif de 256 octets répété 12 fois (voir plus bas) | **[A, S7]** |
| `$BC00-$BDFF` | RAM / registres de contrôle et du contrôleur de disquette (MCX32-FDJ) | voir `08-...` |
| `$BE00-$BFFF` | E/S de la machine : EF9345 (`$BF20-$BF28`), manettes (`$BF30-$BF37`), clavier + son (`$BFFF`), ACIA 6850 de l'interface Minitel (`$BF40…`) | **[A, S7, S8, S10]** |
| `$C000-$DFFF` | ROM interne : assembleur résident Matra + table de saut vidéo (`$D400…`) ; **jamais remplacée** par le MCX32-FDJ | **[A, S7], [B, S4]** |
| `$E000-$FFFF` | ROM : MicroColor BASIC 1.0, routines clavier/écran/son, vecteurs en `$FFF0-$FFFF` ; remplaçable par l'EEPROM du MCX32-FDJ (Disk BASIC) | **[A, S7], [B, S4]** |

## Détail de `$B000-$BBFF` (motif de 256 octets × 12) [A, S7]

| Décalage | Contenu |
|---|---|
| `+$B0..+$FF` | 80 octets de RAM |
| `+$A0..+$AF` | indéfini |
| `+$90..+$9F` | 16 octets de RAM |
| `+$80..+$8F` | indéfini |
| `+$30..+$7F` | 80 octets de RAM |
| `+$20..+$2F` | **copies de l'EF9345** (Alice 32/90) — d'où le `$BF20` des registres |
| `+$10..+$1F` | 16 octets de RAM |
| `+$00..+$0F` | indéfini |

Conséquence pratique : une écriture dans `$B020` atteint le même registre EF9345 qu'une écriture dans `$BF20` ; ne pas ranger de données à ces adresses.

## RAM système `$3000-$3345`

Variables du BASIC, de l'assembleur, de l'écran, de la cassette ; trampolines d'interruption `$3200-$3214` ; 14 crochets `$3285-$32AC` ; tampon clavier `$32B2`. La liste commentée est dans `06-rom-et-points-d-entree.md` §4. Le clavier se redéfinit par `$3009` (voir `05`).

## Mémoire vidéo (hors de l'espace du 6803)

La **mémoire privée de l'EF9345 (8 Ko)** n'est **pas** dans la carte du processeur : on y accède par les registres `$BF20-$BF2F` et des commandes (voir `04-ef9345-video.md`). Avec la configuration de la ROM : page de caractères dans les blocs 0 à 2 (C, B, A), jeu de caractères redéfinissables G'0 dans le bloc 3.

## Zone de pile et programmes

- Les programmes en code machine chargés depuis cassette se placent dans la RAM BASIC ; *Tuiles curieuses* en mode cassette s'exécute à `EXEC 17500` (`$445C`) et nécessite 16 Ko d'extension sur Alice 32 **[A, S8]**.
- En mode cartouche, le code est lié à `$1000` et les données à partir de `$3346` (13126) **[A, S8, Makefile : `-C 4096 -D 13126`]**.
