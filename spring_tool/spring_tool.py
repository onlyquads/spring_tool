'''
# Description:
Based on Luismi Herrera's logic of LMspring:
https://luismiherrera.gumroad.com/.
Fully rewritten using Qt and python3 with better performances in bake process.
A preset system has been added, see the presets section

# How to use:
1. Select all the controllers of the chain. Also works with only 1 controller
2. Click create locator and align the created locator
to the end of the chain to set its scale
3. Hit preview and tweak spring/rigidity settings. This only previews the
first controller of the chain.
4. Hit bake to simulate and bake the whole chain

NOTE: When previewing, you need to read timeline from its begining
Tested on maya2022

# Presets:
You can add presets for different parts of a character/prop to be reused.
That preset file can be shared accross team of artists.
Using presets, you'll be able to launch the whole sim and bake process
by right clicking any preset and 'Do Magic!' menu.
See installation instructions below.

# Launch on-the-go:
Copy/Paste this whole page of code in maya python console and run.
NOTE: No presets UI will be shown if not fully installed and setup. See below

# Installation instructions :
To install the Spring Tool for Maya, follow these steps:

1. Copy the entire `spring_tool` folder into your maya20XX/scripts directory.

2. Launch Maya and run the following Python code in the Maya Script Editor
or Python console to open the tool without presets functions:
   ```python
   from spring_tool import spring_tool
   window = spring_tool.SpringToolWindow()
   window.show()

To launch spring_tool with presets functions, you'll need to add
path and filename to args.
If you work in team, make sure the presets file is in a shared directory sothat
everyone can get and add presets.

Example:

```python
from spring_tool import spring_tool
window = spring_tool.SpringToolWindow(
    prod_root_env_name = None,  # can be usefull if you work with environments
    presets_dir_path='/Users/Username/Desktop',
    presets_filename='spring_tool_presets.json'
    )
window.show()


- Note: 'prod_root_env_name' will be sent as string in
'os.environ.get(prod_root_env_name)' in 'get_presets_file_path' function.

# Launch Administration instructions :
There is an administration window that might be helpful to tweak, rename or
delete any preset created.

To launch it run this python command:

```python
from spring_tool import presets_admin
window = presets_admin.SpringToolPresetAdmin(
    prod_root_env_name=None, # can be usefull if you work with environments
    presets_dir_path="/Users/Username/Desktop",
    presets_filename="spring_tool_presets.json",
    authorized_access=True,  # Set to False to restrict access to the window
    )
window.show()
```

'''

import sys

from functools import wraps
from PySide2 import QtWidgets, QtCore
from PySide2.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QDoubleSpinBox, QSlider, QLabel, QComboBox, QListWidget, QAction, QMenu,
    QCheckBox, QRadioButton)
import maya.cmds as mc
import maya.mel as mm

try:
    from spring_tool import presets
    print('spring tool presets found')
except ImportError:
    presets = None


TOOLNAME = 'Spring_Tool'
TOOL_VERSION = '1.3'

AIM_GRP_NAME = 'SPTL_aim_loc_GRP'
PARTICLE_NAME = 'SPTL_particle'
LOCATOR_NAME = 'SPTL_spring_locator'
LAYER_PREFIX = 'SPTL_layer'
CTL_LOCATOR = 'SPTL_orig_pos_loc'
SPTL_NODE_ATTR = 'Spring_tool_node'
DEFAULT_SPRING_MODE = 'rotation'
DEFAULT_SPRING_VALUE = 0.45
DEFAULT_DECAY_VALUE = 1.2
DEFAULT_RIGIDITY_VALUE = 7.0
AIM_VECTORS = {
            1: ((1, 0, 0), (0, 0, 1)),
            2: ((0, 0, 1), (1, 0, 0)),
            3: ((1, 0, 0), (1, 0, 0)),
            -1: ((-1, 0, 0), (0, 0, 1)),
            -2: ((0, -1, 0), (0, 0, 1)),
            -3: ((0, 0, -1), (1, 0, 0)),
        }
ROTATION_MODE_OPTVAR = 'sptlRotationMode'
TRANSLATION_MODE_OPTVAR = 'sptlTranslationMode'
BAKE_ON_LAYERS_OPTVAR = 'sptlBakeOnAnimLayers'
MERGE_LAYERS_OPTVAR = 'sptlMergeAnimLayers'

window = None


def maya_main_window():
    '''Return Maya's main window'''
    for obj in QtWidgets.QApplication.topLevelWidgets():
        if obj.objectName() == 'MayaWindow':
            return obj
    raise RuntimeError('Could not find MayaWindow instance')


