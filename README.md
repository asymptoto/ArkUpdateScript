# ArkUpdateScript
A Python script to update ARK server mods
Tested on Linux only but this should work on Windows as well

### Requirements
- Python 3 (Python 2 should work as well but is untested, PyPy 3 is tested and works)
- Python `requests` module
- SteamCMD

### Installation
1. Clone the project into a directory
2. Set your ark server directory in settings.ini (the directory that includes ShooterGame)
3. Set your SteamCMD installation directory

### Usage
If you have Python 3 installed, you can simply call `./update.py` or you can specify a different Python interpreter with `<python interpreter> update.py`.
To save time, the ARK server files won't be updated by default. If you want to update the ARK server files as well, call the script with the `--update_game` option.
The script will automatically fetch mods from the `ActiveMods` option in `ShooterGame/Saved/Config/<Linux/Windows>NoEditor/GameUserSettings.ini` so you won't have to configure the installed mods manually.

Plsease report any issues you experience