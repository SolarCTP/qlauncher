import pygame as pg
from typing import NamedTuple
import screenutils
from os.path import abspath, exists

class Button(NamedTuple):
    side_length: int
    icon: None
    application_name: str
    center: tuple

class ImageIcon:
    pass

class Cell:
    def __init__(self, cell_x: int, 
                cell_y: int,
                cell_width: int,
                cell_height: int,
                cell_id: int,
                button_side_length: int,
                button_icon: ImageIcon,
                button_application_path: str):
        
        self.rect = pg.Rect(cell_x, cell_y, cell_width, cell_height)
        self.button = {'side_length': button_side_length,
                    'icon': button_icon,
                    'application_path': button_application_path,
                    'application_name': '',
                    'app_icon_path': '',
                    'center': self.rect.center}
        self.button_rect = pg.Rect(0, 0, self.button['side_length'], self.button['side_length'])
        self.button_rect.center = self.button['center']
        self.id = cell_id

        self._set_application_name_from_path()


    def _set_application_name_from_path(self) -> None:
        """SETTER - Get app name by finding the last slash (which is the first one in reverse order), then subtracting it from the
        number of characters in the path. This does include the extension, though. Then set it as a property of the cell"""
        name = self.button['application_path'][len(self.button['application_path']) - self.button['application_path'][::-1].find('/')::]
        self.button["application_name"] = name

    def _get_application_extension(self) -> str:
        """GETTER - Returns the extension for a button's application"""
        ext = self.button["application_name"][len(self.button["application_name"]) - self.button["application_name"][::-1].find(".") - 1::]
        return ext


    def _get_application_name_no_ext(self) -> str:
        """GETTER - Returns the application name without the extension. The logic is similar to _set_application_name_from_path()"""
        app_name_no_ext = self.button["application_name"][:len(self.button["application_name"]) - self.button["application_name"][::-1].find(".") - 1:]
        return app_name_no_ext


    def _set_application_icon_path_from_name(self) -> None:
        """SETTER - Sets the property app_icon_path to the absolute path to the icon of application_name. Icons are saved in a
        folder named 'appicons' in the same directory as the AppLauncher executable (TO BE CHANGED)."""
        icon_rel_path = ".\\appicons\\" + self._get_application_name_no_ext() + ".png"
        #print('icon_rel_path: ' + icon_rel_path) # DEBUG
        if self.button["application_path"]:
            icon_abs_path = abspath(icon_rel_path)
            #print('icon_abs_path: ' + icon_abs_path) # DEBUG
            self.button["app_icon_path"] = icon_abs_path
        else:
            raise Exception(icon_rel_path + " does not exist")


class Grid:
    def __init__(self, rows: int, columns: int):
        self.rows = rows
        self.columns = columns

        # init cell variables
        self.cell_width = screenutils.get_window_resolution(0.75)[0] // self.columns
        self.cell_height = screenutils.get_window_resolution(0.75)[1] // self.rows
        self.cells: list[Cell] = []

        # init button variables
        self.button_side_lenght = 0
        if self.cell_height <= self.cell_width:
            self.button_side_lenght = self.cell_height * 0.6
        else:
            self.button_side_lenght = self.cell_width * 0.6
            
        # cell creation
        x = 0
        y = 0
        id = 0
        for _ in range(rows):
            for _ in range(columns):
                self.cells.append(Cell(cell_x=x, 
                                       cell_y=y,
                                       cell_width=self.cell_width, 
                                       cell_height=self.cell_height,
                                       cell_id=id,
                                       button_side_length=self.button_side_lenght,
                                       button_icon=None,
                                       button_application_path=''))
                id += 1
                x += self.cell_width
            y += self.cell_height
            x = 0

    def _get_cell_from_id(self, cell_id: int) -> Cell:
        for cell in self.cells:
            if cell.id == cell_id:
                return cell