import unittest
from screen_home import ScreenHome
from issues_box import IssuesBox, IssueInfoBox


class TestSorting(unittest.TestCase):

    unsorted = [{'title': "the ugly"}, {'title': "exit"}, {'title': "the alphabet"}, {'title': "the ugg shit"}]
    sorted_output = [{'title': "the alphabet"}, {'title': "exit"}, {'title': "the ugg shit"}, {'title': "the ugly"}]

    def test_sort_ignore_prefix(self):

        sorted_list = ScreenHome.sort_ignore_prefix(self.unsorted)
        self.assertEqual(sorted_list, self.sorted_output)

    def test_get_issues_dict(self):

        standard_dict = {1: {'owned': 0},
                         2: {'owned': 0},
                         3: {'owned': 0}}

        # print('testing \'3\'')
        issue_range = '3'
        result = IssuesBox.parse_issue_ranges(IssuesBox, issue_range)
        self.assertEqual(result, (standard_dict, False))

        # print('testing \'3+\'')
        issue_range = '3+'
        result = IssuesBox.parse_issue_ranges(IssuesBox, issue_range)
        self.assertEqual(result, (standard_dict, True))

        # print('testing \'1-3\'')
        issue_range = '1-3'
        result = IssuesBox.parse_issue_ranges(IssuesBox, issue_range)
        self.assertEqual(result, (standard_dict, False))

        # print('testing \'1-3+\'')
        issue_range = '1-3+'
        result = IssuesBox.parse_issue_ranges(IssuesBox, issue_range)
        self.assertEqual(result, (standard_dict, True))

        # print('testing \'3, 5-7\'')
        issue_range = '3, 5-7'
        standard_dict = {3: {'owned': 0}, 5: {'owned': 0}, 6: {'owned': 0}, 7: {'owned': 0}}

        result = IssuesBox.parse_issue_ranges(IssuesBox, issue_range)
        self.assertEqual(result, (standard_dict, False))

        standard_dict = {}

        # print('testing \'0, -1, -1.5\'')
        issue_range = {'0': {**standard_dict, **{0: {'owned': 0}}},
                       '-1': {**standard_dict, **{-1: {'owned': 0}}},
                       '-1.5': {**standard_dict, **{-1.5: {'owned': 0}}},
                       '-1.25': {**standard_dict, **{-1.25: {'owned': 0}}},
                       '-1, -1.5, -1.25': {**standard_dict, **{-1: {'owned': 0}, -1.5: {'owned': 0}, -1.25: {'owned': 0}}}
                       }

    def test_convert_string_index(self):

        input_output = [('2nd Copy', 'copy02'),
                        ('Variant', 'variant01')]

        for i in input_output:

            result = IssueInfoBox.convert_string_key(IssueInfoBox, i[0])
            self.assertEqual(i[1], result)

    def test_convert_key_string(self):

        input_output = [('2nd Copy', 'copy02'),
                        ('Variant', 'variant01')]

        for i in input_output:

            result = IssueInfoBox.convert_key_string(IssueInfoBox, i[1])
            self.assertEqual(i[0], result)


if __name__ == '__main__':
    unittest.main()