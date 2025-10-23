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

class ApplicationsApplicationSetGenerator(object):
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
        'cluster_decision_resource': 'ApplicationsDuckTypeGenerator',
        'clusters': 'ApplicationsClusterGenerator',
        'git': 'ApplicationsGitGenerator',
        'list': 'ApplicationsListGenerator',
        'matrix': 'ApplicationsMatrixGenerator',
        'merge': 'ApplicationsMergeGenerator',
        'plugin': 'ApplicationsPluginGenerator',
        'pull_request': 'ApplicationsPullRequestGenerator',
        'scm_provider': 'ApplicationsSCMProviderGenerator',
        'selector': 'V1LabelSelector'
    }

    attribute_map = {
        'cluster_decision_resource': 'clusterDecisionResource',
        'clusters': 'clusters',
        'git': 'git',
        'list': 'list',
        'matrix': 'matrix',
        'merge': 'merge',
        'plugin': 'plugin',
        'pull_request': 'pullRequest',
        'scm_provider': 'scmProvider',
        'selector': 'selector'
    }

    def __init__(self, cluster_decision_resource=None, clusters=None, git=None, list=None, matrix=None, merge=None, plugin=None, pull_request=None, scm_provider=None, selector=None):  # noqa: E501
        """ApplicationsApplicationSetGenerator - a model defined in Swagger"""  # noqa: E501
        self._cluster_decision_resource = None
        self._clusters = None
        self._git = None
        self._list = None
        self._matrix = None
        self._merge = None
        self._plugin = None
        self._pull_request = None
        self._scm_provider = None
        self._selector = None
        self.discriminator = None
        if cluster_decision_resource is not None:
            self.cluster_decision_resource = cluster_decision_resource
        if clusters is not None:
            self.clusters = clusters
        if git is not None:
            self.git = git
        if list is not None:
            self.list = list
        if matrix is not None:
            self.matrix = matrix
        if merge is not None:
            self.merge = merge
        if plugin is not None:
            self.plugin = plugin
        if pull_request is not None:
            self.pull_request = pull_request
        if scm_provider is not None:
            self.scm_provider = scm_provider
        if selector is not None:
            self.selector = selector

    @property
    def cluster_decision_resource(self):
        """Gets the cluster_decision_resource of this ApplicationsApplicationSetGenerator.  # noqa: E501


        :return: The cluster_decision_resource of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :rtype: ApplicationsDuckTypeGenerator
        """
        return self._cluster_decision_resource

    @cluster_decision_resource.setter
    def cluster_decision_resource(self, cluster_decision_resource):
        """Sets the cluster_decision_resource of this ApplicationsApplicationSetGenerator.


        :param cluster_decision_resource: The cluster_decision_resource of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :type: ApplicationsDuckTypeGenerator
        """

        self._cluster_decision_resource = cluster_decision_resource

    @property
    def clusters(self):
        """Gets the clusters of this ApplicationsApplicationSetGenerator.  # noqa: E501


        :return: The clusters of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :rtype: ApplicationsClusterGenerator
        """
        return self._clusters

    @clusters.setter
    def clusters(self, clusters):
        """Sets the clusters of this ApplicationsApplicationSetGenerator.


        :param clusters: The clusters of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :type: ApplicationsClusterGenerator
        """

        self._clusters = clusters

    @property
    def git(self):
        """Gets the git of this ApplicationsApplicationSetGenerator.  # noqa: E501


        :return: The git of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :rtype: ApplicationsGitGenerator
        """
        return self._git

    @git.setter
    def git(self, git):
        """Sets the git of this ApplicationsApplicationSetGenerator.


        :param git: The git of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :type: ApplicationsGitGenerator
        """

        self._git = git

    @property
    def list(self):
        """Gets the list of this ApplicationsApplicationSetGenerator.  # noqa: E501


        :return: The list of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :rtype: ApplicationsListGenerator
        """
        return self._list

    @list.setter
    def list(self, list):
        """Sets the list of this ApplicationsApplicationSetGenerator.


        :param list: The list of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :type: ApplicationsListGenerator
        """

        self._list = list

    @property
    def matrix(self):
        """Gets the matrix of this ApplicationsApplicationSetGenerator.  # noqa: E501


        :return: The matrix of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :rtype: ApplicationsMatrixGenerator
        """
        return self._matrix

    @matrix.setter
    def matrix(self, matrix):
        """Sets the matrix of this ApplicationsApplicationSetGenerator.


        :param matrix: The matrix of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :type: ApplicationsMatrixGenerator
        """

        self._matrix = matrix

    @property
    def merge(self):
        """Gets the merge of this ApplicationsApplicationSetGenerator.  # noqa: E501


        :return: The merge of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :rtype: ApplicationsMergeGenerator
        """
        return self._merge

    @merge.setter
    def merge(self, merge):
        """Sets the merge of this ApplicationsApplicationSetGenerator.


        :param merge: The merge of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :type: ApplicationsMergeGenerator
        """

        self._merge = merge

    @property
    def plugin(self):
        """Gets the plugin of this ApplicationsApplicationSetGenerator.  # noqa: E501


        :return: The plugin of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :rtype: ApplicationsPluginGenerator
        """
        return self._plugin

    @plugin.setter
    def plugin(self, plugin):
        """Sets the plugin of this ApplicationsApplicationSetGenerator.


        :param plugin: The plugin of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :type: ApplicationsPluginGenerator
        """

        self._plugin = plugin

    @property
    def pull_request(self):
        """Gets the pull_request of this ApplicationsApplicationSetGenerator.  # noqa: E501


        :return: The pull_request of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :rtype: ApplicationsPullRequestGenerator
        """
        return self._pull_request

    @pull_request.setter
    def pull_request(self, pull_request):
        """Sets the pull_request of this ApplicationsApplicationSetGenerator.


        :param pull_request: The pull_request of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :type: ApplicationsPullRequestGenerator
        """

        self._pull_request = pull_request

    @property
    def scm_provider(self):
        """Gets the scm_provider of this ApplicationsApplicationSetGenerator.  # noqa: E501


        :return: The scm_provider of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :rtype: ApplicationsSCMProviderGenerator
        """
        return self._scm_provider

    @scm_provider.setter
    def scm_provider(self, scm_provider):
        """Sets the scm_provider of this ApplicationsApplicationSetGenerator.


        :param scm_provider: The scm_provider of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :type: ApplicationsSCMProviderGenerator
        """

        self._scm_provider = scm_provider

    @property
    def selector(self):
        """Gets the selector of this ApplicationsApplicationSetGenerator.  # noqa: E501


        :return: The selector of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :rtype: V1LabelSelector
        """
        return self._selector

    @selector.setter
    def selector(self, selector):
        """Sets the selector of this ApplicationsApplicationSetGenerator.


        :param selector: The selector of this ApplicationsApplicationSetGenerator.  # noqa: E501
        :type: V1LabelSelector
        """

        self._selector = selector

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
        if issubclass(ApplicationsApplicationSetGenerator, dict):
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
        if not isinstance(other, ApplicationsApplicationSetGenerator):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
