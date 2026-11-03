#!/bin/sh
# Construit tous les programmes de la démo : données, binaires, cassettes .k7.
# Exemple ORIGINAL du dépôt alice32-tech-ref.
# Utilise DASM s'il est installé, sinon l'assembleur Python fourni.
# Option : ./construire.sh wav   (fabrique aussi les .wav, ~1 Mo chacun)
set -e
cd "$(dirname "$0")"
mkdir -p build
python3 outils/gen_donnees.py
for p in demo demo2-plasma-scroll demo3-vectoriel test1-logo test2-plasma test3-scroll test3b-scroll-simple test4-musique; do
    if command -v dasm >/dev/null 2>&1; then
        dasm "$p.asm" -f3 -o"build/$p.bin" -l"build/$p.lst" -s"build/$p.sym"
    else
        python3 outils/asm6803.py "$p.asm" -o "build/$p.bin" -l "build/$p.lst" -s "build/$p.sym"
    fi
    nom=$(echo "$p" | cut -c1-8 | tr 'a-z-' 'A-Z_')
    if [ "$1" = "wav" ]; then
        python3 outils/bin2k7.py "build/$p.bin" "$nom" --wav "build/$p.wav"
    else
        python3 outils/bin2k7.py "build/$p.bin" "$nom"
    fi
done
