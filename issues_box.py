from kivy.lang import Builder
from kivy.properties import DictProperty, NumericProperty, ObjectProperty, OptionProperty, StringProperty
from comics_widgets import BoxLayout, FieldBox, Label, TextButton, ToggleButton
from re import match

Builder.load_file('issues_box.kv')


class IssuesBox(BoxLayout):

    # properties from screen_new
    screen = ObjectProperty()
    status_bar = ObjectProperty()

    # local properties
    issues_container = ObjectProperty()
    current_box = ObjectProperty()
    issue_counter = NumericProperty(0)
    info_window_status = OptionProperty('close', options=['open', 'close'])

    # data
    issues_dict = DictProperty()

    def on_info_window_status(self, instance, value):
        """ Disable/Enable all IssueRowBoxes not containing IssueInfoBoxes """
        print("issue info window {}s".format(value))
        for child in self.issues_container.children:
            child.disabled = True if not isinstance(child, IssueInfoBox) and value == 'open' else False

    def on_issue_counter(self, instance, value):
        """ Create and add a new IssueRowBox for every ten issues """
        if value % 10 == 0:
            self.issues_container.add_widget(self.current_box)
            self.current_box = IssueRowBox()

    def load_issues(self, issue_ranges):
        """ Load standard issues based on what user entered """

        self.issues_dict, self.screen.ongoing_series = self.parse_issue_ranges(issue_ranges)

        if self.issues_dict:

            # clear standard issue container
            self.issues_container.clear_widgets()
            self.issue_counter = 0
            self.current_box = IssueRowBox()
            # add issue toggle buttons to container
            self.populate_issue_container()
            # self.current_box = IssueContainerBox()
            # self.add_widget(self.current_box)
        # # focus on next widget
        # if self.standard_issues_text.focus:
        #     self.standard_issues_text.get_focus_next().focus = True
        # # check whether odd issues were somehow already entered and populate if necessary
        # if self.odd_issues_text.text:
        #     self.load_odd_issues(self.status_bar)
        # return True
        # TODO set status... tried, didn't work

    def parse_issue_ranges(self, issue_ranges):

        print('parsing string: {}'.format(issue_ranges))

        issues_dict = {}
        on_going = False
        errors = []

        if match(r'^[1-9]\d{0,2}\+?$', issue_ranges):
            i = issue_ranges
            # check for ongoing series
            if i.endswith('+'):
                on_going = True
                i = i[:-1]

            issues_dict = {**issues_dict, **{k: {'owned': 0} for k in range(1, int(i) + 1)}}
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
                    issues_dict = {**issues_dict, **{k: {'owned': 0} for k in range(start, end + 1)}}

                # handle single negative values, eg. -1, -1.25 and 0
                elif match(r'^-\d{1,3}(.\d{1,2})?$', i):

                    issues_dict[float(i) if '.' in i else int(i)] = {'owned': 0}
                else:
                    errors.append(i)
                    self.status_bar.set_status('The following range(s) caused problems: "{}".'.format(', '.join(errors)),
                                               'error')
                    print("not caught by regex: {}".format(i))

        if not issues_dict:
            self.status_bar.set_status('"{}" couldn\'t be parsed. Please check input again.'.format(issue_ranges),
                                       'error')

        print(issues_dict)
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
            padded_issues = [i for i in std_issues_dict] + [''] * (10 - len(std_issues_dict) % 10)

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

    def populate_issue_container(self):
        """ Add issue buttons to issues container box """

        pre = sorted(i for i in self.issues_dict if i <= 0)
        std = sorted(i for i in self.issues_dict if i > 0)
        self.issue_counter = 0
        self.issues_container.clear_widgets()
        print(pre)
        print(std)

        if pre:
            for i in range(10 - len(pre) % 10):
                self.current_box.add_widget(Label(text='', size_hint=(1, None)))
                self.issue_counter += 1
            for i in pre:
                new_btn = IssueToggleButton(self, self.issues_container, i)
                self.current_box.add_widget(new_btn)
                self.issue_counter += 1

        if std:
            for i in self.pad_issues(std, bool(pre)):
                if i == '':
                    self.current_box.add_widget(Label(text='', size_hint=(1, None)))
                    self.issue_counter += 1
                else:
                    new_btn = IssueToggleButton(self, self.issues_container, i)
                    self.current_box.add_widget(new_btn)
                    self.issue_counter += 1


