import unittest
from screen_home import ScreenHome


class TestSorting(unittest.TestCase):

    unsorted = [(1, "the ugly"), (2, "The Babe"), (3, "United States"), (4, "The Apple"), (5, "Tank Driver")]
    sorted_output = [4, 2, 5, 3, 1]

    def test_true_sort(self):

        sorted_list = ScreenHome.true_sort(self.unsorted)
        self.assertEqual(sorted_list, self.sorted_output)

    def test_sort_ignore_prefix(self):

        sorted_list = ScreenHome.sort_ignore_prefix(self.unsorted)
        self.assertEqual(sorted_list, self.sorted_output)


if __name__ == '__main__':
    unittest.main()