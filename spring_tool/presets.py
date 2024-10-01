import json
import os
import re
from PySide2.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, QInputDialog,
    QDoubleSpinBox, QLabel, QLineEdit, QMessageBox, QRadioButton)
from PySide2 import QtCore


EMPTY_LINE_TEXT = '----------'
ADD_NEW_CHARACTER_TEXT = ' - Add new character -'


def show_error_message(message):
    error_dialog = QMessageBox()
    error_dialog.setText(message)
    error_dialog.setIcon(QMessageBox.Critical)
    error_dialog.setWindowTitle("Warning")
    error_dialog.exec_()


def show_warning_message(message):
    warning_dialog = QMessageBox()
    warning_dialog.setIcon(QMessageBox.Warning)
    warning_dialog.setWindowTitle("Warning")
    warning_dialog.setText(message)

    # Add OK and Cancel buttons
    warning_dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

    # Set the default button to Cancel
    warning_dialog.setDefaultButton(QMessageBox.Cancel)

    # Execute the dialog and get the response
    response = warning_dialog.exec_()

    # Return True if OK is clicked, False if Cancel is clicked
    if response == QMessageBox.Ok:
        return True
    else:
        return False


def create_preset_file(path, filename):
    '''
    If no preset file found but path is set, ask the user to create the file
    automatically
    '''
    message = "No preset file found. Would you like to create one?"
    if not show_warning_message(message):
        return None

    if not os.path.isdir(path):
        raise FileNotFoundError(f"The directory '{path}' does not exist.")

    # Ensure the filename ends with .json
    if not filename.endswith('.json'):
        filename += '.json'

    # Create the full file path
    file_path = os.path.join(path, filename)

    # Create and write an empty dictionary to the JSON file
    with open(file_path, 'w') as json_file:
        json.dump({}, json_file, indent=4)

    return file_path


def load_presets(path):
    if not path:
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def get_preset(path, character_name, body_part):
    presets = load_presets(path)
    if not presets:
        return None
    return presets.get(character_name, {}).get(body_part)


def get_presets_file_path(
        environment_variable_name=None,
        presets_directory_path=None,
        presets_filename=None,
        is_admin=False):

    if not presets_directory_path:
        return False

    presets_path = os.path.normpath(presets_directory_path)
    if environment_variable_name:
        environment_variable_value = os.environ.get(environment_variable_name)
        if environment_variable_value:
            presets_path = os.path.normpath(
                os.path.join(environment_variable_value, presets_path))

    if not os.path.isdir(presets_path):
        return False

    if not presets_filename:
        presets_filename = 'spring_tool_presets.json'

    presets_file_path = os.path.join(presets_path, presets_filename)

    if not os.path.isfile(presets_file_path):
        if is_admin:
            raise FileNotFoundError('No preset file found')
        presets_file_path = create_preset_file(presets_path, presets_filename)

    return presets_file_path


def get_available_characters(path):
    presets = load_presets(path)
    if not presets:
        return None
    return list(presets.keys())


def get_available_body_parts(path, character_name):
    presets = load_presets(path)
    if not presets:
        return None
    return list(presets.get(character_name, {}).keys())


def save_preset(
        path,
        character_name,
        body_part,
        spring_mode,
        spring,
        spring_rigidity,
        decay,
        position
        ):
    presets = load_presets(path)
    if character_name not in presets:
        presets[character_name] = {}
    if body_part in presets.get(character_name, {}):
        raise ValueError(
            f"Body part '{body_part}' already exists for '{character_name}'")
    presets[character_name][body_part] = {
        'spring_mode': spring_mode,
        'spring_value': spring,
        'spring_rigidity': spring_rigidity,
        'decay': decay,
        'position': position
    }
    with open(path, 'w') as f:
        json.dump(presets, f, indent=4)


def get_all_data(path, character_name, body_part):
    presets = load_presets(path)

    # Validate the presence of necessary data
    if not presets:
        return None, None, None, None

    character_data = presets.get(character_name)
    if not character_data:
        return None, None, None, None

    body_part_data = character_data.get(body_part)
    if not body_part_data or not isinstance(body_part_data, dict):
        return None, None, None, None

    # Extract relevant data
    spring_mode = body_part_data.get('spring_mode')
    spring_value = body_part_data.get('spring_value')
    spring_rigidity = body_part_data.get('spring_rigidity')
    decay = body_part_data.get('decay')

    pos_data = body_part_data.get('position')
    position = [(pos_data[0], pos_data[1], pos_data[2])] if pos_data else None

    return spring_mode, spring_value, spring_rigidity, decay, position


