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
    for chunk in [bytestring[i:i + 7]
                  for i in range(0, len(bytestring) + 6, 7)]:
        doctest_debug('chunk: %s', chunk)
        integer = int.from_bytes(chunk, 'big')
        doctest_debug('integer: 0x%x', integer)

def decode(encoded):
    '''
    decode base128 string to binary

    >>> decode(BASE128)
    '''
    integer = 0
    decoded = b''
    for chunk in [encoded[i:i + 8] for i in range(0, len(encoded) + 7, 8)]:
        doctest_debug('chunk: %s', chunk)
        for character in chunk:
            integer <<= 7
            integer |= BASE128.index(character)
        doctest_debug('integer: 0x%x', integer)
        decoded += integer.to_bytes(7, 'big')
    return decoded

if PROGRAM == 'doctest':
    # pylint: disable=function-redefined
    def doctest_debug(message, *args, **kwargs):
        '''
        verbose debugging only during doctests
        '''
        logging.debug(message, *args, **kwargs)
else:
    logging.debug('sys.argv: %s', sys.argv)
