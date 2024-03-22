'''
# Description:
Based on Luismi Herrera's logic of LMspring:
https://luismiherrera.gumroad.com/.
Fully rewritten using Qt and python3 with better perferomances in bake process.
A preset system has been added, see the presets section

# How to use:
Works only for rotations.
1. Select all the controllers of the chain. Also works with only 1 controller
2. Click create locator and align the created locator
to the end of the chain to set its scale
3. Hit preview and tweak spring/rigidity settings. This only previews the
first controller of the chain.
4. Hit bake to simulate and bake the whole chain

# NOTE:
When previewing, you need to read timeline from its begining
Tested on maya2022

# Presets:
You can add presets for different parts of a character/prop to be reused.
That preset file can be shared accross team of artists. See installation
instructions below.

# Launch on-the-go:
Copy/Paste this whole page of code in maya python console and run
Note: No presets UI will be shown if not fully installed and setup. See below

# Installation instructions :
To install the Spring Tool for Maya, follow these steps:

1. Copy the entire `spring_tool` folder into your maya20XX/scripts directory.
2. Open presets.py and setup the different paths.
Example:
    PROD_NIMBLE_ROOT = 'PROD_ROOT_ENV_STR'
    JSON_PRESET_PATH = 'documents/synced_folder/spring_presets'
    JSON_FILENAME = 'spring_tool_presets.json'
    MAC_JSON_PRESET_PATH = '/Users/Username/Desktop/'
3. Launch Maya and run the following Python code in the Maya Script Editor
or Python console to open the tool:
   ```python
   from spring_tool import spring_tool
   window = spring_tool.SpringToolWindow()
   window.show()
'''


import sys
from functools import wraps
from PySide2 import QtWidgets, QtCore
from PySide2.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QDoubleSpinBox, QSlider, QLabel, QRadioButton, QComboBox,
    QLineEdit, QListWidget)
import maya.cmds as mc
import maya.mel as mm

try:
    from spring_tool import presets
except ImportError:
    presets = None


TOOLNAME = 'Spring_Tool'
TOOL_VERSION = '1.2'

AIM_GRP_NAME = 'SPTL_aim_loc_GRP'
PARTICLE_NAME = 'SPTL_particle'
LOCATOR_NAME = 'SPTL_spring_locator'
LAYER_PREFIX = 'SPTL_layer'
CTL_LOCATOR = "SPTL_orig_pos_loc"
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


