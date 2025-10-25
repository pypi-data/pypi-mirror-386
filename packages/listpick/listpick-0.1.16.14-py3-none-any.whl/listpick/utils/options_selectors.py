#!/bin/python
# -*- coding: utf-8 -*-
"""
options_selectors.py
Handle option specification.

Author: GrimAndGreedy
License: MIT
"""

import curses
from typing import Tuple
from listpick.ui.input_field import input_field
from listpick.utils.utils import dir_picker
import logging

logger = logging.getLogger('picker_log')

def default_option_input(stdscr: curses.window, refresh_screen_function=lambda : None, starting_value:str="", field_prefix:str=" Opts: ", registers={}) -> Tuple[bool, str]:

    logger.info("function: default_option_input (options_selectors.py)")
    # notification(stdscr, message=f"opt required for {index}")
    usrtxt = f"{starting_value} " if starting_value else ""
    h, w = stdscr.getmaxyx()
    # field_end = w-38 if show_footer else w-3
    field_end = w-3
    field_end_f = lambda: stdscr.getmaxyx()[1]-3
    usrtxt, return_val = input_field(
        stdscr,
        usrtxt=usrtxt,
        field_prefix=field_prefix,
        x=lambda:2,
        y=lambda: stdscr.getmaxyx()[0]-1,
        max_length=field_end_f,
        registers=registers,
        refresh_screen_function=refresh_screen_function,
        path_auto_complete=False,
        formula_auto_complete=False,
        function_auto_complete=False,
        word_auto_complete=False,
    )
    if return_val: return True, usrtxt
    else: return False, starting_value



def default_option_selector(stdscr: curses.window, refresh_screen_function=None, starting_value:str="", field_prefix:str=" Opts: ", registers={}) -> Tuple[bool, str]:
    """ 
    *** **** *** ** ** *
    NOT YET IMPLEMENTED!!
    *** **** *** ** ** *
    """
    logger.info("function: default_option_selector (options_selectors.py)")
    # notification(stdscr, message=f"opt required for {index}")
    usrtxt = f"{starting_value} " if starting_value else ""
    h, w = stdscr.getmaxyx()
    # field_end = w-38 if show_footer else w-3
    field_end = w-3
    field_end_f = lambda: stdscr.getmaxyx()[1]-3
    usrtxt, return_val = input_field(
        stdscr,
        usrtxt=usrtxt,
        field_prefix=field_prefix,
        x=lambda:2,
        y=lambda: stdscr.getmaxyx()[0]-1,
        max_length=field_end_f,
        registers=registers,
        refresh_screen_function=refresh_screen_function,
    )
    if return_val: return True, usrtxt
    else: return False, starting_value


def output_file_option_selector(stdscr:curses.window, refresh_screen_function, registers={}) -> Tuple[bool, str]:

    logger.info("function: output_file_option_selector (options_selectors.py)")
    s = dir_picker()

    stdscr.clear()
    stdscr.refresh()
    refresh_screen_function()
    usrtxt = f"{s}/"
    h, w = stdscr.getmaxyx()
    # field_end = w-38 if show_footer else w-3
    field_end_f = lambda: stdscr.getmaxyx()[1]-3
    usrtxt, return_val = input_field(
        stdscr,
        usrtxt=usrtxt,
        field_prefix=" Save as: ",
        x=lambda:2,
        y=lambda: stdscr.getmaxyx()[0]-1,
        max_length=field_end_f,
        registers=registers,
    )
    if return_val: return True, usrtxt
    else: return False, ""
