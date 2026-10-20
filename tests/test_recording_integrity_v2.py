import unittest
import numpy as np
from src.audit_recording_integrity_v2 import compare_arrays


class SignalIdentityTests(unittest.TestCase):
    def test_all_channels_and_every_sample_are_checked(self):
        a = np.arange(30, dtype=float).reshape(3, 10)
        b = a.copy()
        b[2, -1] += 1e-6
        rows = compare_arrays(a, b, ["core1", "core2", "noncore"])
        self.assertTrue(rows[0]["exactly_equal"])
        self.assertFalse(rows[2]["exactly_equal"])
        self.assertEqual(rows[2]["equal_samples"], 9)
        self.assertGreater(rows[2]["pearson_correlation"], .999)

    def test_constant_identical_channels_and_invalid_shapes(self):
        rows = compare_arrays(np.ones((1, 10)), np.ones((1, 10)), ["constant"])
        self.assertTrue(rows[0]["exactly_equal"])
        self.assertIsNone(rows[0]["pearson_correlation"])
        with self.assertRaises(ValueError):
            compare_arrays(np.ones((1, 10)), np.ones((1, 9)), ["constant"])
