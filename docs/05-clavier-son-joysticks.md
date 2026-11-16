# Clavier, son, manettes, minuterie

Sources : *Les Astuces d'Alice* (S20, chapitres 2 et 6), source commentée de la ROM V0.70 (S19), Tetrice (S9), Sokoban en FIG-Forth (S21), Tuiles curieuses (S8).
Légende : **[A]** documenté, **[B]** déduit de la ROM, **[C]** hypothèse.

## 1. Clavier

### 1.1 Lecture par la ROM (la plus simple)

| Routine | Adresse | Effet |
|---|---|---|
| `OS_getKey` (« KDINP ») | `$F868` | **attend** une touche, curseur clignotant ; code ASCII dans A ; pas d'écho à l'écran |
| `OS_POLCA` (« POLCA ») | `$F883` | **ne bloque pas** : A = code ASCII de la touche enfoncée, ou 0 et Z = 1 si aucune ; préserve B et X |
| `OS_printCHAR` (« OUTCA ») | `$F9C6` | affiche le caractère A (écran, ou imprimante si `$E8` ≠ 0) |
| `OS_OUTTX` (« OUTTX ») | `$E7A8` | affiche la chaîne pointée par X+1, terminée par `$00` ; s'arrête aussi sur un guillemet `"` |
| `LIPTR` (« LIPRT ») | `$F419` | affiche D (0-65535) en décimal |

Exemple de boucle de jeu sur POLCA **[A]** :

```asm
        jsr  $F883       ; POLCA
        beq  rien        ; Z = 1 : aucune touche
        ; A = code ASCII (flèches $08-$0B, ENTER $0D, BREAK $03)
```

Codes particuliers **[A]** : BREAK `$03` ; ← `$08` ; → `$09` ; ↓ `$0A` ; ↑ `$0B` ; ENTER `$0D` ; espace `$20`.
(Le listing d'Alicetel donne `$92` à l'OCR : valeur erronée, non retenue.)
SHIFT+`@` et CONTROL+`@` ne renvoient **aucun code** : ils basculent des indicateurs (majuscules/minuscules, couleur des caractères graphiques).
Il n'y a **pas d'interruption** clavier : la ROM scrute la matrice à chaque appel.

### 1.2 Redéfinir les touches [A, S20 ; B]

L'adresse **`$3009-$300A` (`TABAD`)** contient un pointeur vers un tableau de 4 adresses de tables (normale, CONTROL, SHIFT, CONTROL de nouveau). Valeurs par défaut en ROM : `TABAD = $D421` ; ce tableau contient `$F986` (normale), `$D838` (CONTROL), `$D800` (SHIFT), `$D838`.
Chaque table fait 57 octets : l'entrée d'index **1 + 8 × ligne + colonne** donne le code de la touche située à cette ligne (0-6) et cette colonne (0-7) de la matrice ; l'index 0 n'est pas une touche. Exemples : `@` = 1, `Q` = 2, `H` = 9, BREAK = `$33`, flèche ← = `$34`, ↑ = `$37`.
Pour changer l'affectation (AZERTY → QWERTY, touches de jeu…), recopier une table en RAM, la modifier, puis écrire son adresse dans `$3009-$300A`.
Codes par défaut des tables **[A, S20]** : lettres en ASCII majuscule (`$41…`), chiffres `$30-$39`, ponctuation ASCII ; certaines combinaisons SHIFT/CONTROL donnent des codes `$80-$FF` : **caractères semi-graphiques** de l'écran standard.

### 1.3 Lecture directe de la matrice (jeux d'action) [A]

Matrice de **8 colonnes × 7 lignes**. Le **port 1** (`$02`) est programmé en sortie, le **port 2** (`$03`) en entrée à l'initialisation.

