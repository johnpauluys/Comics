from kivy.lang import Builder
from kivy.properties import BooleanProperty, DictProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.label import Label

from json import dumps
from re import match

from comics_widgets import AnnualsEditionBox, ComicsScreen, IssueNoteBox, IssueToggleButton, OtherEditionBox, SpecialIssueNoteInputBox


Builder.load_file('screen_new.kv')


class ScreenNew(ComicsScreen):
    """ Screen to allow user to add a comic title, and relative information. """
    publisher_dc_toggle = ObjectProperty()
    publisher_marvel_toggle = ObjectProperty()
    publisher_dark_horse_toggle = ObjectProperty()
    publisher_image_toggle = ObjectProperty()

    other_publisher_toggle = ObjectProperty()
    other_publisher_text = ObjectProperty()
    title_text = ObjectProperty()
    issues_text = ObjectProperty()
    start_date_text = ObjectProperty()
    end_date_text = ObjectProperty()
    special_issue_notes = ObjectProperty()
    issue_note_container = ObjectProperty()
    edition_name_text = ObjectProperty()
    edition_issues_text = ObjectProperty()

    status_bar = ObjectProperty()

    # user input
    publisher_count = NumericProperty(0)
    standard_issues = ListProperty()
    issue_notes = DictProperty()
    odd_issues = ListProperty()
    special_issues = ListProperty()

    ongoing_series = BooleanProperty(False)

    data = {'owned_issues': list(), 'issue_notes': dict()}
    other_editions_data = dict()

    # error handling
    errors = ListProperty()

    def on_special_issues(self, instance, value):

        # clear special_notes_container
        self.special_issue_notes.clear_widgets()

        for i in self.special_issues:
            try:
                current_note = self.issue_notes[i]
            except KeyError:
                current_note = ''
            special = SpecialIssueNoteInputBox(instance, self.special_issue_notes, i, current_note, self.issue_note_container, self.status_bar)
            self.special_issue_notes.add_widget(special)

    def on_issue_notes(self, instance, value):
        """ Update displayed notes """
        self.issue_note_container.clear_widgets()

        back_lit = True  # this will give every 2nd note a grey background
        for issue_number, issue_note in value.items():
            # alternate between backgrounds
            back_lit = True if not back_lit else False
            # add issue note box to notes container
            self.issue_note_container.add_widget(IssueNoteBox(issue_number, issue_note, self.issue_notes, back_lit))
            # add issue to data dict
            self.data['issue_notes'][issue_number] = issue_note.strip()

    def create_odd_issues_lists(self, pre_issues):
        """ Return two sorted list containing pre_issues
                one list to contain values like '1a, 1b, etc.'
                and another list to int anf float values
        """

        # create two empty list
        strings_list = []
        numbers_list = []
        special_list = []

        # split numeric values from strings
        for issue in set([i.strip() for i in pre_issues.split(',')]):
            # handle trailing (or just extra) commas by checking if issue
            if issue:
                # convert to appropriate
                issue = IssueToggleButton.convert_issue_number(issue)
                if not isinstance(issue, str):
                    # handle ints and floats
                    numbers_list.append(issue)
                else:
                    if '_' in issue:
                        special_list.append(issue)
                    else:
                        strings_list.append(issue)

        # sort lists
        strings_list.sort()
        special_list.sort()
        numbers_list.sort()

        # return sorted lists
        return strings_list, special_list, numbers_list

    def populate_issue_container(self, container, issue_list):
        """ Add issue buttons to issues container box """

        ongoing = 0
        if issue_list[-1] == 'ongoing':
            ongoing = 1
            del issue_list[-1]

        # fill the first spots with blank, if necessary
        if issue_list == self.standard_issues and issue_list[0] != 1:
            for i in range(issue_list[0] % 10):
                container.add_widget(Label(size_hint=(1, 1)))

        for i in issue_list:
            # create button
            new_issue_toggle = IssueToggleButton(container, self.data, text=str(i))
            # check whether it should be in a down state
            if i in self.data['owned_issues']:
                new_issue_toggle.state = 'down'
            # add button to container
            container.add_widget(new_issue_toggle)

        if ongoing:
            container.add_widget(Label(size_hint=(1, 1), text='. . .'))

        # fill up empty space to make it took prettier
        if len(issue_list) + ongoing < 10:
            for i in range(10 - len(issue_list) % 10):
                container.add_widget(Label(size_hint=(1, 1)))

    def load_issues(self, container, input_field):

        # clear anything that's already in container
        container.clear_widgets()
        issues = input_field.text.strip()

        # match regex string to see if it is standard issue
        # not starting with a zero followed by digits and ends with an optional '+'
        if match(r'^[1-9]\d*[+]?$', issues) or match(r'^[1-9]\d*[\-][1-9]\d*$', issues):
            if issues.endswith('+'):
                # handle ongoing series
                self.data['issues_in_run'] = issues
                self.standard_issues = list(range(1, int(issues[:-1]) + 1)) + ['ongoing']
                self.ongoing_series = True
            else:
                if '-' in issues:
                    # handle sections, like 25-100, etc.
                    first, last = sorted(issues.split("-"), key=int)
                    self.data['issues_in_run'] = '{}-{}'.format(first, last)
                    self.standard_issues = list(range(int(first), int(last) + 1))
                else:
                    # handle finished series
                    self.data['issues_in_run'] = int(issues)
                    self.standard_issues = list(range(1, int(issues) + 1))
                self.ongoing_series = False

            self.populate_issue_container(container, self.standard_issues)
            self.start_date_text.focus = True

        elif not issues.endswith('-'):
            # handle non standard issues
            strings, specials, numbers = self.create_odd_issues_lists(issues)

            # populate _odd_issue_container
            if strings or specials:
                self.populate_issue_container(container, strings + specials)
            if numbers:
                self.populate_issue_container(container, numbers)

            self.special_issues = specials

            # update data dict with newly formatted values
            print('setting pre_issues to:')

            self.data['pre_issues'] = strings + specials + numbers
            print(self.data['pre_issues'])

        else:

            self.status_bar.set_status("Something went wonky. Check the total issues field.", 'warning')

    def select_all_issues(self, layout):
        for child in layout.children:
            child.state = 'down'

    def deselect_all_issues(self, layout):
        for child in layout.children:
            child.state = 'normal'

    def add_new_edition(self, container, edition_name, edition_issues):
        """ Add new edition to edition's section """
        new_edition = OtherEditionBox(container,
                                      edition_name.strip(),
                                      int(edition_issues),
                                      self.other_editions_data)

        container.add_widget(new_edition)
        self.edition_name_text.text = ''
        self.edition_issues_text.text = ''

    def add_annuals(self, container, edition_name, first, last):

        if not last.text:
            last.text = str(self.get_current_year())

        years = [year for year in range(int(first.text), int(last.text) + 1)]
        annuals = AnnualsEditionBox(container,
                                    edition_name.text,
                                    years,
                                    self.other_editions_data)

        container.add_widget(annuals)
        edition_name.text = ''
        first.text = ''
        last.text = ''

    def add_issue_note(self, issue_number_widget, issue_note_widget):
        """ Add note to specific issue"""

        issue_note = issue_note_widget.text
        issues = [i.strip() for i in issue_number_widget.text.split(',')]

        for issue in issues:

            if match(r'^\d+[-]\d+$', issue):
                start, end = issue.split('-')
                for multi_issue in range(int(start), int(end) + 1):
                    self.issue_notes[multi_issue] = issue_note
            else:
                self.issue_notes[IssueToggleButton.convert_issue_number(issue)] = issue_note

        issue_number_widget.text = ''
        issue_note_widget.text = ''
        issue_number_widget.focus = True

