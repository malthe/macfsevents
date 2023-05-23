Changelog
=========

0.8.4 (2023-05-23)
------------------

- Fix test compatibility with newer Python 3.

0.8.3 (2023-05-23)
------------------

- Fix brown-bag release.

0.8.2 (2023-05-22)
------------------

- Fix file mask string method missing return value (#43).

0.8.1 (2018-02-21)
------------------

- Fix brown-bag release.

0.8 (2018-02-21)
----------------

- Fix bug that could lead to a segfault.
  [ElonKim]

0.7 (2015-12-18)
----------------

- Remove slots definition.

0.6 (2015-12-06)
----------------

- Fixed mask serialization on Python 3.


0.5 (2015-12-02)
----------------

- Fixed thread handling issue which might result in a segmentation
  error.

- Event IDs can be configure in the stream.

- Added support for passing in create flags, latency and "since fields"
  to the Stream.

- Added flags translation facility.

- Supports UTF-8-MAC(NFD).


0.4 (2014-10-23)
----------------

- Do not use 'Distribute'. It's been deprecated


0.3 (2013-01-21)
------------------

- Added compatibility with Python 3. Note that Python 2.7 or better is
  now required.

- Fixed test suite on with 10.8. The event masks reported on this
  platform are non-trivial which is a change from previous versions.

0.2.8 (2012-06-09)
------------------

Bugfixes:

- Fix recursive snapshot.
  [thomasst]

- Use os.lstat instead of os.stat to correctly detect symlinks.
  [thomasst]

0.2.7 (2012-05-29)
------------------

- Added support for IN_ATTRIB.
  [thomasst]

0.2.6 (2012-03-17)
------------------

- Fixed compilation problem on newer platforms.
  [nsfmc]

0.2.5 (2012-02-01)
------------------

- Ignore files that don't exist while recursing.
  [bobveznat]

0.2.4 (2010-12-06)
------------------

- Prevent crashes on recursive folder delete and multiple folder add.
  [totolici].

0.2.3 (2010-07-27)
------------------

- Fixed broken release.

0.2.2 (2010-07-26)
------------------

- Python 2.4 compatibility [howitz]

- Fixed an issue where the addition of a new directory would crash the
  program when using file event monitoring [andymacp].

0.2.1 (2010-04-27)
------------------

- Fixed an import issue [andymacp].

0.2 (2010-04-26)
----------------

- Fixed issue where existing directories would be reported along with
  a newly created one [marcboeker].

- Added support for file event monitoring.

- Fixed reference counting bug which could result in a segmentation
  fault.

0.1 (2009-11-27)
----------------

- Initial public release.
