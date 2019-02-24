import unittest
from screen_home import ScreenHome
from issues_box import IssuesBox


class TestSorting(unittest.TestCase):

    unsorted = [{'title': "the ugly"}, {'title': "exit"}, {'title': "the alphabet"}, {'title': "the ugg shit"}]
    sorted_output = [{'title': "the alphabet"}, {'title': "exit"}, {'title': "the ugg shit"}, {'title': "the ugly"}]

    def test_sort_ignore_prefix(self):

        print(self.unsorted)
        sorted_list = ScreenHome.sort_ignore_prefix(self.unsorted)
        print(sorted_list)
        self.assertEqual(sorted_list, self.sorted_output)

    # def test_json_title_dict(self):
    #     l = [5, 'The Batman Adventures', None, None, 36, None, 'complete', '{"Annuals": {"owned_issues": [1, 2], "no_of_issues": 2}}', '10-1992', '10-1995', None, None]
    #     result = ScreenHome.json_loads_dict({"odd_issues": '["1a", 2]', "owned_issues": "[1,2,3]"})
    #     self.assertEqual(result, {'owned_issues': 'complete', 'odd_issues': ['1a', 2]})

    def test_get_issues_dict(self):
        print('\ntesting issue loading')

        standard_dict = {1: '1',
                         2: '2',
                         3: '3'}

        print('testing \'3\'')
        issue_range = '3'
        result = IssuesBox.parse_issue_ranges(IssuesBox, issue_range)
        self.assertEqual(result, (standard_dict, False))

        print('testing \'3+\'')
        issue_range = '3+'
        result = IssuesBox.parse_issue_ranges(IssuesBox, issue_range)
        self.assertEqual(result, (standard_dict, True))

        print('testing \'1-3\'')
        issue_range = '1-3'
        result = IssuesBox.parse_issue_ranges(IssuesBox, issue_range)
        self.assertEqual(result, (standard_dict, False))

        print('testing \'1-3+\'')
        issue_range = '1-3+'
        result = IssuesBox.parse_issue_ranges(IssuesBox, issue_range)
        self.assertEqual(result, (standard_dict, True))

        print('testing \'3, 5-7\'')
        issue_range = '3, 5-7'
        standard_dict = {3: '3', 5: '5', 6: '6', 7: '7'}

        result = IssuesBox.parse_issue_ranges(IssuesBox, issue_range)
        self.assertEqual(result, (standard_dict, False))

        standard_dict = {}

        print('testing \'0, -1, -1.5\'')
        issue_range = {'0': {**standard_dict, **{0: '0'}},
                       '-1': {**standard_dict, **{-1: '-1'}},
                       '-1.5': {**standard_dict, **{-1.5: '-1.5'}},
                       '-1.25': {**standard_dict, **{-1.25: '-1.25'}},
                       '-1, -1.5, -1.25': {**standard_dict, **{-1: '-1', -1.5: '-1.5', -1.25: '-1.25'}}
                       }
        for k, v in issue_range.items():
            print(k, v)
            standard_dict = v
            print('testing {}'.format(k))
            result = IssuesBox.parse_issue_ranges(IssuesBox, k)
            self.assertEqual(result, (standard_dict, False))
            standard_dict['odd'] = {}

if __name__ == '__main__':
    unittest.main()