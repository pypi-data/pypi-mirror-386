0.6.3
=====

This is a bug fix release.

Breaking changes
----------------

This release is not believed to introduce any backwards-incompatible changes.

Merges
------

+ `ligo!27 <https://git.ligo.org/asimov/pipelines/gwdata/-/merge_requests/27>`_: Fixes an issue with scitokens authentication when downloading frame files.

0.6.2
=====

This is a bug fix release.

Breaking changes
----------------

This release is not believed to introduce any backwards-incompatible changes.

Merges
------

+ `ligo!25 <https://git.ligo.org/asimov/pipelines/gwdata/-/merge_requests/25>`_: Fixes an error where the frame files from calibration are passed from this task.

0.6.1
=====

This is a bug fix release.

Breaking changes
----------------

This release is not believed to introduce any backwards-incompatible changes.

Merges
------

+ `ligo!24 <https://git.ligo.org/asimov/pipelines/gwdata/-/merge_requests/24>`_: Fixes an error related to htcondor authentication.



0.6.0
=====

This is a feature release which introduces new functionality.

Breaking changes
----------------

This release is not believed to introduce any backwards-incompatible changes.

New Features
------------

+ Ability to read calibration uncertainty data from GW Frame files in addition to ascii text files. At present this is only supported for Virgo as LIGO do not distribute data in this format.
+ Ability to download frames which are behind authentication using scitokens.

Merges
------

+ `ligo!20 <https://git.ligo.org/asimov/pipelines/gwdata/-/merge_requests/20>`_: Updated the mechanism by which asimov-gwdata finds and downloads frame files which require authentication.
+ `ligo!21 <https://git.ligo.org/asimov/pipelines/gwdata/-/merge_requests/21>`_: Created a workflow to extract calibration uncertainty envelopes from frame files.

0.5.0
=====

This is a feature release which introduces new functionality.

Breaking changes
----------------

This release is not believed to introduce any backwards-incompatible changes.


New feature
-----------

+ Ability to read PSD files from PESummary metafiles (e.g. existing data releases) and turn these into ASCII or XML format representations as required by parameter estimation pipelines.

Merges
------

+ `ligo!15 <https://git.ligo.org/asimov/pipelines/gwdata/-/merge_requests/15>`_: Allows PSD files to be read from PESummary metafiles and converted for use in pipelines.
+ `ligo!17 <https://git.ligo.org/asimov/pipelines/gwdata/-/merge_requests/17>`_: Corrected the dates of O4 observing runs.
+ `ligo!18 <https://git.ligo.org/asimov/pipelines/gwdata/-/merge_requests/18>`_: Adds provisional support for reading calibration uncertainty envelopes from frame files.

0.4.1
=====

This is a bug fix release.

Breaking changes
----------------

This release is not believed to introduce any backwards-incompatible changes.

Merges
------

+ `ligo!16 <https://git.ligo.org/asimov/pipelines/gwdata/-/merge_requests/16>`_: Allows units to be added to memory and disk requests, and these to be specified in blueprints.

0.4.0
=====

This is a feature release which introduces new functionality.

Breaking changes
-----------------

This release is not believed to introduce any backwards-incompatible changes.

New feature
-----------

+ Ability to specify the calibration version for multiple interferometers independently (e.g. specifying v1 for L1 and v0 for H1)

Merges
------

+ `ligo!13 <https://git.ligo.org/asimov/pipelines/gwdata/-/merge_requests/13>`_: Allows calibration version to be specified by dictionary.


0.3.4
=====


This is a minor bug-fix release, and does not introduce new functionality.

Breaking changes
----------------

This release is not believed to introduce any backwards-incompatible changes.

Merges
------

+ `ligo!12<https://git.ligo.org/asimov/pipelines/gwdata/-/merge_requests/12>`_: Fixes a mistake in the calibration file path.


0.3.3
=====

This is a minor bug-fix release, and does not introduce new functionality.

Breaking changes
----------------

This release is not believed to introduce any backwards-incompatible changes.

Merges
------

+ `ligo!10<https://git.ligo.org/asimov/pipelines/gwdata/-/merge_requests/10>`_: This code fixes issues with the location of calibration uncertainty envelopes on IGWN resources.




0.3.2
=====

This is a minor bug-fix release, and does not introduce new functionality.

Breaking changes
----------------

This release is not believed to introduce any backwards-incompatible changes.

Fixes
-----

This release reverts the removal of cache file generation when frame files are downloaded.

0.3.1
=====

This is a minor bug-fix release, and does not introduce new functionality.

Breaking changes
----------------

This release is not believed to introduce any backwards-incompatible changes.

Merges
------

`ligo!8 <https://git.ligo.org/asimov/pipelines/gwdata/-/merge_requests/8>`_: Removes an extraneous print to stdout.


0.3.0
=====

This is a feature release which introduces new functionality.

Breaking changes
-----------------

This release is not believed to introduce any backwards-incompatible changes.

Merges
------

+ `ligo!6 <https://git.ligo.org/asimov/pipelines/gwdata/-/merge_requests/6>`_: Allows the use of the CBCFlow IllustrativeResult when searching for posteriors.
+ `ligo!5 <https://git.ligo.org/asimov/pipelines/gwdata/-/merge_requests/5>`_: Allows the base directory to be specified for the calibration file search.

0.2.0
=====

This is a feature release which introduces new functionality to help facilitate LIGO parameter estimation analyses conducted on the LIGO Data Grid.

Breaking changes
----------------

This release is not believed to introduce any backwards-incompatible changes.

Merges
------
+ `ligo!3 <https://git.ligo.org/asimov/pipelines/gwdata/-/merge_requests/3>`_: Introduces the ability to find calibration files on the Caltech cluster.


