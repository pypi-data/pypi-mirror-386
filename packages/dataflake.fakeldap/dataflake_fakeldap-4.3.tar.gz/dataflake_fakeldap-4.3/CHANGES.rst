Change log
==========

4.3 (2025-10-24)
----------------

- Add support for Python 3.14 and 3.15.

- Drop support for Python 3.7, 3.8 and 3.9.


4.2 (2024-03-14)
----------------

- Switch to PEP 420 implicit namespace support.

- Add support for Python 3.13.


4.1 (2024-01-03)
----------------

- Add support for Python 3.12.


4.0 (2023-02-03)
----------------

- Drop support for Python 2.7, 3.5, 3.6.


3.0 (2021-11-02)
----------------
- add a test layer using the ``volatildap`` module to compare API call results
  with the equivalent results from a live LDAP server.

- fix several API discrepancies between this module and ``python-ldap``.

- emulate string/bytes treatment from ``python-ldap`` version 3.3 and up,
  see https://www.python-ldap.org/en/latest/bytes_mode.html and ``README.rst``
  in this folder.

- move from ``bootstrap.py`` to ``virtualenv`` and ``pip`` for bootstrapping

- add support for Python 3.8, 3.9 and 3.10 and Pypy3

- drop support for Python 2

- reorganize package structure


2.3 (2018-06-29)
----------------
- test and declare support for Python 3.7


2.2 (2018-05-21)
----------------
- move back to ``python-ldap`` from ``pyldap``, the code has been merged.
- fix last DeprecationWarning


2.1 (2017-12-14)
----------------
- The query filter parsing now allows non-ASCII values to be passed
  [majuscule]
- Expand the allowed characters for query parsing from a hardcoded list
  [adparvum]


2.0 (2017-08-17)
----------------
- drop Python 3.4 compatibility because it cannot deal with 
  ``%s``-style text replacement in byte strings
- switch to aggressive input checking to ensure all DN, RDN or 
  attribute names are passed in as UTF-8-encoded strings. This 
  reflects the :mod:`pyldap` module behavior. Since this is a 
  behavior change, move version number to 2.0.


1.3 (2017-06-06)
----------------
- Python 2/3 compatibility fixes for ``dataflake.ldapconnection``


1.2 (2017-06-01)
----------------
- For Python 2.x, only support Python 2.7 now
- switch from ``python-ldap`` to ``pyldap`` for Python 3 compatibility
- add PEP 8 testing with ``flake8`` to the ``tox`` test config
- code reformatting for PEP 8
- Python 3 compatibilty
- use pkgutil-style namespace declaration
- package cleanup (``.gitignore``, ``MANIFEST.in``, ``README.rst``)
- docs cleanup (``Makefile``, ``conf.py``)
- tests cleanup (``tox.ini``, ``.travis.yml``)
- remove unsupported documentation bits
- fix coverage tests to only test this package
- remove coveralls from the Travis CI configuration


1.1 (2012-10-18)
----------------
- the Filter object will now clean up filter values during creation
  by stripping leading and trailing whitespace. This corresponds to 
  normal LDAP servers' behavior, such as OpenLDAP, where values match 
  regardless of leading or trailing spaces in the query's value.


1.0 (2012-04-20)
----------------
- refactor the monolithic original module into manageable and 
  testable submodules
- convert functions to class methods
- convert doctests to unit tests
- improve test coverage
- Initial release. For changes prior to this release please see the 
  ``dataflake.ldapconnection`` package up to release 1.4.
- add convenience ``tox`` script to buildout
- fix problem with BASE scoped-searches that specified additional 
  filters
- add coverage testing to tox configuration
- Extended ``dataflake.fakeldap.RaisingFakeLDAPConnection`` to accept 
  a list of exceptions to raise. On each call to the method that is set
  to raise the exception, the first item in the exception list
  is removed and raised. This allows testing code areas nested in
  more than one ``try/except`` clause.


Earlier changes
---------------
For earlier changes, please see the change log in the 
``dataflake.ldapconnection`` package prior to version 1.4.
