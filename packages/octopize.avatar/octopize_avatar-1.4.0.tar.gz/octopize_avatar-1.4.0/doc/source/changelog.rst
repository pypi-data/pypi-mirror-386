Changelog
=========

NEXT RELEASE
------------

1.4.0 - 2025/10/22
------------------

.. _section-1:

1.3.0 - 2025/10/14
------------------

.. _section-2:

1.2.0 - 2025/10/08
------------------

.. _section-3:

1.1.0 - 2025/09/23
------------------

.. _section-4:

1.0.10 - 2025/09/15
-------------------

.. _section-5:

1.0.9 - 2025/08/26
------------------

-  BREAKING: deprecated ratio and distance thresholds

.. _section-6:

1.0.8 - 2025/07/25
------------------

-  feat : add endpoint to render plots

.. _section-7:

1.0.7 - 2025/07/16
------------------

-  refactor: improve results download
-  fix: compliance with the new api version

.. _section-8:

1.0.6 - 2025/07/03
------------------

-  fix: compliance with the new api version

.. _section-9:

1.0.5 - 2025/05/26
------------------

-  fix: use specific avatar-yaml version

.. _section-10:

1.0.4 - 2025/05/20
------------------

-  feat: support generating multitable reports
-  feat: add advisor functionality

.. _section-11:

1.0.3 - 2025/04/30
------------------

-  feat: make mandatory a set_name in the runner

.. _section-12:

1.0.2 - 2025/04/29
------------------

-  BREAKING: feat: Release of the python client for the API 1.0.0 🚀 🥳.
-  feat: New documentation of the python client.

.. _section-13:

0.15.0 - 2024/08/26
-------------------

-  feat: add tutorial on job management
-  feat: add GeolocationNormalizationProcessor
-  chore: remove timeout to avoid re-POST
-  BREAKING: chore: remove all batch from client side

.. _section-14:

0.14.0 - 2024/08/07
-------------------

-  BREAKING: remove deprecated persistance_job_id
-  BREAKING: remove deprecated to_categorical_threshold

.. _section-15:

0.13.0 - 2024/07/24
-------------------

-  BREAKING: send the total size of the stream at the start of the
   stream
-  Remove dependency on libmagic

.. _section-16:

0.12.0 - 2024/07/05
-------------------

-  BREAKING: refactor: Dataset.columns is required

.. _section-17:

0.11.0 - 2024/07/01
-------------------

-  BREAKING: fix dataset upload

.. _section-18:

0.10.0 - 2024/06/18
-------------------

-  BREAKING: fix dataset upload

.. _section-19:

0.9.2 - 2024/06/11
------------------

-  feat: retry any kind of network error

.. _section-20:

0.9.1 - 2024/06/10
------------------

-  feat: retry on DNS resolution errors

.. _section-21:

0.9.0 - 2024/06/06
------------------

-  feat: add categorical hidden rate variable to privacy parameters
-  BREAKING refactor: categorical hidden rate is optional in
   PrivacyMetrics

.. _section-22:

0.8.0 - 2024/06/05
------------------

-  BREAKING feat: add linkage methods to TableLink and make linear sum
   assignment the default method.
-  BREAKING refactor: remove ``ExcludeCategoricalParameters`` and
   replace it by ``ExcludeVariablesParameters``

.. _section-23:

0.7.4 - 2024/05/15
------------------

-  Add advice for choosing avatarization parameters
-  Speed up projector load and save
-  Remove dataset_id from get_variable_contributions
-  Add size agnostic bi-directional arrow/parquet streaming utilities

.. _section-24:

0.7.3 - 2024/04/29
------------------

-  Allow passing filetype in datasets.download_dataset and
   pandas_integration.download_dataframe to change the format of the
   retrieved data
-  Deprecate datasets.download_dataset_as_stream and
   datasets.create_dataset_from_stream
-  Deprecate the ‘should_stream’ argument from
   pandas_integration.upload_dataframe and
   pandas_integration.download_dataframe
-  Deprecate ‘request’ argument from datasets.create_dataset in favor of
   ‘source’ argument
-  Add ‘destination’ argument to datasets.download_dataset

.. _section-25:

0.7.2 - 2024/04/12
------------------

-  fix: remove retry logic around Job.last_updated_at

.. _section-26:

0.7.1 - 2024/04/11
------------------

