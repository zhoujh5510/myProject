#!/bin/bash
if [ ! -e translator/trans ]; then
  cd translator && make
  cd ..
fi
for i in *.isc; do 
  cat $i | translator/trans > ${i%.isc}.sisc
done
