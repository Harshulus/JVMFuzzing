# 2023-Dalyell-Research-Project-JVMDiffFuzz

## Fuzzers

3 sections:

### JVM Fuzzers
Contains all the code to run the fuzzer on three JVMs (Amazon 20, Temurin 20 and Zulu 20), and should be easily modifiable to 
accodomate more JVMs. Simply run the file `testrunner.sh` and provide it the arugment either `amzn`, `zulu` or `tem` in order 
to specify which of the JVMs to build the classfiles. The fuzzer then tests the outputted classfiles on all the JVMs and collects 
the coverage of each of the classfiles to find the coverage of the fuzzer. Can be run with debug information, backtracking and 
other customisable parameters such as how long to make the class files, how many and how many errors before backtracking.
Some of the components of the toy PYJVM are used in order to parse the java classfile. 

### PYJVM Fuzzers
Contains the fuzzer for the toy python JVM. Simply run `pyrun.sh` in order to test it. 

### Template
Contains the template class file (and the code that creates it) which is used to build the random classfiles for our fuzzer. 
