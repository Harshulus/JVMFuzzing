import struct

class CodeAttr:
    def __init__(self):
        pass

    def from_reader(self, r):
        self.max_stack = struct.unpack('!H', r.read(2))[0]
        self.max_locals = struct.unpack('!H', r.read(2))[0]
        self.code_len = struct.unpack('!I', r.read(4))[0]
        self.code = r.read(self.code_len)

        return self
    
    def __str__(self) -> str:
        x = str(self.max_stack) + "\n" + str(self.max_locals) + "\n" + str(self.code_len) + "\n" + str(self.code) + "\n"
        return x