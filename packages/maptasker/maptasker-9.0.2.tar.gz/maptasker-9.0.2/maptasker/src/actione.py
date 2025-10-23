"""Evaluate Task actions."""

#! /usr/bin/env python3

# ####################################################################################
#                                                                                    #
#  actione: action evaluation                                                        #
#           given the xml <code>nn</code>, figure out what (action) code it is and   #
#               return the translation                                               #
#                                                                                    #
#          code_child: used to parse the specific <code> xml for action details.     #
#          code_action: the nnn in <code>nnn</code> xml                              #
#          action_type: true if Task action, False if not (e.g. a Profile state      #
#                       or event condition)                                          #
#                                                                                    #
# ####################################################################################
import contextlib
import re

import defusedxml.ElementTree  # Need for type hints

import maptasker.src.actionr as action_results
from maptasker.src.action import get_extra_stuff
from maptasker.src.actionc import ActionCode, action_codes
from maptasker.src.config import CONTINUE_LIMIT
from maptasker.src.debug import not_in_dictionary
from maptasker.src.deprecate import depricated
from maptasker.src.format import format_html
from maptasker.src.primitem import PrimeItems
from maptasker.src.sysconst import pattern13

blank = "&nbsp;"


# See if this Task or Profile code is deprecated.
def check_for_deprecation(the_action_code_plus: str) -> None:
    """
    See if this Task or Profile code isa deprecated
        :param the_action_code_plus: the action code plus the type of action
            (e.g. "861t", "t" = Task, "e" = Event, "s" = State)
        :return: nothing
    """

    lookup = the_action_code_plus[:-1]  # Remove last character to get just the digits
    # if lookup in depricated and the_action_code_plus in action_codes:
    if lookup in depricated and lookup in PrimeItems.tasker_action_codes:
        return "<em> (Is Deprecated)</em> "

    return ""


# Given an action code, evaluate it for display.
def get_action_code(
    code_child: defusedxml.ElementTree,
    code_action: defusedxml.ElementTree,
    action_type: bool,
    code_type: str,
) -> str:
    """
    Given an action code, evaluate it for display
        :param code_child: xml element of the <code>
        :param code_action: xml; element of the <Action
        :param action_type: True if task, False otherwise
        :param code_type: 'e'=event, 's'=state, 't'=task
        :return: formatted output line with action details
    """

    # logger.debug(f"get action code:{code_child.text}{code_type}")
    just_the_code = code_child.text
    the_action_code_plus = just_the_code + code_type

    # See if this code is deprecated
    depricated = check_for_deprecation(the_action_code_plus)

    # We have a code that is not yet in the dictionary?
    if the_action_code_plus not in action_codes:
        the_result = f"Code {the_action_code_plus} not yet mapped{get_extra_stuff(code_action, action_type)}"
        not_in_dictionary(
            "Action/Condition",
            f"'display' for code {the_action_code_plus}",
        )

    else:
        # Format the output with HTML if this is a Task
        if action_type and len(just_the_code) <= 3:
            # The code is in our dictionary.  Add the display name
            the_result = format_html(
                "action_name_color",
                "",
                f"{action_codes[the_action_code_plus].name}{depricated}",
                True,
            )
            # numargs = len(PrimeItems.tasker_action_codes[just_the_code]["args"])

        # Not a Task.  Must be a condition.
        else:
            the_result = f"{action_codes[the_action_code_plus].name}{depricated}"

        # Get the actions results
        the_result = action_results.get_action_results(
            the_action_code_plus,
            action_codes,
            code_action,
            action_type,
        )

        # If this is a redirected lookup entry, create a temporary mirror
        # dictionary entry.
        # Then grab the 'display' key and fill in rest with directed-to keys
        with contextlib.suppress(KeyError):
            if action_codes[the_action_code_plus].redirect:
                # Get the referred-to dictionary item.
                referral = action_codes[the_action_code_plus].redirect

                # Create a temporary mirror dictionary entry using values of redirected code
                temp_lookup_codes = {}
                temp_lookup_codes[the_action_code_plus] = ActionCode(
                    "",
                    action_codes[referral].args,
                    action_codes[the_action_code_plus].name,
                    action_codes[referral].category,
                    action_codes[referral].canfail,
                )

                # Get the results from the (copy of the) referred-to dictionary entry
                the_result = action_results.get_action_results(
                    the_action_code_plus,
                    temp_lookup_codes,
                    code_action,
                    action_type,
                )

    return the_result


