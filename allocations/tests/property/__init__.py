from unittest import TestCase

from hypothesis import given, strategies as st

class HypothesisSetUp(TestCase):
    """Confirms that property based tests are installed and discovered"""

    @given(st.lists(st.integers()))
    def test_sorting_twice_changes_nothing(self, numbers):
        once = sorted(numbers)
        self.assertEqual(sorted(once), once)