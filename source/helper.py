import os

def cpp_str_esc(s, encoding='ascii'):
    if isinstance(s, bytes):
        s = s.encode(encoding)
    result = ''
    for c in s:
        if not (32 <= ord(c) < 127) or c in ('\\', '"'):
            result += '\\%03o' % ord(c)
        else:
            result += c
    return '"' + result + '"'

def cpp_img_esc(file):
    return "{{{0}}}".format("".join(["0x%x," % byte for byte in file.read()]))

def get_files_rec(parent):
    files = set()
    for dir_, _, files_ in os.walk(parent):
        for file_name in files_:
            rel_dir = os.path.relpath(dir_, parent)
            rel_file = os.path.join(rel_dir, file_name)

            rel_file = rel_file.replace("\\","/")
            if rel_file.startswith("./"):
                rel_file = rel_file[2:]

            files.add(rel_file)
    return files