class IssueRowBox(BoxLayout):
    pass


class IssueToggleButton(ToggleButton):

    owned = OptionProperty(0, options=[0, 1])
    issues_box = ObjectProperty()

    def __init__(self, issues_box, issues_container, issues_dict_index, **kwargs):
        super(IssueToggleButton, self).__init__(**kwargs)
        self.issues_box = issues_box
        self.issues_container = issues_container
        self.issues_dict_index = issues_dict_index
        self.text = str(issues_dict_index)

    def on_state(self, instance, value):
        self.owned = 1 if value == 'down' else 0

    def on_owned(self, instance, value):
        print('You {}own issue {}'.format("don't " if not value else '', self.text))
        self.issues_box.issues_dict[self.issues_dict_index]['owned'] = value

    def on_touch_down(self, touch):

        if self.collide_point(*touch.pos):
            if self.issues_box.info_window_status == 'open':
                return False
            if touch.is_double_tap:
                self.state = 'down'
                info_index = self.issues_container.children.index(self.parent)
                info_box = IssueInfoBox(self.issues_box, self)
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


class IssueSelector(FieldBox):
    pass


class IssueInfoBox(BoxLayout):

    issue_number = StringProperty()

    add_copy_button = ObjectProperty()
    add_variant_button = ObjectProperty()
    extra_issues = DictProperty({'copy': 1, 'variant': 0})

    notes = ObjectProperty()

    def __init__(self, issues_box, issue_widget, **kwargs):
        super(IssueInfoBox, self).__init__(**kwargs)
        self.issues_box = issues_box
        self.issues_dict_index = issue_widget.issues_dict_index
        self.issue_number = issue_widget.text
        self.add_copy_button.text = 'add 2nd Copy'
        self.add_variant_button.text = 'add Variant'
        self.load_prev_info()

    def load_prev_info(self):
        """ Load previously entered data, if any """

        # reset counters TODO this still messes up, when removing a previously added extra
        self.extra_issues['copy'] = 0 if self.extra_issues['copy'] >= 2 else 1
        self.extra_issues['variant'] = 0

        # iterate over sorted dict keys
        for i in sorted(self.issues_box.issues_dict[self.issues_dict_index]):
            print(self.extra_issues) # debugging

            # check if notes exist
            if i == 'notes':
                # add old text to notes text input field
                self.notes.text = self.issues_box.issues_dict[self.issues_dict_index][i]

            # check for copies and variants
            # TODO Don't like this and it still causes problems. Find and fix them
            elif 'copy' in i or 'variant' in i:
                # convert key to box label
                box_label = self.convert_key_string(i)
                # set extra notes text
                note = self.issues_box.issues_dict[self.issues_dict_index][i]
                # add extra box widget
                self.add_extra_box(box_label, note)

    def on_extra_issues(self, instance, value):
        """ Change text of add buttons """
        self.add_copy_button.text = 'add {}'.format(self.nth_string('copy'))
        self.add_variant_button.text = 'add {}'.format(self.nth_string('variant'))

    def close_window(self, issue_box):
        """ Remove info window """
        # set status variable to closed
        self.issues_box.info_window_status = 'close'
        # remove widget
        issue_box.remove_widget(self)

    def save_changes(self):
        """ Save changes made on issue """

        # TODO add some confirmation features

        # get rid of old info
        self.clear_extras()

        # iterate of current children
        for c in self.children:
            # find extra issue boxes and store their value into issues dict
            if isinstance(c, ExtraIssueBox):
                # convert sting to to index
                key = self.convert_string_index(c.number_label.text)
                # set user entered value to key in issues dict
                self.issues_box.issues_dict[self.issues_dict_index][key] = c.note.text

        # add notes to issues_dict
        self.issues_box.issues_dict[self.issues_dict_index]['notes'] = self.notes.text

        # close window
        self.close_window(self.parent)

    def convert_string_index(self, string):
        """ Convert string to index, eg. '2nd Copy' returns 'copy02' """

        # check whether a number is present
        # TODO this needs some attention
        if ' ' in string:
            return "{}{:02d}".format(string.split()[1].lower(), int(string.split()[0][:-2]))
        return "{}01".format(string.lower())

    def convert_key_string(self, key):
        """ Convert key eg. 'copy02' or 'variant01' to '2nd Copy' or 'Variant' """

        # split key into type and number
        extra_type, extra_count = key[:-2], int(key[-2:])
        # return formatted string
        return self.nth_string(extra_type, extra_count - 1)

    def clear_extras(self):
        """ Clear all extra info to avoid using old keys, this is only necessary for copies and variants """

        # iterate over sorted dict keys
        for k in sorted(self.issues_box.issues_dict[self.issues_dict_index]):
            # find copies and variants info
            if 'copy' in k or 'variant' in k:
                # delete data from original dict
                del self.issues_box.issues_dict[self.issues_dict_index][k]

    def add_extra_box(self, box_label, note=''):
        """ Add new copy or variant box to layout """

        # handle variants
        if 'variant' in box_label.lower():
            # increase variable count
            self.extra_issues['variant'] += 1
            # set type
            extra_type = 'variant'
        # handle copies
        elif 'copy' in box_label.lower():
            self.extra_issues['copy'] += 1
            extra_type = 'copy'
        else:
            # debugging purposes. could raise an error, but this should never happen with the correct coding
            print("ERROR: Something went wrong!")
            return False
        # add new extra
        new_box = ExtraIssueBox(self, extra_type, box_label, note)
        # using index 1 to insert it after the issue input
        self.add_widget(new_box, 1)

    def nth_string(self, extra_type, extra_count=None):
        """ Return a string depending on amount of extra copies. eg. '2nd copy', '3rd copy', etc"""
        # TODO repeating the same todo for a problem over a buch of functions
        extra_count = self.extra_issues[extra_type] if extra_count is None else extra_count

        if extra_count == 0:
            return '{}'.format(extra_type.title())
        elif extra_count == 1:
            n_string = '2nd'
        elif extra_count == 2:
            n_string = '3rd'
        else:
            n_string = "{}th".format(extra_count + 1)
        return "{} {}".format(n_string, extra_type.title())


