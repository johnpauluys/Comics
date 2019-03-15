# screen_new_py
from kivy.lang import Builder
from json import dumps
from comics_widgets.comics_widgets import ComicsScreen, \
                                          BooleanProperty, DictProperty, ListProperty, NumericProperty,\
                                          ObjectProperty, StringProperty

Builder.load_file('screen_new.kv')


class ScreenNew(ComicsScreen):
    """ Screen to allow user to add a comic title, and relative information. """

    status_bar = ObjectProperty()
    ongoing_series = BooleanProperty(False)

    # error handling
    errors = ListProperty()

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
            return self.get_publisher_table_name(publisher_list[0])

    def set_publishers(self, db_cursor, publisher_list):
        """ Return a sorted list of publisher id numbers """

        publishers = []
        for p in publisher_list:
            sql = "SELECT id FROM PUBLISHERS WHERE publisher IS '{}'".format(p)
            publishers.append(db_cursor.execute(sql).fetchone()[0])

        return sorted(publishers)

    def set_group(self, app, cur):
        """ Prepare data['grouping'] for database """
        # set main group, which has no parent
        parent = None
        for g in self.group_chain:
            # query database to see if group exists
            current = cur.execute("SELECT * FROM GROUPS WHERE name IS '{}'".format(g)).fetchone()
            if current:
                # if it exists, nothing has to happen, except that it now becomes a potential parent
                parent = current[0]
            else:
                # create database entry if group doesn't exist
                parent = app.add_new_group(cur, g, parent)
        # the last group_name should now be the potential parent and its is value gets returned
        return parent

    def set_format(self, db_cursor):
        """ Sets format field to id of selected format
            If no id is available, format will be add to formats table
        """
        if 'format' not in self.data:
            return False
        elif not self.data['format']:
            return False

        # attempt to get id of entered format
        db_cursor.execute("SELECT id FROM FORMATS WHERE format IS '{}'".format(self.data['format']))
        format_id = db_cursor.fetchone()
        if not format_id:
            # add format to FORMATS table in db
            db_cursor.execute("INSERT INTO FORMATS('format') VALUES('{}')".format(self.data['format']))
            self.data['format'] = db_cursor.lastrowid
        else:
            self.data['format'] = format_id[0]

    def focus_special_issue(self, special_issue_container):
        """ Focus on first top most widget of special issues if any """
        if special_issue_container.children:
            special_issue_container.children[-1].ids._issue_note_text.focus = True

# ERROR CHECKING

    def validate_user_input(self):
        """ Check whether all necessary fields are filled out"""
        if not self.publisher_count and not self.other_publisher_text.text:
            error_msg = "No publisher selected / entered."
        elif not self.title_text.text:
            error_msg = "No comic title entered"
        # elif not self.standard_issues_text.text:
        #     error_msg = "No total issues amount entered"
        # TODO Check if issues are present
        elif self.edition_name_text.text:
            error_msg = "Other editions field still has some text. Did you forget to click 'Add'"
        elif self.special_issues:
            error_msg = "There are still open variation / 'joker' issues ( {} ).".format(', '.join(self.special_issues))
            error_msg += " Look at the notes section."
        elif not self.data['owned_issues']:
            error_msg = "You haven't selected any owned issues."
        elif not self.compare_issues_to_owned_issues():
            error_msg = "There was a problem with selected owned issues."
        else:
            print("Data suffices for submission")
            return True
        self.status_bar.set_status(error_msg + " Submission cancelled.", 'error')
        return False

    def compare_issues_to_owned_issues(self):
        """ Check whether issues are selected, but have higher numbers than total issues

            For more information read remove_excess_issues() docstring"""
        # empty errors_list
        self.errors = []
        # check for mistakes and add them to errors list, if necessary
        for i in self.data['owned_issues']:
            if i not in self.data['odd_issues'] and i not in self.standard_issues:
                self.errors.append(i)
        # give user control
        if self.errors:
            self.status_bar.confirm("You've somehow selected {} issue(s) not contained in given data. ".format(len(self.errors)) +
                                    "Does everything look right?", self.remove_excess_issues,
                                    "No, I'll correct it.", "Yes, I double checked!")
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

    def check_collection_complete(self):
        """ Sets owned_issues to complete if all issues owned"""

        if not self.ongoing_series:
            if len(self.data['owned_issues']) == len(self.standard_issues) + len(self.data['odd_issues']):
                self.data['owned_issues'] = 'complete'

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
                v = v.replace("'", "''")
                print("to:", v)

            # check if cols and vals already have values, if so add commas
            if cols:
                cols += ", "
            cols += "'{}'".format(str(k))

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
        self.standard_issues = []
        self.issue_notes = {}
        self.special_issues = []

        self.ongoing_series = False

        self.data = {'odd_issues': list(), 'owned_issues': list(), 'issue_notes': dict()}
        self.other_editions_data = dict()

        self.errors = []

    def print_all_data(self):

        print("""
        publisher_count: {}
        standard_issues: {}
        issue_notes: {}
        special_issues: {}
        ongoing_series: {}
        other_editions_data: {}
        data:""".format(self.publisher_count, self.standard_issues, self.issue_notes,
                   self.special_issues, self.ongoing_series, self.other_editions_data))
        for k in sorted(self.data):
            print("\t... {}: {}".format(k, self.data[k]))

    def submit(self, app):

        self.print_all_data()

        if not self.validate_user_input():
            return False

        # get cursor ready
        cur = app.db_cursor()

        # update publishers if more than one is given
        publisher_list = self.create_publisher_list()
        # add new publisher if necessary
        self.add_new_publisher(app, publisher_list)

        # set table name, depending on selected publisher(s)
        table_name = self.set_table_name(publisher_list)
        # set publishers list if more than one publisher was given
        if table_name == 'InterCompany':
            self.data['publishers'] = self.set_publishers(cur, publisher_list)

        # convert entered format to format id in FORMATS table
        self.set_format(cur)

        # add other_editions to data dict
        self.data['other_editions'] = self.other_editions_data

        # check collection completeness
        self.check_collection_complete()

        # set grouping
        self.data['grouping'] = self.set_group(app, cur)

        print()
        for i in sorted(self.data):
            print("{}: '{}'".format(i, self.data[i]))
        print()

        sql = self.sql_insert_from_dict(self.data, table_name)

        print(sql)

        cur.execute(sql)
        app.conn.commit()

        self.status_bar.set_status(self.data['title'] + " added to database", 'success')
        self.reset_screen()
