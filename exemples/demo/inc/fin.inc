; =====================================================================
;  fin.inc : table de sinus alignée et zones de travail (non chargées)
;  À inclure en DERNIER. Exemple ORIGINAL du dépôt alice32-tech-ref.
; =====================================================================
        ALIGN 256
        INCLUDE "inc/donnees-sinus.inc"
FINPROG                      ; fin du binaire chargé

; --- zones de travail après le programme (rien n'est chargé ici) ---------
TABC    EQU [FINPROG+255]&$FF00   ; palette : codes des tuiles (alignée)
TABA    EQU TABC+256              ; palette : attributs (alignée)
LBUF    EQU TABA+256              ; 80 octets : une rangée du logo
AXB     EQU LBUF+80               ; 48 octets : plasma, AX[x]
RBV     EQU AXB+48                ; 48 octets : plasma, BY[y] puis décalages
LTB     EQU RBV+48                ; 40 octets : tuiles décalées du logo
SLIG    EQU LTB+40                ; 7 x S_N octets : lignes du scrolltext
        IFCONST S_N
FINRAM  EQU SLIG+7*S_N
        ELSE
FINRAM  EQU SLIG
        ENDIF

        ECHO "Binaire : $3400 -", FINPROG, " ; RAM utilisée jusqu'à", FINRAM
        IF FINRAM > $4E00
        ECHO "ERREUR : le programme déborde sur la pile du système ($4E00)"
        ERR
        ENDIF
