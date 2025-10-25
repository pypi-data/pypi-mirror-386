#!/bin/python
# -*- coding: utf-8 -*-
"""
picker_colours.py
Define colour options for listpick--default, help, and notification colours.

Author: GrimAndGreedy
License: MIT
"""

import curses
from typing import Dict
import logging

logger = logging.getLogger('picker_log')


def get_colours(pick:int=0) -> Dict[str, int]:
    """ Define colour options for listpick. """
    logger.info("function get_colours (picker_colours.py)")
    colours = [
        ### (0) Green header, green title, green modes, purple selected, blue cursor
    {
        'background': 232,
        'normal_fg': 255,
        'unselected_bg': 232,
        'unselected_fg': 255,
        'cursor_bg': 21,
        'cursor_fg': 255,
        'selected_bg': 54,
        'selected_fg': 255,
        'header_bg': 255,
        'header_fg': 232,
        'error_bg': 232,
        'error_fg': curses.COLOR_RED,
        'complete_bg': 232,
        'complete_fg': 82,
        'waiting_bg': 232,
        'waiting_fg': curses.COLOR_YELLOW,
        'active_bg': 232,
        'active_fg': 33,
        'paused_bg': 232,
        'paused_fg': 244,
        'search_bg': 162,
        'search_fg': 255,
        'active_input_bg': 255,
        'active_input_fg': 28,
        'modes_selected_bg': 28,
        'modes_selected_fg': 255,
        'modes_unselected_bg': 255,
        'modes_unselected_fg': 232,
        'title_bar': 28,
        'title_bg': 28,
        'title_fg': 255,
        'scroll_bar_bg': 247,
        'selected_header_column_bg': 232,
        'selected_header_column_fg': 255,
        'unselected_header_column_bg': 255,
        'unselected_header_column_fg': 232,
        'footer_bg': 28,
        'footer_fg': 255,
        'refreshing_bg': 28,
        'refreshing_fg': 255,
        'refreshing_inactive_bg': 28,
        'refreshing_inactive_fg': 232,
        '40pc_bg': 232,
        '40pc_fg': 166,
        'footer_string_bg': 28,
        'footer_string_fg': 255,
        'selected_cell_bg': 54,
        'selected_cell_fg': 255,
        'deselecting_cell_bg': 162,
        'deselecting_cell_fg': 255,
        'active_column_bg': 234,
        'active_column_fg': 255,
    },
        ### (1) Black and white
    {
        'background': 232,
        'normal_fg': 255,
        'unselected_bg': 232,
        'unselected_fg': 255,
        'cursor_bg': 255,
        'cursor_fg': 232,
        'selected_bg': 255,
        'selected_fg': 232,
        'header_bg': 255,
        'header_fg': 232,
        'error_bg': 232,
        'error_fg': 255,
        'complete_bg': 232,
        'complete_fg': 255,
        'waiting_bg': 232,
        'waiting_fg': 255,
        'active_bg': 232,
        'active_fg': 255,
        'paused_bg': 232,
        'paused_fg': 255,
        'search_bg': 255,
        'search_fg': 232,
        'active_input_bg': 232,
        'active_input_fg': 255,
        'modes_selected_bg': 255,
        'modes_selected_fg': 232,
        'modes_unselected_bg': 232,
        'modes_unselected_fg': 255,
        'title_bar': 232,
        'title_bg': 255,
        'title_fg': 232,
        'scroll_bar_bg': 255,
        'selected_header_column_bg': 232,
        'selected_header_column_fg': 255,
        'unselected_header_column_bg': 255,
        'unselected_header_column_fg': 232,
        'footer_bg': 255,
        'footer_fg': 232,
        'refreshing_bg': 255,
        'refreshing_fg': 232,
        'refreshing_inactive_bg': 232,
        'refreshing_inactive_fg': 255,
        '40pc_bg': 232,
        '40pc_fg': 255,
        'footer_string_bg': 255,
        'footer_string_fg': 232,
        'selected_cell_bg': 237,
        'selected_cell_fg': 255,
        'deselecting_cell_bg': 162,
        'deselecting_cell_fg': 255,
        'active_column_bg': 234,
        'active_column_fg': 255,
    },
        ### (2) Blue header, blue title, blue modes, purple selected, green cursor
    {
        'background': 232,
        'normal_fg': 255,
        'unselected_bg': 232,
        'unselected_fg': 255,
        'cursor_bg': 28,
        'cursor_fg': 255,
        'selected_bg': 135,
        'selected_fg': 255,
        'header_bg': 255,
        'header_fg': 232,
        'error_bg': 232,
        'error_fg': curses.COLOR_RED,
        'complete_bg': 232,
        'complete_fg': 82,
        'waiting_bg': 232,
        'waiting_fg': curses.COLOR_YELLOW,
        'active_bg': 232,
        'active_fg': 33,
        'paused_bg': 232,
        'paused_fg': 244,
        'search_bg': 162,
        'search_fg': 255,
        'active_input_bg': 255,
        'active_input_fg': 25,
        'modes_selected_bg': 25,
        'modes_selected_fg': 255,
        'modes_unselected_bg': 255,
        'modes_unselected_fg': 232,
        'title_bar': 25,
        'title_bg': 25,
        'title_fg': 255,
        'scroll_bar_bg': 247,
        'selected_header_column_bg': 232,
        'selected_header_column_fg': 255,
        'unselected_header_column_bg': 255,
        'unselected_header_column_fg': 232,
        'footer_bg': 25,
        'footer_fg': 255,
        'refreshing_bg': 25,
        'refreshing_fg': 255,
        'refreshing_inactive_bg': 25,
        'refreshing_inactive_fg': 232,
        '40pc_bg': 232,
        '40pc_fg': 166,
        'footer_string_bg': 25,
        'footer_string_fg': 255,
        'selected_cell_bg': 237,
        'selected_cell_fg': 255,
        'deselecting_cell_bg': 162,
        'deselecting_cell_fg': 255,
        'active_column_bg': 234,
        'active_column_fg': 255,
    },
        ### (3) Purple header, purple title, white modes, green selected, blue cursor
    {
        'background': 232,
        'normal_fg': 255,
        'unselected_bg': 232,
        'unselected_fg': 255,
        'cursor_bg': 54,
        'cursor_fg': 255,
        'selected_bg': 135,
        'selected_fg': 255,
        'header_bg': 255,
        'header_fg': 232,
        'error_bg': 232,
        'error_fg': curses.COLOR_RED,
        'complete_bg': 232,
        'complete_fg': 82,
        'waiting_bg': 232,
        'waiting_fg': curses.COLOR_YELLOW,
        'active_bg': 232,
        'active_fg': 33,
        'paused_bg': 232,
        'paused_fg': 244,
        'search_bg': 162,
        'search_fg': 255,
        'active_input_bg': 255,
        'active_input_fg': 57,
        'modes_selected_bg': 57,
        'modes_selected_fg': 255,
        'modes_unselected_bg': 255,
        'modes_unselected_fg': 232,
        'title_bar': 57,
        'title_bg': 57,
        'title_fg': 255,
        'scroll_bar_bg': 247,
        'selected_header_column_bg': 232,
        'selected_header_column_fg': 255,
        'unselected_header_column_bg': 255,
        'unselected_header_column_fg': 232,
        'footer_bg': 57,
        'footer_fg': 255,
        'refreshing_bg': 57,
        'refreshing_fg': 255,
        'refreshing_inactive_bg': 57,
        'refreshing_inactive_fg': 232,
        '40pc_bg': 232,
        '40pc_fg': 166,
        'footer_string_bg': 57,
        'footer_string_fg': 255,
        'selected_cell_bg': 135,
        'selected_cell_fg': 232,
        'deselecting_cell_bg': 162,
        'deselecting_cell_fg': 255,
        'active_column_bg': 234,
        'active_column_fg': 255,
    },
        ## (4) 3-bit colours
    {
        'background': curses.COLOR_BLACK,
        'normal_fg': curses.COLOR_WHITE,
        'unselected_bg': curses.COLOR_BLACK,
        'unselected_fg': curses.COLOR_WHITE,
        'cursor_bg': curses.COLOR_BLUE,
        'cursor_fg': curses.COLOR_BLACK,
        'selected_bg': curses.COLOR_MAGENTA,
        'selected_fg': curses.COLOR_BLACK,
        'header_bg': curses.COLOR_WHITE,
        'header_fg': curses.COLOR_BLACK,
        'error_bg': curses.COLOR_BLACK,
        'error_fg': curses.COLOR_RED,
        'complete_bg': curses.COLOR_BLACK,
        'complete_fg': curses.COLOR_GREEN,
        'waiting_bg': curses.COLOR_BLACK,
        'waiting_fg': curses.COLOR_YELLOW,
        'active_bg': curses.COLOR_BLACK,
        'active_fg': curses.COLOR_BLUE,
        'paused_bg': curses.COLOR_BLACK,
        'paused_fg': curses.COLOR_WHITE,
        'search_bg': curses.COLOR_WHITE,
        'search_fg': curses.COLOR_MAGENTA,
        'active_input_bg': curses.COLOR_BLACK,
        'active_input_fg': curses.COLOR_WHITE,
        'modes_selected_bg': curses.COLOR_GREEN,
        'modes_selected_fg': curses.COLOR_BLACK,
        'modes_unselected_bg': curses.COLOR_WHITE,
        'modes_unselected_fg': curses.COLOR_BLACK,
        'title_bar': curses.COLOR_BLACK,
        'title_bg': curses.COLOR_GREEN,
        'title_fg': curses.COLOR_BLACK,
        'scroll_bar_bg': curses.COLOR_WHITE,
        'selected_header_column_bg': curses.COLOR_BLACK,
        'selected_header_column_fg': curses.COLOR_WHITE,
        'unselected_header_column_bg': curses.COLOR_WHITE,
        'unselected_header_column_fg': curses.COLOR_BLACK,
        'footer_bg': curses.COLOR_GREEN,
        'footer_fg': curses.COLOR_BLACK,
        'refreshing_bg': curses.COLOR_GREEN,
        'refreshing_fg': curses.COLOR_BLACK,
        'refreshing_inactive_bg': curses.COLOR_GREEN,
        'refreshing_inactive_fg': curses.COLOR_WHITE,
        '40pc_bg': curses.COLOR_BLACK,
        '40pc_fg': curses.COLOR_YELLOW,
        'footer_string_bg': curses.COLOR_GREEN,
        'footer_string_fg': curses.COLOR_BLACK,
        'selected_cell_bg': 237,
        'selected_cell_fg': 255,
        'deselecting_cell_bg': curses.COLOR_MAGENTA,
        'deselecting_cell_fg': curses.COLOR_WHITE,
        'active_column_bg': curses.COLOR_BLACK,
        'active_column_fg': curses.COLOR_WHITE,
    },
        ### (6) Use default colors for bg
    # {
    #     'background': -1,
    #     'normal_fg': -1,
    #     'unselected_bg': -1,
    #     'unselected_fg': -1,
    #     'cursor_bg': 21,
    #     'cursor_fg': -1,
    #     'selected_bg': 54,
    #     'selected_fg': -1,
    #     'header_bg': 255,
    #     'header_fg': 232,
    #     'error_bg': 232,
    #     'error_fg': curses.COLOR_RED,
    #     'complete_bg': 232,
    #     'complete_fg': 82,
    #     'waiting_bg': 232,
    #     'waiting_fg': curses.COLOR_YELLOW,
    #     'active_bg': 232,
    #     'active_fg': 33,
    #     'paused_bg': -1,
    #     'paused_fg': 244,
    #     'search_bg': 162,
    #     'search_fg': -1,
    #     'active_input_bg': -1,
    #     'active_input_fg': 232,
    #     'modes_selected_bg': 232,
    #     'modes_selected_fg': -1,
    #     'modes_unselected_bg': 255,
    #     'modes_unselected_fg': 232,
    #     'title_bar': 232,
    #     'title_bg': 232,
    #     'title_fg': -1,
    #     'scroll_bar_bg': 247,
    #     'selected_header_column_bg': 232,
    #     'selected_header_column_fg': -1,
    #     'unselected_header_column_bg': -1,
    #     'unselected_header_column_fg': -1,
    #     'footer_bg': 232,
    #     'footer_fg': -1,
    #     'refreshing_bg': 232,
    #     'refreshing_fg': -1,
    #     'refreshing_inactive_bg': 232,
    #     'refreshing_inactive_fg': 232,
    #     '40pc_bg': 232,
    #     '40pc_fg': 166,
    #     'footer_string_bg': 232,
    #     'footer_string_fg': -1,
    #     'selected_cell_bg': 54,
    #     'selected_cell_fg': -1,
    #     'deselecting_cell_bg': 162,
    #     'deselecting_cell_fg': -1,
    #     'active_column_bg': 234,
    #     'active_column_fg': -1,
    # },
    ]
    for colour in colours:
        colour["20pc_bg"] = colour["background"]
        colour["40pc_bg"] = colour["background"]
        colour["60pc_bg"] = colour["background"]
        colour["80pc_bg"] = colour["background"]
        colour["100pc_bg"] = colour["background"]
        colour["error_bg"] = colour["background"]
        colour["complete_bg"] = colour["background"]
        colour["waiting_bg"] = colour["background"]
        colour["active_bg"] = colour["background"]
        colour["paused_bg"] = colour["background"]
        colour["paused_bg"] = colour["background"]
        # colour["search_bg"] = colour["background"]
    if pick > len(colours) - 1:
        return colours[0]
    return colours[pick]

