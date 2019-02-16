import unittest
from screen_home import ScreenHome


class TestSorting(unittest.TestCase):

    unsorted = [{'title': "the ugly"}, {'title': "exit"}, {'title': "the alphabet"}, {'title': "the ugg shit"}]
    sorted_output = [{'title': "the alphabet"}, {'title': "exit"}, {'title': "the ugg shit"}, {'title': "the ugly"}]

    def test_sort_ignore_prefix(self):

        print(self.unsorted)
        sorted_list = ScreenHome.sort_ignore_prefix(self.unsorted)
        print(sorted_list)
        self.assertEqual(sorted_list, self.sorted_output)

    def test_json_title_dict(self):
        l = [5, 'The Batman Adventures', None, None, 36, None, 'complete', '{"Annuals": {"owned_issues": [1, 2], "no_of_issues": 2}}', '10-1992', '10-1995', None, None]
        result = ScreenHome.json_loads_dict({"odd_issues": '["1a", 2]', "owned_issues": "[1,2,3]"})
        self.assertEqual(result, {'owned_issues': 'complete', 'odd_issues': ['1a', 2]})

if __name__ == '__main__':
    unittest.main()