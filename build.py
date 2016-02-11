import os
import sys
import logging
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
    print 'flake8 check'
    result = execute_sh('flake8 src')
    print result
    if result:
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
    ALL_TESTS = '-s wts_core -s wts_web -s background_worker -s minestar'
    if test_identifier is None:
        # Discover tests in all of the source folders
        src_args = []
        for folder in SOURCE_FOLDERS:
            src_args.append('-s {0}'.format(folder))
        test_str = ' '.join(src_args)
    else:
        print 'Running with test identifier : ' + test_identifier
        test_str = test_identifier

    result = execute_sh('py.test {0} --junitxml=test_results/junit_results.xml'.format(test_str))
    print result


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
                print 'Deleted pyc file ' + file_to_remove
            except OSError:
                # it's ok if the file does not exist
                print 'Failed to delete file ' + file_to_remove
            try:
                result = execute_sh("pynt 'test[{0}]'".format(test_identifier if test_identifier is not None else ''))
                print result

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


def execute_sh(cmd):
    '''Execute a shell command'''
    child = pexpect.spawn(cmd)
    child.expect(pexpect.EOF)
    return child.before


def print_result_text(text, color):
    print '{3}{0}============= {1} ============={2}'.format(color, text, ShColor.ENDC, ShColor.BOLD)
