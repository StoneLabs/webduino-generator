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
