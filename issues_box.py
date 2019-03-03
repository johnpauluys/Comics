from kivy.lang import Builder
from kivy.properties import DictProperty, NumericProperty, ObjectProperty, OptionProperty, StringProperty
from comics_widgets import BoxLayout, FieldBox, Label, TextButton, ToggleButton
from re import match

Builder.load_file('issues_box.kv')


class IssuesBox(BoxLayout):

    issues_container = ObjectProperty()
    current_box = ObjectProperty()
    status_bar = ObjectProperty()
    issue_counter = NumericProperty(0)
    info_window_status = OptionProperty('closed', options=['open', 'closed'])

    def on_issue_counter(self, instance, value):

        if value % 10 == 0:
            self.issues_container.add_widget(self.current_box)
            self.current_box = IssueRowBox()

    def on_info_window_status(self, instance, value):
        print("issue info window {}".format(value))
        for child in self.issues_container.children:
            child.disabled = True if child.height != 0 and value == 'open' else False

    def load_issues(self, issue_ranges, data_issues_dict):
        """ Load standard issues based on what user entered """

        issues_dict, ongoing_series = self.parse_issue_ranges(issue_ranges)

        if issues_dict:

            # clear standard issue container
            self.issues_container.clear_widgets()
            self.issue_counter = 0
            self.current_box = IssueRowBox()
            # add issue toggle buttons to container
            self.populate_issue_container(issues_dict)
            # self.current_box = IssueContainerBox()
            # self.add_widget(self.current_box)
        # # focus on next widget
        # if self.standard_issues_text.focus:
        #     self.standard_issues_text.get_focus_next().focus = True
        # # check whether odd issues were somehow already entered and populate if necessary
        # if self.odd_issues_text.text:
        #     self.load_odd_issues(self.status_bar)
        # return True

    def parse_issue_ranges(self, issue_ranges):

        print('parsing: {}'.format(issue_ranges))

        issues_dict = {}
        on_going = False
        errors = []

        if match(r'^[1-9]\d{0,2}\+?$', issue_ranges):
            i = issue_ranges
            # check for ongoing series
            if i.endswith('+'):
                on_going = True
                i = i[:-1]

            issues_dict = {**issues_dict, **{k: str(k) for k in range(1, int(i) + 1)}}
        else:
            for i in [r.strip() for r in issue_ranges.split(',')]:
                # handle single numbers and 0
                if match(r'^\d{1,3}$', i):

                    issues_dict[int(i)] = i

                # handle ranges eg. 1-20, 22-24, 28-30+
                elif match(r'^\d{1,3}[\-]\d{1,3}\+?$', i):

                    # check for ongoing series
                    if i.endswith('+'):
                        on_going = True
                        i = i[:-1]

                    start, end = sorted(int(n) for n in i.split('-'))
                    issues_dict = {**issues_dict, **{k: str(k) for k in range(start, end + 1)}}

                # handle single negative values, eg. -1, -1.25 and 0
                elif match(r'^-\d{1,3}(.\d{1,2})?$', i):

                    issues_dict[float(i) if '.' in i else int(i)] = i
                else:
                    errors.append(i)
                    self.status_bar.set_status('The following range(s) caused problems: "{}".'.format(', '.join(errors)),
                                               'error')
                    print("not caught by regex: {}".format(i))

        if not issues_dict:
            self.status_bar.set_status('"{}" couldn\'t be parsed. Please check input again.'.format(issue_ranges),
                                       'error')
        return issues_dict, on_going

    def pad_issues(self, std_issues_dict, pre_issues_entered=False):
        """ Return a list of issues and empty slots, keeping the standard format of n(1-10) per row """

        # set empty list to return
        padded_issues = []
        # TODO user entries like -1, 20 don't behave as expected
        # TODO has to do with 20 % 10 returning 0

        # handle multiple lists
        if std_issues_dict[-1] != len(std_issues_dict):
            # split issues into groups, eg [1, 2, 3, "", 5, "", "", 8]
            split_list, last_group = self.group_issues(std_issues_dict)

            for k, group in split_list.items():
                # pad first slots, if necessary
                if not padded_issues:
                    padded_issues += ['' for _ in range(group[0] % 10 - 1)]
                else:
                    # get difference between first value of
                    # current group and last value of prev group
                    diff = group[0] - split_list[k-1][-1]
                    if diff >= 10:
                        # insert line between big gaps
                        padded_issues += [''] * 10
                    # pad regular gaps
                    padded_issues += ['' for _ in range(diff % 10 - 1)]
                # append issues
                padded_issues += [i for i in group]
            # append padding after issues
            padded_issues += ['' for _ in range((10 - split_list[last_group][-1]) % 10)]
        else:
            # handle a single value, like 20
            print('single value')
            padded_issues = [i for i in std_issues_dict] + [''] * (10 - len(std_issues_dict) % 10)

        print('padded_issues:', padded_issues)
        return padded_issues

    def group_issues(self, std_issues_dict):
        """ Return a list of groups of issues eg. [1, 2, 3, "", 5, "", "", 8]
            The quotation marks will be used as empty blocks, where issues don't exist"""
        # split list in to groups
        split_list = {}
        # set counter used to split issues into groups
        counter = 0
        # set prev to first issue, used to check for gaps
        prev = std_issues_dict[0]
        for i in range(std_issues_dict[-1] + 1):
            # iterate over all possible issues, determined by highest issue
            if i in std_issues_dict:
                # if iteration reaches an issue that exists in range,
                # but isn't one value higher than the prev, increment list counter
                if prev != i - 1:
                    counter += 1
                # prepare prev for next iteration
                prev = i
                # set new key (section), if necessary
                split_list.setdefault(counter, [])
                # append issue to group
                split_list[counter].append(i)
        return split_list, counter


    def populate_issue_container(self, issues_dict):
        """ Add issue buttons to issues container box """

        pre = sorted(i for i in issues_dict if i <= 0)
        std = sorted(i for i in issues_dict if i > 0)
        print('standard issues: {}'.format(std))
        self.issue_counter = 0
        self.issues_container.clear_widgets()

        if pre:
            for i in range(10 - len(pre) % 10):
                self.current_box.add_widget(Label(text='', size_hint=(1, None)))
                self.issue_counter += 1
            for i in pre:
                new_btn = IssueToggleButton(self, self.issues_container, issues_dict, text=issues_dict[i])
                self.current_box.add_widget(new_btn)
                self.issue_counter += 1

        if std:
            for i in self.pad_issues(std, bool(pre)):
                if i == '':
                    self.current_box.add_widget(Label(text='', size_hint=(1, None)))
                    self.issue_counter += 1
                else:
                    new_btn = IssueToggleButton(self, self.issues_container, issues_dict, text=issues_dict[i])
                    self.current_box.add_widget(new_btn)
                    self.issue_counter += 1


