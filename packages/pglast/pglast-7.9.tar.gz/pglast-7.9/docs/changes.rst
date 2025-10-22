.. -*- coding: utf-8 -*-

.. _changes:

Changes
-------

Version 7
#########

7.9 (2025-10-22)
~~~~~~~~~~~~~~~~

- Add an empty line between a ``SELECT foo UNION SELECT bar`` and its ``ORDER
  BY``/``LIMIT``/``OFFSET`` clause, to emphasize the fact that it applies to the whole
  statement, not to the "right" subquery.


7.8 (2025-10-19)
~~~~~~~~~~~~~~~~

- Fix prettification of single keyword statements (`PR #173`__), thanks to Vlastimil Zíma

  __ https://github.com/lelit/pglast/pull/173

- Improve ``WithClause`` printer, when there is more than one *CTE*

- Avoid spurious parenthesis around expression terms in some common cases like ``1 + 2 + 3 + 4``

- Use macOS 14 to build arm 64 wheels and macOS 15 to build x86-64 wheels, given that GH is
  going to `drop macOS 13 runners`__ in a couple of months

  __ https://app.github.media/e/es?s=88570519&e=4325169&elq=c19630476abd40d0b7c6ff415b964f56

- Generate Python 3.14 wheels, thanks to cibuildwheel `3.2.1`__

  __ https://cibuildwheel.pypa.io/en/stable/changelog/#v321


7.7 (2025-04-04)
~~~~~~~~~~~~~~~~

- Nothing visible, fix GitHub Actions CI environment


7.6 (2025-04-03)
~~~~~~~~~~~~~~~~

- Upgrade libpg_query to `17-6.1.0`__

  __ https://github.com/pganalyze/libpg_query/releases/tag/17-6.1.0


7.5 (2025-03-17)
~~~~~~~~~~~~~~~~

- Merge with `Version 6`_


7.4 (2025-03-17)
~~~~~~~~~~~~~~~~

- Merge with `Version 6`_


7.3 (2025-02-09)
~~~~~~~~~~~~~~~~

- Handle the ``SET configuration_parameter FROM CURRENT`` case in the ``VariableSetStmt``
  printer (`PR #168`__), thanks to Bolaji Wahab

  __ https://github.com/lelit/pglast/pull/168


7.2 (2024-12-21)
~~~~~~~~~~~~~~~~

- Merge with `Version 6`_

- Handle ``timestamp AT LOCAL`` expression, new in PG17


7.1 (2024-11-26)
~~~~~~~~~~~~~~~~

- Merge with `Version 6`_


7.0 (2024-11-13)
~~~~~~~~~~~~~~~~

- No visible changes


7.0.dev1 (2024-11-01)
~~~~~~~~~~~~~~~~~~~~~

- Upgrade libpg_query to `17-6.0.0`__

  __ https://github.com/pganalyze/libpg_query/releases/tag/17-6.0.0


7.0.dev0 (2024-10-31)
~~~~~~~~~~~~~~~~~~~~~

- No visible changes with respect to v6, apart from the support for new/revised syntaxes of
  `PostgreSQL 17`__

  __ https://www.postgresql.org/docs/17/release-17.html

~~~~~~~~~~~~~~~~~~~~
**Breaking changes**
~~~~~~~~~~~~~~~~~~~~

- Target PostgreSQL 17, thanks to libpg_query `17-latest-dev`__

  __ https://github.com/pganalyze/libpg_query/tree/17-latest-dev

- Require Python >= 3.9


Version 6
#########

6.16 (2025-03-17)
~~~~~~~~~~~~~~~~~

- No visible changes, just a workaround to a strange CI Windows-only failure on a test
  introduced by v6.15


6.15 (2025-03-17)
~~~~~~~~~~~~~~~~~

- Escape occurrences of C-style end markers in SQL-style comments, when changing comment style
  in the ``RawStream`` (issue `#170`__)

  __ https://github.com/lelit/pglast/issues/170


6.14 (2025-02-09)
~~~~~~~~~~~~~~~~~

- Handle the ``SET configuration_parameter FROM CURRENT`` case in the ``VariableSetStmt``
  printer (backport of `PR #168`__)

  __ https://github.com/lelit/pglast/pull/168


6.13 (2024-12-17)
~~~~~~~~~~~~~~~~~

- Better fix to the ``x AT TIME ZONE foo`` glitch, v6.12 solution was incomplete


6.12 (2024-12-16)
~~~~~~~~~~~~~~~~~

- Properly wrap ``x AT TIME ZONE foo`` in parens when it is the argument of a ``DEFAULT``
  constraint


6.11 (2024-11-26)
~~~~~~~~~~~~~~~~~

- Remove spurious trailing space in the ``ConstrTypePrinter.CONSTR_IDENTITY`` and the
  ``Constraint`` printers (issue `#165`__)

  __ https://github.com/lelit/pglast/issues/165


6.10 (2024-11-01)
~~~~~~~~~~~~~~~~~

- Upgrade libpg_query to `16-5.2.0`__

  __ https://github.com/pganalyze/libpg_query/releases/tag/16-5.2.0


6.9 (2024-10-31)
~~~~~~~~~~~~~~~~

- Fix regression introduced by recent modification to the ``CommonTableExpr`` printer that
  impacted on the ``RawStream`` renderer (issue `#163`__)

  __ https://github.com/lelit/pglast/issues/163

