#!/usr/bin/python3 -OO
'''
simple base 128 encoder/decoder

Use base64 characters and method, except that a selection of printable
8-bit Latin-1 characters are added to make each character represent 7 bits.
Therefore every 8 encoded bytes represent 7 binary data bytes, slightly
better than the 4:3 ratio of base64.
'''
import sys, os, logging  # pylint: disable=multiple-imports
logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)

BASE64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
BASE128 = BASE64 + bytearray(range(193, 256)).decode('latin-1')
PROGRAM = os.path.splitext(os.path.basename(sys.argv[0] or ''))[0]

def doctest_debug(message, *args, **kwargs):  # pylint: disable=unused-argument
    '''
    no-op unless redefined below
    '''

def encode(bytestring):
    '''
    encode bytes to base128

    avoids using := or itertools, to make this work with older Python versions.

    >>> encode(bytes(range(256)))
    '''
    chunks, padding = chunked(bytestring, 7)
    for chunk in chunks:
        doctest_debug('chunk: %s', chunk)
        integer = int.from_bytes(chunk, 'big')
        doctest_debug('integer: 0x%x', integer)

def decode(encoded):
    '''
    decode base128 string to binary

    >>> decode(BASE128)
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
    return decoded

def chunked(something, size):
    r'''
    split string or bytes into chunks of size `size`

    use padding if necessary (b'\0' if bytes and '=' if string)

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
    >>> chunked('1234', 3)
    (['123', '4=='], 2)
    >>> chunked('1234', 5)
    (['1234='], 1)
    '''
    padding = 0
    chunks = [something[i: i + size] for i in range(0, len(something), size)]
    final = chunks[-1]
    if len(final) < size:
        try:
            chunks[-1] = final.ljust(size, b'\0')
        except TypeError:
            chunks[-1] = final.ljust(size, '=')
        padding = len(chunks[-1]) - len(final)
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
