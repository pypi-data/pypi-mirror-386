import os
import re
import argparse

def extract_symbols(text):
    symbols, start, depth = [], None, 0
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if "(symbol " in line and start is None:
            start, depth = i, 0
        if start is not None:
            depth += line.count("(")
            depth -= line.count(")")
            if depth == 0:
                symbols.append("".join(lines[start:i + 1]))
                start = None
    return symbols

def merge_folder(source_dir, target):
    header = "(kicad_symbol_lib\n"
    header2 = '\t(version 20231120)\n\t(generator "kicad_symbol_editor")\n\t(generator_version "8.0")\n'
    footer = ")\n"

    with open(target, "w", encoding="utf-8") as out:
        out.write(header)
        out.write(header2)
        for f in sorted(os.listdir(source_dir)):
            if f.endswith(".kicad_sym"):
                path = os.path.join(source_dir, f)
                data = open(path, encoding="utf-8").read()
                for sym in extract_symbols(data):
                    out.write("\t" + sym.strip() + "\n\n")
        out.write(footer)

def main():
    parser = argparse.ArgumentParser(description="Merge all .kicad_sym files in a folder into one library.")
    parser.add_argument("source_dir", help="Path to folder containing .kicad_sym files")
    parser.add_argument("target", help="Output .kicad_sym filename")
    args = parser.parse_args()
    merge_folder(args.source_dir, args.target)
    print(f"Merged {args.source_dir} into {args.target}")

if __name__ == "__main__":
    main()
