# Utility to generate a stylesheet with all the combinations for alarms


import os.path
import argparse
import json
import itertools


# Stylesheet for widgets which don't react to alarm status
NO_ALARM = 0x0

# Stylesheet for the 'content' of widgets (text, usually)
ALARM_CONTENT = 0x1

# Stylesheet for the border of widgets.
ALARM_BORDER = 0x2

# Stylesheet for 'indicator' ornaments, where you want the "OK" status to actually have a color
ALARM_INDICATOR = 0x4

# Alarm Serverities. Default set to widgets is ALARM_DISCONNECTED
ALARM_NONE = 0
ALARM_MINOR = 1
ALARM_MAJOR = 2
ALARM_INVALID = 3
ALARM_DISCONNECTED = 4

# Alarm Color Definitions
GREEN_ALARM = "#00EB00"
YELLOW_ALARM = "#EBEB00"
RED_ALARM = "#EB0000"
MAGENTA_ALARM = "#EB00EB"
WHITE_ALARM = "#EBEBEB"

# We put all this in a big dictionary to try to avoid constantly
# allocating and deallocating new stylesheet strings.
alarm_style_sheet_map = {
    NO_ALARM: {
        ALARM_NONE: {},
        ALARM_MINOR: {},
        ALARM_MAJOR: {},
        ALARM_INVALID: {},
        ALARM_DISCONNECTED: {}
    },
    ALARM_INDICATOR: { # Not being used at this time
        ALARM_NONE: {"color": GREEN_ALARM},
        ALARM_MINOR: {"color": YELLOW_ALARM},
        ALARM_MAJOR: {"color": RED_ALARM},
        ALARM_INVALID: {"color": MAGENTA_ALARM},
        ALARM_DISCONNECTED: {"color": WHITE_ALARM}
    },
    ALARM_CONTENT: {
        ALARM_NONE: {"color": "black"},
        ALARM_MINOR: {"color": YELLOW_ALARM},
        ALARM_MAJOR: {"color": RED_ALARM},
        ALARM_INVALID: {"color": MAGENTA_ALARM},
        ALARM_DISCONNECTED: {"color": WHITE_ALARM}
    },
    ALARM_BORDER: {
        ALARM_NONE: {"border": "2px solid transparent"},
        ALARM_MINOR: {"border": "2px solid " + YELLOW_ALARM},
        ALARM_MAJOR: {"border": "2px solid " + RED_ALARM},
        ALARM_INVALID: {"border": "2px solid " + MAGENTA_ALARM},
        ALARM_DISCONNECTED: {"border": "2px solid " + WHITE_ALARM}
    },
    ALARM_CONTENT | ALARM_BORDER: {
        ALARM_NONE: {"color": "black", "border": "2px solid transparent"},
        ALARM_MINOR: {"color": YELLOW_ALARM, "border": "2px solid " + YELLOW_ALARM},
        ALARM_MAJOR: {"color": RED_ALARM, "border": "2px solid " + RED_ALARM},
        ALARM_INVALID: {"color": MAGENTA_ALARM, "border": "2px solid " + MAGENTA_ALARM},
        ALARM_DISCONNECTED: {"color": WHITE_ALARM, "border": "2px solid " + WHITE_ALARM}
    }
}


def produce_alarm_stylesheet(stylesheet_name, widget_type_names):
    """
    Write the alarm styles into a file.

    Parameters
    ----------
    stylesheet_name : str
        The absolute path where to save the output alarm stylesheet.
    widget_type_names : list
        A list of strings that are the widget names to write the alarm styles for
    """
    with open(stylesheet_name, 'w') as alarm_stylesheet:
        for widget_type_name in widget_type_names:
            alarm_severity = ALARM_NONE
            while alarm_severity <= ALARM_DISCONNECTED:
                table = list(itertools.product([False, True], repeat=2))
                for row in table:
                    is_border_alarm_sensitive = row[0]
                    is_content_alarm_sensitive = row[1]
                    _write_alarm_style(alarm_stylesheet, widget_type_name, is_border_alarm_sensitive,
                                       is_content_alarm_sensitive, alarm_severity)
                alarm_severity += 1
        alarm_stylesheet.close()



def _write_alarm_style(stylesheet_file, widget_type_name, is_border_alarm_sensitive,
                       is_content_alarm_sensitive, alarm_severity):
    """
    Write to the output stylesheet the styles for an alarm type, with alternating border, content, and border and
    content alarm sensitivities.

    Parameters
    ----------
    stylesheet_file : file descriptor
        The file descriptor to the output stylesheet file
    widget_type_name : str
        The widget name to write the styles for
    is_border_alarm_sensitive : bool
        True if the widget's border style can change according to the alarm severity; False if not
    is_content_alarm_sensitive : bool
        True if the widget's border content can change according to the alarm severity; False if not
    alarm_severity : int
        The severity of the alarm, i.e. ALARM_NONE, ALARM_MINOR, ALARM_MAJOR, ALARM_INVALID, and ALARM_DISCONNECTED
    """
    style = alarm_style_sheet_map[NO_ALARM][alarm_severity]
    style_contents = ''.join([widget_type_name, '[alarmSeverity="', str(alarm_severity), '"]'])

    if is_border_alarm_sensitive and is_content_alarm_sensitive:
        style_contents = ''.join([style_contents, '[alarmSensitiveBorder="true"]',
                                  '[alarmSensitiveContent="true"]'])
        style = alarm_style_sheet_map[ALARM_CONTENT | ALARM_BORDER][alarm_severity]
    elif is_border_alarm_sensitive:
        style_contents = ''.join([style_contents, '[alarmSensitiveBorder="true"]'])
        style = alarm_style_sheet_map[ALARM_BORDER][alarm_severity]
    elif is_content_alarm_sensitive:
        style_contents = ''.join([style_contents, '[alarmSensitiveContent="true"]'])
        style = alarm_style_sheet_map[ALARM_CONTENT][alarm_severity]

    style = json.dumps(style)
    # For a stylesheet, we want to separate settings by semicolons, not commas (as in JSON)
    style = style.replace(',', ';')
    style = style.replace('"', '')

    if style:
        style_contents = ''.join([style_contents, style.strip(), "\n"])
    else:
        style_contents = ''.join([style_contents, " {}\n"])
    stylesheet_file.write(style_contents)


def main():
    parser = argparse.ArgumentParser(description="Python Display Manager (PyDM) Stylesheet Generator")
    parser.add_argument(
        'stylesheet_output_location',
        help='The location to save the output stylesheet',
        nargs='?',
        default=None
    )

    pydm_args = parser.parse_args()
    stylesheet_location = os.path.abspath(pydm_args.stylesheet_output_location)

    produce_alarm_stylesheet(os.path.abspath(stylesheet_location),
                              ["PyDMWidget", "PyDMWritableWidget","PyDMLabel", "PyDMLineEdit", "PyDMSlider",
                               "PyDMCheckbox"])


if __name__ == "__main__":
    main()