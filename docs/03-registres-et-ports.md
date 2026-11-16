# Registres du 6803 et adresses d'E/S

## Registres internes de l'EF6803 / MC6803

> Les adresses ci-dessous sont celles de la fiche standard du MC6803 ; elles ne sont pas toutes listées dans les sources de l'archive. Les lignes confirmées par une source ont leur étiquette.

| Adresse | Registre | Utilisation connue sur Alice |
|---|---|---|
| `$00` | DDR du port 1 | la ROM écrit `$FF` (port 1 en sortie) au démarrage (`$F72E`) **[B]** |
| `$01` | DDR du port 2 | la ROM y écrit `$01` **[B]** |
| `$02` | **port 1 (données)** | **sélection de la colonne du clavier** (`$FE`, `$FD`, `$FB`, `$F7`, `$EF`, `$DF`, `$BF`, `$7F`) **[A, S9]** |
| `$03` | port 2 (données) | **bit 1 = touches SHIFT / CONTROL** (selon la colonne choisie en `$02` : `$7F` pour SHIFT, `$FE` pour CONTROL ; 0 = enfoncée) **[A, S20]** ; le bit 2 est testé par la routine d'affichage de la ROM avant d'émettre vers l'imprimante (état/busy série) ; sortie série par bit-banging **[B, S4 `$F9C6`]** |
| `$08` | TCSR (timer control/status) | bit 5 = TOF (débordement du compteur), bit 6 = OCF ; bits 1-2 et 3 = autorisations d'interruption ; lire TCSR puis `$09` remet TOF à zéro **[A, S8]** |
| `$09-$0A` | compteur libre | incrémenté à ~1 MHz ; le poids faible (`$0A`) sert de graine aléatoire dans Tetrice **[A, S9]** |
| `$0B-$0C` | registre de comparaison (OCR) | écrire efface OCF **[A, S8]** |
| `$0D-$0E` | registre de capture (ICR) | **[A, S8]** |
| `$10-$14` | RMCR, TRCSR, RDR, TDR, RAMCR | non étudiés |

Horloge : quartz 4 MHz, donc cycle E ≈ 1 µs **[B, S1]**. Tetrice compte « 15 débordements du timer = 1 seconde » (65 536 µs × 15 ≈ 0,98 s), ce qui confirme ~1 MHz **[A, S9]**.

## Vecteurs d'interruption (haut de la ROM) [A/B]

| Adresse | Vecteur 6803 | Contenu dans la ROM | Rôle |
|---|---|---|---|
| `$FFF0` | SCI | `$3200` | interruption série (saut en RAM) |
| `$FFF2` | TOF (débordement du timer) = **IRQ2** | `$3203` | **[A, S8 : « `$3203` on Alice32 »]** |
| `$FFF4` | OCF (comparaison) = IRQ2 | `$3206` | **[A, S8 : « `$3206` on Alice32 »]** |
| `$FFF6` | ICF (capture) = IRQ2 | `$3209` | |
| `$FFF8` | **IRQ1** (broche IRQ externe) | `$320C` | |
| `$FFFA` | SWI | `$320F` | |
| `$FFFC` | NMI | `$3212` | |
| `$FFFE` | RESET | `$F72E` | initialisation (`ALINI` dans S10, `doRESET` dans S19) |

Les vecteurs pointent donc en RAM (`$3200-$3214`) ; le programme y place un `JMP adresse` (opcode `$7E`) pour détourner l'interruption. Exemple complet (timer en débordement) : `timer_routines.s` de *Tuiles curieuses* — la routine range `JMP irq2` dans le trampoline, programme `TCSR = $04`, fait `CLI`, et le gestionnaire relit `TCSR` pour acquitter et incrémente un compteur en RAM **[A, S8]**.
Pour désactiver, le code remet un `RTI` (`$3B`) dans le trampoline **[A, S8]**.

## Adresses d'E/S de la machine

| Adresse | Accès | Fonction | Source |
|---|---|---|---|
| `$BF20` | L/E | EF9345 R0 : **commande** (écriture) / **état** (lecture : bit 7 = occupé) | A, S8 |
| `$BF21-$BF27` | L/E | EF9345 R1…R7 | A, S8 |
| `$BF28-$BF2F` | E | mêmes registres R0…R7 **avec déclenchement de la commande** (adresse + 8) | A, S8 |
| `$BF30` | L | manette droite : repos `$3F`, haut `$3E`, bas `$3D`, gauche `$3B`, droite `$37` | A, S7, S21 |
| `$BF34` | L | manette gauche (même codage) | A, S7 |
| `$BF30-$BF37` | L | zone des manettes ; DCAlice reproduit les valeurs de la vraie machine depuis 2025 | A, S2 |
| `$BF40` / `$BF41` | L/E | ACIA **6850** : registre de contrôle/état et émission/réception | A, S10 (interface Minitel d'AliceTel) |
| `$BF4A`, `$BF4C`, `$BF4E` | E | déblocage émission + 1200 bauds, émission 75 bauds, blocage émission | A, S10 |
| `$BFFF` | L | **lecture des lignes du clavier** (colonne choisie par `$0002`) | A, S9 |
| `$BFFF` | E | **sortie son** (bit 7 inversé pour produire un son) | A, S8 ; B, S4 `$FFAB` |

Détail de chaque bloc : `04-ef9345-video.md`, `05-clavier-son-joysticks.md`, `08-disk-basic-et-systeme-de-fichiers.md` (registres du contrôleur de disquette en `$BDF0-$BDFF`).

Note S2 : « retour du bit 7 de `$BFFF` à zéro au lieu de un » — l'émulateur renvoie 0 sur ce bit à la lecture pour imiter la machine réelle ; ne pas compter sur ce bit en lecture.
