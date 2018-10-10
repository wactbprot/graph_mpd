virtual env
===========

.. code-block:: shell

    > python3 -m venv /path/to/graph_mpd
    > cd /path/to/graph_mpd
    > source bin/activate
    > pip install graphviz
    > pip install couchdb

usage
=====

.. code-block:: shell

    > cd /path/to/graph_mpd
    > source bin/activate
    > python main.py --doc <document-id>