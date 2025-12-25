#!/bin/bash
set -e # Close on error

cd ~/Documents/Code/kicad-reveng

source config_remote_build.sh

CHANGED_FILES=`git status --porcelain | cut -d ' ' -f 3`

# Upload files
for f in $CHANGED_FILES; do

    sum_remote=`ssh "$SERVER" "cksum ~/kicad-reveng/$f | cut -d ' ' -f 1"`
    sum_local=`cksum $f | cut -d ' ' -f 1`

    if [[ "$sum_remote" == "$sum_local" ]]; then
        echo "File unchanged: $f"
    else
        rsync -vzh --info=progress2 "$f" "$SERVER:/home/max/kicad-reveng/$f"
    fi
done

# Build
ssh "$SERVER" "cd ~/kicad-reveng/build && make -j32"

# Check whether something has changed
echo "Copying build results..."
count=0
for remote_f in "${BUILD_RESULTS_REMOTE[@]}"; do

    local_f="${BUILD_RESULTS_LOCAL[$count]}"

    sum_remote=`ssh "$SERVER" "cksum ~/kicad-reveng/$remote_f | cut -d ' ' -f 1"`
    sum_local=`cksum $local_f | cut -d ' ' -f 1`

    if [[ "$sum_remote" == "$sum_local" ]]; then
        echo "File unchanged: $remote_f"
    else
        rsync -vzh --info=progress2 "$SERVER:/home/max/kicad-reveng/$remote_f" "$local_f"
    fi

    count=$((count + 1))
done
