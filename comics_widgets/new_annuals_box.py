from comics_widgets.comics_widgets import Label, NumericProperty, OptionProperty, StringProperty
from comics_widgets.new_issues_box import IssuesBox, IssueRowBox, NewIssueToggleButton
from re import match


class AnnualsBox(IssuesBox):

    # local properties
    form_label = StringProperty('Add annuals')
    default_text = "Enter year range(s). Entering more complex ranges is also possible, eg. " \
                   "1981-1984, 1-3, 1988, 4, 1990-1995"
    info_window_status = OptionProperty('close', options=['open', 'close'])
    item_counter = NumericProperty(0)

    # container variables
    total_cols = 5

    def load_issues(self, input_text):

        # remove any issues
        self.clear_issues_container()

        print("{}: loading issues".format(self.__class__.__name__))

        if '-' in input_text or ',' in input_text:  # TODO why is it necessary to write input_text twice?
            issues = self.parse_range(input_text)
        else:
            issues = self.parse_single_value(input_text)

        print(issues)

        self.populate_issue_container(issues)

    @staticmethod
    def parse_range(input_text):
        """ Return a list of ints from a range
            eg: '1-3'            returns [1, 2, 3]
                '1981-1983'      returns [1981, 1982, 1983]
                '1-2, 1983-1985, 3-5' returns [1, 2, 1983, 1984, 1985, 3, 4, 5]
        """
        print("{}.parse_range({})".format(__class__.__name__, input_text))

        # regex matches
        single_number = r'^-?\d{0,3}$'
        single_year = r'^(19|20)\d{2}$'
        range_number = r'^\d{1,3}\s*-\s*[1-9]\d{0,2}$'
        range_year = r'^(19|20)\d{2}\s*-\s*(19|20)\d{2}$'

        issue_list = [i.strip() for i in input_text.split(',')]
        issues = []

        for i in issue_list:
            if match(single_number, i) or match(single_year, i):
                try:
                    issues.append(int(i))
                except ValueError:
                    pass
            elif match(range_year, i) or match(range_number, i):
                start, end = sorted(i.split('-'), key=lambda a: int(a.strip()))
                issues += [j for j in range(int(start), int(end) + 1)]

        return issues

    @staticmethod
    def parse_single_value(input_text):
        """ Return an issue list with values from 1 - n, from a numeric string or int (user_input) """
        print("{}.parse_single_value({})".format(__class__.__name__, input_text))
        try:
            if match(r'^[1-9]\d{0,2}$', input_text):
                return [j for j in range(1, int(input_text) + 1)]
            else:
                return [int(input_text)]
        except ValueError:
            return []

    def populate_issue_container(self, issues):
        """ Add issue buttons to issues container box """

        self.current_row = IssueRowBox()

        for i in issues:
            self.issues_dict[i] = {}
            new_btn = NewIssueToggleButton(i, self, self.issues_container)
            self.current_row.add_widget(new_btn)
            self.item_counter += 1
            self.issues_button_dict[i] = new_btn

        padding = self.total_cols - len(issues) % self.total_cols
        if 0 < padding < 5:
            for p in range(padding):
                self.current_row.add_widget(Label(text='', size_hint=(1, None)))
                self.item_counter += 1

