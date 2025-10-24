# HEA Server Buckets Microservice
[Research Informatics Shared Resource](https://risr.hci.utah.edu), [Huntsman Cancer Institute](https://hci.utah.edu),
Salt Lake City, UT

The HEA Server Buckets Microservice is a service for managing buckets and their data within the cloud.


## Version 1.11.1
* Pass Authorization header to account calls that need it. Addresses a 500 error that happened inconsistently.
* Updated collaborator code to conform to changes to /credentials REST APIs.

## Version 1.11.0
* Added endpoint for getting all bucket collaborators for the account represented by the volume in the request URL.


## Version 1.10.5
* Fixed verbiage when prompting to delete 3 buckets.
* Added hea-downloader rel value for bucket opener choice links.

## Version 1.10.4
* Fixed issue where unfiltered bucket items were returned when buckets were not yet cached.
* Fixed regression where collaborators' credentials were not deleted when a collaborator was removed from an account.
* We now detach a collaborator role policy from any users or groups before deleting it.
* Upon removing a collaborator from a bucket, we now remove any non-existent buckets from the role policy.

## Version 1.10.3
* Bumped heaserver version to 1.37.1.

## Version 1.10.2
* Bumped heaserver version to 1.36.2.

## Version 1.10.1
* Support downloading the contents of an entire bucket.

## Version 1.10.0
* Delegate uploads to the heaserver-folders-aws-s3 microservice.
* Changed default storage class for the uploads template to Deep Glacier.

## Version 1.9.2
* Restored adding collaborators to a bucket and removing collaborators from a bucket.

## Version 1.9.1
* When unversioned buckets are created, set versioning to Disabled not Suspended.

## Version 1.9.0
* Bumped heaserver version to 1.33.0 to address potential issue where desktop object actions fail to be sent to
  RabbitMQ.
* Added delete preflight.
* Replaced error message for when attempting to delete a bucket that is not empty.

## Version 1.8.1
* Bumped heaserver version to 1.32.2 to correct a potential issue causing the microservice to fail to send messages to
  the message broker.

## Version 1.8.0
* We now mark buckets with the new hea-container, hea-self-container, and hea-actual-container rel values.

## Version 1.7.2
* Bumped heaserver version to 1.30.1 to address a potential issue with erroneously assigning CREATOR permissions.

## Version 1.7.1
* Bumped heaserver version to 1.30.0.
* Enhancements to group permissions support.

## Version 1.7.0
* Added group permissions support.

## Version 1.6.10
* Upgraded heaserver dependency for bug fix getting temporary AWS credentials.

## Version 1.6.9
* Fixed 500 error when requesting a new folder or new project form.

## Version 1.6.8
* Don't add a Share to the bucket if we don't know anything about the user's permissions.

## Version 1.6.7
* Fixed a caching issue that prevented the changes in 1.6.6 from working.

## Version 1.6.6
* Really made the change in version 1.6.5 work.

## Version 1.6.5
* Made new object forms always read-write.

## Version 1.6.4
* Bucket items are now filtered when inaccessible.

## Version 1.6.3
* Call the heaserver-folders-aws-s3 service to delete bucket objects.

## Version 1.6.2
* Fixed 500 error when attempting to populate collaborators and when there is no authorization info.

## Version 1.6.1
* Performance improvements.

## Version 1.6.0
* Added support for python 3.12.

## Version 1.5.0
* Removed most integration tests because they overlapped with the unit tests.
* Accept the data query parameter for get requests for a speed boost.

## Version 1.4.6
* Dependency upgrades for compatibility with heaserver-keychain 1.5.0.

## Version 1.4.5
* Missed a place where json needed to be replaced by orjson.

## Version 1.4.4
* Permissions calculation speedup.

## Version 1.4.3
* Caching optimizations.

## Version 1.4.2
* Don't create collaborator groups, roles, etc. if the user has non-collaborator bucket access already.
* Changed the group paths to /Collaborator/AWS Accounts/account id/user id.

## Version 1.4.1
* Addressed potential concurrency issues.
* Fixed bug causing duplicate collaborators in an organization.

## Version 1.4.0
* We now support adding and removing collaborators who are not an admin/manager/member/PI of the organization so that
they can access selected buckets.

## Version 1.3.4
* Improved performance getting a bucket.

## Version 1.3.3
* Fixed type hint errors.
* Updated AWS region list.
* Restored accurate bucket permissions feature.

## Version 1.3.2
* Avoid timeouts loading buckets, which sporadically caused buckets not to be returned.

## Version 1.3.1
* Install setuptools first during installation.
* Correct issue where some users lost access to buckets because the user lacked permissions in AWS to simulate permissions. Instead, such users will appear to receive full permission for everything, which was the behavior prior to version 1.3.0. As before, AWS will still reject requests that users lack permission for.

## Version 1.3.0
* Present accurate bucket permissions.

## Version 1.2.0
* Added deletecontents query parameter the bucket delete endpoint. If true/yes/y, requesting a bucket delete will
delete the bucket's contents first. If false/no/n or omitted, the bucket delete will succeed only if the bucket is
empty.

## Version 1.1.4
* Grant all users DELETER privileges to buckets so that the webclient permits deletion (the backend will still deny
users without permissions to delete buckets).

## Version 1.1.3
* Fixed potential issue preventing the service from updating temporary credentials.

## Version 1.1.2
* Fixed new folder form submission.

## Version 1.1.1
* Display type display name in properties card, and return the type display name from GET calls.

## Version 1.1.0
* Fixed support for uploading to a bucket.
* Pass desktop object permissions back to clients.

## Version 1.0.4
* Changed presented bucket owner to system|aws.
* Omitted shares from the properties template.

## Version 1.0.3
* Improved performance getting all buckets.

## Version 1.0.2
* Improved performance.

## Version 1.0.1
* Improved performance.

## Version 1
Initial release.

## Runtime requirements
* Python 3.10, 3.11, or 3.12.

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
* On Windows, install pywin32 version >= 223 from https://github.com/mhammond/pywin32/releases. In your venv, make sure that
`include-system-site-packages` is set to `true`.

### Trying out the APIs
This microservice has Swagger3/OpenAPI support so that you can quickly test the APIs in a web browser. Do the following:
* Install Docker, if it is not installed already.
* Run the `run-swaggerui.py` file in your terminal. This file contains some test objects that are loaded into a MongoDB
  Docker container.
* Go to `http://127.0.0.1:8080/docs` in your web browser.

Once `run-swaggerui.py` is running, you can also access the APIs via `curl` or other tool. For example, in Windows
PowerShell, execute:
```
Invoke-RestMethod -Uri http://localhost:8080/buckets/ -Method GET -Headers @{'accept' = 'application/json'}`
```
In MacOS or Linux, the equivalent command is:
```
curl -X GET http://localhost:8080/buckets/ -H 'accept: application/json'
```

### Packaging and releasing this project
See the [RELEASING.md](RELEASING.md) file for details.
