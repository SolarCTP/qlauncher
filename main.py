import pygame as pg
import screenutils
import layout
import loader
from tkinter import filedialog
import win32api
import win32con
import win32gui
from subprocess import run
from os import mkdir, remove
from os.path import isdir, exists
import icoextract
from PIL import Image
from pynput import keyboard as kbd
import threading

class DefaultIcons:
    UNSET = pg.image.load("./assets/buttonicons/newapp.png")
    CUSTOMIZATION = pg.image.load("./assets/settings/customization.png")
    SETTINGS = pg.image.load("./assets/settings/settings.png")

class App:

    # Constants initialization   
    TEXT_DISTANCE_FACTOR: float = 1.1
    DEFAULT_WINDOW_SCALE_FACTOR: float = 0.75

    def __init__(self,
        window_resolution: tuple = screenutils.get_window_resolution(DEFAULT_WINDOW_SCALE_FACTOR),
        bg_opacity: int = 50):
        pg.init()
        self.resolution = window_resolution
        self.bg_opacity = bg_opacity
        self.window = None
        self.config: dict = {}
        self.loader = loader.Loader("./config.yaml")
        self._running = True
        self.global_hotkey_listener = kbd.GlobalHotKeys(
            {
                "<alt>+<enter>": self.cb_global_hotkey_pressed
            }
        )
        self.global_hotkey_listener.daemon = True
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
            pg.K_F1: 9,
            pg.K_F11: 10,
            pg.K_F12: 11
        }
        
        # font setup
        pg.font.init()
        self.main_font = pg.font.SysFont("Segoe UI", 24, bold=True)

        # initialize grid
        self.grid = layout.Grid(rows=3, columns=4)

        # initialize global hotkey

    def run_application(self, cell: layout.Cell):
        cmd = ["start", cell.button["application_path"]]
        run(cmd, shell=False)

    def handle_kbd_input(self) -> None:
        for key in self.input_map.keys():
                if pg.key.get_pressed()[key] and not pg.key.get_mods(): # E.g. ALT+F4 should not trigger the F4 button
                    cell = self.grid._get_cell_from_id(self.input_map[key])
                    self.run_application(cell)
                    pg.display.iconify()
    
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
                print("RENDERED ->" + cell.button["app_icon_path"]) # DEBUG
            else:
                self.window.blit(pg.transform.scale(DefaultIcons.UNSET, (cell.button["side_length"], cell.button["side_length"])), cell.button_rect)
           
            if cell.button["application_path"]:

                app_name_no_ext = cell._get_application_name_no_ext()
                app_name_text = self.main_font.render(app_name_no_ext.replace('_', ' '), True, "white")
                app_name_text_width = app_name_text.get_width()

                self.window.blit(app_name_text, (cell.button_rect.topleft[0] + (cell.button['side_length'] // 2) - (app_name_text_width / 2), cell.button_rect.topleft[1] + cell.button["side_length"] * 1.1))

            # --- DEBUG ---
            # if cell.button["application_path"]:
            #     window.blit(main_font.render("  " + str(cell.id) + " - " + str(cell.button["application_path"]), True, "white"), cell.rect)
            # else:
            #     window.blit(main_font.render("  " + str(cell.id), True, "white"), cell.rect)
            # -------------


    def save_icon_to_file(self, cell: layout.Cell) -> None:
        """Uses the icoextract module to save an app's icon from it's path with a specified name in the folder './appicons'"""
        # create directory "appicons" if it doesn't exist, then execute icoextract and put the icon in that directory
        if not isdir("./appicons"):
            mkdir("./appicons", mode=755) # perms: read/write/exec for owner, read/write for group and others
        # cmd = "cmd /c \"icoextract.exe \"" + cell.button['application_path'].replace('/', '\\') + "\" \".\\appicons\\" + cell._get_application_name_no_ext() + "\"\""
        try:
            extractor = icoextract.IconExtractor(cell.button["application_path"])
            ico_file_path = cell.button["app_icon_path"][:-4:] + '.ico'
            extractor.export_icon(ico_file_path)
            with Image.open(ico_file_path) as ico_file:
                ico_file.save(cell.button["app_icon_path"])
            remove(ico_file_path)
        except icoextract.NoIconsAvailableError:
            print('WARNING - No icon avaible for ' + cell.button['application_name'])
        except FileNotFoundError as e:
            print(cell.button["app_icon_path"])
            print("FROM save_icon_to_file: " + str(e))

    def cb_global_hotkey_pressed(self) -> None:
        """CALLBACK - called if the global hotkey is pressed (win+enter). Focuses the launcher if it was previously minimized."""
        print("pressed key")
        if self._running:
            self.resolution = screenutils.get_window_resolution(App.DEFAULT_WINDOW_SCALE_FACTOR)
            self.window = pg.display.set_mode(self.resolution, flags=pg.NOFRAME, display=screenutils.get_primary_monitor_info()["id"])
            print("restored window") # DEBUG
            return True
        else:
            return False

    def handle_mouse_input(self) -> None:
        """Takes care of handling the mouse, which currently is used to set an app to a button"""
        if pg.mouse.get_pressed()[0]:
                for cell in self.grid.cells:
                    if cell.button_rect.collidepoint(pg.mouse.get_pos()):
                        # BUTTON-APP Association:
                        # - Open windows explorer dialogue
                        executable_filetypes = (
                            ("Executable program", "*.exe"),
                            ("Executable program (legacy)", "*.com"),
                            ("Batch script", "*.bat"),
                            ("Python script", "*.py"),
                            ("Powershell script", "*.ps1")
                        )
                        selected_app: str = filedialog.askopenfilename(filetypes=executable_filetypes,
                                                                  title=f"Please choose the program for button ID {cell.id}")
                        
                        # - Set the chosen app or script with the dialogue
                        if selected_app == "":
                            print("no app was selected")
                            break
                        else:
                            cell.button["application_path"] = selected_app
                            cell._set_application_name_from_path()
                        # - Add to config dict
                        self.config[f"{cell.id}"] = {
                            "application_path": cell.button["application_path"]
                        }

                        # - Write config dict
                        try:
                            self.loader._save(self.config)
                        except Exception as e:
                            print("could not save file!!!")
                            print("here is your vomit cascade of a python traceback lmao")
                            raise(e)

                        # - Extract icon from exe files only
                        if cell._get_application_extension() == '.exe':
                            cell._set_application_icon_path_from_name()
                            self.save_icon_to_file(cell)

                            # - Update the cell icon
                            self.draw()
                        break

    def handle_quit_events(self) -> bool:
        """Returns False if a pygame quit event occurs, otherwise returns True. The return value
        should be stored in the variable that determines whether to keep running the event loop or not."""
        for event in pg.event.get():
                if event.type == pg.QUIT:
                    return False
        return True
    
    def handle_minimize_events(self) -> None:
        """Minimizes the window if either ESC or Q is pressed"""
        if pg.key.get_pressed()[pg.K_ESCAPE] or pg.key.get_pressed()[pg.K_q]:
            pg.display.iconify()
    
    def set_window_transparent(self):
        """Nobody knows how this works. But it does. That's the beauty of abstraction and of StackOverflow."""
        hwnd = pg.display.get_wm_info()["window"]
        # Getting information of the current active window
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
        win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0, 0, 0), 50, win32con.LWA_COLORKEY)

    def run(self):

        # pygame window initialization and setup
        self.window = pg.display.set_mode(self.resolution, flags=pg.NOFRAME, display=screenutils.get_primary_monitor_info()["id"])
        pg.display.set_icon(pg.image.load("./assets/icons/logo.png"))
        pg.display.iconify()
        self.set_window_transparent()

        # Load configuration
        try:
            self.config = self.loader._load()
            # print("loaded configuration")
            self.set_apps_from_config()
            self.extract_icons_from_config()


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
        # to decrease useless operations
        self.draw()

        clk = pg.time.Clock()
        while self._running:
            # clock
            clk.tick(60)

            # Handle quit events
            self._running = self.handle_quit_events() # will become False when quit event occurs
            
            # Handle minimizing events
            self.handle_minimize_events()

            # Handle app opening (keyboard) and app setting (mouse)
            self.handle_mouse_input()
            self.handle_kbd_input()

            # Update screen
            pg.display.flip()
        else:
            pg.quit()
            

def main():
    app = App()
    app.global_hotkey_listener.start()
    try:
        app.run()
    except KeyboardInterrupt:
        print("quit")
    

if __name__ == "__main__":
    main()