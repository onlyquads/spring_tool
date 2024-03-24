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