1. écrire dans `$02` un masque dont **un seul bit est à 0** (colonne choisie) : `$FE, $FD, $FB, $F7, $EF, $DF, $BF, $7F` pour les colonnes 0 à 7 ;
2. lire **`$BFFF`** : les bits 0 à 5 donnent les lignes 0 à 5 ; **bit à 0 = touche enfoncée** ; la ligne 6 est la rangée des touches spéciales (voir tableau) ;
3. recommencer pour chaque colonne utile.

| Col. | masque | L0 | L1 | L2 | L3 | L4 | L5 | L6 |
|---|---|---|---|---|---|---|---|---|
| 0 | `$FE` | `@` | `H` | `P` | `X` | `0` | `8` | CONTROL ¹ |
| 1 | `$FD` | `Q` | `I` | `A` | `Y` | `1` | `9` | — |
| 2 | `$FB` | `B` | `J` | `R` | `W` | `2` | `:` | BREAK |
| 3 | `$F7` | `C` | `K` | `S` | — | `3` | `M` | ← |
| 4 | `$EF` | `D` | `L` | `T` | — | `4` | `,` | → |
| 5 | `$DF` | `E` | `/` | `U` | — | `5` | `-` | ↓ |
| 6 | `$BF` | `F` | `N` | `V` | ENTER | `6` | `.` | ↑ |
| 7 | `$7F` | `G` | `O` | `Z` | ESPACE | `7` | `+` | SHIFT ¹ |

¹ **SHIFT et CONTROL se lisent sur le port 2** : pour SHIFT, écrire `$7F` dans `$02` puis lire `$03` : **le bit 1 est à 0 si SHIFT est enfoncée** ; pour CONTROL, écrire `$FE` dans `$02` puis lire `$03` : bit 1 à 0 si CONTROL est enfoncée.

Les cases « — » sont vides : il n'y a aucune touche. (Le livre place le X en colonne 1 / ligne 6 : c'est une erreur de l'ouvrage, corrigée par l'auteur de Tetrice, qui a vérifié que le X est en colonne 0 / ligne 3.)
Le dessin du clavier du schéma (S1) confirme la disposition des lettres.

Bonnes pratiques [A, S20] : relire la colonne après quelques ms pour éviter les **rebonds** ; attendre le relâchement d'ENTER au lancement d'un programme (*Tuiles curieuses* le fait).

Code C de Tetrice (S9) :

```c
POKE(0x0002, masque[col]);   // colonne
key = PEEK(0xBFFF);          // lignes
if (key == 0xFF) continue;   // rien
key = ~key;                  // bit à 1 = touche enfoncée
// rang du premier bit à 1 → ligne 0..5 ; rang > 5 ignoré
```

**Attention** : le registre `$BFFF` sert **aussi au son** (voir plus bas) : écrire dans `$BFFF` ne modifie pas la colonne ; c'est `$02` qui la choisit.

## 2. Son

Le son est produit par un **haut-parleur 1 bit** : on **inverse le bit 7 de `$BFFF`** en écriture, ce qui crée un signal carré (la ROM le nomme `IO_COL_KBD`).

### 2.1 Routine de la ROM : `$FFA5` / `$FFAB` [B, S19]

`SOUND n1, n2` du BASIC (octet `$9E`, `n1` et `n2` de 1 à 255, `n2` en unités d'environ 75 ms) appelle `romSOUND` (`$FFA5`), qui lit les deux paramètres puis entre en **`$FFAB`** avec **A = n1** et **B = n2**. On peut donc appeler directement `$FFAB` depuis le langage machine :

```asm
        ldaa #n1         ; hauteur : plus n1 est grand, plus le son est aigu [B]
        ldab #n2         ; durée
        jsr  $FFAB
```

Fonctionnement : boucle de B périodes ; chaque période attend l'événement « comparaison de sortie » du compteur du 6803 (64 K cycles d'horloge) ; entre-temps inverse le bit 7 de `$BFFF` en attendant `256 − n1` pas de boucle. Particularités importantes :

