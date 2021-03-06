#!/bin/bash

# the directory of the script
# SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

THIS_DIR="$(pwd)"

# the temp directory used, within $DIR
# omit the -p parameter to create a temporal directory in the default location
WORK_DIR=`mktemp -d -p "$THIS_DIR"`

# check if tmp dir was created
if [[ ! "$WORK_DIR" || ! -d "$WORK_DIR" ]]; then
  echo "Could not create temp dir"
  exit 1
fi

# deletes the temp directory
function cleanup {      
  rm -rf "$WORK_DIR"
  echo "Deleted temp working directory $WORK_DIR"
}

# register the cleanup function to be called on the EXIT signal
trap cleanup EXIT


if [[ $1 =~ "tar.7z"$ ]]; then
    echo Extracting tar.7z archive: $1
    7z x -so "$1" | tar xf - -C "$WORK_DIR"
elif [[ $1 =~ "tar.gz"$ ]]; then
    echo Extracting tar.gz archive: $1
    tar -xvf "$1" -C "$WORK_DIR"
elif [[ $1 =~ "7z"$ ]]; then
    echo Extracting 7z archive: $1
    7z x -y "$1" -o"$WORK_DIR"
elif [[ $1 =~ "zip"$ ]]; then
    echo Extracting zip archive: $1
    unzip "$1" -d "$WORK_DIR"
else
    echo "$1 is not a supported archive"
    exit 1
fi

find "$WORK_DIR" -type f -iname "*.cue" | while read f; do chdman5 createcd -i "$f" -o "${f%.*}.chd"; done
find "$WORK_DIR" -type f -iname "*.gdi" | while read f; do chdman5 createcd -i "$f" -o "${f%.*}.chd"; done
find "$WORK_DIR" -type f -iname "*.iso" | while read f; do chdman5 createcd -i "$f" -o "${f%.*}.chd"; done

find "$WORK_DIR" -type f -iname "*.chd" | while read f; do mv "$f" "$THIS_DIR"; done
