import sys
from datetime import datetime
from argparse import ArgumentParser
from distutils.spawn import find_executable
from os.path import isfile

from stegcracker import __url__, __description__
from stegcracker.cracker import Cracker
from stegcracker.helpers import error, wc, handle_interrupt, DevNull, log, CustomHelpFormatter


@handle_interrupt
def main():
    """Main entry point of the application"""

    if any(i in sys.argv for i in ('-q', '--quiet', '--stfu')):
        if any(i in sys.argv for i in ('-V', '--verbose')):
            return error(
                "Arguments 'verbose' and 'quiet', are mutually exclusive. "
                "You have to choose either one of them, not both.")

        sys.stderr = DevNull()

    log(f'StegCracker - ({__url__})',)
    log(f'Copyright (c) {datetime.now().year} - Luke Paris (Paradoxis)')
    log('')

    args = ArgumentParser(
        usage='stegcracker <file> [<wordlist>]',
        formatter_class=CustomHelpFormatter,
        description=__description__)

    args.add_argument('file', action='store', help=(
        f'Input file you think contains hidden information and wish to crack. '
        f'Note: Stegcracker only accepts the following file types: '
        f'{", ".join(Cracker.SUPPORTED_FILES)}'))

    args.add_argument('wordlist', action='store', nargs='?', help=(
        'Wordlist containing the one or more passwords (one password per line). '
        'If no password list is supplied, this will default to the rockyou.txt '
        'wordlist on Kali Linux.'
    ), default='/usr/share/wordlists/rockyou.txt')

    args.add_argument('-o', '--output', default=None, help=(
        'Output file location, this will be the file the data will be written '
        'to on a successful cracked password. If no output location is '
        'specified, the default location will be the same filename with ".out" '
        'appended to the name.'))

    args.add_argument('-t', '--threads', type=int, default=16, help=(
        'Number of concurrent threads used to crack passwords with, increasing '
        'this number might lead to better performance. Default: 16'))

    args.add_argument('-c', '--chunk-size', type=int, default=256, help=(
        'Number of passwords loaded into memory per thread cycle. After each '
        'password of the chunk has been depleted a status update will be '
        'printed to the console with the attempted password. Default: 256'))

    args.add_argument('-q', '--quiet', '--stfu', action='store_true', help=(
        'Runs the program in "quiet mode", meaning no status updates or other '
        'output besides the cracked password will be echoed to the terminal. '
        'By default, all logging / error messages are printed to stderr (making '
        'piping to other processes easier).'
    ), default=False)

    args.add_argument('-V', '--verbose', action='store_true', help=(
        'Runs the program in "verbose mode", this will print additional '
        'debugging information (include this output when submitting bug '
        'reports). Cannot be used in conjunction with the "--quiet" argument.'
    ), default=False)

    args = args.parse_args()

    output = args.output or args.file + '.out'
    extension = args.file.split('.')[::-1][0].lower()

    if not find_executable('steghide'):
        return error(
            'Steghide does not appear to be installed, or has not been added to '
            'your current PATH, please install it using: "apt-get install '
            'steghide -y" or by downloading it from the official code '
            'repository: http://steghide.sourceforge.net/')

    if isfile(output):
        return error(f'Output file {output!r} already exists!')

    if not isfile(args.file):
        return error(f'Input file {args.file!r} does not exist!')

    if not isfile(args.wordlist):
        return error(f'Wordlist {args.wordlist!r} does not exist!')

    if extension not in Cracker.SUPPORTED_FILES:
        return error(
            f'Unsupported file type {extension!r}! Supported '
            f'extensions: {", ".join(Cracker.SUPPORTED_FILES)}')

    if not args.quiet:
        log(f'Counting lines in wordlist..')
        line_count = wc(args.wordlist)
    else:
        line_count = None

    with open(args.wordlist, mode='rb') as wordlist:
        cracker = Cracker(
            file=args.file,
            output=output,
            line_count=line_count,
            quiet=args.quiet,
            verbose=args.verbose,
            threads=args.threads)

        if not args.quiet:
            log(
                f'Attacking file {args.file!r} '
                f'with wordlist {args.wordlist!r}..')

        cracker.run(wordlist)

    if cracker.password:
        log(f'Successfully cracked file with password: {cracker.password}')
        log(f'Tried {cracker.attempts} passwords')
        log(f'Your file has been written to: {output}')
        print(cracker.password)

    elif cracker.has_error:
        return error('Terminating due to previous exception..')

    else:
        return error('Failed to crack file, ran out of passwords.')


if __name__ == '__main__':
    exit(main() or 0)
