# coding: utf-8

import six

from huaweicloudsdkcore.sdk_response import SdkResponse
from huaweicloudsdkcore.utils.http_utils import sanitize_for_serialization


class ShowGroupE2eSettingResponse(SdkResponse):

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    sensitive_list = []

    openapi_types = {
        'e2e_policies': 'E2ePolicyDto',
        'req': 'ReqSettingDto',
        'link': 'LinkSettingDto'
    }

    attribute_map = {
        'e2e_policies': 'e2e_policies',
        'req': 'req',
        'link': 'link'
    }

    def __init__(self, e2e_policies=None, req=None, link=None):
        r"""ShowGroupE2eSettingResponse

        The model defined in huaweicloud sdk

        :param e2e_policies: 
        :type e2e_policies: :class:`huaweicloudsdkcodehub.v4.E2ePolicyDto`
        :param req: 
        :type req: :class:`huaweicloudsdkcodehub.v4.ReqSettingDto`
        :param link: 
        :type link: :class:`huaweicloudsdkcodehub.v4.LinkSettingDto`
        """
        
        super(ShowGroupE2eSettingResponse, self).__init__()

        self._e2e_policies = None
        self._req = None
        self._link = None
        self.discriminator = None

        if e2e_policies is not None:
            self.e2e_policies = e2e_policies
        if req is not None:
            self.req = req
        if link is not None:
            self.link = link

    @property
    def e2e_policies(self):
        r"""Gets the e2e_policies of this ShowGroupE2eSettingResponse.

        :return: The e2e_policies of this ShowGroupE2eSettingResponse.
        :rtype: :class:`huaweicloudsdkcodehub.v4.E2ePolicyDto`
        """
        return self._e2e_policies

    @e2e_policies.setter
    def e2e_policies(self, e2e_policies):
        r"""Sets the e2e_policies of this ShowGroupE2eSettingResponse.

        :param e2e_policies: The e2e_policies of this ShowGroupE2eSettingResponse.
        :type e2e_policies: :class:`huaweicloudsdkcodehub.v4.E2ePolicyDto`
        """
        self._e2e_policies = e2e_policies

    @property
    def req(self):
        r"""Gets the req of this ShowGroupE2eSettingResponse.

        :return: The req of this ShowGroupE2eSettingResponse.
        :rtype: :class:`huaweicloudsdkcodehub.v4.ReqSettingDto`
        """
        return self._req

    @req.setter
    def req(self, req):
        r"""Sets the req of this ShowGroupE2eSettingResponse.

        :param req: The req of this ShowGroupE2eSettingResponse.
        :type req: :class:`huaweicloudsdkcodehub.v4.ReqSettingDto`
        """
        self._req = req

    @property
    def link(self):
        r"""Gets the link of this ShowGroupE2eSettingResponse.

        :return: The link of this ShowGroupE2eSettingResponse.
        :rtype: :class:`huaweicloudsdkcodehub.v4.LinkSettingDto`
        """
        return self._link

    @link.setter
    def link(self, link):
        r"""Sets the link of this ShowGroupE2eSettingResponse.

        :param link: The link of this ShowGroupE2eSettingResponse.
        :type link: :class:`huaweicloudsdkcodehub.v4.LinkSettingDto`
        """
        self._link = link

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
        if not isinstance(other, ShowGroupE2eSettingResponse):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
