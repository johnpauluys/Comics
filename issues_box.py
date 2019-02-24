from kivy.lang import Builder

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.properties import ObjectProperty, OptionProperty, StringProperty

from re import match

Builder.load_file('issues_box.kv')


class IssuesBox(BoxLayout):

    status_bar = ObjectProperty()

    def load_issues(self, issues_container, issue_ranges, data_issues_dict):
        """ Load standard issues based on what user entered """

        issues_dict, ongoing_series = self.parse_issue_ranges(issue_ranges)

        if issues_dict:

        #TODO CONTINUE HERE

            # clear standard issue container
            issues_container.clear_widgets()
            # add issue toggle buttons to container
            self.populate_issue_container(issues_container, issues_dict)
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

                    issues_dict[float(i)] = i
                else:
                    errors.append(i)
                    self.status_bar.set_status('The following range(s) caused problems: "{}".'.format(', '.join(errors)),
                                               'error')
                    print("not caught by regex: {}".format(i))

        if not issues_dict:
            self.status_bar.set_status('"{}" couldn\'t be parsed. Please check input again.'.format(issue_ranges),
                                       'error')
        return issues_dict, on_going

    def pad_issues(self, std_issues_dict):
        """ Return a list of issues and empty slots, keeping the standard format of n(1-10) per row """

        # set empty list to return
        padded_issues = []

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

    def populate_issue_container(self, container, issues_dict):
        """ Add issue buttons to issues container box """

        pre = sorted(i for i in issues_dict if i <= 0)
        std = sorted(i for i in issues_dict if i > 0)
        if pre:
            for i in range(10 - len(pre) % 10):
                container.add_widget(Label(text='', size_hint=(1, None)))
            for i in pre:
                new_btn = IssueToggleButton(container, issues_dict, text=issues_dict[i])
                container.add_widget(new_btn)
        #
        if std:
            for i in self.pad_issues(std):
                if i == '':
                    container.add_widget(Label(text='', size_hint=(1, None)))
                else:
                    new_btn = IssueToggleButton(container, issues_dict, text=issues_dict[i])
                    container.add_widget(new_btn)



        # fill the first spots with blank, if necessary


        # if issue_list == self.standard_issues and issue_list[0] != 1:
        # if issues_dict == self.standard_issues:
        #
        #     for i in range(issues_dict[0] - 1 % 10):
        #         container.add_widget(Label(size_hint=(1, 1)))
        #
        # for i in issues_dict:
        #     # create button
        #     new_issue_toggle = IssueToggleButton(container, self.data, text=str(i))
        #     # check whether it should be in a down state
        #     if i in self.data['owned_issues']:
        #         new_issue_toggle.state = 'down'
        #     # add button to container
        #     container.add_widget(new_issue_toggle)
        #
        # if self.ongoing_series:
        #     container.add_widget(Label(size_hint=(1, 1), text='. . .'))
        #
        # # fill up empty space to make it took prettier
        # if len(issues_dict) + int(self.ongoing_series) < 10:
        #     for i in range(10 - len(issues_dict) % 10):
        #         container.add_widget(Label(size_hint=(1, 1)))


class IssueToggleButton(ToggleButton):

    owned = OptionProperty(0, options=[0, 1])


    def __init__(self, container, data_issues, **kwargs):
        super(IssueToggleButton, self).__init__(**kwargs)
        self.container = container
        self.data = data_issues

    def on_state(self, instance, value):
        self.owned = 1 if value == 'down' else 0
        if self.owned:
            print('You own Issue #{}'. format(self.text))

    def on_touch_down(self, touch):

        if self.collide_point(*touch.pos):
            print(self.text)
            if touch.is_double_tap:
                print('double_tap')
                # self.reverse_state()
                indx = self.parent.children.index(self) + (0 - (self.parent.children.index(self) % 10))

                print(self.parent.children[indx].pos)
                issue_info = IssueInfo(self.parent.children[indx].pos)
                self.parent.add_widget(issue_info)

            else:
                self.reverse_state()
                print('no_double_tap')
        else:
            return super().on_touch_down(touch)

    def on_touch_up(self, touch):

        if touch.grab_current is self:
            print('grabbed', touch)
            touch.ungrab(self)

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

class IssueInfo(BoxLayout):

    def __init__(self, position, **kwargs):
        super(IssueInfo, self).__init__(**kwargs)
        self.pos = position
        print(self.pos)
