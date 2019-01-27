from kivy.app import App
from kivy.config import Config
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager

from os.path import isfile, isdir
from sqlite3 import connect
from screen_new import ScreenNew


# configure app
Config.set('graphics', 'window_state', 'maximized')
Config.set('graphics', 'borderless', 1)


class Settings:
    """ Class to store all settings """

    def __init__(self):
        """ Initiate app's settings """
        # database
        self.database = '../ComicDatabase.db'


class ComicsApp(App):

    settings = Settings()
    pages = ScreenManager()
    pages.add_widget(ScreenNew(name='screen_new'))

    # database
    conn = ObjectProperty()
    cur = ObjectProperty()

    def build(self):
        self.create_database()
        return self.pages

    def connect_db(self):
        print('DATABASE: connecting to database')
        self.conn = connect(self.settings.database)
        self.cur = self.conn.cursor()

    def commit_db(self):
        print('DATABASE: committing to database')
        self.conn.commit()

    def close_db(self):
        print('DATABASE: closing database')
        self.conn.close()

    def create_database(self):
        """ Create a database, is it doesn't exist already"""

        if not isfile(self.settings.database): # check whether database file exists

            self.connect_db()

            self.cur.execute("""CREATE TABLE IF NOT EXISTS 'Publishers'(
                            'id' INTEGER NOT NULL PRIMARY KEY,
                            'publisher' TEXT UNIQUE NOT NULL)
                            """)
            self.cur.execute("""CREATE TABLE IF NOT EXISTS 'InterCompany'(
                            'id' INTEGER NOT NULL PRIMARY KEY,
                            'publishers' TEXT,
                            'title' TEXT NOT NULL,
                            'volume' TEXT,
                            'issues_in_run' INTEGER NOT NULL,
                            'pre_issues' TEXT,
                            'owned_issues' TEXT NOT NULL,
                            'other_editions' TEXT,
                            'start_date' TEXT NOT NULL,
                            'end_date' TEXT NOT NULL,
                            'notes' TEXT,
                            'issue_notes' TEXT)
                            """)
            for p in ['Marvel', 'DC', 'Dark Horse', 'Image']:
                self.create_publisher_table(p)

            print('Database successfully created')
            self.conn.commit()
            self.conn.close()
        else:
            print('Database exists ({})'.format(self.settings.database))

    def create_publisher_table(self, publisher):
        """ Create new tables (publisher) """

        self.cur.execute("INSERT INTO Publishers ('publisher') VALUES ('{}')".format(publisher))
        self.cur.execute("""CREATE TABLE IF NOT EXISTS '{}'(
                            'id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                            'title' TEXT NOT NULL,
                            'volume' TEXT,
                            'issues_in_run' INTEGER NOT NULL,
                            'pre_issues' TEXT,
                            'owned_issues' TEXT NOT NULL,
                            'other_editions' TEXT, 
                            'start_date' TEXT,
                            'end_date' TEXT,
                            'notes' TEXT,
                            'issue_notes' TEXT)""".format(publisher.replace(" ", "_")))
        print("Successfully created publisher table for {}".format(publisher))


if __name__ == '__main__':
    ComicsApp().run()
