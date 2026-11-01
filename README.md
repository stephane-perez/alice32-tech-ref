# Base de connaissances Alice 32 (Matra-Hachette)

Documentation en **français**, en Markdown, de l'**Alice 32** (microprocesseur EF6803 à 1 MHz, contrôleur vidéo EF9345), destinée à écrire de **nouveaux logiciels** pour cette machine : **jeux en assembleur** et **démos** (demomaking) qui exploitent ses particularités, sur machine réelle ou sous émulateur (DCAlice, MAME).

Périmètre : **Alice 32 uniquement** (pas le MC-10, l'Alice 4K ni l'Alice 90, sauf mention).

État : **version 0.2**, construite à partir de la copie du site <http://alice32.free.fr/> et du lot de documentation technique (fiche et note d'application de l'EF9345, fiche du MC6803E, source commenté de la ROM, *Les Astuces d'Alice*, guide de l'éditeur-assembleur). Les questions encore ouvertes sont dans [`docs/12-questions-ouvertes.md`](docs/12-questions-ouvertes.md).

**Pour commencer à programmer un jeu ou une démo** : lire `04`, puis `13`, puis `10`, et partir de [`exemples/squelette-jeu.asm`](exemples/squelette-jeu.asm).

## Sommaire

| Fichier | Contenu |
|---|---|
| [`docs/00-sources.md`](docs/00-sources.md) | Origine de chaque information, crédits, niveaux de confiance |
| [`docs/01-machines.md`](docs/01-machines.md) | L'Alice 32 : composants, comparaison rapide |
| [`docs/02-carte-memoire.md`](docs/02-carte-memoire.md) | Carte mémoire (RAM, ROM, E/S, extensions, mémoire vidéo) |
| [`docs/03-registres-et-ports.md`](docs/03-registres-et-ports.md) | 6803 (ports, timer, vecteurs), adresses d'E/S |
| [`docs/04-ef9345-video.md`](docs/04-ef9345-video.md) | **Contrôleur vidéo EF9345** : registres, commandes, caractères redéfinis, 80 colonnes, temps d'exécution |
| [`docs/05-clavier-son-joysticks.md`](docs/05-clavier-son-joysticks.md) | Clavier (ROM et lecture directe), son, manettes, minuterie |
| [`docs/06-rom-et-points-d-entree.md`](docs/06-rom-et-points-d-entree.md) | ROM de 16 Ko, routines appelables, variables système |
| [`docs/07-basic-microcolor.md`](docs/07-basic-microcolor.md) | Jetons et particularités du BASIC |
| [`docs/08-disk-basic-et-systeme-de-fichiers.md`](docs/08-disk-basic-et-systeme-de-fichiers.md) | Disk BASIC 2.4, API de fichiers, contrôleur MCX32-FDJ |
| [`docs/09-cassette-et-formats-de-fichiers.md`](docs/09-cassette-et-formats-de-fichiers.md) | Cassette, `.k7`/`.wav`, `.rom`/`.bin` |
| [`docs/10-outils-de-developpement.md`](docs/10-outils-de-developpement.md) | Assembleur résident, DASM, CC6303, DCAlice, MAME, flux de travail |
| [`docs/11-catalogue-logiciels.md`](docs/11-catalogue-logiciels.md) | 83 logiciels de l'archive, dont ceux avec sources |
| [`docs/12-questions-ouvertes.md`](docs/12-questions-ouvertes.md) | Incertitudes, erreurs des sources, expériences à faire |
| [`docs/13-programmation-jeux.md`](docs/13-programmation-jeux.md) | **Jeux rapides et démos** : budget cycles, techniques EF9345, idées |
| [`exemples/squelette-jeu.asm`](exemples/squelette-jeu.asm) | Squelette DASM : init écran, caractère redéfini, déplacement, synchro trame |

## Convention de confiance

- **[A]** documenté dans une source citée (`00-sources.md`) ;
- **[B]** déduit de la ROM ou du schéma ;
- **[C]** hypothèse, à tester.

**Rien n'a été exécuté** sur une vraie Alice ni sous émulateur : l'exemple s'assemble avec DASM mais n'est pas testé. Les durées d'exécution de l'EF9345 viennent de la fiche et doivent être mesurées.

## Ce qui n'est volontairement PAS dans ce dépôt

Le dépôt étant public :

- les **ROM** (© Matra-Hachette / Microsoft) et leur **désassemblage / source commenté complet** ;
- les **schémas** (scans de Daniel Coulom) et les **manuels commerciaux** ;
- les logiciels sous droits.

Les adresses et rôles des routines utiles sont documentés ; ROM, source commenté et documentation se récupèrent sur <http://alice32.free.fr/>.

## Contribuer

1. Ajouter la source dans `docs/00-sources.md` avant d'ajouter un fait.
2. Étiqueter le fait **[A]/[B]/[C]**.
3. Une hypothèse testée devient **[A]**, avec la procédure et l'émulateur (version) ou la machine utilisés.
4. Tout en français.