def disable_viewport(func):
    '''
    Decorator - turn off Maya display while func is running.
    if func fails, the error will be raised after.
    '''
    @wraps(func)
    def wrap(*args, **kwargs):
        mm.eval("paneLayout -e -manage false $gMainPane")
        # Decorator will try/except running the function.
        # But it will always turn on the viewport at the end.
        # If the function failed, it will prevent leaving maya viewport off.
        try:
            return func(*args, **kwargs)
        except Exception:
            mc.warning(Exception)
        finally:
            mm.eval("paneLayout -e -manage true $gMainPane")
    return wrap


def add_bool_attr(node, lock=True):

    '''
    Description: Creates custom string attributes and sets the value with
    given name, value.
    '''
    attribute_type = 'bool'
    # check if attribute already exists, if not create it.
    if mc.attributeQuery(SPTL_NODE_ATTR, node=node, exists=True):
        return
    mc.addAttr(
        node,
        longName=SPTL_NODE_ATTR,
        attributeType=attribute_type,
        )
    mc.setAttr(
        f'{node}.{SPTL_NODE_ATTR}',
        True,
        lock=lock
    )


def list_nodes_with_sptl_attr():
    """
    Returns a list of all nodes in the scene that have
    the sptl custom attribute and where the attribute is set to True.
    """
    objects_with_attr = mc.ls(f'*.{SPTL_NODE_ATTR}', sn=True)
    base_objects = [obj.split('.')[0] for obj in objects_with_attr]
    return base_objects


