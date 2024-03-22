import os
import platform
import json
import maya.cmds as mc

'''
Setup paths and preset file name here. For collab, place the
preset json file in a shared directory.
If pref file doesn't exist at given path, it'll create it.

'''

PROD_ROOT = None  # string path (optional)
JSON_PRESET_PATH = None  # string path Use only dir, file name is next line
JSON_FILENAME = 'spring_tool_presets.json'  # Rename if you want
MAC_JSON_PRESET_PATH = ''  # Leave empty if no MAC OS


def get_pref_file_path():

    pref_dir_path = ''
    prod_root = None
    if PROD_ROOT:
        prod_root = os.environ.get(PROD_ROOT)
        print('no prod_root')

    if not JSON_PRESET_PATH:
        return None

    system = platform.system()
    if system == 'Windows':
        pref_dir_path = os.path.normpath(JSON_PRESET_PATH)
    elif system == 'Darwin':
        pref_dir_path = os.path.normpath(MAC_JSON_PRESET_PATH)

    if prod_root:
        pref_dir_path = os.path.join(prod_root, pref_dir_path)

    if not os.path.isdir(pref_dir_path):
        mc.warning('Preference dir not found! ')
        return None

    presets_file_path = os.path.normpath(
        os.path.join(pref_dir_path, JSON_FILENAME))
    return presets_file_path


def load_presets():
    if not get_pref_file_path():
        return None
    try:
        with open(get_pref_file_path(), 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def get_preset(character_name, body_part):
    presets = load_presets()
    if not presets:
        return None
    return presets.get(character_name, {}).get(body_part)


def get_available_characters():
    presets = load_presets()
    if not presets:
        return None
    return list(presets.keys())


def get_available_body_parts(character_name):
    presets = load_presets()
    if not presets:
        return None
    return list(presets.get(character_name, {}).keys())


def get_body_part_info(character_name, body_part):
    preset = get_preset(character_name, body_part)
    return preset if preset else {}


def get_position(character_name, body_part):
    body_part_info = get_body_part_info(character_name, body_part)
    return tuple(body_part_info.get('position', (0, 0, 0)))


def save_preset(
        character_name, body_part, spring, spring_rigidity, decay, position):
    presets = load_presets()
    if character_name not in presets:
        presets[character_name] = {}
    if body_part in presets.get(character_name, {}):
        raise ValueError(
            f"Body part '{body_part}' already exists for '{character_name}'")
    presets[character_name][body_part] = {
        'spring_value': spring,
        'spring_rigidity': spring_rigidity,
        'decay': decay,
        'position': position
    }
    with open(get_pref_file_path(), 'w') as f:
        json.dump(presets, f, indent=4)
