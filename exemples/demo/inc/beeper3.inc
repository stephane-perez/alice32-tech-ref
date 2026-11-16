; =====================================================================
;  beeper3.inc : musique à 3 voix sur le haut-parleur 1 bit
;  Exemple ORIGINAL du dépôt alice32-tech-ref (syntaxe DASM, 6803).
;  Données : donnees-musique3.inc (INCR3, MORCEAU3), outils/gen_donnees.py.
;
;  Chaque voix est un accumulateur de phase 16 bits ; elle « sonne »
;  (sortie 1) tant que l'octet haut de la phase est inférieur à son
;  rapport cyclique (impulsions étroites : 25 %, 25 %, 12,5 %). Les trois
;  voix sont mélangées par un OU logique sur le bit 7 de $BFFF : avec des
;  impulsions étroites, chaque note reste audible (technique des moteurs
;  « beeper » du ZX Spectrum).
;  Fréquences et rapports cycliques sont écrits DANS les instructions
;  (ADDD #, CMPA #) à chaque ligne : 89 cycles par tic, 11 236 tics/s.
;  Le processeur est pris à 100 % (interruptions masquées) ; le clavier
;  est lu entre deux lignes.
;  Statut : [C] non testé sur machine réelle.
; =====================================================================

B3_LIGNE EQU 5               ; une ligne = 5 x 256 tics = 114 ms (un seizième)
B3_D1    EQU 64              ; rapports cycliques (sur 256)
B3_D2    EQU 64
B3_D3    EQU 32

; --- jouer MORCEAU3 ; retour A = 0 (fini), 1 (ESPACE), 2 (ENTRÉE) --------
JOUE3   tpa
        staa B3_CC
        sei
        ldx  #MORCEAU3
        stx  B3_PTR
B3L     ldx  B3_PTR
        ldaa 0,x
        cmpa #$FF
        bne  B3L1
        clra
        jmp  B3FIN
B3L1    jsr  B3_FREQ         ; voix 1
        std  V1A+1
        ldaa #B3_D1
        jsr  B3_DUTY
        staa V1C+1
        ldx  B3_PTR
        ldaa 1,x             ; voix 2
        jsr  B3_FREQ
        std  V2A+1
        ldaa #B3_D2
        jsr  B3_DUTY
        staa V2C+1
        ldx  B3_PTR
        ldaa 2,x             ; voix 3
        jsr  B3_FREQ
        std  V3A+1
        ldaa #B3_D3
        jsr  B3_DUTY
        staa V3C+1
        ldx  B3_PTR
        inx
        inx
        inx
        stx  B3_PTR
        ldaa #B3_LIGNE
        staa B3_CH
        clr  B3_CL
; --- un tic : 89 cycles -------------------------------------------------
TIC
        ldd  B3_P1           ; 5
V1A     addd #0              ; 4  incrément de la voix 1 (modifié)
        std  B3_P1           ; 5
V1C     cmpa #0              ; 2  C = 1 si phase < rapport cyclique (modifié)
        ldab #0              ; 2
        rorb                 ; 2  C -> bit 7
        stab B3_O            ; 4
        ldd  B3_P2
V2A     addd #0
        std  B3_P2
V2C     cmpa #0
        ldab #0
        rorb
        orab B3_O            ; 4  mélange : OU
        stab B3_O
        ldd  B3_P3
V3A     addd #0
        std  B3_P3
V3C     cmpa #0
        ldab #0
        rorb
        orab B3_O
        stab CLASON          ; 4  sortie
        dec  B3_CL           ; 6
        bne  TIC             ; 3
        dec  B3_CH
        bne  TIC
        jsr  LITCLAV         ; entre deux lignes
        tsta
        bne  B3FIN
        jmp  B3L
B3FIN   psha
        clra
        staa CLASON
        ldaa B3_CC
        tap
        pula
        rts

; --- A = note (0 = silence) -> D = incrément de phase ----------------------
B3_FREQ staa B3_N
        tsta
        bne  BF1
        clrb                 ; D = 0
        rts
BF1     deca
        asla
        tab
        ldx  #INCR3
        abx
        ldd  0,x
        rts

; --- A = rapport cyclique voulu -> A = 0 si la note est un silence ---------
B3_DUTY tst  B3_N
        bne  BD1
        clra
BD1     rts

B3_P1   dc.w 0
B3_P2   dc.w 0
B3_P3   dc.w 0
B3_PTR  dc.w 0
B3_O    dc.b 0
B3_CL   dc.b 0
B3_CH   dc.b 0
B3_N    dc.b 0
B3_CC   dc.b 0
