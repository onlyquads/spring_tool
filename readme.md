# Description:
Maya auto spring tool script.
Based on Luismi Herrera's logic of LMspring:
https://luismiherrera.gumroad.com/

Rewritten using Qt and python3 with better perferomances in bake process.
A preset system has been added, see the presets section

<img src="https://garcia-nicolas.com/wp-content/uploads/2024/03/spring_tool_screenshot.png" alt="spring tool ui screenshot" width="300"/>

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
Copy/Paste the whole `spring_tool.py` code in maya python console and run
Note: No presets UI will be shown if not fully installed and setup. See below

# Installation instructions :
To install the Spring Tool for Maya, follow these steps:

1. Copy the `spring_tool` folder into your Maya scripts directory. This directory is typically located at:

    | os       | path                                          |
    | ------   | ------                                        |
    | linux    | ~/< username >/maya                           |
    | windows  | \Users\<username>\Documents\maya              |
    | mac os x | ~<username>/Library/Preferences/Autodesk/maya |

2. Open presets.py and setup the different paths:

    ```python
    # Example
    PROD_NIMBLE_ROOT = "PROD_ROOT_ENV_STR"
    JSON_PRESET_PATH = "documents/synced_folder/spring_presets"
    JSON_FILENAME = "spring_tool_presets.json"
    MAC_JSON_PRESET_PATH = "/Users/Username/Desktop/"
    ```

3. Launch Maya and run the following Python code in the Maya Script Editor or Python console to open the tool:
   ```python
   from spring_tool import spring_tool
   window = spring_tool.SpringToolWindow()
   window.show()