# Put the line '"Structure Output (JSON, etc)' back together.
def fix_json(line_to_fix: str, text_to_match: str) -> str:
    """
    Fix the JSON line by undoing the breakup at the comma for "Structure Output (JSON, etc)".

    Args:
        line_to_fix (str): The line to be fixed.
        texct_to_match (str): The text to match against.

    Returns:
        str: The fixed line.
    """
    # We have to undo the breakup at the comma for "Structure Output (JSON, etc)
    json_location = line_to_fix.find(f"{text_to_match} (JSON")
    if json_location != -1:
        etc_location = line_to_fix.find("etc", json_location)
        temp_line = f"{line_to_fix[:json_location]}{text_to_match} (JSON, {line_to_fix[etc_location:]}"
        line_to_fix = temp_line
    return line_to_fix


# Make the action line pretty by aligning the arguments.
def make_action_pretty(task_code_line: str, indent_amt: int) -> str:
    """
    Makes the given task code line prettier by adding line breaks and indentation.

    Args:
        task_code_line (str): The task code line to be made prettier.
        indent_amt (int): The amount of indentation to be added.

    Returns:
        str: The prettified task code line.
    """

    # Add our leading spaces (indent_amt) and extra spaces for the Task action name.
    temp_line = task_code_line.replace(
        blank,
        "",
    )  # Strip blanks from line to figure out Task action name length.
    close_bracket = temp_line.find(">")
    open_bracket = temp_line.find("<", close_bracket)
    extra_blanks = open_bracket - close_bracket + 5

    # Break at comma followed by a space.  But not if this is a 'Variable Set" or "For"
    if not ">Variable Set<" in task_code_line and not ">For<" in task_code_line:
        task_code_line = task_code_line.replace(
            ", ",
            f", <br>{indent_amt}{blank * extra_blanks}",
        )
        skip_all_commas = False
    else:
        # Variable Set:  Just split at the ', To=', ", Max Rounding Digits", and ", Structure Output"
        task_code_line = (
            task_code_line.replace(", To=", f", <br>{indent_amt}{blank * extra_blanks}To=")
            .replace(
                ", Max Rounding Digits",
                f", <br>{indent_amt}{blank * extra_blanks}Max Rounding Digits",
            )
            .replace(", Structure Output", f", <br>{indent_amt}{blank * extra_blanks}Structure Output")
        )
        # For: Just split at ', Item='
        task_code_line = task_code_line.replace(", Items=", f", <br>{indent_amt}{blank * extra_blanks}Items=")
        skip_all_commas = True
    # Break at newline and comma if not a config param.
    # NOTE: There may be one or more double '\n' strings, which is ok.
    # NOTE: Don't do this if this is a 'Variable Set' or 'For'
    if "Configuration Parameter(s):" not in task_code_line and not skip_all_commas:
        # Replace all commas followed by a non-blank with a break
        task_code_line = re.sub(
            pattern13,
            f"<br>{indent_amt}{blank * (extra_blanks + 7)}",
            task_code_line,
        )
        # Now handle newlines
        task_code_line = task_code_line.replace(
            "\n",
            f"<br>{indent_amt}{blank * (extra_blanks + 7)}",
        )  # 7 for "Values="

    # Break at bracket
    a_bit_more = 9 if "DISABLED" not in task_code_line else 0
    task_code_line = task_code_line.replace(
        "[",
        f"<br>{indent_amt}{blank * (extra_blanks + a_bit_more)}[",
    )
    # Break at (If condition
    task_code_line = task_code_line.replace(
        "(<em>IF",
        f"<br>{indent_amt}{blank * extra_blanks}(<em>IF",
    )
    # Break at label with filler
    task_code_line = task_code_line.replace(
        '<span class="action_label_color"> ...with label:',
        f'<br>{indent_amt}{blank * extra_blanks}<span class="action_label_color">...with label:',
    )

    # Correct "Structure Output (JSON, etc)", which got separated by the comma
    task_code_line = fix_json(task_code_line, "Structure Output")

    # Finally, rtemove the trailing comma since each argument is separated already
    task_code_line = task_code_line.replace(", <br>", "<br>")

    return task_code_line, extra_blanks


