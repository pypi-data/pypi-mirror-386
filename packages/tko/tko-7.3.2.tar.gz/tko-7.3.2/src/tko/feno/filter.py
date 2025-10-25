import os
import argparse
import shutil
from tko.util.decoder import Decoder
from typing import Any

class Mark:
    def __init__(self, marker: str, indent: int):
        self.marker: str = marker
        self.indent: int = indent

    # @override
    def __str__(self):
        return f"{self.marker}:{self.indent}"

class Mode:
    ADD = "ADD!"
    COM = "COM!"
    ACT = "ACT!"
    DEL = "DEL!"
    opts = [ADD, COM, ACT, DEL]

def get_comment(filename: str) -> str:
    com = "//"
    if filename.endswith(".py"):
        com = "#"
    elif filename.endswith(".hs"):
        com = "--"
    elif filename.endswith(".puml"):
        com = "'"
    return com

class Filter:
    def __init__(self, filename: str):
        self.filename = filename
        self.stack = [Mark(Mode.ADD, 0)]
        self.com = get_comment(filename)
        self.tab_char = "\t" if filename.endswith(".go") else " "

    def get_marker(self) -> str:
        return self.stack[-1].marker

    def get_indent(self) -> int:
        return self.stack[-1].indent

    def outside_scope(self, line: str):
        stripped = line.strip()
        left_spaces = len(line) - len(line.lstrip())
        return stripped != "" and left_spaces < self.get_indent()

    def has_single_mode_cmd(self, line: str) -> bool:
        stripped = line.strip()
        for marker in Mode.opts:
            if stripped == self.com + " " + marker:
                return True
        return False

    def change_mode(self, line: str):
        with_left = line.rstrip()
        marker = with_left.lstrip()[len(self.com) + 1:]
        len_spaces = len(with_left) - len(self.com + marker + " ")
        while len(self.stack) > 0 and self.stack[-1].indent >= len_spaces:
            self.stack.pop()
        self.stack.append(Mark(marker, len_spaces))

    def search_temp_mode(self, line: str) -> tuple[str, int, str]:
        for marker in Mode.opts:
            if line.rstrip().endswith(self.com + " " + marker):
                count: int = 0
                for i in range(len(line)):
                    if line[i] == " ":
                        count += 1
                    else:
                        break
                return marker, count, line[:-len(self.com + marker + " ")].rstrip()
        return "---", 0, line

    def __process(self, content: str) -> str:
        lines = content.splitlines()
        output: list[str] = []
        for line in lines:
            while self.outside_scope(line):
                self.stack.pop()
            if self.has_single_mode_cmd(line):
                self.change_mode(line)
                continue
            marker: str = self.get_marker()
            indent: int = self.get_indent()
            temp_marker, temp_indent, line = self.search_temp_mode(line)
            if temp_marker != "---":
                marker = temp_marker
                indent = temp_indent

            if marker == Mode.DEL:
                continue
            elif marker == Mode.ADD:
                output.append(line)
            elif marker == Mode.ACT:
                prefix = self.tab_char * indent + self.com + " "
                if not line.startswith(prefix):
                    prefix = prefix[:-1]
                line = line.replace(prefix, self.tab_char * indent, 1)
                output.append(line)
            elif marker == Mode.COM:
                line = self.tab_char * indent + self.com + " " + line[indent:]
                output.append(line)

        return "\n".join(output) + "\n"
    
    def process(self, content: str) -> str:
        return self.__process(content)

def clean_com(target: str, content: str) -> str:
    com = get_comment(target)
    lines = content.splitlines()
    output = [line for line in lines if not line.lstrip().startswith(com)]
    return "\n".join(output)