class SpringToolWindow(QMainWindow):

    def __init__(
            self,
            parent=None,
            prod_root_env_name=None,
            presets_dir_path=None,
            presets_filename=None,
            lock_write_presets=False,
            ):

        if not parent:
            parent = maya_main_window()
        super(SpringToolWindow, self).__init__(parent=parent)

        self.setWindowTitle(TOOLNAME.replace('_', ' '))
        self.setWindowFlags(QtCore.Qt.Tool)
        self.lock_write_presets = lock_write_presets

        self.ui_main()
        self.load_preferences_states()

        if presets:
            self.presets_file_path = presets.get_presets_file_path(
                prod_root_env_name,
                presets_dir_path,
                presets_filename
            )
            if self.presets_file_path:
                self.ui_presets()

        self.master_scale = 1.0
        self.axes = [0, 0, 0]
        self.locator_position = [0, 0, 0]
        self.aim_loc = None
        self.layer_names_list = []

        # Clear any existing nodes with sptl attribute from previous session
        if list_nodes_with_sptl_attr():
            self.clean_scene()

        if not self.bake_on_layer_checkbox.isChecked():
            self.merge_animation_layer_checkbox.setEnabled(False)

    def ui_main(self):
        '''
        Main part of the tool, left UI panel
        '''
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.main_split_layout = QHBoxLayout(central_widget)
        self.main_layout = QVBoxLayout()

        self.radio_buttons_layout = QHBoxLayout()
        self.rotation_mode_radio_button = QRadioButton('Rotation')
        self.rotation_mode_radio_button.setChecked(True)
        self.rotation_mode_radio_button.toggled.connect(
            self.save_preferences_states)
        self.translation_mode_radio_button = QRadioButton('Translation')
        self.translation_mode_radio_button.toggled.connect(
            self.save_preferences_states)

        self.radio_buttons_layout.addWidget(
            self.rotation_mode_radio_button)
        self.radio_buttons_layout.addWidget(
            self.translation_mode_radio_button)

        self.locators_button = QPushButton('1. Create Locator')
        self.locators_button.clicked.connect(self.handle_locators_btn_clicked)

        self.previz_button = QPushButton('2. Live preview')
        self.previz_button.clicked.connect(self.handle_previz_btn_clicked)

        weight_layout = QHBoxLayout()
        decay_layout = QHBoxLayout()
        rigidity_layout = QHBoxLayout()

        spring_qlabel = QLabel('Spring')
        self.spring_value_spinbox = QDoubleSpinBox()
        self.spring_value_spinbox.setRange(0.0, 1.0)
        self.spring_value_spinbox.setSingleStep(0.01)
        self.spring_value_spinbox.setValue(DEFAULT_SPRING_VALUE)
        self.spring_value_qslider = QSlider(QtCore.Qt.Horizontal)
        self.spring_value_qslider.setRange(0.0, 100.0)
        self.spring_value_qslider.setValue(DEFAULT_SPRING_VALUE*100)
        self.spring_value_spinbox.valueChanged.connect(
            self.spring_value_changed)
        self.spring_value_qslider.valueChanged.connect(
            self.slider_spring_value_changed)

        rigidity_qlabel = QLabel('Rigidity')
        self.rigidity_value_spinbox = QDoubleSpinBox()
        self.rigidity_value_spinbox.setRange(0.0, 10.0)
        self.rigidity_value_spinbox.setSingleStep(0.01)
        self.rigidity_value_spinbox.setValue(DEFAULT_RIGIDITY_VALUE)
        self.rigidity_value_qslider = QSlider(QtCore.Qt.Horizontal)
        self.rigidity_value_qslider.setRange(0.0, 100.0)
        self.rigidity_value_qslider.setValue(DEFAULT_RIGIDITY_VALUE*10)
        self.rigidity_value_spinbox.valueChanged.connect(
            self.rigidity_spinbox_value_changed)
        self.rigidity_value_qslider.valueChanged.connect(
            self.rigidity_slider_value_changed)

        decay_qlabel = QLabel('Decay')
        self.decay_value_spinbox = QDoubleSpinBox()
        self.decay_value_spinbox.setValue(DEFAULT_DECAY_VALUE)
        self.decay_value_spinbox.setSingleStep(0.01)
        self.decay_value_spinbox.setRange(0.0, 10.0)
        self.decay_value_slider = QSlider(QtCore.Qt.Horizontal)
        self.decay_value_slider.setRange(0.0, 100.0)
        self.decay_value_slider.setValue(12.0)
        self.decay_value_spinbox.valueChanged.connect(self.get_user_decay)
        self.decay_value_slider.valueChanged.connect(
            self.slider_decay_value_changed)

        bake_on_layer_option_layout = QHBoxLayout()
        self.bake_on_layer_checkbox = QCheckBox('Bake on layers')
        self.bake_on_layer_checkbox.stateChanged.connect(
            self.save_preferences_states)

        self.merge_animation_layer_checkbox = QCheckBox('Merge layers')
        self.merge_animation_layer_checkbox.stateChanged.connect(
            self.save_preferences_states)

        self.bake_button = QPushButton('3. Bake!')
        self.bake_button.clicked.connect(self.launch_bake)

        self.remove_setup_button = QPushButton('Remove Setup')
        self.remove_setup_button.clicked.connect(self.clear_all)

        weight_layout.addWidget(spring_qlabel)
        weight_layout.addWidget(self.spring_value_spinbox)
        weight_layout.addWidget(self.spring_value_qslider)

        rigidity_layout.addWidget(rigidity_qlabel)
        rigidity_layout.addWidget(self.rigidity_value_spinbox)
        rigidity_layout.addWidget(self.rigidity_value_qslider)

        decay_layout.addWidget(decay_qlabel)
        decay_layout.addWidget(self.decay_value_spinbox)
        decay_layout.addWidget(self.decay_value_slider)

        bake_on_layer_option_layout.addWidget(self.bake_on_layer_checkbox)
        bake_on_layer_option_layout.addWidget(
            self.merge_animation_layer_checkbox)

        self.main_layout.addLayout(self.radio_buttons_layout)
        self.main_layout.addWidget(self.locators_button)
        self.main_layout.addWidget(self.previz_button)
        self.main_layout.addLayout(weight_layout)
        self.main_layout.addLayout(rigidity_layout)
        self.main_layout.addLayout(decay_layout)
        self.main_layout.addLayout(bake_on_layer_option_layout)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.bake_button)
        self.main_layout.addWidget(self.remove_setup_button)
        self.main_split_layout.addLayout(self.main_layout, 2)

    def ui_presets(self):
        '''
        UI for the right panel of the tool
        '''
        self.presets_main_layout = QVBoxLayout()
        self.character_combo = QComboBox()

        self.character_combo.currentIndexChanged.connect(
            self.on_character_changed)
        presets_refresh_button = QPushButton('Refresh')
        presets_refresh_button.clicked.connect(
            self.refresh_characters_combobox)
        save_preset_button = QPushButton('Save Preset')
        save_preset_button.clicked.connect(self.show_save_preset_popup)
        if self.lock_write_presets:
            save_preset_button.setDisabled(True)

        self.body_parts_list_menu = QMenu()
        do_magic_action = QAction("Do Magic!", self)
        self.body_parts_list = QListWidget()
        # Handle right click on QMenuList item
        self.body_parts_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.body_parts_list.customContextMenuRequested.connect(self.show_menu)
        self.body_parts_list_menu.addAction(do_magic_action)
        do_magic_action.triggered.connect(self.launch_all)
        self.body_parts_list.setFixedHeight(159)

        # Populate the combo-box and list
        self.refresh_characters_combobox()

        self.presets_main_layout.addWidget(self.character_combo)
        self.presets_main_layout.addWidget(self.body_parts_list)
        self.presets_main_layout.addWidget(presets_refresh_button)
        self.presets_main_layout.addWidget(save_preset_button)

        self.main_split_layout.addLayout(self.presets_main_layout, 1)
        self.presets_main_layout.addStretch()

    def save_preferences_states(self):
        # Get the current state of each checkbox and radio button
        rotation_mode_state = self.rotation_mode_radio_button.isChecked()
        translation_mode_state = self.translation_mode_radio_button.isChecked()
        bake_on_layer_state = self.bake_on_layer_checkbox.isChecked()
        merge_layers_state = self.merge_animation_layer_checkbox.isChecked()

        # Save the states as integers
        mc.optionVar(iv=(ROTATION_MODE_OPTVAR, int(rotation_mode_state)))
        mc.optionVar(iv=(TRANSLATION_MODE_OPTVAR, int(translation_mode_state)))
        mc.optionVar(iv=(BAKE_ON_LAYERS_OPTVAR, int(bake_on_layer_state)))
        mc.optionVar(iv=(MERGE_LAYERS_OPTVAR, int(merge_layers_state)))

        self.merge_animation_layer_checkbox.setEnabled(bake_on_layer_state)

    def load_preferences_states(self):
        '''
        Load and set the checkbox states from optionVars.
        '''
        self.rotation_mode_radio_button.blockSignals(True)
        self.translation_mode_radio_button.blockSignals(True)
        self.bake_on_layer_checkbox.blockSignals(True)
        self.merge_animation_layer_checkbox.blockSignals(True)

        if mc.optionVar(exists=ROTATION_MODE_OPTVAR):
            rotation_mode_state = mc.optionVar(q=ROTATION_MODE_OPTVAR)
            self.rotation_mode_radio_button.setChecked(
                bool(rotation_mode_state)
                )
        else:
            self.rotation_mode_radio_button.setChecked(False)

        if mc.optionVar(exists=TRANSLATION_MODE_OPTVAR):
            translation_mode_state = mc.optionVar(q=TRANSLATION_MODE_OPTVAR)
            self.translation_mode_radio_button.setChecked(
                bool(translation_mode_state)
                )
        else:
            self.rotation_mode_radio_button.setChecked(False)

        if mc.optionVar(exists=BAKE_ON_LAYERS_OPTVAR):
            bake_on_layer_state = mc.optionVar(q=BAKE_ON_LAYERS_OPTVAR)
            self.bake_on_layer_checkbox.setChecked(bool(bake_on_layer_state))
        else:
            self.bake_on_layer_checkbox.setChecked(False)

        if mc.optionVar(exists=MERGE_LAYERS_OPTVAR):
            merge_layers_state = mc.optionVar(q=MERGE_LAYERS_OPTVAR)
            self.merge_animation_layer_checkbox.setChecked(
                bool(merge_layers_state))
        else:
            self.merge_animation_layer_checkbox.setChecked(False)

        # Unblock signals after setting the states
        self.rotation_mode_radio_button.blockSignals(False)
        self.translation_mode_radio_button.blockSignals(False)
        self.bake_on_layer_checkbox.blockSignals(False)
        self.merge_animation_layer_checkbox.blockSignals(False)

    def showEvent(self, event):
        # Set window width and height to minimum and lock resizability
        super().showEvent(event)
        self.setFixedWidth(self.minimumWidth())
        self.setFixedHeight(self.minimumHeight())

    def show_menu(self, position):
        position = self.body_parts_list.mapToGlobal(position)
        self.body_parts_list_menu.exec_(position)

    def spring_value_changed(self):
        self.spring_value_qslider.blockSignals(True)
        weight = self.spring_value_spinbox.value()
        self.spring_value_qslider.setValue(weight*100)
        self.update_overlap_weight()
        self.spring_value_qslider.blockSignals(False)

    def slider_spring_value_changed(self):
        self.spring_value_spinbox.blockSignals(True)
        value = self.spring_value_qslider.value()
        self.spring_value_spinbox.setValue(value/100)
        self.update_overlap_weight()
        self.spring_value_spinbox.blockSignals(False)

    def slider_decay_value_changed(self):
        self.decay_value_spinbox.blockSignals(True)
        value = self.decay_value_slider.value()
        self.decay_value_spinbox.setValue(value/10)
        self.decay_value_spinbox.blockSignals(False)

    def rigidity_spinbox_value_changed(self):
        self.rigidity_value_qslider.blockSignals(True)
        value = self.rigidity_value_spinbox.value()
        self.rigidity_value_qslider.setValue(value*10)
        self.update_rigidity_value()
        self.rigidity_value_qslider.blockSignals(False)

    def rigidity_slider_value_changed(self):
        self.rigidity_value_spinbox.blockSignals(True)
        value = self.rigidity_value_qslider.value()
        self.rigidity_value_spinbox.setValue(value/10)
        self.update_rigidity_value()
        self.rigidity_value_spinbox.blockSignals(False)

    def handle_locators_btn_clicked(self):
        self.rig_ctl_list = mc.ls(selection=True, tr=True)
        if not self.rig_ctl_list:
            mc.warning('Nothing selected, please select at least 1 object')
            return
        if mc.objExists(AIM_GRP_NAME):
            return mc.warning('Locator already in scene. Delete setup first')
        self.create_locators(self.rig_ctl_list)

    def handle_previz_btn_clicked(self):
        if not mc.objExists(AIM_GRP_NAME):
            mc.warning('Locator not found. Create and adjust locator first')
            return
        if self.rotation_mode_radio_button.isChecked():
            self.setup_live_preview(self.rig_ctl_list, mode='rotation')
        else:
            self.setup_live_preview(self.rig_ctl_list, mode='translation')

    def get_framerange(self):
        frame_in = mc.playbackOptions(minTime=True, query=True)
        frame_out = mc.playbackOptions(maxTime=True, query=True)
        return frame_in, frame_out

    def get_locked_attr(self, object, transform):
        '''
        transform = 'r' for rotate or 't' for translate as string
        '''
        locked_attr_list = []
        locked_attr_list = [
            axis for axis in ['x', 'y', 'z'] if mc.getAttr(
                f'{object}.{transform}{axis}', l=True)]
        return locked_attr_list

    def remove_setup_nodes(self):
        '''
        Removes all the setup nodes from the scene
        '''
        mc.undoInfo(ock=True)
        obj_name_list = (
            [
                TOOLNAME,
                AIM_GRP_NAME,
                PARTICLE_NAME,
                LOCATOR_NAME,
                CTL_LOCATOR
            ]
            )
        for obj in obj_name_list:
            if mc.objExists(f'{obj}*'):
                mc.delete(obj)
        mc.undoInfo(cck=True)

    def clean_scene(self):
        '''
        Remove all the spring tool nodes from the scene
        '''
        mc.undoInfo(ock=True)
        sptl_nodes = list_nodes_with_sptl_attr()
        if not sptl_nodes:
            return
        for node in sptl_nodes:
            if not mc.objExists(node):
                continue
            mc.delete(node)
        mc.undoInfo(cck=True)

    def clear_all(self):
        '''
        Resets all the variables to default
        '''
        self.rig_ctl_list = []
        self.layer_names_list = []
        self.aim_loc = None
        self.axes = None
        self.spring_value_spinbox.setValue(DEFAULT_SPRING_VALUE)
        self.decay_value_spinbox.setValue(DEFAULT_DECAY_VALUE)
        self.clean_scene()

    def refresh_characters_combobox(self):
        '''
        Refresh the characters available in pref files. Clear existing and
        populate it.
        '''
        self.character_combo.clear()
        saved_char_list = presets.get_available_characters(
            self.presets_file_path)
        if saved_char_list:
            saved_char_list.sort()
        if not saved_char_list:
            return
        for char in saved_char_list:
            self.character_combo.addItem(char)
        self.body_parts_list.itemDoubleClicked.connect(
            self.set_values_from_preset)

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

    def launch_all(self):
        '''
        Launch the whole process automatically from selected preset using right
        click. Need to have the controllers selected in viewport.
        '''
        self.rig_ctl_list = mc.ls(selection=True)
        if not self.rig_ctl_list:
            return
        self.create_locators(self.rig_ctl_list)
        self.set_values_from_preset()
        if self.rotation_mode_radio_button.isChecked():
            mode = 'rotation'
        else:
            mode = 'translation'
        self.setup_live_preview(self.rig_ctl_list, mode=mode)
        self.launch_bake()

    def get_aim_loc_position(self):
        '''
        Return the current position X, Y, Z of the aim locator
        to save in presets. If no loc found, return [(0, 0, 0)]
        '''
        if not self.aim_loc:
            return [(0, 0, 0)]
        if mc.objExists(self.aim_loc[0]):
            pos = mc.getAttr(f'{self.aim_loc[0]}.translate')
            position_fixed = [
                tuple(round(coord, 2) for coord in point) for point in pos]
            print(f'FOUND POSITION {position_fixed}')
            return position_fixed

    def show_save_preset_popup(self):
        '''
        show the save preset popup window.
        Store existing main UI's values and pass it to the popup window
        '''
        if not self.presets_file_path:
            return mc.warning(
                'Path to presets not set/found.')
        if self.rotation_mode_radio_button.isChecked():
            spring_mode = 'rotation'
        else:
            spring_mode = 'translation'
        spring_value = self.spring_value_spinbox.value()
        rigidity_value = self.rigidity_value_spinbox.value()
        decay_value = self.decay_value_spinbox.value()
        position = self.get_aim_loc_position()

        self.preset_window = presets.SavePresetPopup(
            self,
            self.presets_file_path,
            spring_mode,
            spring_value,
            rigidity_value,
            decay_value,
            position
            )

        self.preset_window.refresh_signal.connect(
                self.refresh_characters_combobox)
        self.preset_window.show()

    def set_values_from_preset(self):
        '''
        Sets the values from the selected preset in list
        '''
        character_name = self.character_combo.currentText()
        selected_items = self.body_parts_list.selectedItems()
        preset_text = selected_items[0].text()
        preset_values = presets.get_preset(
            self.presets_file_path,
            character_name,
            preset_text
            )
        spring_mode = preset_values.get(
            'spring_mode', DEFAULT_SPRING_MODE)
        spring_value = preset_values.get(
            'spring_value', DEFAULT_SPRING_VALUE)
        spring_rigidity = preset_values.get(
            'spring_rigidity', DEFAULT_RIGIDITY_VALUE)
        decay = preset_values.get('decay', DEFAULT_DECAY_VALUE)
        position = preset_values.get('position', None)

        if spring_mode == 'rotation' or spring_mode is None:
            self.rotation_mode_radio_button.setChecked(True)
        else:
            self.translation_mode_radio_button.setChecked(True)
        self.spring_value_spinbox.setValue(spring_value)
        self.rigidity_value_spinbox.setValue(spring_rigidity)
        self.decay_value_spinbox.setValue(decay)
        self.move_to_pref_position(position)

    def create_locators(self, selected_rig_ctl_list):
        mc.undoInfo(ock=True)
        self.rig_ctl_list = []
        self.rig_ctl_list = sorted(selected_rig_ctl_list)
        aim_loc_grp = mc.group(name=AIM_GRP_NAME, empty=True)
        add_bool_attr(aim_loc_grp)
        mc.parent(aim_loc_grp, self.rig_ctl_list[0], relative=True)
        sel_matrix = mc.xform(
            self.rig_ctl_list[0], q=True, ws=True, matrix=True)
        mc.xform(aim_loc_grp, ws=True, matrix=sel_matrix)
        parent_constraint = mc.parentConstraint(
            self.rig_ctl_list[0], aim_loc_grp, mo=True)
        add_bool_attr(parent_constraint[0])

        self.aim_loc = mc.spaceLocator(name='SPTL_Aim_loc')
        add_bool_attr(self.aim_loc[0])
        mc.parent(self.aim_loc, aim_loc_grp, relative=True)
        mc.undoInfo(cck=True)

    def align_locator(self):
        mc.setAttr(f'{self.aim_loc[0]}.t', *self.axes)

    def get_direction(self):
        self.axes = []
        self.axes.append(mc.getAttr(f'{(self.aim_loc)[0]}.tx'))
        self.axes.append(mc.getAttr(f'{(self.aim_loc)[0]}.ty'))
        self.axes.append(mc.getAttr(f'{(self.aim_loc)[0]}.tz'))
        direction = self.axes.index(max(self.axes, key=abs)) + 1
        if (self.axes[direction-1] < 0):
            direction = direction * -1
        return direction

    def get_user_decay(self):
        decay = self.decay_value_spinbox.value()
        self.decay_value_slider.blockSignals(True)
        self.decay_value_slider.setValue(decay*10)
        self.decay_value_slider.blockSignals(False)
        return decay

    def get_user_spring_weight(self):
        weight = max(0, min(1, 1.0 - self.spring_value_spinbox.value()))
        return weight

    def update_overlap_weight(self):
        if not mc.objExists(f'{PARTICLE_NAME}*'):
            return
        weight = self.get_user_spring_weight()
        particle_system_list = mc.ls(f'{PARTICLE_NAME}*', shapes=False)
        for i in particle_system_list:
            mc.setAttr(f'{i}.goalWeight[0]', weight)

    def update_rigidity_value(self):
        if not mc.objExists(f'{PARTICLE_NAME}*',):
            return
        value = self.rigidity_value_spinbox.value()
        particle_system_list = mc.ls(f'{PARTICLE_NAME}*', shapes=False)
        for i in particle_system_list:
            mc.setAttr(f'{i}.goalSmoothness', 10-value)

    def get_overlap_weight_math(self, spring_weight, decay):
        weight = float('{:.2f}'.format(spring_weight/decay))
        weight = max(0, min(1, weight))
        return weight

    def get_vp_evaluation_mode(self):
        mel_command = 'evaluationManager -query -mode;'
        evaluation_mode = mm.eval(mel_command)
        return evaluation_mode

    def switch_back_vp_eval(self, vp_eval):
        if vp_eval[0] == "parallel":
            mm.eval('evaluationManager -mode "parallel";')
            return
        if vp_eval[0] == "serial":
            mm.eval('evaluationManager -mode "serial";')
            return
        mm.eval('evaluationManager -mode "off";')

    def get_node_shortname(self, node):
        return node.split(':')[-1]

    @disable_viewport
    def setup_live_preview(
        self,
        rig_ctl_list,
        mode=DEFAULT_SPRING_MODE,
        spring_weight=None,
            ):

        mc.undoInfo(ock=True)

        if mc.objExists(TOOLNAME):
            return mc.warning('Live preview already set')

        # Create tool group
        tool_group = mc.group(n=TOOLNAME, em=True)
        add_bool_attr(tool_group)

        # Get frame range and set initial time
        frame_in, frame_out = self.get_framerange()
        mc.currentTime(frame_in, edit=True)

        # Create locator and match its position to the first rig controller
        ctl_locator = mc.spaceLocator(n=CTL_LOCATOR)
        add_bool_attr(ctl_locator[0])
        sel_matrix = mc.xform(rig_ctl_list[0], q=True, ws=True, matrix=True)
        mc.xform(ctl_locator, ws=True, matrix=sel_matrix)

        # Create particle system
        particle_system = mc.particle(p=[(0, 0, 0)], n=PARTICLE_NAME)
        add_bool_attr(particle_system[0])

        # Set up constraints and bake rotation/translation
        if mode == 'translation':
            # Setup for translation mode
            parent_constraint = mc.parentConstraint(
                self.rig_ctl_list[0],
                ctl_locator
                )
            add_bool_attr(parent_constraint[0])
            self.bake_rot_trans_with_mel(ctl_locator)
            mc.delete(parent_constraint)

            orig_sel_constraint = mc.parentConstraint(
                ctl_locator,
                particle_system[0],
                mo=False
                )
            add_bool_attr(orig_sel_constraint[0])
            mc.delete(orig_sel_constraint)

            # Handle locked translation attributes
            locked_rot_attr_list = self.get_locked_attr(rig_ctl_list[0], 't')

        else:  # Rotation mode
            # Align locator to the aim control and bake its rotation
            orig_sel_constraint = mc.parentConstraint(
                self.aim_loc,
                ctl_locator,
                mo=False
                )
            add_bool_attr(orig_sel_constraint[0])
            self.bake_rot_trans_with_mel(ctl_locator)
            mc.delete(orig_sel_constraint)

            # Apply parent constraint from the locator to the particle
            parent_constraint = mc.parentConstraint(
                ctl_locator,
                PARTICLE_NAME,
                mo=False
                )
            add_bool_attr(parent_constraint[0])
            mc.delete(parent_constraint)

            # Handle locked rotation attributes
            locked_rot_attr_list = self.get_locked_attr(rig_ctl_list[0], 'r')

        # Setup spring weight
        if not spring_weight:
            spring_weight = self.get_user_spring_weight()
        goal = mc.goal(PARTICLE_NAME, g=ctl_locator, w=spring_weight)
        add_bool_attr(goal[0])
        self.update_rigidity_value()

        # Create spring locator and connect it to the particle
        spring_loc_name = LOCATOR_NAME
        spring_loc = mc.spaceLocator(n=spring_loc_name)
        add_bool_attr(spring_loc[0])
        scale = self.master_scale
        expression = (
            f'{spring_loc_name}.tx = {PARTICLE_NAME}Shape.wctx / {scale};'
            f'{spring_loc_name}.ty = {PARTICLE_NAME}Shape.wcty / {scale};'
            f'{spring_loc_name}.tz = {PARTICLE_NAME}Shape.wctz / {scale};'
        )
        mc.expression(object=spring_loc_name, string=expression)

        # Point constraint the spring locator to the rig control
        if mode == 'translation':
            point_constraint = mc.pointConstraint(
                spring_loc,
                rig_ctl_list[0],
                mo=True,
                skip=locked_rot_attr_list
                )
        else:
            point_constraint = mc.pointConstraint(
                spring_loc,
                self.aim_loc[0],
                mo=True
                )

        add_bool_attr(point_constraint[0])

        # Parent locator, particle, and spring locator under the tool group
        mc.parent(ctl_locator, PARTICLE_NAME, spring_loc, tool_group)

        if mode == 'rotation':
            # Additional setup for rotation mode: Build aim constraint
            direction = self.get_direction()
            aim_vector, up_vector = AIM_VECTORS[direction]
            aim_constraint = mc.aimConstraint(
                spring_loc[0],
                rig_ctl_list[0],
                aimVector=aim_vector,
                upVector=up_vector,
                worldUpVector=up_vector,
                worldUpObject=ctl_locator[0],
                worldUpType='objectrotation',
                mo=True,
                skip=locked_rot_attr_list,
            )
            add_bool_attr(aim_constraint[0])

        # Set particle start frame
        mc.setAttr(f'{PARTICLE_NAME}.startFrame', frame_in)
        # Enable undo info
        mc.undoInfo(cck=True)

    def move_to_pref_position(self, position):
        '''
        Moves the created setup locator to the position saved in preset file
        '''
        loc = self.aim_loc
        if not mc.objExists(loc[0]):
            return
        saved_position = position
        mc.setAttr(f'{loc[0]}.t', *saved_position)

    @disable_viewport
    def bake_rot_trans_with_mel(self, current_ctl):
        frame_in, frame_out = self.get_framerange()
        mel_command = f'bakeResults -simulation true ' \
            f'-t "{frame_in}:{frame_out}" -sampleBy 1 ' \
            f'-disableImplicitControl true -preserveOutsideKeys true ' \
            f'"{current_ctl[0]}";'
        mm.eval(mel_command, lowestPriority=True)

    @disable_viewport
    def bake_rotation_with_mel(self, current_ctl, layers=False):
        frame_in, frame_out = self.get_framerange()
        mel_command = 'bakeResults -simulation true '
        if layers:
            layer_name = (
                f'{LAYER_PREFIX}_{self.get_node_shortname(current_ctl)}')
            mel_command += f'-destinationLayer "{layer_name}"'
        mel_command += f'-t "{frame_in}:{frame_out}" -sampleBy 1 ' \
            f'-disableImplicitControl true -preserveOutsideKeys true ' \
            f'"{current_ctl}.rotate";'
        mm.eval(mel_command, lowestPriority=True)

    @disable_viewport
    def bake_translation_wilth_mel(self, current_ctl, layers=False):
        frame_in, frame_out = self.get_framerange()
        mel_command = 'bakeResults -simulation true '
        if layers:
            layer_name = (
                f'{LAYER_PREFIX}_{self.get_node_shortname(current_ctl)}')
            mel_command += f'-destinationLayer "{layer_name}"'
        mel_command += f'-t "{frame_in}:{frame_out}" -sampleBy 1 ' \
            f'-disableImplicitControl true -preserveOutsideKeys true ' \
            f'"{current_ctl}.translate";'
        mm.eval(mel_command, lowestPriority=True)

    def create_anim_layer(self, current_ctl):
        mc.select(current_ctl)
        layer_name = f'{LAYER_PREFIX}_{self.get_node_shortname(current_ctl)}'
        mc.animLayer(
            layer_name,
            aso=True,
            etr=True)
        self.layer_names_list.append(layer_name)
        mc.select(clear=True)

    def bake_ctl(self, current_ctl):
        layers = False
        if self.bake_on_layer_checkbox.isChecked():
            self.create_anim_layer(current_ctl)
            layers = True
        if self.rotation_mode_radio_button.isChecked():
            self.bake_rotation_with_mel(current_ctl, layers=layers)
        else:
            self.bake_translation_wilth_mel(current_ctl, layers=layers)
        self.clean_scene()
        return

    def merge_animation_layer(
            self, layer_name_list, merged_layer_name, delete_baked=True):
        if not layer_name_list:
            return
        try:
            mc.optionVar(intValue=('animLayerMergeDeleteLayers', delete_baked))
            if not mc.optionVar(exists='animLayerMergeByTime'):
                mc.optionVar(floatValue=('animLayerMergeByTime', 1.0))

            # Add the target layer at the start of the list
            layer_name_list.insert(0, merged_layer_name)

            # Merge the layers
            mm.eval('animLayerMerge {"%s"}' % '","'.join(layer_name_list))

            # Rename the merged layer
            mc.rename('Merged_Layer', merged_layer_name)

        except Exception:
            mc.warning('Failed to merge animation layers')
            return

    @disable_viewport
    def launch_bake(self):

        rotation_mode = self.rotation_mode_radio_button.isChecked()

        mc.undoInfo(ock=True)

        if not mc.objExists(TOOLNAME):
            mc.warning('No Live Preview setup found, use Live Preview first')
            return
        print('--- BAKING PLEASE WAIT ---')
        spring_weight = self.spring_value_spinbox.value()
        decay = self.get_user_decay()

        vp_eval = self.get_vp_evaluation_mode()
        self.switch_back_vp_eval('off')
        selected_rig_ctl = self.rig_ctl_list
        for i in range(len(selected_rig_ctl)):
            # BAKING FIRST CTL OF THE CHAIN
            if i == 0:
                self.bake_ctl(current_ctl=selected_rig_ctl[i])
                continue

            # BAKING CHILDREN OF THE CHAIN
            self.create_locators([selected_rig_ctl[i]])
            self.align_locator()
            spring_weight = self.get_overlap_weight_math(spring_weight, decay)

            mode = 'rotation' if rotation_mode else 'translation'
            self.setup_live_preview(
                [selected_rig_ctl[i]],
                mode=mode,
                spring_weight=(1 - spring_weight),
            )

            self.bake_ctl(current_ctl=selected_rig_ctl[i])

        if self.merge_animation_layer_checkbox.isChecked():
            controller_name = self.get_node_shortname(selected_rig_ctl[0])
            merged_layer_name = (f'{LAYER_PREFIX}_{controller_name}_merged')
            self.merge_animation_layer(
                self.layer_names_list, merged_layer_name)

        # Clear the anim layer list
        self.layer_names_list = []
        mc.warning('Spring COMPLETED !')
        self.switch_back_vp_eval(vp_eval)
        mc.undoInfo(cck=True)


if __name__ == '__main__':

    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()

    window = SpringToolWindow()
    window.show()
    app.exec_()


def show():
    global window
    if window is not None:
        window.close()
    window = SpringToolWindow()
    window.show()