def remove_preset(path, character_name, body_part=None):
    """
    Remove a body part or entire character preset from the JSON file.

    Parameters:
    - path: The path to the JSON file.
    - character_name: The name of the character to modify.
    - body_part: The specific body part to remove.
    If None, the entire character will be removed.

    Returns:
    - True if the removal was successful, False otherwise.
    """
    presets = load_presets(path)

    # Check if the character exists
    if not presets or character_name not in presets:
        return False  # Return False if the character doesn't exist

    if body_part is None:
        # If body_part is None, remove the entire character entry
        del presets[character_name]
    else:
        # If body_part is provided, remove only the specific body part
        if body_part in presets[character_name]:
            del presets[character_name][body_part]
        else:
            return False  # Return False if the body part doesn't exist

        # If there are no more presets for the character,
        # remove the character entry
        if not presets[character_name]:
            del presets[character_name]

    # Save the updated presets to the JSON file
    with open(path, 'w') as f:
        json.dump(presets, f, indent=4)

    return True  # Return True to indicate successful removal


def rename_key(json_data, old_key, new_key, parent_text=None):
    # If parent_text is None, rename top-level keys
    if parent_text is None:
        if old_key in json_data:
            json_data[new_key] = json_data.pop(old_key)
    else:
        # Rename keys at a lower level based on parent_text
        if parent_text in json_data:
            if old_key in json_data[parent_text]:
                json_data[parent_text][new_key] = (
                    json_data[parent_text].pop(old_key)
                    )
    return json_data


def edit_preset(
        path,
        character_name,
        body_part,
        spring_mode=None,
        spring=None,
        spring_rigidity=None,
        decay=None,
        position=None
        ):
    presets = load_presets(path)

    preset = presets[character_name][body_part]
    if spring_mode is not None:
        preset['spring_mode'] = spring_mode
    if spring is not None:
        preset['spring_value'] = spring
    if spring_rigidity is not None:
        preset['spring_rigidity'] = spring_rigidity
    if decay is not None:
        preset['decay'] = decay
    if position is not None:
        preset['position'] = position

    with open(path, 'w') as f:
        json.dump(presets, f, indent=4)


def name_input_dialog(existing_names, default_name='Character Name'):
    '''
    Show a popup window that asks for a name and checks against existing names.
    :param existing_names: A list of names that are already taken.
    :param default_name: Default name to display in the input dialog.
    :return: The entered name if valid, otherwise None.
    '''

    # Function to handle text changed event to auto correct ' ' to '_'
    def handle_text_changed():
        # Get the current text
        text_value = input_dialog.textValue()
        # Update the text in the input dialog
        input_dialog.setTextValue(text_value)

    # Open the input dialog
    input_dialog = QInputDialog()
    input_dialog.setWindowTitle('Preset Name')
    input_dialog.setLabelText('Enter Name')
    input_dialog.setTextValue(default_name)

    # Connect textChanged signal to handle_text_changed function
    input_dialog.textValueChanged.connect(handle_text_changed)

    # Show the input dialog and get the result
    ok = input_dialog.exec_()
    text = input_dialog.textValue()

    # Check if the user clicked 'OK' and entered a value
    if ok and text:
        # Validate input: no spaces or special characters allowed
        if not re.match("^[a-zA-Z0-9_]+$", text):
            QMessageBox.warning(
                None,
                "Invalid Input",
                "Name must contain only letters, numbers, or underscores.")
            return None

        if not existing_names:
            return text

        # Check if the name is already taken
        if text.lower() in [name.lower() for name in existing_names]:
            QMessageBox.warning(
                None,
                "Name Taken",
                "This name is already taken. Please choose a different name.")
            return None

        # If all validations pass, print and return the name
        print('Entered Name:', text)
        return text
    else:
        return None


