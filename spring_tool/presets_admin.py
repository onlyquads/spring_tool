from PySide2 import QtCore
from PySide2.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QTreeView)
from PySide2.QtGui import QStandardItemModel, QStandardItem
from spring_tool.spring_tool import (
    TOOLNAME, maya_main_window)
from spring_tool import presets
import maya.cmds as mc
import json


class SpringToolPresetAdmin(QWidget):
    def __init__(
            self,
            parent=None,
            prod_root_env_name=None,
            presets_dir_path=None,
            presets_filename=None,
            authorized_access=False
            ):

        if not authorized_access:
            presets.show_error_message('Access Denied')
            raise Exception('Access Denied')

        if not parent:
            parent = maya_main_window()
        super(SpringToolPresetAdmin, self).__init__(parent=parent)

        self.setWindowTitle(TOOLNAME)
        self.setWindowFlags(QtCore.Qt.Tool)

        self.presets_file_path = presets.get_presets_file_path(
            prod_root_env_name,
            presets_dir_path,
            presets_filename,
            is_admin=True
        )

        self.load_preset_admin_ui()

    def load_json_data(self):
        # Load JSON data
        with open(self.presets_file_path, 'r') as file:
            self.json_data = json.load(file)

    def load_qtree_view(self):

        self.load_json_data()

        # Create QTreeView
        self.tree_view = QTreeView(self)

        # Create a model
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Name'])

        # Populate the model with top-level and second-level keys
        self.populate_tree(self.json_data, self.model.invisibleRootItem())

        # Set the model for the QTreeView
        self.tree_view.setModel(self.model)

        # Enable sorting
        self.tree_view.setSortingEnabled(True)
        self.model.sort(0, QtCore.Qt.AscendingOrder)

        self.tree_view.selectionModel().selectionChanged.connect(
            self.check_item_level)

        # Layout
        self.qtree_layout = QVBoxLayout()
        self.qtree_layout.addWidget(self.tree_view)
        self.setLayout(self.qtree_layout)

        # Set up the main window
        self.setWindowTitle('Presets Administration Panel')
        self.setMinimumWidth(200)

    def populate_tree(self, json_data, parent_item):
        """
        Populate the QTreeView with the first and second levels of keys
        from the JSON data.
        """
        if isinstance(json_data, dict):
            # Add first-level keys
            for key, value in json_data.items():
                first_level_item = QStandardItem(key)
                parent_item.appendRow(first_level_item)

                # Add second-level keys if the value is a dictionary
                if isinstance(value, dict):
                    self.add_second_level_keys(value, first_level_item)

    def add_second_level_keys(self, json_data, parent_item):
        if isinstance(json_data, dict):
            for key in json_data:
                second_level_item = QStandardItem(key)
                parent_item.appendRow(second_level_item)

    def refresh_qtree(self):
        """
        Refresh the QTreeView by reloading the JSON data and
        repopulating the tree.
        """
        # Clear the existing model
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Name'])

        self.load_json_data()

        # Repopulate the model with new data
        self.populate_tree(self.json_data, self.model.invisibleRootItem())

        # Enable sorting again after repopulation
        self.tree_view.setSortingEnabled(True)
        self.model.sort(0, QtCore.Qt.AscendingOrder)

    def load_preset_admin_ui(self):
        layout = QVBoxLayout(self)

        self.presets_main_layout = QVBoxLayout()
        self.load_qtree_view()
        self.presets_main_layout.addWidget(self.tree_view)
        presets_options_layout = QHBoxLayout()
        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.clicked.connect(self.refresh_qtree)

        self.edit_preset_value_button = QPushButton('Edit Preset Values')
        self.edit_preset_value_button.clicked.connect(
            self.edit_saved_preset_pressed)
        self.edit_preset_value_button.setEnabled(False)
        edit_name_button = QPushButton('Edit Preset Name')
        edit_name_button.clicked.connect(self.rename_presset_pressed)
        remove_preset_button = QPushButton('Remove')
        remove_preset_button.clicked.connect(self.remove_selected_preset)
        presets_options_layout.addWidget(self.edit_preset_value_button)
        presets_options_layout.addWidget(edit_name_button)
        layout.addLayout(self.presets_main_layout)
        layout.addLayout(presets_options_layout)
        layout.addWidget(remove_preset_button)
        layout.addWidget(self.refresh_button)

        layout.addStretch()

    def get_selected_item(self):

        # Get the selected item
        indexes = self.tree_view.selectionModel().selectedIndexes()
        if indexes:
            selected_item = indexes[0]
            item_text = selected_item.data()  # Retrieve the selected item text

            # Check if there is a parent
            parent_item = selected_item.parent()
            if parent_item.isValid():
                parent_text = parent_item.data()
            else:
                parent_text = None
        else:
            # Selected item is None
            parent_text = None
            item_text = None

        return parent_text, item_text

    def check_item_level(self):
        """
        Enable the button if a second-level item is selected.
        Disable it if a first-level item is selected.
        """
        # Get the selected indexes
        selected_indexes = self.tree_view.selectionModel().selectedIndexes()

        if not selected_indexes:
            return

        # Get the first selected item
        index = selected_indexes[0]

        # Check if the selected item has a parent
        # QtCore.QModelIndex() means it's a first-level item
        if index.parent() == QtCore.QModelIndex():
            self.edit_preset_value_button.setEnabled(False)
        else:
            self.edit_preset_value_button.setEnabled(True)

    def remove_selected_preset(self):
        parent_name, item_text = self.get_selected_item()

        if not item_text:
            return mc.warning('No preset selected')

        if presets.show_warning_message(
                'Are you sure you want to remove this preset?'):
            presets.remove_preset(
                self.presets_file_path,
                character_name=parent_name or item_text,
                body_part=None if not parent_name else item_text
            )
            self.refresh_qtree()

    def on_character_changed(self):
        '''refresh the available body parts in UI list'''
        self.body_parts_list.clear()
        current_character = self.character_combo.currentText()
        saved_presets = presets.get_available_body_parts(
            self.presets_file_path, current_character)
        if not saved_presets:
            return
        if saved_presets is not None:
            self.body_parts_list.addItems(saved_presets)

    def refresh_characters_combobox(self):
        '''
        Refresh the characters available in pref files. Clear existing and
        populate it.
        '''
        self.character_combo.clear()
        saved_char_list = presets.get_available_characters(
            self.presets_file_path)
        saved_char_list.sort()
        if not saved_char_list:
            return
        for char in saved_char_list:
            self.character_combo.addItem(char)

    def rename_presset_pressed(self):
        parent_text, item_text = self.get_selected_item()
        presets.rename_preset(
            self.presets_file_path,
            parent_text,
            item_text,
            )
        self.refresh_qtree()

    def edit_saved_preset_pressed(self):
        '''
        Show the save preset popup window.
        Store existing main UI's values and pass it to the popup window
        '''
        if not self.presets_file_path:
            return mc.warning(
                'Path to presets not set/found.')

        parent_item, item_text = self.get_selected_item()
        if not parent_item:
            return mc.warning('No body part selected.')

        char_name = parent_item
        body_part_name = item_text
        spring_mode, spring_value, spring_rigidity, decay, pos = (
            presets.get_all_data(
                path=self.presets_file_path,
                character_name=char_name,
                body_part=body_part_name
            )
        )

        self.preset_window = presets.SavePresetPopup(
            self,
            self.presets_file_path,
            spring_mode,
            spring_value,
            spring_rigidity,
            decay,
            position=pos,
            char_name=char_name,
            body_part=body_part_name,
            edit_mode=True
            )
        self.preset_window.refresh_signal.connect(
            self.refresh_qtree)
        self.preset_window.show()


def show_preset_admin():
    global window
    if window is not None:
        window.close()
    window = SpringToolPresetAdmin()
    window.show()
