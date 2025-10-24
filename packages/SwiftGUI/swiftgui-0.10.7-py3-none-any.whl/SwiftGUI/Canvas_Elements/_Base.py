from typing import Any, Callable, Hashable, Iterable

import SwiftGUI as sg
from SwiftGUI.Compat import Self

# Todo: Combined canvas-elements

class BaseCanvasElement(sg.BaseWidget): # Inheritance mainly for the update-routine
    defaults = sg.GlobalOptions.Common_Canvas_Element

    canvas: sg.Canvas   # "my" canvas

    _create_method: str = ""    # This should be the name of the method used to create this element with

    _grab_anywhere_on_this = False

    def __init__(
            self,
            key: Hashable = None,
            tk_kwargs: dict = None,
    ):
        super().__init__(key=key, tk_kwargs=tk_kwargs)
        self._is_created = False    # True, if _update_default_keys ran at least once
        self.canvas_id: int | None = None   # This is used to identify the element in the canvas-widget

    def attach_to_canvas(self, my_canvas: sg.Canvas) -> Self:
        """
        Add this element to a canvas.
        Same as my_canvas.add_canvas_element(...)
        :param my_canvas:
        :return:
        """
        my_canvas.add_canvas_element(self)
        return self

    @sg.BaseElement._run_after_window_creation
    def _update_initial(self,*args,**kwargs) -> Self:
        kwargs["_args"] = args
        super()._update_initial(**kwargs)
        return self

    def _update_default_keys(self,kwargs: dict,transfer_keys: bool = True):
        super()._update_default_keys(kwargs, transfer_keys=transfer_keys)

        if not self._is_created:
            fct = getattr(self.canvas.tk_widget, self._create_method)
            args = kwargs["_args"]
            del kwargs["_args"]

            self.canvas_id = fct(args, **kwargs)

            self._is_created = True
            return

        if "_args" in kwargs:
            del kwargs["_args"]
        self.canvas.tk_widget.itemconfigure(self.canvas_id, **kwargs)

    def init_window_creation_done(self):
        self.add_flags(sg.ElementFlag.IS_CREATED)
        self.window = self.canvas.window

        super().init_window_creation_done()

    def _apply_update(self):
        """This should do nothing for canvas-elements!"""
        return

    def _get_value(self) -> Any:
        raise AttributeError(f"{self} has no value!")

    def set_value(self, new_val: Any) -> Any:
        raise AttributeError(f"{self} has no value to set!")

    def _bind_event_to_widget(self, tk_event: str, event_function: Callable) -> Self:
        self.canvas.tk_widget.tag_bind(self.canvas_id, tk_event, event_function)
        return self

    @sg.BaseWidget._run_after_window_creation
    def delete(self) -> Self:
        """
        Delete the element from the canvas.
        :return:
        """
        self.canvas.tk_widget.delete(self.canvas_id)
        return self

    @sg.BaseWidget._run_after_window_creation
    def move_to(self, x: float, y: float) -> Self:
        """
        Move the element to specified coordinates

        :param x:
        :param y:
        :return:
        """
        self.canvas.tk_widget.moveto(self.canvas_id, x, y)
        return self

    #@sg.BaseWidget._run_after_window_creation
    def move(self, x: float, y: float) -> Self:
        """
        Move the element in the specified direction

        :param x: Change in x
        :param y: Change in y
        :return:
        """
        self.canvas.tk_widget.move(self.canvas_id, x, y)
        return self

    @staticmethod
    def _flatten(tuplelist: Iterable[tuple[Any, ...]]) -> list[Any]:
        """
        Turn a list of tuples into a flat list
        :param tuplelist: (x0, y0), (x1, y0), ...
        :return: [x0, y0, x1, y1, ...]
        """
        return [x for xs in tuplelist for x in xs]

    @staticmethod
    def _unflatten(flatlist: Iterable[Any]) -> tuple[tuple[Any], ...]:
        """
        Opposite of flatten
        :param flatlist:
        :return:
        """
        return tuple(sg.Compat.batched(flatlist, 2))

    @sg.BaseWidget._run_after_window_creation
    def update_coords(self, *new_coords: tuple[float, float]) -> Self:
        """
        Update the coordinates of this element.
        What the exact coordinates do is dependent on the actual type of element.
        :param new_coords: (x0, y0), (x1, y1), ...
        :return:
        """
        self.canvas.tk_widget.coords(self.canvas_id, self._flatten(new_coords))
        return self

    def get_coords(self) -> tuple[tuple[float], ...]:
        """
        Return the coordinates of this element.
        What the exact coordinates represent is dependent on the actual type of element.
        :return:
        """
        return self._unflatten(self.canvas.tk_widget.coords(self.canvas_id))

    def get_boundary(self) -> tuple[tuple[int], ...] | tuple[tuple[int], tuple[int]]:
        """
        Return the coordinates of a rectangle that just fits around this element
        :return:
        """
        return self._unflatten(self.canvas.tk_widget.bbox(self.canvas_id))

    def __repr__(self):
        return f"<sgc.{self.__class__.__name__} element at {id(self)}>"