class SpringToolWindow(QMainWindow):

    def __init__(self, parent=None):

        if not parent:
            parent = maya_main_window()
        super(SpringToolWindow, self).__init__(parent=parent)
        self.setWindowTitle(TOOLNAME)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setFixedWidth(300)

        self.ui_main()
        if presets:
            self.ui_presets()

        self.master_scale = 1.0
        self.axes = [0, 0, 0]
        self.locator_position = [0, 0, 0]
        self.aim_loc = None

    def ui_main(self):
        '''
        Main part of the tool, left UI panel
        '''
        central_widget = QWidget(self)
        self.main_split_layout = QHBoxLayout(central_widget)
        self.main_layout = QVBoxLayout()

        self.locators_button = QPushButton('1. Create Locator')
        self.locators_button.clicked.connect(self.handle_locators_btn_clicked)

        self.previz_button = QPushButton('2. Live preview')
        self.previz_button.clicked.connect(self.handle_previz_btn_clicked)

        weight_layout = QHBoxLayout(central_widget)
        decay_layout = QHBoxLayout(central_widget)
        rigidity_layout = QHBoxLayout(central_widget)

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
        bake_on_layer_qlabel = QLabel('Bake on layer:')
        self.layers_on_qradbutton = QRadioButton('ON')

        self.layers_off_qradbutton = QRadioButton('OFF')
        self.layers_off_qradbutton.setChecked(True)

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

        bake_on_layer_option_layout.addWidget(bake_on_layer_qlabel)
        bake_on_layer_option_layout.addWidget(self.layers_on_qradbutton)
        bake_on_layer_option_layout.addWidget(self.layers_off_qradbutton)

        self.main_layout.addWidget(self.locators_button)
        self.main_layout.addWidget(self.previz_button)
        self.main_layout.addLayout(weight_layout)
        self.main_layout.addLayout(rigidity_layout)
        self.main_layout.addLayout(decay_layout)
        self.main_layout.addLayout(bake_on_layer_option_layout)
        self.main_layout.addWidget(self.bake_button)
        self.main_layout.addWidget(self.remove_setup_button)
        self.main_layout.addStretch()
        self.main_split_layout.addLayout(self.main_layout, 2)
        self.setCentralWidget(central_widget)

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

        self.body_parts_list = QListWidget()
        self.body_parts_list.setFixedHeight(133)

        # Populate the combo-box and list
        self.refresh_characters_combobox()

        self.presets_main_layout.addWidget(self.character_combo)
        self.presets_main_layout.addWidget(self.body_parts_list)
        self.presets_main_layout.addWidget(presets_refresh_button)
        self.presets_main_layout.addWidget(save_preset_button)

        self.main_split_layout.addLayout(self.presets_main_layout, 1)
        self.presets_main_layout.addStretch()

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
            return
        if mc.objExists(AIM_GRP_NAME):
            return mc.warning('Locator already in scene. Delete setup first')
        self.create_locators(self.rig_ctl_list)

    def handle_previz_btn_clicked(self):
        if not mc.objExists(AIM_GRP_NAME):
            mc.warning('Locator not found. Create and adjust locator first')
            return
        self.setup_live_preview(self.rig_ctl_list)

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

    def remove_setup(self):
        obj_name_list = [TOOLNAME, AIM_GRP_NAME]
        [mc.delete(obj) for obj in obj_name_list if mc.objExists(f'{obj}*')]

    def clear_all(self):
        self.remove_setup()
        self.rig_ctl_list = []
        self.aim_loc = None
        self.axes = None
        self.spring_value_spinbox.setValue(DEFAULT_SPRING_VALUE)
        self.decay_value_spinbox.setValue(DEFAULT_DECAY_VALUE)

    def refresh_characters_combobox(self):
        '''
        Refresh the characters available in pref files. Clear existing and
        populate it.
        '''
        self.character_combo.clear()
        saved_char_list = presets.get_available_characters()
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
        saved_presets = presets.get_available_body_parts(current_character)
        if not saved_presets:
            return
        if saved_presets is not None:
            self.body_parts_list.addItems(saved_presets)

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
        if not presets.get_pref_file_path():
            return mc.warning(
                'Path to presets not set/found. Check path setup in preset.py')
        spring_value = self.spring_value_spinbox.value()
        rigidity_value = self.rigidity_value_spinbox.value()
        decay_value = self.decay_value_spinbox.value()
        position = self.get_aim_loc_position()

        self.preset_window = SavePresetPopup(
            spring_value,
            rigidity_value,
            decay_value,
            position,
            )
        self.preset_window.show()

    def set_values_from_preset(self, preset):
        '''
        Sets the values from the selected preset in list
        '''
        character_name = self.character_combo.currentText()
        preset_values = presets.get_preset(character_name, preset.text())
        spring_value = preset_values['spring_value']
        spring_rigidity = preset_values['spring_rigidity']
        decay = preset_values['decay']
        position = preset_values['position']

        self.spring_value_spinbox.setValue(spring_value)
        self.rigidity_value_spinbox.setValue(spring_rigidity)
        self.decay_value_spinbox.setValue(decay)
        self.move_to_pref_position(position)

    def create_locators(self, selected_rig_ctl_list):
        self.rig_ctl_list = []
        self.rig_ctl_list = sorted(selected_rig_ctl_list)
        aim_loc_grp = mc.group(name=AIM_GRP_NAME, empty=True)
        sel_matrix = mc.xform(
            self.rig_ctl_list[0], q=True, ws=True, matrix=True)
        mc.xform(aim_loc_grp, ws=True, matrix=sel_matrix)
        mc.parentConstraint(self.rig_ctl_list[0], aim_loc_grp, mo=True)
        self.aim_loc = mc.spaceLocator(name='SPTL_Aim_loc')
        mc.parent(self.aim_loc, aim_loc_grp, relative=True)

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
        if not mc.objExists(PARTICLE_NAME):
            return
        weight = self.get_user_spring_weight()
        mc.setAttr(f'{PARTICLE_NAME}.goalWeight[0]', weight)

    def update_rigidity_value(self):
        if not mc.objExists(PARTICLE_NAME):
            return
        value = self.rigidity_value_spinbox.value()
        mc.setAttr(f'{PARTICLE_NAME}.goalSmoothness', 10-value)

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
    def setup_live_preview(self, rig_ctl_list, spring_weight=None):

        if mc.objExists(TOOLNAME):
            return mc.warning('Live preview already set')
        # ROTATION MODE - AFFECT ONLY ROTATION ATTRIBUTES
        tool_grp = mc.group(n=TOOLNAME, em=True)
        frame_in, frame_out = self.get_framerange()
        mc.currentTime(frame_in, edit=True)
        ctl_locator = mc.spaceLocator(n=CTL_LOCATOR)
        sel_matrix = mc.xform(rig_ctl_list[0], q=True, ws=True, matrix=True)
        mc.xform(ctl_locator, ws=True, matrix=sel_matrix)

        mc.particle(p=[(0, 0, 0)], n=PARTICLE_NAME)

        # Align locator to first selected controller, bake, delete constraint
        orig_sel_constraint = mc.parentConstraint(
            self.aim_loc, ctl_locator, mo=False)
        self.bake_rot_tans_with_mel(ctl_locator)
        mc.delete(orig_sel_constraint)

        parent_constraint = mc.parentConstraint(
            ctl_locator, PARTICLE_NAME, mo=False)
        mc.delete(parent_constraint)

        # Setup Spring weight
        if not spring_weight:
            spring_weight = self.get_user_spring_weight()
        mc.goal(PARTICLE_NAME, g=ctl_locator, w=spring_weight)
        spring_loc_name = LOCATOR_NAME
        self.update_rigidity_value()

        # Create Spring locator and link it to the particle node
        spring_loc = mc.spaceLocator(n=spring_loc_name)
        scale = self.master_scale
        expression = (
            f'{spring_loc_name}.tx = {PARTICLE_NAME}.wctx / {scale};'
            f'{spring_loc_name}.ty = {PARTICLE_NAME}.wcty / {scale};'
            f'{spring_loc_name}.tz = {PARTICLE_NAME}.wctz / {scale};'
            )
        mc.expression(object=spring_loc_name, string=expression)

        mc.pointConstraint(spring_loc, self.aim_loc[0], mo=True)
        mc.parent(ctl_locator, PARTICLE_NAME, spring_loc, tool_grp)

        # BUILD AIM CONSTRAINT
        direction = self.get_direction()
        locked_rot_attr_list = self.get_locked_attr(rig_ctl_list[0], 'r')
        aim_vector, up_vector = AIM_VECTORS[direction]
        mc.aimConstraint(
            spring_loc[0],
            rig_ctl_list[0],
            aimVector=aim_vector,
            upVector=up_vector,
            worldUpVector=up_vector,
            worldUpObject=(ctl_locator[0]),
            worldUpType='objectrotation',
            mo=False,
            skip=locked_rot_attr_list,
            )
        mc.setAttr(f'{PARTICLE_NAME}.startFrame', frame_in)

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
    def bake_rot_tans_with_mel(self, current_ctl):
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

    def create_anim_layer(self, current_ctl):
        mc.select(current_ctl)
        mc.animLayer(
            f'{LAYER_PREFIX}_{self.get_node_shortname(current_ctl)}',
            aso=True,
            etr=True)
        mc.select(clear=True)

    def bake_ctl(self, current_ctl):
        layers = False
        if self.layers_on_qradbutton.isChecked():
            self.create_anim_layer(current_ctl)
            layers = True
        self.bake_rotation_with_mel(current_ctl, layers=layers)
        self.remove_setup()
        return

    @disable_viewport
    def launch_bake(self):

        if not mc.objExists(TOOLNAME):
            mc.warning('No Live Preview setup found, use Live Preview first')
            return
        print('--- BAKING Please WAIT ---')
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
            self.setup_live_preview([selected_rig_ctl[i]], (1-spring_weight))
            self.bake_ctl(current_ctl=selected_rig_ctl[i])
        mc.warning('Spring COMPLETED !')
        self.switch_back_vp_eval(vp_eval)


