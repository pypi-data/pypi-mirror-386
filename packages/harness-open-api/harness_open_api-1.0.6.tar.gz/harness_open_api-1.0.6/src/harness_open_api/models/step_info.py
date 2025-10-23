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

class StepInfo(object):
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
        'baseline_variant': 'str',
        'scan_id': 'str',
        'scan_tool': 'str',
        'stage_id': 'str',
        'step_id': 'str',
        'subproduct': 'str',
        'target_id': 'str',
        'target_name': 'str',
        'target_type': 'str',
        'target_variant': 'str'
    }

    attribute_map = {
        'baseline_variant': 'baselineVariant',
        'scan_id': 'scanId',
        'scan_tool': 'scanTool',
        'stage_id': 'stageId',
        'step_id': 'stepId',
        'subproduct': 'subproduct',
        'target_id': 'targetId',
        'target_name': 'targetName',
        'target_type': 'targetType',
        'target_variant': 'targetVariant'
    }

    def __init__(self, baseline_variant=None, scan_id=None, scan_tool=None, stage_id=None, step_id=None, subproduct=None, target_id=None, target_name=None, target_type=None, target_variant=None):  # noqa: E501
        """StepInfo - a model defined in Swagger"""  # noqa: E501
        self._baseline_variant = None
        self._scan_id = None
        self._scan_tool = None
        self._stage_id = None
        self._step_id = None
        self._subproduct = None
        self._target_id = None
        self._target_name = None
        self._target_type = None
        self._target_variant = None
        self.discriminator = None
        if baseline_variant is not None:
            self.baseline_variant = baseline_variant
        self.scan_id = scan_id
        self.scan_tool = scan_tool
        self.stage_id = stage_id
        self.step_id = step_id
        if subproduct is not None:
            self.subproduct = subproduct
        self.target_id = target_id
        self.target_name = target_name
        self.target_type = target_type
        self.target_variant = target_variant

    @property
    def baseline_variant(self):
        """Gets the baseline_variant of this StepInfo.  # noqa: E501

        A short description of the baseline target variant for the pipeline step's scan diff  # noqa: E501

        :return: The baseline_variant of this StepInfo.  # noqa: E501
        :rtype: str
        """
        return self._baseline_variant

    @baseline_variant.setter
    def baseline_variant(self, baseline_variant):
        """Sets the baseline_variant of this StepInfo.

        A short description of the baseline target variant for the pipeline step's scan diff  # noqa: E501

        :param baseline_variant: The baseline_variant of this StepInfo.  # noqa: E501
        :type: str
        """

        self._baseline_variant = baseline_variant

    @property
    def scan_id(self):
        """Gets the scan_id of this StepInfo.  # noqa: E501

        Scan id  # noqa: E501

        :return: The scan_id of this StepInfo.  # noqa: E501
        :rtype: str
        """
        return self._scan_id

    @scan_id.setter
    def scan_id(self, scan_id):
        """Sets the scan_id of this StepInfo.

        Scan id  # noqa: E501

        :param scan_id: The scan_id of this StepInfo.  # noqa: E501
        :type: str
        """
        if scan_id is None:
            raise ValueError("Invalid value for `scan_id`, must not be `None`")  # noqa: E501

        self._scan_id = scan_id

    @property
    def scan_tool(self):
        """Gets the scan_tool of this StepInfo.  # noqa: E501

        Product name of the scan tool used in this step  # noqa: E501

        :return: The scan_tool of this StepInfo.  # noqa: E501
        :rtype: str
        """
        return self._scan_tool

    @scan_tool.setter
    def scan_tool(self, scan_tool):
        """Sets the scan_tool of this StepInfo.

        Product name of the scan tool used in this step  # noqa: E501

        :param scan_tool: The scan_tool of this StepInfo.  # noqa: E501
        :type: str
        """
        if scan_tool is None:
            raise ValueError("Invalid value for `scan_tool`, must not be `None`")  # noqa: E501

        self._scan_tool = scan_tool

    @property
    def stage_id(self):
        """Gets the stage_id of this StepInfo.  # noqa: E501


        :return: The stage_id of this StepInfo.  # noqa: E501
        :rtype: str
        """
        return self._stage_id

    @stage_id.setter
    def stage_id(self, stage_id):
        """Sets the stage_id of this StepInfo.


        :param stage_id: The stage_id of this StepInfo.  # noqa: E501
        :type: str
        """
        if stage_id is None:
            raise ValueError("Invalid value for `stage_id`, must not be `None`")  # noqa: E501

        self._stage_id = stage_id

    @property
    def step_id(self):
        """Gets the step_id of this StepInfo.  # noqa: E501


        :return: The step_id of this StepInfo.  # noqa: E501
        :rtype: str
        """
        return self._step_id

    @step_id.setter
    def step_id(self, step_id):
        """Sets the step_id of this StepInfo.


        :param step_id: The step_id of this StepInfo.  # noqa: E501
        :type: str
        """
        if step_id is None:
            raise ValueError("Invalid value for `step_id`, must not be `None`")  # noqa: E501

        self._step_id = step_id

    @property
    def subproduct(self):
        """Gets the subproduct of this StepInfo.  # noqa: E501

        The subproduct that identified this Security Issue  # noqa: E501

        :return: The subproduct of this StepInfo.  # noqa: E501
        :rtype: str
        """
        return self._subproduct

    @subproduct.setter
    def subproduct(self, subproduct):
        """Sets the subproduct of this StepInfo.

        The subproduct that identified this Security Issue  # noqa: E501

        :param subproduct: The subproduct of this StepInfo.  # noqa: E501
        :type: str
        """

        self._subproduct = subproduct

    @property
    def target_id(self):
        """Gets the target_id of this StepInfo.  # noqa: E501

        The ID of the target of the pipeline step's scan  # noqa: E501

        :return: The target_id of this StepInfo.  # noqa: E501
        :rtype: str
        """
        return self._target_id

    @target_id.setter
    def target_id(self, target_id):
        """Sets the target_id of this StepInfo.

        The ID of the target of the pipeline step's scan  # noqa: E501

        :param target_id: The target_id of this StepInfo.  # noqa: E501
        :type: str
        """
        if target_id is None:
            raise ValueError("Invalid value for `target_id`, must not be `None`")  # noqa: E501

        self._target_id = target_id

    @property
    def target_name(self):
        """Gets the target_name of this StepInfo.  # noqa: E501

        The name of the target of the pipeline step's scan  # noqa: E501

        :return: The target_name of this StepInfo.  # noqa: E501
        :rtype: str
        """
        return self._target_name

    @target_name.setter
    def target_name(self, target_name):
        """Sets the target_name of this StepInfo.

        The name of the target of the pipeline step's scan  # noqa: E501

        :param target_name: The target_name of this StepInfo.  # noqa: E501
        :type: str
        """
        if target_name is None:
            raise ValueError("Invalid value for `target_name`, must not be `None`")  # noqa: E501

        self._target_name = target_name

    @property
    def target_type(self):
        """Gets the target_type of this StepInfo.  # noqa: E501

        The type of the target of the pipeline step's scan  # noqa: E501

        :return: The target_type of this StepInfo.  # noqa: E501
        :rtype: str
        """
        return self._target_type

    @target_type.setter
    def target_type(self, target_type):
        """Sets the target_type of this StepInfo.

        The type of the target of the pipeline step's scan  # noqa: E501

        :param target_type: The target_type of this StepInfo.  # noqa: E501
        :type: str
        """
        if target_type is None:
            raise ValueError("Invalid value for `target_type`, must not be `None`")  # noqa: E501
        allowed_values = ["repository", "container", "instance", "configuration"]  # noqa: E501
        if target_type not in allowed_values:
            raise ValueError(
                "Invalid value for `target_type` ({0}), must be one of {1}"  # noqa: E501
                .format(target_type, allowed_values)
            )

        self._target_type = target_type

    @property
    def target_variant(self):
        """Gets the target_variant of this StepInfo.  # noqa: E501

        A short description of the target variant of the pipeline step's scan  # noqa: E501

        :return: The target_variant of this StepInfo.  # noqa: E501
        :rtype: str
        """
        return self._target_variant

    @target_variant.setter
    def target_variant(self, target_variant):
        """Sets the target_variant of this StepInfo.

        A short description of the target variant of the pipeline step's scan  # noqa: E501

        :param target_variant: The target_variant of this StepInfo.  # noqa: E501
        :type: str
        """
        if target_variant is None:
            raise ValueError("Invalid value for `target_variant`, must not be `None`")  # noqa: E501

        self._target_variant = target_variant

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
        if issubclass(StepInfo, dict):
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
        if not isinstance(other, StepInfo):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
