#!/bin/sh

TARG=llp-tag-expires

rm -f $TARG/lambda.zip
(cd $TARG && pipenv run lambpy -r requirements.txt)
