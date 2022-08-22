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
