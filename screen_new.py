from kivy.lang import Builder
from kivy.properties import ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.label import Label

from json import dumps

from comics_widgets import AnnualsEditionBox, ComicsScreen, OtherEditionBox, IssueNoteBox, IssueToggleButton


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
    edition_name_text = ObjectProperty()
    edition_issues_text = ObjectProperty()

    status_bar = ObjectProperty()
    # issues_container = ObjectProperty()
    # editions_container = ObjectProperty()

    # user input
    publisher_count = NumericProperty(0)
    data = {'owned_issues': list(), 'issue_notes': dict()}
    other_editions_data = dict()

    # error handling
    errors = ListProperty()

    def on_data(self):
        print("data:", self.data)

    def create_pre_issues_lists(self, pre_issues):
        """ Return two sorted list containing pre_issues
                one list to contain values like '1a, 1b, etc.'
                and another list to int anf float values
        """

        # create two empty list
        strings_list = []
        numbers_list = []

        # split numeric values from strings
        for issue in [i.strip() for i in pre_issues.split(',')]:
            if not issue:
                # handle trailing (or just extra) commas
                continue
            elif issue.isnumeric():
                # handle ints and numbers bigger than 0
                if int(issue) < 1:
                    numbers_list.append(int(issue))
            elif issue.isalnum() or issue.isalpha():
                # handle issues like '1a', '1b', etc.
                strings_list.append(issue)
                #TODO handles xx / _ issues
            else:
                # the rest should be floats
                numbers_list.append(float(issue))

        # sort lists
        strings_list.sort()
        numbers_list.sort()

        # update data dict with newly formatted values
        self.data['pre_issues'] = strings_list + numbers_list

        # return sorted lists
        return sorted(strings_list), sorted(numbers_list)

    def populate_issue_container(self, container, user_data, issue_list):
        """ Add issue buttons to issues container box """

        # error handling, after receiving n problem once (this is probably unnecessary)
        if isinstance(issue_list, int):
            issue_list = list(range(1, issue_list + 1))

        for i in issue_list:
            # create button
            new_issue_toggle = IssueToggleButton(container, user_data, text=str(i))
            # check whether it should be in a down state
            if i in self.data['owned_issues']:
                new_issue_toggle.state = 'down'
            # add button to container
            container.add_widget(new_issue_toggle)
        # fill up empty space to make it took prettier
        if len(issue_list) < 10:
            for i in range(10 - len(issue_list) % 10):
                container.add_widget(Label(size_hint=(1, 1)))

    def load_issues(self, container, no_of_issues, pre_issues, user_data):

        # clear anything that's already there
        container.clear_widgets()

        # if a value for pre_issues is present
        if pre_issues:
            # create sorted two different sorted lists depending on data type
            strings, numbers = self.create_pre_issues_lists(pre_issues)

            if strings:
                self.populate_issue_container(container, user_data, strings)
            if numbers:
                self.populate_issue_container(container, user_data, numbers)
        else:
            self.data['pre_issues'] = []

        self.populate_issue_container(container, user_data, no_of_issues)

    def select_all_issues(self, layout):
        for child in layout.children:
            child.state = 'down'

    def deselect_all_issues(self, layout):
        for child in layout.children:
            child.state = 'normal'

    def add_new_edition(self, container, edition_name, edition_issues):
        """ Add new edition to edition's section """
        new_edition = OtherEditionBox(container,
                                      edition_name,
                                      edition_issues,
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

    def add_issue_note(self, container, issue_number_widget, issue_note_widget):
        """ Add note to specific issue"""

        issue_number = issue_number_widget.text.strip()
        issue_note = issue_note_widget.text.strip()
        # add note to data dict
        self.data['issue_notes'][issue_number] = issue_note
        # add issue note box to notes container
        container.add_widget(IssueNoteBox(issue_number, issue_note, self.data['issue_notes']))
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

    def add_new_publisher(self, app, db_cursor, publisher_list):
        """ Check whether any new publishers were mentioned, if so add them to database"""

        for p in publisher_list:
            if not db_cursor.execute("SELECT * FROM Publishers where publisher IS '{}'".format(p)).fetchone():
                app.create_publisher_table(p)

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
            sql = "SELECT id FROM Publishers WHERE publisher IS '{}'".format(p)
            publishers.append(db_cursor.execute(sql).fetchone()[0])

        return sorted(publishers)

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
        print("pre_issues", self.data['pre_issues'])
        print("owned_issues", self.data['owned_issues'])
        print("issues_in_run", issues_in_run)
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
            if isinstance(v, str) and not v:
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

        if not self.validate_user_input():
            return False

        # update publishers if more than one is given
        publisher_list = self.create_publisher_list()
        table_name = self.set_table_name(publisher_list)

        # set other_editions
        self.data['other_editions'] = self.other_editions_data

        app.connect_db()

        self.add_new_publisher(app, app.cur, publisher_list)

        if table_name == 'InterCompany':
            self.data['publishers'] = self.set_publishers(app.cur, publisher_list)

        sql = self.sql_insert_from_dict(self.data, table_name)

        print(sql)

        app.cur.execute(sql)
        app.conn.commit()
        app.conn.close()

        self.status_bar.set_status(self.data['title'] + " added to database", 'success')
        self.reset_screen()
