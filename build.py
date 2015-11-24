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
def test():
    '''Runs our unit tests'''
    # jumping through a few hoops to getting coloured text printed out
    result = execute_sh('py.test -s src')
    print result


@task()
def watchtest():
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
                result = execute_sh('pynt test')
                print result

            except:
                root.exception('Error running tests')

        def on_modified(self, event):
            self.run_tests(event)

        def on_created(self, event):
            self.run_tests(event)

    observer = Observer()
    observer.schedule(WatchTestsEventHandler(), 'src', recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

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
