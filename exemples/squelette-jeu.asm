; =====================================================================
;  Squelette de programme en langage machine pour Alice 32 (DASM)
;  Exemple ORIGINAL de ce dépôt. Assemblé avec DASM (aucune erreur) ;
;  NON testé sur machine réelle ni sous émulateur : à vérifier.
;
;  Ce qu'il montre :
;    - initialiser l'écran 40 colonnes avec la routine de la ROM ;
;    - redéfinir un caractère (tuile 8 x 10) dans le jeu G'0 ;
;    - l'afficher avec KRF et le déplacer avec les flèches (POLCA) ;
;    - synchroniser la boucle sur la trame (bit 2 de R0, après VRM).
;  Lancement depuis le BASIC :  EXEC 16384   ($4000)
;  Retour au BASIC : touche BREAK (code ASCII $03).
; =====================================================================
        PROCESSOR 6803

R0      EQU $BF20            ; commande / état de l'EF9345
R1      EQU $BF21
R2      EQU $BF22
R3      EQU $BF23
R4      EQU $BF24
R5      EQU $BF25
R6      EQU $BF26
R7      EQU $BF27
EXEC    EQU 8                ; décalage : accès « avec exécution »

TECRAN  EQU $301A            ; type d'écran (0 = 80x25, 1 = 40x25, 2 = 32x16)
INASS   EQU $D42C            ; ROM : initialise l'écran selon TECRAN
POLCA   EQU $F883            ; ROM : touche -> A (0 si aucune)

KRF_W   EQU $01              ; écrire un caractère long, pointeur +1
OCT_AUX EQU $34              ; écrire un octet, pointeur auxiliaire
VRM     EQU $95              ; démasquer VSYNC dans le registre d'état
BREAK   EQU $03

        ORG $4000

DEBUT   ldaa #1              ; 40 colonnes
        staa TECRAN
        jsr  INASS           ; efface l'écran, recharge les jeux, règle l'EF9345
        jsr  ATTEND
        ldaa #VRM
        staa R0+EXEC         ; le bit 2 de R0 suit désormais la synchro verticale
        jsr  ATTEND

; --- redéfinir le caractère n° 0 de G'0 (bloc 3) ---------------------
;  R4 = 0 0 Z2 C6 C5 C4 C3 C2     R5 = Z0 Z1 0 0 NT(3:0)... voir doc 04
;  bloc 3 : Z0 = 1, Z1 = 1, Z2 = 0, Z3 = 0 (Z3 se met dans le bit 6 de R6)
        clr  R6
        clr  R4
        ldaa #$C0            ; Z0 Z1 = 11, tranche 0, caractère 0
        staa R5
        ldaa #OCT_AUX
        staa R0              ; commande chargée, pas encore exécutée
        ldx  #TUILE
        ldab #10
TR1     ldaa 0,x
        inx
        staa R1+EXEC         ; écrit une tranche
        bsr  ATTEND
        ldaa R5
        adda #4              ; tranche suivante (n° dans les bits 5-2 de R5)
        staa R5
        decb
        bne  TR1

; --- afficher la tuile en (X,Y) ---------------------------------------
        ldaa #20
        staa POSX
        ldaa #16
        staa POSY
BOUCLE  bsr  AFFICHE
        jsr  POLCA
        beq  SYNC
        cmpa #BREAK
        beq  FIN
        cmpa #$08            ; flèche gauche
        bne  T1
        dec  POSX
T1      cmpa #$09            ; flèche droite
        bne  T2
        inc  POSX
T2      cmpa #$0B            ; flèche haut
        bne  T3
        dec  POSY
T3      cmpa #$0A            ; flèche bas
        bne  SYNC
        inc  POSY
SYNC    bsr  VSYNC
        bra  BOUCLE
FIN     rts                  ; retour au BASIC

; --- dessiner la tuile ------------------------------------------------
;  (une version complète effacerait l'ancienne position ; limites non testées)
AFFICHE bsr  ATTEND
        ldaa POSY
        staa R6
        ldaa POSX
        staa R7
        ldaa #KRF_W
        staa R0
        clr  R1              ; caractère n° 0
        ldaa #$80            ; B : jeu G'0
        staa R2
        ldaa #$70            ; A : blanc sur noir
        staa R3+EXEC         ; écrire R3 avec exécution lance KRF
        rts

; --- attendre la fin d'une commande ---------------------------------
ATTEND  tst  R0
        bmi  ATTEND
        rts

; --- attendre le début du retour de trame ---------------------------
VSYNC   ldaa R0
        anda #$04
        bne  VSYNC           ; attend que le bit 2 passe à 0
        rts

POSX    dc.b 0
POSY    dc.b 0
; tranches de la tuile, bit 0 = point de gauche
TUILE   dc.b $3C,$7E,$FF,$FF,$FF,$FF,$FF,$FF,$7E,$3C
