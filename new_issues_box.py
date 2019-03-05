from kivy.lang import Builder
from kivy.graphics import Color, Rectangle
from kivy.properties import DictProperty, NumericProperty, ObjectProperty, OptionProperty, StringProperty
from comics_widgets import BoxLayout, FieldBox, Label, TextButton, ToggleButton
from comics_widgets import TestBox  # debugging
from re import match

Builder.load_file('new_issues_box.kv')


class IssuesBox(BoxLayout):
    """ Widget to hold all issue functionailty """

    # properties from screen_new
    screen = ObjectProperty()
    status_bar = ObjectProperty()

    # local properties
    info_window_status = OptionProperty('close', options=['open', 'close'])
    item_counter = NumericProperty(0)

    # container to be filled with issue buttons
    issues_container = ObjectProperty()
    current_row = ObjectProperty()

    # all issue data
    issues_button_dict = DictProperty()
    issues_dict = DictProperty()

    def on_info_window_status(self, instance, value):
        """ Disable/Enable all IssueRowBoxes not containing IssueInfoBoxes """
        print("{}: issue info window {}s".format(self.__class__.__name__, value))
        for child in self.issues_container.children:
            child.disabled = True if not isinstance(child, IssueInfoBox) and value == 'open' else False

    def on_item_counter(self, instance, value):
        """ Create and add a new IssueRowBox for every ten issues """
        if value and value % 10 == 0:
            self.issues_container.add_widget(self.current_row)
            self.current_row = IssueRowBox()

    def clear_issues_container(self):
        """ Reset issues container """

        if not self.issues_container.children:
            return
        print('{}: clearing all issues'.format(self.__class__.__name__))
        # clear issue container
        self.issues_container.clear_widgets()
        # reset counter (this also sets a new issue row)
        self.item_counter = 0

    def load_issues(self, issue_ranges):
        """ Load standard issues based on what user entered """

        # remove any issues
        self.clear_issues_container()

        print("{}: loading issues".format(self.__class__.__name__))

        # add issues to issues_dict and set ongoing series variable
        self.issues_dict, self.screen.ongoing_series = self.parse_issue_ranges(issue_ranges)

        if self.issues_dict:

            # set new current_row
            self.current_row = IssueRowBox()

            # add issue toggle buttons to container
            self.populate_issue_container()

            # self.current_row = IssueContainerBox()
            # self.add_widget(self.current_row)
            self.status_bar.set_status("Select owned issue(s) by single-clicking issue number or double-click to open "
                                       "extra options.", 'hint')

    def parse_issue_ranges(self, issue_ranges):
        """ Return a dictionary from issue ranges (user input) and set whether it is an ongoing series """
        print('{}: parsing \'{}\''.format(self.__class__.__name__, issue_ranges))

        # set local variables
        issues_dict = {}
        on_going = False
        errors = []

        # handle single number of issues. eg '150' or '150' for ongoing series
        if match(r'^[1-9]\d{0,2}\+?$', issue_ranges):
            i = issue_ranges
            # check for ongoing series
            if i.endswith('+'):
                on_going = True
                i = i[:-1]
            # fill issues_dict
            issues_dict = {**issues_dict, **{k: {} for k in range(1, int(i) + 1)}}

        # handle multiple values
        else:
            for i in [r.strip() for r in issue_ranges.split(',')]:
                # handle single numbers and 0
                if match(r'^\d{1,3}$', i):
                    issues_dict[int(i)] = {}

                # handle ranges eg. 1-20, 22-24, 28-30+
                elif match(r'^\d{1,3}[\-]\d{1,3}\+?$', i):

                    # check for ongoing series
                    if i.endswith('+'):
                        on_going = True
                        i = i[:-1]

                    # first and last number of range (swap 1st and last for values like '20-1'
                    start, end = sorted(int(n) for n in i.split('-'))
                    issues_dict = {**issues_dict, **{k: {} for k in range(start, end + 1)}}

                # handle single negative values, eg. -1, -1.25 and 0
                elif match(r'^-\d{1,3}(.\d{1,2})?$', i):
                    # check whether int or float was given
                    issues_dict[float(i) if '.' in i else int(i)] = {}
                else:
                    # if any given string couldn't be parsed, stop operation
                    errors.append(i)
                    print("string not valid: {}".format(i))
                    self.status_bar.set_status('The following range(s) caused problems: "{}".'.format(', '.join(errors)),
                                               'error')
                    return {}, False

        # if entire string fails, let user know
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
        # TODO rewrite this function, it kinda sucks

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

        # create sorted lists of issues
        pre = sorted(i for i in self.issues_dict if i <= 0)
        std = sorted(i for i in self.issues_dict if i > 0)

        if pre:
            # add empty buttons if necessary
            for i in range(10 - len(pre) % 10):
                self.current_row.add_widget(Label(text='', size_hint=(1, None)))
                self.item_counter += 1
            for i in pre:
                new_btn = IssueToggleButton(self, self.issues_container, i)
                self.current_row.add_widget(new_btn)
                self.item_counter += 1
                self.issues_button_dict[i] = new_btn
        if std:
            for i in self.pad_issues(std, bool(pre)):
                if i == '':
                    self.current_row.add_widget(Label(text='', size_hint=(1, None)))
                    self.item_counter += 1
                else:
                    new_btn = IssueToggleButton(self, self.issues_container, i)
                    self.current_row.add_widget(new_btn)
                    self.item_counter += 1
                    self.issues_button_dict[i] = new_btn

        self.add_issue_selector()

    def add_issue_selector(self):

        # create instance of selector box
        issue_selector = IssueSelector(self)

        # check whether bottom row of issue_container contains buttons (This acts as a work around for another problem
        # TODO find the real source of this problem and fix it. Has something to do with group_issues() or pad_issues()
        if any(isinstance(w, IssueToggleButton) for w in self.issues_container.children[0].children):
            # create new row and change height and add issue_selector
            new_row = IssueRowBox(height=issue_selector.height)
            new_row.add_widget(issue_selector)
            # add new row to issues container
            self.issues_container.add_widget(new_row)
        else:
            self.issues_container.children[0].clear_widgets()
            self.issues_container.children[0].height = issue_selector.height
            self.issues_container.children[0].add_widget(issue_selector)


