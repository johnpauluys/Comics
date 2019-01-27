from kivy.lang import Builder
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton

from datetime import datetime

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


class PredictiveTextInput(MyTextInput):
    """" TextInput class that make use of suggestion_text"""

    current_suggested_word = None

    def suggest_text(self, app, db_table, table_field):
        """ Display suggested text """

        #TODO What if I check whether last == current_suggestion before executing everything
        #TODO Wouldn't that make remove_space() unneeded?

        # reset suggestions
        self.suggestion_text = '  '
        self.current_suggested_word = None

        # only continue if right conditions are met
        if self.text and not self.text.endswith(' '):
            # get the last (or only) word in string
            text = self.text.split()[-1]
            # get a suggestion string
            result = self.get_text_suggestion(app, text, db_table, table_field)
            # set suggestion_text
            if result:
                # set a variable to hold entire suggested string
                self.current_suggested_word = result
                # shorten suggestion_text according to typed text, if necessary
                self.suggestion_text = result[len(text):] + '  '

    def get_text_suggestion(self, app, text, db_table, table_field):
        """ Search database for possible string suggestions matching last word of user input """

        # search database
        sql_dict = {'table': db_table, 'field': table_field, 'text': text}
        sql = "SELECT {field} FROM {table} WHERE {field} LIKE '{text}%'".format_map(sql_dict)
        suggestions = app.cur.execute(sql).fetchall()

        if suggestions:
            # create a sorted list from possible words and select the longest
            return sorted([word[0] for word in suggestions], key=len)[-1]

    def complete_string(self, ending=' '):
        """ If suggested text is available, hitting enter will update text string """
        if self.text and self.current_suggested_word:
            self.text = self.text[:self.last_word_index()] + self.current_suggested_word + ending
        self.current_suggested_word = None

    def last_word_index(self):
        """ Return index of first letter in last word"""
        last_word = self.text.split()[-1]
        return self.text.find(' ' + last_word) + 1


class IssueToggleButton(ToggleButton):

    def __init__(self, container, user_data, **kwargs):
        super(IssueToggleButton, self).__init__(**kwargs)
        self.container = container
        self.user_data = user_data

    def convert_string(self, btn_text):
        """ Convert IssueToggleButton.text from string to appropriate type """

        if btn_text.isnumeric():
            return int(btn_text)
        elif btn_text.isalnum() or btn_text.isalpha():
            return btn_text
        else:
            return float(btn_text)

    def on_state(self, instance, value):
        """ Add or remove btn from owned issues list """

        if value == 'down' and self.convert_string(self.text) not in self.user_data['owned_issues']:
            self.user_data['owned_issues'].append(self.convert_string(self.text))
        if value == 'normal' and self.convert_string(self.text) in self.user_data['owned_issues']:
            self.user_data['owned_issues'].remove(self.convert_string(self.text))


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

    def __init__(self, issue_number, issue_note, note_data_dict, **kwargs):
        super(IssueNoteBox, self).__init__(**kwargs)
        # self.container # parent of self
        self.issue_number = issue_number
        # self.issue_note = issue_note  # note text
        self.note_data_dict = note_data_dict  # data dict in root

        self.note_data_dict[issue_number] = issue_note

        self.issue_number_label.text = str(issue_number)
        self.issue_note_label.text = str(issue_note)

    def confirm_delete(self):
        """ Let user decide whether he really wants to delete a note"""
        if self.del_btn.text == '[deleted]':
            self.parent.remove_widget(self)
        else:
            self.parent.status_bar.confirm('Are you sure you want to delete this note?', self.remove_issue_note)

    def remove_issue_note(self):
        """ Remove note from screen and notes dictionary"""
        # add strikethrough to label text
        self.issue_number_label.strikethrough = True
        self.issue_note_label.strikethrough = True
        self.del_btn.text = '[deleted]'
        # remove note from notes_dict
        del self.note_data_dict[self.issue_number]


class StatusBar(FieldBox):
    screen_disabled = BooleanProperty(False)
    current_status = ObjectProperty()

    def set_status(self, status_msg, msg_type='hint'):

        if msg_type == 'normal':
            self.current_status.text = ''
            self.current_status.color = (.6, .6, .6, 1)
        elif msg_type == 'hint':
            self.current_status.text = 'HINT: '
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
