"""Check functionality of the distribution over diagnosis times."""
import unittest

import warnings

import numpy as np
import scipy as sp

from lymph.diagnosis_times import Distribution


class FixtureMixin:
    """Mixin that provides fixtures for the tests."""

    @staticmethod
    def binom_pmf(
        support: np.ndarray,
        max_time: int = 10,
        p: float = 0.5,
    ) -> np.ndarray:
        """Binomial probability mass function."""
        if max_time <= 0:
            raise ValueError("max_time must be a positive integer.")
        if len(support) != max_time + 1:
            raise ValueError("support must have length max_time + 1.")
        if not 0.0 <= p <= 1.0:
            raise ValueError("p must be between 0 and 1.")

        return sp.stats.binom.pmf(support, max_time, p)

    def setUp(self):
        self.max_time = 10
        self.array_arg = np.random.uniform(size=self.max_time + 1, low=0.0, high=10.0)
        self.func_arg = lambda support, p=0.5: self.binom_pmf(support, self.max_time, p)


class DistributionTestCase(FixtureMixin, unittest.TestCase):
    """Test the distribution dictionary."""

    def test_frozen_distribution_without_max_time(self):
        """Test the creation of a frozen distribution without providing a max time."""
        dist = Distribution(self.array_arg)
        self.assertFalse(dist.is_updateable)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            self.assertEqual({}, dist.get_params(as_dict=True))
        self.assertTrue(len(dist.support) == self.max_time + 1)
        self.assertTrue(len(dist.pmf) == self.max_time + 1)
        self.assertTrue(np.allclose(sum(dist.pmf), 1.0))

    def test_frozen_distribution_with_max_time(self):
        """Test the creation of a frozen distribution where we provide the max_time."""
        dist = Distribution(self.array_arg)
        self.assertFalse(dist.is_updateable)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            self.assertEqual({}, dist.get_params(as_dict=True))
        self.assertTrue(len(dist.support) == self.max_time + 1)
        self.assertTrue(len(dist.pmf) == self.max_time + 1)
        self.assertTrue(np.allclose(sum(dist.pmf), 1.0))

        self.assertRaises(ValueError, Distribution, self.array_arg, max_time=5)

    def test_updateable_distribution_without_max_time(self):
        """Test the creation of an updateable distribution without providing a max time."""
        self.assertRaises(ValueError, Distribution, self.func_arg)

    def test_updateable_distribution_with_max_time(self):
        """Test the creation of an updateable distribution where we provide the max_time."""
        dist = Distribution(self.func_arg, max_time=self.max_time)
        self.assertTrue(dist.is_updateable)

        dist.set_params(p=0.5)
        self.assertTrue(len(dist.support) == self.max_time + 1)
        self.assertTrue(len(dist.pmf) == self.max_time + 1)
        self.assertTrue(np.allclose(sum(dist.pmf), 1.0))

    def test_updateable_distribution_raises_value_error(self):
        """Check that an invalid parameter raises a ValueError."""
        dist = Distribution(self.func_arg, max_time=self.max_time)
        self.assertTrue(dist.is_updateable)
        self.assertRaises(ValueError, dist.set_params, p=1.5)
