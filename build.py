import os
import sys
import logging
from collections import namedtuple
from pynt import task
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import time
import pexpect

root = logging.getLogger()
root.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

SOURCE_FOLDERS = ['src']


@task()
def flake():
    print('flake8 check')
    result = _execute_sh('flake8 src')
    if result.exitstatus != 0:
        print_result_text('Flake errors detected, see above', ShColor.FAIL)
    else:
        print_result_text('Flake check passed', ShColor.OKGREEN)


@task(flake)
def test(test_identifier=None):
    """Runs our unit tests"""
    # UNIT_TESTING environment variable changes some decorators
    # to be pass throughs
    os.environ['UNIT_TESTING'] = 'unit testing'
    # jumping through a few hoops to getting coloured text printed out
    if test_identifier is None:
        # Discover tests in all of the source folders
        src_args = []
        for folder in SOURCE_FOLDERS:
            src_args.append('-s {0}'.format(folder))
        test_str = ' '.join(src_args)
    else:
        print('Running with test identifier : ' + test_identifier)
        test_str = test_identifier

    result = _execute_sh('py.test {0} --junitxml=test_results/junit_results.xml'.format(test_str))

    # Report to the outside world that the tests have failed
    if result.exitstatus != 0:
        exit(result.exitstatus)


def create_observer(handler, path):
    observer = Observer()
    observer.schedule(handler, path, recursive=True)
    return observer


@task()
def watchtest(test_identifier=None):
    '''Watching files for changes and runs tests'''

    class WatchTestsEventHandler(PatternMatchingEventHandler):
        patterns = ["*.py"]

        def run_tests(self, event):
            # delete the pyc file
            try:
                file_to_remove = './' + event.src_path + 'c'
                os.remove(file_to_remove)
                print('Deleted pyc file ' + file_to_remove)
            except OSError:
                # it's ok if the file does not exist
                print('Failed to delete file ' + file_to_remove)
            try:
                _execute_sh("pynt 'test[{0}]'".format(test_identifier if test_identifier is not None else ''))

            except:
                root.exception('Error running tests')

        def on_modified(self, event):
            self.run_tests(event)

        def on_created(self, event):
            self.run_tests(event)

    handler = WatchTestsEventHandler()
    observers = []
    for folder in SOURCE_FOLDERS:
        observers.append(create_observer(handler, folder))

    for ob in observers:
        ob.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for ob in observers:
            ob.stop()
            ob.join()


# Utility stuff ----------------------------


class ShColor:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


ShellResult = namedtuple('ShellResult', 'output exitstatus signalstatus')


class ExecuteShellError(Exception):
    pass


# Something simple to make sure python 2 and python 3 are both handled
class StdOutBytesToFile(object):
    def write(self, str_or_bytes_to_write):
        if isinstance(str_or_bytes_to_write, str):
            return sys.stdout.write(str_or_bytes_to_write)
        return sys.stdout.write(str_or_bytes_to_write.decode(sys.stdout.encoding))

    def flush(self):
        return sys.stdout.flush()


def _execute_sh(cmd, abort_on_error=False):
    """Execute a shell command"""
    child = pexpect.spawn(cmd)

    # redirect the stdout of child to parent
    child.logfile = StdOutBytesToFile()

    child.expect(pexpect.EOF, timeout=1200)
    if child.isalive():
        child.wait()

    if abort_on_error:
        if child.exitstatus != 0:
            raise ExecuteShellError('Error executing command: {0}'.format(cmd))

    return ShellResult(output=child.before,
                       exitstatus=child.exitstatus,
                       signalstatus=child.signalstatus)


def print_result_text(text, color):
    print('{3}{0}============= {1} ============={2}'.format(color, text, ShColor.ENDC, ShColor.BOLD))
