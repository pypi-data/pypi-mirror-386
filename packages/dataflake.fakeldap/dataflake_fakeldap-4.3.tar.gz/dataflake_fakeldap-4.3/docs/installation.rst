Installation
============


Prerequisites
-------------
You need to have LDAP libraries and developer files installed prior to
installing :mod:`dataflake.fakeldap`. The most common implementation
is OpenLDAP.


Install with ``pip``
--------------------

.. code:: 

    $ pip install dataflake.fakeldap


Install with ``zc.buildout``
----------------------------
Just add :mod:`dataflake.fakeldap` to the ``eggs`` setting(s) in your
buildout configuration to have it pulled in automatically::

    ...
    eggs =
        dataflake.fakeldap
    ...
