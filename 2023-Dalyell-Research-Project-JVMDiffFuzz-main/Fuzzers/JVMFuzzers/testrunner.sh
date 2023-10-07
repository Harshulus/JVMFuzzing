#!/bin/bash

#Takes one argument: either "amzn", "tem" or "zulu", which determines whether to build the classfiles with the Amazon JVM or the Zulu JVM
#   or the Temurin JVM and test on the other JVMs

# Compiles and builds test classes with the given JVM 

ALLJVMS=("amzn" "zulu" "tem")
JVM=$([ "$1" == "" ] && echo -n "amzn" || echo -n "$1")

source "$HOME/.sdkman/bin/sdkman-init.sh"
sdk use java 20-$JVM

#Compiling the classfile
cd ../template
# python classmaker.py
rm *.class
javac -g:none *.java
cd ../JVMFuzzers

#Making the directory of outputs
mkdir -p output_classes
rm -rf output_classes/*
mkdir -p output_classes/java_output

#Performing the fuzzing
python3 jvmfuzzer.py


#Getting output for the JVM that built the class files
for i in output_classes/test*
do  
    echo $i >> output_classes/java_output/$JVM.txt
    java -cp $i: test >> output_classes/java_output/$JVM.txt 2>&1 
done

for testjvm in ${ALLJVMS[@]}; do 

    if [[ "$JVM" == "$testjvm" ]]
    then 
        continue 
    fi

    sdk use java 20-$testjvm

    #Getting output for the test JVM
    for i in output_classes/test*
    do
        echo $i >> output_classes/java_output/$testjvm.txt
        java -cp $i: test >> output_classes/java_output/$testjvm.txt 2>&1 
    done

    #Testing that output is the same
    DIFF=$(diff output_classes/java_output/$JVM.txt output_classes/java_output/$testjvm.txt)

    if [[ "$DIFF" != "" ]]; then
        echo "The JVMS $JVM and $testjvm differ"
    else
        echo "-------------------------------------"
        echo ""
        echo "The JVMS $JVM and $testjvm produced the same output"
        echo ""
        echo "-------------------------------------"
    fi


done

#Testing Coverage
for i in output_classes/test*
do 
    javap -c $i/test.class > $i/disassembled.txt
    python3 getinsts.py $i
done 

echo "-------------------------------------"
python3 jvmcov.py
