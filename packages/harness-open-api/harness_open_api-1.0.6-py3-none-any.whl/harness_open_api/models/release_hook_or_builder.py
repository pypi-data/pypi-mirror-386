# coding: utf-8

"""
    Harness NextGen Software Delivery Platform API Reference

    The Harness Software Delivery Platform uses OpenAPI Specification v3.0. Harness constantly improves these APIs. Please be aware that some improvements could cause breaking changes. # Introduction     The Harness API allows you to integrate and use all the services and modules we provide on the Harness Platform. If you use client-side SDKs, Harness functionality can be integrated with your client-side automation, helping you reduce manual efforts and deploy code faster.    For more information about how Harness works, read our [documentation](https://developer.harness.io/docs/getting-started) or visit the [Harness Developer Hub](https://developer.harness.io/).  ## How it works    The Harness API is a RESTful API that uses standard HTTP verbs. You can send requests in JSON, YAML, or form-data format. The format of the response matches the format of your request. You must send a single request at a time and ensure that you include your authentication key. For more information about this, go to [Authentication](#section/Introduction/Authentication).  ## Get started    Before you start integrating, get to know our API better by reading the following topics:    * [Harness key concepts](https://developer.harness.io/docs/getting-started/learn-harness-key-concepts/)   * [Authentication](#section/Introduction/Authentication)   * [Requests and responses](#section/Introduction/Requests-and-Responses)   * [Common Parameters](#section/Introduction/Common-Parameters-Beta)   * [Status Codes](#section/Introduction/Status-Codes)   * [Errors](#tag/Error-Response)   * [Versioning](#section/Introduction/Versioning-Beta)   * [Pagination](/#section/Introduction/Pagination-Beta)    The methods you need to integrate with depend on the functionality you want to use. Work with  your Harness Solutions Engineer to determine which methods you need.  ## Authentication  To authenticate with the Harness API, you need to:   1. Generate an API token on the Harness Platform.   2. Send the API token you generate in the `x-api-key` header in each request.  ### Generate an API token  To generate an API token, complete the following steps:   1. Go to the [Harness Platform](https://app.harness.io/).   2. On the left-hand navigation, click **My Profile**.   3. Click **+API Key**, enter a name for your key and then click **Save**.   4. Within the API Key tile, click **+Token**.   5. Enter a name for your token and click **Generate Token**. **Important**: Make sure to save your token securely. Harness does not store the API token for future reference, so make sure to save your token securely before you leave the page.  ### Send the API token in your requests  Send the token you created in the Harness Platform in the x-api-key header. For example:   `x-api-key: YOUR_API_KEY_HERE`  ## Requests and Responses    The structure for each request and response is outlined in the API documentation. We have examples in JSON and YAML for every request and response. You can use our online editor to test the examples.  ## Common Parameters [Beta]  | Field Name | Type    | Default | Description    | |------------|---------|---------|----------------| | identifier | string  | none    | URL-friendly version of the name, used to identify a resource within it's scope and so needs to be unique within the scope.                                                                                                            | | name       | string  | none    | Human-friendly name for the resource.                                                                                       | | org        | string  | none    | Limit to provided org identifiers.                                                                                                                     | | project    | string  | none    | Limit to provided project identifiers.                                                                                                                 | | description| string  | none    | More information about the specific resource.                                                                                    | | tags       | map[string]string  | none    | List of labels applied to the resource.                                                                                                                         | | order      | string  | desc    | Order to use when sorting the specified fields. Type: enum(asc,desc).                                                                                                                                     | | sort       | string  | none    | Fields on which to sort. Note: Specify the fields that you want to use for sorting. When doing so, consider the operational overhead of sorting fields. | | limit      | int     | 30      | Pagination: Number of items to return.                                                                                                                 | | page       | int     | 1       | Pagination page number strategy: Specify the page number within the paginated collection related to the number of items in each page.                  | | created    | int64   | none    | Unix timestamp that shows when the resource was created (in milliseconds).                                                               | | updated    | int64   | none    | Unix timestamp that shows when the resource was last edited (in milliseconds).                                                           |   ## Status Codes    Harness uses conventional HTTP status codes to indicate the status of an API request.    Generally, 2xx responses are reserved for success and 4xx status codes are reserved for failures. A 5xx response code indicates an error on the Harness server.    | Error Code  | Description |   |-------------|-------------|   | 200         |     OK      |   | 201         |   Created   |   | 202         |   Accepted  |   | 204         |  No Content |   | 400         | Bad Request |   | 401         | Unauthorized |   | 403         | Forbidden |   | 412         | Precondition Failed |   | 415         | Unsupported Media Type |   | 500         | Server Error |    To view our error response structures, go [here](#tag/Error-Response).  ## Versioning [Beta]  ### Harness Version   The current version of our Beta APIs is yet to be announced. The version number will use the date-header format and will be valid only for our Beta APIs.  ### Generation   All our beta APIs are versioned as a Generation, and this version is included in the path to every API resource. For example, v1 beta APIs begin with `app.harness.io/v1/`, where v1 is the API Generation.    The version number represents the core API and does not change frequently. The version number changes only if there is a significant departure from the basic underpinnings of the existing API. For example, when Harness performs a system-wide refactoring of core concepts or resources.  ## Pagination [Beta]  We use pagination to place limits on the number of responses associated with list endpoints. Pagination is achieved by the use of limit query parameters. The limit defaults to 30. Its maximum value is 100.  Following are the pagination headers supported in the response bodies of paginated APIs:   1. X-Total-Elements : Indicates the total number of entries in a paginated response.   2. X-Page-Number : Indicates the page number currently returned for a paginated response.   3. X-Page-Size : Indicates the number of entries per page for a paginated response.  For example:    ``` X-Total-Elements : 30 X-Page-Number : 0 X-Page-Size : 10   ```   # noqa: E501

    OpenAPI spec version: 1.0
    Contact: contact@harness.io
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""

import pprint
import re  # noqa: F401

import six

class ReleaseHookOrBuilder(object):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    swagger_types = {
        'action': 'str',
        'action_value': 'int',
        'all_fields': 'dict(str, object)',
        'default_instance_for_type': 'Message',
        'descriptor_for_type': 'Descriptor',
        'initialization_error_string': 'str',
        'initialized': 'bool',
        'release': 'Release',
        'release_or_builder': 'ReleaseOrBuilder',
        'repo': 'Repository',
        'repo_or_builder': 'RepositoryOrBuilder',
        'sender': 'PipelineUser',
        'sender_or_builder': 'UserOrBuilder',
        'unknown_fields': 'UnknownFieldSet'
    }

    attribute_map = {
        'action': 'action',
        'action_value': 'actionValue',
        'all_fields': 'allFields',
        'default_instance_for_type': 'defaultInstanceForType',
        'descriptor_for_type': 'descriptorForType',
        'initialization_error_string': 'initializationErrorString',
        'initialized': 'initialized',
        'release': 'release',
        'release_or_builder': 'releaseOrBuilder',
        'repo': 'repo',
        'repo_or_builder': 'repoOrBuilder',
        'sender': 'sender',
        'sender_or_builder': 'senderOrBuilder',
        'unknown_fields': 'unknownFields'
    }

    def __init__(self, action=None, action_value=None, all_fields=None, default_instance_for_type=None, descriptor_for_type=None, initialization_error_string=None, initialized=None, release=None, release_or_builder=None, repo=None, repo_or_builder=None, sender=None, sender_or_builder=None, unknown_fields=None):  # noqa: E501
        """ReleaseHookOrBuilder - a model defined in Swagger"""  # noqa: E501
        self._action = None
        self._action_value = None
        self._all_fields = None
        self._default_instance_for_type = None
        self._descriptor_for_type = None
        self._initialization_error_string = None
        self._initialized = None
        self._release = None
        self._release_or_builder = None
        self._repo = None
        self._repo_or_builder = None
        self._sender = None
        self._sender_or_builder = None
        self._unknown_fields = None
        self.discriminator = None
        if action is not None:
            self.action = action
        if action_value is not None:
            self.action_value = action_value
        if all_fields is not None:
            self.all_fields = all_fields
        if default_instance_for_type is not None:
            self.default_instance_for_type = default_instance_for_type
        if descriptor_for_type is not None:
            self.descriptor_for_type = descriptor_for_type
        if initialization_error_string is not None:
            self.initialization_error_string = initialization_error_string
        if initialized is not None:
            self.initialized = initialized
        if release is not None:
            self.release = release
        if release_or_builder is not None:
            self.release_or_builder = release_or_builder
        if repo is not None:
            self.repo = repo
        if repo_or_builder is not None:
            self.repo_or_builder = repo_or_builder
        if sender is not None:
            self.sender = sender
        if sender_or_builder is not None:
            self.sender_or_builder = sender_or_builder
        if unknown_fields is not None:
            self.unknown_fields = unknown_fields

    @property
    def action(self):
        """Gets the action of this ReleaseHookOrBuilder.  # noqa: E501


        :return: The action of this ReleaseHookOrBuilder.  # noqa: E501
        :rtype: str
        """
        return self._action

    @action.setter
    def action(self, action):
        """Sets the action of this ReleaseHookOrBuilder.


        :param action: The action of this ReleaseHookOrBuilder.  # noqa: E501
        :type: str
        """
        allowed_values = ["UNKNOWN", "CREATE", "UPDATE", "DELETE", "OPEN", "REOPEN", "CLOSE", "LABEL", "UNLABEL", "SYNC", "MERGE", "EDIT", "PUBLISH", "UNPUBLISH", "PRERELEASE", "RELEASE", "REVIEWREADY", "UNRECOGNIZED"]  # noqa: E501
        if action not in allowed_values:
            raise ValueError(
                "Invalid value for `action` ({0}), must be one of {1}"  # noqa: E501
                .format(action, allowed_values)
            )

        self._action = action

    @property
    def action_value(self):
        """Gets the action_value of this ReleaseHookOrBuilder.  # noqa: E501


        :return: The action_value of this ReleaseHookOrBuilder.  # noqa: E501
        :rtype: int
        """
        return self._action_value

    @action_value.setter
    def action_value(self, action_value):
        """Sets the action_value of this ReleaseHookOrBuilder.


        :param action_value: The action_value of this ReleaseHookOrBuilder.  # noqa: E501
        :type: int
        """

        self._action_value = action_value

    @property
    def all_fields(self):
        """Gets the all_fields of this ReleaseHookOrBuilder.  # noqa: E501


        :return: The all_fields of this ReleaseHookOrBuilder.  # noqa: E501
        :rtype: dict(str, object)
        """
        return self._all_fields

    @all_fields.setter
    def all_fields(self, all_fields):
        """Sets the all_fields of this ReleaseHookOrBuilder.


        :param all_fields: The all_fields of this ReleaseHookOrBuilder.  # noqa: E501
        :type: dict(str, object)
        """

        self._all_fields = all_fields

    @property
    def default_instance_for_type(self):
        """Gets the default_instance_for_type of this ReleaseHookOrBuilder.  # noqa: E501


        :return: The default_instance_for_type of this ReleaseHookOrBuilder.  # noqa: E501
        :rtype: Message
        """
        return self._default_instance_for_type

    @default_instance_for_type.setter
    def default_instance_for_type(self, default_instance_for_type):
        """Sets the default_instance_for_type of this ReleaseHookOrBuilder.


        :param default_instance_for_type: The default_instance_for_type of this ReleaseHookOrBuilder.  # noqa: E501
        :type: Message
        """

        self._default_instance_for_type = default_instance_for_type

    @property
    def descriptor_for_type(self):
        """Gets the descriptor_for_type of this ReleaseHookOrBuilder.  # noqa: E501


        :return: The descriptor_for_type of this ReleaseHookOrBuilder.  # noqa: E501
        :rtype: Descriptor
        """
        return self._descriptor_for_type

    @descriptor_for_type.setter
    def descriptor_for_type(self, descriptor_for_type):
        """Sets the descriptor_for_type of this ReleaseHookOrBuilder.


        :param descriptor_for_type: The descriptor_for_type of this ReleaseHookOrBuilder.  # noqa: E501
        :type: Descriptor
        """

        self._descriptor_for_type = descriptor_for_type

    @property
    def initialization_error_string(self):
        """Gets the initialization_error_string of this ReleaseHookOrBuilder.  # noqa: E501


        :return: The initialization_error_string of this ReleaseHookOrBuilder.  # noqa: E501
        :rtype: str
        """
        return self._initialization_error_string

    @initialization_error_string.setter
    def initialization_error_string(self, initialization_error_string):
        """Sets the initialization_error_string of this ReleaseHookOrBuilder.


        :param initialization_error_string: The initialization_error_string of this ReleaseHookOrBuilder.  # noqa: E501
        :type: str
        """

        self._initialization_error_string = initialization_error_string

    @property
    def initialized(self):
        """Gets the initialized of this ReleaseHookOrBuilder.  # noqa: E501


        :return: The initialized of this ReleaseHookOrBuilder.  # noqa: E501
        :rtype: bool
        """
        return self._initialized

    @initialized.setter
    def initialized(self, initialized):
        """Sets the initialized of this ReleaseHookOrBuilder.


        :param initialized: The initialized of this ReleaseHookOrBuilder.  # noqa: E501
        :type: bool
        """

        self._initialized = initialized

    @property
    def release(self):
        """Gets the release of this ReleaseHookOrBuilder.  # noqa: E501


        :return: The release of this ReleaseHookOrBuilder.  # noqa: E501
        :rtype: Release
        """
        return self._release

    @release.setter
    def release(self, release):
        """Sets the release of this ReleaseHookOrBuilder.


        :param release: The release of this ReleaseHookOrBuilder.  # noqa: E501
        :type: Release
        """

        self._release = release

    @property
    def release_or_builder(self):
        """Gets the release_or_builder of this ReleaseHookOrBuilder.  # noqa: E501


        :return: The release_or_builder of this ReleaseHookOrBuilder.  # noqa: E501
        :rtype: ReleaseOrBuilder
        """
        return self._release_or_builder

    @release_or_builder.setter
    def release_or_builder(self, release_or_builder):
        """Sets the release_or_builder of this ReleaseHookOrBuilder.


        :param release_or_builder: The release_or_builder of this ReleaseHookOrBuilder.  # noqa: E501
        :type: ReleaseOrBuilder
        """

        self._release_or_builder = release_or_builder

    @property
    def repo(self):
        """Gets the repo of this ReleaseHookOrBuilder.  # noqa: E501


        :return: The repo of this ReleaseHookOrBuilder.  # noqa: E501
        :rtype: Repository
        """
        return self._repo

    @repo.setter
    def repo(self, repo):
        """Sets the repo of this ReleaseHookOrBuilder.


        :param repo: The repo of this ReleaseHookOrBuilder.  # noqa: E501
        :type: Repository
        """

        self._repo = repo

    @property
    def repo_or_builder(self):
        """Gets the repo_or_builder of this ReleaseHookOrBuilder.  # noqa: E501


        :return: The repo_or_builder of this ReleaseHookOrBuilder.  # noqa: E501
        :rtype: RepositoryOrBuilder
        """
        return self._repo_or_builder

    @repo_or_builder.setter
    def repo_or_builder(self, repo_or_builder):
        """Sets the repo_or_builder of this ReleaseHookOrBuilder.


        :param repo_or_builder: The repo_or_builder of this ReleaseHookOrBuilder.  # noqa: E501
        :type: RepositoryOrBuilder
        """

        self._repo_or_builder = repo_or_builder

    @property
    def sender(self):
        """Gets the sender of this ReleaseHookOrBuilder.  # noqa: E501


        :return: The sender of this ReleaseHookOrBuilder.  # noqa: E501
        :rtype: PipelineUser
        """
        return self._sender

    @sender.setter
    def sender(self, sender):
        """Sets the sender of this ReleaseHookOrBuilder.


        :param sender: The sender of this ReleaseHookOrBuilder.  # noqa: E501
        :type: PipelineUser
        """

        self._sender = sender

    @property
    def sender_or_builder(self):
        """Gets the sender_or_builder of this ReleaseHookOrBuilder.  # noqa: E501


        :return: The sender_or_builder of this ReleaseHookOrBuilder.  # noqa: E501
        :rtype: UserOrBuilder
        """
        return self._sender_or_builder

    @sender_or_builder.setter
    def sender_or_builder(self, sender_or_builder):
        """Sets the sender_or_builder of this ReleaseHookOrBuilder.


        :param sender_or_builder: The sender_or_builder of this ReleaseHookOrBuilder.  # noqa: E501
        :type: UserOrBuilder
        """

        self._sender_or_builder = sender_or_builder

    @property
    def unknown_fields(self):
        """Gets the unknown_fields of this ReleaseHookOrBuilder.  # noqa: E501


        :return: The unknown_fields of this ReleaseHookOrBuilder.  # noqa: E501
        :rtype: UnknownFieldSet
        """
        return self._unknown_fields

    @unknown_fields.setter
    def unknown_fields(self, unknown_fields):
        """Sets the unknown_fields of this ReleaseHookOrBuilder.


        :param unknown_fields: The unknown_fields of this ReleaseHookOrBuilder.  # noqa: E501
        :type: UnknownFieldSet
        """

        self._unknown_fields = unknown_fields

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        if issubclass(ReleaseHookOrBuilder, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, ReleaseHookOrBuilder):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