- Expose the ``RawStream`` renderer in the CLI tool with a new ``--normalize`` option


6.8 (2024-10-29)
~~~~~~~~~~~~~~~~

- Upgrade libpg_query to not-yet-publicly-released commit__, to solve an issue related to
  `plpgsql` (issue `#156`__)

  __ https://github.com/pganalyze/libpg_query/commit/06670290ad39e61805ecacbc6267df61f6ae3d91
  __ https://github.com/lelit/pglast/issues/156


6.7 (2024-10-28)
~~~~~~~~~~~~~~~~

- Generate wheels on PyPI using Python 3.13.0 final release, thanks to cibuildwheel `2.21.3`__

  __ https://cibuildwheel.pypa.io/en/stable/changelog/#v2213

- Improve ``CommonTableExpr`` printer, reducing horizontal space waste


6.6 (2024-09-30)
~~~~~~~~~~~~~~~~

- Make recently introduced doctest related to issue #88 work on different Python versions


6.5 (2024-09-29)
~~~~~~~~~~~~~~~~

- Fix glitch when using the ``--preserve-comments`` flag (issue `#159`__)

  __ https://github.com/lelit/pglast/issues/159

- Finally add a note to ``parse_plpgsql()`` documentation mentioning how it differs from
  ``parse_sql()`` (issue `#88`__)

  __ https://github.com/lelit/pglast/issues/88


6.4 (2024-09-28)
~~~~~~~~~~~~~~~~

- Fix issue with deserialization of deeply nested ASTs (issue `#153`__)

  __ https://github.com/lelit/pglast/issues/153

- Upgrade libpg_query to not-yet-publicly-released commit__, to solve an issue related to
  `plpgsql` (issue `#154`__)

  __ https://github.com/pganalyze/libpg_query/commit/680f5ee67c6fdae497c8d1edfadd02b9b8eac74f
  __ https://github.com/lelit/pglast/issues/154


6.3 (2024-08-06)
~~~~~~~~~~~~~~~~

- Fix ``SEQUENCE NAME`` in ``create_seq_stmt_def_elem`` (`PR #151`__), thanks to orages

  __ https://github.com/lelit/pglast/pull/151

- Generate wheels on PyPI using Python 3.13.0rc1 release, thanks to cibuildwheel `2.20.0`__

  __ https://cibuildwheel.pypa.io/en/stable/changelog/#v2200

- Use `Cython 3.0.11`__

  __ https://github.com/cython/cython/blob/master/CHANGES.rst#3011-2024-08-05


6.2 (2024-02-01)
~~~~~~~~~~~~~~~~

- Almost no-op release to fix issue `144`__, producing correct wheels for macOS arm64

  __ https://github.com/lelit/pglast/issues/144

6.1 (2024-01-22)
~~~~~~~~~~~~~~~~

- Inherit fix for issue `143`__ from `version 5`_

  __ https://github.com/lelit/pglast/issues/143


6.0 (2024-01-22)
~~~~~~~~~~~~~~~~

- Produce wheels for macOS arm64


6.0.dev2 (2024-01-21)
~~~~~~~~~~~~~~~~~~~~~

- Enable compilation on Windows and produce related 32bit and 64bit wheels (issue `#7`__)

  __ https://github.com/lelit/pglast/issues/7


6.0.dev1 (2024-01-11)
~~~~~~~~~~~~~~~~~~~~~

- Re-enable Linux 32bit wheels, thanks to libpg_query to `16-5.1.0`__

  __ https://github.com/pganalyze/libpg_query/releases/tag/16-5.1.0


6.0.dev0 (2023-12-29)
~~~~~~~~~~~~~~~~~~~~~

- No visible changes with respect to v5, apart from the support for new/revised syntaxes of
  `PostgreSQL 16`__

  __ https://www.postgresql.org/docs/16/release-16.html

- Do not build binary wheels for Python 3.8

- Skip compilation on Linux 32bit (see `this comment`__ for details)

  __ https://github.com/pganalyze/libpg_query/pull/225#issuecomment-1864145089

~~~~~~~~~~~~~~~~~~~~
**Breaking changes**
~~~~~~~~~~~~~~~~~~~~

- Target PostgreSQL 16, thanks to libpg_query `16-5.0.0`__

  __ https://github.com/pganalyze/libpg_query/releases/tag/16-5.0.0


Version 5
#########

5.9 (2024-01-22)
~~~~~~~~~~~~~~~~

- Fix issue `143`__, affecting ``AlterOwnerStmt`` and ``RenameStmt`` printers

  __ https://github.com/lelit/pglast/issues/143


5.8 (2024-01-11)
~~~~~~~~~~~~~~~~

- Fix issue `#142`__, a glitch that affected 32-bit systems

  __ https://github.com/lelit/pglast/issues/142


5.7 (2023-12-23)
~~~~~~~~~~~~~~~~

- Use `Cython 3.0.7`__

  __ https://github.com/cython/cython/blob/master/CHANGES.rst#307-2023-12-19

- Update libpg_query to `15-4.2.4`__

  __ https://github.com/pganalyze/libpg_query/releases/tag/15-4.2.4


5.6 (2023-12-07)
~~~~~~~~~~~~~~~~

