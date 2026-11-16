; =====================================================================
;  sample.inc : jouer un son échantillonné sur le haut-parleur 1 bit
;  Exemple ORIGINAL du dépôt alice32-tech-ref (syntaxe DASM, 6803).
;  Données : outils/wav2sample.py (SAMPLE, SAMPLE_FIN, SM_N).
;
;  Modulation sigma-delta du premier ordre : à chaque tic (12 cycles),
;  A += échantillon x 16 ; la RETENUE de l'addition va directement au
;  bit 7 de $BFFF. La proportion de 1 en sortie vaut échantillon / 16 :
;  16 niveaux sur un seul bit, à ~83 kHz (inaudible), que le haut-parleur
;  et l'oreille moyennent. SM_N tics par échantillon : 4 717 Hz pour 16.
;  Le processeur est pris à 100 %, interruptions masquées.
;  Statut : [C] non testé sur machine réelle (réponse du haut-parleur
;  et de son étage de sortie inconnue).
; =====================================================================

JOUE_SAMPLE
        tpa
        staa SM_CC
        sei                  ; pas d'interruption : le rythme doit être régulier
        ldx  #SAMPLE
        clra                 ; accumulateur
SMB     ldab 0,x             ; échantillon pair : quartet haut, déjà x 16
        andb #$F0
        stab SMV
        REPEAT SM_N
        adda SMV             ; 4  retenue = bit de sortie
        ldab #0              ; 2  (ne touche pas à C)
        rorb                 ; 2  C -> bit 7
        stab CLASON          ; 4
        REPEND
        ldab 0,x             ; échantillon impair : quartet bas x 16
        aslb
        aslb
        aslb
        aslb
        stab SMV
        REPEAT SM_N
        adda SMV
        ldab #0
        rorb
        stab CLASON
        REPEND
        inx
        cpx  #SAMPLE_FIN
        beq  SMF
        jmp  SMB
SMF     clra
        staa CLASON          ; haut-parleur au repos
        ldaa SM_CC
        tap
        rts

SMV     dc.b 0
SM_CC   dc.b 0
