import tkinter as tk
import SwiftGUI as sg
import matplotlib.lines
from SwiftGUI.Compat import Self
from matplotlib.figure import Figure
from matplotlib.axes._axes import Axes
from typing import Hashable, Any
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk,
)

from SwiftGUI_Matplot import GlobalOptions


class Matplot(sg.BaseWidget):
    tk_widget: tk.Canvas
    defaults = GlobalOptions.Matplot

    def __init__(
            self,
            /,
            figure: Figure = None,
            axes: Axes = None,

            key: Hashable = None,
            legend: bool = None,

            navigation_bar: bool = None,

            dpi: int = None,

            background_color: sg.Color | str = None,
            background_color_outside: sg.Color | str = None,

            width: int = None,
            height: int = None,

            borderwidth: int = None,
            bordercolor: sg.Color | str = None,

            title: str = None,

            spine_color: sg.Color | str = None,
            tick_color: sg.Color | str = None,
            text_color: sg.Color | str = None,

            # expand: bool = None,
            # expand_y: bool = None,
            tk_kwargs: dict = None,
    ):
        super().__init__(
            key=key,
            # expand= expand,
            # expand_y= expand_y,
            tk_kwargs=tk_kwargs,
        )


        if figure is None:
            figure = Figure()

        if axes is None:
            axes = figure.add_subplot()

        self.figure = figure
        self.axes = axes

        self._legend = self.defaults.single("legend", legend)

        self._update_initial(
            text_color = text_color,
            background_color_outside = background_color_outside,
            background_color = background_color,
            height = height,
            width = width,
            dpi = dpi,
            borderwidth = borderwidth,
            bordercolor = bordercolor,
            title = title,
            spine_color = spine_color,
            tick_color = tick_color,
        )

        self._add_toolbar = self.defaults.single("navigation_bar", navigation_bar)

    toolbar: NavigationToolbar2Tk = None
    def _init_widget_for_inherrit(self, container) -> tk.Widget:
        frame = tk.Frame(master= container)

        figure_canvas = FigureCanvasTkAgg(self.figure, master= frame)
        self.canvas = figure_canvas

        figure_canvas.get_tk_widget().pack()

        if self._add_toolbar:
            self.toolbar = NavigationToolbar2Tk(self.canvas)

        return frame

    _text_color = None  # Color of the title and the axis-labels
    def _update_special_key(self,key:str,new_val:Any) -> bool|None:
        match key:
            case "background_color":
                if new_val is None:
                    return
                self.axes.set_facecolor(new_val)
            case "background_color_outside":
                new_val = self.defaults.single("background_color", new_val)
                if new_val is None:
                    return
                self.figure.set_facecolor(new_val)

            case "height":
                if new_val is None:
                    return
                self.figure.set_figheight(new_val)
            case "width":
                if new_val is None:
                    return
                self.figure.set_figwidth(new_val)

            case "dpi":
                if new_val is None:
                    return
                self.figure.set_dpi(new_val)

            case "borderwidth":
                if new_val is None:
                    return
                self.figure.set_linewidth(new_val)
            case "bordercolor":
                new_val = self.defaults.single("color", new_val)
                if new_val is None:
                    return
                self.figure.set_edgecolor(new_val)

            case "title":
                if new_val is None:
                    return
                self.axes.set_title(
                    new_val,
                    color= self.defaults.single("text_color", self._text_color)
                )

            case "spine_color":
                new_val = self.defaults.single("text_color", new_val)
                if new_val is None:
                    return
                self.axes.spines["bottom"].set_color(new_val)
                self.axes.spines["top"].set_color(new_val)
                self.axes.spines["left"].set_color(new_val)
                self.axes.spines["right"].set_color(new_val)
            case "tick_color":
                new_val = self.defaults.single("text_color", new_val)
                if new_val is None:
                    return
                self.axes.tick_params(colors=new_val)

            case "text_color":
                if new_val is None:
                    return
                self._text_color = new_val
                self.axes.xaxis.label.set_color(new_val)
                self.axes.yaxis.label.set_color(new_val)

            case _:
                return super()._update_special_key(key, new_val)

        return True

    def plot(self, xs, ys, *args, color= None, label:str= "", **kwargs) -> list[matplotlib.lines.Line2D]:
        """
        Call axes.plot with some global options applied
        :return:
        """
        kwargs["color"] = color

        self.defaults.apply(kwargs)

        kwargs["label"] = label

        r = self.axes.plot(xs, ys, *args, **kwargs)
        self.refresh()

        return r

    def scatter(self, xs, ys, *args, color= None, label:str= "", **kwargs) -> Any:
        """
        Call axes.plot with some global options applied
        :return:
        """
        kwargs["color"] = color

        self.defaults.apply(kwargs)

        kwargs["label"] = label

        r = self.axes.scatter(xs, ys, *args, **kwargs)
        self.refresh()

        return r

    def bar(self, x, height, width = 0.5, bottom = 0, *args, color= None, label:str= "", **kwargs) -> Any:
        """
        Call axes.plot with some global options applied
        :return:
        """
        kwargs["color"] = color

        self.defaults.apply(kwargs)

        kwargs["label"] = label

        r = self.axes.bar(x, height, width, bottom, *args, **kwargs)
        self.refresh()

        return r

    def grid(self, color= None, **kwargs):
        """
        Call axes.grid with some global options applied
        :param color:
        :param kwargs:
        :return:
        """
        kwargs["color"] = self.defaults.single("text_color", color)

        self.defaults.apply(kwargs)
        r = self.axes.grid(**kwargs)
        self.refresh()

        return r

    def refresh(self) -> Self:
        """
        Show changes made to the figure/axes
        :return:
        """
        if self.has_flag(sg.ElementFlag.IS_CREATED):
            if self._legend:
                self.axes.legend()

            self.canvas.draw()

        return self

    def clear(self) -> Self:
        """
        Remove all lines from the plot
        :return:
        """
        self.axes.cla()
        # lines = self.axes.lines
        # for l in lines:
        #     l.remove()

        self.refresh()
        return self

    def update(self, **kwargs) -> Self:
        super().update(**kwargs)
        self.refresh()
        return self
