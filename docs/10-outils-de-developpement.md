# Outils de développement

Sources : guide de l'éditeur-assembleur résident (S22), source commenté de la ROM (S19), *In The Dark* (S13), *Tuiles curieuses* (S8, Makefile et script MAME), notice DCAlice (S2), *Les Astuces d'Alice* (S20).
Légende : **[A]** documenté, **[B]** déduit, **[C]** hypothèse.

Il y a trois façons de produire du code pour l'Alice 32 : **sur la machine** (assembleur résident en ROM), **en croisé sur PC** (DASM, ou C avec CC6303), et **tester** sous émulateur (DCAlice, MAME) ou sur la vraie machine (cassette, cartouche). Pour des jeux ou des démos de plus de quelques centaines d'octets, la voie recommandée est **DASM sur PC + DCAlice**, qui est celle de *In The Dark* **[A, S13]**.

## 1. Assembleur résident de l'Alice 32 (ROM `$C000-$DFFF`)

L'éditeur-assembleur est en ROM : il n'y a rien à charger **[A, S22]**. Il est de Matra (« ASSEMBLEUR ALICE REV 71.00, COPYRIGHT MATRA 1984 » d'après l'exemple du guide).

### 1.1 Préparer et entrer

1. Sauvegarder le BASIC en mémoire puis faire `NEW`.
2. Réserver la zone du **fichier source** : `CLEAR LN,AD` avec `LN > 60` et `AD` = adresse de stockage du source. Plages indiquées par le guide : sans extension, de 13250 à 20480 environ ; avec l'extension 16 Ko, de 13250 à 36864 **[A, S22]** (le texte OCR de la borne haute sans extension est abîmé : à vérifier).
3. Entrer dans l'éditeur : `EXEC 49152` (`$C000`, début de la ROM de l'assembleur) **[A, S20 ; B]**. L'écran passe en fond bleu, curseur clignotant.
4. Après une erreur ou un retour au BASIC, un nouvel appel d'entrée **récupère le source** tant qu'aucune commande BASIC n'a été tapée entre-temps **[A, S22]**.

Mémoire disponible : environ 7 Ko sans extension (≈ 300 lignes de source, ≈ 1 Ko de code objet) ; avec l'extension 16 Ko, ≈ 1000 lignes et ≈ 4 Ko de code **[A, S22]**. C'est donc **limité pour un jeu**, mais suffisant pour une routine ou une démo courte.

### 1.2 Éditeur

Éditeur « pleine page » : tout l'écran sauf la dernière ligne (dialogue). Fonctionne en 40 ou 80 colonnes. Une ligne est validée en la quittant avec ENTER ou les déplacements verticaux. Deux appuis sur BREAK reviennent au BASIC ; INIT en cas de plantage. Les commandes sont des combinaisons **CTRL + lettre** : le guide en donne la fonction (déplacement, effacer/insérer ligne ou caractère, répétition des touches, recherche par numéro de ligne ou par texte, sauvegarde/chargement/vérification/fusion sur cassette, copie sur imprimante, assemblage), mais **la lettre de chaque commande est une image** perdue à l'OCR : les lettres ne sont pas reproduites ici **[C]**. À reprendre en lisant le guide original.

Seules les lignes situées après le curseur sont concernées par la recherche de chaîne. Annuler une commande qui demande une réponse : BREAK.

### 1.3 Format des lignes **[A, S22]**

```
ETIQUETTE  MNEMONIQUE  OPERANDE   ; commentaire
```

- **Étiquette** : colonne 1 (contre le bord gauche), **5 caractères au plus**. Une ligne qui commence par un espace n'a pas d'étiquette.
- **Mnémonique ou directive** : après au moins un espace. Tous les éléments d'une ligne sont séparés par au moins un espace.
- **Valeurs** : **hexadécimal** uniquement, préfixé de `$` (pas de décimal ni de binaire) ; `#` = immédiat ; `<` devant l'opérande = adressage direct en page zéro ; `n,X` = indexé ; sans préfixe = étendu.
- **Commentaire** : après `;`.
- Synonymes acceptés : `LSL`=`ASL`, `BHS`=`BCC`, `BLO`=`BCS`.