def rename_preset(
        presets_path,
        parent_text,
        item_text
        ):

    current_name = item_text
    saved_preset_list = get_available_body_parts(
        presets_path, parent_text)
    if not parent_text:
        saved_preset_list = get_available_characters(presets_path)

    new_preset_name = name_input_dialog(saved_preset_list, current_name)
    if not new_preset_name:
        return

    # Read JSON data from file
    with open(presets_path, 'r') as file:
        json_data = json.load(file)

    rename_key(json_data, item_text, new_preset_name, parent_text)

    # Save updated JSON data back to the file
    with open(presets_path, 'w') as file:
        json.dump(json_data, file, indent=4)


class SavePresetPopup(QWidget):

    refresh_signal = QtCore.Signal()

    def __init__(
            self,
            main_window,
            presets_path,
            spring_mode,
            spring_value,
            rigidity_value,
            decay_value,
            position,
            parent=None,
            char_name=None,
            body_part=None,
            edit_mode=False,
            ):

        super().__init__(parent=parent)

        self.setWindowTitle("Save Preset")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.main_window = main_window
        self.presets_file_path = presets_path
        self.presets = load_presets(presets_path)
        self.spring_mode = spring_mode
        self.spring_value = spring_value
        self.rigidity_value = rigidity_value
        self.decay_value = decay_value
        self.loc_position = position[0]
        self.edit_mode = edit_mode
        self.load_preset_popup_ui()
        if spring_mode == 'rotation' or spring_mode is None:
            self.rotation_mode_radio.setChecked(True)
        else:
            self.translation_mode_radio.setChecked(True)
        if char_name:
            self.character_name_combobox.setCurrentText(char_name)
        if body_part:
            self.body_part_line_edit.setText(body_part)
        if edit_mode:
            self.character_name_combobox.setEnabled(False)
            self.body_part_line_edit.setEnabled(False)

    def load_preset_popup_ui(self):
        layout = QVBoxLayout()

        # Spring mode
        spring_mode_layout = QHBoxLayout()
        spring_mode_label = QLabel("Spring Mode")
        self.rotation_mode_radio = QRadioButton('Rotation')
        self.translation_mode_radio = QRadioButton('Translation')
        spring_mode_layout.addWidget(spring_mode_label)
        spring_mode_layout.addWidget(self.rotation_mode_radio)
        spring_mode_layout.addWidget(self.translation_mode_radio)
        layout.addLayout(spring_mode_layout)

        # Character Name
        char_name_layout = QHBoxLayout()
        character_label = QLabel("Character Name:")
        self.character_name_combobox = QComboBox()
        char_name_layout.addWidget(character_label)
        char_name_layout.addWidget(self.character_name_combobox)
        layout.addLayout(char_name_layout)
        self.populate_characters_combobox()
        self.character_name_combobox.currentIndexChanged.connect(
            self.character_combobox_changed
        )

        # Body Part
        body_part_layout = QHBoxLayout()
        body_part_label = QLabel("Body part Name:")
        self.body_part_line_edit = QLineEdit()
        body_part_layout.addWidget(body_part_label)
        body_part_layout.addWidget(self.body_part_line_edit)
        layout.addLayout(body_part_layout)

        # Spring
        spring_layout = QHBoxLayout()
        spring_label = QLabel("Spring:")
        self.spring_spinbox = QDoubleSpinBox()
        self.spring_spinbox.setRange(0.0, 1.0)
        self.spring_spinbox.setSingleStep(0.01)
        self.spring_spinbox.setValue(self.spring_value)
        spring_layout.addWidget(spring_label)
        spring_layout.addWidget(self.spring_spinbox)
        layout.addLayout(spring_layout)

        # Rigidity
        rigidity_layout = QHBoxLayout()
        rigidity_label = QLabel("Rigidity:")
        self.rigidity_spinbox = QDoubleSpinBox()
        self.rigidity_spinbox.setRange(0.0, 10.0)
        self.rigidity_spinbox.setSingleStep(0.01)
        self.rigidity_spinbox.setValue(self.rigidity_value)
        rigidity_layout.addWidget(rigidity_label)
        rigidity_layout.addWidget(self.rigidity_spinbox)
        layout.addLayout(rigidity_layout)

        # Decay
        decay_layout = QHBoxLayout()
        decay_label = QLabel("Decay:")
        self.decay_spinbox = QDoubleSpinBox()
        self.decay_spinbox.setSingleStep(0.01)
        self.decay_spinbox.setRange(0.0, 10.0)
        self.decay_spinbox.setValue(self.decay_value)
        decay_layout.addWidget(decay_label)
        decay_layout.addWidget(self.decay_spinbox)
        layout.addLayout(decay_layout)

        # Position
        position_layout = QHBoxLayout()
        position_label = QLabel('loc Pos (x,y,z):')
        self.position_tx_spinbox = QDoubleSpinBox()
        self.position_ty_spinbox = QDoubleSpinBox()
        self.position_tz_spinbox = QDoubleSpinBox()
        self.position_tx_spinbox.setMinimum(-999999)
        self.position_ty_spinbox.setMinimum(-999999)
        self.position_tz_spinbox.setMinimum(-999999)

        self.position_tx_spinbox.setValue(self.loc_position[0])
        self.position_ty_spinbox.setValue(self.loc_position[1])
        self.position_tz_spinbox.setValue(self.loc_position[2])
        position_layout.addWidget(position_label)
        position_layout.addWidget(self.position_tx_spinbox)
        position_layout.addWidget(self.position_ty_spinbox)
        position_layout.addWidget(self.position_tz_spinbox)
        layout.addLayout(position_layout)

        # Buttons
        button_layout = QHBoxLayout()
        confirm_button = QPushButton("Confirm")
        confirm_button.clicked.connect(self.save_preset_pressed)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        button_layout.addWidget(confirm_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def populate_characters_combobox(self):
        '''
        Populate the characters available in the pref file. Or ask for a
        new name
        '''
        self.character_name_combobox.clear()
        saved_char_list = get_available_characters(self.presets_file_path)
        if saved_char_list:
            saved_char_list.sort()
            for char in saved_char_list:
                self.character_name_combobox.addItem(char)
        empty_line_text = EMPTY_LINE_TEXT
        self.character_name_combobox.addItem(empty_line_text)
        add_new_character_name_text = ADD_NEW_CHARACTER_TEXT
        self.character_name_combobox.addItem(add_new_character_name_text)

    def character_combobox_changed(self):
        saved_char_list = get_available_characters(self.presets_file_path)
        current_combobox_item = self.character_name_combobox.currentText()
        if current_combobox_item == ADD_NEW_CHARACTER_TEXT:
            new_character_name = name_input_dialog(saved_char_list)
            if not new_character_name:
                self.character_name_combobox.setCurrentText(EMPTY_LINE_TEXT)
                return
            self.character_name_combobox.addItem(new_character_name)
            self.character_name_combobox.setCurrentText(new_character_name)
        return

    def save_preset_pressed(self):

        character_name = self.character_name_combobox.currentText()
        body_part = self.body_part_line_edit.text()

        saved_names = get_available_body_parts(
            self.presets_file_path, character_name)

        if saved_names and not self.edit_mode:
            if body_part.lower() in [name.lower() for name in saved_names]:
                QMessageBox.warning(
                    None,
                    "Name Taken",
                    "This name is already taken. "
                    "Please choose a different name.")
                return

        if self.rotation_mode_radio.isChecked():
            spring_mode = 'rotation'
        else:
            spring_mode = 'translation'

        spring = self.spring_spinbox.value()
        rigidity = self.rigidity_spinbox.value()
        decay = self.decay_spinbox.value()
        position_x = self.position_tx_spinbox.value()
        position_y = self.position_ty_spinbox.value()
        position_z = self.position_tz_spinbox.value()
        position = [position_x, position_y, position_z]

        print("Character Name:", character_name)
        print("Body Part Name:", body_part)
        print("Spring Mode", spring_mode)
        print("Spring:", spring)
        print("Rigidity:", rigidity)
        print("Decay:", decay)
        print("position", position)

        if not self.edit_mode:
            save_preset(
                self.presets_file_path,
                character_name,
                body_part,
                spring_mode,
                spring,
                rigidity,
                decay,
                position)
            self.close()
            self.refresh_signal.emit()
            return

        edit_preset(
            self.presets_file_path,
            character_name,
            body_part,
            spring_mode,
            spring,
            rigidity,
            decay,
            position)
        self.close()
        self.refresh_signal.emit()
