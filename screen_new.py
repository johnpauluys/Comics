from kivy.lang import Builder
from kivy.properties import BooleanProperty, DictProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty

from json import dumps
from re import match

from comics_widgets import AnnualsEditionBox, ComicsScreen, IssueNoteBox,\
                           IssueToggleButton, OtherEditionBox, SpecialIssueNoteInputBox
from issues_box import IssuesBox

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
    start_date_text = ObjectProperty()
    end_date_text = ObjectProperty()
    # odd_issues_container = ObjectProperty()

    group_chain = ListProperty()
    grouping_text = StringProperty()
    standard_issues_container = ObjectProperty()

    edition_name_text = ObjectProperty()
    edition_issues_text = ObjectProperty()

    status_bar = ObjectProperty()

    # user input
    publisher_count = NumericProperty(0)
    standard_issues = ListProperty()
    issue_notes = DictProperty()
    special_issues = ListProperty()

    issues = DictProperty()
    ongoing_series = BooleanProperty(False)

    data = {'issues': dict(), 'owned_issues': list(), 'issue_notes': dict()}
    other_editions_data = dict()

    # error handling
    errors = ListProperty()

    # debugging methods
    @staticmethod
    def on_ongoing_series(instance, value):
        print("{}: series marked as ongoing".format(instance.__class__.__name__)) if value else None

    def on_group_chain(self, instance, value):
        """ Update grouping text to show current selected group(s) """
        self.grouping_text = ' - '.join(value)

    def set_grouping_info(self, cur, group_name_field):
        """ Set grouping info list to represent grouping chain """

        # create a list text from group_name_field, before clearing it
        group_name = group_name_field.text.split(',')
        group_name_field.text = ''

        for g in group_name:
            # strip whitespace
            g = g.strip()
            # return (id, group_name, parent_id) if group exists in database
            group_info = self.check_group_exists(cur, g)

            if group_info:
                # if group (g) exists, create group chain
                self.group_chain = self.create_group_chain(cur, group_info)

            else:
                # if group doesn't exist, append it to group chain
                self.group_chain.append(g)

    def check_group_exists(self, cur, group_name):
        """ Check whether entered group name exists in data base """
        # check database for group and return result
        return cur.execute("SELECT * FROM GROUPS WHERE name IS '{}' COLLATE NOCASE".format(group_name)).fetchone()

    def create_group_chain(self, cur, group_info):

        # set group_name as group_chain's first value
        group_chain = [group_info[1]]
        # and set previous chain to current group's parent
        prev_link = group_info[-1]

        while prev_link:
            # get current group's parent
            parent_info = cur.execute("SELECT * FROM GROUPS WHERE id IS '{}'".format(prev_link)).fetchone()
            # set prev_link to current parents' parent_id
            prev_link = parent_info[-1]
            # insert parent's name into beginning of group_tree list
            group_chain.insert(0, parent_info[1])

        return group_chain

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

    def create_odd_issues_lists(self, odd_issues):
        """ Return three sorted list containing odd_issues
                one list to contain values like '1a, 1b, etc.'
                and another list to int anf float values
        """
        # create two empty list
        strings_list = []
        numbers_list = []
        special_list = []
        error_list = []

        # split numeric values from strings
        for issue in set([i.strip() for i in odd_issues.split(',')]):
            # handle trailing (or just extra) commas by checking if issue
            if issue:
                # convert to appropriate
                issue = IssueToggleButton.convert_issue_number(issue)

                if isinstance(issue, int) or isinstance(issue, float):
                    if issue not in self.standard_issues:
                        numbers_list.append(issue)
                    else:
                        error_list.append(str(issue))
                elif isinstance(issue, str):
                    if '_' in issue:
                        if int(issue.split('_')[0]) in self.standard_issues:
                            special_list.append(issue)
                        else:
                            error_list.append(issue)
                    else:
                        strings_list.append(issue)

        # sort lists
        strings_list.sort()
        special_list.sort(key=lambda a: int(a.split('_')[0]))
        numbers_list.sort()

        # return sorted lists
        return strings_list, special_list, numbers_list, error_list

    def load_odd_issues(self, status_bar):

        self.odd_issues_container.clear_widgets()

        issues = self.odd_issues_text.text.strip()

        # split string up into different formats
        strings, specials, numbers, errors = self.create_odd_issues_lists(issues)

        # populate odd_issues_container
        if strings or specials:
            self.populate_issue_container(self.odd_issues_container, strings + specials)
        if numbers:
            self.populate_issue_container(self.odd_issues_container, numbers)

        self.special_issues = specials

        # update data dict with newly formatted values
        print('setting odd_issues to:')

        self.data['odd_issues'] = strings + specials + numbers
        print(self.data['odd_issues'])

        if errors:
            if len(errors) > 1:
                error_msg = "The following conflicts occurred:"
            else:
                error_msg = "The following conflict occurred:"
            doubles, variants = [], []
            for error in errors:
                if '_' in error:
                    variants.append(error)
                else:
                    doubles.append(error)
            if doubles:
                if len(doubles) > 1:
                    error_msg += " {} exist in standard issues.".format(', '.join(sorted(doubles)))
                else:
                    error_msg += " {} exists in standard issues.".format(doubles[0])
            if variants:
                if len(variants) > 1:
                    error_msg += " {} must exist in standard issues, as they are variants.".format(', '.join(variants))
                else:
                    error_msg += " {} must exist in standard issues, as it considered a variant.".format(variants[0])

            status_bar.set_status(error_msg, 'notice')

    def select_issue_range(self, range_input, layouts_list):
        """ Select issues """

        issues = []
        for n in [i.strip() for i in range_input.text.split(',')]:
            if match(r'^[1-9]\d*\-[1-9]\d*', n):
                start, end = n.split('-')
                issues += [str(issue) for issue in list(range(int(start), int(end) + 1))]
            else:
                issues.append(n)

        for layout in layouts_list:
            for child in layout.children:
                if child.text in issues:
                    print(child.text, issues)
                    child.state = 'down'
                    issues.remove(child.text)
        if issues:
            missing_issues = ', '.join(issues)
            self.status_bar.set_status("Something went wrong. {} not in issues.".format(missing_issues), 'notice')
            range_input.text = missing_issues
            range_input.select_all()
        else:
            range_input.text = ''
        range_input.focus = True

    def select_all_issues(self, layouts_list):

        for layout in layouts_list:

            for child in layout.children:
                child.state = 'down'

    def deselect_all_issues(self, layouts_list):

        for layout in layouts_list:
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

    def add_annuals(self, ed_container, edition_name, ed_issues_text):

        # regex matches
        single_number = r'^[1-9]\d{0,2}$'
        single_year = r'^(19|20)\d{2}$'
        range_number = r'^[1-9]\d{0,2}\-[1-9]\d{0,2}$'
        range_year = '^(19|20)\d{2}\-(19|20)\d{2}$'

        issue_list = [i.strip() for i in ed_issues_text.text.split(',')]
        print(issue_list)
        issues = []

        # if len(issue_list) == 1 and match(single_number, issue_list[0]):
        #     no_of_issues = int(issue_list[0])
        #     issues = list(range(1, no_of_issues + 1))
        #     self.other_editions_data[edition_name.text] = {'owned_issues': [], 'no_of_issues': no_of_issues}

        for i in issue_list:
            if match(single_number, i) or match(single_year, i):
                    issues.append(int(i))
            elif match(range_year, i) or match(range_number, i):
                first, last = i.split('-')
                issues += [ed for ed in range(int(first), int(last) + 1)]

        self.other_editions_data[edition_name.text] = {'owned_issues': [], 'issues': issues}

        print(self.other_editions_data)
        annuals = AnnualsEditionBox(ed_container,
                                    edition_name.text,
                                    issues,
                                    self.other_editions_data)

        ed_container.add_widget(annuals)
        edition_name.text = ''
        ed_issues_text.text = ''
        edition_name.focus = True

    def add_annuals_old(self, container, edition_name, first, last):

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
