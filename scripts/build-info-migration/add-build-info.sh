#!/bin/sh
#
# This script adds BUILD-INFO.txt for each build which lacks it.
# Algo is:
# Each build of each job is scanned. If particular build lacks BUILD-INFO.txt,
# then latest build of that job looked up for BUILD-INFO.txt, and used as a template
# if present. If not present, designated file is used as default BUILD-INFO.txt
# template. Template file is copied into build's directory.
#

# has "OpenID-Launchpad-Teams: linaro-android-restricted"
DEFAULT_TEMPLATE="/srv/snapshots.linaro.org/www/android/~linaro-android-restricted/juice-linaro/100/BUILD-INFO.txt"

for job in /srv/snapshots.linaro.org/www/android/~linaro-android-restricted/*; do
    templ="$job/lastSuccessful/BUILD-INFO.txt"
    if [ ! -f "$templ" ]; then
        templ=$DEFAULT_TEMPLATE
    fi

    for build in $job/*; do
        if [ ! -f "$build/BUILD-INFO.txt" ]; then
            cp $templ $build/
        fi
    done
done
