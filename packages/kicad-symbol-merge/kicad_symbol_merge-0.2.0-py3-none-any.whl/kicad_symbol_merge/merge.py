import os, re, argparse

HEADER  = "(kicad_symbol_lib\n"
HEADER2 = '\t(version 20231120)\n\t(generator "kicad_symbol_editor")\n\t(generator_version "8.0")\n'
FOOTER  = ")\n"

def extract_symbols(text):
    syms, start, depth = [], None, 0
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if "(symbol " in line and start is None:
            start, depth = i, 0
        if start is not None:
            depth += line.count("(")
            depth -= line.count(")")
            if depth == 0:
                syms.append("".join(lines[start:i + 1]))
                start = None
    return syms

def symbol_name(sym_block):
    first = sym_block.splitlines()[0]
    m = re.search(r'\(symbol\s+"([^"]+)"', first)
    if m: return m.group(1)
    m = re.search(r'\(symbol\s+([^\s()]+)', first)
    return m.group(1) if m else None

def read_lib_symbols(path):
    if not os.path.exists(path): return [], set()
    data = open(path, encoding="utf-8").read()
    syms = extract_symbols(data)
    names = {symbol_name(s) for s in syms if symbol_name(s)}
    return syms, names

def merge_folder(source_dir, target):
    existing_syms, existing_names = read_lib_symbols(target)
    added_syms, added_names, skipped = [], set(), 0

    for f in sorted(os.listdir(source_dir)):
        if not f.endswith(".kicad_sym"): continue
        data = open(os.path.join(source_dir, f), encoding="utf-8").read()
        for s in extract_symbols(data):
            nm = symbol_name(s)
            if not nm: continue
            if nm in existing_names or nm in added_names:
                skipped += 1
                continue
            added_syms.append(s)
            added_names.add(nm)

    with open(target, "w", encoding="utf-8") as out:
        out.write(HEADER); out.write(HEADER2)
        for s in existing_syms: out.write("\t" + s.strip() + "\n\n")
        for s in added_syms:    out.write("\t" + s.strip() + "\n\n")
        out.write(FOOTER)

    print(f"Scanned: {source_dir}")
    print(f"Existing in target: {len(existing_syms)}")
    print(f"Added: {len(added_syms)}   Skipped (dups): {skipped}")
    print(f"Output: {target}")

def main():
    ap = argparse.ArgumentParser(description="Append only new KiCad symbols into a target .kicad_sym")
    ap.add_argument("source_dir", help="Folder with .kicad_sym files")
    ap.add_argument("target", help="Target .kicad_sym")
    args = ap.parse_args()
    merge_folder(args.source_dir, args.target)

if __name__ == "__main__":
    main()
