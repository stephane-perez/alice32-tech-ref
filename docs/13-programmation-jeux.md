# Programmer des jeux rapides et des démos sur Alice 32

Ce document rassemble les **leviers de vitesse** de la machine et les techniques qui en découlent, pour des **jeux** comme pour des **démos** (demomaking : voir §10). Il s'appuie sur `04-ef9345-video.md` (le processeur vidéo), `05-clavier-son-joysticks.md` et `03-registres-et-ports.md`.
Légende : **[A]** documenté dans une source citée ; **[B]** déduit (calcul à partir d'une source) ; **[C]** idée **non testée** sur machine ou émulateur : à valider avant de s'y fier.
Un squelette de programme (assemblé avec DASM, non exécuté) est fourni dans `exemples/squelette-jeu.asm`.

## 1. Les budgets

| Ressource | Valeur | Origine |
|---|---|---|
| Horloge du processeur | 4 MHz / 4 = **1 MHz** (1 cycle = 1 µs) | [A] S20 |
| Trame vidéo | 50 Hz, **20 ms = environ 20 000 cycles** par image | [A] |
| Écran actif | 25 rangées × 640 µs = **16 ms** ; retour de trame ≈ 4 ms | [B] fiche EF9345 |
| Mémoire vidéo | 8 Ko = 8 blocs de 1 Ko, inaccessibles directement | [A] S20 |
| Mémoire accessible par le 6803 | RAM `$3000-$4FFF` (8 Ko) + extensions | voir `02-carte-memoire.md` |
| Instructions (cycles) | `LDAA` immédiat 2, direct 3, étendu/indexé 4 ; `STAA` direct 3, étendu/indexé 4 ; `LDD` 3/4/5 ; `STD` -/4/5 ; `INX`/`DEX` 3 ; `INC`/`DEC` étendu 6 ; `TST` étendu 6 ; branchement 3 ; `BSR` 6, `JSR` étendu 6, `RTS` 5 ; `MUL` **10** ; `PSHX` 4, `PULX` 5 | [A] datasheet MC6803 table 13 |
| RAM interne du 6803 | `$0080-$00FF` : accès « direct » plus rapide (3 cycles au lieu de 4) ; **utilisée par le BASIC et la ROM** | [A] S20, S19 |

Un jeu en langage machine dispose donc de quelques milliers d'instructions par image. Le goulot d'étranglement est presque toujours **l'écriture à l'écran**, pas le calcul.

## 2. Règles d'or de l'écran

1. **Tester BUSY (bit 7 de R0) avant tout accès à R1-R7** ; jamais d'écriture « à l'aveugle » : le composant suspend ses commandes pendant la première et la dernière ligne de chaque rangée (≈ 104 µs par rangée affichée) **[A]**.
2. **Charger la commande une seule fois** dans R0 (`$BF20`), puis lancer chaque exécution par une écriture dans R1, R2 ou R3 **+ 8** (`$BF29`, `$BF2A`, `$BF2B`) : un seul accès par caractère quand les attributs ne changent pas **[A]**.
3. **Garder une copie de l'écran en RAM** (1 000 octets pour les codes C) pour la logique de jeu et la détection des collisions. Lire l'écran par KRF lecture (`$08`) coûte 7,5 µs de commande plus des attentes **[B]** : à éviter.
4. **N'écrire que ce qui change** (cellules modifiées), à l'aide d'une liste de « cellules sales ».
5. **Utiliser les commandes matérielles** pour tout ce qui est en bloc (effacer, copier une rangée) plutôt que des boucles du 6803.
6. **Écrire pendant le retour de trame** quand l'image doit rester propre : attendre le bit 2 de R0 (après `VRM`) puis écrire ; pendant les ≈ 4 ms de retour de trame les commandes ne sont pas suspendues **[B]**.

## 3. Techniques

### 3.1 Initialisation en trois lignes avec la ROM [A, S20 ; B]

```asm
        ldaa #1            ; 0 = 80x25, 1 = 40x25, 2 = 32x16
        staa $301A         ; TECRAN
        jsr  $D42C         ; INASS : règle l'EF9345, efface, recharge le jeu de caractères
```

La routine `$D42C` recopie aussi le jeu de caractères d'Alice dans la mémoire vidéo : tout ce qu'on avait redéfini dans G'0 avant l'appel est écrasé ; **à appeler avant de définir ses propres tuiles** (le livre précise que le jeu est recopié à chaque RESET ou sortie de l'assembleur). *Remarque :* le livre cite l'adresse du type d'écran en `$3018` ; la ROM commentée (octet par octet identique à `alice32.rom`) et *Castle Attack* (`POKE 12314`) donnent **`$301A`**.

### 3.2 Attendre la trame [A + B]

```asm
        ldaa #$95
        staa $BF28         ; VRM, une fois à l'initialisation
...
vsync   ldaa $BF20
        anda #$04
        bne  vsync         ; le bit 2 est à 0 pendant 2 lignes (128 µs) par trame
```

La fenêtre de 128 µs est facile à attraper : une lecture + test + branchement = 11 cycles. Une boucle de jeu = **calcul, puis attente de trame, puis écriture des changements** : jeu verrouillé à 50 images/s **[B]**. Si la boucle prend plus de 20 ms on tombe à 25 images/s : mesurer avec le compteur du timer (`$09-$0A`, 1 tick = 1 µs) **[B]**.

### 3.3 Effacer l'écran très vite : CLF [A]

R1 = `$20` (espace), R2 = 0, R3 = `$70` (blanc sur noir), R6 = R7 = 0, lancer `$05`, attendre ≈ 5 ms (4,7 ms pour 1 000 caractères) puis envoyer `NOP` (`$91`) pour l'arrêter : la commande ne s'arrête pas seule. Environ 1/4 de trame au lieu de plusieurs dizaines de ms en boucle.

### 3.4 Défilement vertical gratuit : ROR/YOR [A, S18 ; B]

Le registre **ROR** (indirect 7) contient l'origine verticale **YOR** (bits 4-0, de 8 à 31) : la rangée affichée en haut de l'écran. Les rangées suivantes sont lues par incrémentation **modulo 24**. Donc :

- **défilement vers le haut d'une rangée** : écrire la nouvelle rangée du bas **dans la mémoire de l'ancienne rangée du haut**, puis faire YOR := YOR + 1 (modulo 24, en restant entre 8 et 31) ;
- coût : **une rangée de 40 caractères + une écriture IND**, quel que soit le défilement ; aucune copie.
- parfait pour : course de voitures, shoot'em up vertical, labyrinthe, titre qui défile. Le défilement horizontal n'a pas d'équivalent matériel (voir 3.7).

### 3.5 Copier des rangées : MVT [A]

`MVT` copie des **triplets** (un caractère long = 3 octets dans 3 blocs) d'un tampon à l'autre : 2 + 12 n µs pour n caractères (n ≤ 40), soit ≈ **480 µs par rangée complète**. La ROM s'en sert pour son défilement (`GR_SCROLLUP` en `$D5C5`).
Décaler une rangée d'un caractère vers la gauche : source = rangée, X = 1 ; destination = la même rangée, X = 0 ; arrêt en fin de tampon. 24 rangées ≈ 11,5 ms **[B]** : possible à 50 images/s, mais cela occupe presque toute l'image et se heurte aux suspensions de commande **[C]**. Un défilement horizontal fin se fait plutôt par des tuiles pré-décalées (3.7).

### 3.6 Double mémoire d'image (pages) [B + C]

Le registre ROR choisit la page affichée. Une page long occupe **3 blocs consécutifs, dont le premier est pair, dans un même « district »** (blocs 0-3 ou 4-7) : avec 8 blocs, **deux pages sont possibles : blocs 0-2 et blocs 4-6** ; restent les blocs 3 et 7 pour les caractères redéfinis. On dessine dans la page cachée pendant que l'autre est affichée, puis on bascule en écrivant ROR pendant le retour de trame. **[C : combinaison non testée]**. Contrepartie : plus de place pour les jeux G'1x ni pour les jeux quadrichromes (5 blocs libres au maximum dans la configuration à une page : « Q3 à Q7 » d'après S20).

### 3.7 Tuiles et sprites avec caractères redéfinis [A]

Chaque cellule de 8 × 10 points peut devenir un petit bitmap de **10 octets** : 100 caractères dans chacun des jeux G'0, G'10, G'11 (**300 en tout**, avec deux couleurs par cellule) ; voir `04-ef9345-video.md` §7 pour l'adressage.

- **Fond de jeu** : une carte de tuiles (labyrinthe, plateforme…) dont chaque élément est une cellule ; l'écran est 40 × 24 cellules. Les tuiles sont définies une fois, puis chaque case ne coûte qu'un KRF.
- **Sprite par redéfinition** : un sprite de 2 × 2 cellules est un groupe de 4 caractères redéfinis ; à chaque image, on **calcule en RAM** l'image décalée du sprite (décalage au pixel près : `ASRD`, `LSLD`, `LSRD` de 3 cycles manipulent 2 octets) puis on **réécrit ses 4 × 10 octets** avec `OCT` (≈ 4 µs par octet de commande, plus attentes) **[B]**. L'écran, lui, n'est pas touché : les 4 caractères restent à leur place. Mais le sprite est **verrouillé sur la grille** de cellules : pour déplacer au pixel, il faut le dessiner sur 2 × 2 cellules et le faire courir à travers les 4 cellules voisines (un sprite de 8 × 10 point de large couvre au plus 2 cellules en largeur et 2 en hauteur).
- **Sprites pré-décalés** : pour un petit nombre de sprites très fréquents (tir, balle), pré-calculer en RAM les 8 versions décalées et ne faire que des copies.
- **Piège du livre** : l'octet de commande `OCT` avec incrémentation n'avance pas le numéro de tranche ; il faut ajouter 4 à R5 à chaque tranche (voir le squelette).
- **Les touches du BASIC** : la ROM place ses caractères semi-graphiques « SHIFT+lettre » dans G'0 ; redéfinir G'0 modifie ce qu'on voit en tapant ces touches (jusqu'à `JSR $D42C` ou RESET) **[A, S20]**.

### 3.8 Quatre couleurs par cellule : quadrichrome [A]

Une cellule quadrichrome (B = `$C0` + …) affiche **4 couleurs choisies parmi 8** (A = palette ordonnée) avec **la moitié de la résolution horizontale** (160 × 250 points sur l'écran ; ou 160 × 125 en basse résolution, 5 tranches par caractère répétées). Intérêt : sprites multicolores, décors. Limites : au plus 5 jeux (Q3-Q7) quand on garde une page et un jeu G'0 ; une palette ne peut pas contenir n'importe quel ordre de couleurs (voir `04` §6.1). Vu l'espace limité de la mémoire vidéo (8 Ko), c'est un luxe.

### 3.9 Effets gratuits du composant [A]

- **Clignotement** (attribut de caractère, 0,5 Hz, A bit 3 en 40 col.) et **vidéo inverse** (A bit 7) : animation sans coût processeur (`PAT` bit 6 doit être à 1).
- **Double hauteur / double largeur** (B bits 1 et 3, en répétant le code sur la rangée / colonne suivante) : gros caractères, scores, titres ; **zoom d'écran** par MAT bit 7 (toutes les rangées doublées).
- **Couleur de marge** (MAT bits 2-0) : un seul `IND` (2 µs) change la couleur du cadre : flash de dégât, effet de transition.
- **Masquer des zones** : PAT bits 0-2 désactivent la rangée de service, la moitié haute ou la moitié basse du corps : **volets d'écran** instantanés.
- **Curseur matériel** : une cellule complémentée ou soulignée à la position du pointeur principal (clignotant 1 Hz) : sélecteur de menu sans écrire.
- **Rangée de service** (la ligne d'état Y = 0) : ligne de score fixe qui ne défile pas avec YOR.

### 3.10 Mode graphique 160 × 125 (HIRES) [A + B]

Le mode 80 colonnes « mosaïque » (`CLS 80`/`81`) donne des points de 3 × 2 pixels : **160 × 125 points, 2 couleurs pour tout l'écran** (C0 et C1 de DOR). Allumer un point demande de lire la cellule (KRL, 11,5 µs), modifier le bon bit et la réécrire (KRL, 12,5 µs) : environ **25-40 µs par point** avec les attentes **[B]**, soit 500-800 points par image. Bien adapté à des **tracés vectoriels simples** (quelques segments), pas à des fonds pleins. Pour du plein écran, préférer les tuiles.

## 4. Entrées

- **Clavier / manette en un appel** : `JSR $F883` (POLCA) donne un code ASCII, mais **une seule touche à la fois** et il balaie toute la matrice à chaque appel ; pour un jeu de quelques touches (direction + tir) lire directement les colonnes concernées (`STAA $02` puis `LDAA $BFFF` : une dizaine de cycles par colonne) **[A, B]**.
- **SHIFT et CONTROL** sont sur le port 2 (`$03`, bit 1) : utile comme touches de tir ; voir `05`.
- **Manettes** : `$BF30` (droite) et `$BF34` (gauche), actifs à 0 ; au repos `$3F` ; haut `$3E`, bas `$3D`, gauche `$3B`, droite `$37` **[A]**. Combiner clavier et manette comme le Sokoban de Dominique Constant : une valeur de manette qui change est transformée en code de flèche.
- **Anti-rebond** : relire après quelques ms avant de valider un appui (une boucle `DEX`/`BNE` de 10 000 pas ≈ 60 ms à 6 cycles par pas) ; attendre le relâchement d'ENTER au lancement.

## 5. Son sans bloquer le jeu

- La routine ROM `$FFAB` (SOUND) **bloque** tout le temps du son et bloque le clavier : à réserver aux jingles de début et de fin.
- Pour un son **pendant** le jeu, inverser le bit 7 de `$BFFF` à des instants choisis : par exemple **une inversion par image** (25 Hz de fondamentale) ou depuis une **interruption TOF** (toutes les 65,5 ms, trop lent) ou **OCF** (comparaison de sortie, période réglable à partir du compteur `$09-$0A`) pour obtenir des notes de 100 Hz à quelques kHz **[B + C]**.
- Un « bruit » (explosion) s'obtient en inversant `$BFFF` selon un registre à décalage (LFSR) ou le compteur libre `$0A` **[C]**.
- Rappel : le son et la lecture du clavier **partagent** `$BFFF` ; ne pas lire les touches pendant qu'une note joue au bit 7 **[B]**.

## 6. Interruptions et temps

- **TOF** (vecteur `$FFF2` → trampoline RAM `$3203`) : toutes les 65,536 ms ; **OCF** (`$FFF4` → `$3206`) : à un instant programmable par `$0B-$0C` ; **NMI** (`$FFFC` → `$3212`) disponible sur le connecteur d'extension. Dans les trampolines la ROM a placé des `RTI` espacés de 3 octets : remplacer par un `JMP` **[A, S20]**.
- Ne pas utiliser **SCI** (partagé entre l'imprimante et la cassette) ni la capture d'entrée (ports pris par le clavier).
- **Aléatoire** : `LDAA $0A` (poids faible du compteur libre) pris au moment d'un appui de touche ; ou la fonction `RND` du BASIC (routine `romRND`, `$F62A`, graine `RNDSEED`) **[B, S19]**. Un jeu qui tire un nombre à chaque image peut aussi se servir d'un générateur congruentiel en 16 bits (`MUL`, 10 cycles) **[C]**.

## 7. Où loger le programme

- **Depuis le BASIC** : `CLOADM` puis `EXEC adresse`, ou une ligne BASIC `EXEC`. Zone libre sans extension : `$3346` (début du programme BASIC) jusqu'à `$4F94` (pile système) : environ 7 Ko moins le programme BASIC et ses variables ; avec l'extension de 16 Ko on peut loger le code vers `$5000+` **[A, S19]**. *Tuiles curieuses* s'exécute avec `EXEC 17500`.
- **En cartouche** : `$1000-$2FFF` (jusqu'à 8 banques de 8 Ko avec Multiports), lancement par `EXEC 4096` **[A, S2, S14]** (voir `09`).
- **RAM interne `$80-$FF`** : plus rapide, mais le BASIC et la ROM y rangent leurs variables ; la réutiliser **sans retour au BASIC** (programme qui ne rend pas la main, RESET pour sortir) **[C]**.
- **Chaîne de compilation** : *Tuiles curieuses* est écrit en C (CC6303) avec des routines assembleur ; l'assembleur de la ROM (`EXEC 49152`) convient pour de petits programmes ; DASM sur PC pour le reste (voir `10-outils-de-developpement.md`).

## 8. Idées de jeux adaptées à la machine

| Genre | Technique clé |
|---|---|
| Course / shoot'em up vertical | défilement ROR/YOR (3.4), rangée de service pour le score |
| Labyrinthe, Pac-Man, Sokoban | carte de tuiles (3.7), copie RAM de l'écran, clavier/manette direct |
| Casse-briques, Pong | quelques sprites pré-décalés, marge qui clignote en cas de perte |
| Jeux de réflexion (Tetrice) | tuiles, OCT, blocs en G'10/G'11 ; peu de défilement |
| Aventure texte/graphique | 80 colonnes, accents G20/G21 (A), double hauteur pour les titres |
| Vectoriel simple | HIRES 160 × 125 (3.10) |

## 9. À mesurer sur émulateur ou machine réelle

Ces points sont **déduits de calculs** et devraient être vérifiés (voir `12-questions-ouvertes.md`) :

1. nombre réel de caractères KRF/s en boucle serrée, avec et sans attente BUSY ;
2. effet exact d'un changement de ROR en cours de trame (instant où la nouvelle page est prise en compte) ;
3. fenêtre réelle pour écrire dans le retour de trame ;
4. conflit éventuel entre DOR `$13` (valeur de la ROM) et une page de 3 blocs en 0-2 ;
5. émulation par DCAlice : elle simule un temps fixe de 30 cycles par commande, donc **ne reflète pas les durées réelles** (S2).

## 10. Pistes pour des démos (demomaking) [C, toutes à tester]

Les mêmes leviers servent aux démos ; ce qui suit découle des capacités du composant décrites dans `04` et **n'a pas été essayé**.

- **Barres de couleur dans la marge** : MAT (bits 2-0) change la couleur du cadre en 2 µs par `IND`. En l'écrivant plusieurs fois dans une même trame, à des instants synchronisés sur le bit 2 de R0 et le compteur `$09-$0A` (1 tick = 1 µs, ligne TV = 64 µs), on peut espérer des **bandes horizontales** dans la marge. Limites : les commandes sont suspendues autour des rangées (≈ 104 µs), donc la précision est de l'ordre de la rangée (640 µs) **[C]**.
- **Défilement vertical fluide** (YOR, §3.4) combiné à une carte de tuiles : paysages, tunnels, textes de fin.
- **Animation par redéfinition de caractères** (§3.7) : changer les 10 octets d'une tuile fait « bouger » toutes ses occurrences à l'écran **sans toucher la page** : eau, flammes, plasma à base de quelques tuiles réparties sur tout l'écran.
- **Plasma / dégradés** : attributs A (couleurs de fond et de premier plan) calculés par table de sinus et écrits en KRF ; 8 couleurs par composante, avec inverse et clignotement pour 3 ou 4 teintes supplémentaires.
- **Écran multicolore à 160 × 250** avec les caractères quadrichromes (§3.8), au prix de la mémoire vidéo.
- **Zoom et gros caractères** : MAT bit 7, double hauteur/largeur : textes géants, effet de zoom par bascule ; **volets** avec PAT bits 1-2.
- **Scrolltext horizontal** : décalage de tuiles pré-calculées dans G'0 + MVT d'une rangée (§3.5) ; le texte se déplace au pixel près si l'on redéfinit les caractères de la rangée.
- **Musique** : le son est 1 bit sur `$BFFF` ; pour jouer des notes pendant l'animation, faire alterner la fréquence à chaque passage de boucle ou depuis OCF (§5) ; deux voix demandent un mélange logiciel (`EORA` de deux signaux carrés) **[C]**.
- **Contraintes à garder en tête** : 1 MHz, 20 000 cycles par image, une seule voix 1 bit, pas de sprite matériel, 8 Ko de mémoire vidéo ; l'économie vient du **matériel** de l'EF9345 (CLF, MVT, YOR, marges, attributs) plus que du processeur.
- **Où trouver des exemples** : *Tuiles curieuses* (tuiles, S8), les programmes de démonstration du catalogue (`11-catalogue-logiciels.md`), et le désassemblage/commentaire de la ROM (`06`).
