; =====================================================================
;  commun.inc : constantes et routines partagées (EF9345, clavier, horloge)
;  Exemple ORIGINAL du dépôt alice32-tech-ref (syntaxe DASM, 6803).
;  Références : docs/04-ef9345-video.md, 05-clavier-son-joysticks.md,
;               03-registres-et-ports.md, 13-programmation-jeux.md
;
;  Le programme principal doit définir AVANT l'inclusion :
;    AVEC_MUSIQUE  EQU 0 ou 1
; =====================================================================

; --- EF9345 ($BF20-$BF2F) --------------------------------------------
R0      EQU $BF20            ; commande (écriture) / état (lecture)
R1      EQU $BF21            ; octet C, tranche ou valeur d'un registre indirect
R2      EQU $BF22            ; octet B (jeu, double hauteur/largeur)
R3      EQU $BF23            ; octet A (couleurs)
R4      EQU $BF24            ; pointeur auxiliaire : Y (+ Z2)
R5      EQU $BF25            ; pointeur auxiliaire : X (+ Z0 Z1)
R6      EQU $BF26            ; pointeur principal  : Y (+ Z2, Z3)
R7      EQU $BF27            ; pointeur principal  : X (+ Z0 Z1)
XR0     EQU $BF28            ; mêmes registres « avec exécution » (+8)
XR1     EQU $BF29
XR3     EQU $BF2B

