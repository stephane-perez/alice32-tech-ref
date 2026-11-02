; =====================================================================
;  partie-logo.inc : logo « ALICE 32 » en carte de tuiles, défilement
;  vertical FLUIDE par le registre ROR (YOR) + tuiles redéfinies.
;  Exemple ORIGINAL du dépôt alice32-tech-ref (syntaxe DASM, 6803).
;
;  Principe (doc 13 §3.4 et §3.7, doc 04 §4 ROR) :
;  - la carte virtuelle a des rangées m = 0, 1, 2… ; la rangée m est rangée
;    dans la rangée mémoire Y(m) = 8 + (m mod 24) de la page ;
;  - YOR = Y(pos) : la rangée de carte « pos » est en haut de l'écran ;
;    augmenter pos d'une unité fait monter tout l'écran de 10 points,
;    il suffit d'écrire UNE rangée (celle qui entre) ;
;  - entre deux rangées, le décalage fin p (0-9 points) est obtenu en
;    redéfinissant 3 tuiles : chaque case affiche les lignes p à p+9 de
;    « sa » tuile suivie de celle du dessous. Une case du logo est donc
;    codée par la paire (case, case du dessous) : 0 = plein/plein,
;    1 = plein/vide, 2 = vide/plein, tuile 32 (vide) sinon.
;  Coût par image : 40 octets OCT (+ 1 IND et 40 KRF quand pos change).
;  Statut : [C] non testé sur machine réelle.
; =====================================================================

LOGO_M0 EQU 24               ; première rangée de carte du logo

PARTIE1 clra
        jsr  EFFACE
        ldaa #8
        jsr  ECRROR          ; YOR = 8, page en bloc 0
        clr  TXY
        ldx  #TITRE1
        ldaa #$70            ; blanc sur noir
        clrb
        jsr  TEXTE
        clr  LP
        clr  LPOS
        clr  LNEW
        ldd  #0
        std  LQ
        jsr  L_TUILES
; les 24 rangées de départ (carte 0 à 23 : vide, le logo est en 24-30)
        clr  LM
P1A     ldaa LM
        jsr  L_PREP
        ldaa LM
        jsr  L_YDE
        jsr  L_ECR
        inc  LM
        ldaa LM
        cmpa #24
        bne  P1A
; script : (position cible en points, pause en images)
        ldx  #SCRIPT1
        stx  LSCR
P1B     ldx  LSCR
        ldaa 0,x
        cmpa #$FF
        beq  P1FIN
        ldd  0,x
        std  LCIBLE
        ldaa 2,x
        staa LPAUSE
        inx
        inx
        inx
        stx  LSCR
P1C     ldd  LQ
        subd LCIBLE
        beq  P1PAUSE
        bcs  P1MONTE         ; LQ < cible : le logo monte
        jsr  L_DESC
        bra  P1IMG
P1MONTE jsr  L_MONTE
P1IMG   jsr  VSYNC
        jsr  L_APPL
        jsr  CONTROLE
        bne  P1FIN
        bra  P1C
P1PAUSE ldaa LPAUSE
        beq  P1B
        deca
        staa LPAUSE
        jsr  VSYNC
        jsr  CONTROLE
        bne  P1FIN
        bra  P1C
P1FIN   rts

; --- monter d'un point --------------------------------------------------
L_MONTE ldx  LQ
        inx
        stx  LQ
        inc  LP
        ldaa LP
        cmpa #10
        bne  LMF
        clr  LP
        inc  LPOS
        ldaa LPOS            ; la rangée qui entre en bas : pos + 23
        adda #23
        psha
        jsr  L_PREP
        pula
        jsr  L_YDE
        staa LROWY
        ldaa LPOS
        jsr  L_YDE
        staa LROR
        ldaa #1
        staa LNEW
LMF     rts

; --- descendre d'un point -----------------------------------------------
L_DESC  ldx  LQ
        dex
        stx  LQ
        ldaa LP
        bne  LD1
        ldaa #9
        staa LP
        dec  LPOS
        ldaa LPOS            ; la rangée qui entre en haut : pos
        jsr  L_PREP
        ldaa LPOS
        jsr  L_YDE
        staa LROWY
        staa LROR
        ldaa #1
        staa LNEW
        rts
LD1     dec  LP
        rts

; --- à faire juste après la synchro trame -------------------------------
L_APPL  ldaa LNEW
        beq  L_TUILES
        clr  LNEW
        ldaa LROR
        jsr  ECRROR          ; nouvelle origine verticale
        ldaa LROWY
        jsr  L_ECR           ; la rangée qui entre
