#!/bin/sh

#Compiling the classfile
cd ../template
python classmaker.py
rm *.class
javac -g:none *.java
cp test.class ../PYJVMFuzzers
cd ../PYJVMFuzzers

python3 fuzzer.py
