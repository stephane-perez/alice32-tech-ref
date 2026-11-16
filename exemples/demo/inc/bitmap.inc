; =====================================================================
;  bitmap.inc : fenêtre en VRAI bitmap 160 x 150 pixels en 40 colonnes
;  Exemple ORIGINAL du dépôt alice32-tech-ref (syntaxe DASM, 6803).
;  Le programme principal définit SANS_PALETTE et inclut ce fichier
;  après commun.inc, puis donnees-persp.inc et fin.inc.
;
;  Principe (doc 04 §7.4, doc 13 §3.7) : une fenêtre de 20 x 15 cellules
;  8 x 10 où chaque cellule a SON caractère redéfini : 100 de G'0
;  (bloc 3), 100 de G'10 (bloc 4), 100 de G'11 (bloc 5), avec DOR = $23
;  (réglage de « Tuiles curieuses »). Les 300 caractères forment un
;  bitmap de 160 x 150 pixels, 1 bit par pixel, deux couleurs par cellule.
;
;  Rangement : un tampon de 40 octets de l'EF9345 contient les 10 tranches
;  de 4 caractères consécutifs, dans l'ordre X = 4 x tranche + (code & 3).
;  On associe chaque tampon à un « groupe » de 4 cellules côte à côte
;  (32 x 10 pixels) : 75 groupes = 75 tampons (25 par jeu). Envoyer un
;  groupe = 40 octets par OCT avec incrémentation, sans recalculer
;  l'adresse.
;  À chaque image : on efface en RAM les groupes dessinés à l'image
;  précédente, on trace (Bresenham au pixel près, en notant les groupes
;  touchés), puis on envoie les groupes effacés ou touchés.
;  Statut : [C] non testé sur machine réelle.
; =====================================================================

