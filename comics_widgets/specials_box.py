from kivy.lang import Builder
from comics_widgets.comics_widgets import BoxLayout, FieldBox, NumericProperty, ObjectProperty, StringProperty


Builder.load_file('comics_widgets/specials_box.kv')


class SpecialsBox(BoxLayout):

    comic_title = StringProperty()
    issues_box_issues_text = ObjectProperty()

    specials_container = ObjectProperty()
    specials_scroller = ObjectProperty()

    specials_data = {}

    def add_special(self, title, issues, fmt, start_date, end_date, notes):
        """ Add new special """

        # get copy of local variables
        local = locals()

        # create special widget
        new_special = SpecialEdition(self, self.specials_data, title, issues, fmt, start_date, end_date, notes)

        # create data dict entry (skipping self, locals copy and empty strings
        self.specials_data[new_special] = {k: local[k] for k in local if k not in ['self', 'local'] and local[k] != ''}

        # display new special to user
        self.specials_container.add_widget(new_special)

        self.clear_form()
        self.ids['_title_text'].focus = True

    def load_special(self, specials_dict):

        self.clear_form()

        for k, v in specials_dict.items():
            self.ids['_{}_text'.format(k)].text = v

    def clear_form(self):

        form_ids = [k for k in self.ids if k.endswith('_text')]
        for k in form_ids:
            self.ids[k].text = ''



    def print_data_dict(self):
        for k, v in self.specials_data.items():
            print("   {}\n{}".format(k, v))


class SpecialsContainer(BoxLayout):
    pass


class SpecialEdition(FieldBox):

    title = StringProperty('no title given')
    fmt = StringProperty('none')
    issues = NumericProperty('1')
    start_date = StringProperty()
    end_date = StringProperty()
    notes = StringProperty('no notes')

    def __init__(self, specials_form, specials_data, title, issues, fmt, start_date, end_date, notes, **kwargs):
        super(SpecialEdition, self).__init__(**kwargs)
        self.specials_form = specials_form
        self.specials_data = specials_data
        self.title = title
        self.issues = issues
        self.fmt = fmt
        self.start_date = start_date
        self.end_date = end_date
        self.notes = notes

    def delete_special(self):
        self.specials_form.load_special(self.specials_data[self])
        del self.specials_data[self]
        self.parent.remove_widget(self)
        print('deleted')