C_KRF   EQU $01              ; KRF écriture + incrémentation de X
C_OCTA  EQU $34              ; OCT écriture, pointeur auxiliaire
C_OCTAI EQU $35              ; idem + incrémentation
C_CLF   EQU $05              ; effacer la page (ne s'arrête pas seule)
C_NOP   EQU $91
C_VRM   EQU $95              ; le bit 2 de l'état suit la synchro trame
IND_MAT EQU 2                ; numéros de registres indirects (IND = $80 + r)
IND_ROR EQU 7

B_G0    EQU $00              ; octet B : jeu interne G0
B_GP0   EQU $80              ; octet B : jeu utilisateur G'0 (bloc 3, DOR = $13)
T_D0    EQU 32               ; tuiles de trame 0 %, 25 %, 50 %, 75 % : codes 32-35

; --- 6803, ROM et E/S -------------------------------------------------
PORT1   EQU $02              ; colonne du clavier
TCSR    EQU $08              ; contrôle/état du timer
TCNT    EQU $09              ; compteur libre (1 µs)
OCR     EQU $0B              ; comparaison de sortie
CLASON  EQU $BFFF            ; lecture : lignes du clavier ; écriture : son (bit 7)
TECRAN  EQU $301A            ; type d'écran pour INASS
INASS   EQU $D42C            ; ROM : initialise l'EF9345 selon TECRAN
VEC_TOF EQU $3203            ; trampoline RAM du débordement du timer
VEC_OCF EQU $3206            ; trampoline RAM de la comparaison de sortie

; =====================================================================
;  Attendre que l'EF9345 soit libre (BUSY = bit 7 de R0)
; =====================================================================
ATTEND  tst  R0
        bmi  ATTEND
        rts

; =====================================================================
;  Écrire un registre indirect : A = valeur, B = numéro (0-7)
; =====================================================================
ECRIND  bsr  ATTEND
        staa R1
        orab #$80
        stab XR0             ; IND + r avec exécution
        rts

; =====================================================================
;  Attendre le début de la synchro trame (front descendant du bit 2).
;  Délai de garde d'environ 45 ms si le bit ne bouge pas (émulateur).
; =====================================================================
VSYNC   ldx  #3000
VS1     dex
        beq  VSF
        ldaa R0
        anda #$04
        beq  VS1             ; attendre la fin d'une éventuelle impulsion
        ldx  #3000
VS2     dex
        beq  VSF
        ldaa R0
        anda #$04
        bne  VS2             ; attendre l'impulsion (bit 2 = 0)
VSF     rts

; =====================================================================
;  Écran 40 colonnes par la ROM, puis VRM
;  (page en blocs 0-2, G'0 en bloc 3, DOR = $13, ROR = $08)
; =====================================================================
INITECRAN
        ldaa #1
        staa TECRAN
        jsr  INASS
        jsr  ATTEND
        ldaa #C_VRM
        staa XR0
        rts

; =====================================================================
;  Effacer la page par CLF : A = attribut (C = espace, B = G0)
; =====================================================================
EFFACE  psha
        jsr  ATTEND
        pula
        staa R3
        ldaa #$20
        staa R1
        clr  R2
        clr  R6
        clr  R7
        ldaa #C_CLF
        staa XR0
        ldx  #2500           ; ~15 ms (DEX/BNE = 6 cycles)
EF1     dex
        bne  EF1
        ldaa #C_NOP          ; arrête CLF
        staa XR0
        rts

; =====================================================================
;  Écrire un registre ROR = A (origine verticale YOR, page en bloc 0)
; =====================================================================
ECRROR  ldab #IND_ROR
        jmp  ECRIND

; =====================================================================
;  Afficher une chaîne du jeu G0 : X = chaîne (fin = 0), A = attribut,
;  B = colonne, TXY = rangée (0 = rangée de service, 8-31 = corps)
; =====================================================================
TEXTE   psha
        jsr  ATTEND
        pula
        staa R3
        clr  R2
        stab R7
        ldaa TXY
        staa R6
        ldaa #C_KRF
        staa R0              ; commande chargée, pas encore exécutée
TX1     ldaa 0,x
        beq  TXF
        inx
TX2     tst  R0
        bmi  TX2
        staa XR1             ; R1 avec exécution : un caractère
        bra  TX1
TXF     rts

; =====================================================================
;  Redéfinir le caractère A du jeu G'0 (bloc 3) avec les 10 octets de X.
;  Au retour X pointe après les 10 octets.
;  R4 = C >> 2 ; R5 = Z0 Z1 (11) + (C & 3) + 4 x tranche   (doc 04, §7.2)
; =====================================================================
DEFCAR  tab
        lsrb
        lsrb
        stab DC_R4
        anda #3
        oraa #$C0
        staa DC_R5
        jsr  ATTEND
        ldaa DC_R4
        staa R4
        ldaa #C_OCTA
        staa R0
        ldab #10
DC1     jsr  ATTEND
        ldaa DC_R5
        staa R5
        adda #4              ; tranche suivante
        staa DC_R5
        ldaa 0,x
        inx
        staa XR1
        decb
        bne  DC1
        rts

; =====================================================================
;  Envoyer OS_N octets de X vers la mémoire de l'EF9345 par OCT + AP
;  avec incrémentation : A = R4, B = R5 de départ.
;  Dans un tampon de jeu de caractères X = 4 x tranche + (code & 3) :
;  des octets consécutifs parcourent les 4 caractères d'un tampon, tranche
;  par tranche.
; =====================================================================
OCTSEQ  psha
        jsr  ATTEND
        pula
        staa R4
        stab R5
        ldaa #C_OCTAI
        staa R0
        ldab OS_N
OS1     ldaa 0,x
        inx
OS2     tst  R0
        bmi  OS2
        staa XR1
        decb
        bne  OS1
        rts

; =====================================================================
;  Palette de dégradés : 256 teintes cycliques.
;  v = 16 x segment + 4 x niveau + (0-3) ;
;  couleur de fond = SEQCOUL[segment], premier plan = SEQCOUL[segment + 1],
;  tuile = trame 0/25/50/75 % selon le niveau.
;  TABC[v] = code de la tuile, TABA[v] = attribut ; tables alignées sur 256.
; =====================================================================
INITPAL ldx  #TABC
IP1     stx  TMPW
        ldaa TMPW+1
        lsra
        lsra
        anda #3
        adda #T_D0
        staa 0,x
        inx
        cpx  #TABC+256
        bne  IP1
        ldx  #TABA
IP2     stx  TMPW
        ldab TMPW+1
        lsrb
        lsrb
        lsrb
        lsrb
        pshx
        ldx  #SEQCOUL
        abx
        ldaa 1,x             ; premier plan
        asla
        asla
        asla
        asla
        oraa 0,x             ; fond
        pulx
        staa 0,x
        inx
        cpx  #TABA+256
        bne  IP2
; tuiles de trame 32-35
        ldaa #T_D0
        staa TMPC
        ldx  #TRAMES
IP3     ldaa TMPC
        jsr  DEFCAR
        inc  TMPC
        ldaa TMPC
        cmpa #T_D0+4
        bne  IP3
        rts

; =====================================================================
;  Une rangée de dégradé : A = Y (8-31) ; teinte de départ BV, pas BDV.
;  Code auto-modifié : l'octet faible des adresses TABC/TABA reçoit v.
; =====================================================================
BARRE   psha
        jsr  ATTEND
        pula
        staa R6
        clr  R7
        ldaa #B_GP0
        staa R2
        ldaa #C_KRF
        staa R0
        ldaa #40
        staa BCPT
BA1     ldab BV
        stab BA2+2
        stab BA3+2
        addb BDV
        stab BV
BA2     ldaa TABC            ; code de la tuile (adresse modifiée)
BA3     ldab TABA            ; attribut (adresse modifiée)
BA4     tst  R0
        bmi  BA4
        staa R1
        stab XR3             ; KRF
        dec  BCPT
        bne  BA1
        rts

; =====================================================================
;  Clavier en lecture directe : ESPACE (colonne 7, ligne 3) et ENTRÉE
;  (colonne 6, ligne 3). Retourne A = 1 (ESPACE), 2 (ENTRÉE) ou 0, une
;  seule fois par appui, après 3 lectures identiques (anti-rebond).
; =====================================================================
LITCLAV clrb
        ldaa #$7F
        staa PORT1
        ldaa CLASON
        anda #$08
        bne  LC1
        orab #1
LC1     ldaa #$BF
        staa PORT1
        ldaa CLASON
        anda #$08
        bne  LC2
        orab #2
LC2     tstb
        beq  LCREL
        cmpb KDER
        bne  LCNOUV
        ldaa KCPT
        cmpa #4
        bhs  LCRIEN          ; appui déjà signalé
        inca
        staa KCPT
        cmpa #3
        bne  LCRIEN
        tba
        rts
LCNOUV  stab KDER
        clr  KCPT
        bra  LCRIEN
LCREL   clr  KDER
        clr  KCPT
LCRIEN  clra
        rts

; =====================================================================
;  À appeler une fois par image : ENTRÉE quitte la démo ;
;  retourne Z = 0 si ESPACE (partie suivante).
; =====================================================================
CONTROLE
        jsr  LITCLAV
        bita #2
        beq  CT1
        jmp  QUITTE
CT1     anda #1
        rts

; =====================================================================
;  Démarrage commun : à appeler par JMP depuis le point d'entrée
;  (la pile du BASIC est mémorisée pour le retour).
; =====================================================================
DEMARRE sts  SAVESP
        tpa
        staa SAVECC
        sei
        jsr  INITECRAN
        jsr  INITPAL
        jsr  HORLOGE
        jmp  PRINCIPAL

; =====================================================================
;  Retour au BASIC : coupe les interruptions, restaure l'écran et la pile
; =====================================================================
QUITTE  sei
        clra
        staa TCSR            ; plus d'interruptions du timer
        ldaa #$3B            ; RTI dans les trampolines
        staa VEC_TOF
        staa VEC_OCF
        clra
        staa CLASON          ; haut-parleur au repos
        jsr  INITECRAN
        lds  SAVESP
        ldaa SAVECC
        tap
        rts

; =====================================================================
;  Horloge : interruption TOF toutes les 65,536 ms -> TICKS + 1
;  (+ musique si AVEC_MUSIQUE). Voir docs/03 et 05 §4.
; =====================================================================
HORLOGE sei
        ldaa #$7E            ; JMP
        staa VEC_TOF
        ldx  #IT_TOF
        stx  VEC_TOF+1
        ldaa TCSR            ; acquitter TOF : lire TCSR puis le compteur
        ldaa TCNT
        IF AVEC_MUSIQUE
        jsr  MUS_INIT
        ldaa #$0C            ; ETOI + EOCI
        ELSE
        ldaa #$04            ; ETOI
        ENDIF
        staa TCSR
        cli
        rts

IT_TOF  ldaa TCSR
        ldaa TCNT            ; acquitte TOF
        ldx  TICKS
        inx
        stx  TICKS
        IF AVEC_MUSIQUE
        jsr  MUS_TICK
        ENDIF
        rti

; --- données et variables communes ------------------------------------
TRAMES  dc.b $00,$00,$00,$00,$00,$00,$00,$00,$00,$00   ; 0 %
        dc.b $11,$44,$11,$44,$11,$44,$11,$44,$11,$44   ; 25 %
        dc.b $55,$AA,$55,$AA,$55,$AA,$55,$AA,$55,$AA   ; 50 %
        dc.b $EE,$BB,$EE,$BB,$EE,$BB,$EE,$BB,$EE,$BB   ; 75 %
; suite cyclique de 16 couleurs (B V R) + la première répétée
SEQCOUL dc.b 0,4,6,7,6,4,0,1,3,7,3,1,0,5,7,5,0

SAVESP  dc.w 0
SAVECC  dc.b 0
TICKS   dc.w 0
TMPW    dc.w 0
TMPC    dc.b 0
TXY     dc.b 0
DC_R4   dc.b 0
DC_R5   dc.b 0
OS_N    dc.b 0
BV      dc.b 0
BDV     dc.b 0
BCPT    dc.b 0
KDER    dc.b 2               ; au lancement ENTRÉE est encore enfoncée :
KCPT    dc.b 4               ; on attend qu'elle soit relâchée
