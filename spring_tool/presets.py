'''
Handle json save, search and get
'''

import json


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
        'spring_value': spring,
        'spring_rigidity': spring_rigidity,
        'decay': decay,
        'position': position
    }
    with open(path, 'w') as f:
        json.dump(presets, f, indent=4)


def get_all_data(path, character_name, body_part):
    presets = load_presets(path)
    if not presets or character_name not in presets or body_part not in presets[character_name]:
        # Return None for all variables if data doesn't exist
        return None, None, None, None

    data = presets[character_name][body_part]
    if not isinstance(data, dict):  # Check if data is a dictionary
        # Return None for all variables if data is not a dictionary
        return None, None, None, None

    spring_value = data.get('spring_value')
    spring_rigidity = data.get('spring_rigidity')
    decay = data.get('decay')
    pos_data = data.get('position')

    position = [(pos_data[0], pos_data[1], pos_data[2])]

    return spring_value, spring_rigidity, decay, position


def remove_preset(path, character_name, body_part):
    presets = load_presets(path)
    if not presets or character_name not in presets or body_part not in presets[character_name]:
        return False  # Return False if the preset doesn't exist

    del presets[character_name][body_part]

    # If there are no more presets for the character,
    # remove the character entry as well
    if not presets[character_name]:
        del presets[character_name]

    # Save the updated presets to the JSON file
    with open(path, 'w') as f:
        json.dump(presets, f, indent=4)

    return True  # Return True to indicate successful removal


def edit_preset(
        path,
        character_name,
        body_part,
        spring=None,
        spring_rigidity=None,
        decay=None,
        position=None
        ):
    presets = load_presets(path)
    if character_name not in presets or body_part not in presets[character_name]:
        raise ValueError(
            f"Body part '{body_part}' does not exist for '{character_name}'")

    preset = presets[character_name][body_part]
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
