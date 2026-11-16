; =====================================================================
;  math3d.inc : objets 3D, rotations et projection (partagé)
;  Exemple ORIGINAL du dépôt alice32-tech-ref (syntaxe DASM, 6803).
;  Le fichier qui l'inclut définit AVANT :
;    M3_CX, M3_CY : centre de la fenêtre (points)
;    M3_W, M3_H   : taille de la fenêtre (points, au plus 255 / 128 + centre)
;    M3_X15       : 1 = projection agrandie de moitié (fenêtre plus grande)
;    V_PX         : 16 abscisses projetées, suivies de 16 ordonnées (V_PY)
;  et inclut donnees-persp.inc et donnees-sinus.inc (par fin.inc).
; =====================================================================

; --- angles : avancer selon les vitesses de l'objet -----------------------
V_ANGLES
        ldx  V_OBJ
        ldaa V_AX
        adda 3,x
        staa V_AX
        ldaa V_AY
        adda 4,x
        staa V_AY
        ldaa V_AZ
        adda 5,x
        staa V_AZ
        rts

; --- lire l'en-tête de l'objet courant ---------------------------------
V_CHOISIT
        ldx  V_OBJ
        ldaa 0,x
        staa V_NV
        ldaa 1,x
        staa V_NA
        ldaa 2,x
        staa V_COUL
        ldab #6
        abx
        stx  V_SOMM          ; sommets
        ldab V_NV
        aslb
        addb V_NV            ; 3 octets par sommet
        abx
        stx  V_ARET          ; arêtes
        rts

; =====================================================================
;  Rotation et projection des sommets -> V_PX, V_PY
; =====================================================================
V_TRANSF
        ldaa V_AY
        jsr  SINCOS
        stab V_CY
        staa V_SY
        ldaa V_AX
        jsr  SINCOS
        stab V_CXX
        staa V_SX
        ldaa V_AZ
        jsr  SINCOS
        stab V_CZ
        staa V_SZ
        ldx  V_SOMM
        clr  V_I
VT1     stx  V_P
        ldaa 0,x
        staa V_X
        ldaa 1,x
        staa V_Y
        ldaa 2,x
        staa V_Z
; rotation autour de Y : (x, z)
        ldaa V_X
        staa R_U
        ldaa V_Z
        staa R_V
        ldaa V_CY
        staa R_C
        ldaa V_SY
        staa R_S
        jsr  ROT2
        ldaa R_U
        staa V_X
        ldaa R_V
        staa V_Z
; autour de X : (y, z)
        ldaa V_Y
        staa R_U
        ldaa V_Z
        staa R_V
        ldaa V_CXX
        staa R_C
        ldaa V_SX
        staa R_S
        jsr  ROT2
        ldaa R_U
        staa V_Y
        ldaa R_V
        staa V_Z
; autour de Z : (x, y)
        ldaa V_X
        staa R_U
        ldaa V_Y
        staa R_V
        ldaa V_CZ
        staa R_C
        ldaa V_SZ
        staa R_S
        jsr  ROT2
; perspective : facteur = PERSP[z + 128]
        ldab V_Z
        eorb #$80
        ldx  #PERSP
        abx
        ldab 0,x
        stab V_F
        ldab V_I
        ldx  #V_PX
        abx
        ldaa R_U             ; x écran = M3_CX + x f / 256
        ldab V_F
        jsr  PMUL
        IF M3_X15
        tab                  ; x 1,5
        asrb
        aba
        ENDIF
        adda #M3_CX
        cmpa #M3_W
        bhs  VT_HORS
        staa 0,x
        ldaa R_V             ; y écran = M3_CY - y f / 256
        ldab V_F
        jsr  PMUL
        IF M3_X15
        tab
        asrb
        aba
        ENDIF
        nega
        adda #M3_CY
        cmpa #M3_H
        bhs  VT_HORS
        staa 16,x
        bra  VT2
VT_HORS ldaa #$FF
        staa 0,x
VT2     ldx  V_P
        inx
        inx
        inx
        inc  V_I
        ldaa V_I
        cmpa V_NV
        beq  VT3
        jmp  VT1
VT3     rts

