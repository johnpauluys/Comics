from kivy.lang import Builder
from kivy.properties import BooleanProperty, DictProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.label import Label

from json import dumps, loads
from re import match

from comics_widgets import ComicListWidget, ComicsScreen


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
        """ Set up class """
        self.publishers = self.set_publishers(cur)
        self.publisher_keys = self.get_table_fields(cur, self.publishers[1])
        self.inter_keys = self.get_table_fields(cur, 'InterCompany')

        titles = self.load_all_titles(cur)
        self.show_titles(titles)

    def load_all_titles(self, cur):
        """ Return sorted list of all titles by all publishers """

        titles = []
        # get titles from publishers
        for p_id in self.publishers:
            titles += self.get_publisher_titles(cur, p_id)
        # get titles from inter company cross overs
        titles += self.get_inter_company_titles(cur)

        return self.sort_ignore_prefix(titles)

    @staticmethod
    def set_publishers(cur):
        """ Return dictionary of publishers
            1: 'publisher1'
            2: 'publisher2'
        """
        return {p[0]: p[1] for p in cur.execute("SELECT id, publisher FROM PUBLISHERS").fetchall()}

    @staticmethod
    def get_table_fields(cur, table_name):
        """ Return list of fields (column names) of specified table """
        cur.execute("SELECT * FROM {}".format(table_name)).fetchone()
        return list(map(lambda a: a[0], cur.description))

    def show_titles(self, titles):
        """ Load title widgets """

        if self.titles_container.children:
            self.titles_container.clear_widgets()

        for t in titles:
            # append '*' to inter company titles
            if 'publishers' in t:
                t['title'] += '*'

            title_label = ComicListWidget(t['title'],
                                          t['volume'],
                                          t['format'],
                                          t['standard_issues'],
                                          t['odd_issues'],
                                          t['owned_issues'],
                                          t['other_editions'],
                                          t['start_date'],
                                          t['end_date'],
                                          t['notes'],
                                          t['issue_notes'])
            self.titles_container.add_widget(title_label)

    def get_publisher_titles(self, cur, p_id):
        """ Return a list of titles [dict] by publisher """

        # set table name
        table = self.get_publisher_table(self.publishers[p_id])
        # get titles from db
        titles = cur.execute("SELECT * FROM {}".format(table)).fetchall()

        return self.cleanup_titles(titles, self.publisher_keys)

    def get_inter_company_titles(self, cur):
        """ Return a list of inter company cross over titles """

        titles = cur.execute("SELECT * FROM InterCompany").fetchall()
        return self.cleanup_titles(titles, self.inter_keys)

    def cleanup_titles(self, titles, keys):
        """ Zip dictionary and jsonify dicts and lists from database """
        titles = [self.zip_titles(t, keys) for t in titles]
        titles = self.json_loads_dict(titles)

        return titles

    @staticmethod
    def zip_titles(sql_tuple, keys):
        """ Return a dictionary zipped from list of keys and sql tuples"""

        return dict(zip(keys, sql_tuple))

    @staticmethod
    def json_loads_dict(titles_list):
        """ json.loads all fields where possible and return jsonified dict """

        jsonable_fields = ['odd_issues', 'other_editions', 'issue_notes', 'publishers']
        for title in titles_list:
            for f in jsonable_fields:
                try:
                    if title[f]:
                        title[f] = loads(title[f])
                except KeyError:
                    pass
            if title['owned_issues'] != 'complete':
                title['owned_issues'] = loads(title['owned_issues'])

        return titles_list

    @staticmethod
    def get_publisher_table(publisher):
        return publisher.replace(' ', '_')

    @staticmethod
    def sort_ignore_prefix(unsorted_list, ignore='the '):
        """ Return list sorted database indices ignore specified prefix """

        # sort list ignoring 'the' (default)
        return sorted(unsorted_list, key=lambda a: a['title'][len(ignore):] if a['title'].lower().startswith(ignore) else a['title'])
