# HEA Server Framework
[Research Informatics Shared Resource](https://risr.hci.utah.edu), [Huntsman Cancer Institute](https://healthcare.utah.edu/huntsmancancerinstitute/), Salt Lake City, UT

The HEA Server Framework contains shared code for creating HEA microservices.


## Version 1.43.0
* Improved performance of getting a user's group information.
* Improved performance of getting large numbers of objects from mongo.
* Use boto3 "adaptive" retry algorithm.
* Bumped heaobject version to 1.33.0.
* Documented APIs where the HTTP request needs an Authorization header.
* Use the new heaobject.volume.Volume.credentials_id attribute.
* New heaserver.service.util.do_nothing co-routine for do_something() if foo else do_nothing() scenarios.

## Version 1.42.0
* Bumped heaobject version to 1.32.0.

## Version 1.41.2
* Bumped heaobject version to 1.31.2.
* Improved error handling when parsing messages received from the message broker.
* Fixed issue getting AWS collaborator information for non-OrganizationAccessRole users.

## Version 1.41.1
* heaserver.service.uritemplate.tvars now decodes extracted variable values as needed.

## Version 1.41.0
* optionsFromUrl CJ template property values can now contain URI templates and expand them using the properties of the
  document's desktop object and the HTTP request's headers and route parameters.
* Handle accounts with the new collaborator classes.

## Version 1.40.0
* Fixed bug in AWS permissions simulation boto3 API usage.
* Support the s3:DeleteObjectVersion action while simulating permissions.
* Added has_read_only_permission, has_editor_permission, has_deleter_permission, and has_sharer_permission
  functions to supported action itemif functions.
* Finally fixed the MaybeDockerNotRunning exception not getting raised reliably.
* Documented hea-deleter rel value.
* Bumped heaobject version to 1.30.0.
* Added collaborator information to AWS account objects.

## Version 1.39.1
* Removed import statement involving wrapt.

## Version 1.39.0
* Added really_close method to the heaserver.service.db.Database class. Made all calls to its close method non-async.
  Call close in context managers, and call really_close when exiting a microservice.
* Removed wrapt dependency.

## Version 1.38.0
* Added hea-parent rel value.
* Bumped heaobject version to 1.29.0.

## Version 1.37.3
* Bumped heaobject version to 1.28.1.

## Version 1.37.2
* Added the wrapt library as a dependency.
* Prevent the default Mongo instance available through the HEA_DB app property from being closed except at
  microservice shutdown.

## Version 1.37.1
* Bumped heaobject version to 1.28.0.

## Version 1.37.0
* Added CLIENT_ERROR_RESTORE_ALREADY_IN_PROGRESS Boto3 client error constant.
* Refactored subscriber_cleanup_context_factory to fix the issue of it stopping message processing after a few
  days.
* Send messages to RabbitMQ with delivery mode set to PERSISTENT.
* If the permissions context says that an attribute has read-only permissions, always make that attribute read-only in
  Collection+JSON templates.

## Version 1.36.2
* Bumped heaobject version to 1.27.1.

## Version 1.36.1
* Bumped heaobject version to 1.27.0.

## Version 1.36.0
* Added missing context parameter to heaserver.service.db.mongoservicelib.get and get_all.

## Version 1.35.0
* Added heaserver.service.aiohttp.extract_sort.
* Replaced dict with heaserver.service.db.mongoservicelib.SortDict more places.
* Fixed heaserver.service.db.mongoservicelib.MongoSortOrder.from_request type hint and related documentation. The type
  hint and documentation said it could return None, and it couldn't.
* Removed heaserver.service.db.mongoservicelib.extract_sort_dict, as it duplicated a MongoSortOrder method.

## Version 1.34.0
* Added delete and delete_bulk for opensearch
* Documented expected desktop object move, copy, delete, rename, and versioning behavior.
* Added some logging.
* Added heaserver.service.aiohttp.SortOrder enum and parse_sort function.
* Documented the expected behavior of the sort query parameter. Also documented the sort_attr query
  parameter.
* Renamed heaserver.service.db.awsservicelib.s3_object_display_name to s3_object_message_display_name.
* Added as_sort_order, from_sort_order, from_request, and from_request_dict methods to
  heaserver.service.db.mongoservicelib.MongoSortOrder. Removed
  heaserver.service.db.mongoservicelib.parse_sort_query_param, which was replaced by
  MongoSortOrder.from_request and better complies with how sort query parameters are supposed to work.

## Version 1.33.1
* Bumped heaobject version to 1.26.3.

## Version 1.33.0
* Worked around aiodiskqueue bug preventing loading of previously persisted messages.
* Added heaserver.service.db.aws.CLIENT_ERROR_BUCKET_NOT_EMPTY boto3 error code constant, and the
  heaserver.service.db.aws.client_error_status function maps it to the 400 status code.

## Version 1.32.2
* Fixed potential resource leak in heaserver.service.messagebroker.publisher_cleanup_context_factory.

## Version 1.32.1
* Bumped heaobject version to 1.26.0.

## Version 1.32.0
* Fixed python 3.11 compatibility regression.
* Cast HEA_WSTL_BUILDER_FACTORY to the correct callable.
* Fixed missing heaserver.service.requestproperty.HEA_WSTL_BUILDER request property.
* Bumped heaobject verstion to 1.25.0.
* Added heaserver.service.db.aws.CLIENT_ERROR_ENTITY_ALREADY_EXISTS.
* Documented new hea- rel values.
* Fixed another instance of "never awaited" warnings in the message broker code.

## Version 1.31.0
* Bumped heaobject version to 1.24.0.
* Made more complete use of the heaserver.service.wstl.WeSTLactionType typed dict. The argument to
  heaserver.service.wstl.RuntimeWeSTLDocumentBuilder.add_design_time_action is now a WeSTLctionType instead of a
  generic dict. Similarly, RuntimeWeSTLDocumentBuilder.find_action now returns a WeSTLactionType or None instead of a
  generic dict or None.
* Added hea property to WeSTLactionType.
* In the heaserver.service.db.mongoservicelib module, get_dict, get_desktop_object, get_by_name_dict,
  get_all_desktop_objects, and get_all_desktop_objects_gen now all have permission context and mongo parameters to
  facilitate reuse. There are also new functions to make working with requests for ascending/descending order easier to
  handle.
* Also in the heaserver.service.db.mongoservicelib module, a bug was fixed causing permissions not to be included in
  the HTTP response when the desktop objects were retrieved from the cache.

## Version 1.30.2
* Fixed heaserver.service.wstl.WeSTLactionType target type.
* Use heaserver.service.wstl.WeSTLactionType everywhere it should be.
* Ensure cached get-all requests return the objects' permissions.

## Version 1.30.1
* Bumped heaobject version to 1.23.0.

## Version 1.30.0
* Bumped heaobject version to 1.22.0.
* Added new method to the heaobject.service.db.database.Database class, get_default_permission_context.
* Changed heaserver.service.db.mongo.Mongo class methods to accept a PermissionContext instead of a sub.
* Made similar changes to the heaserver.service.testcase.mockmongo.MockMongo class.
* Changed heaobject.service.db.mongoservicelib to use the get_default_permission_context method above to pass a context
  into heaobject.service.db.mongo.Mongo objects.
* Refactored permission checks to use heaserver.service.heaobjectsupport.RESTPermissionGroup's new has_any method.
* Changed heaserver.service.db.mongoexpr.sub_filter_expr to accept just permissions and context parameters, and
  altered its implementation to use the heaobject.root.DesktopObject's new dynamic_permission_supported and
  super_admin_default_permissions attributes.
* Removed a redundant EnumWithAttrs class from the heaserver.service.heaobjectsupport module. Instead, that module now
  imports an identical class from the heaobject library.
* Implemented in operator support for heaserver.service.heaobjectsupport.RESTPermissionGroup.
* Added documentation to the heaobject.service.heaobjectsupport.HEAServerPermissionContext class.
* Declared a new standard rel-value, hea-container, for links to desktop objects.

## Version 1.29.0
* Added GET api so you get documents by id for opensearch.
* Cleaned up code for unused SUB.

## Version 1.28.1
* Don't consult the people microservice for the group membership of system users.
* Bumped heaobject version to 1.21.1.

## Version 1.28.0
* Bumped heaobject version to 1.21.0.
* heaserver.service.db.aws.AWSPermissionContext and S3ObjectPermissionContext are no longer generic.
* New heaserver.service.db.aws.AWSDesktopObjectTypeVar_cov covariant version of the AWSDesktopObjectTypeVar type.
* New heaserver.service.db.Database.get_default_permission_context method.
* Made return types of heaserver.service.db.DatabaseManager subclass methods more specific.
* The subclasses of heaobject.root.PermissionContext now accept any DesktopObject and appropriately delegate to the
  superclass.

## Version 1.27.4
* Bumped heaobject version to 1.20.2.

## Version 1.27.3
* Fixed Queue.task_done() was never awaited bug.

## Version 1.27.2
* Bumped boto3 version and added AWS common runtime extra feature.

## Version 1.27.1
* Avoid issue where getting temporary AWS credentials fails sporadically because the AWS datetime is slightly off from
  the datetime of the server running HEA.

## Version 1.27.0
* Added heaserver.service.db.aws.get_default_share() function to get a share object assuming no information about what
  AWS permissions the user has for a desktop object.
* Added heaserver.service.db.aws.add_default_share_to_desktop_object() function, which adds the share created by
  get_default_share() above if the requesting user is not system|none.
* Opensearch close session timing issues fixed
* Opted for more stable pagination approach for search results coming from OpenSearch.

## Version 1.26.0
* heaserver.service.aws.AWSPermissionContext's constructor no longer accepts a volume_id argument. Instead, it gets
  the volume_id from the HTTP request.

## Version 1.25.1
* Now depends on heaobject 1.20.0 with no breaking changes.

## Version 1.25.0
* Now depends on heaobject 1.19.0.

## Version 1.24.0
* Now depends on heaobject 1.18.0.
* If the heaserver.service.util.AsyncioLockCache reaches capacity, really wait until something has been evicted.
* The sleep time in heaserver.service.util.yield_control is now the minimum value.

## Version 1.23.0
* Added optional failed_cb keyword argument to heaserver.service.messagebroker.publisher_cleanup_context_factory that
  is called when something goes wrong with the connection to RabbitMQ.
* Events that cannot be published to the message broker are now persisted in a queue backed by sqlite and retried later
  if the PublishQueuePersistencePath config property is set. If not set, the queue is in-memory only.

## Version 1.22.1
* Updated openservicelib to handle for batch_insert

## Version 1.22.0
* Added hea-recently-accessed to list of standard relation values.
* Added heaserver.service.desktopobjectop module that abstracts some of the logic for common desktop object operations
  (experimental).
* Prevent trying to set the _id field to ObjectId(None) when id is None in heaserver.service.db.mongo.Mongo.
* Fixed type hints for heaserver.service.util.queued_processing.

## Version 1.21.5
* Expanding to the opensearch db api for update, update_bulk, delete, and delete_bulk.
* Bug fix in search api for opensearch.

## Version 1.21.1
* Fixed queued_processing bug when no exceptions to ignore are passed in.
* Documented that heaserver.service.db.mongo.Mongo sets the created and updated timestamps in the UTC timezone.

## Version 1.21.0
* Changed heaserver.service.util.queued_processing to accept an AsyncIterable instead of a callable and fix some bugs.

## Version 1.20.0
* We no longer attempt to create an organization and account manually in moto. Fixes an error in some tests because the
  organization and account are created and linked automatically.
* Support substituting request header values in link URLs.
* Address potential resource leaks.
* Lots of doc string enhancements.
* New heaserver.service.util function, filter_mapping, which is useful for creating header mappings from request
  objects.
* New heaserver.service.client.post_data_create function for returning just the id of the created object, rather than
  the entire URL like with heaserver.service.client.post.
* We now use freezegun when creating expected values for testing.
* New mongoservicelib.get_desktop_object function.
* Added a pre-save hook callback to mongoservicelib.put.

## Version 1.19.1
* Support heaobject 1.16.*.

## Version 1.19.0
* Moved S3 object-related APIs to heaserver-folders-aws-s3.
* Performance improvements.
* Use uvloop event loop on non-Windows platforms.
* Set Activity.request_url attribute.

## Version 1.18.0
* Turn on eager task factory when running Python 3.12.
* Fixed timing issue in heaserver.service.aiohttp.RequestFileLikeWrapper, potentially causing a hang.
* Replaced deprecated logger.warn with logger.warning.
* Fixed bug in awsservicelib.copy_object where copy fails if the target folder contains an object with a name that is a prefix of the object to be copied.

## Version 1.17.0
* Added support for Python 3.12.

## Version 1.16.1
* Fixed regression in heaserver.service.db.awsservicelib._copy_object_extract_target causing error when there are query parameters in the target URL.

## Version 1.16.0
* Implemented a new async retry decorator for async context managers, heaserver.service.util.async_retry_context_manager.
* Fixed retry and async_retry to raise the actual exception rather than RetryExhaustedError.
* Removed RetryExhaustedError.
* Altered the Mongo context manager not to close the client in __aexit__().
* Don't let freezegun prevent asyncio.sleep() from working.
* The Collection+JSON representor can now be configured to omit data and permissions and just return links.

## Version 1.15.1
* Fixed testing bugs in handling of enum formatting and where owner may have wrong expected readOnly status.

## Version 1.15.0
* Added resource_base parameter to mongoservicelib.post and mongoservicelib.post_dict.
* Docstring enhancements.
* Fixed AttributeError in mockmongo.update_admin.
* Added client_error_code() function to the heaserver.service.db.aws module to centralize what to do to extract the error code out of a boto3 ClientError exception.
* In a Collection+JSON template when there is more than one desktop object in the document, create an object desktop object of the same type and use its attributes to determine which fields to make read-only.

## Version 1.14.1
* Includes opensearch-py sdk the required dependency of OpenSearch.

## Version 1.14.0
* Adds supporting classes for doing  search in OpenSearch.
* Added client_error_code() function to the heaserver.service.db.aws module to centralize what to do to extract the error code out of a boto3 ClientError exception.
* In a Collection+JSON template when there is more than one desktop object in the document, create an object desktop object of the same type and use its attributes to determine which fields to make read-only.

## Version 1.14.0
* Added resource_base parameter to mongoservicelib.post and mongoservicelib.post_dict.
* Docstring enhancements.
* Fixed AttributeError in mockmongo.update_admin.
* Added client_error_code() function to the heaserver.service.db.aws module to centralize what to do to extract the error code out of a boto3 ClientError exception.
* In a Collection+JSON template when there is more than one desktop object in the document, create an object desktop object of the same type and use its attributes to determine which fields to make read-only.

## Version 1.13.2
* Fixed handling of id fields in mongo admin non-desktop object upsert and update.
* Properly remove 'id' fields in desktop objects.

## Version 1.13.1
* Cache account owner information for a caching boost.

## Version 1.13
* Removed heaserver.service.aiohttp.StreamResponseFileLikeWrapper.
* Handle iterator-of-tuple header format in heaserver.service.response.status_ok().

## Version 1.12.2
* Made heaserver.service.testcase.microsevicetestcase.MicroserviceTestCase an abstract class with a default constructor
to prevent errors with recent pytest versions. The class was previously documented as abstract but did not inherit from
abc.ABC nor did it have any methods marked as abstract.
* Updated dependencies.

## Version 1.12.1
* Caching optimizations.

## Version 1.12.0
* Support passing the Bearer token in the access_token query parameter as an alternative to the Authorization header.

## Version 1.11.0
* The OIDC claim constants now include more claims.
* Respond with HTTP status code 409 (Conflict) on insertions when there is a conflict.
* Added optional desktop object parameter to heaserver.service.db.mongoservicelib.put.
* Addressed minor bugs in the testing framework.
* The heaserver.service.db.database.DatabaseContextManager.credentials property now does a deep copy of the credential list before returning it.
* Altered parameter validation of heaserver.service.db.aws.S3.get_client() so that the credentials and volume_id parameters can both be None (which delegates credentials to the boto3 library).
* Improved docstrings.
* New functions for improving error messages (s3_object_display_name and http_error_message in heaserver.service.awsservicelib,
and http_error_message in heaserver.service.aiohttp).

## Version 1.10.7
* Updated pymongo dependency

## Version 1.10.6
* Addressed potential interpreter hang at the end of running tests.

## Version 1.10.5
* Fixed bug sometimes preventing role from being assumed.

## Version 1.10.4
* Improved performance generating cloud credentials.

## Version 1.10.3
* Fixed type hints and logging.
* Make mongo insert calls return HTTP Conflict status code when appropriate.
* Resolved a potential issue getting an AWS account.

## Version 1.10.2
* Adds email util

## Version 1.10.1
* Limit the duration of privilege elevation when requesting it from AWS.

## Version 1.10.0
* Added elevate_privileges method to heaserver.service.db.S3.

## Version 1.9.0
* Fixed type hints, requiring mostly minor API changes.

## Version 1.8.3
* Fixed error getting object versions if no prefix is specified.

## Version 1.8.2
* Retry getting temporary credentials when the call to boto3 assume_role_with_web_identity fails.
* Use boto3's built-in paginator everywhere.

## Version 1.8.1
* Prevent failed content downloads from hanging the microservice.

## Version 1.8.0
* Moved CLIENT_ERROR* constants from heaserver.service.db.awsservicelib to the aws module.
* Updated the logic for determining permissions for AWS accounts, buckets, and objects to fallback to full permissions if the user lacks permission in AWS to simulate permissions. Thus, the behavior will fall back to that of version 1.6 or earlier. As before, AWS will still reject requests that the user lacks permissions for. A future version of heaserver will likely attempt to use elevated permissions to perform the simulation.

## Version 1.7.1
* Fixed the order in which multiple exceptions are raised.

## Version 1.7.0
* requirements_dev.txt now sets a minimum version of setuptools to address a security vulnerability. Also updated to a newer version of build.
* Implemented attribute-level permissions.
* Addressed potential performance issue with unarchiving large numbers of AWS S3 objects.
* Addressed potential crash when the server loses its connection to a client while downloading an object's contents, and increased logging during downloads.
* Mapped AWS access policies to HEA permissions so that HEA may present accurate permissions for AWS accounts, S3 buckets, and S3 objects.

## Version 1.6.3
* Upgrading heaobject dependency to get bug fixes.

## Version 1.6.2
* Added ability to toggle aws key duration depending on if system credential manager or any other user.
* Background tasks now pass the aiohttp app object as a parameter of the coroutine added to the queue.
* Added the scheduled_cleanup_ctx manager for scheduling reoccurring tasks with a delay optionally.
* Prevent the id field from appearing in mongodb when a new desktop object is inserted.


## Version 1.6.0
* Improved docstrings.
* New heaobject dependency.
* Removed account_type_names parameters from heaserver.service.db.database.get_volumes and heaserver.service.db.database.Database.get_volumes.
* New heaserver.service.util.now() function.
* Removed file system-related parameters from heaserver.service.heaobjectsupport functions (type_to_resource_url, get_dict, get, get_all, get_component, get_resource_url).
* heaserver.service.client: Made a type passed into type_or_obj not used to create the object instance; new get_all_list() function.
* Use heaobject.util.now() instead of datetime.now() to get the current datetime with a timezone.
* Don't allow creating a new desktop object in MongoDB if the current user and the owner of the object are not the same.
* Set the created and modified attributes of desktop objects in heaserver.service.db.mongo.
* Populate new AWSAccount attributes.

## Version 1.5.3
* When updating AWS temporary credentials, generate new headers rather than pass the headers from the HTTP request,
possibly resulting in a Content-Length header that is shorter than the request body.
* Make heaserver.service.db.aws.get_credentials raise the right exception.

## Version 1.5.2
* Fixed TypeError regression in the heaserver.service.client module.

## Version 1.5.1
* Ensure the Content-Type header is set to application/json in heaserver.service.client put and post calls.

## Version 1.5.0
* Added attribute-level permissions.
* Temporarily restored the role check that was removed in version 1.4.1 in case an AWS credentials object with overly
permissive permissions is altered.

## Version 1.4.2
* Synchronize around getting temporary credentials.

## Version 1.4.1
* Increased the boto3 max connection pool size from the default value (10) to 25.
* Fixed a connection leak in DatabaseContextManager, and fixed the documentation for the connection() method.
* Updated heaobject dependency.
* Removed an unnecessary role check.

## Version 1.4.0
* Added type_display_name attribute to all HEA objects.

## Version 1.3.0
* Performance improvement getting accounts.
* heaserver.service.db.database.DatabaseContextManagers now allow initializing with either a volume id or a Credentials
object.

## Version 1.2.0
* get_volumes() in the database module and Database class can now filter by account ids.
* New heaobject dependency: new heaobject.root.AbstractAssociation base class and heaobject.account.AccountAssociation
implementation, and heaobject.organization.Organization class now has an accounts attribute using AccountAssociation.

## Version 1.1.3
* Fixed permissions setting in mongoservicelib.aggregate().

## Version 1.1.2
* Added resolved permissions for desktop objects in WeSTL and Collection+JSON docs.

## Version 1.1.1
* No longer errors out when accessing account information that the user is unauthorized to see.

## Version 1.1.0
* AWS account objects are now populated with more information.
* New heaobject with new APIs.

## Version 1.0.8
* Performance improvements converting to/from a HEAObject and a dictionary.

## Version 1.0.7
* Prevent a condition where zip file generation resulted in a truncated zip file.

## Version 1.0.6
* Prevent hang while getting HEA object content when the client connection goes away.

## Version 1.0.5
* Backed out boto connections issue.

## Version 1.0.4
* Don't crash when getting the user's AWS account list includes an account that doesn't exist.
* Fixed exceptions while unarchiving objects.
* Better error messaging when trying to move archived files.
* Allow copying and moving unarchived files.

## Version 1.0.3
* Added heaserver.service.response.status_generic_error() function.
* Made heaserver.service.db.awsservicelib.handle_client_error always return an HTTP response object that can be raised
  as an exception.

## Version 1.0.2
* Improved performance of heaserver.service.activity.DesktopObjectActionLifecycle context manager.
* Removed unused properties from heaserver.service.activity.DesktopObjectActionLifecycle.
* Implemented input validation for heaserver.service.db.awsservicelib.archive_object().

## Version 1.0.1
* Fixed caching bug affecting mongodb paginated queries.
* Fixed passing one desktop object dict to heaserver.service.wstl.RuntimeWeSTLDocumentBuilder().

## Version 1
Initial release.

## Runtime requirements
* Python 3.10, 3.11, or 3.12.

## Configuration
The `heaserver.service.messagebroker` module supports publishing and receiving messages to/from a RabbitMQ message
broker. A `HEASERVER_MESSAGE_BROKER_QUEUE_PATH` environment variable is supported that, if set with the path to a
sqlite database, will cause message broker messages that fail to publish to be persisted and retried later. If not set,
failed messages will be stored only in memory and thus lost if the microservice is restarted. The variable need not be
set for microservices that do not publish to the message broker. The same file must not be shared across multiple
microservices or data corruption may result.

## Development environment

### Build requirements
* Any development environment is fine.
* On Windows, you also will need:
    * Build Tools for Visual Studio 2019, found at https://visualstudio.microsoft.com/downloads/. Select the C++ tools.
    * git, found at https://git-scm.com/download/win.
* On Mac, Xcode or the command line developer tools is required, found in the Apple Store app.
* Python 3.10, 3.11, or 3.12: Download and install Python from https://www.python.org, and select the options to install
for all users and add Python to your environment variables. The install for all users option will help keep you from
accidentally installing packages into your Python installation's site-packages directory instead of to your virtualenv
environment, described below.
* Create a virtualenv environment using the `python -m venv <venv_directory>` command, substituting `<venv_directory>`
with the directory name of your virtual environment. Run `source <venv_directory>/bin/activate` (or `<venv_directory>/Scripts/activate` on Windows) to activate the virtual
environment. You will need to activate the virtualenv every time before starting work, or your IDE may be able to do
this for you automatically. **Note that PyCharm will do this for you, but you have to create a new Terminal panel
after you newly configure a project with your virtualenv.**
* From the project's root directory, and using the activated virtualenv, run `pip install wheel` followed by
  `pip install -r requirements_dev.txt`. **Do NOT run `python setup.py develop`. It will break your environment.**

### Running tests
Run tests with the `pytest` command from the project root directory. To improve performance, run tests in multiple
processes with `pytest -n auto`.

### Running integration tests
* Install Docker

### Packaging and releasing this project
See the [RELEASING.md](RELEASING.md) file for details.
