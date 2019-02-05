from kivy.app import App
from kivy.config import Config
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager

from os.path import isfile
from sqlite3 import connect
from screen_new import ScreenNew, ScreenHome


# configure app
Config.set('kivy', 'desktop', 1)
Config.set('graphics', 'borderless', 0)
Config.set('graphics', 'resizable', 0)
Config.set('graphics', 'window_state', 'maximized')
# Config.set('graphics', 'width', 1366)
# Config.set('graphics', 'height', 768)


class ComicsApp(App):

    # database
    db_path = 'database/ComicsDatabase.db'
    conn = ObjectProperty()

    comic_publishers = ('Marvel', 'DC', 'Dark Horse', 'Image')

    # add screen manager and load first page
    pages = ScreenManager()
    pages.add_widget(ScreenNew(name='screen_new'))

    def build(self):
        self.title = 'Holger\'s Comic Collection'
        self.create_comics_database()
        return self.pages

    def db_cursor(self):
        """ Return database cursor """
        return self.conn.cursor()

    def create_comics_database(self):
        """ Create a database, is it doesn't exist already"""

        if not isfile(self.db_path): # check whether database file exists and create if necessary
            print('Creating {} file'.format(self.db_path))
            self.conn = connect(self.db_path)
            cur = self.db_cursor()

            self.create_settings_table(cur)
            self.create_formats_table(cur)
            self.create_publishers_table(cur)
            self.create_inter_company_table(cur)

            for p in self.comic_publishers:
                self.create_publisher_table(cur, p)

            print('{} creation complete'.format(self.db_path.split('/')[-1].split('.')[0]))
            self.conn.commit()
        else:
            print('Database exists at \'{}\''.format(self.db_path))
            self.conn = connect(self.db_path)

    @staticmethod
    def create_settings_table(db_cursor):
        """ Create settings table """

        db_cursor.execute("""CREATE TABLE 'SETTINGS'(
                          'last_backup' TEXT,
                          'changes_since_backup' INTEGER)""")
        print("SETTINGS table created")

    @staticmethod
    def create_formats_table(db_cursor):
        """ Create FORMATS table """

        db_cursor.execute("""CREATE TABLE 'FORMATS'(
                          'id' INTEGER NOT NULL PRIMARY KEY,
                          'format' TEXT UNIQUE NOT NULL)""")
        print("FORMATS table created")

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
                          'notes' TEXT,
                          'issue_notes' TEXT)""".format(publisher.replace(" ", "_")))
        print("Publisher table for {} created".format(publisher), end=' -> ')

        # add publisher to PUBLISHERS table
        db_cursor.execute("INSERT INTO PUBLISHERS ('publisher') VALUES ('{}')".format(publisher))
        print("{} added to PUBLISHERS table".format(publisher))

    @staticmethod
    def create_inter_company_table(db_cursor):
        """ Create table for inter company cross overs"""

        db_cursor.execute("""CREATE TABLE 'InterCompany'(
                          'id' INTEGER NOT NULL PRIMARY KEY,
                          'publishers' TEXT NOT NULL,
                          'title' TEXT NOT NULL,
                          'format' TEXT, 
                          'volume' TEXT,
                          'standard_issues' INTEGER NOT NULL,
                          'odd_issues' TEXT,
                          'owned_issues' TEXT NOT NULL,
                          'other_editions' TEXT,
                          'start_date' TEXT,
                          'end_date' TEXT,
                          'notes' TEXT,
                          'issue_notes' TEXT)""")
        print("InterCompany table created")


if __name__ == '__main__':
    ComicsApp().run()