- Fix issue `#138`__, a defect that hindered the creation of AST nodes that act as *markers*,
  (currently ``A_Star`` and ``CheckPointStmt``), that do not carry any other information

  __ https://github.com/lelit/pglast/issues/138

- Use `Cython 3.0.6`__

  __ https://github.com/cython/cython/blob/master/CHANGES.rst#306-2023-11-26

- Handle the ``ENABLE TRIGGER ALL`` in ``AlterTableCmd``

- Fix issue `#136`__, a regression introduced by “Avoid overly abundancy of parentheses in
  expressions”

  __ https://github.com/lelit/pglast/issues/136


5.5 (2023-10-07)
~~~~~~~~~~~~~~~~

- Use `Cython 3.0.3`__

  __ https://github.com/cython/cython/blob/master/CHANGES.rst#303-2023-10-05

- Produce wheels using final Python 3.12 release, thanks to ``cibuildwheel`` `2.16.2`__

  __ https://cibuildwheel.readthedocs.io/en/stable/changelog/#v2162


5.4 (2023-08-24)
~~~~~~~~~~~~~~~~

- Improve documentation, adding ``parser.Displacements``, ``parser.scan`` and ``parser.split``
  examples (`issue #128`__)

  __ https://github.com/lelit/pglast/issues/128

- Fix issues `#129`__ and `#130`__ (merged from `version 4.4`__)

  __ https://github.com/lelit/pglast/issues/129
  __ https://github.com/lelit/pglast/issues/130
  __ `4.4 (2023-08-24)`_


5.3 (2023-08-05)
~~~~~~~~~~~~~~~~

- Update libpg_query to `15-4.2.3`__

  __ https://github.com/pganalyze/libpg_query/releases/tag/15-4.2.3


5.2 (2023-05-20)
~~~~~~~~~~~~~~~~

- Update libpg_query to `15-4.2.1`__

  __ https://github.com/pganalyze/libpg_query/releases/tag/15-4.2.1


5.1 (2023-02-28)
~~~~~~~~~~~~~~~~

- Merge `version 4.2`__ changes

  __ `4.2 (2023-02-27)`_


5.0 (2023-02-19)
~~~~~~~~~~~~~~~~

- No changes


5.0.dev1 (2023-02-11)
~~~~~~~~~~~~~~~~~~~~~

- Update libpg_query to `15-4.2.0`__

  __ https://github.com/pganalyze/libpg_query/releases/tag/15-4.2.0

~~~~~~~~~~~~~~~~~~~~
**Breaking changes**
~~~~~~~~~~~~~~~~~~~~

- Change the type of the ``ast.Float`` value from ``Decimal`` to ``str``

  Using a ``Decimal`` implies potential differences in the representation of floating numbers,
  and already caused issues (`#91`__ and `#100`__) in the past, making it impossible to render,
  say, ``SELECT 0.0e1``, due to the fact that ``Decimal('0.0e1')`` resolves to
  ``Decimal('0')``.

  __ https://github.com/lelit/pglast/issues/91
  __ https://github.com/lelit/pglast/issues/100


5.0.dev0 (2022-12-19)
~~~~~~~~~~~~~~~~~~~~~

- No visible changes with respect to v4, apart from the support for new/revised syntaxes of
  `PostgreSQL 15`__

  __ https://www.postgresql.org/docs/15/release-15.html

~~~~~~~~~~~~~~~~~~~~
**Breaking changes**
~~~~~~~~~~~~~~~~~~~~

- Target PostgreSQL 15, thanks to libpg_query `15-4.0.0`__

  __ https://github.com/pganalyze/libpg_query/releases/tag/15-4.0.0


Version 4
#########

4.5 (unreleased)
~~~~~~~~~~~~~~~~

- Use `Cython 3.0.2`__

  __ https://github.com/cython/cython/blob/master/CHANGES.rst#302-2023-08-27


4.4 (2023-08-24)
~~~~~~~~~~~~~~~~

- Fix issues `#129`__ and `#130`__ (merged from `version 3.18`__)

  __ https://github.com/lelit/pglast/issues/129
  __ https://github.com/lelit/pglast/issues/130
  __ `3.18 (2023-08-24)`_


4.3 (2023-04-27)
~~~~~~~~~~~~~~~~

- Fix `serialization issue`__ when column's ``DEFAULT`` value is an expression

  __ https://github.com/pganalyze/libpg_query/issues/188


4.2 (2023-02-27)
~~~~~~~~~~~~~~~~

- Handle special syntax required by ``SET TIME ZONE INTERVAL '-08:00' hour to minute``

- Fix mistype mapping of raw C "long" and "double" attributes, that were decorated with the
  wrong Python type


4.1 (2022-12-19)
~~~~~~~~~~~~~~~~

- Fix serialization glitches introduced by “Avoid overly abundancy of parentheses in
  expressions” (to be precise, by this__ commit)

  __ https://github.com/lelit/pglast/commit/6cfe75eea80f9c9bec4ba467e7ec1ec0796020de


4.0 (2022-12-12)
~~~~~~~~~~~~~~~~

- Update libpg_query to final `14-3.0.0`__

  __ https://github.com/pganalyze/libpg_query/releases/tag/14-3.0.0


4.0.dev0 (2022-11-24)
~~~~~~~~~~~~~~~~~~~~~

