# Études : image, échantillons, son à plusieurs voix, overscan, multi-résolution

Cinq questions posées pour pousser la machine. Pour chacune : la réponse, les raisons, et un programme d'essai dans `exemples/demo/`.
Légende : **[A]** documenté, **[B]** déduit ou **mesuré dans le simulateur du dépôt** (6803 exact au cycle près, EF9345 simplifié), **[C]** hypothèse à vérifier sur machine.
**Essais sur Alice 32 réelle (S26, novembre 2026)** :
- `demo4-bitmap` et `demo5-image` : **parfaits** ;
- `demo6-sample` : notes et batterie reconnaissables, voyelle synthétique non ;
- `demo7-trois-voix` : correct, mais les trois voix se distinguent mal ;
- `demo8-effets-son` : effets audibles, la PWM « fait SID », l'arpège convainc moins, barres fluides ;
- `demo9-marge-raster` : une bande par rangée stable, réglages plus fins instables ;
- `demo11-raster-ecran` : les bandes défilent, et passent derrière l'image HIRES (80 colonnes) ;
- `demo12-ym` et cinq musiques YM converties : jouées correctement, boucle intro + motif comprise ;
- `demo10-multimode` : 40 et 80 colonnes dans la même image, avec une rangée perturbée à la jonction.

Les autres résultats ci-dessous sont mesurés dans le simulateur.

## 1. Afficher une image convertie (HIRES 160 × 125, deux couleurs)

**Oui.** Chaîne complète : `outils/img2hires.py` (PNG, JPEG… → données) puis `inc/image.inc` (routine assembleur), démonstration `demo5-image`.

- **Le format produit est le rangement même de la mémoire de l'EF9345** en 80 colonnes (`04` §8.1, d'après MAME) : pour chaque paire de colonnes, code pair, code impair, octet d'attributs (quartet haut = colonne paire). Avec KRL en incrémentation (`$51`), on met l'octet d'attributs dans R3 une fois par paire : le composant prend lui-même le bon quartet et passe à la colonne suivante. **3 000 octets** par image (+ DOR et MAT), environ 2 000 KRL pour l'afficher (≈ 60 ms) **[B]**.
- Le script redimensionne l'image en gardant ses proportions (un point fait 3 × 2 pixels, presque carré sur un écran 4:3), la convertit en niveaux de gris, puis la réduit à deux couleurs par tramage :
  - méthodes : Floyd-Steinberg, matrice ordonnée 4 × 4 ou simple seuil ;
  - réglages : couleur d'encre et de fond parmi les 8, contraste, inversion ;
  - un aperçu PNG montre le résultat attendu.
- **Vérification [B]** : l'écran simulé de `demo5-image` est identique, pixel pour pixel, à l'aperçu du script.
- **Limites** :
  - 2 couleurs pour tout l'écran : l'encre vient de DOR, le fond est la couleur de la marge ;
  - 160 × 125 points, l'image occupe toute la RAM vidéo de la page.
  - Une 3ᵉ couleur est possible en théorie : le bit D de chaque cellule de 6 × 10 pixels choisit entre les deux couleurs de DOR. Non réalisé.
- Avec 300 caractères redéfinis en 40 colonnes, on peut aussi afficher une **fenêtre de 160 × 150 points fins** à deux couleurs par cellule (`demo4-bitmap`) ; le même script pourrait la remplir.

## 2. Overscan « comme le shifter de l'Atari ST » ?

**Non pour de vrais pixels dans la bordure ; oui pour des bandes de couleur dans la marge, avec une précision à étudier.**

- Sur le ST, l'overscan consiste à tromper le shifter, qui lit la RAM en continu, par des changements de fréquence aux bons instants. Il affiche alors des données hors de la zone normale.
- L'EF9345 fonctionne autrement **[A, S17]** :
  - il produit lui-même toute la synchronisation (registre TGS) ;
  - il n'affiche que **25 rangées de 10 lignes**, chacune chargée dans un tampon pendant la première et la dernière ligne de la rangée ;
  - le reste de l'image est la **marge**, d'une seule couleur (MAT bits 2-0) ;
  - aucun registre ne fixe la taille ou la position de la zone affichée, et il n'y a pas de 26ᵉ rangée à lire.
- Ce qui reste possible : **changer la couleur de la marge pendant la trame**, ce qui donne des bandes horizontales dans la bordure. Mesures dans le simulateur **[B]** :
  - une boucle qui attend le compteur du timer puis écrit MAT (IND, avec test de BUSY) coûte **≈ 125 cycles** : on peut faire un changement toutes les 2 lignes TV au mieux, **pas à chaque ligne** ;
  - une **rafale déroulée** sans test de BUSY descend à **10 µs** par changement, soit 6 par ligne TV : des segments de couleur au milieu d'une ligne de bordure **si** l'EF9345 prend les écritures en compte immédiatement **[C]** ;
  - les commandes, IND compris, sont suspendues ≈ 104 µs par rangée **[A]** : il faut s'attendre à des pertes ou à des décalages.