- elle **utilise le registre de comparaison de sortie du timer** (`$0B-$0C`) : ne pas la combiner avec ses propres interruptions de comparaison ;
- elle **bloque le clavier** pendant le son (le signal passe par la ligne de lecture du clavier) ;
- elle **modifie X**, A et B ; elle remet `$BFFF` à 0 à la fin.

### 2.2 Routine maison (Tuiles curieuses, S8) [A]

```asm
SOUND_PORT equ $BFFF
        clra
loop:   pshx             ; durée sur la pile
        eora #$ff        ; inverse le signal
        staa SOUND_PORT
        ...              ; attente de « hauteur » itérations (dex / bne)
        pulx
        dex              ; durée - 1
        bne  loop
        rts
```

Une routine maison permet de **jouer du son sans bloquer le jeu** en ne faisant qu'une inversion par image ou par interruption timer ; voir `13-programmation-jeux.md`.

## 3. Manettes (joysticks)

Octets d'état lisibles en **`$BF30` (manette droite)** et **`$BF34` (manette gauche)** ; la zone `$BF30-$BF37` est émulée « comme la vraie machine » par DCAlice (S2). Leur codage brut est établi par le Sokoban en FIG-Forth (S21) **[A]** :

| Position (manette droite) | Valeur lue en `$BF30` |
|---|---|
| repos | `$3F` |
| haut | `$3E` |
| bas | `$3D` |
| gauche | `$3B` |
| droite | `$37` |

→ **bits 0 à 3 = haut, bas, gauche, droite, actifs à 0** ; le bit 5 vaut 1 en permanence (masque `$3F` au repos). Le bit 4 est très probablement le **tir** (actif à 0, soit `$2F` seul) **[C]**. Le Disk BASIC (`JOYSTK(0)` gauche, `JOYSTK(1)` droite) retourne un entier : bit 0 haut (1), bit 1 bas (2), bit 2 gauche (4), bit 3 droite (8), bit 4 tir (16) **[A, S5]** : c'est l'inverse logique des octets bruts, aux bits 0-4.
Le Sokoban transforme une valeur de manette en code de flèche (`$5E` pour haut dans son code : c'est son propre choix ; `$0A` bas, `$09` droite, `$08` gauche) et ne lit la manette qu'au changement de valeur, puis appelle `POLCA` : modèle simple pour accepter à la fois clavier et manette.
Certaines manettes provoquent des déplacements rapides : *In The Dark* conseille le clavier (S13). DCAlice permet de connecter ou déconnecter chaque manette (S2).

## 4. Minuterie du 6803

- Le compteur libre `$09-$0A` s'incrémente à chaque **cycle d'horloge E = 1 µs** (quartz 4 MHz / 4) et déborde toutes les **65,536 ms** (≈ 15,26 fois par seconde : 15 débordements ≈ 0,98 s) **[A, S20, S9]**.
- Registre `TCSR` (`$08`) : bit 7 ICF, **bit 6 OCF** (comparaison de sortie), **bit 5 TOF** (débordement). TOF se remet à 0 par lecture de `TCSR` puis de `$09`. OCF par lecture de `TCSR` puis écriture de `$0B/$0C`.
- Registre de comparaison de sortie `$0B-$0C` ; **la capture d'entrée est inutilisable** sur l'Alice (les ports 1 et 2 servent au clavier).
- Avec les interruptions : vecteur TOF `$FFF2` → trampoline RAM **`$3203`** (voir `03-registres-et-ports.md`) ; à l'initialisation la ROM y met des `RTI` espacés de 3 octets, qu'on remplace par un `JMP` vers sa routine.
- Pour des **tops plus courts qu'une trame** (50 Hz = 20 ms), utiliser OCF avec `$0B-$0C` (sans appeler SOUND de la ROM).
- Idée de S20 : le compteur sert aussi de **générateur pseudo-aléatoire** (`ANDB #7` sur `$0A`).
- Le BASIC propose `TIMER` (Disk BASIC) **[A, S5]**.
