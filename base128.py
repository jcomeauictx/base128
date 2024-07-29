#!/usr/bin/python3 -OO
'''
simple base 128 encoder/decoder

Use base64 characters and method, except that a selection of printable
8-bit Latin-1 characters are added to make each character represent 7 bits.
Therefore every 8 encoded bytes represent 7 binary data bytes, slightly
better than the 4:3 (8:6) ratio of base64.

>>> len(BASE64)
64
>>> len(BASE128)
128
>>> encode(decode(BASE128)) == BASE128
True
'''
import sys, os, io, logging  # pylint: disable=multiple-imports
logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)
# pylint: disable=consider-using-f-string, consider-using-with
BASE64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
BASE128 = BASE64 + bytearray(range(192, 256)).decode('latin-1')
ZERO = BASE128[0]
PAD = '='
PROGRAM = os.path.splitext(os.path.basename(sys.argv[0] or ''))[0]

def doctest_debug(message, *args, **kwargs):  # pylint: disable=unused-argument
    '''
    no-op unless redefined below
    '''

def encode(bytestring):
    r'''
    encode bytes to base128

    avoids using := or itertools, to make this work with older Python versions.

    >>> from base64 import b64encode
    >>> encode(b'\0')
    'AA======'
    >>> b64encode(b'\0').decode()
    'AA=='
    >>> encode(b'\0\1')
    'AAg====='
    >>> b64encode(b'\0\1').decode()
    'AAE='
    >>> encode(b'\0\1\2')
    'AAgg===='
    >>> b64encode(b'\0\1\2').decode()
    'AAEC'
    >>> encode(b'\0\1\2\3')
    'AAggY==='
    >>> b64encode(b'\0\1\2\3')
    b'AAECAw=='
    >>> encode(b'\0\1\2\3\4')
    'AAggYQ=='
    >>> b64encode(b'\0\1\2\3\4')
    b'AAECAwQ='
    >>> encode(b'\0\1\2\3\4\5')
    'AAggYQK='
    >>> b64encode(b'\0\1\2\3\4\5')
    b'AAECAwQF'
    >>> encode(b'\0\1\2\3\4\5\6')
    'AAggYQKG'
    >>> b64encode(b'\0\1\2\3\4\5\6')
    b'AAECAwQFBg=='
    >>> encode(b'\0\1\2\3\4\5\6\7')
    'AAggYQKGDÀ======'
    >>> b64encode(b'\0\1\2\3\4\5\6\7')
    b'AAECAwQFBgc='
    >>> encode(b'\0\1\2\3\4\5\6\7\x08')
    'AAggYQKGDÂA====='
    >>> b64encode(b'\0\1\2\3\4\5\6\7\x08')
    b'AAECAwQFBgcI'
    '''
    def encode_int(integer):
        '''
        inner generator function to process one integerified chunk at a time
        '''
        bitmask = (1 << 7) - 1
        for _ in range(8):
            yield BASE128[integer & bitmask]
            integer >>= 7

    encoded = ''
    chunks, padding = chunked(bytestring, 7)
    for chunk in chunks:
        doctest_debug('chunk: %s', chunk)
        integer = int.from_bytes(chunk, 'big')
        doctest_debug('integer: 0x%x', integer)
        characters = list(reversed(list(encode_int(integer))))
        doctest_debug('characters: %s', characters)
        encoded += ''.join(characters)
    return encoded[:(-padding or None)] + PAD * padding