| Directive | Rôle |
|---|---|
| `ORG $adr` | **obligatoire en première ligne** : adresse d'implantation du code. Plage : `$3000-$4FFF` sans extension, jusqu'à `$5FFF` avec l'extension 16 Ko (attention à ne pas écraser le source) |
| `EXC $adr` ou `EXC étiquette` | point d'entrée (première instruction exécutée) |
| `ETIQ = $1234` | affecte une valeur à une étiquette |
| `'texte` | place du texte ASCII à l'adresse courante |
| `BLC $nn` | réserve un bloc de nn octets (255 au plus) |
| `DFO $nn` / `DFD $nnnn` | définit un octet / deux octets (poids fort d'abord) |

Il n'y a pas de macros ni de `INCLUDE`. Pas de `EQU` : on écrit `=`.

Exemple du guide (extrait, programme d'essai qui produit du bruit en inversant le bit 7 de `$BFFF`, il **boucle** sans fin) :

```
        ORG $4800
        EXC INIT
INIT    LDX #$0001
        STX COMPT
DEBUT   CLRA
        LDAB #$30
BRUIT   LDX COMPT
        EORA #$80
        STAA $BFFF        ; adresse qui fait du bruit
BOUCL   DEX
        BNE BOUCL
        DECB
        BNE BRUIT
        ...
COMPT   DFD $0
```

### 1.4 Assembler et lancer

La commande d'assemblage demande le **support du listing** (écran, imprimante, ou écran réduit aux erreurs), puis un **nom pour le fichier objet** sur cassette (ENTER pour ne pas le sauvegarder), puis propose d'**exécuter** le programme (OUI/NON). Après l'exécution l'Alice repasse en BASIC. L'assemblage se fait **en deux passes**, et le listing affiche numéro de ligne, adresse, octets (6 caractères au plus), ligne source, nombre d'erreurs par passe, puis la table des symboles **[A, S22]**. SHIFT+@ suspend le défilement.

Codes d'erreur de l'assembleur **[A, S22]** :

| Lettre | Sens | Lettre | Sens |
|---|---|---|---|
| A | table de symboles pleine | I | registre inconnu |
| B | symbole déjà défini | J | adressage indexé incorrect |
| C | valeur > 255 (adressage direct) | K | branchement relatif hors portée |
| D | expression incomplète | L | ORG déjà défini |
| E | expression inexistante | M | plus de place pour l'objet |
| F | expression erronée | N | pas de `ORG` |
| G | symbole inexistant | O | instruction incomplète |
| H | instruction inconnue | P | instruction inexistante (ex. `STAA #…`) |

Codes de l'éditeur (ERREUR n + bip) : 1 erreur de lecture cassette (donnée), 2 erreur de lecture (mémoire), 3 fichier plus gros que la mémoire, 4 mémoire pleine, 6 chaîne introuvable, 7 nombre incorrect, 8 type de fichier incorrect (le fichier n'a pas été créé par l'éditeur) **[A, S22]**.

### 1.5 Routines utiles données par le guide (annexe 4)

| Adresse | Rôle |
|---|---|
| `$F883` | scrutation du clavier (A = 0 si aucune touche) |
| `$F9C6` | émet A : écran si `$E8` = 0, imprimante si `$E8` = 1 ; position écran en `$3280` (rangée) et `$3281` (colonne) |
| `$E7A8` | émet la chaîne pointée par X (terminée par 0) |
| `$FBD4` | efface l'écran |
| `$F7AD` | copie un tableau (X = source, dont le premier mot est la taille en octets ; D = destination) |
| `$FFAB` | son : A = fréquence 1-255, B = durée 1-255 |

Voir `06-rom-et-points-d-entree.md` pour la liste complète.

## 2. DASM sur PC (recommandé)

**DASM** est un assembleur croisé multiprocesseur en ligne de commande. Il gère le 6803 avec `PROCESSOR 6803` **[A, S13, S19]**. Le source commenté de la ROM s'assemble avec lui en produisant un binaire **identique octet par octet** à `alice32.rom` **[A, S19]** : c'est la meilleure preuve que cette chaîne convient.

Syntaxe utile (différences avec l'assembleur résident) **[B : connaissance générale de DASM, recoupée par `exemples/squelette-jeu.asm` qui s'assemble]** :

- `PROCESSOR 6803` en tête, `ORG $4000` pour l'adresse ;
- constantes : `NOM EQU valeur` (ou `NOM = valeur`) ; octets : `dc.b` (et non `FCB`) ; mots : `dc.w` ;
- les **étiquettes commencent en colonne 0**, les instructions sont indentées ;
- décimal, binaire (`%…`) et hexadécimal (`$…`) acceptés, noms d'étiquettes longs, `INCLUDE`, macros, `IF/ENDIF`, `REPEAT/REND`, `ALIGN` ;
- commande type, sortie binaire brute : `dasm prog.asm -f3 -oprog.bin -lprog.lst -sprog.sym` (`-f3` = binaire sans en-tête, comme pour la ROM).

Le binaire brut commence à l'adresse de `ORG` : il reste à le charger à cette adresse (§ 4).

Le dépôt fournit `exemples/squelette-jeu.asm` (172 octets à `$4000`, `EXEC 16384`) qui s'assemble sans erreur avec DASM ; **il n'a pas été exécuté** sous émulateur **[A]**.

## 3. CC6303 / `cc68` (langage C)

*Tuiles curieuses* (S8) est écrit en **C** avec quelques routines assembleur, compilé avec **CC6303** (`/opt/cc68/bin/cc68`, `as68`, `ld68`) en ciblant le **Tandy MC-10** (même processeur, même BASIC ; options `-D__TANDY_MC10__`, `-m6803`) **[A, S8]**. Options de l'éditeur de liens du Makefile : `-b -C 4096 -D 13126 -Z 0x90` : code à `$1000` (cartouche), données à 13126 (`$3346`, début de la RAM BASIC), **page zéro à partir de `$90`** parce que « les 32 premiers octets sont utilisés par le système » **[A]**. On s'en sert pour deux sortes de sortie :

- **cartouche** : binaire de 4 Ko ou plus à `$1000`, lancé par `EXEC 4096` (`ld68` puis retrait des 4096 premiers octets) ;
- **cassette** : `cc68 … -tmc10 -o build/tape` produit un `.c10` renommé en `.k7`, chargé par `CLOADM` puis `EXEC 17500` **[A, S8]** (adresse propre à ce jeu).

Le C est confortable pour la logique, mais pour des **jeux rapides ou des démos** à cycles comptés, le code critique (affichage, raster, son) doit rester en assembleur, comme dans ce projet (`ef9345_routines.s`, `sound_routines.s`).

## 4. Charger et lancer un binaire

| Moyen | Procédure | Source |
|---|---|---|
| **Cassette** (`.k7`, `.wav`) | `CLOADM` puis `EXEC adr` (ou `RUN` pour *In The Dark*) | S13, S8, S3 |
| **Cartouche** (`.rom`) | chargée dans la fenêtre `$1000-$2FFF`, lancée par `EXEC 4096` | S13, S2, S8 |
| **RAM** | écrire l'objet en RAM (POKE depuis un chargeur BASIC), `EXEC adr` | S20 |
| **Assembleur résident** | OUI à « exécuter » après l'assemblage | S22 |

Pour fabriquer un `.k7` à partir d'un binaire brut, voir `09-cassette-et-formats-de-fichiers.md` (`dcalicek7`, formats `.k7`/`.wav`).

Pour qu'un binaire soit lancé directement au démarrage sans commande, une cartouche doit avoir le format attendu par la ROM : détails à étudier **[C]** (voir `12-questions-ouvertes.md`).

## 5. Émulateurs et débogage

### 5.1 DCAlice (Daniel Coulom)

- Émulateur Windows de l'Alice 32 (aussi MC-10, Alice 4K, Alice 90), écrit par Daniel Coulom, en continu depuis 2005 **[A, S2]**. Version fournie : 20260504.
- Fonctions utiles : chargement de cassette (`.k7`, `.wav`, `.txt` BASIC converti à la volée), cartouche (8 banques de 8 Ko), manettes, **débogueur** (désassemblage, points d'arrêt), disquettes MCX32-FDJ **[A, S2]**.
- Limites pour la programmation fine : l'EF9345 est émulé avec un **temps d'exécution fixe de 30 cycles** par commande, donc ne donne pas les vraies durées **[A, S2]** ; ne pas déduire les performances de l'émulateur. *In The Dark* demande une version 2024.03.19 ou plus récente **[A, S13]**.
- Programme Windows ; son `.exe` n'a pas été exécuté pour ce dépôt.

### 5.2 MAME (pilote `alice32`)

*Tuiles curieuses* se lance ainsi **[A, S8]** :

```
mame alice32 -max -ui_active -ext multi -cart build/match.64k.rom     # cartouche (extension « multiports »)
mame alice32 -max -ui_active -ext ram   -cass build/match.k7           # cassette, extension RAM
mame … -debug                                                          # avec le débogueur
```

Le Makefile prévient qu'il utilise une **version de MAME avec l'extension Multiports** personnalisée ; selon la version de MAME l'option `-ext multi` peut ne pas exister **[A, S8]**.
L'auteur fournit un script Lua (`alice_boot.lua`, licence MIT) qui : met en pause l'émulateur ; lance jusqu'au **point d'arrêt `$E274`** (invite « prêt » du BASIC) ; puis saisit `EXEC 4096` au clavier virtuel : c'est un modèle d'automatisation d'un test en ligne de commande **[A, S8]**. MAME offre un **débogueur complet** (points d'arrêt, mémoire, désassemblage) ; la fidélité de son modèle d'EF9345 aux durées réelles n'est pas établie **[C]**.

### 5.3 Vraie machine

Un Alice 32 fonctionne avec : cassette (`.wav` joué sur le magnétophone, 44 100 Hz 8 bits mono recommandé) ou **cartouche** (fichier `.rom` des jeux de l'archive). *In The Dark* a été testé sur vraie machine par des testeurs, avec cassette et cartouche **[A, S13]** ; l'auteur avait perdu sa machine et n'a pas pu tout tester : **les comportements EF9345 sont à valider sur le matériel** **[A]**.

## 6. Flux de travail recommandé

1. Écrire le programme en assembleur 6803 (DASM), avec des constantes d'après `03-registres-et-ports.md` et `04-ef9345-video.md`.
2. Assembler : `dasm prog.asm -f3 -oprog.bin -lprog.lst -sprog.sym`.
3. Convertir en `.k7` ou `.rom` selon le cas, charger dans DCAlice ou MAME.
4. Déboguer avec le débogueur (points d'arrêt sur le vecteur et la boucle principale).
5. Valider les **durées et effets vidéo** sur le matériel réel avant de les considérer comme acquis (voir `12-questions-ouvertes.md`).
6. Documenter ici toute découverte sous forme [A] avec la procédure de test.

## 7. Compter les cycles

Le 6803 de l'Alice tourne avec une horloge E de **1 MHz (1 cycle = 1 µs)**. Cycles (datasheet MC6803, table des instructions, S23) : `LDAA` immédiat 2 / direct 3 / étendu 4 ; `STAA` direct 3 / étendu 4 ; `INX`, `DEX` 3 ; `TST` étendu 6 ; branchement 3 ; `MUL` 10 ; `JSR` étendu 6 ; `BSR` 6 ; `RTS` 5 ; `LDD` et `STD` étendu 5 **[A, S23]**. Une boucle `DEX/BNE` coûte donc 6 µs par tour ; une image à 50 Hz dure 20 ms, soit **≈ 20 000 cycles** pour tout faire, dont une partie perdue en attente de l'EF9345 (voir `13-programmation-jeux.md`).
