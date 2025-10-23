# coding: utf-8

import six

from huaweicloudsdkcore.sdk_response import SdkResponse
from huaweicloudsdkcore.utils.http_utils import sanitize_for_serialization


class ListGroupProtectedRefsUserGroupsResponse(SdkResponse):

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    sensitive_list = []

    openapi_types = {
        'body': 'list[ProtectedRefsUserGroupBasicDto]',
        'x_total': 'str'
    }

    attribute_map = {
        'body': 'body',
        'x_total': 'X-Total'
    }

    def __init__(self, body=None, x_total=None):
        r"""ListGroupProtectedRefsUserGroupsResponse

        The model defined in huaweicloud sdk

        :param body: 成员组列表
        :type body: list[:class:`huaweicloudsdkcodehub.v4.ProtectedRefsUserGroupBasicDto`]
        :param x_total: 
        :type x_total: str
        """
        
        super(ListGroupProtectedRefsUserGroupsResponse, self).__init__()

        self._body = None
        self._x_total = None
        self.discriminator = None

        if body is not None:
            self.body = body
        if x_total is not None:
            self.x_total = x_total

    @property
    def body(self):
        r"""Gets the body of this ListGroupProtectedRefsUserGroupsResponse.

        成员组列表

        :return: The body of this ListGroupProtectedRefsUserGroupsResponse.
        :rtype: list[:class:`huaweicloudsdkcodehub.v4.ProtectedRefsUserGroupBasicDto`]
        """
        return self._body

    @body.setter
    def body(self, body):
        r"""Sets the body of this ListGroupProtectedRefsUserGroupsResponse.

        成员组列表

        :param body: The body of this ListGroupProtectedRefsUserGroupsResponse.
        :type body: list[:class:`huaweicloudsdkcodehub.v4.ProtectedRefsUserGroupBasicDto`]
        """
        self._body = body

    @property
    def x_total(self):
        r"""Gets the x_total of this ListGroupProtectedRefsUserGroupsResponse.

        :return: The x_total of this ListGroupProtectedRefsUserGroupsResponse.
        :rtype: str
        """
        return self._x_total

    @x_total.setter
    def x_total(self, x_total):
        r"""Sets the x_total of this ListGroupProtectedRefsUserGroupsResponse.

        :param x_total: The x_total of this ListGroupProtectedRefsUserGroupsResponse.
        :type x_total: str
        """
        self._x_total = x_total

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.openapi_types):
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
                if attr in self.sensitive_list:
                    result[attr] = "****"
                else:
                    result[attr] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        import simplejson as json
        if six.PY2:
            import sys
            reload(sys)
            sys.setdefaultencoding("utf-8")
        return json.dumps(sanitize_for_serialization(self), ensure_ascii=False)

    def __repr__(self):
        """For `print`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, ListGroupProtectedRefsUserGroupsResponse):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