; --- envoyer les 3 tuiles décalées de LP lignes (codes 0-2 de G'0) -------
L_TUILES
        ldx  #LTB            ; construire les 40 octets du tampon Y' = 0 :
        ldaa LP              ; pour chaque tranche NT (0-9), i = p + NT,
        staa LTMP            ; X = 4 NT + code : tuile 0, 1, 2, puis 3 (vide)
        ldaa #10
        staa LCPT
LT1     ldab LTMP
        cmpb #10
        bhs  LT_BAS
        pshx                 ; i < 10 : on est dans la case elle-même
        ldx  #PLEIN
        abx
        ldaa 0,x
        pulx
        staa 0,x             ; plein/plein
        staa 1,x             ; plein/vide
        clr  2,x             ; vide/plein
        bra  LT3
LT_BAS  subb #10             ; i >= 10 : on est dans la case du dessous
        pshx
        ldx  #PLEIN
        abx
        ldaa 0,x
        pulx
        staa 0,x
        clr  1,x
        staa 2,x
LT3     clr  3,x
        inx
        inx
        inx
        inx
        inc  LTMP
        dec  LCPT
        bne  LT1
        ldx  #LTB
        ldaa #40
        staa OS_N
        clra                 ; R4 = 0 : tampon des codes 0-3
        ldab #$C0            ; R5 : Z0 Z1 = 11 (bloc 3), X = 0
        jmp  OCTSEQ

; --- A = rangée de carte m -> A = rangée mémoire 8 + (m mod 24) -----------
L_YDE   cmpa #24
        blo  LY1
        suba #24
        bra  L_YDE
LY1     adda #8
        rts

; --- A = rangée de carte m -> X = ses 40 cases (rangée vide hors du logo)
L_ADR   suba #LOGO_M0
        bcs  LA_V
        cmpa #LOGO_H
        bhs  LA_V
        ldab #40
        mul
        addd #LOGO
        std  TMPW
        ldx  TMPW
        rts
LA_V    ldx  #LOGOZ
        rts

; --- préparer dans LBUF les codes (40) puis attributs (40) de la rangée m
L_PREP  staa LTMP
        bsr  L_ADR
        stx  LPA
        ldaa LTMP
        inca
        bsr  L_ADR
        stx  LPB
        ldx  #LBUF
        stx  LPO
        ldaa #40
        staa LCPT
LPR1    ldx  LPA
        ldaa 0,x             ; a = couleur de la case
        inx
        stx  LPA
        ldx  LPB
        ldab 0,x             ; b = couleur de la case du dessous
        inx
        stx  LPB
        tsta
        beq  LPR_A0
        tstb
        beq  LPR_FE
        clrb                 ; plein / plein : tuile 0
        bra  LPR_ST
LPR_FE  ldab #1              ; plein / vide : tuile 1
        bra  LPR_ST
LPR_A0  tstb
        beq  LPR_V
        tba                  ; vide / plein : tuile 2, couleur du dessous
        ldab #2
        bra  LPR_ST
LPR_V   ldab #T_D0           ; vide (A = 0 : noir sur noir)
LPR_ST  asla                 ; couleur en premier plan, fond noir
        asla
        asla
        asla
        ldx  LPO
        stab 0,x
        staa 40,x
        inx
        stx  LPO
        dec  LCPT
        bne  LPR1
        rts

; --- écrire LBUF dans la rangée mémoire A (KRF, G'0) ----------------------
L_ECR   psha
        jsr  ATTEND
        pula
        staa R6              ; Y ; Z2 = Z3 = 0
        clr  R7              ; X = 0 ; Z0 = Z1 = 0 : page en bloc 0
        ldaa #B_GP0
        staa R2
        ldaa #C_KRF
        staa R0
        ldx  #LBUF
        ldab #40
LE1     ldaa 0,x
LE2     tst  R0
        bmi  LE2
        staa R1
        ldaa 40,x
        staa XR3             ; KRF
        inx
        decb
        bne  LE1
        rts

; position (en points) à atteindre, puis pause (en images) ; $FFFF = fin
SCRIPT1 dc.w 160             ; monte jusqu'au milieu (logo en rangée 8)
        dc.b 100
        dc.w 310             ; continue jusqu'à disparaître en haut
        dc.b 25
        dc.w 160             ; redescend au milieu
        dc.b 100
        dc.w 0               ; et sort par le bas
        dc.b 25
        dc.w $FFFF

TITRE1  dc.b " ALICE 32 DEMO - 1/3 : LOGO ET YOR",0

LQ      dc.w 0               ; position = 10 x pos + p
LCIBLE  dc.w 0
LSCR    dc.w 0
LPA     dc.w 0
LPB     dc.w 0
LPO     dc.w 0
LPAUSE  dc.b 0
LPOS    dc.b 0
LP      dc.b 0
LM      dc.b 0
LTMP    dc.b 0
LCPT    dc.b 0
LNEW    dc.b 0
LROR    dc.b 0
LROWY   dc.b 0
