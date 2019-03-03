from kivy.lang import Builder
from kivy.properties import BooleanProperty, DictProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton

from datetime import datetime
from re import match

Builder.load_file('comics_widgets.kv')


class ComicsScreen(Screen):

    @staticmethod
    def get_current_year():
        """ Return current year """
        return datetime.now().year

    @staticmethod
    def get_publisher_table_name(publisher):
        """ Return table name generated by publisher name """
        # remove problematic characters
        for r in (' ', '!'):
            publisher = publisher.replace(r, '_')
        # return name
        return publisher.lower()

    @staticmethod
    def sort_ignore_prefix(unsorted_list, ignore='the '):
        """ Return list sorted database indices ignore specified prefix """
        return sorted(unsorted_list,
                      key=lambda a: a['title'][len(ignore):] if a['title'].lower().startswith(ignore) else a['title'])


class FieldBox(BoxLayout):
    pass


class FieldLabel(Label):
    pass


class TextButton(Button):
    pass


class TextToggleButton(ToggleButton):
    pass


class MyTextInput(TextInput):
    """ Custom TextInput class """

    allowed_spaces = NumericProperty(1)

    def on_text(self, instance, value):
        """ Allow user to only input the correct formats """

        if not self.validate_input(value):
            self.text = value[:-1]

    def validate_input(self, user_input):
        """ Don't allow user to start string with a space or enter a double space"""

        # Had to implement this, to avoid some bug in kivy's suggest text feature
        if user_input == ' ' or user_input.endswith(' ' * (self.allowed_spaces + 1)):
            return False
        return True


class IssueNumberInput(MyTextInput):
    """ TextInput class to handle standard issue input """

    def validate_input(self, user_input):
        """ Only allow standard issue numbers and issue ranges eg. 24-120 """
        return True
        if match(r'^[1-9]\d{0,3}(\+|-[1-9]\d{0,3})?$', user_input):
            return True
        return False


class OddIssueInput(MyTextInput):
    """ TextInput class to handle odd issues input"""

    def validate_input(self, user_input):
        """ Only allow processable input values. """

        odd = '-?(\d{1,4}((\D[\D\d]?)|(\.\d{1,2})|(_((\d|\D){1,2})?))?)?'
        repeat_odd = r'^' + odd + '(,\s?' + odd + ')*$'
        if match(repeat_odd, user_input):
            return True
        return False


class DateInput(MyTextInput):

    date_valid = BooleanProperty(False)
    status_bar = ObjectProperty()
    error_status = "Date format not valid. Use any of the following: \"DD/MM/YYYY\", \"MM/YYY\", \"YYYY\""

    def set_date(self, data_dict, dict_key):

        if self.text:
            date = self.validate_date(self.text)
            if date:
                self.date_valid = True
                if self.focus:
                    self.get_focus_next().focus = True
                data_dict[dict_key] = date
            else:
                self.select_all()
                self.status_bar.set_status(self.error_status, 'notice')
        else:
            data_dict[dict_key] = None
            if self.focus:
                self.get_focus_next().focus = True

    def validate_date(self, date):

        self.date_valid = False

        if match(r'^((19)|(20))\d{2}$', date):
            # check yyyy
            # print('date format: yyyy')
            return date
        else:
            d_format = str()
            delimiter = ''

            if match(r'^[01]\d[.\/-]?[12][90]\d{2}$', date):
                # check mm/yyyy
                # print('date format: mm-yyyy')
                delimiter = date[2] if len(date) == 7 else ''
                d_format = '%m{0}%Y'

            elif match(r'^[0-3]\d[.\/-]?[01]\d[.\/-]?[12][90]\d{2}$', date):
                # dd/mm/yyyy
                # print('date format: dd/mm/yyyy')
                delimiter = date[2] if len(date) == 10 else ''
                if delimiter and delimiter == date[5]:
                    d_format = '%d{0}%m{0}%Y'
                else:
                    return False
            try:
                time_stamp = datetime.strptime(date, d_format.format(delimiter))
                if time_stamp:
                    return time_stamp.strftime(d_format.format('/'))
            except ValueError:
                return False