-  feat: overhaul client architecture

.. _section-27:

0.7.0- 2024/04/05
-----------------

-  fix: change shuffle multi-table process to return the right dataframe
-  fix: return metric parameter error to user
-  feat: return error to user if data contains ninf
-  feat: improve multi-table anonymization quality (utility)
-  feat: verify compatibility with server on client init
-  feat: add dataset name in the multitable privacy metrics
-  feat: create privacy geolocation assessment feature
-  refactor: add custom methods for Datasets
-  refactor: change seed place for avatarization and metrics job
   parameters to guarantee reproducibility

.. _section-28:

0.6.2
-----

-  feat: add should_verify_ssl to ApiClient to bypass
-  refactor: revert to AvatarizationParameters.dataset_id being required
-  feat: add pydantic constraints to privacy metrics fields
-  feat: add multi table avatarization and privacy metrics jobs
-  feat: add ‘name’ keyword argument to create_dataset

.. _section-29:

0.6.1
-----

-  feat: enable parquet format for dataset upload
-  feat: use pydantic v2
-  feat: add InterRecordBoundedCumulatedDifferenceProcessor
-  fix: max file size error message

.. _section-30:

0.6.0
-----

-  feat: detect potential id columns
-  feat: add created_at, kind to Jobs
-  feat: add time series

.. _section-31:

0.5.2
-----

-  feat: add InterRecordBoundedRangeDifferenceProcessor

.. _section-32:

0.5.1
-----

-  fix: compatibility mapping due to breaking change

BREAKING CHANGE
~~~~~~~~~~~~~~~

-  remove broken endpoint ``/projections``

.. _section-33:

0.4.0
-----

-  feat: Limit the size of ``nb_days`` in ``find_all_jobs_by_user``
-  feat: implement anonymization, metrics and report generation as a
   batch
-  feat: apply license check only during anonymization, not during
   upload
-  fix: Prevent user from uploaded a dataframe with ``bool`` dtype
-  fix: Correctly handle error on missing job
-  fix: standardize metrics in the anonymization report

.. _breaking-change-1:

BREAKING CHANGE
~~~~~~~~~~~~~~~

-  remove ``patch`` parameter from ``create_dataset``

.. _section-34:

0.3.3
-----

-  Add ``should_stream`` parameter to ``{upload,download}_dataframe``
   and ``{create,download}_dataset``. This should prevent issues with
   timeouts during upload and download, as well as lessen the load on
   the server for big files.
-  Add ``jobs.cancel_job`` method to cancel a job
-  Add ``use_categorical_reduction`` parameter
-  Add maximum password length of 128 characters
-  Add report creation without avatarization job
-  Remove re-raise of JSONDecodeError
-  Add commit hash to generated files
-  Fix: verify that ``known_variables`` and ``target`` are known when
   launching a privacy metrics job
-  Fix: call analyze_dataset only once in notebooks

.. _section-35:

0.3.2
-----

-  catch JSONDecodeError and re-raise with more info

.. _section-36:

0.3.1
-----

-  add ``should_verify_ssl`` to allow usage of self-signed certificate
   on server side
-  add ``InterRecordCumulatedDifferenceProcessor``
-  add ``InterRecordRangeDifferenceProcessor``
-  improve logging and error handling in avatarization_pipeline to
   resume easier on failure

.. _section-37:

0.3.0
-----

BREAKING
~~~~~~~~

-  ``ReportCreate`` now takes required ``avatarization_job_id``,
   ``signal_job_id``, and ``privacy_job_id`` parameters
-  Mark ``AvatarizationParameters.to_categorical_threshold`` as
   deprecated
-  ``client.jobs.create_avatarization_job`` behaviour does not compute
   metrics anymore. Use ``client.jobs.create_full_avatarization_job``
   instead
-  ``AvatarizationResult`` now has ``signal_metrics`` and
   ``privacy_metrics`` properties as ``Optional``
-  Verify dataset size on upload. This will prevent you from uploading a
   dataset that is too big to handle for the server
-  The ``direct_match_protection`` privacy metrics got renamed to
   ``column_direct_match_protection``
-  ``dataset_id`` from ``AvatarizationParameters`` is now required
-  ``dataset_id`` from ``AvatarizationJob``,\ ``SignalMetricsJob`` and
   ``PrivacyMetricsJob`` got removed
