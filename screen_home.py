from kivy.lang import Builder
from kivy.properties import BooleanProperty, DictProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.label import Label

from json import dumps
from re import match

from comics_widgets import AnnualsEditionBox, ComicsScreen, IssueNoteBox, IssueToggleButton, OtherEditionBox, SpecialIssueNoteInputBox


Builder.load_file('screen_home.kv')


class ScreenHome(ComicsScreen):
    """ Screen to allow user to add a comic title, and relative information. """

    titles_container = ObjectProperty()
    status_bar = ObjectProperty()

    # list of dicts containing publisher id and name in PUBLISHERS table of database
    publishers = DictProperty()

    # database field names for each publishers and inter-company crossovers
    publisher_keys = ListProperty()
    inter_keys = ListProperty()

    def prepare_variables(self, cur):
        self.publishers = self.set_publishers(cur)
        self.publisher_keys = self.get_table_fields(cur, self.publishers[1])
        self.inter_keys = self.get_table_fields(cur, 'InterCompany')
        # print(self.publishers, self.publisher_keys, self.inter_keys)
        print('loading comic titles')

        self.get_titles_by_publisher(cur)


    def load_comic_titles(self, cur):
        print('loading comic titles')

        self.get_titles_by_publisher(cur)

    @staticmethod
    def set_publishers(cur):
        """ Return list of publishers """

        return {p[0]: p[1] for p in cur.execute("SELECT id, publisher FROM PUBLISHERS").fetchall()}

    @staticmethod
    def get_table_fields(cur, table_name):
        """ Return list of fields (column names) of specified table """
        cur.execute("SELECT * FROM {}".format(table_name)).fetchone()
        return list(map(lambda a: a[0], cur.description))

    def get_titles_by_publisher(self, cur):

        titles_by_publisher = dict()
        for p_id in self.publishers:
            table = self.publishers[p_id].replace(' ', '_')
            print(table)
            titles = cur.execute("SELECT id, title FROM {}".format(table)).fetchall()
            inter_sql = "SELECT id, title FROM InterCompany WHERE publishers LIKE '%{}%'".format(p_id)
            titles += ((str(i[0])+'+', i[1]) for i in cur.execute(inter_sql).fetchall())
            for title in titles:
                print(title)

            sorted_titles = list()
            for db_id in self.sort_ignore_prefix(titles):
                if isinstance(db_id, str):
                    db_id = int(db_id[:-1])
                    title = cur.execute("SELECT * FROM InterCompany WHERE id IS {}".format(db_id)).fetchall()[0]
                    sorted_titles.append(dict(zip(self.inter_keys, title)))
                else:
                    title = cur.execute("SELECT * FROM {} WHERE id IS {}".format(table, db_id)).fetchall()[0]
                    sorted_titles.append(dict(zip(self.publisher_keys, title)))
            titles_by_publisher[table] = sorted_titles

        print(titles_by_publisher)
        for publisher in sorted(titles_by_publisher):

            publisher_label = Label(text=publisher)
            self.titles_container.add_widget(publisher_label)
            for titles in titles_by_publisher[publisher]:
                if 'publishers' in titles:
                    titles['title'] += '*'
                title_label = Label(text="   " + titles['title'])
                self.titles_container.add_widget(title_label)

    @staticmethod
    def sort_ignore_prefix(unsorted_list, ignore='the '):
        """ Return list sorted database indices ignore specified prefix """

        # sort list ignoring the (default)
        ordered = sorted(unsorted_list, key=lambda a: a[1][len(ignore)] if a[1].lower().startswith(ignore) else a[1])
        # return indices
        return [i[0] for i in ordered]

    @staticmethod
    def true_sort(unsorted_list):
        """ Return list of sorted database indices ignoring articles in title names """

        articles = ('the', 'a', 'an')

        new_list = list()
        for i in unsorted_list:
            if i[1].lower().split()[0] in articles:
                temp_name = ' '.join(i[1].split()[1:])
                new_list.append((temp_name, i[0]))
            else:
                new_list.append((i[1], i[0]))

        sorted_titles = list()
        for item in sorted(new_list):
            for u in unsorted_list:
                # print(u)
                # print(u[0])
                if u[0] == item[1]:
                    sorted_titles.append(u[0])

        return sorted_titles
