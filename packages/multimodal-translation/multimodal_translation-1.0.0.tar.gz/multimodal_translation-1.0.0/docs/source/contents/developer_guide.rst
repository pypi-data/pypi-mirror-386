===============
Developer Guide
===============

| Insall `pip` 
 
.. code-block:: shell

    python3 -m pip install 


| Clone the repository 

.. code-block:: shell

    git clone git@github.com:Issamricin/multimodal-translation.git
    cd multimodal-translation

| Make the project in edit mode  

.. code-block:: shell

    pip install -e .



Publish Notes
-------------
Steps to test the publish on pypi, see workflow files for publishing on pypi test server (release_test.yaml)

| If you do an update for the README.rst, please copy and paste into  `RST-Check <https://rsted.info.ucl.ac.be/>`__ 

.. code-block:: shell

   git clone git@github.com:Issamricin/multimodal-translation.git
   python -m venv .venv 


You need to install tox on to run the workflow tox task or env run task 

| **tox check list before you push to remote repo**

.. code-block:: shell

   python -m pip install tox 
   tox -v -s false -e pin-deps
   tox -e type -v -s false
   tox -v -s false | tee test_output.log
   tox -e coverage --sitepackages -v -s false
   tox -e wheel-test -s false
   tox -e check -v -s false
   tox -e isort -vv -s false
   tox -e black -vv -s false
   tox -e ruff -vv -s false
   tox -e prospector -vv -s false
 

| Below is to build and check the twine for pypi publish in case an error in the markup you need to check rst online 

 `Making Friendly PyPi Package  <https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme/>`__ 

.. code-block:: shell

   python -m pip install build 
   python -m build -s
   python -m build --wheel
   python -m pip install --upgrade twine
   twine check dist/* 
    
 
Now you need to have your test project setup on testpypi 
`Publishing <https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/>`__ 
so to trigger the workflow you need to create a test tag and push it so it triggers the release_test.yaml
Before you do that update your package version in the toml, tox and __init__.py file

| suppose my package release is 0.3.3 
| Test tag  is **test-0.3.3**
| Prod tag is **release-0.3.3**

| To trigger the release into test pypi  
| $  git tag test-0.3.3
| $  git push origin  --tags


`Git Basic Tag Commands <https://git-scm.com/book/en/v2/Git-Basics-Tagging>`__ 

   
Developer Notes
---------------
Testing, Documentation Building, Scripts, CI/CD, Static Code Analysis for this project.

1. **Test Suite**, using `pytest`_, located in `tests` dir
2. **Parallel Execution** of Unit Tests, on multiple cpu's
3. **Documentation Pages**, hosted on `readthedocs` server, located in `docs` dir
4. **CI(Continuous Integration)/CD(Continuous Delivery) Pipeline**, running on `Github Actions`, defined in `.github/`

   a. **Test Job Matrix**, spanning different `platform`'s and `python version`'s

      1. Platforms: `ubuntu-latest`
      2. Python Interpreters:  `3.13`
   b. **Continuous Deployment**
   
      `Production`
      
         1. **Python Distristribution** to `pypi.org`_, on `tags` test-* and release-* (e.g. test-0.1.0 to release to test pypi), pushed to `main` branch
         2. **Docker Image** to `Dockerhub`_, on every push, with automatic `Image Tagging`
      
      `Staging`

         3. **Python Distristribution** to `test.pypi.org`_, on "pre-release" `tags` **v*-rc**, pushed to `release` branch

   c. **Configurable Policies** for `Docker`, and `Static Code Analysis` Workflows
5. **Automation**, using `tox`_, driven by single `tox.ini` file

   a. **Code Coverage** measuring
   b. **Build Command**, using the `build`_ python package
   c. **Pypi Deploy Command**, supporting upload to both `pypi.org`_ and `test.pypi.org`_ servers
   d. **Type Check Command**, using `mypy`_
   e. **Lint** *Check* and `Apply` commands, using the fast `Ruff`_ linter, along with `isort`_ and `black`_


Project Detials:
----------------

| Test cases cover exception (network) and ValidationError and success translation

| The code covers up to 90% and we show the coverage report. Use Tox to execute coverage report with test

| Finally, tox staff from the list to are checked to make sure things are correct before pushing changes to remote repo. 

| Example of a json object request which will come from the rest call from the web application (End Usage)

.. code-block:: shell

   {
    "text": "Hello, this is the text."
    "lang": "en",
    "targets": [
        "se",
        "ku",
        "pl"
    ]
   }


| Example of the response which will be sent back to web view

.. code-block:: shell

  [
    {
        "text": "Hej där, Jag är kroppend av meddelande",
        "lang": "se"
    },
    {
     "error": " ku is not supported blalaaa"
    },
    {
        "text": "blalaaa",
        "lang": "pl"
    }
  ]

Audio:
------

One Audio language to Many languages Text Translation:
------------------------------------------------------

| See the src/multimodaltranslation/audio which we are working on which is being wrapped by speech_recognition
  Google API is good but it has limitation and you can check that
  In the model we have BytesIO but try to start with simple file and change the model signature if needed.
  The reason for BytesIO usage since the call will come from the web client with payload of stream.


RST File Checker:
-----------------

https://rsted.info.ucl.ac.be/


Ready to contribute?
--------------------

| Make sure to read the usage to further understand this project.
| `Usage <https://multimodal-translation.readthedocs.io/en/latest/contents/usage.html>`_

| Now that you have a general idea about the project, you are ready to start contributing and developing.
| `Contribute! <https://multimodal-translation.readthedocs.io/en/latest/contents/contribution.html>`_

| You can also check the technical debt for future development.
| `Technical debt <https://multimodal-translation.readthedocs.io/en/latest/contents/tech_debt.html>`_

API Documentation
-----------------
We follow Google style documentation for packages, modules, classes, methods 

.. LINKS
.. _Tox: https://tox.wiki/en/latest/
.. _Pytest: https://docs.pytest.org/en/7.1.x/
.. _Build: https://github.com/pypa/build
.. _Docker: https://hub.docker.com/
.. _pypi.org: https://pypi.org/
.. _test.pypi.org: https://test.pypi.org/
.. _mypy: https://mypy.readthedocs.io/en/stable/
.. _Ruff: https://docs.astral.sh/ruff/
.. _Isort: https://pycqa.github.io/isort/__ 
.. _Black: https://black.readthedocs.io/en/stable/
.. _Google API docs: https://www.sphinx-doc.org/en/master/usage/extensions/example_google.html
.. _Dockerhub: https://www.docker.com/products/docker-hub/