- Pistes non essayées **[C]** : passer de 50 à 60 Hz (TGS bit 0) au milieu de la trame pour décaler l'affichage, le « mode entrelacé » (TGS bit 1), la marge « insérée » (MAT bit 3). Sans documentation, ces essais peuvent faire « rouler » l'image ; ils ne mettraient de toute façon aucune donnée dans la bordure.
- **Essai** : `demo9-marge-raster`, avec 4 réglages : une bande par rangée, toutes les 2 lignes, aussi vite que possible, rafale de 10 µs.
- **Résultat sur machine réelle [A, S26]** : une bande par rangée est **stable** ; les réglages plus fins montrent des instabilités (photos à venir).
- **Des bandes sur toute la largeur ?** Deux moyens, à essayer avec `demo11-raster-ecran` :
  - en 80 colonnes, le fond de chaque cellule est la couleur de la marge : les bandes de MAT passent alors derrière l'image ou le texte. **Confirmé sur machine réelle [A, S26]** : les bandes défilent derrière l'image HIRES ;
  - en 40 colonnes, une cellule **masquée** (octet B bit 2, avec PAT bit 3 = 1) devait, d'après la fiche (S17), s'afficher dans la couleur de la marge. **Infirmé sur machine réelle [A, S26]** : le fond masqué reste noir, et les bandes ne se voient que dans la bordure. Le fond de la cellule était noir ; `demo11-raster-ecran` le met maintenant en bleu, pour savoir si une cellule masquée montre son propre fond.
  - **En pratique**, pour des bandes derrière du texte, utiliser les 80 colonnes, dont le fond est la marge. On peut aussi combiner un haut en 40 colonnes et un bas en 80 colonnes avec rasters (`demo10-multimode`).

## 3. Jouer un échantillon sur le haut-parleur 1 bit

**Oui, en prenant tout le processeur.** Chaîne : `outils/wav2sample.py` (WAV → échantillons 4 bits) puis `inc/sample.inc`, démonstration `demo6-sample`.

- Le haut-parleur n'a qu'un bit (bit 7 de `$BFFF`, `05` §2) : il faut **moduler la densité des impulsions**. Le lecteur utilise une **modulation sigma-delta du premier ordre** :
  - à chaque tic de 12 cycles, `A += échantillon × 16`, et la **retenue** de l'addition est envoyée sur le haut-parleur ;
  - la proportion de 1 vaut échantillon / 16, soit 16 niveaux sur un bit, à **≈ 83 kHz** (inaudible).
  - Le haut-parleur et l'oreille font la moyenne. C'est la même idée que les voix numérisées des PC à buzzer, plus fine que la largeur d'impulsion (PWM) simple.
- **Débit** : 16 tics par échantillon donnent **4 717 Hz**, ce qui suffit pour une voix « téléphone ». En 4 bits, cela fait 2,4 Ko/s : **≈ 2 s de son** dans la RAM libre de la machine de base. Avec l'extension de 16 Ko, environ 7 s de plus, à condition de charger les données à partir de `$5000`.
- **Mesures [B]** : fréquence mesurée de 4 728 Hz, et corrélation de **0,9999** entre la densité de sortie et les échantillons.
- **Contraintes** :
  - interruptions coupées et écran figé pendant la lecture ;
  - clavier inutilisable, parce qu'il partage `$BFFF`.
  - La réponse réelle du haut-parleur et de son transistor n'est pas connue **[C]** : un filtrage plus sévère que prévu atténuerait le son ; une sortie trop lente lisserait au contraire le bruit de quantification, ce qui irait dans le bon sens.
- Le son de test de `demo6-sample` est une synthèse originale : notes pincées, batterie, voyelle « a » → « i ». Pour un vrai enregistrement : `python3 outils/wav2sample.py mon_son.wav -o inc/donnees-sample.inc`.

## 4. Musique à 2 voix ou plus, et son enrichi par le matériel

**Oui, de deux façons.**

### 4.1 Mélange logiciel : 3 voix, processeur à 100 % (`demo7-trois-voix`, `inc/beeper3.inc`)

