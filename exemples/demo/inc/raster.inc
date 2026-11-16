; =====================================================================
;  raster.inc : écrire un registre de l'EF9345 à un instant précis
;  de la trame (compteur libre du 6803 : 1 µs)
;  Exemple ORIGINAL du dépôt alice32-tech-ref (syntaxe DASM, 6803).
;  Statut : [C] EXPÉRIENCE : l'effet d'un changement de registre pendant
;  l'affichage n'est décrit ni par la fiche ni par ce dépôt ; il n'est
;  visible que sur une vraie machine (ou un émulateur qui dessine ligne
;  par ligne, ce qui reste à vérifier pour DCAlice et MAME).
; =====================================================================

; --- départ : juste après VSYNC, R_T0 = compteur -------------------------
R_DEPART
        ldd  TCNT
        std  R_T0
        rts

; --- attendre que (compteur - R_T0) >= D (µs) ------------------------------
R_ATT   std  R_CIBLE
RA1     ldd  TCNT
        subd R_T0
        subd R_CIBLE
        bcs  RA1
        rts

; --- écrire le registre indirect B (0-7) avec A, sans délai inutile -------
R_IND   psha
RA2     tst  R0
        bmi  RA2
        pula
        staa R1
        orab #$80
        stab XR0
        rts


; --- D -> 5 chiffres décimaux dans R_TXT ------------------------------
R_DEC   std  R_V
        ldx  #R_TXT
        ldaa #'0'
        staa 0,x
        staa 1,x
        staa 2,x
        staa 3,x
        staa 4,x
        ldd  R_V
RD1     subd #10000
        bcs  RD2
        inc  0,x
        bra  RD1
RD2     addd #10000
RD3     subd #1000
        bcs  RD4
        inc  1,x
        bra  RD3
RD4     addd #1000
RD5     subd #100
        bcs  RD6
        inc  2,x
        bra  RD5
RD6     addd #100
RD7     subd #10
        bcs  RD8
        inc  3,x
        bra  RD7
RD8     addd #10
        addb #'0'
        stab 4,x
        rts

R_T0    dc.w 0
R_CIBLE dc.w 0
R_V     dc.w 0
R_COL   dc.b 0
R_TXT   dc.b "00000",0