class DeepFilter:
    extensions = [".md", ".c", ".cpp", ".h", ".hpp", ".py", ".java", ".js", ".ts", ".hs", ".txt", ".go", ".json", ".mod", ".puml", ".sh", ".sql", ".yaml", ".exec", ".hide", ".tio"]

    def __init__(self):
        self.cheat_mode = False
        self.quiet_mode = False
        self.indent = ""
    
    def print(self, *args: str, **kwargs: Any):
        if not self.quiet_mode:
            print(self.indent, end="")
            print(*args, **kwargs)

    def set_indent(self, prefix: int):
        self.indent = prefix * " "
        return self

    def set_quiet(self, value: bool):
        self.quiet_mode = (value == True)
        return self
    
    def set_cheat(self, value: bool):
        self.cheat_mode = (value == True)
        return self

    def copy(self, source: str, destiny: str, deep: int):
        if deep == 0:
            return
        
        if os.path.isdir(source):
            chain = source.split(os.sep)
            if len(chain) > 1 and chain[-1].startswith("."):
                return
            if not os.path.isdir(destiny):
                os.makedirs(destiny)
            for file in sorted(os.listdir(source)):
                self.copy(os.path.join(source, file), os.path.join(destiny, file), deep - 1)
            return
        
        filename = os.path.basename(source)
        folder = os.path.dirname(source)
        deny_list = os.path.join(folder, ".deny")
        if os.path.isfile(deny_list):
            with open(deny_list) as f:
                deny = [x.strip() for x in f.read().splitlines()]
                if filename in deny:
                    print("(disabled):", destiny)
                    return

        if not any([filename.endswith(ext) for ext in self.extensions]):
            # print("(skipped ): ", filename)
            return

        content = Decoder.load(source)

        processed = Filter(filename).process(content)

        if self.cheat_mode:
            if processed != content:
                cleaned = clean_com(source, content)
                Decoder.save(destiny, cleaned)
        elif processed != "" and processed != "\n":
            Decoder.save(destiny, processed)

        line = ""
        if self.cheat_mode:
            if processed != content:
                line += "(cleaned ): "
            else:
                line += "(disabled): "
        else:
            if processed == "" or processed == "\n":
                line += "(disabled): "
            elif processed != content:
                line += "(filtered): "
            else:
                line += "(        ): "
        line += destiny

        self.print(line)

class CodeFilter:
    @staticmethod
    def open_file(path: str): 
        if os.path.isfile(path):
            file_content = Decoder.load(path)
            return True, file_content
        print("Warning: File", path, "not found")
        return False, "" 

    @staticmethod
    def cf_recursive(target_dir: str, output_dir: str, force: bool, cheat: bool = False, quiet: bool = False, indent: int = 0):
        if not os.path.isdir(target_dir):
            print("Error: target must be a folder in recursive mode")
            exit()
        if os.path.exists(output_dir):
            if not force:
                print("Error: output folder already exists")
                exit()
            else:
                # recursive delete all folder content without deleting the folder itself
                for file in os.listdir(output_dir):
                    path = os.path.join(output_dir, file)
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        os.remove(path)

        deep_filter = DeepFilter().set_cheat(cheat).set_quiet(quiet).set_indent(indent)
        deep_filter.copy(target_dir, output_dir, 10)

    @staticmethod
    def cf_single_file(target: str, output: str, update: bool, cheat: bool):
        file = target
        success, content = CodeFilter.open_file(file)
        if success:
            if cheat:
                content = clean_com(file, content)
            else:
                content = Filter(file).process(content)

            if output:
                if os.path.isfile(output):
                    old = Decoder.load(output)
                    if old != content:
                        Decoder.save(output, content)
                else:
                    Decoder.save(output, content)
            elif update:
                Decoder.save(file, content)
            else:
                print(content)

def filter_main(args: argparse.Namespace):
    if args.cheat:
        args.recursive = True

    if args.recursive:
        CodeFilter.cf_recursive(args.target, args.output, force=args.force, cheat=args.cheat, quiet=args.quiet, indent=args.indent)
        exit()

    CodeFilter.cf_single_file(args.target, args.output, args.update, args.cheat)
