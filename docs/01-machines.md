# L'Alice 32 : la machine

L'**Alice 32** (Matra-Hachette, 1984) est un micro-ordinateur construit autour d'un **EF6803** (compatible Motorola MC6803) et du processeur vidéo **EF9345**. Son nom vient de sa mémoire : « 16 Ko de mémoire morte + 16 Ko de mémoire vive » **[A, S20]**, soit 8 Ko de RAM pour le processeur et 8 Ko de mémoire privée pour l'EF9345.
Ce dépôt ne décrit **que l'Alice 32** ; les autres machines de la famille (Tandy MC-10, Alice d'origine à MC6847, Alice 90) ne sont mentionnées que lorsqu'un programme ou une doc les distingue.

## Résumé

| Élément | Alice 32 |
|---|---|
| Processeur | EF6803, quartz 4 MHz, horloge interne E = **1 MHz** **[A, S20]** |
| Vidéo | **EF9345** (40 ou 80 colonnes, 8 couleurs, caractères redéfinissables), 8 Ko de mémoire privée **[A, S20]** |
| RAM utilisateur | **8 Ko** (`$3000-$4FFF`), extension de **16 Ko** possible (`$5000-…`) **[A, S7, S8]** |
| ROM | **16 Ko** (`$C000-$FFFF`) : assembleur Matra + MicroColor BASIC 1.0 (Microsoft) **[A]** |
| Modes texte | `CLS 80` / `81` (80 × 25, mode graphique « HIRES » 160 × 125), `CLS 40` (40 × 25), `CLS 32` (32 × 16) **[B, S19]** |
| Clavier | matrice 8 × 7, 53 touches environ **[A]** |
| E/S | cassette (1 200 bauds environ), RS-232 (imprimante), 2 manettes, bus d'extension **[A]** |
| Extensions | RAM 16 Ko, cartouches (Multiports), contrôleur de disquette MCX32-FDJ de Darren Atkinson **[A, S2, S7]** |

DCAlice émule l'Alice 32 (et les autres machines) ainsi que le contrôleur MCX32-FDJ **[A, S2]**. MAME propose un pilote `alice32` **[A, S8]**.
Un logiciel peut être lié à une machine : par exemple *Tuiles curieuses* ne fonctionne que sur Alice 32/90 **[A, S8]**.

## Composants identifiés sur le schéma [S1] — confiance B

| Réf. | Composant | Rôle |
|---|---|---|
| Z8 | **EF6803**, quartz **4 MHz** | processeur |
| Z9 | **EF9345** | contrôleur vidéo |
| Z10, Z11 | 2 × TMS4408NLB (RAM dynamique, 4 bits chacune) | **mémoire privée de l'EF9345 : 8 Ko** (confirmé par S20) |
| Z1, Z2 | 2 × TMS4408NLT (4 bits chacune) | RAM utilisateur (8 Ko) |
| Z6 | ROM « 123128 » (128 kbits = 16 Ko) | ROM système |
| Z5 | gate array MTE **803A005** | contrôle de la RAM dynamique et décodage |
| Z7 | gate array MTE **803A006** | décodage d'adresses / sélections d'E/S, à confirmer |
| Z12 | gate array MTE **803A007** (quartz 12 MHz « Y1 ») | signaux vidéo / adressage de la RAM vidéo |
| J1-J2 | prises magnétophone / RS-232 (niveaux RS232C par Z3, Z4) | cassette, imprimante |
| J4 | connecteur de bus d'extension (36 broches : adresses, données, R/W, E, IRQ, NMI, RESET, entrée son) | extensions |
| J5-J6 | connecteur et matrice du clavier | 8 colonnes × 7 lignes |
| Z13 | régulateur 7805 | alimentation (10 V~) |

Le bus d'extension a 36 points : la broche 35 est inutilisée et la **36 est l'entrée son** ; **NMI est sur la broche 31** **[A, S20 + errata]**. L'interruption IRQ1 n'est pas disponible sur le connecteur.
Incertitude : le rôle précis de chaque gate array est déduit des signaux, pas d'une doc.
