Super simple python project scaffolding

Step 1.
Create VirtualEnv in project base folder:

virtualenv VirtualEnv

Step 2.
Activate your VirtualEnv

source VirtualEnv/bin/activate

Step 3. 
Install development requirements

pip install -r pip_requirements_dev.txt

Step 4.
Run the watch test task

pynt watchtest

Step 5.
Add some code to src


The  build task will watch your python files and run unit tests when a change is detected.

Test files need to have 'test' in the file name e.g. some_module_test.py

Test methods need to start with the word 'test' e.g.


import unittest

class SomethingTestCase(unittest.TestCase):

    def test_some_stuff(self):
        pass

Is the minimum passing test case.

Enjoy!