class PredictiveTextInput(MyTextInput):
    """" TextInput class that make use of suggestion_text"""

    current_suggested_word = StringProperty()

    def suggest_text(self, db_cursor, db_table, table_field):
        """ Display suggested text """
        # reset suggestions
        self.suggestion_text = '  '
        self.current_suggested_word = ''

        # only continue if right conditions are met
        if self.text and not self.text.endswith(' '):
            # get the last (or only) word in string
            text = self.text.split()[-1]
            # get a suggestion string
            result = self.get_text_suggestion(db_cursor, text, db_table, table_field)
            # set suggestion_text
            if result:
                # set a variable to hold entire suggested string
                self.current_suggested_word = result
                # shorten suggestion_text according to typed text, if necessary
                self.suggestion_text = result[len(text):] + '  '
                if text.lower() == self.current_suggested_word.lower().strip():
                    self.suggestion_text = '  '
                    self.current_suggested_word = ''

    def suggest_text_from_list(self, word_list):

        # reset suggestions
        self.suggestion_text = '  '
        self.current_suggested_word = ''

        if self.text and not self.text.endswith(' '):
            # get the last (or only) word in string
            text = self.text.split()[-1]
            # get a suggestion string
            result = ''
            for word in word_list:
                if word.lower().startswith(text.lower()):
                    result = word
                    break
            if result:
                # set a variable to hold entire suggested string
                self.current_suggested_word = result
                # shorten suggestion_text according to typed text, if necessary
                self.suggestion_text = result[len(text):] + '  '
                if text.lower() == self.current_suggested_word.lower().strip():
                    self.suggestion_text = '  '
                    self.current_suggested_word = ''

    @staticmethod
    def get_text_suggestion(db_cursor, text, db_table, table_field):
        """ Search database for possible string suggestions matching last word of user input """

        # search database
        sql_dict = {'table': db_table, 'field': table_field, 'text': text}
        sql = "SELECT {field} FROM {table} WHERE {field} LIKE '{text}%'".format_map(sql_dict)
        suggestions = db_cursor.execute(sql).fetchall()

        if suggestions:
            # create a sorted list from possible words and select the longest
            return sorted([word[0] for word in suggestions], key=len)[-1]

    def complete_string(self, ending=' '):
        """ If suggested text is available, hitting enter will update text string """
        if self.text and self.current_suggested_word:
            self.text = self.text[:self.last_word_index()] + self.current_suggested_word + ending
            self.current_suggested_word = ''

    def last_word_index(self):
        """ Return index of first letter in last word"""
        last_word = self.text.split()[-1]
        return self.text.find(last_word)


class IssueToggleButton(ToggleButton):

    def __init__(self, container, user_data, **kwargs):
        super(IssueToggleButton, self).__init__(**kwargs)
        self.container = container
        self.user_data = user_data

    @staticmethod
    def convert_issue_number(btn_text):
        """ Convert IssueToggleButton.text from string to appropriate type """

        btn_text = btn_text.strip()

        if match(r'^((-?[1-9]\d{0,3})|0)$', btn_text):
            # handle ints
            # print("int: {}".format(btn_text))
            return int(btn_text)
        elif match(r'^-?\d{1,4}\.\d{1,2}$', btn_text):
            # handle fractions
            # print("float: {}".format(btn_text))
            return float(btn_text)
        elif match(r'^-?\d{1,4}((\D{1,2})|((\.\d{1,2})?_((\D|\d){1,2})?))$', btn_text):
            # handle strings like 1a, 1_, 1_a, 1_ab, 1_a1, etc
            # print("str: {}".format(btn_text))
            return str(btn_text)
        else:
            print("no match: {}".format(btn_text))

    def on_state(self, instance, value):
        """ Add or remove btn from owned issues list """

        if value == 'down' and self.convert_issue_number(self.text) not in self.user_data['owned_issues']:
            self.user_data['owned_issues'].append(self.convert_issue_number(self.text))
        if value == 'normal' and self.convert_issue_number(self.text) in self.user_data['owned_issues']:
            self.user_data['owned_issues'].remove(self.convert_issue_number(self.text))


class SpecialIssueNoteInputBox(FieldBox):
    screen = ObjectProperty()
    container = ObjectProperty()
    issue_code = StringProperty()
    current_note = StringProperty()
    note_container = ObjectProperty()
    status_bar = ObjectProperty()

    def __init__(self, screen, container, issue_code, current_note, note_container, status_bar, **kwargs):
        super(SpecialIssueNoteInputBox, self).__init__(**kwargs)
        self.screen = screen
        self.container = container
        self.issue_code = issue_code
        self.current_note = current_note
        self.note_container = note_container
        self.status_bar = status_bar