- Update libpg_query to `14-3.0.0`__

  __ https://github.com/pganalyze/libpg_query/blob/14-latest/CHANGELOG.md#14-300---2022-11-17

- Avoid overly abundancy of parentheses in expressions

- Prefer ``SELECT a FROM b LIMIT ALL`` to ``... LIMIT NONE``

~~~~~~~~~~~~~~~~~~~~
**Breaking changes**
~~~~~~~~~~~~~~~~~~~~

- Target PostgreSQL 14

- The wrapper classes used in previous versions, implemented in ``pglast.node``, are gone: now
  everything works on top of the ``AST`` classes (`issue #80`__)

  __ https://github.com/lelit/pglast/issues/80

- The ``Ancestor`` class is not iterable anymore: it was an internal implementation facility,
  now moved to a ``_iter_members()`` method


Version 3
#########

3.18 (2023-08-24)
~~~~~~~~~~~~~~~~~

- Fix ``BooleanTest`` printer, enclosing expression within parens in more cases (`issue
  #129`__)

  __ https://github.com/lelit/pglast/issues/129

- Fix ``Constraint`` printer, avoiding repetition of "DEFERRABLE INITIALLY DEFERRED" on some
  kind of constraints (`issue #130`__)

  __ https://github.com/lelit/pglast/issues/130


3.17 (2022-11-04)
~~~~~~~~~~~~~~~~~

- Fix ``AlterSubscriptionStmt`` printer, handling "SET PUBLICATION" without options


3.16 (2022-11-03)
~~~~~~~~~~~~~~~~~

- Update libpg_query to `13-2.2.0`__

  __ https://github.com/pganalyze/libpg_query/blob/13-latest/CHANGELOG.md#13-220---2022-11-02


3.15 (2022-10-17)
~~~~~~~~~~~~~~~~~

- Produce Python 3.11 wheels (`PR #108`__), thanks to ``cibuildwheel`` 2.11.1__ and to Bastien
  Gandouet

  __ https://github.com/lelit/pglast/pull/108
  __ https://cibuildwheel.readthedocs.io/en/stable/changelog/#v2111


3.14 (2022-08-08)
~~~~~~~~~~~~~~~~~

- Harden the way ``Visitor`` handle modifications to the AST (`issue #107`__)

  __ https://github.com/lelit/pglast/issues/107


3.13 (2022-06-29)
~~~~~~~~~~~~~~~~~

- Update libpg_query to `13-2.1.2`__

  __ https://github.com/pganalyze/libpg_query/blob/13-latest/CHANGELOG.md#13-212---2022-06-28


3.12 (2022-06-19)
~~~~~~~~~~~~~~~~~

- Rewrite the implementation of the ``referenced_relations()`` function, that was flawed with
  regard to CTEs handling (`issue #106`__), thanks to Michal Charemza for providing his own
  version

  __ https://github.com/lelit/pglast/issues/106

- Improve ``WithClause`` printer indentation

- Fix minor whitespace related issues in a few printer functions


3.11 (2022-05-29)
~~~~~~~~~~~~~~~~~

- Fix the ``Visitor`` class, it was ignoring nodes nested in sub-lists

- Reduce the size of the generated parser by factoring out common code into helper functions


3.10 (2022-05-11)
~~~~~~~~~~~~~~~~~

- Update libpg_query to `13-2.1.1`__ (`PR #102`__), thanks to James Guthrie

  __ https://github.com/pganalyze/libpg_query/blob/13-latest/CHANGELOG.md#13-211---2022-05-03
  __ https://github.com/lelit/pglast/pull/102

- Produce `musllinux`__ wheels, thanks to ``cibuildwheel`` `2.5.0`__ (:PEP:`656` was actually
  introduced in `2.2.0`__)

  __ https://peps.python.org/pep-0656/
  __ https://cibuildwheel.readthedocs.io/en/stable/changelog/#v250
  __ https://cibuildwheel.readthedocs.io/en/stable/changelog/#v220


3.9 (2022-02-24)
~~~~~~~~~~~~~~~~

- Fix bug handling node containing a ``location`` field, e.g. ``CreateTableSpaceStmt`` (`issue
  #98`__)

  __ https://github.com/lelit/pglast/issues/98

- Properly handle dereferenced array expression (`issue #99`__)

  __ https://github.com/lelit/pglast/issues/99

- Avoid improper "floatification" of literal integers (`issue #100`__)

  __ https://github.com/lelit/pglast/issues/100


3.8 (2021-12-28)
~~~~~~~~~~~~~~~~

- Fix glitch in the AST extractor tool (`issue #97`__)

  __ https://github.com/lelit/pglast/issues/97

- Add Linux AArch64 wheel build support (`PR #95`__), thanks to odidev

  __ https://github.com/lelit/pglast/pull/95

- Fix type mismatch when using ``--remove-pg_catalog-from-functions`` (`PR #93`__), thanks
  to Boris Zentner

  __ https://github.com/lelit/pglast/pull/93/


3.7 (2021-10-13)
~~~~~~~~~~~~~~~~

- Update libpg_query to `13-2.1.0`__

  __ https://github.com/pganalyze/libpg_query/blob/13-latest/CHANGELOG.md#13-210---2021-10-12_


3.6 (2021-10-09)
~~~~~~~~~~~~~~~~

- Use latest libpg_query, to fix an error parsing ``PLpgSQL`` statements (`issue #88`__)

  __ https://github.com/lelit/pglast/issues/88


