# Processeur vidéo EF9345 (Alice 32)

Sources : fiche constructeur SGS-Thomson (mars 1995, **S17**), note d'application AN325 « EF9345 general application principles » (**S18**), source commentée de la ROM V0.70 (**S19**, constantes `cVDP_*` et tables d'initialisation), programmes qui tournent (S8 *Tuiles curieuses*, S9 *Tetrice*).
Les datasheets sont des scans lus par OCR ; **les valeurs de ce document ont été relues sur l'image des pages** (tableau des commandes, schéma de DOR) ou recoupées avec la ROM.
Légende : **[A]** documenté, **[B]** déduit de la ROM ou du schéma, **[C]** hypothèse.
Ce document sert de référence ; les techniques pour jeux sont dans `13-programmation-jeux.md`.

## 1. Vue d'ensemble

- Contrôleur d'écran couleur « semi-graphique » **à puce unique** : sorties R, V, B, I (incrustation), synchro. Quartz de **12 MHz**, balayage 50 Hz / 625 lignes (TGS bit 0 = 0) sur l'Alice 32 **[A, B]**.
- Il possède sa **mémoire privée** (DRAM ; 8 Ko sur l'Alice 32) que le microprocesseur **n'atteint pas directement** : tout passe par les registres R0-R7 et des commandes.
- Deux formats d'écran : **25 (ou 21) rangées de 40 caractères** (cellule 8 × 10 points) ou **de 80 caractères** (cellule 6 × 10). Les caractères redéfinissables (UDS) n'existent qu'en 40 colonnes **[A]**.
- Jeu de caractères interne : 128 alphanumériques (G0) + 128 semi-graphiques ; extension par des jeux utilisateur en mémoire privée (plus de 1 000 caractères).
- Défilement vertical **matériel** (registre ROR), curseur matériel, clignotement, double hauteur/largeur, incrustation sur signal vidéo externe.
- L'Alice 32 le voit aux adresses **`$BF20-$BF2F`** (décodage `XX20` : le quartet haut de l'adresse reçue doit valoir `0010` **[A]**).
- Taille de la mémoire vidéo de l'Alice 32 : 2 circuits DRAM de 4 bits (schéma, voir `01-machines.md`) ; capacité de **8 Ko** (8 blocs de 1 Ko) **[A, S20 p. 82 et 138]** ; *Tuiles curieuses* utilise les blocs 0 à 5 **[A, S8]**. Au RESET (et par `INASS`), la ROM recopie la police Alice dans G'0 (bloc 3) **[A, S20]**.

## 2. Interface avec le 6803

### 2.1 Registres directs

| Adresse | Registre | Rôle |
|---|---|---|
| `$BF20` | R0 | **écriture** : commande ; **lecture** : état |
| `$BF21` | R1 | donnée (octet C d'un caractère, ou octet « tranche », ou valeur d'un registre indirect) |
| `$BF22` | R2 | donnée (octet B) |
| `$BF23` | R3 | donnée (octet A) |
| `$BF24-25` | R4, R5 | **pointeur auxiliaire** AP |
| `$BF26-27` | R6, R7 | **pointeur principal** MP (R6 = Y et Z, R7 = X et Z) |