def decode(encoded):
    r'''
    decode base128 string to binary

    >>> from base64 import b64decode
    >>> len(decode(BASE128)) == (7 / 8) * len(BASE128)
    True
    >>> decode('AA======')
    b'\x00'
    >>> b64decode('AA======')
    b'\x00'
    >>> decode('AAg=====')
    b'\x00\x01'
    >>> b64decode('AAg=====')
    b'\x00\x08'
    >>> decode('AAgg====')
    b'\x00\x01\x02'
    >>> b64decode('AAgg====')
    b'\x00\x08 '
    >>> decode('AAggY===')
    b'\x00\x01\x02\x03'
    >>> # b64decode('AAggY===')  # invalid base64 string
    >>> decode('AAggYQ==')
    b'\x00\x01\x02\x03\x04'
    >>> b64decode('AAggYQ==')
    b'\x00\x08 a'
    >>> decode('AAggYQK=')
    b'\x00\x01\x02\x03\x04\x05'
    >>> b64decode('AAggYQK=')
    b'\x00\x08 a\x02'
    >>> decode('AAggYQKG')
    b'\x00\x01\x02\x03\x04\x05\x06'
    >>> b64decode('AAggYQKG')
    b'\x00\x08 a\x02\x86'
    >>> decode('AAggYQKGDÀ======')
    b'\x00\x01\x02\x03\x04\x05\x06\x07'
    >>> decode('AAggYQKGDÂA=====')
    b'\x00\x01\x02\x03\x04\x05\x06\x07\x08'
    '''
    decoded = b''
    chunks, padding = chunked(encoded, 8)
    base128 = {c: BASE128.index(c) for c in BASE128}
    logging.log(logging.NOTSET, 'base128: %s', base128)
    for chunk in chunks:
        doctest_debug('chunk: %s', chunk)
        integer = 0
        for character in chunk:
            integer <<= 7
            try:
                integer |= base128[character]
            except ValueError as problem:
                logging.error('failed decode at %r: %s', character, problem)
                raise
        doctest_debug('integer: 0x%x', integer)
        try:
            decoded += integer.to_bytes(7, 'big')
        except OverflowError:
            logging.error('integer 0x%x will not fit in 7 bytes', integer)
            break
    return decoded[:(-padding or None)]

def chunked(something, size, pad=True):
    r'''
    split string or bytes into chunks of size `size`

    use padding (b'\0' if bytes; strings should already be padded

    >>> chunked(b'1234', 1)
    ([b'1', b'2', b'3', b'4'], 0)
    >>> chunked(b'1234', 2)
    ([b'12', b'34'], 0)
    >>> chunked(b'1234', 3)
    ([b'123', b'4\x00\x00'], 2)
    >>> chunked(b'1234', 4)
    ([b'1234'], 0)
    >>> chunked(b'1234', 5)
    ([b'1234\x00'], 1)
    >>> chunked('1234==', 3)
    (['123', '4AA'], 2)
    >>> chunked('1234=', 5)
    (['1234A'], 1)
    >>> chunked('1234', 5)
    (['1234A'], 1)
    '''
    try:
        if pad:
            padding = len(something) - len(something.rstrip('='))
            something = something.replace('=', ZERO)
        else:
            raise PermissionError('No padding requested')
    except (TypeError, PermissionError):
        padding = 0
    chunks = [something[i: i + size] for i in range(0, len(something), size)]
    final = chunks[-1]
    if len(final) < size:
        if isinstance(final, bytes):
            chunks[-1] = final.ljust(size, b'\0')
            padding = len(chunks[-1]) - len(final)
        elif pad:
            padding = size - len(final)
            chunks[-1] = final.ljust(size, ZERO)
    return chunks, padding

def dispatch(command=None, infile=None, outfile=None):
    '''
    call subroutine as command line specifies

    `encode` reads binary and writes unicode
    `decode` reads unicode and writes binary
    '''
    def latin1_open(*args):
        if not args[-1].endswith('b'):
            return open(*args, encoding='latin-1')
        return open(*args)  # pylint: disable=unspecified-encoding
    latin1_in = io.open(sys.stdin.fileno(), encoding='latin-1')
    latin1_out = io.open(sys.stdout.fileno(), encoding='latin-1')
    if command not in ('encode', 'decode'):
        logging.error('Must specify either "encode" or "decode"')
        return
    modes = {'encode': ('rb', 'w'), 'decode': ('r', 'wb')}[command]
    stdio = {
        'encode': (sys.stdin.buffer, latin1_out),
        'decode': (latin1_in, sys.stdout.buffer)
    }[command]
    preprocess = {
        'encode': bytes,
        'decode': lambda s: ''.join(s.split())
    }[command]
    postprocess = {
        'encode': lambda s: '\r\n'.join(chunked(s, 76, False)[0]),
        'decode': bytes
    }[command]
    infile = latin1_open(infile, modes[0]) if infile else stdio[0]
    outfile = latin1_open(outfile, modes[1]) if outfile else stdio[1]
    logging.debug('command: %s, infile: %s, outfile: %s',
                  command, infile, outfile)
    data = preprocess(infile.read())
    outfile.write(postprocess(eval(command)(data)))  # pylint: disable=eval-used

if PROGRAM == 'doctest':
    # pylint: disable=function-redefined
    def doctest_debug(message, *args, **kwargs):
        '''
        verbose debugging only during doctests
        '''
        logging.debug(message, *args, **kwargs)
elif __name__ == '__main__':
    dispatch(*sys.argv[1:])