# SUBMIT FUNCTIONS ####################

    def create_publisher_list(self):
        """ Check whether more than one publisher is entered and update list accordingly """

        # create empty list
        publisher_list = []

        # check whether any popular publishers are selected
        # add them to list, if necessary
        if self.publisher_dc_toggle.state == 'down':
            publisher_list.append('DC')
        if self.publisher_marvel_toggle.state == 'down':
            publisher_list.append('Marvel')
        if self.publisher_dark_horse_toggle.state == 'down':
            publisher_list.append('Dark Horse')
        if self.publisher_image_toggle.state == 'down':
            publisher_list.append('Image')

        # add other publisher(s), if any
        if self.other_publisher_toggle.state == 'down' and self.publisher_text:
            for p in [i.strip() for i in self.publisher_text.split(',')]:
                if p and p not in publisher_list:
                    publisher_list.append(p)

        return publisher_list

    def add_new_publisher(self, app, publisher_list):
        """ Check whether any new publishers were mentioned, if so add them to database"""

        for p in publisher_list:
            if not app.db_cursor().execute("SELECT * FROM PUBLISHERS where publisher IS '{}'".format(p)).fetchone():
                app.create_publisher_table(app.db_cursor(), p)

    def set_table_name(self, publisher_list):
        """ Return table name, created from  publisher_list"""

        if len(publisher_list) > 1:
            # if more than one publisher is selected/entered
            return 'InterCompany'
        else:
            # if only one publisher is selected/entered, format name
            return publisher_list[0].replace(' ', '_')

    def set_publishers(self, db_cursor, publisher_list):
        """ Return a sorted list of publisher id numbers """

        publishers = []
        for p in publisher_list:
            sql = "SELECT id FROM PUBLISHERS WHERE publisher IS '{}'".format(p)
            publishers.append(db_cursor.execute(sql).fetchone()[0])

        return sorted(publishers)

    def set_format(self, db_cursor):

        db_cursor.execute("SELECT id FROM FORMATS WHERE format IS '{}'".format(self.data['format']))
        format_id = db_cursor.fetchone()
        if not format_id:
            db_cursor.execute("INSERT INTO FORMATS('format') VALUES('{}')".format(self.data['format']))
            self.data['format'] = db_cursor.lastrowid
        else:
            self.data['format'] = format_id

    def focus_special_issue(self, special_issue_container):
        """ Focus on first top most widget of special issues if any """
        if special_issue_container.children:
            special_issue_container.children[-1].ids._issue_note_text.focus = True


