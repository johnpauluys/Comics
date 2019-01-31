from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton

from datetime import datetime
from re import match

Builder.load_file('comics_widgets.kv')


class ComicsScreen(Screen):

    def get_current_year(self):
        return datetime.now().year


class FieldBox(BoxLayout):
    pass


class FieldLabel(Label):
    pass


class MyTextInput(TextInput):

    number_of_spaces_allowed = NumericProperty(1)

    def on_text(self, instance, value):
        self.remove_space(instance, value)

    def remove_space(self, widget, text):
        """ Don't allow user to start string with a space or enter a double space"""
        # Had to implement this, to avoid some bug in kivy's suggest text feature
        if text == ' ' or text.endswith(' ' * (self.number_of_spaces_allowed + 1)):
            widget.text = text[:-1]


class IssueNumberInput(TextInput):

    def on_text(self, instance, value):
        """ Allow user to only input the correct formats """
        if not self.validate_input(value):
            self.text = value[:-1]

    def validate_input(self, user_input):
        """ Check whether the correct format is given, then return boolean """

        if match(r'^[1-9]\d*[\+]?$', user_input) or match(r'^[1-9]\d*[\-]([1-9]\d*)?$', user_input):
            return True
        return False


class DateInput(TextInput):

    def check_input(self, start_date, end_date):
        """ Check whether valid dates are given """
        try:
            start, start_format = self.validate_date(start_date.text, return_info=True)
            end, end_format = self.validate_date(end_date.text, return_info=True)

            if start > end:
                start_date.text, end_date.text = end_date.text, start_date.text

        except ValueError:
            return False
        except TypeError:
            pass
        return True

    def validate_date(self, date_string, return_info=False):

        date = ObjectProperty()
        formats = ["%Y", "%m/%Y", "%d/%m/%Y"]
        strikes = 0

        for f in formats:
            try:
                date = datetime.strptime(date_string, f)
                if return_info:
                    return date, formats[strikes]
            except ValueError:
                strikes += 1
        return True if strikes == 3 else False


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
                if word.startswith(text):
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

    def get_text_suggestion(self, db_cursor, text, db_table, table_field):
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

        if btn_text.isnumeric():
            # handle ints
            return int(btn_text)
        else:
            try:
                # handle floats
                return float(btn_text)
            except ValueError:
                # return string as is
                return btn_text

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

        issues = "{} - {}".format(years[0], years[-1])
        if years[-1] == datetime.now().year:
            issues = '{} - present'.format(years[0])

        self.issues_data[edition_name] = {'owned_issues': [], 'issues': issues}
        print(issues_data, self.issues_data)

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
        elif msg_type == 'important':
            self.current_status.text = 'IMPORTANT: '
            self.current_status.color = (1, 1, 0, 1)
        elif msg_type == 'warning':
            self.current_status.text = 'WARNING: '
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
            print(instance.text)
            # call function if user chose yes
            if instance.text == confirm:
                print(instance.text)
                callback()
            self.clear_status()

        # disable rest of screen
        self.screen_disabled = True

        no = Button(text=decline)
        no.bind(on_press=response)

        yes = Button(text=confirm)
        yes.bind(on_press=response)

        self.set_status(question, 'warning')
        self.add_widget(no)
        self.add_widget(yes)


class TestBox(BoxLayout):
    pass


class TestLabel(Label):
    pass
