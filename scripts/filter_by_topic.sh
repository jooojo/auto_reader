#!/bin/bash

topic=${1}
conf=${2}

data="./data/${conf}.tsv"
./auto_read.py "Is this passage about $topic" ${data} tmp
paste <(cat tmp | tr A-Z a-z) ${data} | awk '$1=="yes"' | cut -f2- > output/"${conf}_${topic}.tsv"
rm tmp