class IssueToggleButton(ToggleButton):

    owned = OptionProperty(0, options=[0, 1])
    issues_box = ObjectProperty()

    def __init__(self, issues_box, issues_container, data_issues, **kwargs):
        super(IssueToggleButton, self).__init__(**kwargs)
        self.issues_box = issues_box
        self.issues_container = issues_container
        self.data = data_issues

    def on_state(self, instance, value):
        self.owned = 1 if value == 'down' else 0
        if self.owned:
            print('You own Issue #{}'. format(self.text))

        print(self.data)


    # def on_owned(self, instance, value):
    #     if value:
    #         print(self.data[self.text])

    def on_touch_down(self, touch):

        if self.collide_point(*touch.pos):
            if self.issues_box.info_window_status == 'open':
                return False
            if touch.is_double_tap:
                self.state = 'down'
                info_index = self.issues_container.children.index(self.parent)
                info_box = IssueInfo(self.issues_box, self.issues_container, self)
                self.issues_container.add_widget(info_box, index=info_index)
                self.issues_box.info_window_status = 'open'
            else:
                self.reverse_state()
        else:
            return super().on_touch_down(touch)

    # def on_touch_up(self, touch):
    #
    #     if touch.grab_current is self:
    #         print('grabbed', touch)
    #         touch.ungrab(self)

    def reverse_state(self):
        self.state = 'down' if self.state == 'normal' else 'normal'

    # @staticmethod
    # def convert_issue_number(btn_text):
    #     """ Convert IssueToggleButton.text from string to appropriate type """
    #
    #     btn_text = btn_text.strip()
    #
    #     if match(r'^((-?[1-9]\d{0,3})|0)$', btn_text):
    #         # handle ints
    #         # print("int: {}".format(btn_text))
    #         return int(btn_text)
    #     elif match(r'^-?\d{1,4}\.\d{1,2}$', btn_text):
    #         # handle fractions
    #         # print("float: {}".format(btn_text))
    #         return float(btn_text)
    #     elif match(r'^-?\d{1,4}((\D{1,2})|((\.\d{1,2})?_((\D|\d){1,2})?))$', btn_text):
    #         # handle strings like 1a, 1_, 1_a, 1_ab, 1_a1, etc
    #         # print("str: {}".format(btn_text))
    #         return str(btn_text)
    #     else:
    #         print("no match: {}".format(btn_text))

    # def on_state(self, instance, value):
    #     """ Add or remove btn from owned issues list """
    #
    #     if value == 'down' and self.convert_issue_number(self.text) not in self.user_data['owned_issues']:
    #         self.user_data['owned_issues'].append(self.convert_issue_number(self.text))
    #     if value == 'normal' and self.convert_issue_number(self.text) in self.user_data['owned_issues']:
    #         self.user_data['owned_issues'].remove(self.convert_issue_number(self.text))