3.5 (2021-09-26)
~~~~~~~~~~~~~~~~

- Forward the ``special_functions`` option to substream, when concatenating items
  (`issue #89`__)

  __ https://github.com/lelit/pglast/issues/89

- Fix representation of floating point numbers without decimal digits (`issue #91`__)

  __ https://github.com/lelit/pglast/issues/91

- Produce Python 3.10 wheels, thanks to ``cibuildwheel`` 2.1.2

- Update libpg_query to `13-2.0.7`__

  __ https://github.com/pganalyze/libpg_query/blob/13-latest/CHANGELOG.md#13-207---2021-07-16_

- New option ``--remove-pg_catalog-from-functions`` on the command line tool (`PR #90`__), thanks
  to Boris Zentner

  __ https://github.com/lelit/pglast/pull/90/

- Implement more *special functions* (`PR #92`__), thanks to Boris Zentner

  __ https://github.com/lelit/pglast/pull/92/


3.4 (2021-08-21)
~~~~~~~~~~~~~~~~

- Fix another packaging issue, that prevented recompilation from the sdist ``.tar.gz`` (`issue
  #86`__), thanks to Christopher Brichford

  __ https://github.com/lelit/pglast/issues/82


3.3 (2021-07-04)
~~~~~~~~~~~~~~~~

- Update libpg_query to `13-2.0.6`__

  __ https://github.com/pganalyze/libpg_query/blob/13-latest/CHANGELOG.md#13-206---2021-06-29_


3.2 (2021-06-25)
~~~~~~~~~~~~~~~~

- Effectively include libpg_query's vendored sources (`issue #82`__)

  __ https://github.com/lelit/pglast/issues/82


3.1 (2021-06-25)
~~~~~~~~~~~~~~~~

- Fix packaging glitch (`issue #82`__)

  __ https://github.com/lelit/pglast/issues/82

- Build wheels also for macOS

- Update libpg_query to `13-2.0.5`__

  __ https://github.com/pganalyze/libpg_query/blob/13-latest/CHANGELOG.md#13-205---2021-06-24_


3.0 (2021-06-04)
~~~~~~~~~~~~~~~~

- Fix glitch in the ``RawStream``, avoiding spurious space after an open parenthesis

- Improve the ``Visitor`` class, to make it easier altering the original tree

- Properly handle nested lists in the serialization of AST Node


3.0.dev2 (2021-05-22)
~~~~~~~~~~~~~~~~~~~~~

- Fix bug in ``CreateStmt`` printer (`issue #79`__)

  __ https://github.com/lelit/pglast/issues/79

- Make it possible to pass also concrete ``ast.Node``\ s to ``RawStream```

~~~~~~~~~~~~~~~~~~~~
**Breaking changes**
~~~~~~~~~~~~~~~~~~~~

- To reduce confusion, the ``printer`` module has been removed: print-specific stuff is now
  directly exposed by the ``printers`` subpackage while serialization classes are now in the
  new ``stream`` module

- The default value for the ``safety_belt`` option of the ``printify()`` function is now
  ``False``


3.0.dev1 (2021-05-16)
~~~~~~~~~~~~~~~~~~~~~

- Fix ``AT_SetIdentity``, ``AT_EnableReplicaTrig`` and ``AlterSubscriptionStmt`` printers

- Improve ``AlterTSConfigType`` and ``IntoClause`` printers

- New generic "visitor pattern" (`issue #51`__) exemplified by a new
  ``referenced_relations()`` function (`issue #66`__)

  __ https://github.com/lelit/pglast/issues/51
  __ https://github.com/lelit/pglast/issues/66

- Refine printing of SQL comments

- Implement ``AlterExtensionStmt`` printer


3.0.dev0 (2021-05-03)
~~~~~~~~~~~~~~~~~~~~~

- Expose the new ``pg_query_scan()`` function as ``parser.scan()``

- Expose the ``pg_query_parse()`` function as ``parser.parse_sql_json()``

- Expose the new ``pg_query_parse_protobuf()`` function as ``parser.parse_sql_protobuf()``

- Expose the new ``pg_query_deparse_protobuf()`` function as ``parser.deparse_protobuf()``

- Honor the ``catalogname`` of a ``RangeVar`` if present (`issue #71`__)

  __ https://github.com/lelit/pglast/issues/71

- Cover almost all ``SQL`` statements, testing against the whole ``PostgreSQL`` `regression
  suite`__ (`issue #68`__, `PR #72`__ and `PR #77`__), thanks to Ronan Dunklau and Hong Cheng

  __ https://github.com/pganalyze/libpg_query/tree/13-latest/test/sql/postgres_regress_
  __ https://github.com/lelit/pglast/issues/68
  __ https://github.com/lelit/pglast/pull/72
  __ https://github.com/lelit/pglast/pull/77

- New rudimentary support for the `preserve comments` feature (`issue #23`__)

  __ https://github.com/lelit/pglast/issues/23

~~~~~~~~~~~~~~~~~~~~
**Breaking changes**
~~~~~~~~~~~~~~~~~~~~

- Target PostgreSQL 13

- The ``pglast.parser`` module exposes all ``libpg_query`` entry points, even the new
  ``pg_query_deparse_protobuf()`` function that is basically equivalent to
  ``RawStream``\ -based printer

