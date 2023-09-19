# Qlauncher
### Warning: still in development
The project is still in a **pre-alpha state**, some core features have not yet been implemented and it is **not yet ready for use**. 

## About
QLauncher is a blazing fast alternative to the slow and laggy Windows search feature, at least for your most commonly used applications. It is written in python using [Pygame](https://github.com/pygame/pygame).

## How it works - some implementation details
It runs in the background until you press the hotkey to open it (`Alt + Shift + Enter` by default, no custom keybinds yet). Then the main window appears, where, on the first run, you will see blank buttons with a "+". To set an app to a button, click on it, then use the Explorer dialog to select the executable you want to run. QLauncher will extract the icon from the executable (if there is one) using the [Icoextract](https://github.com/jlu5/icoextract) module, then cache it to a directory called `appicons` (for faster subsequent startups of the launcher) and finally set the icon to the button you choose earlier.
Now you have set an application to that button, and you will be able to launch it by pressing the corresponding F key that is labeled on the right side of the button.
All the set apps are stored in a [Yaml](https://it.wikipedia.org/wiki/YAML) file called `config.yaml`, which is loaded on startup (TODO: check if the config's yaml syntax is respected, or else the launcher might crash) and updated every time an app on a button is set/changed

## Usage (from source):
Clone the repository and run these commands in the cloned directory:
```sh
python -m venv .
pip install -r requirements.txt
python main.py
```

## TODO

Alpha:
- Implement logging through the corresponding python module
- Customization settings:
  - Background color
  - Set background image
  - Background opacity
- Ability to move around applications
- Systray integration

Beta:
- Some animations, should be customizable
