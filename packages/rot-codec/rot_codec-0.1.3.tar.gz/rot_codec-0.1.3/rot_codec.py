import os
import functools
import codecs
import click


a = ord('a')
z = ord('z')
A = ord('A')
Z = ord('Z')
i0 = ord('0')
i9 = ord('9')
ROT_MIN = 33 # !
ROT_MAX = 126 # ~

ROT5_ENCODE_RANGES = [(i0, i9, 5)]
ROT5_DECODE_RANGES = [(i0, i9, -5)]
ROT13_ENCODE_RANGES = [(A, Z, 13), (a, z, 13)]
ROT13_DECODE_RANGES = [(A, Z, -13), (a, z, -13)]
ROT18_ENCODE_RANGES = [(i0, i9, 5), (A, Z, 13), (a, z, 13)]
ROT18_DECODE_RANGES = [(i0, i9, -5), (A, Z, -13), (a, z, -13)]
ROT47_ENCODE_RANGES = [(ROT_MIN, ROT_MAX, 47)]
ROT47_DECODE_RANGES = [(ROT_MIN, ROT_MAX, -47)]
ASCIIROT_NAMES = []
ASCIIROT_ENCODE_RANGES = {}
ASCIIROT_DECODE_RANGES = {}

for i in range(256):
    name = "asciirot{0}".format(i+1)
    ASCIIROT_NAMES.append(name)
    ASCIIROT_ENCODE_RANGES[name] = [(0, 255, i+1)]
    ASCIIROT_DECODE_RANGES[name] = [(0, 255, -i-1)]

def get_ASCIIROT_ranges(name):
    return ASCIIROT_ENCODE_RANGES[name], ASCIIROT_DECODE_RANGES[name]

def rot(text, rot_ranges):
    result = ""
    for c in text:
        ord_c = ord(c)
        transformed = False
        for rot_range in rot_ranges:
            if rot_range[0] <= ord_c <= rot_range[1]:
                ord_c = (rot_range[1] + ord_c + rot_range[2] - 2 * rot_range[0] + 1) % (rot_range[1] - rot_range[0] + 1) + rot_range[0]
                result += chr(ord_c)
                transformed = True
                break
        if not transformed:
            result += c
    return result

def make_rot_coder(rot_ranges):
    def real(text: str) -> str:
        result = rot(text, rot_ranges)
        return result, len(result)
    return real

def rot5_encode(text):
    return rot(text, ROT5_ENCODE_RANGES)

def rot5_decode(text):
    return rot(text, ROT5_DECODE_RANGES)

def rot13_encode(text):
    return rot(text, ROT13_ENCODE_RANGES)

def rot13_decode(text):
    return rot(text, ROT13_DECODE_RANGES)

def rot18_encode(text):
    return rot(text, ROT18_ENCODE_RANGES)

def rot18_decode(text):
    return rot(text, ROT18_DECODE_RANGES)

def rot47_encode(text):
    return rot(text, ROT47_ENCODE_RANGES)

def rot47_decode(text):
    return rot(text, ROT47_DECODE_RANGES)

def _rot5_encoder(text: str) -> str:
    result = rot5_encode(text)
    return result, len(result)

def _rot5_decoder(text: str) -> str:
    result = rot5_decode(text)
    return result, len(result)

def _rot5_search(name):
    if name == "rot5":
        return codecs.CodecInfo(_rot5_encoder, _rot5_decoder, name="rot5")
    else:
        return None

def _rot13_encoder(text: str) -> str:
    result = rot13_encode(text)
    return result, len(result)

def _rot13_decoder(text: str) -> str:
    result = rot13_decode(text)
    return result, len(result)

def _rot13_search(name):
    if name == "rot13":
        return codecs.CodecInfo(_rot5_encoder, _rot5_decoder, name="rot13")
    else:
        return None

def _rot18_encoder(text: str) -> str:
    result = rot18_encode(text)
    return result, len(result)

def _rot18_decoder(text: str) -> str:
    result = rot18_decode(text)
    return result, len(result)

def _rot18_search(name):
    if name == "rot18":
        return codecs.CodecInfo(_rot5_encoder, _rot5_decoder, name="rot18")
    else:
        return None

def _rot47_encoder(text: str) -> str:
    result = rot47_encode(text)
    return result, len(result)

def _rot47_decoder(text: str) -> str:
    result = rot47_decode(text)
    return result, len(result)

def _rot47_search(name):
    if name == "rot47":
        return codecs.CodecInfo(_rot5_encoder, _rot5_decoder, name="rot47")
    else:
        return None

def _asciirot_search(name):
    if name in ASCIIROT_NAMES:
        encode_ranges, decode_ranges = get_ASCIIROT_ranges(name)
        encoder = make_rot_coder(encode_ranges)
        decoder = make_rot_coder(decode_ranges)
        return codecs.CodecInfo(encoder, decoder, name=name)
    else:
        return None

codecs.register(_rot5_search)
codecs.register(_rot13_search)
codecs.register(_rot18_search)
codecs.register(_rot47_search)
codecs.register(_asciirot_search)

def get_content(content, encoding="utf-8"):
    if not content:
        if hasattr(os.sys.stdin, "reconfigure"):
            os.sys.stdin.reconfigure(encoding=encoding)
            content = os.sys.stdin.read()
            return content
        else:
            import codecs
            content = codecs.getreader(encoding)(os.sys.stdin).read()
            return content
    if os.path.exists(content):
        with open(content, "r", encoding=encoding) as fobj:
            return fobj.read()
    return content


@click.group()
def main():
    """
    target character set for rot5 : 0-9

    target character set for rot13 : a-zA-Z

    target character set for rot18 : 0-9a-zA-Z

    target character set for rot46 : chr(33)-chr(126)

    target character set for asciirot1 ~ asciirot256 : chr(0)-chr(255)
    """
    pass


@main.command(name="rot")
@click.option("-m", "--method", type=click.Choice(["rot5", "rot13", "rot18", "rot47"] + ASCIIROT_NAMES), default="rot13")
@click.option("-d", "--decode", is_flag=True)
@click.option("-e", "--encoding", default="utf-8", help="Message encoding. Default UTF-8. Use iso-8859-1 for any binary MESSAGE.")
@click.argument("message", nargs=1, required=False)
def rot_cli(method, decode, encoding, message):
    """
    """
    message = get_content(message, encoding)
    if not decode:
        result = codecs.encode(message, method)
    else:
        result = codecs.decode(message, method)
    click.echo(result)

@main.command(name="guess")
@click.option("-e", "--encoding", default="utf-8", help="Message encoding. Default UTF-8. Use iso-8859-1 for any binary MESSAGE.")
@click.argument("message", nargs=1, required=False)
def rot_guess_decode():
    pass

if __name__ == "__main__":
    main()
