#!/bin/bash

THIS_DIR="$(pwd)"

WORK_DIR=`mktemp -d -p "$THIS_DIR"`

function cleanup {      
  rm -rf "$WORK_DIR"
  echo "Deleted temp working directory $WORK_DIR"
}

trap cleanup EXIT

find "$THIS_DIR" -type f -iname "*.cue" | while read f; do chdman5 createcd -i "$f" -o "${f%.*}.chd"; done
find "$THIS_DIR" -type f -iname "*.gdi" | while read f; do chdman5 createcd -i "$f" -o "${f%.*}.chd"; done
find "$THIS_DIR" -type f -iname "*.iso" | while read f; do chdman5 createcd -i "$f" -o "${f%.*}.chd"; done

find "$THIS_DIR" -type f -iname "*.chd" | while read f; do mv "$f" "$THIS_DIR"; done