# ERROR CHECKING

    def validate_user_input(self):
        """ Check whether all necessary fields are filled out"""
        # TODO check if owned issues were selected
        if not self.publisher_count and not self.other_publisher_text.text:
            print("No publisher selected / entered")
        elif self.other_publisher_text.current_suggested_word:
            print('Check Publisher(s) Other text')
        elif not self.title_text.text:
            print('No comic title entered')
        elif not self.issues_text.text:
            print('No total issues amount entered')
        elif self.edition_name_text.text:
            print("Other editions field still has some text. Did you forget to click 'Add'")
        elif not self.compare_issues_to_owned_issues():
            print("There was a problem with selected owned issues.")
        else:
            print("Data suffices for submission")
            return True
        print('Submission canceled, see reasons above')
        return False

    def compare_issues_to_owned_issues(self):
        """ Check whether issues are selected, but have higher numbers than total issues

            For more information read remove_excess_issues() docstring"""
        # empty errors_list
        self.errors = []
        issues_in_run = list(range(1, self.data['issues_in_run'] + 1))
        # check for mistakes and add them to errors list, if necessary
        for i in self.data['owned_issues']:
            if i not in self.data['pre_issues'] and i not in issues_in_run:
                self.errors.append(i)
        # give user control
        if self.errors:
            self.status_bar.confirm("You've somehow selected {} issue(s) not contained in given data. ".format(len(self.errors)) +
                                    "Does everything look right?", self.remove_excess_issues,
                                    "I'll check/correct it.", "Yes, the application messed up!")
            return False
        return True

    def remove_excess_issues(self):
        """ This should never be called, but mistakes happen

            The reason for this being possible is because of the issues being dynamically added to the screen.
            It is possible to add 20 issues and select eg. 18, 19 and 20. Changing the total issue count to 15
            would leave 18, 19, and 20 still in the owned issues list. I could remove it, but I'd rather do the above
            check before writing to the database instead of the user accidentally changing the the issue number and
            and losing some of the selection he already has.
        """
        print('Removing excess issues')
        for e in range(len(self.errors)):
            self.data['owned_issues'].remove(self.errors.pop())

    def sql_insert_from_dict(self, dictionary, table_name):
        """ Create an SQL command string from data dictionary """

        cols = ''
        vals = ''

        for k, v in dictionary.items():
            print(k, "->", str(v))

            # set NULL string if v empty
            if not v or v == 'None':
                v = 'null'

            # jsonify lists and dicts
            elif isinstance(v, list) or isinstance(v, dict):
                print('jsonifying', k)
                v = dumps(v)
                print("----->", v)

            # escape problem characters
            if isinstance(v, str) and "'" in v:
                print("editing", k)
                # for old, new in [('&', '&&'), ("'", "''"), ('%', '%%')]:
                #     v = v.replace(old, new)
                v = v.replace("'", "''")
                print("to:", v)

            # check if cols and vals already have values, if so add commas
            if cols:
                cols += ", "
            cols += str(k)

            if vals:
                vals += ", "

            if v == 'null':
                # handle null values
                vals += "{}".format(v)
            else:
                vals += "'{}'".format(v)

        return "INSERT INTO '{}' ({}) VALUES ({})".format(table_name, cols, vals)

    def reset_screen(self):
        """ Reset Screen to original state """

        # reset widgets and clear widget containers
        for i in self.ids:
            if i.endswith('_text'):
                self.ids[i].text = ''
            elif i.endswith('_toggle'):
                self.ids[i].state = 'normal'
            elif i.endswith('_container'):
                self.ids[i].clear_widgets()

        # empty dictionaries and lists, etc
        self.publisher_count = 0
        self.data = {'owned_issues': list(), 'issue_notes': dict()}
        self.other_editions_data = dict()

    def submit(self, app):
        print()
        for i in sorted(self.data):
            print("{}: '{}'".format(i, self.data[i]))
        print()
        return

        if not self.validate_user_input():
            return False

        # update publishers if more than one is given
        publisher_list = self.create_publisher_list()
        table_name = self.set_table_name(publisher_list)

        # set other_editions
        self.data['other_editions'] = self.other_editions_data

        cur = app.db_cursor()

        self.set_format(cur)

        self.add_new_publisher(app, publisher_list)

        if table_name == 'InterCompany':
            self.data['publishers'] = self.set_publishers(cur, publisher_list)

        sql = self.sql_insert_from_dict(self.data, table_name)

        print(sql)

        cur.execute(sql)
        app.conn.commit()

        self.status_bar.set_status(self.data['title'] + " added to database", 'success')
        self.reset_screen()
