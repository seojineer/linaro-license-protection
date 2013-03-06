#!/bin/sh
#
# This script validates that each build of each job has BUILD-INFO.txt present
#

for job in /srv/snapshots.linaro.org/www/android/~linaro-android-restricted/*; do
    for build in $job/*; do
        if [ ! -f "$build/BUILD-INFO.txt" ]; then
            echo "ERROR: $build lacks BUILD-INFO.txt"
        fi
    done
done