class IssueRowBox(BoxLayout):
    pass


class IssueSelector(FieldBox):
    pass


class IssueInfo(BoxLayout):

    issues_box = ObjectProperty()
    issues_container = ObjectProperty()
    issue_number = StringProperty()

    add_copy_button = ObjectProperty()
    add_variant_button = ObjectProperty()
    extra_issues = DictProperty({'copy': 1, 'variant': 0})

    def __init__(self, issues_box, issues_container, issue_widget, **kwargs):
        super(IssueInfo, self).__init__(**kwargs)
        self.issues_box = issues_box
        self.issues_container = issues_container
        self.issue_number = issue_widget.text
        self.add_copy_button.text = 'add 2nd Copy'
        self.add_variant_button.text = 'add Variant'

    def on_extra_issues(self, instance, value):
        self.add_copy_button.text = 'add {}'.format(self.nth_string('copy'))
        self.add_variant_button.text = 'add {}'.format(self.nth_string('variant'))

    def close_window(self, issue_box):
        self.issues_box.info_window_status = 'closed' if self.issues_container else None
        issue_box.remove_widget(self)

    def add_extra_box(self, box_label):
        """ Add new copy or variant box to layout """
        if 'variant' in box_label.lower():
            self.extra_issues['variant'] += 1
            extra_type = 'variant'
        elif 'copy' in box_label.lower():
            self.extra_issues['copy'] += 1
            extra_type = 'copy'
        else:
            print("ERROR: Something went wrong!")
            return False

        new_box = ExtraIssueBox(self, extra_type, box_label)
        self.add_widget(new_box, 1)

    def nth_string(self, extra_type, extra_count=None):
        """ Return a string depending on amount of extra copies. eg. '2nd copy', '3rd copy', etc"""
        print('extra_count: {}'.format(extra_count))
        extra_count = self.extra_issues[extra_type] if extra_count is None else extra_count
        if extra_count == 0:
            return '{}'.format(extra_type.title())
        elif extra_count == 1:
            n_string = '2nd'
        elif extra_count == 2:
            n_string = '3rd'
        else:
            n_string = "{}th".format(extra_count + 1)
        print('n_string: {}'.format(n_string))
        return "{} {}".format(n_string, extra_type.title())


class ExtraIssueBox(BoxLayout):

    issue_info_box = ObjectProperty()
    box_label = StringProperty()
    extra_number_label = ObjectProperty()

    def __init__(self, issue_info_box, extra_type, box_label, **kwargs):
        super(ExtraIssueBox, self).__init__(**kwargs)
        self.issue_info_box = issue_info_box
        self.extra_type = extra_type
        self.box_label = box_label

    # def on_box_label(self, instance, value):
    #     self.extra_number_label.text = self.box_label


    def remove_me(self):
        self.issue_info_box.remove_widget(self)
        self.issue_info_box.extra_issues[self.extra_type] -= 1
        self.fix_numbering()

    def fix_numbering(self):
        current_count = self.issue_info_box.extra_issues[self.extra_type]
        for c in self.issue_info_box.children:

            if isinstance(c, type(self)) and c.extra_type == self.extra_type:
                current_count -= 1

                print(current_count, c, type(c), c.extra_type)
                c.box_label = self.issue_info_box.nth_string(self.extra_type, current_count)


class AddExtraButton(TextButton):
    extra_type = StringProperty()
    issue_info_container = ObjectProperty()

    # def __init__(self, issue_info_container, **kwargs):
    #     super(ExtraToggleButton, self).__init__(**kwargs)
    #     self.issue_info_container = issue_info_container