class OtherEditionBox(BoxLayout):

    issues_container = ObjectProperty()

    def __init__(self, container, edition_name, edition_issues, issues_data, **kwargs):
        super(OtherEditionBox, self).__init__(**kwargs)
        self.container = container
        self.edition_name = edition_name
        self.issues_data = issues_data

        self.issues_data[edition_name] = {'owned_issues': [], 'no_of_issues': edition_issues}

        self.ids._editions_label.text = edition_name

        # add issues
        for i in range(int(edition_issues)):

            new_issue_btn = IssueToggleButton(self.issues_container, self.issues_data[edition_name], text=str(i+1))
            self.issues_container.add_widget(new_issue_btn)

        # fill up empty spaces
        for i in range(int(edition_issues % 10)):
            self.issues_container.add_widget(Label())

    def remove_edition(self):
        del self.issues_data[self.edition_name]
        self.container.remove_widget(self)


class AnnualsEditionBox(BoxLayout):

    annuals_container = ObjectProperty()

    def __init__(self, container, edition_name, years, issues_data, **kwargs):
        super(AnnualsEditionBox, self).__init__(**kwargs)
        self.container = container
        self.edition_name = edition_name
        self.issues_data = issues_data

        self.ids._annuals_label.text = edition_name

        for y in years:
            new_issue_btn = IssueToggleButton(self.annuals_container, self.issues_data[self.edition_name], text=str(y))
            self.annuals_container.add_widget(new_issue_btn)

        # fill up empty spaces
        for i in range(len(years) % 5):
            self.annuals_container.add_widget(Label())

    def remove_edition(self):
        del self.issues_data[self.edition_name]
        self.container.remove_widget(self)


class IssueNoteBox(FieldBox):

    issue_number_label = ObjectProperty()
    issue_note_label = ObjectProperty()
    del_btn = ObjectProperty()
    back_lit = BooleanProperty()

    def __init__(self, issue_number, issue_note, notes_dict, backlit, **kwargs):
        super(IssueNoteBox, self).__init__(**kwargs)
        self.issue_number = issue_number
        self.issue_number_label.text = '# {}'.format(str(issue_number))
        self.issue_note_label.text = issue_note
        self.issue_notes_dict = notes_dict
        self.back_lit = backlit

    def confirm_delete(self):
        """ Let user decide whether he really wants to delete a note"""
        if self.del_btn.text == '[deleted]':
            self.parent.remove_widget(self)
        else:
            self.parent.status_bar.confirm('Are you sure you want to delete this note?', self.remove_issue_note)

    def remove_issue_note(self):
        """ Remove note from notes dictionary"""

        del self.issue_notes_dict[self.issue_number]


class StatusBar(FieldBox):
    screen_disabled = BooleanProperty(False)
    current_status = ObjectProperty()

    def set_status(self, status_msg, msg_type='hint'):

        if msg_type == 'normal':
            self.current_status.text = ''
            self.current_status.color = (.6, .6, .6, 1)
        elif msg_type == 'hint':
            self.current_status.text = ''  # ''HINT: '
            self.current_status.color = (.2, .7, .9, 1)
        elif msg_type == 'notice':
            self.current_status.text = 'PLEASE NOTE: '
            self.current_status.color = (1, 1, 0, 1)
        elif msg_type == 'error':
            self.current_status.text = 'ERROR: '
            self.current_status.color = (1, 0, 0, 1)
        elif msg_type == 'success':
            self.current_status.text = 'SUCCESS: '
            self.current_status.color = (0, 1, 0, 1)

        self.current_status.text += status_msg

    def clear_status(self):
        """ Clear status """
        self.current_status.text = ''

    def confirm(self, question, callback, decline='no', confirm='yes'):
        """ Change status bar to question, run callback if answer is yes"""

        def response(instance):
            """ Clear status bar and respond to user's decision"""
            self.remove_widget(yes)
            self.remove_widget(no)
            self.screen_disabled = False
            # call function if user chose yes
            if instance.text == confirm:
                callback()
            self.clear_status()

        # disable rest of screen
        self.screen_disabled = True

        no = Button(text=decline)
        no.bind(on_press=response)

        yes = Button(text=confirm)
        yes.bind(on_press=response)

        self.set_status(question, 'notice')
        self.add_widget(no)
        self.add_widget(yes)

    def get_current_status(self):
        return self.current_status.text