class SavePresetPopup(QWidget):
    def __init__(self, spring_value, rigidity_value, decay_value, position):
        super(SavePresetPopup, self).__init__()
        self.setWindowTitle("Save Preset")

        self.presets = presets.load_presets()
        self.spring_value = spring_value
        self.rigidity_value = rigidity_value
        self.decay_value = decay_value
        self.loc_position = position[0]
        self.load_preset_popup_ui()

    def load_preset_popup_ui(self):
        layout = QVBoxLayout()

        # Character Name
        character_layout = QHBoxLayout()
        character_label = QLabel("Character Name:")
        self.character_line_edit = QLineEdit()
        character_layout.addWidget(character_label)
        character_layout.addWidget(self.character_line_edit)
        layout.addLayout(character_layout)

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

    def save_preset_pressed(self):
        character_name = self.character_line_edit.text()
        body_part = self.body_part_line_edit.text()
        spring = self.spring_spinbox.value()
        rigidity = self.rigidity_spinbox.value()
        decay = self.decay_spinbox.value()
        position_x = self.position_tx_spinbox.value()
        position_y = self.position_ty_spinbox.value()
        position_z = self.position_tz_spinbox.value()
        position = [position_x, position_y, position_z]

        print("Character Name:", character_name)
        print("Body Part Name:", body_part)
        print("Spring:", spring)
        print("Rigidity:", rigidity)
        print("Decay:", decay)
        print("position", position)

        presets.save_preset(
            character_name,
            body_part,
            spring,
            rigidity,
            decay,
            position)
        self.close()


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