def get_help_colours(pick: int=0) -> Dict[str, int]:
    """ Define help colour options for listpick. """
    logger.info("function get_help_colours (picker_colours.py)")
    colours = get_colours(pick)
    # colours = [get_colours(i) for i in range(get_theme_count())]
    # for i in range(len(colours)):

    # 3-bit colours
    colours_3_bit = [4]
    if pick in colours_3_bit:
        colours['cursor_bg'] = curses.COLOR_WHITE
        colours['cursor_fg'] = curses.COLOR_BLACK
        colours['selected_bg'] = curses.COLOR_WHITE
        colours['selected_fg'] = curses.COLOR_BLACK
    else:
        colours['cursor_bg'] = 235
        colours['cursor_fg'] = 255
        colours['selected_bg'] = 25
        colours['selected_fg'] = 255

    return colours


def get_notification_colours(pick:int=0) -> Dict[str, int]:
    """ Define notification colour options for listpick. """
    logger.info("function get_notification_colours (picker_colours.py)")
    colours = get_colours(pick)

    # Black and white
    if pick == 1:
        colours['background'] = 237
        colours['unselected_bg'] = 237
        colours['cursor_bg'] = 237
        colours['cursor_fg'] = 255
        colours['selected_bg'] = 237
        colours['selected_fg'] = 255

    # 3-bit colours
    elif pick == 4:
        colours['background'] = curses.COLOR_BLACK
        colours['unselected_bg'] = curses.COLOR_BLACK
        colours['cursor_bg'] = curses.COLOR_WHITE
        colours['cursor_fg'] = curses.COLOR_BLACK
        colours['selected_bg'] = curses.COLOR_WHITE
        colours['selected_fg'] = curses.COLOR_BLACK
    else:
        colours['background'] = 237
        colours['unselected_bg'] = 237
        colours['cursor_bg'] = 238
        colours['cursor_fg'] = 255
        colours['selected_bg'] = 237

    colours['selected_header_column_fg'] = colours['header_fg']
    colours['selected_header_column_bg'] = colours['header_bg']
    colours['unselected_header_column_fg'] = colours['header_fg']
    colours['unselected_header_column_bg'] = colours['header_bg']

    return colours

def get_fallback_colours() -> Dict[str, int]:
    logger.info("function get_fallback_colours (picker_colours.py)")
    return get_colours(4)

def get_theme_count() -> int:
    """ Get the number of themes. """
    logger.info("function get_theme_count (picker_colours.py)")
    col_list = []
    i = 0
    for i in range(100):
        x = get_colours(i)
        if x in col_list:
            break
        col_list.append(x)
    return i

def check_for_missing_keys():
    """ Check if any of the colour_dicts have missing keys--i.e., if their keys are incongruous. """
    ref = 0
    count = get_theme_count()

    colours = [get_colours(i) for i in range(count)]

    diffs = []
    for i in range(count):
        print(f"{i}")
        for j in range(count):
            diff = set(colours[i].keys()) - set(colours[j].keys())
            print(f"    colours[{i}] - colours[{j}] = {diff}")
            if diff:
                diffs.append(f"    colours[{i}] - colours[{j}] = {diff}")

    if diffs:
        print("*"*80)
        print("*"*80)
        for d in diffs:
            print(d)

