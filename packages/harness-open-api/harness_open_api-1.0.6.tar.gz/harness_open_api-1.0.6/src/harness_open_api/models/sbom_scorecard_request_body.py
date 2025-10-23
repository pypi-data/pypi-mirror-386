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

class SbomScorecardRequestBody(object):
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
        'account_id': 'str',
        'avg_score': 'str',
        'category': 'list[CategoryScorecard]',
        'creation_on': 'str',
        'max_score': 'str',
        'orchestration_id': 'str',
        'org_id': 'str',
        'project_id': 'str',
        'sbom_details': 'SbomDetailsForScorecard',
        'score_card_info': 'ScorecardInfo'
    }

    attribute_map = {
        'account_id': 'account_id',
        'avg_score': 'avg_score',
        'category': 'category',
        'creation_on': 'creation_on',
        'max_score': 'max_score',
        'orchestration_id': 'orchestration_id',
        'org_id': 'org_id',
        'project_id': 'project_id',
        'sbom_details': 'sbom_details',
        'score_card_info': 'score_card_info'
    }

    def __init__(self, account_id=None, avg_score=None, category=None, creation_on=None, max_score=None, orchestration_id=None, org_id=None, project_id=None, sbom_details=None, score_card_info=None):  # noqa: E501
        """SbomScorecardRequestBody - a model defined in Swagger"""  # noqa: E501
        self._account_id = None
        self._avg_score = None
        self._category = None
        self._creation_on = None
        self._max_score = None
        self._orchestration_id = None
        self._org_id = None
        self._project_id = None
        self._sbom_details = None
        self._score_card_info = None
        self.discriminator = None
        if account_id is not None:
            self.account_id = account_id
        if avg_score is not None:
            self.avg_score = avg_score
        if category is not None:
            self.category = category
        if creation_on is not None:
            self.creation_on = creation_on
        if max_score is not None:
            self.max_score = max_score
        if orchestration_id is not None:
            self.orchestration_id = orchestration_id
        if org_id is not None:
            self.org_id = org_id
        if project_id is not None:
            self.project_id = project_id
        if sbom_details is not None:
            self.sbom_details = sbom_details
        if score_card_info is not None:
            self.score_card_info = score_card_info

    @property
    def account_id(self):
        """Gets the account_id of this SbomScorecardRequestBody.  # noqa: E501


        :return: The account_id of this SbomScorecardRequestBody.  # noqa: E501
        :rtype: str
        """
        return self._account_id

    @account_id.setter
    def account_id(self, account_id):
        """Sets the account_id of this SbomScorecardRequestBody.


        :param account_id: The account_id of this SbomScorecardRequestBody.  # noqa: E501
        :type: str
        """

        self._account_id = account_id

    @property
    def avg_score(self):
        """Gets the avg_score of this SbomScorecardRequestBody.  # noqa: E501


        :return: The avg_score of this SbomScorecardRequestBody.  # noqa: E501
        :rtype: str
        """
        return self._avg_score

    @avg_score.setter
    def avg_score(self, avg_score):
        """Sets the avg_score of this SbomScorecardRequestBody.


        :param avg_score: The avg_score of this SbomScorecardRequestBody.  # noqa: E501
        :type: str
        """

        self._avg_score = avg_score

    @property
    def category(self):
        """Gets the category of this SbomScorecardRequestBody.  # noqa: E501


        :return: The category of this SbomScorecardRequestBody.  # noqa: E501
        :rtype: list[CategoryScorecard]
        """
        return self._category

    @category.setter
    def category(self, category):
        """Sets the category of this SbomScorecardRequestBody.


        :param category: The category of this SbomScorecardRequestBody.  # noqa: E501
        :type: list[CategoryScorecard]
        """

        self._category = category

    @property
    def creation_on(self):
        """Gets the creation_on of this SbomScorecardRequestBody.  # noqa: E501


        :return: The creation_on of this SbomScorecardRequestBody.  # noqa: E501
        :rtype: str
        """
        return self._creation_on

    @creation_on.setter
    def creation_on(self, creation_on):
        """Sets the creation_on of this SbomScorecardRequestBody.


        :param creation_on: The creation_on of this SbomScorecardRequestBody.  # noqa: E501
        :type: str
        """

        self._creation_on = creation_on

    @property
    def max_score(self):
        """Gets the max_score of this SbomScorecardRequestBody.  # noqa: E501


        :return: The max_score of this SbomScorecardRequestBody.  # noqa: E501
        :rtype: str
        """
        return self._max_score

    @max_score.setter
    def max_score(self, max_score):
        """Sets the max_score of this SbomScorecardRequestBody.


        :param max_score: The max_score of this SbomScorecardRequestBody.  # noqa: E501
        :type: str
        """

        self._max_score = max_score

    @property
    def orchestration_id(self):
        """Gets the orchestration_id of this SbomScorecardRequestBody.  # noqa: E501


        :return: The orchestration_id of this SbomScorecardRequestBody.  # noqa: E501
        :rtype: str
        """
        return self._orchestration_id

    @orchestration_id.setter
    def orchestration_id(self, orchestration_id):
        """Sets the orchestration_id of this SbomScorecardRequestBody.


        :param orchestration_id: The orchestration_id of this SbomScorecardRequestBody.  # noqa: E501
        :type: str
        """

        self._orchestration_id = orchestration_id

    @property
    def org_id(self):
        """Gets the org_id of this SbomScorecardRequestBody.  # noqa: E501


        :return: The org_id of this SbomScorecardRequestBody.  # noqa: E501
        :rtype: str
        """
        return self._org_id

    @org_id.setter
    def org_id(self, org_id):
        """Sets the org_id of this SbomScorecardRequestBody.


        :param org_id: The org_id of this SbomScorecardRequestBody.  # noqa: E501
        :type: str
        """

        self._org_id = org_id

    @property
    def project_id(self):
        """Gets the project_id of this SbomScorecardRequestBody.  # noqa: E501


        :return: The project_id of this SbomScorecardRequestBody.  # noqa: E501
        :rtype: str
        """
        return self._project_id

    @project_id.setter
    def project_id(self, project_id):
        """Sets the project_id of this SbomScorecardRequestBody.


        :param project_id: The project_id of this SbomScorecardRequestBody.  # noqa: E501
        :type: str
        """

        self._project_id = project_id

    @property
    def sbom_details(self):
        """Gets the sbom_details of this SbomScorecardRequestBody.  # noqa: E501


        :return: The sbom_details of this SbomScorecardRequestBody.  # noqa: E501
        :rtype: SbomDetailsForScorecard
        """
        return self._sbom_details

    @sbom_details.setter
    def sbom_details(self, sbom_details):
        """Sets the sbom_details of this SbomScorecardRequestBody.


        :param sbom_details: The sbom_details of this SbomScorecardRequestBody.  # noqa: E501
        :type: SbomDetailsForScorecard
        """

        self._sbom_details = sbom_details

    @property
    def score_card_info(self):
        """Gets the score_card_info of this SbomScorecardRequestBody.  # noqa: E501


        :return: The score_card_info of this SbomScorecardRequestBody.  # noqa: E501
        :rtype: ScorecardInfo
        """
        return self._score_card_info

    @score_card_info.setter
    def score_card_info(self, score_card_info):
        """Sets the score_card_info of this SbomScorecardRequestBody.


        :param score_card_info: The score_card_info of this SbomScorecardRequestBody.  # noqa: E501
        :type: ScorecardInfo
        """

        self._score_card_info = score_card_info

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
        if issubclass(SbomScorecardRequestBody, dict):
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
        if not isinstance(other, SbomScorecardRequestBody):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
