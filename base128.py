#!/usr/bin/python3 -OO
'''
simple base 128 encoder/decoder

Use base64 characters and method, except that a selection of printable
8-bit Latin-1 characters are added to make each character represent 7 bits.
Therefore every 8 encoded bytes represent 7 binary data bytes, slightly
better than the 4:3 (8:6) ratio of base64.

The maximum padding in each case is one less than the number of bytes in
an uncompressed group: therefore, 7-1=6 in base128 and 3-1=2 in the case of
base64. Six padding characters ("=") in a short compressed string will easily
ruin whatever is gained by the better compression, so we will choose some
other unused characters to represent 2, 3, 4, 5, and 6 padding characters.

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
DICT128 = {c: BASE128.index(c) for c in BASE128}
ZERO = BASE128[0]
PAD = '='
PADDING = [PAD] + [chr(n) for n in range(161, 166)]
PROGRAM = os.path.splitext(os.path.basename(sys.argv[0] or ''))[0]
LINE_LENGTH = 76  # per base64 wikipedia
ENCODER_BITMASK = (1 << 7) - 1  # extract an index from integer

def doctest_debug(message, *args, **kwargs):  # pylint: disable=unused-argument
    '''
    no-op unless redefined below

    still need to comment out all doctest_debug calls before release
    '''

def encode(bytestring):
    r'''
    encode bytes to base128

    avoids using := or itertools, to make this work with older Python versions.

    b64encode output shown for comparison; for short strings, base64 is
    often smaller.

    >>> from base64 import b64encode
    >>> encode(b'\0')
    'AA======'
    >>> b64encode(b'\0')
    b'AA=='
    >>> encode(b'\0\1')
    'AAg====='
    >>> b64encode(b'\0\1')
    b'AAE='
    >>> encode(b'\0\1\2')
    'AAgg===='
    >>> b64encode(b'\0\1\2')
    b'AAEC'
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
    >>> # to avoid unicode characters in program source, encode these to bytes
    >>> encode(b'\0\1\2\3\4\5\6\7').encode('latin-1')
    b'AAggYQKGD\xc0======'
    >>> b64encode(b'\0\1\2\3\4\5\6\7')
    b'AAECAwQFBgc='
    >>> encode(b'\0\1\2\3\4\5\6\7\x08').encode('latin-1')
    b'AAggYQKGD\xc2A====='
    >>> b64encode(b'\0\1\2\3\4\5\6\7\x08')
    b'AAECAwQFBgcI'
    '''
    encoded = ''
    chunks, padding = chunked(bytestring, 7)
    logging.debug('decoding ...%s', chunks[-5:])
    for chunk in chunks:
        #doctest_debug('chunk: %s', chunk)
        integer = int.from_bytes(chunk, 'big')
        #doctest_debug('integer: 0x%x', integer)
        characters = list(reversed(list(encode_int(integer))))
        #doctest_debug('characters: %s', characters)
        encoded += ''.join(characters)
    return encoded[:(-padding or None)] + PAD * padding

def decode(encoded):
    r'''
    decode base128 string to binary

    b64decode output shown for comparison, except in cases where latin-1
    characters are in the string.

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
    >>> decode('AAggYQKGD\xc0======')
    b'\x00\x01\x02\x03\x04\x05\x06\x07'
    >>> decode('AAggYQKGD\xc2A=====')
    b'\x00\x01\x02\x03\x04\x05\x06\x07\x08'
    '''
    chunks, padding = chunked(encoded, 8)
    logging.debug('decoding ...%s', chunks[-5:])
    decoded = b''
    pieces = []
    for chunk in chunks:
        pieces.append(decode_chunk(chunk))
    decoded = b''.join(pieces)
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

def encode_int(integer):
    '''
    generator to process one integerified chunk at a time
    '''
    for _ in range(8):
        yield BASE128[integer & ENCODER_BITMASK]
        integer >>= 7

def decode_chunk(chunk):
    r'''
    get binary data from chunk of latin-1 data

    >>> decode_chunk('AAAAAAAA')
    b'\x00\x00\x00\x00\x00\x00\x00'
    '''
    integer = 0
    character = decoded = b''  # define here so they show up in error messages
    #doctest_debug('chunk: %s', chunk)
    try:
        for character in chunk:
            integer = (integer << 7) | DICT128[character]
        decoded = integer.to_bytes(7, 'big')
        #doctest_debug('decoded: %s', decoded)
        return decoded
    except ValueError as problem:
        logging.error('failed decode of chunk %r at byte %r: %s',
                      chunk, character, problem)
        raise
    except OverflowError:
        logging.error('integer 0x%x will not fit in 7 bytes', integer)
        raise

def preprocess(command, something):
    '''
    return bytes unchanged, but clean up latin-1
    '''
    processed = something
    if command == 'decode':
        logging.debug('preprocessing %s data %r', command, something[:80])
        processed = pessimize_padding(''.join(something.split()))
        if processed == something:
            logging.debug('preprocessing left data unchanged')
    else:
        logging.debug('no preprocessing done for %s', command)
    return processed

def postprocess(command, something):
    '''
    split up latin-1 into lines, but pass through bytes unchanged
    '''
    processed = something
    if command == 'encode':
        chunks = chunked(optimize_padding(something), LINE_LENGTH, False)[0]
        logging.debug('postprocessing chunks: ...%r', chunks[-2:])
        processed = os.linesep.join(chunks) + os.linesep
        logging.debug('processed: ...%r', processed[-80:])
    else:
        logging.debug('no postprocessing done for %s', command)
    return processed

def latin1_open(*args, **kwargs):
    '''
    make sure text inputs and outputs are read or written as latin-1
    '''
    logging.debug('latin1_open(*%s)', args)
    if hasattr(args[0], 'fileno'):
        if args[0] in (sys.stdin, sys.stdout):
            # pylint: disable=unspecified-encoding
            kwargs['encoding'] = 'latin-1'
            return io.open(args[0].fileno(), *args[1:], **kwargs)
        return args[0]  # sys.{stdin,stdout}.buffer
    if not args[-1].endswith('b'):  # not binary means string
        logging.debug('opening %s as latin-1 string data', args[0])
        return open(*args, encoding='latin-1')
    logging.debug('opening %s as binary data', args[0])
    return open(*args)  # pylint: disable=unspecified-encoding

def optimize_padding(encoded):
    r'''
    combine 2 to 6 padding characters ("=") into one extended pad character

    >>> optimize_padding('AA======')
    'AA\xa5'
    '''
    padding = len(encoded) - len(encoded.rstrip(PAD))
    if padding > 1:
        encoded = encoded.rstrip(PAD) + PADDING[padding - 1]
    return encoded

def pessimize_padding(encoded):
    r'''
    convert extended pad character into 2 to 6 "=" characters

    this does *not* check for malformed combinations of base64-style pad
    characters and base128 extended padding.

    >>> pessimize_padding('AA\xa5')
    'AA======'
    '''
    if encoded.endswith(tuple(PADDING[1:])):
        encoded = encoded[:-1] + (PAD * (PADDING.index(encoded[-1]) + 1))
    return encoded

def dispatch(command=None, infile=None, outfile=None):
    '''
    call subroutine as command line specifies

    `encode` reads binary and writes latin-1
    `decode` reads latin-1 and writes binary
    '''
    if command not in ('encode', 'decode'):
        logging.error('Must specify either "encode" or "decode"')
        return
    modes = {'encode': ('rb', 'w'), 'decode': ('r', 'wb')}[command]
    stdio = {
        'encode': (sys.stdin.buffer, sys.stdout),
        'decode': (sys.stdin, sys.stdout.buffer)
    }[command]
    infile = latin1_open(infile or stdio[0], modes[0])
    outfile = latin1_open(outfile or stdio[1], modes[1])
    logging.debug('command: %s, infile: %s, outfile: %s',
                  command, infile, outfile)
    data = preprocess(command, infile.read())
    outfile.write(postprocess(
        command, eval(command)(data))  # pylint: disable=eval-used
    )

if PROGRAM == 'doctest':
    # pylint: disable=function-redefined
    def doctest_debug(message, *args, **kwargs):
        '''
        verbose debugging only during doctests
        '''
        logging.debug(message, *args, **kwargs)
elif __name__ == '__main__':
    dispatch(*sys.argv[1:])
