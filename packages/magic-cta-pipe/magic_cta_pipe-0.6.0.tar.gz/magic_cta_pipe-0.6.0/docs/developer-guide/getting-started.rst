.. _getting_started_dev:

Getting Started For Developers
==============================

.. warning::

   The following guide is used only if you want to *develop* the
   ``magic-cta-pipe`` package, if you just want to write code that uses it
   as a dependency, you can install ``magic-cta-pipe`` from PyPI.
   See :ref:`getting_started_users`


Forking vs. Working in the Main Repository
------------------------------------------
If you are a member of CTA (Consortium or Observatory), or
otherwise a regular contributor to magic-cta-pipe, the maintainers can give you
access to the main repository at ``cta-observatory/magic-cta-pipe``.
Please contact Alessio Berti (alessioberti90@gmail.com) to get write access to the repository.
Working directly in the main repository has two main advantages
over using a personal fork:

- No need for synchronisation between the fork and the main repository
- Easier collaboration on the same branch with other developers

If you are an external contributor and don't plan to contribute regularly,
you need to go for the fork solution.

The instructions below have versions for both approaches, select the tab that applies to your
setup.


Cloning the repository
----------------------

The examples below use ssh, assuming you setup an ssh key to access GitHub.
See `the GitHub documentation <https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account>`_ if you haven't done so already.

.. tab-set::

   .. tab-item:: Working in the main repository
      :sync: main

      Clone the repository:

      .. code-block:: console

          $ git clone git@github.com:cta-observatory/magic-cta-pipe.git
          $ cd magic-cta-pipe


   .. tab-item:: Working a fork
      :sync: fork

      In order to checkout the software so that you can push changes to GitHub without
      having write access to the main repository at ``cta-observatory/magic-cta-pipe``, you
      `need to fork <https://help.github.com/articles/fork-a-repo/>`_ it.

      After that, clone your fork of the repository and add the main reposiory as a second
      remote called ``upstream``, so that you can keep your fork synchronized with the main repository.

      .. code-block:: console

          $ git clone https://github.com/[YOUR-GITHUB-USERNAME]/magic-cta-pipe.git
          $ cd magic-cta-pipe
          $ git remote add upstream https://github.com/cta-observatory/magic-cta-pipe.git



Setting up the development environment
--------------------------------------

We provide a ``conda`` environment with all packages needed for development of ``magic-cta-pipe`` and a couple of additonal helpful pacakages (like ipython, jupyter and vitables):

.. code-block:: console

    $ conda env create -f environment.yml

This will install a ``conda`` environment called ``magic-lst``. Next, switch to this new virtual environment:

.. code-block:: console

    $ conda activate magic-lst

You will need to run that last command any time you open a new
terminal to activate the conda environment.


Installing magic-cta-pipe in development mode
---------------------------------------------

Now setup this cloned version for development.
The following command will use the editable installation feature of python packages.
From then on, all the magic-cta-pipe executables and the library itself will be
usable from anywhere, given you have activated the ``magic-lst`` conda environment.

.. code-block:: console

    $ pip install -e .

Using the editable installation means you will not have to rerun the installation for
simple code changes to take effect.
However, for things like adding new submodules or new entry points, rerunning the above
step might still be needed.

We are using the ``black`` and ``isort`` auto-formatters for automatic
adherence to the code style (see our :doc:`/developer-guide/style-guide`).
To enforce running these tools whenever you make a commit, setup the
`pre-commit hook <https://pre-commit.com/>`_:

.. code-block:: console

    $ pre-commit install

The pre-commit hook will then execute the tools with the same settings as when the a pull request is checked on github,
and if any problems are reported the commit will be rejected.
You then have to fix the reported issues before tying to commit again.
Note that a common problem is code not complying with the style guide, and that whenever this was the only problem found,
simply adding the changes resulting from the pre-commit hook to the commit will result in your changes being accepted.

``pre-commit`` will run the following checks:

* ``isort``, which checks the import statements
* ``black`` and ``flake8``, which check for the formatting of the code
* ``numpydoc-validation``, which checks for the ``numpydoc`` validation tools.

Run the tests to make sure everything is OK:

.. code-block:: console

    $ pytest

Build the HTML docs locally and open them in your web browser, from the ``docs/_buid/html`` directory:

.. code-block:: console

    $ make doc

To update to the latest development version (merging in remote changes
to your local working copy):


