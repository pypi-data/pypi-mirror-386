import os
import shutil
import subprocess
import sys
from typing import Callable
from unittest import TestCase, TestSuite

from launchable.testpath import TestPath


def get_java_command():
    if shutil.which("java"):
        return "java"

    if os.access(os.path.expandvars("$JAVA_HOME/bin/java"), os.X_OK):
        return os.path.expandvars("$JAVA_HOME/bin/java")

    return None


def cygpath(p):
    # When running in Cygwin ported Python (as opposed to Windows native Python), the paths we deal with are in
    # the cygwin format. But when we invoke Windows native Java (and there's no Cygwin ported Java), those parameters
    # need to be in the Windows path format.
    #
    # In Cygwin aware world, it is always the responsibility of the Cygwin process calling Windows native process to
    # do this conversion, so here we are.
    #
    # Cygwin ported Python is not to be confused with Windows native Python running in Windows with cygwin.
    # So tests like CYGWIN env var, "uname" are incorrect.
    if sys.platform == 'cygwin':
        p = subprocess.check_output(['cygpath', '-w', p]).decode().strip()
    return p


def junit5_nested_class_path_builder(
        default_path_builder: Callable[[TestCase, TestSuite, str], TestPath]) -> Callable[[TestCase, TestSuite, str], TestPath]:
    """
    Creates a path builder function that handles JUnit 5 nested class names.

    With @Nested tests in JUnit 5, test class names have inner class names
    like com.launchableinc.rocket_car.NestedTest$InnerClass.
    It causes a problem in subsetting because Launchable CLI can't detect inner classes in subsetting.
    So, we need to ignore the inner class names. The inner class name is separated by $.
    Note: Launchable allows $ in test paths. But we decided to remove it in this case
          because $ in the class name is not a common case.

    Args:
        default_path_builder: The original path builder function to wrap

    Returns:
        A function that wraps the default path builder and handles nested class names
    """
    def path_builder(case: TestCase, suite: TestSuite, report_file: str) -> TestPath:
        test_path = default_path_builder(case, suite, report_file)
        return [{**item, "name": item["name"].split("$")[0]} if item["type"] == "class" else item for item in test_path]

    return path_builder
