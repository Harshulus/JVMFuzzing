import subprocess
import random
import struct
from pyjvm.CPInfo import CPInfo, CPTag
from pyjvm.FieldInfo import FieldInfo
from pyjvm.AttributeInfo import AttributeInfo


class Fuzzer:
    def execute_binary(self) -> str:
        """
        Runs a subprocess which invokes the JVM on the input written to the temp file in
        the call to generate()

        No parameters

        Returns one of the following strings: "Complete", "Incomplete", "Incorrect" or "Error",
            indicating whether the sequence was complete, incomplete, incorrect (i.e. invalid instruction) or
            any other type of error (these are both incorrect states but we need some way to differentiate)
        """
        try:
            result = subprocess.run(
                ["python3", "run_unittest.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=2,
            )
        except subprocess.TimeoutExpired:
            return "Error"

        stderr = result.stderr.decode("utf-8")
        print(len(result.stdout.decode("utf-8").split("\n")))
        print(result.stdout.decode("utf-8"))

        if len(stderr) != 0:
            err = stderr.strip().split("\n")[-1]
            print(err)

            if err == "pyjvm.Machine.Incomplete":
                return "Incomplete"
            elif err == "pyjvm.Machine.Incorrect":
                return "Incorrect"
            else:
                return "Error"

        # no exceptions
        return "Complete"

    def generate(
        self,
        min_len: int,
        max_err: int,
        start: str,
        end: str,
        code_attr_len: int,
        tlv: bool = False,
    ) -> bytes:
        """
        Returns a sequence of complete instructions for the JVM as a byte string.

        Params:
            int min_len :: the minimum length for the sequences
            int max_err :: the maximum times we can attempt adding a new instruction before backtracking
            str start :: the starting prefix for the class file
            str end :: the ending suffix for the class file
            code_attr_len :: the length of the code attribute itself without any code
            bool tlv :: whether to use TLV encoding (default is False)
        """

        if tlv:
            return self.generate_tlv(min_len, max_err, start, end, code_attr_len)

        # Setting max stack to 512 and number of locals to 7
        pre = b"\x20\x00\x00\x07"
        input_data = b""
        err_cnt = 0

        while True:
            num = random.randrange(0, 255)

            # Backtrack
            if err_cnt > max_err:
                input_data = input_data[: -1 * min(2, len(input_data))]
                err_cnt = 0
                continue

            input_data += num.to_bytes(1, byteorder="big")

            # Calculate total length
            total_length = (code_attr_len + len(input_data)).to_bytes(
                4, byteorder="big"
            )

            # Combine all parts
            total = (
                total_length
                + pre
                + len(input_data).to_bytes(4, byteorder="big")
                + input_data
            )

            # Write to a temporary file
            with open("test.class", "wb") as f:
                f.write(start)
                f.write(total)
                f.write(end)

            # Process the result (your existing logic)
            result = self.execute_binary()

            if result == "Complete":
                # Disregard and continue if the sequence is not long enough
                if len(input_data) < min_len:
                    input_data = input_data[:-1]
                    continue
                return input_data

            elif result == "Incorrect" or result == "Error":
                input_data = input_data[:-1]
                err_cnt += 1
                continue

            err_cnt = 0

    def generate_tlv(
        self, min_len: int, max_err: int, start: bytes, end: bytes, code_attr_len: int
    ) -> bytes:
        """
        Generates TLV-encoded data.

        Params:
            min_len (int): The minimum length for the sequences.
            max_err (int): The maximum times we can attempt adding a new instruction before backtracking.
            start (bytes): The starting prefix for the class file.
            end (bytes): The ending suffix for the class file.
            code_attr_len (int): The length of the code attribute itself without any code.

        Returns:
            bytes: TLV-encoded data.
        """
        pre = bytes([0x20, 0x00, 0x00, 0x07])
        tlv_data = bytearray()
        err_cnt = 0

        while True:
            tag = bytes([random.randint(1, 255)])
            length = bytes([random.randint(1, 255)])
            value = bytes([random.randint(0, 255)])

            if err_cnt > max_err:
                if len(tlv_data) >= 3:
                    last_tlv_length = int.from_bytes(tlv_data[-2:], byteorder="big") + 3
                    tlv_data = tlv_data[:-last_tlv_length]
                err_cnt = 0
                continue

            tlv_data.extend(tag + length + value)

            total_length = (code_attr_len + len(tlv_data)).to_bytes(4, byteorder="big")
            total = (
                total_length
                + pre
                + len(tlv_data).to_bytes(4, byteorder="big")
                + tlv_data
            )

            with open("test.class", "wb") as f:
                f.write(start)
                f.write(total)
                f.write(end)

            result = self.execute_binary()

            if result == "Complete":
                if len(tlv_data) < min_len:
                    if len(tlv_data) >= 3:
                        last_tlv_length = (
                            int.from_bytes(tlv_data[-2:], byteorder="big") + 3
                        )
                        tlv_data = tlv_data[:-last_tlv_length]
                    continue
                return bytes(tlv_data)

            elif result == "Incorrect" or result == "Error":
                if len(tlv_data) >= 3:
                    last_tlv_length = int.from_bytes(tlv_data[-2:], byteorder="big") + 3
                    tlv_data = tlv_data[:-last_tlv_length]
                err_cnt += 1
                continue

            err_cnt = 0

    def main_finder(self, path: str) -> tuple:
        """
        Finds where main is located and returns the start point at which we
        need to modify the class file from (namely the length of the Code attribute) and
        the end point of the code. It also returns how long the attribute is without the
        code itself: important since the attribute itself needs a size in the classfile.

        Parameters:
            str path :: a path to the class file
        """
        f = open(path, "rb")

        # Seeking past magic and classfile edition
        f.seek(8, 0)

        # Going through the constant pool now
        # Important to keep these since we need to keep track of the
        # constants to know when we hit the main method and code attribute
        const_count = struct.unpack("!H", f.read(2))[0]
        i = 1
        consts = list()
        while i < const_count:
            c = CPInfo().from_reader(f)
            consts.append(c)
            if c.tag == CPTag.DOUBLE:
                consts.append(CPInfo())
                i += 1

            i += 1

        # Seeking past access flags and class name indexes
        f.seek(6, 1)

        # Moving past the interfaces
        interface_count = struct.unpack("!H", f.read(2))[0]
        for i in range(interface_count):
            struct.unpack("!H", f.read(2))[0]

        # Moving past the fields
        fcnt = struct.unpack("!H", f.read(2))[0]
        for i in range(fcnt):
            fi = FieldInfo().from_reader(f)

        # At the methods section
        mcnt = struct.unpack("!H", f.read(2))[0]

        # Iterates through the methods until we find main
        for i in range(mcnt):
            f.seek(2, 1)
            name_idx = struct.unpack("!H", f.read(2))[0]
            if consts[name_idx - 1].string == "main":
                main = True
            else:
                main = False
            f.seek(2, 1)
            attr_cnt = struct.unpack("!H", f.read(2))[0]

            # Iterates through the attributes in main until we find the code attribute
            # If not main, simply keep iterating through the attributes until we get to the next
            # method
            for i in range(attr_cnt):
                if main:
                    name_idx = struct.unpack("!H", f.read(2))[0]

                    # Once we find the code attribute we break since we know where it starts and ends
                    if consts[name_idx - 1].string == "Code":
                        start_idx = f.tell()
                        length_attr = struct.unpack("!I", f.read(4))[0]

                        # Seek past locals and max stack
                        f.seek(4, 1)

                        length_code = struct.unpack("!I", f.read(4))[0]
                        code_attr_length = length_attr - length_code

                        f.seek(length_code, 1)
                        end_idx = f.tell()
                        break

                    # Not the code attribute so keep iterating
                    else:
                        length = struct.unpack("!I", f.read(4))[0]
                        f.seek(length, 1)

                else:
                    AttributeInfo().from_reader(f)

            # We've got main so no reason to keep looking through methods
            if main:
                break
        f.close()

        return start_idx, end_idx, code_attr_length

    def parse_tlv(self, data):
        tlv_instructions = []

        i = 0
        while i < len(data):
            # Extract tag, length, and value
            tag = data[i]
            length = data[i + 1]
            value = data[i + 2 : i + 2 + length]

            # Add the TLV instruction to the list
            tlv_instructions.append({"tag": tag, "length": length, "value": value})

            # Move the index to the next TLV instruction
            i += 2 + length

        return tlv_instructions

    def get_valid(self, num: int, min_len: int, max_err: int) -> list:
        """
        Returns a list of complete sequences of instructions for the JVM.

        Params:
            int num :: the specified number of sequences to generate
            int min_len :: the minimum length for the sequences
            int max_err :: the maximum times we can attempt adding a new instruction before backtracking
        """

        start_idx, end_idx, code_attr_length = self.main_finder("test.class")
        f = open("test.class", "rb")
        start = f.read(start_idx)
        f.seek(end_idx)
        end = f.read(-1)
        f.close()

        valid = []
        while len(valid) < num:
            tlv_data = self.generate(
                min_len, max_err, start, end, code_attr_length, tlv=True
            )
            instructions = self.parse_tlv(tlv_data)  # Parse TLV-encoded data

            # Append the parsed TLV instructions to the valid list
            valid.append({"tlv_data": tlv_data, "instructions": instructions})

        return valid


if __name__ == "__main__":
    count = 1
    length = 400
    max_err = 40
    valid = Fuzzer().get_valid(count, length, max_err)

    for i, entry in enumerate(valid):
        print(f"Sequence {i + 1} - TLV Data: {entry['tlv_data']}")
        print("Parsed Instructions:")
        for j, instruction in enumerate(entry["instructions"]):
            print(f"  Instruction {j + 1}:")
            print(f"    Tag: {instruction['tag']}")
            print(f"    Length: {instruction['length']}")
            print(f"    Value: {instruction['value']}")