.. tab-set::

   .. tab-item:: Working in the main repository
      :sync: main

      .. code-block:: console

         $ git pull

   .. tab-item:: Working a fork
      :sync: fork

      .. code-block:: console

         $ git fetch upstream
         $ git merge upstream/master --ff-only
         $ git push

      Note: you can also press the "Sync fork" button on the main page of your fork on the github
      and then just use ``git pull``.

Developing a new feature or code change
---------------------------------------

You should always create a new branch when developing some new code.
Make a new branch for each new feature, so that you can make pull-requests
for each one separately and not mix code from each.
It is much easier to review and merge small, well-defined contributions than
a collection of multiple, unrelated changes.

Most importantly, you should *never* add commits to the ``master`` branch of your fork,
as the ``master`` branch will often be updated in the main ``cta-observatory`` repository
and having a diverging history in the ``master`` branch of a fork will create issues when trying
to keep forks in sync.

Remember that ``git switch <name>`` [#switch]_ switches between branches,
``git switch -c <name>`` creates a new branch and switches to it,
and ``git branch`` on it's own will tell you which branches are available
and which one you are currently on.


Create a feature branch
^^^^^^^^^^^^^^^^^^^^^^^

First think of a name for your code change, here we'll use
*implement_feature_1* as an example.


To ensure you are starting your work from an up-to-date ``master`` branch,
we recommend starting a new branch like this:


.. tab-set::

   .. tab-item:: Working in the main repository
      :sync: main

      .. code-block:: console

         $ git fetch  # get the latest changes
         $ git switch -c <new branch name> origin/master  # start a new branch from master

   .. tab-item:: Working a fork
      :sync: fork

      .. code-block:: console

         $ git fetch upstream  # get latest changes from main repository
         $ git switch -c <new branch name> upstream/master # start new branch from upstream/master



Edit the code
^^^^^^^^^^^^^

Make as many commits as you want (more than one is generally
better for large changes!).

.. code-block:: sh

    $ git add some_changed_file.py another_file.py
    $ git commit
      [type descriptive message in window that pops up]

and repeat. The commit message should follow the *Git conventions*:
use the imperative, the first line is a short description, followed by a blank line,
followed by details if needed (in a bullet list if applicable). You
may even refer to GitHub issue ids, and they will be automatically
linked to the commit in the issue tracker.  An example commit message::

  fix bug #245

  - changed the order of if statements to avoid logical error
  - added unit test to check for regression

Of course, make sure you frequently test via ``make test`` (or ``pytest`` in a
sub-module), check the style, and make sure the docs render correctly
(both code and top-level) using ``make doc``.

.. note::

   A git commit should ideally contain one and only one feature change
   (e.g it should not mix changes that are logically different).
   Therefore it's best to group related changes with ``git
   add <files>``. You may even commit only *parts* of a changed file
   using and ``git add -p``.  If you want to keep your git commit
   history clean, learn to use commands like ``git commit --amend``
   (append to previous commit without creating a new one, e.g. when
   you find a typo or something small).

   A clean history and a chain of well-written commit messages will
   make it easier on code reviews to see what you did.

Push your changes
^^^^^^^^^^^^^^^^^

The first time you push a new branch, you need to specify to which remote the branch
should be pushed [#push]_. Normally this will be ``origin``:

.. code-block:: console

   $ git push -u origin implement_feature_1

After that first setup, you can push new changes using a simple

.. code-block:: console

   $ git push


You can do this at any time and more than once. It just moves the changes
from your local branch on your development machine to your fork on github.


Integrating changes from the ``master`` branch.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In case of updates to the ``master`` branch during your development,
it might be necessary to update your branch to integrate those changes,
especially in case of conflicts.

To get the latest changes, run:

.. tab-set::

   .. tab-item:: Working in the main repository
      :sync: main

      .. code-block:: console

         $ git fetch

   .. tab-item:: Working a fork
      :sync: fork

      .. code-block:: console

         $ git fetch upstream

Then, update a local branch using:

.. tab-set::

   .. tab-item:: Working in the main repository
      :sync: main

      .. code-block:: console

         $ git rebase origin/master

      or

      .. code-block:: console

         $ git merge origin/master

   .. tab-item:: Working a fork
      :sync: fork

      .. code-block:: console

         $ git rebase upstream/master

      or

      .. code-block:: console

         $ git merge upstream/master

For differences between rebasing and merging and when to use which, see `this tutorial <https://www.atlassian.com/git/tutorials/merging-vs-rebasing>`_.



Create a *Pull Request*
^^^^^^^^^^^^^^^^^^^^^^^

.. warning::
   Before creating a pull request, please check the following:

   * the code style is ok i.e. run:

      .. code-block:: console

         pre-commit run --all-files

     and possibly fix files that needs changes

   * the documentation builds without issues i.e. run:

      .. code-block:: console

         make doc

     and have a look at the local documentation with your browser by opening ``docs/_build/html/index.html``

   * the tests are passing i.e. run:

      .. code-block:: console

         make test

     and fix the code if there are failing tests.

When you are happy, you can create a pull request (PR):

* if you work on a fork, on your github fork page by clicking "pull request". You can also do this via *GitHub Desktop* if you have
  that installed, by pushing the pull-request button in the upper-right-hand corner.
* if you work on the main repository, on the `magic-cta-pipe pull requests page <https://github.com/cta-observatory/magic-cta-pipe/pulls>`_,
  by clicking on the `New pull request` button.

Make sure to describe all the changes and give examples and use cases!

See the :ref:`pull-requests` section for more info.

Wait for a code review
^^^^^^^^^^^^^^^^^^^^^^

Keep in mind the following:

* At least one reviewer must look at your code and accept your
  request. They may ask for changes before accepting. Like before opening a PR,
  please verify that code style is ok, that documentation builds fine and that
  unit tests are not failing before committing new changes to the PR branch. This
  avoids that the Continuos Integration runs for changes that you know already
  are not passing all checks. See also :ref:`pull-requests` section for more info.
* All unit tests must pass.  They are automatically run by *Travis* when
  you submit or update your pull request and you can monitor the
  results on the pull-request page.  If there is a test that you added
  that should *not* pass because the feature is not yet implemented,
  you may `mark it as skipped temporarily
  <https://docs.pytest.org/en/latest/skipping.html>`_ until the
  feature is complete.
* All documentation must build without errors. Again, this is checked
  by *Travis*.  It is your responsibility to run ``make doc`` and check
  that you don't have any syntax errors in your docstrings (check the
  local documentation in your browser by opening the file ``docs/_build/html/index.html``)
* All code you have written should follow the style guide (e.g. no
  warnings when you run the ``flake8`` syntax checker)

If the reviewer asks for changes, all you need to do is make them, ``git
commit`` them and then run ``git push`` and the reviewer will see the changes.

When the PR is accepted, the reviewer will merge your branch into the
*master* repo on cta-observatory's account.

Delete your feature branch
^^^^^^^^^^^^^^^^^^^^^^^^^^

since it is no longer needed (assuming it was accepted and merged in):

.. code-block:: console

    $ git switch master  # switch back to your master branch

pull in the upstream changes, which should include your new features, and
remove the branch from the local and remote (github).

.. tab-set::

   .. tab-item:: Working in the main repository
      :sync: main

      .. code-block:: console

         $ git pull

   .. tab-item:: Working a fork
      :sync: fork

      .. code-block:: console

         $ git fetch upstream
         $ git merge upstream/master --ff-only

And then delete your branch:

.. code-block:: console

   $ git branch --delete --remotes implement_feature_1


Debugging Your Code
-------------------

More often than not your tests will fail or your algorithm will
show strange behaviour. **Debugging** is one of the powerful tools each
developer should know. Since using ``print`` statements is **not** debugging and does
not give you access to runtime variables at the point where your code fails, we recommend
using ``pdb`` or ``ipdb`` for an IPython shell.
A nice introduction can be found `here <https://hasil-sharma.github.io/2017-05-13-python-ipdb/>`_.

More Development help
---------------------

For coding details, read the :ref:`code_guidelines` section of this
documentation.

To make git a bit easier (if you are on a Mac computer) you may want
to use the `github-desktop GUI <https://desktop.github.com/>`_, which
can do most of the fork/clone and remote git commands above
automatically. It provides a graphical view of your fork and the
upstream cta-observatory repository, so you can see easily what
version you are working on. It will handle the forking, syncing, and
even allow you to issue pull-requests.

.. rubric:: Footnotes

.. [#switch] ``git switch`` is a relatively new addition to git. If your version of git does not have it, update or use ``git checkout`` instead. The equivalent old command to ``git switch -c`` is ``git checkout -b``.

.. [#push] As of git version 2.37, you can set these options so that ``git push`` will just work,
    also for the first push:

    .. code-block:: console

       $ git config --global branch.autoSetupMerge simple
       $ git config --global push.autoSetupRemote true