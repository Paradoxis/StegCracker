import shutil
import sys
from itertools import zip_longest, islice
from subprocess import Popen, PIPE
from traceback import print_tb
from typing import Iterable
from threading import BoundedSemaphore
from multiprocessing.pool import ThreadPool

from stegcracker import __url__
from stegcracker.helpers import error, b2s, b2s_file


class Cracker:
    SUPPORTED_FILES = ('jpg', 'jpeg', 'bmp', 'wav', 'au')

    def __init__(self, file: str, output: str, line_count: int,
                 threads: int = 8, chuck_size: int = 32, quiet: bool = False,
                 verbose: bool = False):
        """
        Cracker constructor
        :param threads: Number of threads to attempt to crack the signature
        :param file: File to (attempt) to crack
        :param output: Output file to write the file to
        :param chuck_size: Number of passwords to attempt per thread
        """
        self.lock = BoundedSemaphore()
        self.pool = ThreadPool(processes=threads)
        self.thread_count = threads

        self.quiet = quiet
        self.verbose = verbose
        self.file = file
        self.output = output
        self.chunk_size = chuck_size
        self.line_count = line_count or 1
        self.has_error = False
        self.iterable = None

        self.attempts = 0
        self.password = None

    def run(self, iterable: Iterable[str]):
        """Run the brute-forcer by iterating over a set of strings"""
        self.iterable = iterable

        for i in range(self.thread_count):
            self.pool.apply_async(self.crack, args=[i + 1], error_callback=self.error_handler)

        self.pool.close()
        self.pool.join()

    def error_handler(self, exc):
        """
        Error callback handler for thread related issues
        :param exc: Exception
        :return: None
        """
        error(
            f'Unhandled exception in cracker thread. Please report this issue '
            f'on the official bug tracker: "{__url__}/issues" and don\'t forget '
            f'to include the following traceback:')

        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        print_tb(exc.__traceback__, file=sys.stderr)
        self.has_error = True
        self.pool.terminate()

    def passwords(self):
        self.lock.acquire()
        passwords = list(islice(self.iterable, self.chunk_size))
        self.lock.release()
        return passwords

    def crack(self, thread_id):
        """Attempt to crack a number of passwords"""
        attempts = 0
        password = ''
        passwords = self.passwords()
        thread_id = str(thread_id).rjust(len(str(self.thread_count)), '0')

        while any(passwords) and not self.password and not self.has_error:
            for password in passwords:
                if isinstance(password, bytes):
                    password = b2s(password)

                attempts += 1

                with Popen([
                    'steghide',
                    'extract',
                    '-sf', self.file,
                    '-xf', self.output,
                    '-p', password,
                    '-f'
                ], stdout=PIPE, stderr=PIPE) as proc:
                    proc.wait()

                    if self.verbose:
                        self.lock.acquire()
                        sys.stderr.write(f'[Thread {thread_id}]: ')
                        shutil.copyfileobj(b2s_file(proc.stderr), sys.stderr)
                        shutil.copyfileobj(b2s_file(proc.stdout), sys.stderr)
                        self.lock.release()

                if proc.returncode == 0:
                    self.password = password
                    self.pool.terminate()
                    break

            if not self.quiet:
                self.lock.acquire()

                self.attempts += attempts
                percentage = self.attempts * 100 / self.line_count

                print((
                    f"{self.attempts}/{self.line_count} ({percentage:.2f}%) "
                    f"Attempted: {password[0:20]}".strip()
                ), end='\r', flush=True, file=sys.stderr)

                self.lock.release()

            passwords = self.passwords()