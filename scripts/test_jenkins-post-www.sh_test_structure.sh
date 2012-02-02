#/bin/env bash

# Test MANIFEST creation for jenkins-post-www.sh

root=`mktemp -d`

mkdir -p $root/from/user_build/1/subdir/anotherdir/yetanotherdir
touch $root/from/user_build/1/file1
touch $root/from/user_build/1/file2
touch $root/from/user_build/1/file3
touch $root/from/user_build/1/subdir/subfile1
touch $root/from/user_build/1/subdir/subfile2
touch $root/from/user_build/1/subdir/subfile3

mkdir -p $root/from/user_build/2/subdir/anotherdir/yetanotherdir
touch $root/from/user_build/2/file1
touch $root/from/user_build/2/file2
touch $root/from/user_build/2/file3
touch $root/from/user_build/2/subdir/subfile1
touch $root/from/user_build/2/subdir/subfile2
touch $root/from/user_build/2/subdir/subfile3

mkdir -p $root/to

./jenkins-post-www.sh user_build/1 $root/from $root/to

# MANIFEST should list all files, but no directories, in $root/from/user_build/1

cat > $root/expected << EOF
file1
file2
file3
subdir/subfile3
subdir/subfile2
subdir/subfile1
EOF

diff $root/expected $root/to/~user/build/1/MANIFEST
if [[ $? == 0 ]]; then
    echo "Passed"
else
    echo "Failed"
fi

rm -r $root
