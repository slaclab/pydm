======================
Development Guidelines
======================
It is recommended that PyDM is updated and maintained in the
following way. This workflow was not invented here at SLAC, 
there are many helpful tutorials online like `this
<https://guides.github.com/introduction/flow>`_ if you want more information.

Creating a Local Checkout
=========================
If you want to make changes to a repository the first step is to create your
own fork. This allows you to create feature branches without cluttering the
main repository. It also assures that the main repository is only added to by
Pull Request and review. Repositories can be forked from the GitHub site like
presented at `this example <https://help.github.com/articles/fork-a-repo>`_. 
Once this repository is created, you can clone into your own workspace.

.. code:: sh

   $ git clone https://YOUR-USERNAME@github.com/YOUR-USERNAME/REPOSITORY.git

Now, that we have a copy of the repository create a branch for the feature or
bug you would like to work on.

.. code:: sh

   $ git checkout -b my-feature

   $ git status
   On branch my-feature
   nothing to commit, working tree clean

Commit Guidelines
=================
Now you are ready to start working! Make changes to files and commit them to
your new branch. We like to preface our commit messages with a descriptor code.
This makes it easier for someone reviewing your commit history to see what you
have done.  These are borrowed from the `NumPy
<https://docs.scipy.org/doc/numpy/dev/gitwash/development_workflow.html#writing-the-commit-message>`_
development documentation.

====  ===
Code  Description
====  ===
API   an (incompatible) API change
BLD   change related to building
BUG   bug fix
DEP   deprecate something, or remove a deprecated object
DEV   development tool or utility
DOC   documentation
ENH   enhancement
MNT   maintenance commit (refactoring, typos, etc.)
REV   revert an earlier commit
STY   style fix (whitespace, PEP8)
TST   addition or modification of tests
REL   related to releasing numpy
WIP   Commit that is a work in progress
====  ===

It is also helpful underneath classes and functions to write docstrings. These
are later converted by Sphinx into HTML documentation. They also are a valuable
tool for exploration of a codebase within an IPython terminal. Docstrings
should follow the form described in the `NumPy documentation
<http://www.sphinx-doc.org/en/stable/ext/example_numpy.html>`_

Merging Changes
===============
Once you are happy with your code, ``push`` it back to your fork on GitHub.

.. code:: sh
   
   $ git push origin my-feature

You should now be able to create a Pull Request back to the original
repository. **You should never commit directly back to the original
repository**. In fact, if you are creating a new repository it is possible to
strictly disallow this by explicitly protecting certain branches from direct
commits.The reason we feel strongly that Pull Requests are necessary because
they:

1) Allows other collaborators to view the changes you made, and give feedback.
2) Leave an easily understood explanation to why these changes are necessary.

Once these changes are deemed acceptable to enter the main repository, they
Pull Request can be merged.

Syncing your Local Checkout
===========================
Inevitably, changes to the upstream repository will occur and you will need to
update your local checkout to reflect those. The first step is to make your
local checkout aware of the upstream repository. If this is done correctly, you
should see something like this:

.. code:: sh

   $ git remote add upstream https://github.com/UPSTREAM-ORG/REPOSITORY.git
   $ git remote -v
   origin   https://github.com/YOUR-USERNAME/REPOSITORY.git (fetch)
   origin   https://github.com/YOUR-USERNAME/REPOSITORY.git (push)
   upstream https://github.com/UPSTREAM-ORG/REPOSITORY.git (fetch)
   upstream https://github.com/UPSTREAM-ORG/REPOSITORY.git (push)

Now, we need to fetch any changes from the upstream repository. ``git fetch``
will grab the latest commits that were merged since we made our own fork

.. code:: sh

   $ git fetch upstream


Ideally you haven't made any changes to your ``master`` branch. So you should be
able to merge the latest ``master`` branch from the upstream repository without
concern. All you need to do is to switch to your ``master`` branch, and pull in
the changes from the upstream remote. It is usually a good idea to push any
changes back to your fork as well.

.. code:: sh

   $ git checkout master
   $ git pull upstream master
   $ git push origin master

Finally, we need to update our feature-branch to have the new changes. Here we
use a ``git rebase`` to take our local changes, remove them temporarily, pull
the upstream changes into our branch, and then re-add our local changes on the
tip of the commit history. This avoids extraneous merge commits that clog the
commit history of the branch. A more in-depth discussion can be found `here
<https://www.atlassian.com/git/tutorials/merging-vs-rebasing>`_. This process
should look like this:

.. code:: sh

   $ git checkout my-feature
   $ git rebase upstream/master

.. note::

   This process should not be done if you think that anyone else is also
   working on that branch. The rebasing process re-writes the commit history so
   any other checkout of the same branch referring to the old history will
   create duplicates of all the commits.
