'''
This part is still wip. Presets will show up but edition doesn't work
'''

from PySide2 import QtCore
from PySide2.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QComboBox, QListWidget, QMenu)
from spring_tool.spring_tool import (
    TOOLNAME, get_presets_file_path, SavePresetPopup)
from spring_tool import presets
import maya.cmds as mc


class SpringToolPresetAdmin(QWidget):
    def __init__(
            self,
            prod_root_env_name=None,
            presets_dir_path=None,
            presets_filename=None
            ):

        super(SpringToolPresetAdmin, self).__init__()

        self.setWindowTitle(TOOLNAME)
        self.setWindowFlags(QtCore.Qt.Tool)

        self.presets_file_path = get_presets_file_path(
            prod_root_env_name,
            presets_dir_path,
            presets_filename
        )

        self.load_preset_admin_ui()

    def load_preset_admin_ui(self):
        layout = QVBoxLayout(self)

        preset_choice_layout = QVBoxLayout()
        self.presets_main_layout = QVBoxLayout()
        self.character_combo = QComboBox()

        self.character_combo.currentIndexChanged.connect(
            self.on_character_changed)
        presets_refresh_button = QPushButton('Refresh')
        presets_refresh_button.clicked.connect(
            self.refresh_characters_combobox)

        self.body_parts_list_menu = QMenu()
        self.body_parts_list = QListWidget()
        self.body_parts_list.setFixedHeight(133)

        # Populate combobox
        self.refresh_characters_combobox()

        preset_choice_layout.addWidget(self.character_combo)
        preset_choice_layout.addWidget(self.body_parts_list)
        preset_choice_layout.addWidget(presets_refresh_button)

        presets_options_layout = QHBoxLayout()

        edit_preset_button = QPushButton('Edit')
        edit_preset_button.clicked.connect(self.edit_preset_clicked)
        remove_preset_button = QPushButton('Remove')
        remove_preset_button.clicked.connect(self.remove_preset_clicked)
        presets_options_layout.addWidget(edit_preset_button)
        presets_options_layout.addWidget(remove_preset_button)

        layout.addLayout(preset_choice_layout)
        layout.addLayout(presets_options_layout)

        layout.addStretch()

    def edit_preset_clicked(self):
        self.show_saved_preset_popup()

    def remove_preset_clicked(self):
        character_name = self.character_combo.currentText()
        selected_items = self.body_parts_list.selectedItems()
        body_part_name = selected_items[0].text()
        presets.remove_preset(
            self.presets_file_path,
            character_name,
            body_part_name
            )
        print('Removing Presets')

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
        if not saved_char_list:
            return
        for char in saved_char_list:
            self.character_combo.addItem(char)

    def show_saved_preset_popup(self):
        '''
        show the save preset popup window.
        Store existing main UI's values and pass it to the popup window
        '''
        if not self.presets_file_path:
            return mc.warning(
                'Path to presets not set/found.')

        char_name = self.character_combo.currentText()
        selected_items = self.body_parts_list.selectedItems()
        body_part_name = selected_items[0].text()
        spring_value, spring_rigidity, decay, pos = presets.get_all_data(
            path=self.presets_file_path,
            character_name=char_name,
            body_part=body_part_name
        )

        print(f'This is the saved position : {pos[0]}')
        self.preset_window = SavePresetPopup(
            self,
            self.presets_file_path,
            spring_value,
            spring_rigidity,
            decay,
            position=pos,
            char_name=char_name,
            body_part=body_part_name,
            edit_mode=True
            )
        self.preset_window.show()


def show_preset_admin():
    global window
    if window is not None:
        window.close()
    window = SpringToolPresetAdmin()
    window.show()
