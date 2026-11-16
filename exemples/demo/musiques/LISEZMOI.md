# Musiques YM

Fichiers `.ym` (registres du YM2149 trame par trame) pour `outils/ym2alice.py` et `demo12-ym`.

**Source** : dossier `YmSampleFiles` du dépôt [StSound](https://github.com/arnaud-carre/StSound) d'Arnaud Carré (commit `a27c293`, septembre 2026), fichiers d'exemple largement diffusés dans la scène démo. Les musiques restent l'œuvre de leurs auteurs, cités ci-dessous d'après l'en-tête des fichiers.

| Fichier | Format | Titre | Auteur | Durée | Conversion |
|---|---|---|---|---|---|
| `ANCOOL1.YM` | YM2 | (pas de titre dans le fichier) | (non indiqué) | 92 s | oui ; intro de 1,92 s puis motif de 7,68 s : `--boucle 96 --fin 480` |
| `ND-Loader.ym` | YM6 | Nostalgic-O-Demo Loader Song | TAO of ACF | 10 s | oui, mais le sync-buzzer n'est pas reproduit |
| `ND-Toxygene.ym` | YM6 | Nostalgic-O-Demo Toxygen Music | TAO of ACF | 265 s | idem |
| `Scout.ym` | YM5 | Scout | Jochen Hippel (Jeroen Tel) | 246 s | oui |
| `Union Tcb 2.ym` | MIX1 | — | — | — | **non** : échantillons numériques |
| `VirtualEscape1.YM` | YM6 | Virtual Escape (Equinox) Intro Tune | Jedi / Sector One | 53 s | oui, effets spéciaux non reproduits |
| `VirtualEscape2.ym` | YM6 | Virtual Escape (Equinox) Main Tune | Furax / Equinox | 287 s | idem |
| `YMKNUCK.YM` | YMT1 | — | — | — | **non** : format tracker |
| `enchant1.ym` | YM6 | Enchanted Lands: Intro | Jochen Hippel | 233 s | oui |
| `jess1.ym` | YM5 | Camerto for acid band | Jean-Sébastien Gérard (Jess) | 476 s | oui |
| `jess2.ym` | YM5 | Sharpness Buzztone | Jean-Sébastien Gérard (Jess) | 392 s | oui, effets spéciaux non reproduits |
| `test-alice.ym` | YM6 | Test Alice 32 | dépôt alice32-tech-ref (`outils/ym_test.py`) | 8 s | oui |

Dans la RAM de base (≈ 5,4 Ko pour la musique), un morceau tient 20 à 40 s. Pour choisir ce qui est joué : `--cherche-boucle` trouve les répétitions, puis `--boucle` et `--fin` fixent l'intro et le motif à répéter.