class ExtraIssueBox(BoxLayout):

    box_label = StringProperty()
    number_label = ObjectProperty()
    note = ObjectProperty()

    def __init__(self, issue_info_box, extra_type, box_label, note, **kwargs):
        super(ExtraIssueBox, self).__init__(**kwargs)
        self.issue_info_box = issue_info_box
        self.extra_type = extra_type
        self.box_label = box_label
        self.note.text = note

    # def on_box_label(self, instance, value):
    #     self.extra_number_label.text = self.box_label

    def remove_me(self):
        """ Remove extra """
        # TODO remove data from issues_dict
        self.issue_info_box.extra_issues[self.extra_type] -= 1
        self.fix_numbering()
        self.issue_info_box.remove_widget(self)

    def fix_numbering(self):
        # get current count
        current_count = self.issue_info_box.extra_issues[self.extra_type]

        # iterate over all children
        for c in self.issue_info_box.children:
            # find extra_issues_boxes
            if isinstance(c, type(self)) and c.extra_type == self.extra_type:
                # adjust current count
                current_count -= 1
                # change label accordingly
                c.box_label = self.issue_info_box.nth_string(self.extra_type, current_count)


class AddExtraButton(TextButton):
    extra_type = StringProperty()
    issue_info_container = ObjectProperty()
