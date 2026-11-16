; =====================================================================
;  musique.inc : mélodie 1 bit jouée SANS BLOQUER le programme
;  Exemple ORIGINAL du dépôt alice32-tech-ref (syntaxe DASM, 6803).
;
;  - interruption OCF (comparaison de sortie, vecteur $FFF4 -> $3206) :
;    inverse le bit 7 de $BFFF toutes les « demi-périodes » de la note ;
;    on ajoute la demi-période à OCR, donc la hauteur ne dérive pas ;
;  - le débordement du compteur (TOF, 65,536 ms, voir commun.inc) appelle
;    MUS_TICK, qui fait avancer la partition (durées en débordements).
;  Coût : ~60 cycles par inversion, soit ~5 % du processeur pour un la 440.
;  Doc : 05-clavier-son-joysticks.md §2 et §4, 13-programmation-jeux.md §5.
;  Statut : [C] non testé sur machine réelle.
; =====================================================================

MUS_INIT                     ; appelée par HORLOGE, interruptions masquées
        ldaa #$7E            ; JMP IT_OCF dans le trampoline
        staa VEC_OCF
        ldx  #IT_OCF
        stx  VEC_OCF+1
        ldx  #MELODIE
        stx  MPTR
        ldaa #1
        staa MDUR            ; la première note part au prochain TOF
        clr  MASQUE
        clr  SONVAL
        ldd  #1000
        std  DEMIP
        ldd  TCNT
        addd #200
        std  OCR             ; acquitte OCF (après la lecture de TCSR)
        rts

; --- interruption OCF : une inversion du haut-parleur -------------------
IT_OCF  ldaa TCSR            ; acquittement 1/2
        ldd  OCR
        addd DEMIP
        std  OCR             ; acquittement 2/2 + prochaine échéance
        ldaa SONVAL
        eora MASQUE          ; MASQUE = $80 (note) ou 0 (silence)
        staa SONVAL
        staa CLASON
        rti

; --- un pas de partition (appelé par IT_TOF) -----------------------------
MUS_TICK
        dec  MDUR
        beq  MT_NOTE
        ldaa MDUR
        cmpa #1
        bne  MT_F
        ldaa MLEN            ; articulation : dernier pas muet pour les
        cmpa #3              ; notes de 3 pas et plus
        blo  MT_F
        clr  MASQUE
MT_F    rts
MT_NOTE ldx  MPTR
        ldaa 0,x
        cmpa #$FF            ; fin : reprise
        bne  MT_1
        ldx  #MELODIE
        ldaa 0,x
MT_1    ldab 1,x
        stab MDUR
        stab MLEN
        inx
        inx
        stx  MPTR
        staa NOTEACT
        tsta
        beq  MT_SIL
        asla                 ; 2 octets par demi-période
        tab
        ldx  #PERIODES-2
        abx
        ldd  0,x
        std  DEMIP
        ldaa #$80
        staa MASQUE
        rts
MT_SIL  clr  MASQUE
        rts

MPTR    dc.w 0
DEMIP   dc.w 0
MDUR    dc.b 0
MLEN    dc.b 0
MASQUE  dc.b 0
SONVAL  dc.b 0
NOTEACT dc.b 0               ; note en cours (0 = silence), pour l'affichage
