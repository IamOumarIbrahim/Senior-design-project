#!/usr/bin/env bash
#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

# builds the blind check library, run this on the machine that will use it
# without the library preprocessor.py uses opencv and gives the same answer
set -e
cd "$(dirname "$0")"
if [ "$OS" = "Windows_NT" ]; then
    g++ -O3 -march=native -shared -static -o blind_check.dll blind_check.cpp
else
    g++ -O3 -march=native -shared -fPIC -o blind_check.so blind_check.cpp
fi
echo "built blind check"