- The ``split()`` function is now based on the lower level ``pg_query_split_with_xxx()``
  functions

- The ``parse_sql()`` function returns native Python objects, not a ``JSON`` string as before:
  all PG *nodes* are now represented by subclasses of ``pglast.ast.Node``, without exception,
  even ``Expr`` and ``Value`` are there. The latter impacts on ``pglast.node.Scalar``: for
  example it now may contains a ``ast.Integer`` instance instead of a Python ``int``

- The ``pgpp --parse-tree`` output is a `pprint`__ represention of the ``AST``, not a ``JSON``
  string as before

  __ https://docs.python.org/3.9/library/pprint.html#pprint.pprint

- The ``ParseError`` exception does not expose the ``location`` as an instance member anymore,
  although its still there, as the second argument (ie ``.args[1]``); furthermore, its value
  now corresponds to the index in the original Unicode string, instead of the offset in the
  ``UTF-8`` representation passed to the underlying C function


Version 2
#########

2.0.dev3 (2021-02-20)
~~~~~~~~~~~~~~~~~~~~~

- Handle ``INCLUDE`` clause in ``IndexStmt`` (`PR #67`__), thanks to Ronan Dunklau

  __ https://github.com/lelit/pglast/pull/67


2.0.dev2 (2020-10-24)
~~~~~~~~~~~~~~~~~~~~~

- Merge new ``fingerprint`` functionality from ``v1`` (i.e. ``master``) branch


2.0.dev1 (2020-09-26)
~~~~~~~~~~~~~~~~~~~~~

- Require Python 3.6 or greater

- Handle ``ALTER TYPE .. RENAME VALUE`` in ``AlterEnumStmt`` (`PR #52`__), thanks to Ronan
  Dunklau

  __ https://github.com/lelit/pglast/pull/52

- Add support for Create / Alter / Drop PROCEDURE (`PR #48`__), thanks to Ronan Dunklau

  __ https://github.com/lelit/pglast/pull/48

- Use Ronan's fork__ of libpg_query, targeting PostgreSQL 12.1 (`PR #36`__)

  __ https://github.com/rdunklau/libpg_query
  __ https://github.com/lelit/pglast/pull/36

- Change get_postgresql_version() to return a ``(major, minor)`` tuple (`issue #38`__)

  __ https://github.com/lelit/pglast/issues/38

- Handle ``ALTER TABLE ... ALTER COLUMN ... SET STORAGE ...``

- Handle PG12 materialized CTEs (`issue #57`)

- Support column numbers in ``ALTER INDEX`` (`PR #58`__), thanks to Ronan Dunklau

  __ https://github.com/lelit/pglast/pull/58

- Handle ``SET LOGGED`` and ``SET UNLOGGED`` in ``ALTER TABLE`` (`PR #59`__), thanks to Ronan
  Dunklau

  __ https://github.com/lelit/pglast/pull/59

- Handle ``ALTER TYPE ... RENAME`` (`PR #62`__), , thanks to Ronan
  Dunklau

  __ https://github.com/lelit/pglast/pull/62


Version 1
#########

1.18 (2021-06-01)
~~~~~~~~~~~~~~~~~

- Fix exclusion constraint printer (`issue #81`__)

  __ https://github.com/lelit/pglast/issues/81


1.17 (2021-02-20)
~~~~~~~~~~~~~~~~~

- Fix the generic case in the ``RenameStmt`` printer


1.16 (2021-02-20)
~~~~~~~~~~~~~~~~~

- Promote to the *stable* state

- Move the job of building and uploading binary wheels from TravisCI to GitHub Actions


1.15 (2021-02-19)
~~~~~~~~~~~~~~~~~

- Fix ``IF EXISTS`` variant of ``RenameStmt`` printer (`PR #70`__), thanks to Jonathan
  Mortensen

  __ https://github.com/lelit/pglast/pull/70

- Update libpg_query to 10-1.0.5


1.14 (2020-10-24)
~~~~~~~~~~~~~~~~~

- Produce Python 3.9 wheels, thanks to ``cibuildwheel`` 1.6.3

- Expose the ``libpg_query``'s `fingerprint`__ functionality (`PR #64`__), thanks to Yiming
  Wang

  __ https://github.com/lfittl/libpg_query/wiki/Fingerprinting
  __ https://github.com/lelit/pglast/pull/64


1.13 (2020-09-26)
~~~~~~~~~~~~~~~~~

- Handle ``SELECT FROM foo``


1.12 (2020-06-08)
~~~~~~~~~~~~~~~~~

- Double quote column names in the ``TYPE_FUNC_NAME_KEYWORDS`` set (`issue #55`__)

  __ https://github.com/lelit/pglast/issues/55

- Possibly wrap ``SELECT`` in ``UNION``/``INTERSECT`` between parens, when needed
  (`issue #55`__)

  __ https://github.com/lelit/pglast/issues/55


1.11 (2020-05-08)
~~~~~~~~~~~~~~~~~

- Fix ``A_Expr`` printer, when ``lexpr`` is missing (`PR #54`__), thanks to Aiham

  __ https://github.com/lelit/pglast/pull/54

- Support ``DISABLE ROW LEVEL SECURITY`` in ``AlterTableCmd`` (`PR #49`__), thanks to Ronan
  Dunklau

  __ https://github.com/lelit/pglast/pull/49