B_W     EQU 20               ; octets (cellules) par ligne de pixels
B_H     EQU 150              ; lignes de pixels
B_NG    EQU 75               ; groupes
B_COL0  EQU 10               ; première colonne de la fenêtre (sur 40)
B_Y0    EQU 13               ; première rangée mémoire (rangée d'écran 5)
B_DUREE EQU 183              ; une figure pendant 12 s

M3_CX   EQU 80               ; paramètres de math3d.inc
M3_CY   EQU 75
M3_W    EQU 160
M3_H    EQU 150
M3_X15  EQU 1                ; projection agrandie de moitié

; --- zones de travail (après le programme) --------------------------------
B_BM    EQU FINPROG          ; bitmap : 150 x 20 octets
B_USED  EQU B_BM+B_W*B_H     ; 75 : groupe dessiné à cette image
B_SEND  EQU B_USED+B_NG      ; 75 : groupe à envoyer (effacé)
B_GR4   EQU B_SEND+B_NG      ; 75 : R4 du tampon du groupe
B_GPTR  EQU B_GR4+B_NG       ; 75 x 2 : adresse du groupe dans le bitmap
V_PX    EQU B_GPTR+2*B_NG    ; 16 x puis 16 y projetés
B_LX    EQU V_PX+32          ; 64 x puis 64 y de la courbe
V_FINRAM EQU B_LX+128

; =====================================================================
PARTIE6 ldaa #$74            ; blanc sur fond bleu autour de la fenêtre
        jsr  EFFACE
        ldaa #8
        jsr  ECRROR
        ldaa #$23            ; DOR : G'0 bloc 3, G'10 bloc 4, G'11 bloc 5
        ldab #4
        jsr  ECRIND
        clr  TXY
        ldx  #B_TITRE
        ldaa #$74
        clrb
        jsr  TEXTE
        ldaa #10
        staa TXY
        ldx  #B_SOUS
        ldaa #$74
        ldab #2
        jsr  TEXTE
        ldaa #31
        staa TXY
        ldx  #B_AIDE
        ldaa #$74
        ldab #4
        jsr  TEXTE
        jsr  B_TABLES
; bitmap à zéro, aucun groupe dessiné, tout est à envoyer (tuiles vides)
        ldx  #B_BM
B6Z     clr  0,x
        inx
        cpx  #B_USED+B_NG
        bne  B6Z
        ldx  #B_SEND
        ldab #B_NG
B6Z2    ldaa #1
        staa 0,x
        inx
        decb
        bne  B6Z2
        jsr  B_ENVOI
        clr  B_MODE
B6NOUV  ldd  TICKS
        addd #B_DUREE
        std  B_FIN
        jsr  B_PREP
B6B     jsr  B_IMAGE
        jsr  CONTROLE        ; ENTRÉE quitte
        bne  B6S             ; ESPACE : figure suivante
        ldd  TICKS
        subd B_FIN
        bmi  B6B
B6S     inc  B_MODE
        ldaa B_MODE
        cmpa #3
        bne  B6NOUV
        clr  B_MODE
        bra  B6NOUV

; --- préparer la figure B_MODE : objet, couleur, nom ----------------------
B_PREP  ldaa B_MODE
        bne  BP1
        ldx  #OBJ_CUBE
        ldaa #$20            ; vert sur noir
        bra  BP3
BP1     cmpa #1
        bne  BP2
        ldx  #OBJ_VAIS
        ldaa #$70            ; blanc sur noir
        bra  BP3
BP2     ldaa #$60            ; cyan sur noir (courbe)
        bra  BP4
BP3     stx  V_OBJ
        psha
        jsr  V_CHOISIT
        pula
BP4     jsr  B_CASES
        ldaa #29
        staa TXY
        ldab B_MODE          ; nom de la figure (14 caractères)
        ldaa #15
        mul
        addd #B_NOMS
        std  TMPW
        ldx  TMPW
        ldaa #$74
        ldab #13
        jmp  TEXTE

; =====================================================================
;  Tables des groupes : g = 0..74 ; jeu = g / 25 ; tampon = g mod 25
;  tampon 0 -> codes 0-3 (Y' = 0), tampon b > 0 -> Y' = b + 7 (codes 32-127)
;  position : rangée g / 5, cellules 4 (g mod 5) à 4 (g mod 5) + 3
; =====================================================================
B_TABLES
        clr  B_G
        clr  B_JEU
        clr  B_BUF
BT1     ldab B_G
        ldx  #B_GR4
        abx
        ldaa B_BUF           ; Y'
        beq  BT2
        adda #7
BT2     ldab B_JEU
        beq  BT3
        oraa #$20            ; G'10, G'11 : Z2 = 1 (blocs 4, 5)
BT3     staa 0,x             ; R4
; adresse : B_BM + (g / 5) x 200 + (g mod 5) x 4
        ldaa B_G
        clrb
BT6     cmpa #5
        blo  BT7
        suba #5
        incb
        bra  BT6
BT7     asla
        asla
        staa B_TMP           ; 4 x (g mod 5)
        ldaa #200
        mul
        addd #B_BM
        addb B_TMP
        adca #0
        std  TMPW
        ldab B_G
        aslb
        ldx  #B_GPTR
        abx
        ldd  TMPW
        std  0,x
; suivant
        inc  B_BUF
        ldaa B_BUF
        cmpa #25
        bne  BT8
        clr  B_BUF
        inc  B_JEU
BT8     inc  B_G
        ldaa B_G
        cmpa #B_NG
        bne  BT1
        rts

; --- les 300 cases de la fenêtre (A = attribut) ----------------------------
B_CASES staa B_ATTR
        clr  B_ROW
BC1     jsr  ATTEND
        ldaa B_ROW
        adda #B_Y0
        staa R6
        ldaa #B_COL0
        staa R7
        ldaa B_ATTR
        staa R3
        ldaa B_ROW           ; jeu = rangée / 5
        ldab #$80
        cmpa #5
        blo  BC2
        ldab #$A0
        cmpa #10
        blo  BC2
        ldab #$B0
BC2     stab R2
        ldaa #C_KRF
        staa R0
        ldab B_ROW           ; premier groupe de la rangée = 5 x rangée
        tba
        aslb
        aslb
        aba
        staa B_G
        ldaa #5
        staa B_CPT
BC3     ldab B_G
        ldx  #B_GR4
        abx
        ldaa 0,x
        anda #$1F            ; Y'
        asla
        asla                 ; premier code = 4 Y'
        ldab #4
BC4     tst  R0
        bmi  BC4
        staa XR1             ; KRF : code A, puis X + 1
        inca
        decb
        bne  BC4
        inc  B_G
        dec  B_CPT
        bne  BC3
        inc  B_ROW
        ldaa B_ROW
        cmpa #15
        bne  BC1
        rts

; =====================================================================
;  Une image
; =====================================================================
B_IMAGE ldaa B_MODE
        cmpa #2
        beq  BI1
        jsr  V_ANGLES
        jsr  V_TRANSF
        bra  BI2
BI1     jsr  B_LISS
BI2     jsr  B_EFFACE
        ldaa B_MODE
        cmpa #2
        beq  BI3
        jsr  B_ARETES
        bra  BI4
BI3     jsr  B_COURBE
BI4     jmp  B_ENVOI

; --- effacer en RAM les groupes dessinés à l'image précédente ---------------
B_EFFACE
        clr  B_G
BE1     ldab B_G
        ldx  #B_USED
        abx
        tst  0,x
        beq  BE3
        clr  0,x
        ldaa #1
        staa B_NG,x          ; à envoyer
        ldab B_G
        aslb
        ldx  #B_GPTR
        abx
        ldx  0,x
        ldaa #10
        staa B_CPT
BE2     ldd  #0              ; 4 octets par ligne, par mots de 16 bits
        std  0,x
        std  2,x
        ldab #B_W
        abx
        dec  B_CPT
        bne  BE2
BE3     inc  B_G
        ldaa B_G
        cmpa #B_NG
        bne  BE1
        rts

; --- envoyer les groupes effacés ou dessinés -------------------------------
B_ENVOI clr  B_G
BN1     ldab B_G
        ldx  #B_USED
        abx
        ldaa 0,x
        oraa B_NG,x
        beq  BN9
        clr  B_NG,x
        jsr  B_GROUPE
BN9     inc  B_G
        ldaa B_G
        cmpa #B_NG
        bne  BN1
        rts

B_GROUPE
        ldab B_G
        ldx  #B_GR4
        abx
        ldaa 0,x
        ldab #$C0            ; R5 : G'0 = bloc 3 (Z0 = Z1 = 1)
        psha
        ldaa B_G
        cmpa #25
        blo  BG0
        clrb                 ; G'10 = bloc 4
        cmpa #50
        blo  BG0
        ldab #$80            ; G'11 = bloc 5 (Z0 = 1)
BG0     jsr  ATTEND
        pula
        staa R4
        stab R5
        ldaa #C_OCTAI
        staa R0
        ldab B_G
        aslb
        ldx  #B_GPTR
        abx
        ldx  0,x
        ldaa #10
        staa B_CPT
BG1
XX      SET 0
        REPEAT 4             ; une tranche des 4 caractères du tampon
        ldaa XX,x
        tst  R0
        bmi  .-3
        staa XR1
XX      SET XX+1
        REPEND
        ldab #B_W
        abx
        dec  B_CPT
        bne  BG1
        rts

; --- arêtes de l'objet 3D --------------------------------------------------
B_ARETES
        ldx  V_ARET
        ldaa V_NA
        staa B_CPT2
BA1     stx  V_P
        ldab 0,x
        ldx  #V_PX
        abx
        ldaa 0,x
        cmpa #$FF
        beq  BA2
        staa BL_X0
        ldaa 16,x
        staa BL_Y0
        ldx  V_P
        ldab 1,x
        ldx  #V_PX
        abx
        ldaa 0,x
        cmpa #$FF
        beq  BA2
        staa BL_X1
        ldaa 16,x
        staa BL_Y1
        jsr  B_LIGNE
BA2     ldx  V_P
        inx
        inx
        dec  B_CPT2
        bne  BA1
        rts

; --- courbe de Lissajous : x = sin(3t + phase), y = sin(2t) ----------------
B_LISS  ldaa B_PH
        adda #1
        staa B_PH
        clr  B_I
BL1     ldaa B_I             ; t = 4 i
        asla
        asla
        tab
        asla
        aba                  ; 3t
        adda B_PH
        jsr  SINCOS          ; A = sinus
        ldab #72
        jsr  SMUL
        asld
        adda #80
        ldab B_I
        ldx  #B_LX
        abx
        staa 0,x
        ldaa B_I
        asla
        asla
        asla                 ; 2t
        jsr  SINCOS
        ldab #66
        jsr  SMUL
        asld
        nega
        adda #75
        ldab B_I
        ldx  #B_LX
        abx
        staa 64,x
        inc  B_I
        ldaa B_I
        cmpa #64
        bne  BL1
        rts

B_COURBE
        clr  B_I
BK1     ldab B_I
        ldx  #B_LX
        abx
        ldaa 0,x
        staa BL_X0
        ldaa 64,x
        staa BL_Y0
        incb
        andb #63
        ldx  #B_LX
        abx
        ldaa 0,x
        staa BL_X1
        ldaa 64,x
        staa BL_Y1
        jsr  B_LIGNE
        inc  B_I
        ldaa B_I
        cmpa #64
        bne  BK1
        rts

; =====================================================================
;  Segment (BL_X0, BL_Y0) - (BL_X1, BL_Y1) dans le bitmap (Bresenham)
;  x 0-159, y 0-149. État : X = octet, BL_M = bit (bit 0 = pixel de
;  gauche), BL_BX = colonne d'octet, BL_B = ligne dans la cellule (0-9),
;  BL_G = groupe.
; =====================================================================
B_LIGNE ldaa BL_X1           ; toujours de gauche à droite
        cmpa BL_X0
        bhs  BL2
        ldab BL_X0
        staa BL_X0
        stab BL_X1
        ldaa BL_Y0
        ldab BL_Y1
        staa BL_Y1
        stab BL_Y0
BL2     ldaa BL_X1
        suba BL_X0
        staa BL_DX
        clr  BL_DIR
        ldaa BL_Y1
        suba BL_Y0
        bcc  BL3
        nega
        inc  BL_DIR          ; vers le haut
BL3     staa BL_DY
; position de départ
        ldaa BL_Y0
        ldab #B_W
        mul
        addd #B_BM
        std  TMPW
        ldab BL_X0
        lsrb
        lsrb
        lsrb
        stab BL_BX
        ldx  TMPW
        abx
        ldab BL_X0
        andb #7
        ldaa #1
BL4     tstb
        beq  BL5
        asla
        decb
        bra  BL4
BL5     staa BL_M
        ldaa BL_Y0           ; ligne dans la cellule et groupe
        clrb
BL6     cmpa #10
        blo  BL7
        suba #10
        incb
        bra  BL6
BL7     staa BL_B
        tba
        asla
        asla
        aba                  ; 5 x rangée
        ldab BL_BX
        lsrb
        lsrb
        aba
        staa BL_G
        jsr  B_MARQUE
        ldaa BL_DX
        cmpa BL_DY
        blo  BLY
; --- x principal ---
        inca
        staa BL_N
        ldaa BL_DX
        lsra
        staa BL_E
BLX     ldaa 0,x             ; allumer le pixel
        oraa BL_M
        staa 0,x
        dec  BL_N
        beq  BLF
        asl  BL_M            ; pixel suivant à droite, même octet en général
        bcc  BLX1
        jsr  B_XOCT          ; octet suivant
BLX1    ldaa BL_E
        suba BL_DY
        bcc  BLX2
        adda BL_DX
        staa BL_E
        jsr  B_YPAS
        bra  BLX
BLX2    staa BL_E
        bra  BLX
BLF     rts
; --- y principal ---
BLY     ldaa BL_DY
        inca
        staa BL_N
        ldaa BL_DY
        lsra
        staa BL_E
BLY1    ldaa 0,x
        oraa BL_M
        staa 0,x
        dec  BL_N
        beq  BLF
        jsr  B_YPAS
        ldaa BL_E
        suba BL_DX
        bcc  BLY2
        adda BL_DY
        staa BL_E
        jsr  B_XPAS
        bra  BLY1
BLY2    staa BL_E
        bra  BLY1

B_XPAS  asl  BL_M            ; pixel suivant à droite
        bcc  BXF
B_XOCT  rol  BL_M            ; bit 7 -> bit 0 de l'octet suivant
        inx
        inc  BL_BX
        ldab BL_BX
        andb #3
        bne  BXF
        inc  BL_G            ; nouveau groupe
        jmp  B_MARQUE
BXF     rts

B_YPAS  tst  BL_DIR
        bne  BYH
        ldab #B_W            ; vers le bas
        abx
        inc  BL_B
        ldaa BL_B
        cmpa #10
        bne  BXF
        clr  BL_B
        ldaa BL_G
        adda #5
        staa BL_G
        jmp  B_MARQUE
BYH     stx  TMPW            ; vers le haut
        ldd  TMPW
        subd #B_W
        std  TMPW
        ldx  TMPW
        dec  BL_B
        bpl  BXF
        ldaa #9
        staa BL_B
        ldaa BL_G
        suba #5
        staa BL_G
; --- noter le groupe BL_G comme dessiné (X conservé) -----------------------
B_MARQUE
        pshx
        ldab BL_G
        ldx  #B_USED
        abx
        ldaa #1
        staa 0,x
        pulx
        rts

        INCLUDE "inc/math3d.inc"

B_TITRE dc.b " ALICE 32 - VRAI BITMAP 160 X 150",0
B_SOUS  dc.b "300 CARACTERES REDEFINIS : 1 PAR CASE",0
B_AIDE  dc.b "ESPACE : SUITE   ENTREE : BASIC",0
B_NOMS  dc.b " CUBE         ",0
        dc.b " VAISSEAU     ",0
        dc.b " LISSAJOUS    ",0

B_FIN   dc.w 0
B_MODE  dc.b 0
B_G     dc.b 0
B_JEU   dc.b 0
B_BUF   dc.b 0
B_TMP   dc.b 0
B_ROW   dc.b 0
B_ATTR  dc.b 0
B_CPT   dc.b 0
B_CPT2  dc.b 0
B_PH    dc.b 0
B_I     dc.b 0
BL_X0   dc.b 0
BL_Y0   dc.b 0
BL_X1   dc.b 0
BL_Y1   dc.b 0
BL_DX   dc.b 0
BL_DY   dc.b 0
BL_DIR  dc.b 0
BL_E    dc.b 0
BL_N    dc.b 0
BL_M    dc.b 0
BL_BX   dc.b 0
BL_B    dc.b 0
BL_G    dc.b 0
