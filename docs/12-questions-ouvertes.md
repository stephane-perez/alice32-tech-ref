# Questions ouvertes, incertitudes et erreurs connues

Ce qui n'est **pas** établi, avec la manière de le trancher. Priorité : ce qui conditionne les **jeux rapides et les démos** (§ 1). Sources citées dans `00-sources.md`.

## 1. Vidéo (EF9345) : à mesurer sur machine réelle ou sous MAME

| # | Question | Pourquoi c'est important | Comment trancher |
|---|---|---|---|
| V1 | **Débit réel** de `KRF` / `OCT` / `MVT` dans une boucle serrée (temps d'attente entre deux commandes, durée de BUSY, effet des suspensions de ≈ 104 µs en début/fin de rangée) | budget d'un jeu : combien de cases par image | boucle de test chronométrée par le timer `$09-$0A`, résultat en cycles |
| V2 | **Changer ROR (YOR) en cours de trame** : effet, délai, valeurs interdites | défilement fin, effets de type « raster » pour démos | écrire ROR à des moments variés (timer) et filmer/capturer |
| V3 | **Fenêtre utile de la suppression de trame** : durée disponible pour écrire sans scintillement (bit 2 de R0 = 0 pendant 2 lignes TV après `VRM`) | redessiner pendant la trame sans « neige » | tester l'écriture hors et pendant ces lignes |
| V4 | **Conflit éventuel DOR = `$13`** (valeur ROM) avec un double tampon sur 3 blocs | pagination (flipping) | lire le contenu des blocs 0-2 / 4-6 après changement de DOR/ROR |
| V5 | Signification du **bit 3 du registre d'état** (MSB de R1 ?) | diagnostic | écrire R1 et lire R0 |
| V6 | **Câblage de la sortie « I » (insert)** sur la carte : couleurs 8 à 15 | palette complète en 40 colonnes | schéma (S1) + essai |
| V7 | Capacité exacte de la mémoire vidéo : **8 Ko**, confirmée par S20 ; les 8 blocs de 1 Ko sont-ils tous utilisables comme pages/jeux de caractères ? | voir `04-ef9345-video.md` | essai |
| V8 | Émulation : DCAlice utilise 30 cycles fixes par commande (S2) ; l'écart de MAME avec le matériel est inconnu | on ne peut pas régler un effet sur émulateur | comparer avec une vraie Alice |

## 2. Entrées, son, interruptions

| # | Question | Piste |
|---|---|---|
| E1 | **Bit de tir** des manettes (probablement le bit 4, actif à 0) **[C]** | lire `$BF30` / `$BF34` tir enfoncé (S21 ne donne que les directions) |
| E2 | Bit 7 de `$BFFF` **en lecture** (partage clavier/son) | essai |
| E3 | Comportement de `POLCA` : durée d'un appel, anti-rebond, répétition | chronométrer |
| E4 | Son non bloquant : meilleure méthode (OCF avec `$0B-$0C` vs une inversion par image) | essai sur DCAlice puis sur machine |
| E5 | **Interruptions** : vecteurs RAM `$3200-$3212` (trampolines), latence réelle, compatibilité avec `SOUND` de la ROM | essai ; NMI sur la broche 31 de l'extension (S1) |

## 3. ROM, système, supports

| # | Question | Piste |
|---|---|---|
| R1 | Adresse du type d'écran : **`$301A`** (source ROM S19, Castle Attack S12) contre **`$3018`/`$3010`** (livre S20) | le source ROM prévaut ; confirmer par essai |
| R2 | Rôle exact de plusieurs variables système et hooks de `$3000-$3345` (doUSER, pEXEC, pCOLD, ROLTB…) signalés [C] dans `06-rom-et-points-d-entree.md` | lecture du source commenté S19 |
| R3 | **Format d'une cartouche** : en-tête éventuel, démarrage automatique, banques (S2 : 8 banques de 8 Ko) | analyser des `.rom` de l'archive (*In The Dark*, *Tuiles curieuses*) |
| R4 | Séquence de **démarrage sur disquette** (MCX32-FDJ, S6-S7) | S7 + désassemblage |
| R5 | **Lettres des commandes CTRL** de l'éditeur-assembleur (S22) : images perdues à l'OCR | relire le guide papier ou DCAlice |
| R6 | Borne haute de `CLEAR LN,AD` sans extension (S22 OCR abîmé) | essai |
| R7 | Les documents **MC-10 / Alice 4K / Alice 90** ne sont pas traités (hors périmètre) | si l'utilisateur veut étendre le dépôt |

## 4. Démomaking : questions propres

Hypothèses de `13-programmation-jeux.md` § 10, toutes [C] :

1. Effets « gratuits » par **modification de ROR/YOR** en cours de trame (barres, ondulations) : faisabilité et plage horizontale.
2. **Changement de DOR/ROR par rangée** pour afficher plus de deux jeux de caractères définis par l'utilisateur (« UDC ») à l'écran.
3. Utilisation de la **marge** (couleur MAT) comme bande raster.
4. **Mode 80 colonnes mosaïque (HIRES 160×125)** comme plan pour plasmas/feux ; coût de remplissage d'écran par `KRL`/`MVT`.
5. Sons de démo : deux voix par entrelacement 1 bit, **coût** en cycles et conflit avec les commandes EF9345.
6. Synchronisation sur le **timer** à 1 µs de résolution (65,536 ms par tour) au lieu de la trame.
7. Taille : limite de **RAM** (`$3000-$4FFF` sans extension) et fenêtre cartouche `$1000-$2FFF`.

## 5. Erreurs et divergences relevées dans les sources

- *Les Astuces d'Alice* (S20) : place le X du clavier en colonne 1 / ligne 6 ; il est en colonne 0 / ligne 3 (corrigé par l'auteur de Tetrice, S9).
- Adresse du type d'écran (R1 ci-dessus).
- Listing d'Alicetel (S10) : code de BREAK lu `$92` par l'OCR ; la ROM (S19) donne `$03`.
- Désassemblage heuristique (version 0.1 du dépôt) remplacé par le source commenté S19, **identique octet par octet** à la ROM.

## 6. Comment ajouter une réponse

Écrire la procédure de test et le résultat dans le document concerné, passer l'étiquette en **[A]**, citer l'émulateur (version) ou la machine, et supprimer la ligne ici.