- Implement ``CreateOpClassStmt`` printer (`PR #47`__), thanks to Ronan Dunklau

  __ https://github.com/lelit/pglast/pull/47


1.10 (2020-01-25)
~~~~~~~~~~~~~~~~~

- Fix collation name printer (`PR #44`__), thanks to Ronan Dunklau

  __ https://github.com/lelit/pglast/pull/44

- Implement ``CreatePLangStmt`` printer (`PR #42`__), thanks to Bennie Swart

  __ https://github.com/lelit/pglast/pull/42

- Fix privileges printer (`PR #41`__), thanks to Bennie Swart

  __ https://github.com/lelit/pglast/pull/41

- Handle ``TRUNCATE`` event in ``CreateTrigStmt`` printer (`PR #40`__), thanks to Bennie Swart

  __ https://github.com/lelit/pglast/pull/40

- Fix function body dollar quoting (`PR #39`__), thanks to Bennie Swart

  __ https://github.com/lelit/pglast/pull/39


1.9 (2019-12-20)
~~~~~~~~~~~~~~~~

- Prettier ``INSERT`` representation


1.8 (2019-12-07)
~~~~~~~~~~~~~~~~

- Prettier ``CASE`` representation

- New option to emit a semicolon after the last statement (`issue #24`__)

  __ https://github.com/lelit/pglast/issues/24


1.7 (2019-12-01)
~~~~~~~~~~~~~~~~

- Implement ``NotifyStmt`` printer

- Implement ``RuleStmt`` printer, thanks to Gavin M. Roy for his `PR #28`__

  __ https://github.com/lelit/pglast/pull/28

- Fix ``RenameStmt``, properly handling object name

- Produce Python 3.8 wheels, thanks to `cibuildwheel`__ 1.0.0

  __ https://github.com/joerick/cibuildwheel

- Support ``ALTER TABLE RENAME CONSTRAINT`` (`PR #35`__), thanks to Ronan Dunklau

  __ https://github.com/lelit/pglast/pull/35


1.6 (2019-09-04)
~~~~~~~~~~~~~~~~

- Fix issue with boolean expressions precedence (`issue #29`__)

  __ https://github.com/lelit/pglast/issues/29

- Implement ``BitString`` printer

- Support ``LEAKPROOF`` option (`PR #31`__), thanks to Ronan Dunklau

  __ https://github.com/lelit/pglast/pull/31

- Support ``DEFERRABLE INITIALLY DEFERRED`` option (`PR #32`__), thanks to Ronan Dunklau

  __ https://github.com/lelit/pglast/pull/32


1.5 (2019-06-04)
~~~~~~~~~~~~~~~~

- Fix issue with ``RETURNS SETOF`` functions, a more general solution than the one proposed by
  Ronan Dunklau (`PR #22`__)

  __ https://github.com/lelit/pglast/pull/22

- Allow more than one empty line between statements (`PR #26`__), thanks to apnewberry

  __ https://github.com/lelit/pglast/pull/26


1.4 (2019-04-06)
~~~~~~~~~~~~~~~~

- Fix wrap of trigger's WHEN expression (`issue #18`__)

  __ https://github.com/lelit/pglast/issues/18

- Support for variadic functions (`PR #19`__), thanks to Ronan Dunklau

  __ https://github.com/lelit/pglast/pull/19

- Support ORDER / LIMIT / OFFSET for set operations (`PR #20`__), thanks to Ronan Dunklau

  __ https://github.com/lelit/pglast/pull/20

- Implement ``ConstraintsSetStmt`` and improve ``VariableSetStmt`` printers


1.3 (2019-03-28)
~~~~~~~~~~~~~~~~

- Support ``CROSS JOIN`` and timezone modifiers on time and timestamp datatypes (`PR #15`__),
  thanks to Ronan Dunklau

  __ https://github.com/lelit/pglast/pull/15

- Many new printers and several enhancements (`PR #14`__), thanks to Ronan Dunklau

  __ https://github.com/lelit/pglast/pull/14

- Expose the package version as pglast.__version__ (`issue #12`__)

  __ https://github.com/lelit/pglast/issues/12


1.2 (2019-02-13)
~~~~~~~~~~~~~~~~

- Implement new `split()` function (see `PR #10`__)

  __ https://github.com/lelit/pglast/pull/10

- Implement ``BooleanTest`` printer (`issue #11`__)

  __ https://github.com/lelit/pglast/issues/11


1.1 (2018-07-20)
~~~~~~~~~~~~~~~~

- No visible changes, but now PyPI carries binary wheels for Python 3.7.


1.0 (2018-06-16)
~~~~~~~~~~~~~~~~

.. important:: The name of the package has been changed from ``pg_query`` to ``pglast``, to
               satisfy the request made by the author of ``libpg_query`` in `issue #9`__.

               This affects both the main repository on GitHub, that from now on is
               ``https://github.com/lelit/pglast``, and the ReadTheDocs project that hosts the
               documentation, ``http://pglast.readthedocs.io/en/latest/``.

               I'm sorry for any inconvenience this may cause.

__ https://github.com/lelit/pglast/issues/9


0.28 (2018-06-06)
~~~~~~~~~~~~~~~~~

- Update libpg_query to 10-1.0.2

- Support the '?'-style parameter placeholder variant allowed by libpg_query (details__)

