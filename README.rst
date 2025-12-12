=======================================
Repository with small git hooks scripts
=======================================

Hooks from that repository are using LLM to help with some basic actions
while commiting changes in your project.

All of those scripts are oriented on using local LLMs through the Ollama API.

Installation
------------

First you need to install `ollama` python library.
This can be done through the package provided by distro of your choice,
like for example on Fedora:

.. code-block:: bash

    sudo dnf install python3-ollama

Or through the pip package manager:

.. code-block:: bash

    pip install ollama

Then you can install the hooks by running the following command:

.. code-block:: bash

    ./install.sh <destination repository path>

Where `<destination repository path>` is the path to the repository you want to install the hooks in.