#!/bin/bash
BASE_PATH=/home/android-build-linaro/android/.tmp
TARGET_PATH=/srv3/snapshots.linaro.org/www/android/

# Expected argument: username_jobname/buildno
build_path="$1"

if [[ -n $2 ]]; then
    BASE_PATH=$2
fi

if [[ -n $3 ]]; then
    TARGET_PATH=$3
fi

if [ -z "$build_path" ]; then
    echo "Missing build path"
    exit 1;
fi

# Paranoid security - alarm on 2 dots separated only by 0 or more backslahes
if echo "$build_path" | grep -q -E '\.\\*\.'; then
    echo "No double-dots in build names please"
    exit 1
fi

if [ ! -d $BASE_PATH/$build_path ]; then
    echo "WARNING: Expected directory $BASE_PATH/$build_path does not exist"
    exit 0
fi

job_dir=$(dirname $build_path)
build_number=$(basename $build_path)
username=`echo "$job_dir" | cut -d_ -f1`
jobname=`echo "$job_dir" | cut -d_ -f2-`

echo -n "Moving $BASE_PATH/$build_path to $TARGET_PATH/~$username/$jobname/... " &&
(mkdir -p "$TARGET_PATH/~$username/$jobname" && \
     cp -a $BASE_PATH/"$build_path" "$TARGET_PATH/~$username/$jobname/" && \
     rm -rf $BASE_PATH/"$build_path" && \
     echo "done")

cd "$TARGET_PATH/~$username/$jobname/$build_number" && find * -xtype f > MANIFEST
