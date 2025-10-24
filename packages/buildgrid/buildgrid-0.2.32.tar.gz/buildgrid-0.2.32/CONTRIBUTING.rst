.. _contributing:

Contributing
============

Some guidelines for people wanting to contribute. Also please always feel free
to speak to us, we're very friendly :-)


.. _feature-additions:

Feature additions
-----------------

We welcome contributions in the form of bug fixes or feature additions. Please
discuss with us before submitting anything, as we may well have some important
context which will could help guide your efforts.

Any major feature additions should be raised first as a proposal on the
BuildGrid mailing list to be discussed between the core contributors. Once 
this discussion has taken place and there is agreement on how to proceed, 
it should be followed by with a Gitlab issue being raised which summarizes 
the tasks required.

We strongly recommend that you propose the feature in advance of
commencing any work.

The author of any patch is expected to take ownership of that code and is to
support it for a reasonable time-frame. This means addressing any unforeseen
side effects and quirks the feature may have introduced.

.. _BuildGrid mailing list: https://lists.buildgrid.build/cgi-bin/mailman/listinfo/buildgrid

.. _patch-submissions:

Patch submissions
-----------------

Branches must be submitted as merge requests (MR) on GitLab and should have a 
corresponding issue raised in advance (whenever possible). If it's a small change,
an MR without it being associated to an issue is okay, but generally we prefer an
issue to be raised in advance so that we can track the work that is
currently in progress on the project.

