from kivy.lang import Builder
from kivy.properties import DictProperty, ListProperty, ObjectProperty

from json import loads

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

    def prepare_screen(self, cur):
        """ Set up class """

        self.publishers = self.set_publishers(cur)
        self.publisher_keys = self.get_table_fields(cur, self.publishers[1])
        self.inter_keys = self.get_table_fields(cur, 'InterCompany')

        titles = self.load_all_titles(cur)
        self.show_titles(titles)

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

    def load_all_titles(self, cur):
        """ Return sorted list of all titles by all publishers """
        titles = []
        # get titles from publishers
        for p_id in self.publishers:
            titles += self.get_publisher_titles(cur, p_id)
        # get titles from inter company cross overs
        titles += self.get_inter_company_titles(cur)

        return self.sort_ignore_prefix(titles)

    def get_publisher_titles(self, cur, p_id):
        """ Return a list of titles [dict] by publisher """
        # set table name
        publisher = self.publishers[p_id]
        table = self.get_publisher_table_name(publisher)
        # get titles from db
        titles = cur.execute("SELECT * FROM {}".format(table)).fetchall()
        titles = self.cleanup_titles(titles, self.publisher_keys)
        # add publisher field
        # TODO this was just a quick fix, refactor and create cleaner code
        for title in titles:
            title['publisher'] = publisher

        return titles

    def get_inter_company_titles(self, cur):
        """ Return a list of inter company cross over titles """
        titles = cur.execute("SELECT * FROM InterCompany").fetchall()
        return self.cleanup_titles(titles, self.inter_keys)

    def cleanup_titles(self, titles, keys):
        """ Zip dictionary and jsonify dicts and lists from database """
        titles = [self.zip_titles(t, keys) for t in titles]
        titles = self.json_loads_dict(titles)
        titles = self.set_none_values(titles)
        return titles

    @staticmethod
    def zip_titles(sql_tuple, keys):
        """ Return a dictionary zipped from list of keys and sql tuples"""
        return dict(zip(keys, sql_tuple))

    def json_loads_dict(self, titles_list):
        """ json.loads all fields where possible and return jsonified dict """

        json_fields = ['odd_issues', 'other_editions', 'issue_notes']
        for title in titles_list:
            for field in json_fields:
                try:
                    if title[field]:
                        title[field] = loads(title[field])
                except KeyError:
                    pass
            if title['owned_issues'] != 'complete':
                title['owned_issues'] = loads(title['owned_issues'])
            # set publishers
            if 'publishers' in title:
                # create string from list of publishers
                title['publishers'] = ', '.join(sorted(self.publishers[i] for i in loads(title['publishers'])))
        return titles_list

    @staticmethod
    def set_none_values(titles):
        """ Return appropriate (empty) data types from db NULL entries """
        for title in titles:
            if not title['notes']:
                title['notes'] = ''
            if not title['issue_notes']:
                title['issue_notes'] = {}
        return titles

    def show_titles(self, titles):
        """ Load title widgets """

        # clear widgets for a fresh reload
        if self.titles_container.children:
            self.titles_container.clear_widgets()

        for t in titles:
            # change title to reflect volume number
            if t['volume']:
                t['title'] += " (Vol. {})".format(str(t['volume']))
            # append '*' to inter company titles
            if 'publishers' in t:
                t['title'] += '*'
                title_label = ComicListWidget(t['title'],
                                              t['publishers'],
                                              t['volume'],
                                              t['format'],
                                              t['standard_issues'],
                                              t['odd_issues'],
                                              t['owned_issues'],
                                              t['other_editions'],
                                              t['start_date'],
                                              t['end_date'],
                                              t['grouping'],
                                              t['notes'],
                                              t['issue_notes'])
            else:
                # TODO part of earlier quick fix. surely this can be shortened
                title_label = ComicListWidget(t['title'],
                                              t['publisher'],
                                              t['volume'],
                                              t['format'],
                                              t['standard_issues'],
                                              t['odd_issues'],
                                              t['owned_issues'],
                                              t['other_editions'],
                                              t['start_date'],
                                              t['end_date'],
                                              t['grouping'],
                                              t['notes'],
                                              t['issue_notes'])
            self.titles_container.add_widget(title_label)
