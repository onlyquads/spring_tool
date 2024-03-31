# Description:
Maya auto spring tool script.
Based on Luismi Herrera's logic of LMspring:
https://luismiherrera.gumroad.com/

Rewritten using Qt and python3 with better perferomances in bake process.
A preset system has been added, see the presets section

<div style="text-align: center;">
    <img src="https://garcia-nicolas.com/wp-content/uploads/2024/03/spring_tool_screenshot.png" alt="spring tool ui screenshot" width="300"/>
</div>

[Link to quick tutorial Video](https://garcia-nicolas.com/wp-content/uploads/2024/03/spring_tool_tuto.mp4)

# How to use:
Works only for rotations.
1. Select all the controllers of the chain. Also works with only 1 controller
2. Click create locator and align the created locator
to the end of the chain to set its scale
3. Hit preview and tweak spring/rigidity settings. This only previews the
first controller of the chain.
4. Hit bake to simulate and bake the whole chain

- Note: When previewing, you need to read timeline from its begining
    Tested on maya2022

# Presets:
You can add presets for different parts of a character/prop to be reused.
That preset file can be shared accross team of artists.
<p><b>Magic trick:</b>
Using presets, you'll be able to launch the whole sim and bake process
by right clicking any preset and 'Do Magic!' menu.</p>
<p>See installation instructions below.</p>


# Launch on-the-go:
Copy/Paste the whole `spring_tool.py` code in maya python console and run.
- Note: No presets UI will be shown if not fully installed and setup. See below

# Installation instructions :
To install the Spring Tool for Maya, follow these steps:

1. Copy the `spring_tool` folder into your Maya scripts directory. This directory is typically located at:

    | os       | path                                          |
    | ------   | ------                                        |
    | linux    | ~/< username >/maya                           |
    | windows  | \Users\<username>\Documents\maya              |
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
    presets_filename='spring_tool_presets.json'
    )
window.show()
```
- Note: 'prod_root_env_name' will be sent as string in 'os.environ.get(prod_root_env_name)' in 'get_presets_file_path' function.

