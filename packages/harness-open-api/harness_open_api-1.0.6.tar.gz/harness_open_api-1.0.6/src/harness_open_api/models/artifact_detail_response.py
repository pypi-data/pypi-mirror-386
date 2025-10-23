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

class ArtifactDetailResponse(object):
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
        'build_pipeline_execution_id': 'str',
        'build_pipeline_id': 'str',
        'build_pipeline_name': 'str',
        'components_count': 'int',
        'id': 'str',
        'metadata': 'dict(str, object)',
        'name': 'str',
        'non_prod_env_count': 'int',
        'orchestration_id': 'str',
        'prod_env_count': 'int',
        'scorecard': 'ArtifactDetailResponseScorecard',
        'sto_issue_count': 'StoIssueCount',
        'tag': 'str',
        'updated': 'str',
        'url': 'str'
    }

    attribute_map = {
        'build_pipeline_execution_id': 'build_pipeline_execution_id',
        'build_pipeline_id': 'build_pipeline_id',
        'build_pipeline_name': 'build_pipeline_name',
        'components_count': 'components_count',
        'id': 'id',
        'metadata': 'metadata',
        'name': 'name',
        'non_prod_env_count': 'non_prod_env_count',
        'orchestration_id': 'orchestration_id',
        'prod_env_count': 'prod_env_count',
        'scorecard': 'scorecard',
        'sto_issue_count': 'sto_issue_count',
        'tag': 'tag',
        'updated': 'updated',
        'url': 'url'
    }

    def __init__(self, build_pipeline_execution_id=None, build_pipeline_id=None, build_pipeline_name=None, components_count=None, id=None, metadata=None, name=None, non_prod_env_count=None, orchestration_id=None, prod_env_count=None, scorecard=None, sto_issue_count=None, tag=None, updated=None, url=None):  # noqa: E501
        """ArtifactDetailResponse - a model defined in Swagger"""  # noqa: E501
        self._build_pipeline_execution_id = None
        self._build_pipeline_id = None
        self._build_pipeline_name = None
        self._components_count = None
        self._id = None
        self._metadata = None
        self._name = None
        self._non_prod_env_count = None
        self._orchestration_id = None
        self._prod_env_count = None
        self._scorecard = None
        self._sto_issue_count = None
        self._tag = None
        self._updated = None
        self._url = None
        self.discriminator = None
        if build_pipeline_execution_id is not None:
            self.build_pipeline_execution_id = build_pipeline_execution_id
        if build_pipeline_id is not None:
            self.build_pipeline_id = build_pipeline_id
        if build_pipeline_name is not None:
            self.build_pipeline_name = build_pipeline_name
        if components_count is not None:
            self.components_count = components_count
        self.id = id
        if metadata is not None:
            self.metadata = metadata
        self.name = name
        if non_prod_env_count is not None:
            self.non_prod_env_count = non_prod_env_count
        if orchestration_id is not None:
            self.orchestration_id = orchestration_id
        if prod_env_count is not None:
            self.prod_env_count = prod_env_count
        if scorecard is not None:
            self.scorecard = scorecard
        if sto_issue_count is not None:
            self.sto_issue_count = sto_issue_count
        self.tag = tag
        if updated is not None:
            self.updated = updated
        if url is not None:
            self.url = url

    @property
    def build_pipeline_execution_id(self):
        """Gets the build_pipeline_execution_id of this ArtifactDetailResponse.  # noqa: E501

        Pipeline execution id of build pipeline used to orchestrate the artifact  # noqa: E501

        :return: The build_pipeline_execution_id of this ArtifactDetailResponse.  # noqa: E501
        :rtype: str
        """
        return self._build_pipeline_execution_id

    @build_pipeline_execution_id.setter
    def build_pipeline_execution_id(self, build_pipeline_execution_id):
        """Sets the build_pipeline_execution_id of this ArtifactDetailResponse.

        Pipeline execution id of build pipeline used to orchestrate the artifact  # noqa: E501

        :param build_pipeline_execution_id: The build_pipeline_execution_id of this ArtifactDetailResponse.  # noqa: E501
        :type: str
        """

        self._build_pipeline_execution_id = build_pipeline_execution_id

    @property
    def build_pipeline_id(self):
        """Gets the build_pipeline_id of this ArtifactDetailResponse.  # noqa: E501

        Pipeline id of build pipeline used to orchestrate the artifact  # noqa: E501

        :return: The build_pipeline_id of this ArtifactDetailResponse.  # noqa: E501
        :rtype: str
        """
        return self._build_pipeline_id

    @build_pipeline_id.setter
    def build_pipeline_id(self, build_pipeline_id):
        """Sets the build_pipeline_id of this ArtifactDetailResponse.

        Pipeline id of build pipeline used to orchestrate the artifact  # noqa: E501

        :param build_pipeline_id: The build_pipeline_id of this ArtifactDetailResponse.  # noqa: E501
        :type: str
        """

        self._build_pipeline_id = build_pipeline_id

    @property
    def build_pipeline_name(self):
        """Gets the build_pipeline_name of this ArtifactDetailResponse.  # noqa: E501

        Pipeline name of build pipeline used to orchestrate the artifact  # noqa: E501

        :return: The build_pipeline_name of this ArtifactDetailResponse.  # noqa: E501
        :rtype: str
        """
        return self._build_pipeline_name

    @build_pipeline_name.setter
    def build_pipeline_name(self, build_pipeline_name):
        """Sets the build_pipeline_name of this ArtifactDetailResponse.

        Pipeline name of build pipeline used to orchestrate the artifact  # noqa: E501

        :param build_pipeline_name: The build_pipeline_name of this ArtifactDetailResponse.  # noqa: E501
        :type: str
        """

        self._build_pipeline_name = build_pipeline_name

    @property
    def components_count(self):
        """Gets the components_count of this ArtifactDetailResponse.  # noqa: E501

        Count of the normalized components within the artifact  # noqa: E501

        :return: The components_count of this ArtifactDetailResponse.  # noqa: E501
        :rtype: int
        """
        return self._components_count

    @components_count.setter
    def components_count(self, components_count):
        """Sets the components_count of this ArtifactDetailResponse.

        Count of the normalized components within the artifact  # noqa: E501

        :param components_count: The components_count of this ArtifactDetailResponse.  # noqa: E501
        :type: int
        """

        self._components_count = components_count

    @property
    def id(self):
        """Gets the id of this ArtifactDetailResponse.  # noqa: E501

        Artifact Identifier  # noqa: E501

        :return: The id of this ArtifactDetailResponse.  # noqa: E501
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this ArtifactDetailResponse.

        Artifact Identifier  # noqa: E501

        :param id: The id of this ArtifactDetailResponse.  # noqa: E501
        :type: str
        """
        if id is None:
            raise ValueError("Invalid value for `id`, must not be `None`")  # noqa: E501

        self._id = id

    @property
    def metadata(self):
        """Gets the metadata of this ArtifactDetailResponse.  # noqa: E501


        :return: The metadata of this ArtifactDetailResponse.  # noqa: E501
        :rtype: dict(str, object)
        """
        return self._metadata

    @metadata.setter
    def metadata(self, metadata):
        """Sets the metadata of this ArtifactDetailResponse.


        :param metadata: The metadata of this ArtifactDetailResponse.  # noqa: E501
        :type: dict(str, object)
        """

        self._metadata = metadata

    @property
    def name(self):
        """Gets the name of this ArtifactDetailResponse.  # noqa: E501

        Name of the artifact  # noqa: E501

        :return: The name of this ArtifactDetailResponse.  # noqa: E501
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this ArtifactDetailResponse.

        Name of the artifact  # noqa: E501

        :param name: The name of this ArtifactDetailResponse.  # noqa: E501
        :type: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")  # noqa: E501

        self._name = name

    @property
    def non_prod_env_count(self):
        """Gets the non_prod_env_count of this ArtifactDetailResponse.  # noqa: E501

        Count of pre-production env in which artifact is deploye  # noqa: E501

        :return: The non_prod_env_count of this ArtifactDetailResponse.  # noqa: E501
        :rtype: int
        """
        return self._non_prod_env_count

    @non_prod_env_count.setter
    def non_prod_env_count(self, non_prod_env_count):
        """Sets the non_prod_env_count of this ArtifactDetailResponse.

        Count of pre-production env in which artifact is deploye  # noqa: E501

        :param non_prod_env_count: The non_prod_env_count of this ArtifactDetailResponse.  # noqa: E501
        :type: int
        """

        self._non_prod_env_count = non_prod_env_count

    @property
    def orchestration_id(self):
        """Gets the orchestration_id of this ArtifactDetailResponse.  # noqa: E501

        Orchestration step identifier  # noqa: E501

        :return: The orchestration_id of this ArtifactDetailResponse.  # noqa: E501
        :rtype: str
        """
        return self._orchestration_id

    @orchestration_id.setter
    def orchestration_id(self, orchestration_id):
        """Sets the orchestration_id of this ArtifactDetailResponse.

        Orchestration step identifier  # noqa: E501

        :param orchestration_id: The orchestration_id of this ArtifactDetailResponse.  # noqa: E501
        :type: str
        """

        self._orchestration_id = orchestration_id

    @property
    def prod_env_count(self):
        """Gets the prod_env_count of this ArtifactDetailResponse.  # noqa: E501

        Count of production env in which artifact is deployed  # noqa: E501

        :return: The prod_env_count of this ArtifactDetailResponse.  # noqa: E501
        :rtype: int
        """
        return self._prod_env_count

    @prod_env_count.setter
    def prod_env_count(self, prod_env_count):
        """Sets the prod_env_count of this ArtifactDetailResponse.

        Count of production env in which artifact is deployed  # noqa: E501

        :param prod_env_count: The prod_env_count of this ArtifactDetailResponse.  # noqa: E501
        :type: int
        """

        self._prod_env_count = prod_env_count

    @property
    def scorecard(self):
        """Gets the scorecard of this ArtifactDetailResponse.  # noqa: E501


        :return: The scorecard of this ArtifactDetailResponse.  # noqa: E501
        :rtype: ArtifactDetailResponseScorecard
        """
        return self._scorecard

    @scorecard.setter
    def scorecard(self, scorecard):
        """Sets the scorecard of this ArtifactDetailResponse.


        :param scorecard: The scorecard of this ArtifactDetailResponse.  # noqa: E501
        :type: ArtifactDetailResponseScorecard
        """

        self._scorecard = scorecard

    @property
    def sto_issue_count(self):
        """Gets the sto_issue_count of this ArtifactDetailResponse.  # noqa: E501


        :return: The sto_issue_count of this ArtifactDetailResponse.  # noqa: E501
        :rtype: StoIssueCount
        """
        return self._sto_issue_count

    @sto_issue_count.setter
    def sto_issue_count(self, sto_issue_count):
        """Sets the sto_issue_count of this ArtifactDetailResponse.


        :param sto_issue_count: The sto_issue_count of this ArtifactDetailResponse.  # noqa: E501
        :type: StoIssueCount
        """

        self._sto_issue_count = sto_issue_count

    @property
    def tag(self):
        """Gets the tag of this ArtifactDetailResponse.  # noqa: E501

        Version of the artifact  # noqa: E501

        :return: The tag of this ArtifactDetailResponse.  # noqa: E501
        :rtype: str
        """
        return self._tag

    @tag.setter
    def tag(self, tag):
        """Sets the tag of this ArtifactDetailResponse.

        Version of the artifact  # noqa: E501

        :param tag: The tag of this ArtifactDetailResponse.  # noqa: E501
        :type: str
        """
        if tag is None:
            raise ValueError("Invalid value for `tag`, must not be `None`")  # noqa: E501

        self._tag = tag

    @property
    def updated(self):
        """Gets the updated of this ArtifactDetailResponse.  # noqa: E501

        Last Updated time of artifact  # noqa: E501

        :return: The updated of this ArtifactDetailResponse.  # noqa: E501
        :rtype: str
        """
        return self._updated

    @updated.setter
    def updated(self, updated):
        """Sets the updated of this ArtifactDetailResponse.

        Last Updated time of artifact  # noqa: E501

        :param updated: The updated of this ArtifactDetailResponse.  # noqa: E501
        :type: str
        """

        self._updated = updated

    @property
    def url(self):
        """Gets the url of this ArtifactDetailResponse.  # noqa: E501

        Registry url of the artifact  # noqa: E501

        :return: The url of this ArtifactDetailResponse.  # noqa: E501
        :rtype: str
        """
        return self._url

    @url.setter
    def url(self, url):
        """Sets the url of this ArtifactDetailResponse.

        Registry url of the artifact  # noqa: E501

        :param url: The url of this ArtifactDetailResponse.  # noqa: E501
        :type: str
        """

        self._url = url

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
        if issubclass(ArtifactDetailResponse, dict):
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
        if not isinstance(other, ArtifactDetailResponse):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