class IssueRowBox(BoxLayout):
    pass


class IssueSelector(FieldBox):

    def __init__(self, issues_box, **kwargs):
        super(IssueSelector, self).__init__(**kwargs)
        self.issues_box = issues_box

    def test(self):
        print(type(self.issues_box.issues_dict))

    def select_issue_range(self, range_input):
        """ Select issues in given range """

        # parse range
        issue_selection_list = self.parse_range_input(range_input)

        errors = []
        if issue_selection_list:
            for i in issue_selection_list:
                try:
                    # select issue
                    self.issues_box.issues_button_dict[i].state = 'down'
                except KeyError:
                    # append issue number to errors list
                    errors.append(str(i))

            # set status bar
            if errors:
                # set status if errors were detected
                if len(errors) > 1:
                    msg = ('The following aren\'t in current given issues: {}'.format(', '.join(errors)), 'notice')
                else:
                    msg = ('The number {} is not in current given issues.'.format(', '.join(errors)), 'notice')
            else:
                msg = ('Selection successfully completed.',)
        else:
            msg = ('\'{}\' is an invalid range.'.format(range_input), 'error')

        self.issues_box.status_bar.set_status(*msg)

    def parse_range_input(self, range_input):
        """ Return a list of issue numbers parsed from range(s)
            '1-3'    would return [1, 2, 3,]
            '1-3, 5' would return [1, 2, 3, 5] """

        selection = []
        # iterate over each section of input
        for n in [i.strip() for i in range_input.split(',')]:
            # handle ranges eg. 1-15
            if match(r'^[1-9]\d*\s*-\s*[1-9]\d*', n):
                start, end = n.split('-')
                selection += [i for i in list(range(int(start), int(end) + 1))]
            else:
                try:
                    # handle single numbers
                    selection.append(float(n) if '.' in n else int(n))
                except ValueError:
                    msg = '\'{}\' is not a valid entry.'.format(n)
                    self.issues_box.status_bar.set_status(msg, 'error')
                    return False
        return selection

    def select_all_issues(self):
        """ Select all issues """
        for i in self.issues_box.issues_button_dict.values():
            i.state = 'down'

    def deselect_all_issues(self):
        """ Deselect all issues """
        for i in self.issues_box.issues_button_dict.values():
            i.state = 'normal'


