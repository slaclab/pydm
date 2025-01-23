============
Contributing
============

Contributions are welcome, and are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/slaclab/pydm/issues.

If you are reporting a bug, please try to include:

* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug, including the earliest version you know has the issue.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "feature"
is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

PyDM could always use more documentation, whether
as part of the official docs, in docstrings,
or even on the web in blog posts, articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/slaclab/pydm/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `pydm` for local development.

1. Fork the `pydm` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_username_here/pydm.git

3. Install your local copy into a new conda environment. Assuming you have conda installed, this is how you set up your fork for local development::

    $ conda create -n pydm-environment python=3.8 pyqt=5.12.3 pip numpy scipy six psutil pyqtgraph -c conda-forge
    $ cd pydm/
    $ pip install -e .

4. Install additional packages only needed for development and building the docs::

    $ pip install -r dev-requirements.txt
    $ pip install -r docs-requirements.txt

5. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

6. Install and enable ``pre-commit`` for this repository::

    $ pip install pre-commit
    $ pre-commit install

7. Add new tests for any additional functionality or bugs you may have discovered.  And of course, be sure that all previous tests still pass by running::

    $ python run_tests.py

8. Add documentation for any new features and algorithms into the .rst files of the /docs directory. Create a local build of the docs by running::

    $ cd docs
    $ make html

8. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

9. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

When you submit a pull request, check that it meets these guidelines:

1. Try to keep pull requests small.
2. Make frequent but logical commits, and follow the commit-message guidelines below.
3. Fix any formatting/linting issues that pre-commit finds. (pre-commit should prevent you from committing if you don't)
4. New features and algorithms need documentation! Don't forget the .rst files in the /docs directory.
5. Most pull requests should include new tests.
6. Check the GitHub Actions status and make sure that the tests have passed for all supported platforms and Python versions.
7. Don't take requests to change your code personally!

Commit Message Guidelines
-------------------------

Commit messages should be clear and follow a few basic rules. Example:

.. code-block::

    ENH: add functionality X to pydm.<submodule>.

    The first line of the commit message starts with a capitalized acronym
    (options listed below) indicating what type of commit this is.  Then a blank
    line, then more text if needed.  Lines shouldn't be longer than 72
    characters.  If the commit is related to a ticket, indicate that with
    "See #3456", "See ticket 3456", "Closes #3456" or similar.

Describing the motivation for a change, the nature of a bug for bug fixes 
or some details on what an enhancement does are also good to include in a 
commit message. Messages should be understandable without looking at the code 
changes. 

Standard acronyms to start the commit message with are:


+------+------------------------------------------------------------+
| Code | Description                                                |
+======+============================================================+
| API  | An (incompatible) API change                               |
+------+------------------------------------------------------------+
| BLD  | Change related to building                                 |
+------+------------------------------------------------------------+
| BUG  | Bug fix                                                    |
+------+------------------------------------------------------------+
| DEP  | Deprecate something, or remove a deprecated object         |
+------+------------------------------------------------------------+
| DEV  | Development tool or utility                                |
+------+------------------------------------------------------------+
| DOC  | Documentation                                              |
+------+------------------------------------------------------------+
| ENH  | Enhancement                                                |
+------+------------------------------------------------------------+
| MNT  | Maintenance commit (refactoring, typos, etc.)              |
+------+------------------------------------------------------------+
| REV  | Revert an earlier commit                                   |
+------+------------------------------------------------------------+
| STY  | Style fix (whitespace, PEP8)                               |
+------+------------------------------------------------------------+
| TST  | Addition or modification of tests                          |
+------+------------------------------------------------------------+
| REL  | Related to releasing PyDM                                  |
+------+------------------------------------------------------------+
| WIP  | Commit that is a work in progress                          |
+------+------------------------------------------------------------+