When submitting a merge request, please obtain a review from another committer 
who is familiar with the area of the code base which the branch effects. Two
approvals from other committers who are not the patch author will be needed
before any merge (we use Gitlab's 'approval' feature for this).

Below is a list of good patch submission good practice:

- Each commit should address a specific issue number in the commit message. This
  is really important for provenance reasons.
- Merge requests that are not yet ready for review should be prefixed with the
  ``Draft:`` identifier.
- Submitted branches should not contain a history of work done.
- Unit tests should be a separate commit.

Commit messages
~~~~~~~~~~~~~~~

Commit messages must be formatted with a brief summary line, optionally followed
by an empty line and then a free form detailed description of the change. The
summary line must start with what changed, followed by a colon and a very brief
description of the change. If there is an associated issue, it **must** be
mentioned somewhere in the commit message.

**Example**::

   worker.py: Fixed to be more human than human

   Gifted the worker with a past so we can create
   a cushion or a pillow for their emotions and
   consequently, we can control them better.

   This fixes issue #8.

For more tips, please read `The seven rules of a great Git commit message`_.

.. _The seven rules of a great Git commit message: https://chris.beams.io/posts/git-commit/#seven-rules

.. _coding-style:

Coding style
------------

Python coding style for BuildGrid is `PEP 8`_. We do have a couple of minor
exceptions to this standard, we dont want to compromise code readability by
being overly restrictive on line length for instance.

BuildGrid's test suite includes a PEP8 style compliance check using `flake8`_.
That test suite is automatically run for every change submitted to the GitLab
server and the merge request sytem requires the test suite execution to succeed
before changes can be pulled upstream. This means you have to respect the BuildGrid
coding style. For convenience you can run `tox -e flake8` to perform these checks.

BuildGrid's CI also runs a static type check in the form of `mypy`_. While mypy
is stable, it is not yet 1.0 and thus is not able to understand every use case
in typing (such as recursive types and complex mutators). Nevertheless, type
annotations are strongly preferred for readability, with complex type issues
flagged with ``# type: ignore``.

Configuration and exceptions for ``flake8`` can be found in:

- The `setup.cfg`_ file for ``flake8``.

.. _PEP 8: https://www.python.org/dev/peps/pep-0008
.. _flake8: https://flake8.pycqa.org/en/latest/
.. _setup.cfg: https://gitlab.com/BuildGrid/buildgrid/blob/master/setup.cfg
.. _mypy: http://mypy-lang.org/

Automated code formatting should be run using `isort` and `black` before submitting
MRs to the project. These tools can be invoked by running `tox -e format`.

Imports
~~~~~~~

Both absolute and relative imports are allowed. Prefer absolute imports when
possible, but if the absolute import path gets too long, relative imports are
okay.

Absolute::

  from buildgrid.worker import Worker

Relative::

  from .worker import Worker


Symbol naming
'''''''''''''

Any private symbol must start with a single leading underscore for two reasons:

- So that it does not bleed into documentation and *public API*.
- So that it is clear to developers which symbols are not used outside of the
  declaring *scope*.

Remember that with python, the modules (python files) are also symbols within
their containing *package*, as such; modules which are entirely private to
BuildGrid are named as such, e.g. ``_roy.py``.


Typing
......

Always add type annotations to your code and ensure that mypy verifies it.

BuildGrid was started before we began adding type annotations to the codebase,
so you may run across functions that are not annotated. If you do, please leave
the functions better than you found them and add annotations. mypy was designed
with `this maintenance pattern <https://mypy.readthedocs.io/en/latest/existing_code.html>`_
in mind.

.. _codebase-testing:

Testing
-------

BuildGrid is using `pytest`_ for regression and newly added code testing. The
test suite contains a serie of unit-tests and also run linting tools in order to
detect coding-style_ breakage. The full test suite is automatically executed by
GitLab CI system for every push to the server. Passing all the tests is a
mandatory requirement for any merge request to the trunk.

.. _pytest: https://docs.pytest.org


Running tests
~~~~~~~~~~~~~

In order to run the entire test suite, simply run:

.. code-block:: sh

   tox -e ci-venv -- pytest tests

pyest's `usage documentation section`_ details the different command line
options that can be used when invoking the test runner.

.. _usage documentation section: https://docs.pytest.org/en/latest/usage.html


Test coverage
~~~~~~~~~~~~~

We are doing our best at keeping BuildGrid's test coverage score as high as
possible. Doing so, we ask for any merge request to include necessary test
additions and/or modifications in order to maintain that coverage level. A
detailed `coverage report`_ is produced and publish for any change merged to the
trunk.

.. _coverage report: https://buildgrid.gitlab.io/buildgrid/coverage/

.. _gitlab-features:

GitLab features
---------------

We intend to make use of some of GitLab's features in order to structure the
activity of the BuildGrid project. In doing so we are trying to achieve the
following goals:

- Full transparency of the current work in progress items
- Provide a view of all current and planned activity which is relatively easy
  for the viewer to digest
- Ensure that we keep it simple and easy to contribute to the project

Explanation of how the project is currenlty using some GitLab features:

- `Labels`_: allow us to filter tickets (ie, 'issues' in gitlab terminology)
  in useful ways. They add complexity and effort as they grow in number, so the
  general approach is to ensure the ones we have are actually used and are 
  applied consistently. See the `BuildGrid labels`_. 
- `Boards`_: allow us to visualise and manage issues and labels in a simple way.
  Issues start life in the ``Backlog`` column by default, and we move them into
  ``ToDo`` when we aim to complete them in the current development cycle.
  ``Doing`` is only for when an item is currently being worked on. When on the
  Board view, dragging and dropping an issue from column to column automatically
  adjusts the relevant labels. See the `BuildGrid boards`_.
  
  
Guidelines for using GitLab features when working on this project: 
  
- When raising an issue, please:
   
  - check to see if there already is an issue to cover this task (if not then 
    raise a new one)
  - assign the appropriate label or labels (tip: the vast majority of issues 
    raised will be either an enhancement or a bug)
    
- If you plan to work on an issue, please:

  - self-assign the ticket
  - ensure the ticket is in the ``ToDo`` column of the board if you aim to 
    complete in the current sprint but aren't yet working on it, and
    the ``Doing`` column if you are working on it currently.

- Please note that Gitlab issues are for either 'tasks' or 'bugs' - ie not for 
  long discussions (where the mailing list is a better choice) or for ranting, 
  for example.
  
The above may seem like a lot to take in, but please don't worry about getting 
it right the first few times. The worst that can happen is that you'll get a 
friendly message from a current contributor who explains the process. We welcome
and value all contributions to the project!  

.. _Labels: https://docs.gitlab.com/ee/user/project/labels.html
.. _BuildGrid labels: https://gitlab.com/BuildGrid/buildgrid/labels
.. _Boards: https://docs.gitlab.com/ee/user/project/issue_board.html
.. _BuildGrid boards: https://gitlab.com/BuildGrid/buildgrid/boards
.. _Templates: https://docs.gitlab.com/ee/user/project/description_templates.html