class IssueToggleButton(ToggleButton):
    """ Class representing an issue toggle button """

    # outside properties
    issues_box = ObjectProperty()
    issue_container = ObjectProperty()

    # own properties
    index_in_dict = NumericProperty()
    info_box = ObjectProperty()

    # data
    owned = OptionProperty(0, options=[0, 1])
    notes = StringProperty()
    extra_issues_count = DictProperty({'copy': 0, 'variant': 0})

    def __init__(self, issues_box, issues_container, index_in_dict, **kwargs):
        super(IssueToggleButton, self).__init__(**kwargs)
        self.issues_box = issues_box
        self.issues_container = issues_container
        self.index_in_dict = index_in_dict

    def on_extra_issues_count(self, instance, value):
        """ Change text of add buttons """
        copy_count = 'copy{:02d}'.format(int(self.extra_issues_count['copy']) + 1)
        variant_count = 'variant{:02d}'.format(int(self.extra_issues_count['variant']) + 1)

        copy_str = IssueInfoBox.convert_key_string(copy_count)
        variant_str = IssueInfoBox.convert_key_string(variant_count)
        if self.info_box:
            self.info_box.add_copy_button.text = 'add {}'.format(copy_str)
            self.info_box.add_variant_button.text = 'add {}'.format(variant_str)

    def on_state(self, instance, value):
        """ Set owned status to 1 if button is down, otherwise set it to 0 """
        self.owned = 1 if value == 'down' else 0

    def on_owned(self, instance, value):
        """ Update issues_dict accordingly, depending on state. """
        print('{}: You {}own issue #{}'.format(instance.__class__.__name__, "don't " if not value else '', self.text))
        self.issues_box.issues_dict[self.index_in_dict]['owned'] = value
        # update copy count
        self.extra_issues_count['copy'] += 1 if value else -1

    def mark_note(self, mark=True):
        print('marking')
        if mark:
            self.text = self.text + '*' if not self.text.endswith('*') else self.text
        else:
            self.text = self.text[:-1] if self.text.endswith('*') else self.text

    def on_touch_down(self, touch):

        if self.collide_point(*touch.pos):
            # cancel any action if info window is open
            if self.issues_box.info_window_status == 'open':
                return False
            # handle double-clicking
            if touch.is_double_tap:
                # set issue as owned
                self.state = 'down'
                # open info box
                self.open_info_box()
            else:
                self.reverse_state()
        else:
            return super().on_touch_down(touch)

    def open_info_box(self):
        """ Open issue info box """
        # get current index of parent. This is where info box will be inserted into
        info_index = self.issues_container.children.index(self.parent)
        # add info box to issues container
        info_box = IssueInfoBox(self)
        self.info_box = info_box
        self.issues_container.add_widget(info_box, index=info_index)
        # set info window status to open
        self.issues_box.info_window_status = 'open'

    # def on_touch_up(self, touch):
    #
    #     if touch.grab_current is self:
    #         print('grabbed', touch)
    #         touch.ungrab(self)

    def reverse_state(self):
        self.state = 'down' if self.state == 'normal' else 'normal'


