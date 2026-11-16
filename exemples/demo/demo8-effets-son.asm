; =====================================================================
;  DÉMO 8 : son enrichi par interruptions (PWM, vibrato, arpège)
;  Exemple ORIGINAL du dépôt alice32-tech-ref, syntaxe DASM :
;      dasm demo8-effets-son.asm -f3 -obuild/demo8-effets-son.bin
;  CLOADM puis EXEC 13312. ESPACE = effet suivant, ENTRÉE = BASIC.
;  Les barres continuent de défiler : le processeur reste disponible.
;  NON testé sur machine réelle.
; =====================================================================
        PROCESSOR 6803

AVEC_MUSIQUE EQU 0           ; l'horloge seule : le son est dans musique-plus.inc

        ORG $3400
DEBUT   jmp  DEMARRE
PRINCIPAL
        ldaa #$70
        jsr  EFFACE
        clr  TXY
        ldx  #T8_1
        ldaa #$70
        clrb
        jsr  TEXTE
        ldaa #30
        staa TXY
        ldx  #T8_2
        ldaa #$30
        ldab #4
        jsr  TEXTE
        clr  P8_I
        jsr  P8_NOM
        jsr  M2_INIT
P8      jsr  VSYNC
        jsr  M2_IMAGE
        inc  P8_PH
        ldaa P8_PH
        staa BV
        ldaa #5
        staa BDV
        ldaa #20
        jsr  BARRE
        ldaa P8_PH
        nega
        staa BV
        ldaa #22
        jsr  BARRE
        jsr  CONTROLE        ; ENTRÉE quitte
        beq  P8
        inc  P8_I            ; ESPACE : effet suivant
        ldaa P8_I
        cmpa #5
        bne  P8A
        clr  P8_I
P8A     jsr  P8_NOM
        bra  P8

; --- afficher l'effet P8_I et régler M2_MODE ---------------------------
P8_NOM  ldab P8_I
        ldx  #P8_MODES
        abx
        ldaa 0,x
        staa M2_MODE
        ldaa #24
        mul                  ; 24 octets par nom
        addd #P8_NOMS
        std  TMPW
        ldx  TMPW
        ldaa #16
        staa TXY
        ldaa #$60
        ldab #8
        jmp  TEXTE

T8_1    dc.b " ALICE 32 - SON ENRICHI PAR LE TIMER",0
T8_2    dc.b "ESPACE : EFFET SUIVANT  ENTREE : BASIC",0
P8_MODES dc.b 0,1,2,4,7
P8_NOMS dc.b "CARRE SIMPLE           ",0
        dc.b "PWM (TIMBRE QUI VARIE) ",0
        dc.b "VIBRATO                ",0
        dc.b "ARPEGE (ACCORD)        ",0
        dc.b "LES TROIS ENSEMBLE     ",0
P8_I    dc.b 0
P8_PH   dc.b 0

        INCLUDE "inc/commun.inc"
        INCLUDE "inc/musique-plus.inc"
        INCLUDE "inc/donnees-musique.inc"
        INCLUDE "inc/donnees-periodes2.inc"
        INCLUDE "inc/fin.inc"
