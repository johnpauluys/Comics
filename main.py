from kivy.app import App
from kivy.config import Config
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager

from os.path import isfile
from sqlite3 import connect, Error
from datetime import datetime

from screen_home import ScreenHome
from screen_new import ScreenNew


# configure app
# Config.set('kivy', 'desktop', 1)
# Config.set('graphics', 'borderless', 0)
# Config.set('graphics', 'resizable', 0)
# Config.set('graphics', 'window_state', 'maximized')
Config.set('graphics', 'width', 1366)
Config.set('graphics', 'height', 768)


class ComicsApp(App):

    # database
    db_path = 'database/ComicsDatabase.db'
    conn = ObjectProperty()

    comic_publishers = ('Marvel', 'DC', 'Dark Horse', 'Image')

    # add screen manager and load first page
    pages = ScreenManager()

    def build(self):
        self.title = 'Holger\'s Comic Collection'
        self.create_comics_database()
        # self.pages.add_widget(ScreenHome(name='screen_home'))
        self.pages.add_widget(ScreenNew(name='screen_new'))
        return self.pages

    def db_cursor(self):
        """ Return database cursor """
        return self.conn.cursor()

    def switch_screen(self, screen_name):
        """ Switch to screen """
        # check if given screen already being displayed
        if not self.pages.current == screen_name:
            # check if screen has already been loaded
            if not self.pages.has_screen(screen_name):
                # load if necessary
                if screen_name == 'screen_home':
                    self.pages.add_widget(ScreenHome(name='screen_home'))
                elif screen_name == 'screen_new':
                    self.pages.add_widget(ScreenNew(name='screen_new'))
            # switch to screen
            self.pages.current = screen_name

    def create_comics_database(self):
        """ Create a database, is it doesn't exist already"""

        start = datetime.now()
        if not isfile(self.db_path): # check whether database file exists and create if necessary
            try:
                print('Creating {} file'.format(self.db_path))
                self.conn = connect(self.db_path)
                cur = self.db_cursor()

                self.create_settings_table(cur)
                self.create_formats_table(cur)
                self.create_publishers_table(cur)
                self.create_inter_company_table(cur)
                self.create_groups_table(cur)

                for p in self.comic_publishers:
                    self.create_publisher_table(cur, p)

                print('{} creation complete'.format(self.db_path.split('/')[-1].split('.')[0]))
                self.conn.commit()

            except Error:
                print('ERROR, rolling back database')
                self.conn.rollback()
        else:
            print('Database exists at \'{}\''.format(self.db_path))
            self.conn = connect(self.db_path)
        print(datetime.now() - start)

    @staticmethod
    def create_formats_table(db_cursor):
        """ Create FORMATS table """

        db_cursor.execute("""CREATE TABLE 'FORMATS'(
                          'id' INTEGER NOT NULL PRIMARY KEY,
                          'format' TEXT UNIQUE NOT NULL)""")
        print("FORMATS table created")

    @staticmethod
    def create_groups_table(db_cursor):
        """ Create settings table """

        db_cursor.execute("""CREATE TABLE 'GROUPS'(
                          'id' INTEGER NOT NULL UNIQUE PRIMARY KEY,
                          'name' TEXT NOT NULL UNIQUE,
                          'parent' INTEGER)""")
        print("GROUPS table created")

    @staticmethod
    def create_inter_company_table(db_cursor):
        """ Create table for inter company cross overs"""

        db_cursor.execute("""CREATE TABLE 'InterCompany'(
                          'id' INTEGER NOT NULL PRIMARY KEY,
                          'publishers' TEXT NOT NULL,
                          'title' TEXT NOT NULL,
                          'volume' TEXT,
                          'format' TEXT, 
                          'standard_issues' INTEGER NOT NULL,
                          'odd_issues' TEXT,
                          'owned_issues' TEXT NOT NULL,
                          'other_editions' TEXT,
                          'start_date' TEXT,
                          'end_date' TEXT,
                          'grouping' TEXT,
                          'notes' TEXT,
                          'issue_notes' TEXT)""")
        print("InterCompany table created")

    @staticmethod
    def create_publishers_table(db_cursor):
        """ Create table to hold publishers """

        db_cursor.execute("""CREATE TABLE 'PUBLISHERS'(
                        'id' INTEGER NOT NULL PRIMARY KEY,
                        'publisher' TEXT UNIQUE NOT NULL)""")
        print("PUBLISHERS table created")


    @staticmethod
    def create_publisher_table(db_cursor, publisher):
        """ Create single publisher table """

        table = ScreenHome.get_publisher_table_name(publisher)

        # create table
        db_cursor.execute("""CREATE TABLE IF NOT EXISTS '{}'(
                          'id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                          'title' TEXT NOT NULL,
                          'volume' TEXT,
                          'format' INTEGER,
                          'standard_issues' INTEGER NOT NULL,
                          'odd_issues' TEXT,
                          'owned_issues' TEXT,
                          'other_editions' TEXT, 
                          'start_date' TEXT,
                          'end_date' TEXT,
                          'grouping' TEXT,
                          'notes' TEXT,
                          'issue_notes' TEXT)""".format(table))
        print("Publisher table for {} created".format(publisher), end=' -> ')

        # add publisher to PUBLISHERS table
        db_cursor.execute("INSERT INTO PUBLISHERS ('publisher') VALUES ('{}')".format(publisher))
        print("{} added to PUBLISHERS table".format(publisher))

    @staticmethod
    def create_settings_table(db_cursor):
        """ Create settings table """

        db_cursor.execute("""CREATE TABLE 'SETTINGS'(
                          'last_backup' TEXT,
                          'changes_since_backup' INTEGER)""")
        print("SETTINGS table created")

    def add_new_group(self, db_cursor, group_name, parent_id=None):

        sql = "INSERT INTO GROUPS (name, parent) VALUES ('{}', ".format(group_name)
        sql += "{})".format(parent_id) if parent_id else "NULL)"
        print(sql)

        db_cursor.execute(sql)
        return db_cursor.lastrowid


if __name__ == '__main__':
    ComicsApp().run()