- Chaque voix est un accumulateur de phase sur 16 bits. Elle produit une **impulsion étroite** tant que l'octet haut de la phase est inférieur à son **rapport cyclique** (25 %, 25 %, 12,5 %).
- Les trois voix sont mélangées par un **OU** sur le bit 7 de `$BFFF`. Avec des impulsions étroites, les notes restent distinctes : c'est la technique des moteurs « beeper » du ZX Spectrum.
- Fréquences et rapports cycliques sont **écrits dans les instructions** (`ADDD #`, `CMPA #`, code auto-modifié). Un tic coûte **89 cycles**, soit 11 236 tics/s ; la justesse est de 0,4 %.
- **Mesures [B]** : le spectre de la sortie simulée contient bien les notes de l'accord en cours (fa 87 Hz, 175 Hz, 349 Hz, la 440 Hz, do 523 Hz).
- Un morceau original de 16 mesures (mélodie, basse en octaves, arpège) est généré par `gen_donnees.py`. 4 voix sont possibles à environ 8 500 tics/s (117 cycles par tic), mais le son devient plus « granuleux ».
- **Limite** : rien d'autre ne tourne pendant la musique. L'écran reste figé ; le clavier est lu entre deux notes.

### 4.2 Son enrichi par les interruptions du timer (`demo8-effets-son`, `inc/musique-plus.inc`)

C'est l'équivalent des « effets timer » du ST sur le YM2149, avec **le processeur presque libre**.

- L'interruption **OCF** (`$3206`) alterne **deux durées**, pour l'alternance haute et l'alternance basse : le **rapport cyclique** devient réglable, donc le timbre aussi.
- Une routine appelée à chaque image (50 Hz) fait avancer la mélodie et applique trois effets :
  - **PWM** : balayage du rapport cyclique de 50 % à 12 %, un timbre qui « respire », à la manière du SID ;
  - **vibrato** : ± 1,6 % ;
  - **arpège** : note, quinte, octave à 16,7 Hz, ce qui donne l'illusion d'un accord.
- **Mesures [B]** : la boucle principale garde **49,8 images/s** (deux barres de dégradé animées) pendant la musique ; le rapport cyclique varie bien de 0,12 à 0,50 ; l'arpège monte jusqu'au do 7 (période 479 µs).
- **Ce que le 6803 n'offre pas** : un seul registre de comparaison (OCF), donc **une seule voix** sous interruptions. Deux voix demanderaient soit des interruptions très rapides (≈ 10 kHz, 60 % du processeur), soit l'arpège, qui alterne les notes d'un accord. Le débordement du compteur (TOF, 65,5 ms) est trop lent pour des effets ; la synchro de trame (50 Hz) convient.
- **Pistes [C]** : une « batterie numérique » (un court sample joué à la place de la note, comme les « digi-drums » du ST) ; des enveloppes de volume, impossibles sur un seul bit, sinon par le rapport cyclique.

### 4.3 Musiques YM de l'Atari ST (`demo12-ym`, `outils/ym2alice.py`, `inc/ymplay.inc`)

- **Source du format** : le lecteur AtariAudio d'Arnaud Carré (licence MIT). Les fichiers YM2/YM3 contiennent 14 registres par trame ; YM5/YM6 ont un en-tête « LeOnArD! » (horloge, cadence, boucle, digidrums, titre, auteur), 16 registres par trame, rangés registre par registre ou trame par trame. La plupart sont compressés en LHA `-lh5-`.
- **Conversion** : le YM2149 est émulé trame par trame.
  - Les périodes deviennent des incréments de phase.
  - Le volume, ou l'enveloppe **moyennée sur la trame**, devient la largeur des impulsions.
  - Le mixeur indique, pour chaque voie, le son, le bruit ou les deux. Une voie qui ne joue que du bruit est hachée à la fréquence du bruit du YM.
  - Le flux ne code que ce qui change, avec une table d'au plus 255 fréquences : ≈ 2 octets par trame, soit ≈ 40 s dans la RAM de base.
- **Lecteur** : 3 voix + bruit (LFSR 16 bits), 122 cycles par tic, processeur à 100 %. Par rapport à `demo7`, les impulsions sont plus étroites (au plus 16 %) et proportionnelles au volume, pour que les voix se masquent moins.
- **Vérifié dans le simulateur [B]** : sortie identique au modèle Python, tic pour tic. **Non reproduit** : voix SID, digidrums, sync-buzzer, enveloppes rapides servant de forme d'onde.
- **Essai sur de vrais fichiers** : les 11 fichiers de `YmSampleFiles` du dépôt StSound d'Arnaud Carré, tous compressés en `-lh5-`. La décompression intégrée réussit pour tous, CRC vérifié.
  - 9 sur 11 se convertissent. Ils prennent 2,7 à 4,6 octets par trame selon le morceau : dans la RAM de base, environ 5,4 Ko pour la table des fréquences et le flux, il tient **21 à 37 s** de chaque morceau.
  - 2 sont en MIX1 (échantillons numériques) et en YMT1 (format tracker), qui ne sont pas des suites de registres du YM2149 : ils ne sont pas gérés.
  - 5 morceaux sur les 9 utilisent les effets spéciaux du ST, qui ne sont pas reproduits.
  - Sur *Scout*, la sortie du lecteur est identique au modèle Python sur 24 012 tics.
  - Pour des morceaux plus longs, il faudrait placer les données dans l'extension mémoire, ou les lire depuis la cassette ou la disquette par morceaux.