# Finalize the action line and append it to the list of actions.
def finalize_action_details(
    task_code_line: str,
    alist: list,
    indent: int,
    extra_blanks: int,
) -> list:
    """
    Finalize the action line and append it to the list of actions.

    Args:
        task_code_line (str): The action line to be finalized.
        alist (list): The list of actions.
        indent (int): The number of spaces to indent the output line.
        extra_blanks (int): Additional spaces to add to the output line.
        count (int): The count of continued lines.

    Returns:
        list: The updated list of actions.
    """

    # Append as-is if there's no newline and length exceeds 80, or if pretty output is enabled
    if (
        ("\n" not in task_code_line and len(task_code_line) > 80)
        or PrimeItems.program_arguments["pretty"]
        or "text-box" in task_code_line
    ):
        alist.append(task_code_line)
        return alist

    # Split into individual lines at line breaks
    array_of_lines = task_code_line.split("\n")

    for i, item in enumerate(array_of_lines[: CONTINUE_LIMIT + 1]):
        if i == 0:
            alist.append(item)
        else:
            alist.append(f"...indent={indent + extra_blanks}item={item}")

    # Add continuation limit message if necessary
    if len(array_of_lines) > CONTINUE_LIMIT:
        # Add comment that we have reached the limit for continued details.
        alist[-1] = f"{alist[-1]}</span>" + format_html(
            "Red",
            "",
            (
                f"<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;... continue limit of {CONTINUE_LIMIT!s} "
                'reached.  See "CONTINUE_LIMIT =" in config.py for '
                "details"
            ),
            True,
        )

    return alist


# Construct Task Action output line
def build_action(
    alist: list,
    task_code_line: str,
    code_element: defusedxml.ElementTree,
    indent: int,
    indent_amt: str,
) -> list:
    """
    Construct Task Action output line
        :param alist: list of actions (all <Actions> formatted for output
        :param task_code_line: output text of Task
        :param code_element: xml element of <code> under <Action>
        :param indent: the number of spaces to indent the output line
        :param indent_amt: the indent number of spaces as "&nbsp;" for each space
        :return: finalized output string
    """

    # Clean up the action line by removing any leading ermpty field
    task_code_line = task_code_line.replace(
        f"{blank * 2},",
        f"{blank * 2}",
    )  # Drop the leading comma if present.

    # Calculate total indentation to put in front of action
    count = indent

    if count != 0:
        # Add the indent amount to the front of the Action output line
        front_matter = '<span class="action_name_color">'
        task_code_line = task_code_line.replace(
            front_matter,
            f"{front_matter}{indent_amt}",
            1,
        )
        count = 0
    if count < 0:
        indent_amt += task_code_line
        task_code_line = indent_amt

    # Make the output align/pretty.  Don't make label html pretty if they have html.
    if PrimeItems.program_arguments["pretty"]:
        lbl_position = task_code_line.find("...with label:")
        temp = task_code_line.split("<div")
        just_the_action = temp[0]
        just_the_label = temp[1] if len(temp) > 1 else ""

        # If we have a label then make it pretty.
        if lbl_position == -1 or just_the_label:
            # If we have a label, then put it back together after separation.
            add_on = f"<div {just_the_label}" if just_the_label else ""
            task_code_line, extra_blanks = make_action_pretty(just_the_action, indent_amt)
            task_code_line = f"{task_code_line}{add_on}"
        else:
            extra_blanks = 0
    else:
        extra_blanks = 0

    # Flag Action if not yet known to us.  Tell user (and me) about it.
    if not task_code_line:  # If no Action details
        alist.append(
            format_html(
                "unknown_task_color",
                "",
                f"Action {code_element.text}: not yet mapped",
                True,
            ),
        )
        # Handle this situation in which we can't find the action code.
        not_in_dictionary("Action", code_element.text)

    # We have Task Action details
    else:
        alist = finalize_action_details(
            task_code_line,
            alist,
            indent,
            extra_blanks,
        )

    return alist
