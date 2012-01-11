#!/bin/sh
BASE_PATH=/home/android-build-linaro/android/.tmp
TARGET_PATH=/srv3/snapshots.linaro.org/www/android/

# Expected argument: ~username_jobname/buildno
build_path="$1"

if [ -z "$build_path" ]; then
    echo "Missing build path"
    exit 1;
fi

# Paranoid security
if echo "$build_path" | grep -q "\."; then
    echo "No dots in build names please"
    exit 1
fi

if [ -d $BASE_PATH/$build_path ]; then
    job_dir=$(dirname $build_path)
    username=`echo "$job_dir" | cut -d_ -f1`
    jobname=`echo "$job_dir" | cut -d_ -f2-`
    echo -n "Moving $BASE_PATH/$build_path to $TARGET_PATH/~$username/$jobname/... " &&
    (mkdir -p "$TARGET_PATH/~$username/$jobname" && \
     cp -a $BASE_PATH/"$build_path" "$TARGET_PATH/~$username/$jobname/" && \
     rm -rf $BASE_PATH/"$build_path" && \
     echo "done")
fi
