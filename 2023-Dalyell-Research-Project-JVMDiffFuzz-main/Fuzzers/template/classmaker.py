import random
import string

def name_finder(i):
    name = " "
    j = i
    name += lower[j  % 26]
    j //= 26

    while j > 0:
        name += lower[j % 26]
        j //= 26
    
    return name

f = open("test.java", "w")
f.write("public class test{\n")

values = ["int", "double", "float", "char", "int[]", "float[]", "double[]", "char", "String", "String[]"]
lower = list(string.ascii_lowercase)

key_words = [" if", " do", " for"]

#Write locals
constant = 0
for i in range(8000):
    var = "\tpublic "
    if i % 5 == 0:
        var += "static "
    
    var += values[random.randrange(0, 9)]
    #Need var names

    name = name_finder(i + constant)
    while name in key_words:
        constant += 1
        name = name_finder(i + constant)
    var += name

    var += ";\n"
    f.write(var)


#Write static methods

for i in range(500):
    blah = "public static void test" + str(i) + "(){return;}\n"
    f.write(blah)

f.write("\tpublic static void main(String[] args){")
constant = 0
for i in range(8000):
    # var = "\t\tpublic "
    # if i % 5 == 0:
    #     var += "static "
    var = "\t\t"
    
    var += values[random.randrange(0, 9)]
    #Need var names

    name = name_finder(i + constant)
    while name in key_words:
        constant += 1
        name = name_finder(i + constant)
    var += name

    var += ";\n"
    f.write(var)
        

f.write("\t}\n")
f.write("}\n")

