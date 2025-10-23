import tkinter as tk
import tkinter.font as font
from collections.abc import Iterable, Callable
from typing import Literal, Any

from SwiftGUI import ElementFlag, BaseWidget, GlobalOptions, Literals, Color
from SwiftGUI.Compat import Self


class Input(BaseWidget):
    """
    Copy this class ot create your own Widget

    The following methods are to be overwritten if needed:
    _get_value  (determines the value returned by this widget)
    _init_widget_for_inherrit   (Initializes the widget)
    """
    _tk_widget_class:type = tk.Entry # Class of the connected widget
    defaults = GlobalOptions.Input   # Default values (Will be applied to kw_args-dict and passed onto the tk_widget

    _transfer_keys = {
        "background_color_disabled":"disabledbackground",
        "background_color_readonly":"readonlybackground",
        "background_color":"background",
        "text_color":"foreground",
        "text_color_disabled": "disabledforeground",
        "highlightbackground_color": "highlightbackground",
        "selectbackground_color": "selectbackground",
        "select_text_color": "selectforeground",
        "pass_char":"show",
        "cursor_color":"insertbackground",
    }

    def __init__(
            self,
            # Add here
            text: str = None,
            /,
            key: Any = None,
            key_function: Callable|Iterable[Callable] = None,
            width: int = None,
            default_event: bool = False,
            #
            cursor: Literals.cursor = None,
            takefocus: bool = None,
            #
            justify: Literal["left","right","center"] = None,
            background_color: str|Color = None,
            background_color_readonly: str|Color = None,
            text_color: str|Color = None,
            text_color_disabled: str|Color = None,
            highlightbackground_color: str|Color = None,
            selectbackground_color: str|Color = None,
            select_text_color: str|Color = None,
            cursor_color: str | Color = None,
            selectborderwidth: int = None,
            highlightcolor: str|Color = None,
            highlightthickness: int = None,
            pass_char: str = None,
            readonly: bool = None,   # Set state to tk.Normal, or 'readonly'
            relief: Literals.relief = None,
            exportselection: bool = None,
            validate: Literals.validate = None,
            validatecommand: Callable = None,
            #
            # Mixed options
            fonttype: str = None,
            fontsize: int = None,
            font_bold: bool = None,
            font_italic: bool = None,
            font_underline: bool = None,
            font_overstrike: bool = None,
            #
            expand: bool = None,
            expand_y: bool = None,
            tk_kwargs: dict[str:Any]=None
    ):
        """

        :param text: Default text to be displayed
        :param key: Element-Key. Can be used to change the text later
        :param cursor: Cursor-Type. Changes how the cursor looks when hovering over this element
        :param takefocus: True, if you want this element to be able to be focused when pressing tab. Most likely False for texts.
        :param tk_kwargs: Additional kwargs to pass to the ttk-widget
        :param background_color: Background-Color
        """
        # Not used:
        # :param underline: Which character to underline for alt+character selection of this element

        super().__init__(key=key,tk_kwargs=tk_kwargs,expand=expand,expand_y=expand_y)
        self._key_function = key_function

        if tk_kwargs is None:
            tk_kwargs = dict()

        self._default_event = default_event
        self._value_change_callback: Callable | None = None
        # if default_event:
        #     self.bind_event("<KeyRelease>",key=self.key,key_function=self._key_function)

        self._update_initial(
            takefocus = takefocus,
            background_color = background_color,
            background_color_readonly = background_color_readonly,
            cursor = cursor,
            readonly = readonly,
            exportselection = exportselection,
            font_bold = font_bold,
            font_italic = font_italic,
            font_overstrike = font_overstrike,
            font_underline = font_underline,
            fontsize = fontsize,
            fonttype = fonttype,
            highlightbackground_color = highlightbackground_color,
            highlightcolor = highlightcolor,
            highlightthickness = highlightthickness,
            justify = justify,
            pass_char = pass_char,
            relief = relief,
            select_text_color = select_text_color,
            selectbackground_color = selectbackground_color,
            selectborderwidth = selectborderwidth,
            text = text,
            text_color = text_color,
            text_color_disabled = text_color_disabled,
            validate = validate,
            validatecommand = validatecommand,
            width = width,
            cursor_color = cursor_color,
            **tk_kwargs,
        )

    def _update_font(self):
        # self._tk_kwargs will be passed to tk_widget later
        self._tk_kwargs["font"] = font.Font(
            self.window.parent_tk_widget,
            family=self._fonttype,
            size=self._fontsize,
            weight="bold" if self._bold else "normal",
            slant="italic" if self._italic else "roman",
            underline=bool(self._underline),
            overstrike=bool(self._overstrike),
        )

    def _update_special_key(self, key: str, new_val: Any) -> bool|None:
        # Fish out all special keys to process them seperately
        match key:
            case "default_event":
                self._default_event = new_val
            case "fonttype":
                self._fonttype = self.defaults.single(key,new_val)
                self.add_flags(ElementFlag.UPDATE_FONT)
            case "fontsize":
                self._fontsize = self.defaults.single(key,new_val)
                self.add_flags(ElementFlag.UPDATE_FONT)
            case "font_bold":
                self._bold = self.defaults.single(key,new_val)
                self.add_flags(ElementFlag.UPDATE_FONT)
            case "font_italic":
                self._italic = self.defaults.single(key,new_val)
                self.add_flags(ElementFlag.UPDATE_FONT)
            case "font_underline":
                self._underline = self.defaults.single(key,new_val)
                self.add_flags(ElementFlag.UPDATE_FONT)
            case "font_overstrike":
                self._overstrike = self.defaults.single(key,new_val)
                self.add_flags(ElementFlag.UPDATE_FONT)
            case "readonly":
                self._tk_kwargs["state"] = "readonly" if new_val else "normal"
            case _: # Not a match
                return super()._update_special_key(key, new_val)

        return True

    def _apply_update(self):
        # If the font changed, apply them to self._tk_kwargs
        if self.has_flag(ElementFlag.UPDATE_FONT):
            self._update_font()
            self.remove_flags(ElementFlag.UPDATE_FONT)

        super()._apply_update() # Actually apply the update

    def _personal_init_inherit(self):
        self._set_tk_target_variable(default_key="text")

    def init_window_creation_done(self):
        super().init_window_creation_done()
        self._value_change_callback = self.window.get_event_function(self, key= self.key, key_function= self._key_function)
        self._tk_target_value.trace_add("write", self._event_callback)

    def set_value(self, val:str) -> Self:
        self._prev_value = val  # Avoid event trigger
        super().set_value(val)
        return self

    _prev_value: str = None
    def _event_callback(self, *_):
        value = self.value
        if self._prev_value == value:
            return

        self._prev_value = value
        if self._default_event:
            self._value_change_callback()