- **Sur machine réelle [A, S26]** : `demo12-ym` et les cinq morceaux convertis (Scout, Enchanted Lands, Camerto, ANCOOL1, Virtual Escape 2) **se jouent correctement** ; ANCOOL1 boucle bien sur son motif après l'intro.
- **Choisir ce qui boucle** : `--cherche-boucle` repère les répétitions exactes des registres, et `--boucle B --fin F` joue les trames 0 à F−1 puis reprend en B. Pour ANCOOL1 : intro de 96 trames (batterie seule), puis motif de 384 trames répété. Dans le simulateur, l'intro n'est jouée qu'une fois, puis le motif est rejoué à l'identique (état du lecteur comparé trame par trame). Les fichiers d'exemple sont dans `exemples/demo/musiques/`.

## 5. Plusieurs résolutions dans la même image ?

**Dans une même rangée : oui, nativement, par cellule. Entre 40 et 80 colonnes : inconnu, une expérience est prête.**

- **Ce que l'EF9345 mélange déjà** : en 40 colonnes, **chaque cellule** choisit son jeu par l'octet B **[A, S17]**. On peut donc mêler dans une même image :
  - du texte (G0 et accents G20/G21) ;
  - des mosaïques 2 × 3 (G10) ;
  - des caractères redéfinis en 8 × 10 (G'0, G'10, G'11) ;
  - des **quadrichromes** (4 couleurs, demi-résolution horizontale) ;
  - de la **double hauteur et double largeur**.
- C'est une forme de multi-résolution plus souple que celle du CPC (changement de mode par ligne). La démo `demo` montre déjà côte à côte le logo, le texte de 40 colonnes et des caractères doublés.
- **Ce qui est global à l'image** : le format 40 ou 80 colonnes (TGS bits 7-6 et PAT bit 7), le zoom (MAT bit 7), la page et YOR (ROR), les jeux (DOR). Le « 32 × 16 » du BASIC est un choix de la ROM (`TECRAN` = 2), pas un mode de l'EF9345 **[B]**.
- **Changer TGS en cours de trame** pour avoir du 40 colonnes en haut et du 80 colonnes en bas : rien dans la fiche ne l'interdit. Une condition est remplie : les deux rangements en mémoire sont compatibles rangée par rangée (40 colonnes : blocs 0, 1, 2 ; 80 colonnes : blocs 0, 2, 4 ; `04` §8.1). DOR, en revanche, change de sens entre les deux modes (jeux de caractères en 40, couleurs en 80) : il faut une valeur valable pour les deux (`$72` dans l'essai). On ne sait pas si l'EF9345 relit le format à chaque rangée ou seulement en début de trame **[C]**.
- **Essai** : `demo10-multimode`. Le haut de la page est rangé en 40 colonnes, le bas en 80. À chaque trame, TGS passe à 40 colonnes juste après la synchro, puis à 80 colonnes à l'instant affiché ; ESPACE descend la coupure d'une rangée (640 µs).
  - Le simulateur, qui dessine toute l'image dans un seul mode, montre ce qui se passe si le format n'est lu qu'une fois : la partie rangée dans l'autre mode est illisible.
  - **Résultat sur machine réelle [A, S26]** : **ça marche**. Le haut est lisible en 40 colonnes et le bas en 80 colonnes : le format est donc relu en cours de trame. Une rangée est perturbée à la jonction (photos à venir) ; il faudra régler l'instant du changement.

## Programmes et ce qu'ils doivent montrer

| Programme | Ce qu'il faut regarder ou écouter |
|---|---|
| `demo5-image` | le paysage de test, net, en blanc sur noir |
| `demo6-sample` | trois notes, une batterie, une voyelle (≈ 2 s) ; ESPACE rejoue |
| `demo7-trois-voix` | mélodie + basse + arpège reconnaissables ensemble |
| `demo8-effets-son` | différence audible entre carré, PWM, vibrato, arpège ; barres fluides |
| `demo9-marge-raster` | bandes dans la marge : hauteur, stabilité, effet de la rafale |
| `demo10-multimode` | une coupure nette 40 / 80 colonnes, ou un seul mode pour tout l'écran |

Chaque résultat obtenu sur machine réelle peut passer la ligne correspondante de `12-questions-ouvertes.md` en **[A]**.
