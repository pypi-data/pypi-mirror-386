pylibfinder (supports Python 3.10 to 3.14 on POSIX)
====================================================

- pylibfinder is a Python library that allows you to spot a keyword as a function inside the Python standard library.
- It provides a convenient way to search for functions that match a given keyword within the standard library modules.
- With pylibfinder, you can easily identify the modules and functions that are available in Python and gain insights  into their usage and availability.
- This library is designed to assist developers in finding relevant functions and understanding the   Python standard library better.


.. image:: https://img.shields.io/pypi/v/pylibfinder
   :target: https://pypi.python.org/pypi/pylibfinder/

.. image:: https://github.com/Agent-Hellboy/pylibfinder/actions/workflows/test.yml/badge.svg
    :alt: CI Tests
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



Installation
============


For stable version

        - clone the repo: ``git clone https://github.com/Agent-Hellboy/pylibfinder``
        - cd into it: ``cd pylibfinder``
        - install with pip: ``pip install .`` (on macOS and Linux)

For development

**Recommended (Easy setup):**

        - git clone https://github.com/Agent-Hellboy/pylibfinder
        - cd pylibfinder
        - ``pip install -e .`` (installs in editable mode with proper Python headers detection)
        - make changes to ``src/pylibfinder.c``
        - reinstall with ``pip install -e .`` to rebuild
        - open repl and test

**Manual compilation:**

**macOS:**

        - Install Homebrew Python: ``brew install python@3.13``
        - Find Python include path: ``python3.13 -c "import sysconfig; print(sysconfig.get_path('include'))"``
        - Compile: ``gcc -shared -o pylibfinder.so -fPIC -I /opt/homebrew/opt/python@3.13/Frameworks/Python.framework/Versions/3.13/include/python3.13 src/pylibfinder.c src/module_scanner.c -lpython3.13``
        - It will generate ``pylibfinder.so``
        - Test in Python REPL: ``python3.13 -c "import pylibfinder; print(pylibfinder.find_similar('power'))``

**Linux:**

        - Install Python dev package: ``sudo apt-get install python3.13-dev``
        - Compile: ``gcc -shared -o pylibfinder.so -fPIC -I /usr/include/python3.13 src/pylibfinder.c src/module_scanner.c``
        - It will generate ``pylibfinder.so``
        - Test in Python REPL: ``python3.13 -c "import pylibfinder; print(pylibfinder.find_similar('power'))``


Example
=======

**Semantic similarity search - Find similar functions:**

.. code:: py

      >>> import pylibfinder
      >>>
      >>> # Search for 'power' to find math functions (default threshold 0.5)
      >>> pylibfinder.find_similar('power')
      [{'Module': 'builtins', 'Function': 'pow', 'Similarity': 0.6}, ...]
      >>>
      >>> # Search for 'print' with custom threshold
      >>> result = pylibfinder.find_similar('print', 0.5)
      >>> result[0]
      {'Module': 'builtins', 'Function': 'print', 'Similarity': 1.0}
      >>>
      >>> # Find functions similar to 'parseInt' (Java function) with higher threshold
      >>> pylibfinder.find_similar('parseInt', 0.6)
      [{'Module': 're._parser', 'Function': '_parse_sub', 'Similarity': 0.6}]
      >>>



Contributing
============

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.
