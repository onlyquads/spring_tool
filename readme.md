## Description:
The Spring Tool is an auto spring simulation script for Maya, inspired by Luismi Herrera's LMspring:   [LMspring on Gumroad](https://luismiherrera.gumroad.com/).

Rewritten using Qt and python3 with better performances in bake process.
A preset system has been added, see the presets section

<div style="text-align: center;">
    <img src="https://garcia-nicolas.com/wp-content/uploads/2024/09/spring_tool.png" alt="spring tool ui screenshot" width="300"/>
</div>

[Watch a Quick Tutorial](https://garcia-nicolas.com/download/3147/?tmstv=1713513016&v=3148)

## How to use:

1. **Select Controllers:** Choose all the controllers in the chain (or just one).
2. **Create Locator:** Click "Create Locator" and align it to the end of the chain to set its scale.
3. **Preview:** Hit "Preview" and tweak the spring/rigidity settings. This previews only the first controller in the chain.
4. **Bake:** Click "Bake" to simulate and bake the entire chain.


> **Note:** When previewing, ensure you read the timeline from the beginning. Tested on Maya 2022.

## Presets:
You can add presets for different parts of a character/prop to be reused.
That preset file can be shared accross team of artists.
<p><b>Magic trick:</b>
Using presets, you'll be able to launch the whole sim and bake process
by right clicking any preset and 'Do Magic!' menu.</p>
See the Working with Presets section for details.

## Launch on-the-go:
You can quickly run the Spring Tool by copying the `spring_tool.py` code into Maya’s Python console and executing it.

> **Note:** The Presets UI will not be displayed unless the tool is fully installed and set up. See the installation instructions below.


## Installation instructions :
To install the Spring Tool for Maya, follow these steps:

1. Copy the `spring_tool` folder into your Maya scripts directory. This directory is typically located at:

    | os       | path                                          |
    | ------   | ------                                        |
    | linux    | ~/< username >/maya                           |
    | windows  | \Users\\%username%\Documents\maya              |
    | mac os x | ~<username>/Library/Preferences/Autodesk/maya |

2. Launch Maya and run the following Python code in the Maya Script Editor
or Python console to open the tool without presets functions:
   ```python
   from spring_tool import spring_tool
   window = spring_tool.SpringToolWindow()
   window.show()
   ```

To launch spring_tool with presets functions, you'll need to add path and filename
to args.
If you work in team, make sure the presets file is in a shared directory sothat
everyone can get and add presets.

Example:

```python
from spring_tool import spring_tool
window = spring_tool.SpringToolWindow(
    prod_root_env_name = None,  # can be usefull if you work with environments
    presets_dir_path='/Users/Username/Desktop',
    presets_filename='spring_tool_presets.json',
    lock_write_presets=False  # can be used to prevent users to add presets
    )
window.show()
```
- Note: 'prod_root_env_name' will be sent as string in 'os.environ.get(prod_root_env_name)' in 'get_presets_file_path' function.

## Working with Presets:
Once the Spring Tool is installed correctly, you should see a panel on the right side of the interface.

### Creating Presets

To create a preset, follow these steps:

    1.	Select the controllers you want to work with.
    2.	Create a locator and position it at the end of the chain.
    3.	Click ‘Save Preset’—the locator’s coordinates and values will be automatically populated in the Save Preset popup window.

### Applying Presets

When presets are available, you can apply them easily:

    1.	Select the necessary controllers in the viewport.
    2.	Right-click on the desired preset and choose the ‘DO MAGIC’ option.

This will automatically execute the entire process, applying the preset seamlessly.


## Presets Administration UI instructions :
The Spring Tool includes an administration window for managing presets. You can use this interface to tweak, rename, or delete any created preset.

<div style="text-align: center;">
    <img src="https://garcia-nicolas.com/wp-content/uploads/2024/08/spring_tool_admin-e1723926107251.png" alt="spring tool admin ui screenshot" width="300"/>
</div>



To launch it run this python command:

```python
from spring_tool import presets_admin
window = presets_admin.SpringToolPresetAdmin(
    prod_root_env_name=None, # can be usefull if you work with environments
    presets_dir_path="/Users/Username/Desktop",
    presets_filename="spring_tool_presets.json",
    authorized_access=True,  # Set this to False if you want to prevent users to access the administration window
    )
window.show()
```