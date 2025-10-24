import SwiftGUI as sg

class Matplot(
    sg.GlobalOptions.Common_Background,
    sg.GlobalOptions.Common_Textual,
    sg.GlobalOptions.Common,
    sg.GlobalOptions.Common_Canvas_Element,
):
    navigation_bar: bool = False
    borderwidth: int = 0
    legend: bool = None
    dpi: int = None
    background_color_outside: sg.Color | str = None
    width: int = None
    height: int = None
    bordercolor: sg.Color | str = None
    title: str = None
    spine_color: sg.Color | str = None
    tick_color: sg.Color | str = None



