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

class AllIssuesOccurrenceDetailsResult(object):
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
        'description': 'str',
        'exemption_id': 'str',
        'issue_type': 'str',
        'occurrences': 'list[dict(str, object)]',
        'pagination': 'StoPagination',
        'reference_identifiers': 'list[RefIds]',
        'severity_code': 'str',
        'target_name': 'str',
        'target_type': 'str',
        'title': 'str',
        'variant_name': 'str'
    }

    attribute_map = {
        'description': 'description',
        'exemption_id': 'exemptionId',
        'issue_type': 'issueType',
        'occurrences': 'occurrences',
        'pagination': 'pagination',
        'reference_identifiers': 'referenceIdentifiers',
        'severity_code': 'severityCode',
        'target_name': 'targetName',
        'target_type': 'targetType',
        'title': 'title',
        'variant_name': 'variantName'
    }

    def __init__(self, description=None, exemption_id=None, issue_type=None, occurrences=None, pagination=None, reference_identifiers=None, severity_code=None, target_name=None, target_type=None, title=None, variant_name=None):  # noqa: E501
        """AllIssuesOccurrenceDetailsResult - a model defined in Swagger"""  # noqa: E501
        self._description = None
        self._exemption_id = None
        self._issue_type = None
        self._occurrences = None
        self._pagination = None
        self._reference_identifiers = None
        self._severity_code = None
        self._target_name = None
        self._target_type = None
        self._title = None
        self._variant_name = None
        self.discriminator = None
        self.description = description
        if exemption_id is not None:
            self.exemption_id = exemption_id
        if issue_type is not None:
            self.issue_type = issue_type
        self.occurrences = occurrences
        if pagination is not None:
            self.pagination = pagination
        if reference_identifiers is not None:
            self.reference_identifiers = reference_identifiers
        self.severity_code = severity_code
        self.target_name = target_name
        self.target_type = target_type
        self.title = title
        self.variant_name = variant_name

    @property
    def description(self):
        """Gets the description of this AllIssuesOccurrenceDetailsResult.  # noqa: E501

        Issue description  # noqa: E501

        :return: The description of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :rtype: str
        """
        return self._description

    @description.setter
    def description(self, description):
        """Sets the description of this AllIssuesOccurrenceDetailsResult.

        Issue description  # noqa: E501

        :param description: The description of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :type: str
        """
        if description is None:
            raise ValueError("Invalid value for `description`, must not be `None`")  # noqa: E501

        self._description = description

    @property
    def exemption_id(self):
        """Gets the exemption_id of this AllIssuesOccurrenceDetailsResult.  # noqa: E501

        ID of Security Test Exemption  # noqa: E501

        :return: The exemption_id of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :rtype: str
        """
        return self._exemption_id

    @exemption_id.setter
    def exemption_id(self, exemption_id):
        """Sets the exemption_id of this AllIssuesOccurrenceDetailsResult.

        ID of Security Test Exemption  # noqa: E501

        :param exemption_id: The exemption_id of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :type: str
        """

        self._exemption_id = exemption_id

    @property
    def issue_type(self):
        """Gets the issue_type of this AllIssuesOccurrenceDetailsResult.  # noqa: E501

        Issue Type  # noqa: E501

        :return: The issue_type of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :rtype: str
        """
        return self._issue_type

    @issue_type.setter
    def issue_type(self, issue_type):
        """Sets the issue_type of this AllIssuesOccurrenceDetailsResult.

        Issue Type  # noqa: E501

        :param issue_type: The issue_type of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :type: str
        """

        self._issue_type = issue_type

    @property
    def occurrences(self):
        """Gets the occurrences of this AllIssuesOccurrenceDetailsResult.  # noqa: E501

        List of occurrences  # noqa: E501

        :return: The occurrences of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :rtype: list[dict(str, object)]
        """
        return self._occurrences

    @occurrences.setter
    def occurrences(self, occurrences):
        """Sets the occurrences of this AllIssuesOccurrenceDetailsResult.

        List of occurrences  # noqa: E501

        :param occurrences: The occurrences of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :type: list[dict(str, object)]
        """
        if occurrences is None:
            raise ValueError("Invalid value for `occurrences`, must not be `None`")  # noqa: E501

        self._occurrences = occurrences

    @property
    def pagination(self):
        """Gets the pagination of this AllIssuesOccurrenceDetailsResult.  # noqa: E501


        :return: The pagination of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :rtype: StoPagination
        """
        return self._pagination

    @pagination.setter
    def pagination(self, pagination):
        """Sets the pagination of this AllIssuesOccurrenceDetailsResult.


        :param pagination: The pagination of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :type: StoPagination
        """

        self._pagination = pagination

    @property
    def reference_identifiers(self):
        """Gets the reference_identifiers of this AllIssuesOccurrenceDetailsResult.  # noqa: E501

        Reference Identifiers  # noqa: E501

        :return: The reference_identifiers of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :rtype: list[RefIds]
        """
        return self._reference_identifiers

    @reference_identifiers.setter
    def reference_identifiers(self, reference_identifiers):
        """Sets the reference_identifiers of this AllIssuesOccurrenceDetailsResult.

        Reference Identifiers  # noqa: E501

        :param reference_identifiers: The reference_identifiers of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :type: list[RefIds]
        """

        self._reference_identifiers = reference_identifiers

    @property
    def severity_code(self):
        """Gets the severity_code of this AllIssuesOccurrenceDetailsResult.  # noqa: E501

        Severity code  # noqa: E501

        :return: The severity_code of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :rtype: str
        """
        return self._severity_code

    @severity_code.setter
    def severity_code(self, severity_code):
        """Sets the severity_code of this AllIssuesOccurrenceDetailsResult.

        Severity code  # noqa: E501

        :param severity_code: The severity_code of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :type: str
        """
        if severity_code is None:
            raise ValueError("Invalid value for `severity_code`, must not be `None`")  # noqa: E501
        allowed_values = ["Critical", "High", "Medium", "Low", "Info", "Unassigned"]  # noqa: E501
        if severity_code not in allowed_values:
            raise ValueError(
                "Invalid value for `severity_code` ({0}), must be one of {1}"  # noqa: E501
                .format(severity_code, allowed_values)
            )

        self._severity_code = severity_code

    @property
    def target_name(self):
        """Gets the target_name of this AllIssuesOccurrenceDetailsResult.  # noqa: E501

        The name of the target of the pipeline step's scan  # noqa: E501

        :return: The target_name of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :rtype: str
        """
        return self._target_name

    @target_name.setter
    def target_name(self, target_name):
        """Sets the target_name of this AllIssuesOccurrenceDetailsResult.

        The name of the target of the pipeline step's scan  # noqa: E501

        :param target_name: The target_name of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :type: str
        """
        if target_name is None:
            raise ValueError("Invalid value for `target_name`, must not be `None`")  # noqa: E501

        self._target_name = target_name

    @property
    def target_type(self):
        """Gets the target_type of this AllIssuesOccurrenceDetailsResult.  # noqa: E501

        Target Type  # noqa: E501

        :return: The target_type of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :rtype: str
        """
        return self._target_type

    @target_type.setter
    def target_type(self, target_type):
        """Sets the target_type of this AllIssuesOccurrenceDetailsResult.

        Target Type  # noqa: E501

        :param target_type: The target_type of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :type: str
        """
        if target_type is None:
            raise ValueError("Invalid value for `target_type`, must not be `None`")  # noqa: E501

        self._target_type = target_type

    @property
    def title(self):
        """Gets the title of this AllIssuesOccurrenceDetailsResult.  # noqa: E501

        Title of the Security Issue  # noqa: E501

        :return: The title of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :rtype: str
        """
        return self._title

    @title.setter
    def title(self, title):
        """Sets the title of this AllIssuesOccurrenceDetailsResult.

        Title of the Security Issue  # noqa: E501

        :param title: The title of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :type: str
        """
        if title is None:
            raise ValueError("Invalid value for `title`, must not be `None`")  # noqa: E501

        self._title = title

    @property
    def variant_name(self):
        """Gets the variant_name of this AllIssuesOccurrenceDetailsResult.  # noqa: E501

        Variant name  # noqa: E501

        :return: The variant_name of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :rtype: str
        """
        return self._variant_name

    @variant_name.setter
    def variant_name(self, variant_name):
        """Sets the variant_name of this AllIssuesOccurrenceDetailsResult.

        Variant name  # noqa: E501

        :param variant_name: The variant_name of this AllIssuesOccurrenceDetailsResult.  # noqa: E501
        :type: str
        """
        if variant_name is None:
            raise ValueError("Invalid value for `variant_name`, must not be `None`")  # noqa: E501

        self._variant_name = variant_name

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
        if issubclass(AllIssuesOccurrenceDetailsResult, dict):
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
        if not isinstance(other, AllIssuesOccurrenceDetailsResult):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