class IssueInfoBox(BoxLayout):
    """ Class representing info box. This widget will allow user to add extra copies,
        variants and notes to current issue """

    # outside properties
    issues_box = ObjectProperty()

    # own relevant properties
    issue = ObjectProperty()
    index_in_dict = NumericProperty()
    extra_issues = DictProperty()
    notes = ObjectProperty()

    add_copy_button = ObjectProperty()
    add_variant_button = ObjectProperty()

    def __init__(self, issue_button, **kwargs):
        super(IssueInfoBox, self).__init__(**kwargs)
        self.issues_box = issue_button.issues_box
        self.issue = issue_button
        self.index_in_dict = issue_button.index_in_dict
        self.extra_issues = issue_button.extra_issues_count
        self.add_copy_button.text = 'add {}'.format(self.convert_type_number_string('copy',
                                                                                    int(self.extra_issues['copy']+1)))
        self.add_variant_button.text = 'add {}'.format(self.convert_type_number_string('variant',
                                                                                       int(self.extra_issues['variant']+1)))
        self.load_prev_info()

    def load_prev_info(self):
        """ Load previously entered data, if any """

        # reset counters
        self.issue.extra_issues_count['copy'] = 1
        self.issue.extra_issues_count['variant'] = 0

        # iterate over sorted dict keys
        for i in sorted(self.issues_box.issues_dict[self.index_in_dict]):

            # check if notes exist
            if i == 'notes':
                # add old text to notes text input field
                self.notes.text = self.issues_box.issues_dict[self.index_in_dict][i]

            # check for copies and variants
            elif 'copy' in i or 'variant' in i:
                # convert key to box label
                box_label = self.convert_key_string(i)
                # set extra notes text
                note = self.issues_box.issues_dict[self.index_in_dict][i]
                # add extra box widget
                self.add_extra_box(box_label, note)

    def get_extras(self):
        """ Return a list of opened extra issue boxes """
        return [b for b in self.children if isinstance(b, ExtraIssueBox)]

    def check_empty_extras(self):
        """ Return True if any extras exist without note text """
        return True if False in [bool(e.note.text) for e in self.get_extras()] else False

    def close_window(self, issue_box):
        """ Remove info window """
        # set status variable to closed
        self.issues_box.info_window_status = 'close'
        # remove widget
        issue_box.remove_widget(self)

    def save_changes(self):
        """ Save changes made on issue """

        # cancel all operations if extra boxes are without decriptions
        if self.check_empty_extras():
            self.issues_box.status_bar.set_status('Please fill out all copy/variant description fields.', 'error')
            return False

        # get rid of old info, to avoid still containing old data
        self.clear_extras()

        # iterate over extras
        for e in self.get_extras():
            # convert sting to to index
            key = self.convert_string_key(e.number_label.text)
            # set user entered value to key in issues dict
            self.issues_box.issues_dict[self.index_in_dict][key] = e.note.text

        # add notes to issues_dict
        if self.notes.text:
            self.issues_box.issues_dict[self.index_in_dict]['notes'] = self.notes.text
            self.issue.mark_note(True)
        # close window
        self.close_window(self.parent)
        # inform user that everything went okay
        self.issues_box.status_bar.set_status('Successfully updated information for issue #{}.'.format(self.issue.text))

    @staticmethod
    def convert_string_key(string):
        """ Convert string to index, eg. '2nd Copy' returns 'copy02' """

        # check whether a number is present
        if ' ' in string:
            return "{}{:02d}".format(string.split()[1].lower(), int(string.split()[0][:-2]))
        return "{}01".format(string.lower())

    @staticmethod
    def convert_key_string(key):
        """ Convert key eg. 'copy02' or 'variant01' to '2nd Copy' or 'Variant' """

        # split key into type and number
        extra_type, extra_count = key[:-2], int(key[-2:])

        if extra_count == 1:
            return '{}'.format(extra_type.title())
        elif extra_count == 2:
            n_string = '2nd'
        elif extra_count == 3:
            n_string = '3rd'
        else:
            n_string = "{}th".format(extra_count)
        return "{} {}".format(n_string, extra_type.title())

    @staticmethod
    def convert_type_number_string(extra_type, extra_count):

        key = '{}{:02d}'.format(extra_type.lower(), int(extra_count))
        return IssueInfoBox.convert_key_string(key)

    def clear_extras(self):
        """ Clear all extra info to avoid using old keys, this is only necessary for copies and variants """

        # iterate over sorted dict keys
        for k in sorted(self.issues_box.issues_dict[self.index_in_dict]):
            # find copies and variants info
            if 'copy' in k or 'variant' in k or k is 'notes':
                # delete data from original dict
                del self.issues_box.issues_dict[self.index_in_dict][k]

    def add_extra_box(self, box_label, note=''):
        """ Add new copy or variant box to layout """

        # handle variants
        if 'variant' in box_label.lower():
            # increase variable count
            self.issue.extra_issues_count['variant'] += 1
            # set type
            extra_type = 'variant'
        # handle copies
        elif 'copy' in box_label.lower():
            self.issue.extra_issues_count['copy'] += 1
            extra_type = 'copy'
        else:
            # debugging purposes. could raise an error, but this should never happen with the correct coding
            print("ERROR: Something went wrong!")
            return False
        # add new extra
        new_box = ExtraIssueBox(self, extra_type, box_label, note)
        # using index 1 to insert it after the issue input
        self.add_widget(new_box, 1)


class ExtraIssueBox(BoxLayout):

    issues_box = ObjectProperty()
    box_label = StringProperty()
    number_label = ObjectProperty()
    extra_type = StringProperty('copy')
    note = ObjectProperty()

    def __init__(self, issue_info_box, extra_type, box_label, note, **kwargs):
        super(ExtraIssueBox, self).__init__(**kwargs)
        self.issues_box = issue_info_box.issues_box
        self.issue_info_box = issue_info_box
        self.extra_type = extra_type
        self.box_label = box_label
        self.note.text = note

    # def on_box_label(self, instance, value):
    #     self.extra_number_label.text = self.box_label

    def remove_me(self):
        """ Remove extra """
        # TODO remove data from issues_dict
        self.issue_info_box.issue.extra_issues_count[self.extra_type] -= 1
        self.issue_info_box.remove_widget(self)
        self.fix_numbering()

    def fix_numbering(self):
        # get current count
        current_count = int(self.issue_info_box.issue.extra_issues_count[self.extra_type])
        # iterate over all children
        for c in self.issue_info_box.get_extras():
            if c.extra_type == self.extra_type:
                # adjust current count
                current_count -= 1
                print('fix_numbering: current_count', current_count)
                # change label accordingly
                c.box_label = self.issue_info_box.convert_type_number_string(self.extra_type, current_count + 1)


class AddExtraButton(TextButton):
    extra_type = StringProperty()
    issue_info_container = ObjectProperty()
