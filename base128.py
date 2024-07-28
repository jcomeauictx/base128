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
import sys, os, logging  # pylint: disable=multiple-imports
logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)
# pylint: disable=consider-using-f-string
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
    >>> b64encode(b'\0')
    'AA======'
    >>> encode(b'\0\1')
    'AAg====='
    >>> b64encode(b'\0\1')
    'AAg====='
    >>> encode(b'\0\1\2')
    'AAgg===='
    >>> b64encode(b'\0\1\2')
    'AAgg===='
    >>> encode(b'\0\1\2\3')
    'AAggY==='
    >>> b64encode(b'\0\1\2\3')
    'AAggY==='
    >>> encode(b'\0\1\2\3\4')
    'AAggYQ=='
    >>> b64encode(b'\0\1\2\3\4')
    'AAggYQ=='
    >>> encode(b'\0\1\2\3\4\5')
    'AAggYQK='
    >>> b64encode(b'\0\1\2\3\4\5')
    'AAggYQK='
    >>> encode(b'\0\1\2\3\4\5\6')
    'AAggYQKG'
    >>> b64encode(b'\0\1\2\3\4\5\6')
    'AAggYQKG'
    >>> encode(b'\0\1\2\3\4\5\6\7')
    'AAggYQKGDÀ======'
    >>> b64encode(b'\0\1\2\3\4\5\6\7')
    'AAggYQKGDÀ======'
    >>> encode(b'\0\1\2\3\4\5\6\7\0x8')
    'AAggYQKGDÀPDÀ==='
    >>> b64encode(b'\0\1\2\3\4\5\6\7\0x8')
    'AAggYQKGDÀPDÀ==='
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
    b'x\00'
    >>> decode('AAg=====')
    >>> b64decode('AAg=====')
    >>> decode('AAgg====')
    >>> b64decode('AAgg====')
    >>> decode('AAggY===')
    >>> b64decode('AAggY===')
    >>> decode('AAggYQ==')
    >>> b64decode('AAggYQ==')
    >>> decode('AAggYQK=')
    >>> b64decode('AAggYQK=')
    >>> decode('AAggYQKG')
    >>> b64decode('AAggYQKG')
    >>> decode('AAggYQKGDA======')
    >>> b64decode('AAggYQKGDA======')
    >>> decode('AAggYQKGDAPDA===')
    >>> b64decode('AAggYQKGDAPDA===')
    '''
    decoded = b''
    chunks, padding = chunked(encoded, 8)
    for chunk in chunks:
        doctest_debug('chunk: %s', chunk)
        integer = 0
        for character in chunk:
            integer <<= 7
            try:
                integer |= BASE128.index(character)
            except ValueError as problem:
                logging.error('failed decode at %r: %s', character, problem)
                raise
        doctest_debug('integer: 0x%x', integer)
        try:
            decoded += integer.to_bytes(7, 'big')
        except OverflowError as failed:
            logging.error('integer 0x%x will not fit in 7 bytes', integer)
            break
    return decoded[:(-padding or None)]

def chunked(something, size):
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
        padding = len(something) - len(something.rstrip('='))
        something = something.replace('=', ZERO)
    except TypeError:
        padding = 0
    chunks = [something[i: i + size] for i in range(0, len(something), size)]
    final = chunks[-1]
    if len(final) < size:
        if isinstance(final, bytes):
            chunks[-1] = final.ljust(size, b'\0')
            padding = len(chunks[-1]) - len(final)
        else:
            padding = size - len(final)  # let's just pad it
            chunks[-1] = final.ljust(size, ZERO)
            
    return chunks, padding

if PROGRAM == 'doctest':
    # pylint: disable=function-redefined
    def doctest_debug(message, *args, **kwargs):
        '''
        verbose debugging only during doctests
        '''
        logging.debug(message, *args, **kwargs)
else:
    logging.debug('sys.argv: %s', sys.argv)
