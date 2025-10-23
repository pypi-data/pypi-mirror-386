"""Make doctests in the lymph package discoverable by unittest."""

import doctest
import unittest

from lymph import diagnosis_times, graph, matrix, modalities, utils
from lymph.models import bilateral, unilateral


def load_tests(loader, tests: unittest.TestSuite, ignore):
    """Load doctests from the lymph package."""
    tests.addTests(doctest.DocTestSuite(diagnosis_times))
    tests.addTests(doctest.DocTestSuite(graph))
    tests.addTests(doctest.DocTestSuite(utils))
    tests.addTests(doctest.DocTestSuite(matrix))
    tests.addTests(doctest.DocTestSuite(modalities))

    tests.addTests(doctest.DocTestSuite(unilateral))
    tests.addTests(doctest.DocTestSuite(bilateral))
    return tests