; --- A = angle -> A = sinus, B = cosinus (signés, -126..126) -----------
SINCOS  staa SC1+2
        adda #64
        staa SC2+2
SC1     ldaa SINUS           ; (adresses modifiées : SINUS est aligné)
        suba #64
        asla
SC2     ldab SINUS
        subb #64
        aslb
        rts

; --- (R_U, R_V) tourné de (R_C, R_S) : U' = (U c - V s) / 128,
;     V' = (U s + V c) / 128 -------------------------------------------
ROT2    ldaa R_U
        ldab R_C
        jsr  SMUL
        std  R_T1
        ldaa R_V
        ldab R_S
        jsr  SMUL
        std  R_T2
        ldd  R_T1
        subd R_T2
        asld
        staa R_NU
        ldaa R_U
        ldab R_S
        jsr  SMUL
        std  R_T1
        ldaa R_V
        ldab R_C
        jsr  SMUL
        addd R_T1
        asld
        staa R_V
        ldaa R_NU
        staa R_U
        rts

; --- D = A x B, signés ---------------------------------------------------
SMUL    staa SM_A
        eorb SM_A
        stab SM_S            ; bit 7 = signe du produit
        eorb SM_A
        tsta
        bpl  SM1
        nega
SM1     tstb
        bpl  SM2
        negb
SM2     mul
        tst  SM_S
        bpl  SM3
        coma
        comb
        addd #1
SM3     rts

; --- D = A (signé) x B (non signé) ---------------------------------------
PMUL    tsta
        bmi  PM1
        mul
        rts
PM1     nega
        mul
        coma
        comb
        addd #1
        rts

; =====================================================================
;  Objets : nb sommets, nb arêtes, couleur (D), vitesses X, Y, Z,
;  sommets (x, y, z signés, rayon <= 60), arêtes (paires de sommets).
;  Dessins originaux.
; =====================================================================
OBJ_CUBE
        dc.b 8, 12, 0, 1, 2, 3
        dc.b -34,-34,-34,  34,-34,-34,  34, 34,-34, -34, 34,-34
        dc.b -34,-34, 34,  34,-34, 34,  34, 34, 34, -34, 34, 34
        dc.b 0,1, 1,2, 2,3, 3,0, 4,5, 5,6, 6,7, 7,4, 0,4, 1,5, 2,6, 3,7

OBJ_VAIS                     ; chasseur : nez, cockpit, ailes, arrière, dérive
        dc.b 8, 16, 1, 1, 3, 0
        dc.b   0,  0, 56     ; 0 nez
        dc.b   0, 12,  8     ; 1 cockpit
        dc.b -52, -4,-22     ; 2 aile gauche
        dc.b  52, -4,-22     ; 3 aile droite
        dc.b -16,  6,-30     ; 4 arrière gauche
        dc.b  16,  6,-30     ; 5 arrière droit
        dc.b   0,-10,-28     ; 6 ventre
        dc.b   0, 28,-36     ; 7 dérive
        dc.b 0,1, 0,2, 0,3, 0,6, 1,4, 1,5, 2,4, 3,5
        dc.b 2,6, 3,6, 4,5, 4,6, 5,6, 1,7, 7,4, 7,5

; --- variables du calcul 3D ---------------------------------------------
V_OBJ   dc.w 0
V_SOMM  dc.w 0
V_ARET  dc.w 0
V_P     dc.w 0
R_T1    dc.w 0
R_T2    dc.w 0
V_NV    dc.b 0
V_NA    dc.b 0
V_COUL  dc.b 0
V_AX    dc.b 0
V_AY    dc.b 0
V_AZ    dc.b 0
V_CY    dc.b 0
V_SY    dc.b 0
V_CXX   dc.b 0
V_SX    dc.b 0
V_CZ    dc.b 0
V_SZ    dc.b 0
V_I     dc.b 0
V_X     dc.b 0
V_Y     dc.b 0
V_Z     dc.b 0
V_F     dc.b 0
R_U     dc.b 0
R_V     dc.b 0
R_C     dc.b 0
R_S     dc.b 0
R_NU    dc.b 0
SM_A    dc.b 0
SM_S    dc.b 0
