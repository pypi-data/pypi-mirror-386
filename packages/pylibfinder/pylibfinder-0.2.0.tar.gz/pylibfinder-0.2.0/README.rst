pylibfinder (supports Python 3.10 to 3.14 on POSIX)
====================================================

- pylibfinder is a Python library that allows you to spot a keyword as a function inside the Python standard library.
- It provides a convenient way to search for functions that match a given keyword within the standard library modules.
- With pylibfinder, you can easily identify the modules and functions that are available in Python and gain insights  into their usage and availability.
- This library is designed to assist developers in finding relevant functions and understanding the   Python standard library better.


.. image:: https://img.shields.io/pypi/v/pylibfinder
   :target: https://pypi.python.org/pypi/pylibfinder/

.. image:: https://github.com/Agent-Hellboy/pylibfinder/actions/workflows/test.yml/badge.svg
    :target: https://github.com/Agent-Hellboy/pylibfinder/actions/workflows/test.yml

.. image:: https://img.shields.io/pypi/pyversions/pylibfinder.svg
   :target: https://pypi.python.org/pypi/pylibfinder/

.. image:: https://img.shields.io/pypi/wheel/pylibfinder.svg
   :target: https://pypi.python.org/pypi/pylibfinder/

.. image:: https://img.shields.io/badge/C%20Extension-yes-brightgreen.svg
   :target: https://github.com/Agent-Hellboy/pylibfinder

.. image:: https://img.shields.io/badge/platform-macOS-blue.svg
   :target: https://github.com/Agent-Hellboy/pylibfinder

.. image:: https://img.shields.io/badge/platform-Linux-blue.svg
   :target: https://github.com/Agent-Hellboy/pylibfinder

.. image:: https://img.shields.io/badge/License-MIT-blue.svg
   :target: https://github.com/Agent-Hellboy/pylibfinder/blob/main/LICENSE

.. image:: https://pepy.tech/badge/pylibfinder
   :target: https://pepy.tech/project/pylibfinder

.. image:: https://img.shields.io/pypi/format/pylibfinder.svg
   :target: https://pypi.python.org/pypi/pylibfinder/

Installation
============


For stable version

        - clone the repo: ``git clone https://github.com/Agent-Hellboy/pylibfinder``
        - cd into it: ``cd pylibfinder``
        - install with pip: ``pip install .`` (on Mac and Linux)

For development

        - git clone https://github.com/Agent-Hellboy/pylibfinder
        - cd pylibfinder
        - make changes in funcfinder.c
        - compile it using ``gcc -shared -o funcfinder.so -fPIC -I /usr/include/python3.13 funcfinder.c``
        - it will generate a funcfinder.so
        - open repl and test


Example
=======

.. code:: py

      >>> import funcfinder
      >>> funcfinder.get_module('literal')
      [{'Module': 'ast', 'Function': 'literal_eval'}, {'Module': 're._compiler', 'Function': '_get_literal_prefix'}]
      >>>



Contributing
============

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.
