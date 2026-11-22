from unittest import TestCase
from hypothesis import given, strategies as st

class HypothesisTests(TestCase):
    """confirms that property based tests are installed and discovered"""

    @given(st.lists(st.integers()))
    def test_sorting_twice_changes_nothing(self, nums):
        once = sorted(nums)
        self.assertEqual(sorted(once), once)