class InfoDropDownContent(BoxLayout):

    publisher = StringProperty()
    standard_issues = StringProperty()
    dates = StringProperty()
    title_notes = StringProperty()
    issue_notes = StringProperty()

    def __init__(self, publisher, standard_issues, dates, title_notes, issue_notes, **kwargs):
        super(InfoDropDownContent, self).__init__(**kwargs)
        self.publisher = publisher
        self.standard_issues = (str(standard_issues))
        self.dates = dates
        self.title_notes = title_notes
        self.issue_notes = self.convert_issue_notes(issue_notes)

    @staticmethod
    def convert_issue_notes(issue_notes):
        notes = ''
        for k in sorted(issue_notes, key=lambda a: int(a.split('_')[0])):
            notes += "{:<10}{}\n".format(str(k), issue_notes[k])
        return notes


class ComicListWidget(BoxLayout):

    title_label = ObjectProperty()
    dropdown = ObjectProperty()

    title = StringProperty()
    progress = StringProperty()
    owned_issues = ''
    notes = StringProperty()
    issue_notes = DictProperty()

    data = DictProperty()

    def __init__(self, title, publisher, volume, format_, standard_issues, odd_issues, owned_issues,
                 other_editions, start_date, end_date, group, notes, issue_notes, **kwargs):
        super(ComicListWidget, self).__init__(**kwargs)
        self.title = title
        self.publisher = publisher
        self.volume = volume
        self.format = format_
        self.standard_issues = standard_issues
        self.odd_issues = odd_issues
        self.owned_issues = owned_issues
        self.other_editions = other_editions
        self.start_date = start_date
        self.end_date = end_date
        self.group = group
        self.notes = notes
        self.issue_notes = issue_notes

        self.progress = self.get_progress()

    def get_progress(self):
        """ Return a percentage string of owned vs available comics """
        if self.owned_issues != 'complete':
            # check if title is still ongoing
            ongoing = ('', '')
            if isinstance(self.standard_issues, str):
                total_issues = int(self.standard_issues[:-1])
                ongoing = ('+', '~')
            elif isinstance(self.standard_issues, int):
                # set total issue count
                total_issues = self.standard_issues
            else:
                return '???'
            if self.odd_issues:
                # add odd issues, if any
                total_issues += len(self.odd_issues)
            # set total owned issue count
            owned_issues = len(self.owned_issues)
            # return percentage
            return "{}/{}{} ({}{:.1%})".format(owned_issues, total_issues,
                                               ongoing[0], ongoing[1], owned_issues/total_issues)

        return self.owned_issues

    def clear_dropdown(self):
        """ Clear any content in dropdown section """
        self.dropdown.clear_widgets()

    def get_date_string(self):
        if self.start_date:
            dates = self.start_date
            if self.end_date:
                dates += " - {}".format(self.end_date)
            return dates
        return ''

    def open_info(self):
        """ Create/remove dropdown content """

        # this acts as a toggle btn, clearing if anything is available...
        if self.dropdown.children:
            self.title_label.color = (.6, .6, .6, 1)
            self.clear_dropdown()
        # ...or adding content if dropdown is empty
        else:
            dates = self.get_date_string()

            self.title_label.color = (1, 1, 1, 1)

            self.dropdown.add_widget(InfoDropDownContent(self.publisher, self.standard_issues, dates,
                                                         self.notes, self.issue_notes))

    def open_issues(self):

        if self.dropdown.children:
            self.clear_dropdown()

        else:
            issues_container = GridLayout(cols=10, size_hint_x=.5)

            std_issues = int()

            if isinstance(self.standard_issues, str):
                if self.standard_issues.endswith('+'):
                    std_issues = int(self.standard_issues[:-1])
            else:
                std_issues = self.standard_issues

            for i in range(std_issues):
                if i+1 in self.owned_issues:
                    btn = ToggleButton(size_hint=(1, None), text=str(i+1), state='down')
                else:
                    btn = ToggleButton(size_hint=(1, None), text=str(i+1))
                issues_container.add_widget(btn)

            self.dropdown.add_widget(issues_container)