-  ``client.users.get_user`` now accepts an ``id`` rather than a
   ``username``
-  ``SignalMetricsParameters.job_id`` got renamed to
   ``persistance_job_id``
-  ``CreateUser`` does not take ``is_email_confirmed`` as parameter
   anymore
-  Processors get imported from ``avatars.processors`` instead of
   ``avatars.processor.{processor_name}``

   -  Example:
      ``from avatars.processors.expected_mean import ExpectedMeanProcessor``
      becomes ``from avatars.processors import ExpectedMeanProcessor``

Others
~~~~~~

-  feat: add more metrics and graphs to report
-  feat: add ``client.compatibility.is_client_compatible`` to verify
   client-server compatibility
-  feat: enable to avatarize without calculating metrics using
   ``client.jobs.create_avatarization_job``
-  feat: add ``nb_dimensions`` property to ``Dataset``
-  feat: add ``User`` object
-  feat: use ``patch`` in ``client.datasets.create_dataset`` to patch
   dataset columns on upload
-  feat: add ``correlation_protection_rate``, ``inference_continuous``,
   ``inference_categorical``, ``row_direct_match_protection`` and
   ``closest_rate`` privacy metrics
-  feat: add ``known_variables``, ``target``,
   ``closest_rate_percentage_threshold``, and
   ``closest_rate_ratio_threshold`` to ``PrivacyMetricsParameters``
-  docs: add multiple versions of the documentation
-  feat: each user now belongs to an organization and gets a new field:
   ``organization_id``
-  fix: fixed a bug where computing privacy metrics with distinct
   missing values was impossible

.. _section-38:

0.2.2
-----

-  Improve type hints of the method
-  Update tutorial notebooks with smaller datasets
-  Fix bugs in tutorial notebooks
-  Improve error message when the call to the API times out
-  Add ``jobs.find_all_jobs_by_user``
-  Add two new privacy metrics: ``direct_match_protection`` and
   ``categorical_hidden_rate``
-  Add the ``DatetimeProcessor``

.. _section-39:

0.2.1
-----

-  Fix to processor taking the wrong number of arguments
-  Make the ``toolz`` package a mandatory dependency
-  Fix a handling of a target variable equaling zero

.. _section-40:

0.2.0
-----

-  Drop support for python3.8 # BREAKING CHANGE
-  Drop ``jobs.get_job`` and ``job.create_job``. # BREAKING CHANGE
-  Rename ``DatasetResponse`` to ``Dataset`` # BREAKING CHANGE
-  Rename ``client.pandas`` to ``client.pandas_integration`` # BREAKING
   CHANGE
-  Add separate endpoint to compute metrics separately using
   ``jobs.create_signal_metrics_job`` and
   ``jobs.create_privacy_metrics_job``.
-  Add separate endpoint to access metrics jobs using
   ``jobs.get_signal_metrics`` and ``job.get_privacy_metrics``
-  Add processors to pre- and post-process your data before, and after
   avatarization for custom use-cases. These are accessible under
   ``avatars.processors``.
-  Handle errors more gracefully
-  Add ExcludeCategoricalParameters to use embedded processor on the
   server side

.. _section-41:

0.1.16
------

-  Add forgotten password endpoint
-  Add reset password endpoint
-  JobParameters becomes AvatarizationParameters
-  Add DCR and NNDR to privacy metrics

.. _section-42:

0.1.15
------

-  Handle category dtype
-  Fix dtype casting of datetime columns
-  Add ability to login with email
-  Add filtering options to ``find_users``
-  Avatarizations are now called with ``create_avatarization_job`` and
   ``AvatarizationJobCreate``. ``create_job`` and ``JobCreate`` are
   deprecated but still work.
-  ``dataset_id`` is now passed to ``AvatarizationParameters`` and not
   ``AvatarizationJobCreate``.
-  ``Job.dataset_id`` is deprecated. Use ``Job.parameters.dataset_id``
   instead.

.. _breaking-1:

BREAKING
~~~~~~~~

-  Remove ``get_health_config`` call.

.. _section-43:

0.1.14
------

-  Give access to avatars unshuffled avatars dataset

.. _section-44:

0.1.13
------

-  Remove default value for ``to_categorical_threshold``
-  Use ``logger.info`` instead of ``print``
