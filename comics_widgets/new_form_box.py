from kivy.lang import Builder
from kivy.properties import ListProperty, NumericProperty, ObjectProperty, OptionProperty, StringProperty
from comics_widgets.comics_widgets import BoxLayout

Builder.load_file('comics_widgets/new_form_box.kv')


class NewFormBox(BoxLayout):

    publisher_dc_toggle = ObjectProperty()
    publisher_marvel_toggle = ObjectProperty()
    publisher_dark_horse_toggle = ObjectProperty()
    publisher_image_toggle = ObjectProperty()

    other_publisher_toggle = ObjectProperty()
    other_publisher_text = ObjectProperty()

    publisher_count = NumericProperty(0)
    ongoing_series = OptionProperty(0, options=[0, 1])

    group_chain = ListProperty()
    grouping_text = StringProperty()

    status_bar = ObjectProperty()

    form_data = {}

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
