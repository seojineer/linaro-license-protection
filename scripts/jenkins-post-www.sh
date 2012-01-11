#!/bin/sh
BASE_PATH=/home/android-build-linaro/android/.tmp
TARGET_PATH=/srv3/snapshots.linaro.org/www/android/
for dir in `ls $BASE_PATH`; do
  if [ -d $BASE_PATH/$dir ]; then
    username=`echo "$dir" | cut -d_ -f1`
    buildname=`echo "$dir" | cut -d_ -f2-`
    echo -n "Moving $BASE_PATH/$dir to $TARGET_PATH/~$username/$buildname... " &&
    (mkdir -p "$TARGET_PATH/~$username/$buildname" && \
     cp -a $BASE_PATH/"$dir"/* "$TARGET_PATH/~$username/$buildname/" && \
     rm -rf $BASE_PATH/"$dir" && \
     echo "done")
  fi
done
