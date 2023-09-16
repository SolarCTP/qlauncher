import pygame as pg
from tkinter import filedialog
import win32api
import win32con
import win32gui
from subprocess import Popen, DETACHED_PROCESS
from os import mkdir, remove
from os.path import isdir, exists
import icoextract
from PIL import Image
import keyboard
from configparser import ConfigParser
import webbrowser
import pylnk3 as lnk

import screenutils
import layout
import loader
from appevents import *
import winutils

import pystray as tray
from PIL import Image

import traceback

class AppIcons:
    UNSET = pg.image.load("./assets/buttonicons/newapp.png")
    CUSTOMIZATION = pg.image.load("./assets/settings/customization.png")
    SETTINGS = pg.image.load("./assets/settings/settings.png")

class App:

    # Constants initialization   
    TEXT_DISTANCE_FACTOR: float = 1.1
    DEFAULT_WINDOW_SCALE_FACTOR: float = 0.75

    def __init__(self,
        window_resolution: tuple = screenutils.calc_window_resolution(DEFAULT_WINDOW_SCALE_FACTOR),
        bg_opacity: int = 50):
        pg.init()
        self.resolution = window_resolution
        self.bg_opacity = bg_opacity
        self.window = None
        self.config: dict = {}
        self.loader = loader.Loader("./config.yaml")
        self._running = True
        self._autominimize_needed = False

        self.input_map = {
            pg.K_F1: 0,
            pg.K_F2: 1,
            pg.K_F3: 2,
            pg.K_F4: 3,
            pg.K_F5: 4,
            pg.K_F6: 5,
            pg.K_F7: 6,
            pg.K_F8: 7,
            pg.K_F9: 8,
            pg.K_F10: 9,
            pg.K_F11: 10,
            pg.K_F12: 11
        }
        self._keydown = False

        # font setup
        pg.font.init()
        self.main_font = pg.font.SysFont("Segoe UI", 24, bold=True)

        # initialize grid
        self.grid = layout.Grid(rows=3, columns=4)

        # initialize global hotkey
        keyboard.add_hotkey("alt+shift+enter", self.cb_global_hotkey_pressed)

    def run_application(self, cell: layout.Cell) -> None:
        if cell._get_application_extension() == ".url":
            webbrowser.open(cell.button["application_path"])
            return
        elif cell._get_application_extension() == ".lnk":
            lnk_file = lnk.Lnk(cell.button["application_path"])
            cmd = [lnk_file.path] # read exe from .lnk file
            print("Running: " + cmd[0]) # debug
            Popen(cmd,
                  creationflags=DETACHED_PROCESS,
                  shell=True if "%" in cmd[0] else False #use shell if there are any %env_variables%
                  )
            print("successful")
        else:
            cmd = [cell.button["application_path"]]
            print("Running: " + cmd[0]) # debug
            if cmd.count("") == 0:
                Popen(cmd, creationflags=DETACHED_PROCESS)
                print("succesful!")


                
    
    def set_apps_from_config(self) -> None:
        """"SETTER - Reads config and sets path and name for every application. To be run on startup."""
        for cell_id, button_properties in self.config.items():
            self.grid.cells[int(cell_id)].button["application_path"] = button_properties["application_path"]
            self.grid.cells[int(cell_id)]._set_application_name_from_path()
    
    
    def extract_icons_from_config(self) -> None:
        """Extracts the icon from every cell with a set application if it doesn't exist yet"""
        for cell in self.grid.cells:
            if cell.button["application_name"] and not exists(cell.button["app_icon_path"]):
                cell._set_application_icon_path_from_name()
                self.save_icon_to_file(cell)
    

    def draw(self):
        """Draws a background for each button, then all of the application icons (or the default + icon if the button app is not set). Finally draws the name of
        each application."""
        
        self.window.fill(pg.Color(0,0,0))
        for cell in self.grid.cells:
            keybind_text = self.main_font.render('F' + str(cell.id + 1), True, "white")
            keybind_text_width = keybind_text.get_width()
            keybind_text_height = keybind_text.get_height()
            pg.draw.circle(self.window, center = cell.button_rect.midright, color = pg.Color(255, 255, 255), radius=cell.button['side_length'] // 2.8)            
            app_bg_rect = cell.button_rect.inflate((cell.button['side_length'] * 0.15, cell.button['side_length'] * 0.15))
            app_outline_rect = app_bg_rect.inflate((cell.button['side_length'] * 0.04, cell.button['side_length'] * 0.04))
            # app_bg_rect = app_bg_rect.move((0, cell.button['side_length'] * 0.2))
            pg.draw.rect(self.window, pg.Color(255, 255, 255), app_outline_rect, border_radius = 30)
            keybind_slot_rect = pg.draw.circle(self.window, center = cell.button_rect.midright, color = pg.Color(35, 35, 35), radius=cell.button['side_length'] // 3)
            pg.draw.rect(self.window, pg.Color(35, 35, 35), app_bg_rect, border_radius = 30)
            self.window.blit(keybind_text, (keybind_slot_rect.centerx + (cell.button['side_length'] // 6) - (keybind_text_width / 2), keybind_slot_rect.midleft[1] - (keybind_text_height // 2)))


            if exists(cell.button["app_icon_path"]):
                button_icon_scaled = pg.transform.scale(pg.image.load(cell.button["app_icon_path"]).convert_alpha(),
                                                    (cell.button["side_length"], cell.button["side_length"]))
                self.window.blit(button_icon_scaled, cell.button_rect)
                # print("RENDERED ->" + cell.button["app_icon_path"]) # DEBUG
            else:
                self.window.blit(pg.transform.scale(AppIcons.UNSET, (cell.button["side_length"], cell.button["side_length"])), cell.button_rect)
           

            if cell.button["application_path"]:
                app_name_no_ext = cell._get_application_name_no_ext()
                app_name_text = self.main_font.render(app_name_no_ext.replace('_', ' '), True, "white")
                app_name_text_width = app_name_text.get_width()

                self.window.blit(app_name_text, (cell.button_rect.topleft[0] + (cell.button['side_length'] // 2) - (app_name_text_width / 2), cell.button_rect.topleft[1] + cell.button["side_length"] * 1.1))

    def _extract_icon_from_exe(self, cell: layout.Cell, from_lnk_file: bool = False):
        path_to_exe: str = ""
        if from_lnk_file:
            path_to_exe = lnk.Lnk(cell.button["application_path"]).path
        else:
            path_to_exe = cell.button["application_path"]
        extractor = icoextract.IconExtractor(path_to_exe)
        ico_file_path = cell.button["app_icon_path"][:-4:] + '.ico'
        extractor.export_icon(ico_file_path)
        with Image.open(ico_file_path) as ico_file:
            ico_file.save(cell.button["app_icon_path"])
        remove(ico_file_path)

    def save_icon_to_file(self, cell: layout.Cell) -> None:
        """Uses the icoextract module to save an app's icon from it's path with a specified name in the folder './appicons'.
        If it's a URL file (which is just an INI configuration file in disguise), the app path and icon path are read from it."""
        # create directory "appicons" if it doesn't exist, then execute icoextract and put the icon in that directory
        if not isdir("./appicons"):
            mkdir("./appicons", mode=755) # perms: read/write/exec for owner, read/write for group and others
        # cmd = "cmd /c \"icoextract.exe \"" + cell.button['application_path'].replace('/', '\\') + "\" \".\\appicons\\" + cell._get_application_name_no_ext() + "\"\""
        try:
            if cell._get_application_extension() == ".lnk":
                print(cell.button["application_path"])
                # lnk_file = lnk.Lnk(cell.button["application_name"])
                lnk_file = lnk.Lnk(cell.button["application_path"])
                if lnk_file.icon == None or lnk_file.icon.endswith(".exe"):
                    self._extract_icon_from_exe(cell=cell, from_lnk_file=True)
                else:
                    print(lnk_file.icon)
                    with Image.open(lnk_file.icon) as ico_file:
                        ico_file.save(cell.button["app_icon_path"])

            elif cell._get_application_extension() == ".exe":
                self._extract_icon_from_exe(cell=cell)

            elif cell._get_application_extension() == ".url":
                ini_parser = ConfigParser()
                ini_parser.read(cell.button["application_path"])
                print(ini_parser.sections())
                cell.button["application_path"] = ini_parser.get("InternetShortcut", "URL", raw=True)
                ico_file_path = ini_parser.get("InternetShortcut", "IconFile", raw=True)
                with Image.open(ico_file_path) as ico_file:
                    ico_file.save(cell.button["app_icon_path"])

        except icoextract.NoIconsAvailableError:
            print('WARNING - No icon avaible for ' + cell.button['application_name'],
                  "\nEither it doesn't have one or it has a custom one")

        except FileNotFoundError as e:
            print(cell.button["app_icon_path"])
            print("FROM save_icon_to_file:")
            traceback.print_exc()


    def restore_window(self) -> bool:
        if self._running:
            return winutils.restore_window()
        else:
            return False


    def cb_global_hotkey_pressed(self) -> None:
        """CALLBACK - called if the global hotkey is pressed (win+enter). Focuses the launcher if it was previously minimized."""
        winutils._minimize_triggered = 0
        return self.restore_window()


    def _update_config_single_button(self, cell: layout.Cell) -> None:
        """updates the config dict, then saves this updated version to the config"""
        self.config[f"{cell.id}"] = {
            "application_path": cell.button["application_path"]
        }
        self.loader._save(self.config)


    def update_single_button(self, cell: layout.Cell, executable_path: str) -> None:
        """Changes the title of the specified cell's button to app_name"""
        # update button in layout
        if executable_path == "":
            print("no app was selected")
        else:
            cell.button["application_path"] = executable_path
            cell._set_application_name_from_path()

        # update config and save
        self._update_config_single_button(cell=cell)


    def handle_mouse_input(self) -> None:
        """Takes care of handling the mouse, which currently is used to set an app to a button
        or (TODO) to change its icon"""
        if pg.mouse.get_pressed()[0]: # = left mouse button pressed
            for cell in self.grid.cells:
                if cell.button_rect.collidepoint(pg.mouse.get_pos()):
                    # BUTTON-APP Association:
                    # - Open windows explorer dialogue
                    selected_executable_path: str = winutils.filedialog_executable(cell.id)
                    
                    # - Set the chosen app or script with the dialogue
                    if selected_executable_path == "":
                        print("no app was selected") # debug, to be formalized
                        break
                    else:
                        self.update_single_button(cell, selected_executable_path)

                    # - Extract icon from exe files
                    cell._set_application_icon_path_from_name()
                    self.save_icon_to_file(cell)

                    # - Update the cell icon
                    self.draw()

                    break

        elif pg.mouse.get_pressed()[2]:
            for cell in self.grid.cells:
                if cell.button_rect.collidepoint(pg.mouse.get_pos()):
                    selected_img_path = winutils.filedialog_image(cell.id)

                    if selected_img_path == "":
                        print("no image was selected")
                        break
                    else:
                        with Image.open(selected_img_path) as img:
                            img.save(cell.button["app_icon_path"])

                    self.draw()

                    break

    def handle_kbd_input(self) -> None:
        if not self._keydown:
            for key in self.input_map.keys(): # application keys
                if pg.key.get_pressed()[key] and not (pg.key.get_mods() & pg.KMOD_ALT): # E.g. ALT+F4 should not trigger the F4 button
                    self._keydown = True
                    cell = self.grid._get_cell_from_id(self.input_map[key])
                    if cell.button["application_path"]:
                        self.run_application(cell)
                        pg.display.iconify()
                    else:
                        print("no app set for that button") # debug
                    break

    def check_events(self) -> bool:
        """Returns False if a pygame quit event occurs, otherwise returns True. The return value
        should be stored in the variable that determines whether to keep running the event loop or not.
        Also redraws the window if the respective timer ran out"""
        for event in pg.event.get():
                if event.type == pg.QUIT:
                    return False
                if event.type == REDRAWEVENT:
                    self.draw()
                if event.type == pg.KEYUP:
                    self._keydown = False
        return True
    
    def handle_minimize_events(self) -> None:
        """Hides the window if either ESC or Q is pressed"""
        minimize_keys = [pg.K_q, pg.K_ESCAPE]
        for key in minimize_keys:
            if pg.key.get_pressed()[key]:
                pg.display.iconify()
        winutils.minimize_if_unfocused()
    
    def set_window_transparent(self):
        """Just works\n
        Nobody knows how this works. But it does. That's the beauty of StackOverflow."""
        hwnd = pg.display.get_wm_info()["window"]
        # Getting information of the current active window
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
        win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0, 0, 0), 50, win32con.LWA_COLORKEY)

    def run(self):

        # pygame window initialization and setup
        self.window = pg.display.set_mode(self.resolution, flags=pg.NOFRAME, display=screenutils.get_primary_monitor_info()["id"])
        pg.display.set_icon(pg.image.load("./assets/icons/logo.png"))
        pg.display.set_caption("QLauncher")
        pg.display.iconify()
        self.set_window_transparent()

        # set a timer to redraw everything in the window every 2s (probably snake oil)
        pg.time.set_timer(REDRAWEVENT, 2000)

        # Load configuration
        try:
            self.config = self.loader._load()
            # print("loaded configuration")
            self.set_apps_from_config()
            self.extract_icons_from_config()
            # self.

        except FileNotFoundError as excp:

            print(str(excp.with_traceback(None))) # DEBUG

            # print("specified config file does not exist. creating one...")
            try:
                self.loader._save(self.config)
                # print('config file created')
            except:
                print("could not create file. quitting...")
                quit(1)

        # draws once before event loop. elements are rendered again only when actual changes happen
        # to decrease resource usage
        self.draw()

        clk = pg.time.Clock()
        while self._running:
            # clock
            clk.tick(screenutils.get_primary_monitor_refreshrate())

            # Handle quit events and timer to redraw window
            self._running = self.check_events() # will become False when quit event occurs

            # Handle minimizing events
            self.handle_minimize_events()

            # Handle app opening (keyboard) and app/icon setting (mouse)
            self.handle_mouse_input()
            self.handle_kbd_input()

            # Update screen
            pg.display.flip()
        else:
            pg.quit()
            

def main():
    app = App()
    try:
        app.run()
    except KeyboardInterrupt:
        print("quit")
    

if __name__ == "__main__":
    main()
