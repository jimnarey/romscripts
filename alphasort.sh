#!/bin/bash

LETTERS=("A" "B" "C" "D" "E" "F" "G" "H" "I" "J" "K" "L" "M" "N" "O" "P" "Q" "R" "S" "T" "U" "V" "W" "X" "Y" "Z")

for LETTER in "${LETTERS[@]}"
do
	mkdir $LETTER
	find . -maxdepth 1 -type f -iname "$LETTER*" -execdir mv {} ./$LETTER \;

done

mkdir 0
find . -maxdepth 1 -type f -execdir mv {} ./0 \;