**Règle capitale de l'exécution [A]** : chaque registre est visible à **deux adresses** : `$BF20+n` (bit 3 de l'adresse = 0) et `$BF28+n` (bit 3 = 1). Une commande chargée dans R0 n'est **exécutée qu'après un accès (lecture ou écriture) à une adresse haute `$BF28-$BF2F`**.
Conséquence : on charge la commande **une fois** dans R0 (`$BF20`), puis chaque écriture dans `$BF29` (R1 « avec exécution ») relance la même commande avec un nouvel argument. C'est la base des boucles d'affichage rapides (*Tuiles curieuses* l'utilise pour afficher une chaîne).

### 2.2 Registre d'état (lecture de R0) [A]

| Bit | Nom | Sens |
|---|---|---|
| 7 | **BUSY** | 1 pendant l'exécution d'une commande |
| 6 | Alarme | mis à 1 quand LXm ou LXa est à 1 **et** qu'une incrémentation est effectuée |
| 5 | LXm | X du pointeur principal valait 39 avant l'éventuelle incrémentation |
| 4 | LXa | idem pour le pointeur auxiliaire (ou fichier d'attributs plein pour KRV) |
| 3 | — | reflète le bit 7 de R1 |
| 2 | VSYNC | état de la synchro verticale : à 0 pendant 2 lignes TV par trame, à 1 le reste du temps ; **masquable** par VSM/VRM |
| 1-0 | — | inutilisés (0) |

Les bits 3 à 6 sont remis à 0 au début de toute commande. Le masque VSYNC est **indéterminé à la mise sous tension** : exécuter `VRM` (voir plus bas) pour que le bit 2 suive la synchro.
La routine `WAIT_VSYNC` de *Tuiles curieuses* teste le masque `$04` de R0, ce qui est cohérent avec ce tableau **[A + B]**.

### 2.3 Accès pendant une commande [A]

- **BUSY = 1** : seule la lecture de R0 est fiable ; écrire un autre registre est inefficace. **Toujours attendre BUSY = 0** avant de toucher R1…R7 :

```asm
attente: tst  $BF20      ; N = bit 7
         bmi  attente
```

- Écrire une nouvelle commande avec le bit d'exécution **pendant** qu'une autre tourne **interrompt** la première (les registres sont alors indéterminés).
- **À la mise sous tension** l'état de BUSY est indéterminé : lancer d'abord `NOP` (`$91`, voir le tableau) **sans tester BUSY**. La ROM de l'Alice fait de même (`NOP_EF9345`). *Remarque de la ROM :* son commentaire signale un risque de confusion entre `$90` et `$91` ; la valeur correcte du NOP est **`$91`**.
- Les commandes sont **suspendues pendant la dernière et la première ligne TV de chaque rangée active** (période d'environ **104 µs**) car le bus mémoire est alors occupé au chargement du tampon de rangée. VRM et VSM ne sont pas suspendues. Les accès aux registres indirects (IND) le sont aussi.
- Les temps d'exécution du tableau suivant sont donnés **en µs** (une unité = 12 périodes d'horloge = 1 µs).

## 3. Commandes (octet écrit dans R0)

Le bit 3 (`R/W`) vaut **0 = écriture des registres de données vers la mémoire** (le 6803 écrit dans le composant) et **1 = lecture**. Le bit 0 `I` = incrémentation automatique du pointeur après l'accès. Valeurs relues sur le tableau de la fiche constructeur et recoupées avec les constantes `cVDP_CMD_*` de la ROM **[A]**.

| Nom | Code (écr. / lect.) | Fonction | Registres | Durée écr. / lect. (µs) |
|---|---|---|---|---|
| **IND** | `$80+r` / `$88+r` | transfert R1 ↔ registre indirect *r* (0 = lecture de la ROM de caractères, 1 TGS, 2 MAT, 3 PAT, 4 DOR, 7 ROR) | R1 | 2 / 3,5 |
| **KRF** | `$00` + I / `$08` + I | caractère **fixe long 24 bits** (40 col.) : R1 = C, R2 = B, R3 = A | MP | 4 / 7,5 |
| **KRG** | `$02` + I / `$0A` + I | caractère fixe court 16 bits (40 col.) | MP | 5,5 / 7,5 |
| **KRV** | `$20` + I / `$28` + I | code **variable** 8/24 bits | MP, R5 | ≈ 3 + 3·j |
| **KRE** | `$10` + I / `$18` + I | code long « étendu » (accès à un code variable décompressé) | MP, R4 | 4 / 7,5 |
| **OCT** | `$30` + `p`·4 + I / `$38` + … | **octet** générique (pointeur principal ou, si bit 2 = 1, **auxiliaire**) : R1 ↔ mémoire | MP ou AP | 4 / 4,5 |
| **KRC** | `$40` + I / `$48` + I | caractère 80 col. court 8 bits | MP | 9 / 9,5 |
| **KRL** | `$50` + I / `$58` + I | caractère 80 col. long 12 bits (C + quartet A) | MP | 12,5 / 11,5 |
| **EXP** | `$60` | expansion d'une rangée de codes variables | MP, R4, R5 | < 247 |
| **CMP** | `$70` | compression d'une rangée | MP, R4, R5 | < 402 |
| **MVB** | `$D0` … `$DF` | **déplacement de tampons** d'octets | MP, AP | 2 + 4n |
| **MVD** | `$E0` … `$EF` | déplacement de paires d'octets | MP, AP | 2 + 8n |
| **MVT** | `$F0` … `$FF` | déplacement de triplets (**1 caractère long = 3 octets**) | MP, AP | 2 + 12n |
| **CLF** | `$05` | **effacer la page** 24 bits : R1, R2, R3 recopiés partout | MP | < 4 700 pour 1 K codes |
| **CLG** | `$07` | effacer la page 16 bits | MP | < 5 800 |
| **VSM** | `$99` | masquer VSYNC dans l'état (bit 2 reste 0) | — | 1 |
| **VRM** | `$95` | **démasquer** VSYNC (bit 2 suit la synchro) | — | 1 |
| **INY** | `$B0` | Y du pointeur principal + 1 | — | 2 |
| **NOP** | `$91` | ne rien faire ; **sert aussi à arrêter une commande qui ne s'arrête pas seule** (CLF, MVx sans arrêt) | — | 1 |

(n = nombre d'éléments déplacés, ≤ 40 ; j = 1 pour un code long.)

**Paramètres des déplacements MVB/MVD/MVT** : `1 1 x x | s s̄ a a` : le quartet haut donne le type (`$D` MVB, `$E` MVD, `$F` MVT) ; dans le quartet bas, les bits 3-2 `s s̄` choisissent le sens (`01` : source = MP, destination = AP ; `10` : source = AP, destination = MP), les bits 1-0 `a a` la condition d'arrêt (`01` : arrêt en fin de tampon ; `10` : pas d'arrêt, la commande tourne jusqu'à `NOP`) **[A]**. La ROM emploie les constantes : `MVT + MP→AP + arrêt fin de tampon = $F5`, `MVT + AP→MP + pas d'arrêt = $FA`, et `MVT + AP→MP + arrêt fin de tampon` pour le défilement **[B]**.

**Effacer la page (CLF)** : R1, R2, R3 = valeurs C, B, A ; R6 = R7 = 0 ; lancer `$05` avec exécution (écriture à `$BF28`) ; **l'opération ne s'arrête pas seule** : attendre environ 5 ms (la note d'application attend 15 ms) puis envoyer `NOP` pour l'arrêter **[A, S18]**. Pour effacer en blanc sur noir : C = `$20` (espace), B = `$00`, A = `$70`.

## 4. Registres indirects (écrits par IND via R1)

| r | Nom | Rôle |
|---|---|---|
| 0 | ROM | lecture d'une tranche de la ROM de caractères (adresse dans R6, R7) |
| 1 | **TGS** | génération de synchro et format |
| 2 | **MAT** | marge, curseur, zoom |
| 3 | **PAT** | rangée de service, zones, incrustation, clignotement |
| 4 | **DOR** | emplacement des jeux de caractères utilisateur |
| 7 | **ROR** | adresse de la page affichée, origine verticale |

### TGS (`IND+1` = `$81`) [A, B]

| Bit | Sens |
|---|---|
| 0 | 0 : 625 lignes (50 Hz) ; 1 : 525 lignes (60 Hz) |
| 1 | 1 : entrelacé |
| 2 | 1 : resynchro horizontale externe |
| 3 | 1 : resynchro verticale externe |
| 4 | 1 : sortie synchro **composite** (broche HVS/HS) ; 0 : H et V séparées |
| 5 | rangée de service lue en Y = 1 (1) ou Y = 0 (0) |
| 7-6 | format (avec PAT7) : `00` + PAT7 = 0 → 40 col. **long** (24 bits) ; `01` → 40 col. variable ; `00` + PAT7 = 1 → 40 col. court (16 bits) ; `11` → 80 col. long ; `10` → 80 col. court (constantes `cVDP_TGS_MODE_*` de la ROM) |

### MAT (`$82`) [A]

| Bit | Sens |
|---|---|
| 2-0 | **couleur de la marge** (B V R : 0 noir … 7 blanc) |
| 3 | marge « insérée » (signal I haut pendant la marge) |
| 5-4 | mode du curseur : `00` complément fixe, `10` complément clignotant, `01` souligné fixe, `11` souligné clignotant |
| 6 | affichage du curseur (sur la position du pointeur principal) |
| 7 | **zoom** : double hauteur de toutes les rangées du corps de l'écran |

### PAT (`$83`) [A]

| Bit | Sens |
|---|---|
| 0 | rangée de service affichée |
| 1 | partie haute du corps affichée (120 premières lignes) |
| 2 | partie basse du corps affichée |
| 3 | « conceal » actif (40 col. : un caractère masqué s'affiche comme la marge) |
| 5-4 | mode d'insertion : `00` incrustation, `01` boîte, `10` marque par caractère, `11` marque de zone active |
| 6 | clignotement actif (0,5 Hz pour les caractères, 1 Hz pour le curseur) |
| 7 | 40 col. : `1` avec TGS7-6 = `00` → format court ; 0 pour les autres formats |

### DOR (`$84`) [A, relu sur la figure 22 de la fiche]

Indique **dans quel bloc de 1 Ko** de la mémoire privée se trouvent les jeux utilisateur :

| Jeu | Valeur de Z (bloc de 1 Ko : Z3 Z2 Z1 Z0) |
|---|---|
| G'0 (alphanumérique, octet B = `$80`) | DOR3 DOR2 DOR1 DOR0 |
| G'10 / G'11 (semi-graphiques, octets B = `$A0` / `$B0`) | DOR6 DOR5 DOR4 et **bit 4 de B** (0 : G'10, 1 : G'11) |
| Q0 à Q7 (quadrichromes, B = `$C0` + …) | DOR7, bit 5 de B, bit 3 de B, bit 4 de B |

Valeurs rencontrées en 40 colonnes : **`$13`** (ROM Alice : G'0 dans le bloc 3), **`$23`** (*Tuiles curieuses* : G'0 bloc 3, G'10 bloc 4, G'11 bloc 5, pages en blocs 0-2) **[A, B]**.
**Attention** : avec la page de caractères dans les blocs 0 (C), 1 (B), 2 (A), la valeur `$13` place G'10 dans le bloc 2, qui contient déjà les octets A de la page : ne pas utiliser G'10 avec ce réglage **[C]** ; préférer `$23` (testé en vrai par *Tuiles curieuses*).

### ROR (`$87`) [A]

| Bits | Sens |
|---|---|
| 4-0 | **YOR** : numéro (8 à 31) de la première rangée affichée sous la rangée de service |
| 7-5 | bloc d'origine de la page (**pair** : Z0 = 0 implicite). Ordre **Z3, Z1, Z2** : la note précise que Z1 et Z2 sont inversés. Exemple de la note : page à partir du bloc 4 (Z3 Z2 Z1 Z0 = 0100) → ROR7-6-5 = `001` |

La rangée affichée en haut est suivie des suivantes par incrémentation de Y **modulo 24** sans quitter le bloc d'origine : **changer YOR de 1 fait défiler l'écran d'une rangée sans rien copier** (voir `13-programmation-jeux.md`).

### Valeurs d'initialisation de la ROM Alice 32 [B, S19]

| Mode | TGS | MAT | PAT | DOR | ROR |
|---|---|---|---|---|---|
| 40 colonnes (long) | `$10` | `$28` | `$67` | `$13` | `$08` |
| 80 colonnes / HIRES (long) | `$D0` | `$28` | `$67` | `$FA` | `$08` |
| 80 col., assembleur | `$D0` | `$2C` (marge bleue) | `$67` | `$AF` | `$08` |

Le BASIC emploie les types d'écran **TECRAN** : 0 = 80 × 25, 1 = 40 × 25, 2 = 32 × 16 (`CLS` 80/81, 40, 32).
La séquence est : `NOP`, chargement de R1 puis `IND+r` pour TGS, MAT, PAT, DOR, ROR (attendre BUSY entre chaque), puis `VRM`, puis effacement de la mémoire par `MVT`/`CLF`.

## 5. Organisation de la mémoire privée [A]

La mémoire est vue comme des **tampons de 40 octets** adressés par un triplet logique **(Z, Y, X)** :

- **X** = 0 à 39 : octet dans un tampon ;
- **Y** = 0, 1 ou **8 à 31** : tampon dans un bloc (les rangées 2 à 7 n'existent pas ; **la rangée de service est Y = 0**, les 24 rangées de texte sont Y = 8 à 31) ;
- **Z** = 0 à 15 : bloc de 1 Ko.

Un bloc contient donc 25 tampons complets (Y = 0 ; 8 à 31) plus un tampon Y = 1 complet **dans les blocs pairs** ou partiel (X = 32 à 39) dans les blocs impairs : les restes sont appariés.
Chaque rangée de l'écran en format long occupe **trois tampons de même Y** dans **trois blocs consécutifs** (C, B, A). Une page se compose de trois blocs, le premier étant pair.

### Pointeurs R4/R5 (auxiliaire) et R6/R7 (principal)

- **R7** et **R5** : bits 5-0 = X (0 à 39), bit 7 = **Z0**, bit 6 = **Z1** (la note signale que l'ordre Z0-Z1 est inversé) ;
- **R6** et **R4** : bits 4-0 = Y (0, 1 ou 8-31), bit 5 = **Z2** ; **le bit 6 de R6 = Z3** (c'est la routine `AXPNT` de la note qui le range ainsi, pour le pointeur auxiliaire aussi).

Exemple (routine `AXPNT` de la note d'application, qui construit AP à partir de Z, du code C et du numéro de tranche) :

```
R5 = Z0 Z1 0 0 0 0 C1 C0   (+ 4 × numéro de tranche)
R4 = 0 0 Z2 C6 C5 C4 C3 C2
R6 bit 6 = Z3
```

L'auto-incrémentation (bit I des commandes) n'incrémente que **X** (modulo 40) pour KRF ; elle ne passe **pas** à la rangée suivante : après X = 39 le pointeur revient à X = 0, LXm et l'alarme sont mis à 1 ; utiliser `INY` pour la rangée suivante **[A]**.

## 6. Caractères en 40 colonnes

### 6.1 Format long 24 bits (celui de l'Alice 32)

Chaque cellule 8 × 10 points est décrite par trois octets C, B, A (R1, R2, R3 pour KRF).

**Octet C** : code du caractère (0-127 ; le bit 7 est ignoré en format long ; pour les jeux utilisateur les codes valides vont de 0 à 3 et de 32 à 127, soit **100 caractères par jeu**).

**Caractère bichrome** (octet B : bits 7-6 ≠ `11`) :

| Octet A (R3) | | Octet B (R2) | |
|---|---|---|---|
| bits 6-4 | couleur de **premier plan** (B V R) | bit 0 | **insertion** (couleur de l'« incrustation » : orange avec DOR par défaut) |
| bit 3 | clignotement | bit 1 | **double hauteur** (répéter le caractère sur la rangée Y + 1) |
| bits 2-0 | couleur de **fond** (B V R) | bit 2 | **conceal** |
| bit 7 | **vidéo inverse** | bit 3 | **double largeur** (répéter sur X + 1) |
| | | bits 7-4 | **jeu** (voir ci-dessous) |

Couleurs (3 bits B V R) : 0 noir, 1 rouge, 2 vert, 3 jaune, 4 bleu, 5 magenta, 6 cyan, 7 blanc **[A]**. (Tetrice les nomme autrement : 3 « orange », 7 « rose » : ce sont des noms de programme, pas de la fiche.)
Les codes couleur 8-15 de Tetrice sont obtenus en mettant le **bit 0 de B (insertion)** à 1 : la sortie I du composant s'ajoute alors à la couleur (variantes plus claires ou orangées). Le détail du rendu (broche I câblée sur la carte) n'est pas établi **[C]**.

**Jeux de caractères (bits 7-4 de B)** :

| B (bits 7-4) | Jeu | Contenu |
|---|---|---|
| `0000` | **G0** | 128 caractères alphanumériques (matrice 7 × 5 dans 8 × 10 ; tableau page 25 de la fiche) |
| `0010` | **G10** | 128 **mosaïques** semi-graphiques standard (blocs 2 × 3, vidéotex) |
| `0011` | **G11** | 32 traits (« strokes ») |
| `0100` / `0101` | G20 / G21 | alphanumériques **accentués** (minuscule + accent) |
| `1000` | G'0 | **jeu utilisateur alphanumérique** (100 caractères, DOR3-0) |
| `1010` / `1011` | G'10 / G'11 | **jeux utilisateur semi-graphiques** (100 caractères chacun) |
| `11xx` | Q0 à Q7 | **jeux utilisateur quadrichromes** |

*Remarques de la fiche :* les caractères semi-graphiques (G10, G11, G'1x) ne peuvent pas être soulignés ; une double hauteur / largeur se règle en **répétant** le code sur deux positions ; un caractère de G20/G21 doit être en format long.

**Caractère quadrichrome** (octet B bits 7-6 = `11`) : jusqu'à **4 couleurs** par cellule au prix de la **moitié de la résolution horizontale**. L'octet A donne alors une **palette ordonnée** de 4 couleurs sur 8 : chaque bit à 1 de A (B V R = bits 0-7) sélectionne une couleur, rangées dans l'ordre des bits ; si plus de 4 bits sont à 1 les plus forts sont ignorés ; si moins de 4, la palette est complétée par du blanc.
Exemple de la note : A = `$54` → rouge, jaune, bleu, cyan. B bits 5-3 = numéro du jeu Q0-Q7 ; bit 2 (R) : 0 = **haute résolution** (10 tranches par caractère) ; 1 = **basse résolution** (5 tranches répétées deux fois ; le bit k = bit 2 de B… choisit le demi-jeu).

### 6.2 Formats court et variable

- **Court (KRG)** : 16 bits, A et B partiellement mémorisés : économise 1/3 de mémoire mais pas d'accents ni de jeux G'1x/Q.
- **Variable (KRV)** : 8 ou 24 bits (C7 = 1 : code long ; sinon le caractère hérite des attributs précédents) ; commandes **EXP/CMP** pour décompresser/compresser une rangée.
L'Alice 32 utilise le **format long** : c'est le seul étudié ici.

## 7. Caractères redéfinis (UDS) et sprites

### 7.1 Principe [A]

Une cellule 8 × 10 = **10 octets**, un par ligne (« tranche »). Les points sont codés **bit 0 = point de gauche** (bit de poids faible d'abord, valeur « ordre inversé » dans la fiche : une tranche `$3F` allume les 6 premiers points à partir de la gauche).
Exemple de la note (logo) : tranches `$20,$38,$3C,$3E,$3F,$3F,$1F,$1F,$0F,$0F`.
Un jeu occupe **un bloc de 1 Ko** : 4 cellules par tampon de 40 octets (adresse de la 1ʳᵉ tranche d'un caractère C : tampon `C >> 2`, octets `(C & 3) × 10`… voir 7.2).

### 7.2 Écrire une tranche (méthode de la note d'application, vérifiée par *Tuiles curieuses*) [A]

On utilise **OCT avec le pointeur auxiliaire** (`$34` = OCT + AP) pour ne pas déranger le pointeur principal (qui sert au curseur et aux caractères).

Adresse d'une tranche NT (0-9) du caractère C (0-127, jeu dans le bloc Z) :

```
R4 = 0 0 Z2 C6 C5 C4 C3 C2         (bits 4-0 de R4 = Y' = C >> 2)
R5 = Z0 Z1 0 0 0 0 C1 C0  + 4·NT   (le numéro de tranche est dans les bits 5-2 de R5)
R6 bit 6 = Z3
```

D'où la formule vue dans *Tuiles curieuses* (`udc.c`) : adresse = base + ((C >> 2) << 8) + (C & 3) + 4 × NT, avec base = `$2000` pour G'10 et `$2080` pour G'11 (bloc 4 et 5 de DOR = `$23`) **[A, B]**.
**Piège** : l'auto-incrémentation avec OCT ne fait pas passer à la tranche suivante (NT est dans les bits 5-2 de R5, pas dans le poids faible) ; il faut ajouter `$04` à R5 à la main :

```asm
; écrire 10 tranches de (X) dans le caractère dont R4/R5 sont déjà initialisés
        ldaa #$34        ; OCT + pointeur auxiliaire (écriture)
        staa $BF20       ; commande chargée, pas encore exécutée
        ldab #10
boucle: ldaa 0,x
        inx
        staa $BF29       ; R1 avec exécution : écrit la tranche
attend: tst  $BF20
        bmi  attend
        ldaa #$04
        adda $BF25       ; R5 += 4 : tranche suivante
        staa $BF25
        decb
        bne  boucle
```

(Adapté de l'exemple de la note, qui est en 6809 : la structure `WRSLA1` fait exactement cela.)

### 7.3 Afficher un caractère redéfini

Écrire par KRF : C = numéro du caractère (0-3, 32-127), B = `$80` (G'0), `$A0` (G'10) ou `$B0` (G'11), A = couleurs (fond/premier plan, bit 7 inverse, bit 3 clignotement). Les caractères G'10 / G'11 peuvent être mélangés librement avec tout le reste de l'écran.

### 7.4 Performances à connaître

Avec les jeux G'10, G'11 et G'0 on dispose de **300 caractères bichromes** redéfinissables, soit un écran **pseudo-graphique de 320 × 250** pixels avec deux couleurs indépendantes par cellule 8 × 10 ; avec les quadrichromes : jusqu'à 800 caractères en haute résolution (160 × 250 pixels, 4 couleurs par cellule) ou 1 600 en basse résolution **[A, S18]**. L'écran 40 × 25 = 1 000 cellules est donc **entièrement « bitmappable » à condition d'y affecter jusqu'à 1 000 cellules distinctes** : impossible avec seulement 300 caractères bichromes, d'où l'usage typique en **tuiles** et en **sprites** de quelques cellules.

## 8. Caractères en 80 colonnes (mode « HIRES » de l'Alice 32)

- Cellule 6 × 10 points ; deux formats : **long 12 bits** (octet C + quartet A de 4 attributs) et court 8 bits (C seul, aucun attribut) ; les deux utilisent G0 (128 caractères 6 × 10).
- **Attributs du quartet A** (format long) : bit 0 **D** (sélection de couleur : choisit entre C0 et C1 de DOR), bit 1 **U** souligné, bit 2 **F** clignotant, bit 3 **N** négatif. Court : tous à 0.
- **Mosaïque** (C7 = 1) : 10 bits (A3-A1 et C6-C0) commandent chacun un sous-bloc de **3 points × 2 lignes** de la cellule : 2 colonnes × 5 rangées = **160 × 125 points** en 80 × 25 (la ROM adresse les points par `(X div 2, Y div 5)`) **[A + B]**. C'est le mode HIRES du BASIC (`CLS 80`/`81`, `SET`/`RESET`/`POINT` à l'échelle 160 × 125) ; couleur : 2 couleurs seulement pour tout l'écran (C0, C1 de DOR).
- **DOR en 80 colonnes** : bits 7-4 = couleur C1 (bit 7 = insertion), bits 3-0 = couleur C0 (bit 3 = insertion) ; l'attribut D choisit la paire (fond / premier plan), N les échange ; la ROM utilise `$FA` (C0 = vert, C1 = blanc) et `$AF` (l'inverse). Détail de la combinaison D/N : figure 33 de la fiche **[B, à relire sur l'image]**.
- Codage mémoire : deux caractères consécutifs sont regroupés en **3 octets** (C pair, C impair, et deux quartets A) ; X sur 80 positions se transforme en pointeur R7 par une rotation à droite de la position (voir figure 32 de la fiche) ; accès par **KRL** (`$50`/`$58`) : **le quartet A doit être répété dans R3 (haut et bas)** pour que l'écriture « lecture-modification-écriture » de A soit correcte ; la ROM le fait (« l'attribut doit être répété 2 fois dans l'octet »).
- Pas de jeux utilisateur (UDS) en 80 colonnes.

## 9. Le timing

- Horloge 12 MHz ; les points sortent à 8 MHz (40 col.) ou 12 MHz (80 col.) ; la mémoire est accédée en **cycles de 500 ns**.
- Une ligne TV dure **64 µs** ; une rangée de caractères = 10 lignes = **640 µs**. Le micro peut accéder à la mémoire environ **une fois par µs**, sauf pendant la première et la dernière ligne d'une rangée (104 µs sur 640 µs : environ 16 % du temps) où le tampon de rangée est rechargé.
- La trame dure 20 ms (50 Hz) ; **25 rangées × 640 µs = 16 ms** d'écran actif, le reste est le retour de trame. C'est pendant le retour de trame (bit 2 de R0 bas) que les commandes ne sont **pas** suspendues : c'est le moment idéal pour réécrire beaucoup de cellules.

## 10. Écrans-types

### Initialisation 40 colonnes long (équivalent de la ROM)

```asm
        ldaa #$91
        staa $BF28           ; NOP sans test de BUSY
        ; pour chaque couple (valeur, commande) du tableau :
        ;   attendre BUSY=0 ; écrire la valeur dans R1 ($BF21) ; écrire la commande dans $BF28
tab     fcb  $10,$81         ; TGS
        fcb  $28,$82         ; MAT
        fcb  $67,$83         ; PAT
        fcb  $23,$84         ; DOR (valeur de Tuiles curieuses)
        fcb  $08,$87         ; ROR : page en bloc 0, YOR = 8
        ; puis : commande VRM ($95) vers $BF28
```

### Écrire un caractère en (X, Y)

R6 = Y (ligne 8-31 ; la ligne d'état est 0), R7 = X ; R1 = C ; R2 = B ; R3 = A ; commande `$01` (KRF + incrémentation) avec exécution (écriture de la dernière donnée dans `$BF2B`, soit R3 + 8, ou de la commande dans `$BF28`).

## 11. Questions ouvertes

- Utilisabilité des 8 blocs comme pages et jeux de caractères (la taille de 8 Ko est établie, voir § 1).
- Rôle exact du bit 3 de l'état (reflet du bit 7 de R1) : notation de la fiche, non exploitée par les programmes lus.
- Validation sur machine réelle ou sous MAME des durées d'exécution (DCAlice émule un temps fixe de 30 cycles).
