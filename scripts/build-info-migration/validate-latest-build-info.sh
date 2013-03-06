#!/bin/sh
#
# This script validates that latest build of each job has BUILD-INFO.txt present
#

for job in /srv/snapshots.linaro.org/www/android/~linaro-android-restricted/*; do
    bi="$job/lastSuccessful"
    if [ ! -f "$bi/BUILD-INFO.txt" ]; then
        real=$(readlink $bi)
        echo "ERROR: $bi ($real) lacks BUILD-INFO.txt"
        ls -ld $real
    fi
done
