import os
import shutil
import sys
from io import StringIO
from importlib import reload
from tempfile import NamedTemporaryFile, mkdtemp
from unittest import TestCase
from unittest.mock import patch
from contextlib import redirect_stdout, redirect_stderr
from uuid import uuid4

import stegcracker
from stegcracker import __main__ as cli, cracker, __version__, helpers

FILE = 'tests/data/tom.jpg'
FILE_MISSING = str(uuid4())
FILE_INVALID = 'tests/data/tom.php'
WORDLIST = 'tests/data/tom.txt'
WORDLIST_GZ = 'tests/data/tom.txt.gz'
WORDLIST_INVALID = 'tests/data/tom.invalid.txt'

ROCKYOU_ONLY_GZ = 'tests/data/rockyou-only-gz.txt'
ROCKYOU_EXISTS = 'tests/data/rockyou-without-gz.txt'

PASSWORD = 'TOM'


class CliTestCase(TestCase):
    wordlist = None

    def setUp(self):
        reload(cli)

    def call(self, *argv):
        stdout, stderr = StringIO(), StringIO()

        with patch.object(sys, 'argv', new=['stegcracker'] + list(argv)):
            with redirect_stdout(stdout):
                with redirect_stderr(stderr):
                    try:
                        code = cli.main()
                    except SystemExit as e:
                        code = e.code

        stdout.seek(0)
        stderr.seek(0)

        return stdout, stderr, code

    @patch.object(cracker.Cracker, 'crack')
    def test_default_no_args(self, crack):
        """Ensure a default help message when none of the operators are used"""

        stdout, stderr, code = self.call()
        self.assertIn('Copyright', stderr.read())
        self.assertEqual(crack.call_count, 0)
        self.assertNotEqual(code, 0)

    @patch.object(cracker.Cracker, 'crack')
    def test_version(self, crack):
        """Ensure calling -v or --version is possible and returns the current version number"""

        for alias in ('-v', '--version'):
            stdout, stderr, code = self.call(alias)
            stdout = stdout.read().strip()

            self.assertNotIn('Copyright', stderr.read())
            self.assertEqual(stdout, __version__)
            self.assertEqual(crack.call_count, 0)
            self.assertEqual(code, 0)

    @patch.object(cracker.Cracker, 'crack')
    def test_default_help(self, crack):
        """Ensure an extended help message when the --help flag is passed"""

        stdout, stderr, code = self.call('--help')
        self.assertIn('Copyright', stderr.read())
        self.assertEqual(crack.call_count, 0)
        self.assertEqual(code, 0)

    @patch.object(cracker.Cracker, 'crack')
    def test_default_quiet(self, crack):
        """Ensure a jpg image can be cracked"""

        for alias in ('-q', '--quiet', '--stfu'):
            stdout, stderr, code = self.call(alias)
            self.assertEqual('', stderr.read())
            self.assertEqual('', stdout.read())
            self.assertEqual(crack.call_count, 0)
            self.assertNotEqual(code, 0)

    @patch.object(cracker.Cracker, 'crack')
    def test_mutually_exclusive_args(self, crack):
        """Ensure that it's not possible to run --verbose and --quiet at the same time"""

        stdout, stderr, code = self.call('--verbose', '--quiet')
        self.assertIn('Error', stderr.read())
        self.assertEqual(crack.call_count, 0)
        self.assertNotEqual(code, 0)

    @patch.object(cli, 'find_executable', return_value=None)
    @patch.object(cracker.Cracker, 'crack')
    def test_required_executables(self, crack, find_executable):
        """Ensure that the required executables are installed"""

        stdout, stderr, code = self.call(FILE, WORDLIST)
        self.assertIn('Error', stderr.read())
        self.assertEqual(find_executable.call_count, 1)
        self.assertEqual(crack.call_count, 0)
        self.assertNotEqual(code, 0)

    @patch.object(cracker.Cracker, 'crack')
    def test_output_file_exists(self, crack):
        """Ensure that an output file cannot accidentally be overwritten"""

        with NamedTemporaryFile(prefix='stegcracker_') as output_file:
            stdout, stderr, code = self.call(FILE, WORDLIST, '--output', output_file.name)
            self.assertIn('Error', stderr.read())
            self.assertEqual(crack.call_count, 0)
            self.assertNotEqual(code, 0)

    @patch.object(cracker.Cracker, 'crack')
    def test_input_file_nonexistent(self, crack):
        """Ensure that an input file exists"""

        stdout, stderr, code = self.call(FILE_MISSING, WORDLIST)
        self.assertIn('Error', stderr.read())
        self.assertEqual(crack.call_count, 0)
        self.assertNotEqual(code, 0)

    @patch.object(cracker.Cracker, 'crack')
    def test_wordlist_file_nonexistent(self, crack):
        """Ensure that a wordlist exists"""

        stdout, stderr, code = self.call(FILE, FILE_MISSING)
        self.assertIn('Error', stderr.read())
        self.assertEqual(crack.call_count, 0)
        self.assertNotEqual(code, 0)

    @patch.object(cracker.Cracker, 'crack')
    def test_invalid_extension(self, crack):
        """Ensure only valid files can be passed to stegcracker"""

        stdout, stderr, code = self.call(FILE_INVALID, WORDLIST)
        self.assertIn('Error', stderr.read())
        self.assertEqual(crack.call_count, 0)
        self.assertNotEqual(code, 0)

    def test_successful_crack(self):
        """Ensure a file can be cracked successfully"""
        directory = mkdtemp(prefix='stegcracker_')
        file = directory + '/' + str(uuid4()) + '.txt'

        try:
            stdout, stderr, code = self.call(FILE, WORDLIST, '--output', file)
            self.assertNotIn('Error', stderr.read())
            self.assertEqual(PASSWORD, stdout.read().strip())
            self.assertEqual(code, 0)
            self.assertTrue(os.path.isfile(file))

        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_successful_quiet_crack(self):
        """Ensure a file can be cracked successfully and not echo any output besides the valid password"""
        directory = mkdtemp(prefix='stegcracker_')
        file = directory + '/' + str(uuid4()) + '.txt'

        try:
            stdout, stderr, code = self.call(FILE, WORDLIST, '--output', file, '--quiet')
            self.assertEqual('', stderr.read())
            self.assertEqual(PASSWORD, stdout.read().strip())
            self.assertEqual(code, 0)
            self.assertTrue(os.path.isfile(file))

        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_failed_crack(self):
        """Ensure that an error message is printed when no password is found"""
        directory = mkdtemp(prefix='stegcracker_')
        file = directory + '/' + str(uuid4()) + '.txt'

        try:
            stdout, stderr, code = self.call(FILE, WORDLIST_INVALID, '--output', file, '--quiet')
            self.assertNotIn('Error', stderr.read())
            self.assertEqual('', stdout.read())
            self.assertNotEqual(code, 0)
            self.assertFalse(os.path.isfile(file))

        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_failed_quiet_crack(self):
        """Ensure that no error message is printed when no password is found and --quiet is enabled"""
        directory = mkdtemp(prefix='stegcracker_')
        file = directory + '/' + str(uuid4()) + '.txt'

        try:
            stdout, stderr, code = self.call(FILE, WORDLIST_INVALID, '--output', file, '--quiet')
            self.assertEqual('', stderr.read())
            self.assertEqual('', stdout.read())
            self.assertNotEqual(code, 0)
            self.assertFalse(os.path.isfile(file))

        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_verbose_output(self):
        """Ensure the steghide output is sent to STDERR when using --verbose"""
        directory = mkdtemp(prefix='stegcracker_')
        file = directory + '/' + str(uuid4()) + '.txt'

        err_message = 'steghide: could not extract any data with that passphrase'
        suc_message = 'wrote extracted data to '

        try:
            stdout, stderr, code = self.call(FILE, WORDLIST, '--output', file, '--verbose')
            stderr = stderr.read()
            self.assertIn(err_message, stderr)
            self.assertIn(suc_message, stderr)
            self.assertEqual(PASSWORD, stdout.read().strip())
            self.assertEqual(code, 0)
            self.assertTrue(os.path.isfile(file))

        finally:
            shutil.rmtree(directory, ignore_errors=True)

    @patch.object(cracker.Cracker, 'crack')
    def test_gzipped_files_cant_be_used(self, crack):
        """Ensure if a gzipped file is passed a friendly error message is returned"""

        stdout, stderr, code = self.call(FILE, WORDLIST_GZ)
        self.assertIn('zipped', stderr.read())
        self.assertEqual(crack.call_count, 0)
        self.assertNotEqual(code, 0)

    @patch.object(cracker, 'Popen', side_effect=ValueError('Sample error'))
    @patch.object(cracker.ThreadPool, 'terminate')
    def test_exception_handling_in_thread(self, terminate, popen):
        """Ensure that errors are handled gracefully inside threads"""

        directory = mkdtemp(prefix='stegcracker_')
        file = directory + '/' + str(uuid4()) + '.txt'

        issue_url = stegcracker.__url__ + '/issues'

        try:
            stdout, stderr, code = self.call(FILE, WORDLIST, '--output', file, '--verbose')
            self.assertIn(issue_url, stderr.read())
            self.assertEqual('', stdout.read())
            self.assertNotEqual(code, 0)
            self.assertFalse(os.path.isfile(file))
            self.assertGreater(popen.call_count, 0)
            self.assertGreater(terminate.call_count, 0)

        finally:
            shutil.rmtree(directory, ignore_errors=True)

    @patch.object(helpers, 'check_output')
    def test_print_diagnostic_info_subprocess_error(self, check_output):
        """Subprocess errors in print diagnostic info should return 'unknown' strings"""

        check_output.side_effect = helpers.SubprocessError

        output = StringIO()

        with redirect_stderr(output):
            helpers.print_diagnostic_info()

        output.seek(0)

        self.assertIn('unknown', output.read(), msg=(
            'Expected "unknown" to be in the error output.'))

    def test_uses_rockyou_by_default(self):
        with patch.object(cli, 'DEFAULT_WORDLIST_PATH', new=FILE_MISSING):
            stdout, stderr, code = self.call(FILE)
            self.assertNotEqual(code, 0, msg='Wordlist should not exist on the system')

        with patch.object(cli, 'DEFAULT_WORDLIST_PATH', new=ROCKYOU_ONLY_GZ):
            stdout, stderr, code = self.call(FILE)
            self.assertNotEqual(code, 0, msg='Wordlist should exist on the system, but gzipped')

        # Should be successful
        directory = mkdtemp(prefix='stegcracker_')
        file = directory + '/' + str(uuid4()) + '.txt'

        try:
            with patch.object(cli, 'DEFAULT_WORDLIST_PATH', new=WORDLIST):
                stdout, stderr, code = self.call(FILE, '--output', file)
                self.assertEqual(code, 0, msg='Wordlist should exist on the system (and use the default)')

            self.assertTrue(os.path.isfile(file))

        finally:
            shutil.rmtree(directory, ignore_errors=True)
