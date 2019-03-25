import sys
from functools import lru_cache
from io import BytesIO


def error(message):
    """Write an error to the console"""
    print(f'\033[31mError:\033[0m {message}', file=sys.stderr)
    return 1


def b2s(binary):
    """
    Binary to string helper which ignores all data which can't be decoded
    :param binary: Binary bytes string
    :return: String
    """
    return binary.decode(encoding='ascii', errors='ignore')


def b2s_file(binary_file):
    """
    File based binary to string helper
    :param binary_file: Binary file to convert
    :return: The same file object with a patched method
    """
    orig = binary_file.read
    binary_file.read = lambda *a, **k: b2s(orig(*a, **k))
    return binary_file


def log(message):
    print(message, file=sys.stderr)
    return 0


@lru_cache()
def wc(file):
    """Get number of lines in a file"""
    with open(file, mode='rb') as fd:
        return sum(1 for _ in fd)


def handle_interrupt(func):
    """Decorator which ensures that keyboard interrupts are handled properly."""
    def wrapper():
        try:
            return func() or 0
        except KeyboardInterrupt:
            print('\n\033[31mError:\033[0m Aborted.')
            return 1
    return wrapper


class DevNull(BytesIO):
    def write(self, *_): pass

    def read(self, *_): return b''
