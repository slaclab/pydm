=============================
Customizing the Look and Feel
=============================

Instead of rolling out hardcoded styles or reinvent the wheel, PyDM leverages
the existing Qt Style Sheet mechanism.

Qt Style Sheet terminology and syntactic rules are almost identical to those of
HTML CSS. More on the rules, selectors and syntax can be found at this
`link <https://doc.qt.io/Qt-5/stylesheet-syntax.html>`_.

By default PyDM ships with a `default stylesheet file <https://github.com/slaclab/pydm/blob/master/pydm/default_stylesheet.qss>`_
that is used unless an user specify a file to be used either via the PyDM
launcher argument `–-stylesheet STYLESHEET` or via the `PYDM_STYLESHEET`
environment variable.

To help users extend this feature, PyDM offers two main configurations that can
be used:

- **PYDM_STYLESHEET**
  Path to the QSS files defining the global stylesheets for the PyDM
  application. When used, it will override the default look. If using multiple
  files they must be separated by the path separator.
  For example: ``/path_to/my_style_1.qss:/path_to/other/my_other_style.qss``
- **PYDM_STYLESHEET_INCLUDE_DEFAULT**
  Whether or not to include the PyDM Default stylesheet along with customized
  files. Note that the PyDM default stylesheet will have lower precedence
  compared to files specified at ``PYDM_STYLESHEET``.

Specifying Style Sheets in Displays
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you would like to use a custom style sheet in your PyDM display, you have a
few different options:

1. Put QSS code directly into your Display's `styleSheet` property.  This is mostly
   useful if you only need a small amount of QSS, and you only expect to use it once.
   The `styleSheet` property can be set in Qt Designer, or with Python code.
2. Put a path to a QSS file in the Display's `styleSheet` property.  This is useful
   if you want to reuse the same QSS file for many files, but don't want the custom style
   to apply to *all* displays, just some subset.
3. Set the `PYDM_STYLESHEET` environment variable to a path to a QSS file.  This will
   apply to all displays you load.
4. Set the `--stylesheet` argument when launching PyDM.  This will apply to all displays
   you load from this instance of PyDM.  It takes precedence over the `PYDM_STYLESHEET`
   property.

A combination of 1/2 and 3/4 are also possible - the styles from 3/4 are applied
first, then the styles from 1/2 are applied.  This gives you the ability to override pieces
of the global style with the `styleSheet` property.

Processing Order of Style Sheets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The file will be processed from top to bottom and the bottom-most rules will
take precedence over rules defined at the top in case of repeated/conflicts.

Rules defined at widgets will always take precedence over general rules defined
at higher levels.

Important Notes
^^^^^^^^^^^^^^^

When writing your own style sheet rules please be always mindful about your
selectors since, as with HTML CSS, the style rules will cascade to child widgets.