__ https://github.com/lfittl/libpg_query/issues/45


0.27 (2018-04-15)
~~~~~~~~~~~~~~~~~

- Prettier JOINs representation, aligning them with the starting relation


0.26 (2018-04-03)
~~~~~~~~~~~~~~~~~

- Fix cosmetic issue with ANY() and ALL()


0.25 (2018-03-31)
~~~~~~~~~~~~~~~~~

- Fix issue in the safety belt check performed by ``pgpp`` (`issue #4`__)

__ https://github.com/lelit/pglast/issues/4


0.24 (2018-03-02)
~~~~~~~~~~~~~~~~~

- Implement ``Null`` printer


0.23 (2017-12-28)
~~~~~~~~~~~~~~~~~

- Implement some other DDL statements printers

- New alternative style to print *comma-separated-values* lists, activated by a new
  ``--comma-at-eoln`` option on ``pgpp``


0.22 (2017-12-03)
~~~~~~~~~~~~~~~~~

- Implement ``TransactionStmt`` and almost all ``DROP xxx`` printers


0.21 (2017-11-22)
~~~~~~~~~~~~~~~~~

- Implement ``NamedArgExpr`` printer

- New alternative printers for a set of *special functions*, activated by a new
  ``--special-functions`` option on ``pgpp`` (`issue #2`__)

__ https://github.com/lelit/pglast/issues/2


0.20 (2017-11-21)
~~~~~~~~~~~~~~~~~

- Handle special de-reference (``A_Indirection``) cases


0.19 (2017-11-16)
~~~~~~~~~~~~~~~~~

- Fix serialization of column labels containing double quotes

- Fix corner issues surfaced implementing some more DDL statement printers


0.18 (2017-11-14)
~~~~~~~~~~~~~~~~~

- Fix endless loop due to sloppy conversion of command line option

- Install the command line tool as ``pgpp``


0.17 (2017-11-12)
~~~~~~~~~~~~~~~~~

- Rename printers.sql to printers.dml (**backward incompatibility**)

- List printer functions in the documentation, referencing the definition of related node type

- Fix inconsistent spacing in JOIN condition inside a nested expression

- Fix representation of unbound arrays

- Fix representation of ``interval`` data type

- Initial support for DDL statements

- Fix representation of string literals containing single quotes


0.16 (2017-10-31)
~~~~~~~~~~~~~~~~~

- Update libpg_query to 10-1.0.0


0.15 (2017-10-12)
~~~~~~~~~~~~~~~~~

- Fix indentation of boolean expressions in SELECT's targets (`issue #3`__)

__ https://github.com/lelit/pglast/issues/3


0.14 (2017-10-09)
~~~~~~~~~~~~~~~~~

- Update to latest libpg_query's 10-latest branch, targeting PostgreSQL 10.0 final


0.13 (2017-09-17)
~~~~~~~~~~~~~~~~~

- Fix representation of subselects requiring surrounding parens


0.12 (2017-08-22)
~~~~~~~~~~~~~~~~~

- New option ``--version`` on the command line tool

- Better enums documentation

- Release the GIL while calling libpg_query functions


0.11 (2017-08-11)
~~~~~~~~~~~~~~~~~

- Nicer indentation for JOINs, making OUTER JOINs stand out

- Minor tweaks to lists rendering, with less spurious whitespaces

- New option ``--no-location`` on the command line tool


0.10 (2017-08-11)
~~~~~~~~~~~~~~~~~

- Support Python 3.4 and Python 3.5 as well as Python 3.6


0.9 (2017-08-10)
~~~~~~~~~~~~~~~~

- Fix spacing before the $ character

- Handle type modifiers

- New option ``--plpgsql`` on the command line tool, just for fun


0.8 (2017-08-10)
~~~~~~~~~~~~~~~~

- Add enums subpackages to the documentation with references to their related headers

- New ``compact_lists_margin`` option to produce a more compact representation when possible
  (see `issue #1`__)

__ https://github.com/lelit/pglast/issues/1


0.7 (2017-08-10)
~~~~~~~~~~~~~~~~

- Fix sdist including the Sphinx documentation


0.6 (2017-08-10)
~~~~~~~~~~~~~~~~

- New option ``--parse-tree`` on the command line tool to show just the parse tree

- Sphinx documentation, available online


0.5 (2017-08-09)
~~~~~~~~~~~~~~~~

- Handle some more cases when a name must be double-quoted

- Complete the serialization of the WindowDef node, handling its frame options


0.4 (2017-08-09)
~~~~~~~~~~~~~~~~

- Expose the actual PostgreSQL version the underlying libpg_query libray is built on thru a new
  ``get_postgresql_version()`` function

- New option `safety_belt` for the ``prettify()`` function, to protect the innocents

- Handle serialization of ``CoalesceExpr`` and ``MinMaxExpr``


0.3 (2017-08-07)
~~~~~~~~~~~~~~~~

- Handle serialization of ``ParamRef`` nodes

- Expose a ``prettify()`` helper function


0.2 (2017-08-07)
~~~~~~~~~~~~~~~~

- Test coverage at 99%

- First attempt at automatic wheel upload to PyPI, let's see...


0.1 (2017-08-07)
~~~~~~~~~~~~~~~~

- First release ("Hi daddy!", as my soul would tag it)
