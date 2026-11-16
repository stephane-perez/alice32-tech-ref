; =====================================================================
;  ymplay.inc : joue une musique YM (Atari ST, YM2149) convertie par
;  outils/ym2alice.py, sur le haut-parleur 1 bit de l'Alice 32.
;  Exemple ORIGINAL du dépôt alice32-tech-ref (syntaxe DASM, 6803).
;  Données : inc/donnees-ym.inc (YM_TABF, YM_FLUX, YM_TPF, YM_TITRE...).
;
;  Trois voix + bruit, processeur à 100 % (interruptions masquées) :
;  - voix : accumulateur de phase 16 bits ; impulsion tant que l'octet
;    haut de la phase est sous le « rapport cyclique », qui suit le
;    VOLUME de la voie YM (impulsions étroites : les voix se masquent peu) ;
;  - bruit : registre à décalage 16 bits ; une voie dont le bruit est
;    activé dans le mixeur du YM est « hachée » par ce bruit ;
;  - mélange : OU logique sur le bit 7 de $BFFF.
;  Un tic = 122 cycles (8 197 tics/s) ; une trame YM = YM_TPF tics.
;  Fréquences, rapports cycliques et routage du bruit sont écrits dans
;  les instructions (code auto-modifié) à chaque trame.
;  Flux : un octet M par trame :
;    M = $80 + N (N >= 1) : N trames sans changement ;
;    M = $80 : fin, suivi de l'adresse de reprise (boucle) ;
;    sinon M = masque : bit 0-2 : indice de fréquence des voix 1-3,
;      bit 3 : octet volumes 1 (quartet haut) et 2 (quartet bas),
;      bit 4 : octet volume 3 (quartet haut) + bruit voies 1-3 (bits 0-2) ;
;    suivis des octets indiqués, dans cet ordre.
;  Statut : [C] non testé sur machine réelle.
; =====================================================================

; --- jouer ; retour A = 1 (ESPACE) ou 2 (ENTRÉE) --------------------------
YM_JOUE tpa
        staa YM_CC
        sei
        ldx  #YM_FLUX
        stx  YM_PTR
        clr  YM_REP
        ldd  #$ACE1
        std  YM_LF
YMF     jsr  YM_TRAME
        jsr  LITCLAV
        tsta
        bne  YMFIN
        ldaa #YM_TPF
        staa YM_CNT
; --- un tic : 122 cycles ------------------------------------------------
YMT     ldd  YM_P1           ; 5   voix 1
YA1     addd #0              ; 4   (incrément modifié)
        std  YM_P1           ; 5
YC1     cmpa #0              ; 2   (rapport cyclique modifié)
        ldab #0              ; 2
        rorb                 ; 2   C -> bit 7
YN1     andb YM_UN           ; 4   (adresse modifiée : YM_UN ou YM_LF)
        stab YM_O            ; 4
        ldd  YM_P2           ;     voix 2
YA2     addd #0
        std  YM_P2
YC2     cmpa #0
        ldab #0
        rorb
YN2     andb YM_UN
        orab YM_O            ; 4
        stab YM_O            ; 4
        ldd  YM_P3           ;     voix 3
YA3     addd #0
        std  YM_P3
YC3     cmpa #0
        ldab #0
        rorb
YN3     andb YM_UN
        orab YM_O
        stab CLASON          ; 4   sortie
        ldd  YM_LF           ; 5   bruit : LFSR de Galois 16 bits
        asld                 ; 3
        bcs  YMB1            ; 3
        nop                  ; 2   (même durée dans les deux cas)
        bra  YMB2            ; 3
YMB1    eorb #$2D            ; 2
        brn  YMB2            ; 3
YMB2    std  YM_LF           ; 5
        dec  YM_CNT          ; 6
        bne  YMT             ; 3
        jmp  YMF
YMFIN   psha
        clra
        staa CLASON
        ldaa YM_CC
        tap
        pula
        rts

; --- lire la trame suivante du flux ---------------------------------------
YM_TRAME
        tst  YM_REP
        beq  YT1
        dec  YM_REP          ; trame inchangée
        rts
YT1     ldx  YM_PTR
        ldaa 0,x
        inx
        tsta
        bpl  YT3
        anda #$7F
        bne  YT2
        ldx  0,x             ; fin : reprise à l'adresse qui suit
        stx  YM_PTR
        bra  YT1
YT2     deca                 ; N trames inchangées, dont celle-ci
        staa YM_REP
        stx  YM_PTR
        rts
YT3     staa YM_M
        lsr  YM_M            ; bit 0 : fréquence voix 1
        bcc  YT4
        ldab 0,x
        inx
        jsr  YM_FREQ
        std  YA1+1
YT4     lsr  YM_M            ; bit 1 : voix 2
        bcc  YT5
        ldab 0,x
        inx
        jsr  YM_FREQ
        std  YA2+1
YT5     lsr  YM_M            ; bit 2 : voix 3
        bcc  YT6
        ldab 0,x
        inx
        jsr  YM_FREQ
        std  YA3+1
YT6     lsr  YM_M            ; bit 3 : volumes 1 et 2
        bcc  YT7
        ldab 0,x
        inx
        pshb
        lsrb
        lsrb
        lsrb
        lsrb
        jsr  YM_DUTY
        stab YC1+1
        pulb
        andb #$0F
        jsr  YM_DUTY
        stab YC2+1
YT7     lsr  YM_M            ; bit 4 : volume 3 et bruit
        bcc  YT9
        ldab 0,x
        inx
        pshb
        lsrb
        lsrb
        lsrb
        lsrb
        jsr  YM_DUTY
        stab YC3+1
        pulb
        stx  YM_PTR
        ldx  #YM_UN          ; bruit voie 1 ?
        lsrb
        bcc  YT8A
        ldx  #YM_LF
YT8A    stx  YN1+1
        ldx  #YM_UN
        lsrb
        bcc  YT8B
        ldx  #YM_LF
YT8B    stx  YN2+1
        ldx  #YM_UN
        lsrb
        bcc  YT8C
        ldx  #YM_LF
YT8C    stx  YN3+1
        rts
YT9     stx  YM_PTR
        rts

; --- B = indice -> D = incrément de phase (X conservé) ----------------------
YM_FREQ pshx
        ldx  #YM_TABF
        abx
        abx
        ldd  0,x
        pulx
        rts

; --- B = volume 0-15 -> B = rapport cyclique (X conservé) ------------------
YM_DUTY pshx
        ldx  #YM_RC
        abx
        ldab 0,x
        pulx
        rts

; rapport cyclique (sur 256) selon le volume YM : ~3 dB par pas, 40 au maximum
YM_RC   dc.b 0,1,1,1,1,2,2,3,4,6,8,11,16,22,28,40

YM_P1   dc.w 0
YM_P2   dc.w 0
YM_P3   dc.w 0
YM_LF   dc.w 0               ; registre du bruit (bit 7 de l'octet haut)
YM_PTR  dc.w 0
YM_UN   dc.b $FF             ; « pas de bruit » : masque neutre
YM_O    dc.b 0
YM_CNT  dc.b 0
YM_REP  dc.b 0
YM_M    dc.b 0
YM_CC   dc.b 0
