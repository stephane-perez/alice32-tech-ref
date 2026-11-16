; =====================================================================
;  musique-plus.inc : son enrichi par les interruptions du timer
;  Exemple ORIGINAL du dépôt alice32-tech-ref (syntaxe DASM, 6803).
;  Données : MELODIE (donnees-musique.inc), PER2 (donnees-periodes2.inc).
;
;  Comme les « effets timer » de l'Atari ST, sans charger le processeur :
;  - l'interruption OCF alterne DEUX durées (haut / bas) : rapport
;    cyclique variable, donc timbre variable ;
;  - M2_IMAGE, appelée à chaque image (50 Hz) par la boucle principale,
;    fait avancer la mélodie et applique les effets choisis par M2_MODE :
;      bit 0 : PWM (balayage du rapport cyclique de 50 % à 12 %),
;      bit 1 : vibrato (+/- 1,6 %),
;      bit 2 : arpège (note, quinte, octave : un « accord » à 16,7 Hz).
;  Le programme principal installe d'abord l'horloge (commun.inc).
;  Statut : [C] non testé sur machine réelle.
; =====================================================================

M2_MIN  EQU 100              ; durée minimale d'une alternance (µs)

M2_INIT sei
        ldaa #$7E
        staa VEC_OCF
        ldx  #IT_OCF2
        stx  VEC_OCF+1
        ldx  #MELODIE
        stx  M2_PTR
        ldaa #1
        staa M2_DUR
        clr  M2_MASQ
        clr  M2_SON
        ldaa #128
        staa M2_DUTY
        ldd  #1000
        std  M2_H
        std  M2_B
        ldaa TCSR
        ldd  TCNT
        addd #200
        std  OCR
        ldaa #$0C            ; ETOI (horloge) + EOCI (son)
        staa TCSR
        cli
        rts

; --- interruption OCF : inverser la sortie, durée selon le niveau -------
IT_OCF2 ldaa TCSR            ; acquittement 1/2
        ldaa M2_SON
        eora M2_MASQ
        staa M2_SON
        staa CLASON
        bmi  IO2H
        ldd  OCR             ; on vient de passer en bas
        addd M2_B
        std  OCR             ; acquittement 2/2
        rti
IO2H    ldd  OCR             ; on vient de passer en haut
        addd M2_H
        std  OCR
        rti

; --- à appeler une fois par image -------------------------------------
M2_IMAGE
        inc  M2_FR
        dec  M2_DUR
        bne  M2E
        ldx  M2_PTR          ; note suivante
        ldaa 0,x
        cmpa #$FF
        bne  M2N1
        ldx  #MELODIE
        ldaa 0,x
M2N1    ldab 1,x             ; durée : pas de 65,5 ms -> x 3 images
        stab M2_DUR
        aslb
        addb M2_DUR
        stab M2_DUR
        inx
        inx
        stx  M2_PTR
        staa M2_NOTE
        clr  M2_MASQ
        tsta
        beq  M2E
        ldaa #$80
        staa M2_MASQ
M2E     ldaa M2_NOTE
        bne  M2E0
        rts                  ; silence
; arpège : + 0, 7, 12 demi-tons selon l'image
M2E0    ldab M2_MODE
        andb #4
        beq  M2E2
        ldab M2_FR
M2E1    cmpb #3
        blo  M2E1B
        subb #3
        bra  M2E1
M2E1B   ldx  #M2_ARP
        abx
        adda 0,x
M2E2    deca                 ; période = PER2[note - 1]
        asla
        tab
        ldx  #PER2
        abx
        ldd  0,x
        std  M2_P
; vibrato : P += k x (P / 128), k = -2..2
        ldab M2_MODE
        andb #2
        beq  M2E4
        ldab M2_FR
        lsrb
        andb #7
        ldx  #M2_VIB
        abx
        ldab 0,x
        stab M2_K
        ldd  M2_P
        lsrd
        lsrd
        lsrd
        lsrd
        lsrd
        lsrd
        lsrd                 ; D = P / 128
        std  M2_D
M2E3    tst  M2_K
        beq  M2E4
        bmi  M2E3N
        ldd  M2_P
        addd M2_D
        std  M2_P
        dec  M2_K
        bra  M2E3
M2E3N   ldd  M2_P
        subd M2_D
        std  M2_P
        inc  M2_K
        bra  M2E3
; PWM : rapport cyclique en triangle 128 -> 32 -> 128
M2E4    ldab M2_MODE
        andb #1
        bne  M2E5
        ldaa #128
        staa M2_DUTY
        bra  M2E7
M2E5    ldaa M2_DUTY
        tst  M2_DDIR
        bne  M2E6
        suba #3
        staa M2_DUTY
        cmpa #32
        bhi  M2E7
        inc  M2_DDIR
        bra  M2E7
M2E6    adda #3
        staa M2_DUTY
        cmpa #128
        blo  M2E7
        clr  M2_DDIR
; H = P x rapport / 256 ; B = P - H (au moins M2_MIN chacun)
M2E7    ldaa M2_P+1
        ldab M2_DUTY
        mul
        staa M2_D            ; (octet faible x rapport) / 256
        ldaa M2_P
        ldab M2_DUTY
        mul
        addb M2_D
        adca #0              ; D = H
        subd #M2_MIN
        bcc  M2E8
        ldd  #0
M2E8    addd #M2_MIN
        std  M2_D            ; H
        ldd  M2_P
        subd M2_D
        subd #M2_MIN
        bcc  M2E9
        ldd  #0
M2E9    addd #M2_MIN         ; B
        sei                  ; les deux valeurs ensemble
        std  M2_B
        ldd  M2_D
        std  M2_H
        cli
        rts

M2_ARP  dc.b 0,7,12
M2_VIB  dc.b 0,1,2,1,0,-1,-2,-1
M2_PTR  dc.w 0
M2_P    dc.w 0
M2_D    dc.w 0
M2_H    dc.w 0
M2_B    dc.w 0
M2_DUR  dc.b 0
M2_NOTE dc.b 0
M2_MASQ dc.b 0
M2_SON  dc.b 0
M2_DUTY dc.b 0
M2_DDIR dc.b 0
M2_FR   dc.b 0
M2_K    dc.b 0
M2_MODE dc.b 0
