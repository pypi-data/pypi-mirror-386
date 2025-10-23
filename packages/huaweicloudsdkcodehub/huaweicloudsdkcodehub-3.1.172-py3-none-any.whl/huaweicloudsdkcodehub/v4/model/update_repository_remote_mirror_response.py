# coding: utf-8

import six

from huaweicloudsdkcore.sdk_response import SdkResponse
from huaweicloudsdkcore.utils.http_utils import sanitize_for_serialization


class UpdateRepositoryRemoteMirrorResponse(SdkResponse):

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    sensitive_list = []

    openapi_types = {
        'url': 'str',
        'mirroring_enabled': 'bool',
        'endpoint_uuid': 'str',
        'sync_branch_type': 'str'
    }

    attribute_map = {
        'url': 'url',
        'mirroring_enabled': 'mirroring_enabled',
        'endpoint_uuid': 'endpoint_uuid',
        'sync_branch_type': 'sync_branch_type'
    }

    def __init__(self, url=None, mirroring_enabled=None, endpoint_uuid=None, sync_branch_type=None):
        r"""UpdateRepositoryRemoteMirrorResponse

        The model defined in huaweicloud sdk

        :param url: **参数解释：**  源仓地址。 **约束限制：** 不涉及。
        :type url: str
        :param mirroring_enabled: **参数解释：**  开启定时同步 **取值范围：** - true，不开启定时同步。 - false，开启定时同步。 **约束限制：** 不涉及。
        :type mirroring_enabled: bool
        :param endpoint_uuid: **参数解释：**  拓展点UUID。 **约束限制：** 不涉及。
        :type endpoint_uuid: str
        :param sync_branch_type: **参数解释：**  分支同步。 **取值范围：** - all，同步全部分支。 - default，同步默认分支。 **约束限制：** 不涉及。
        :type sync_branch_type: str
        """
        
        super(UpdateRepositoryRemoteMirrorResponse, self).__init__()

        self._url = None
        self._mirroring_enabled = None
        self._endpoint_uuid = None
        self._sync_branch_type = None
        self.discriminator = None

        if url is not None:
            self.url = url
        if mirroring_enabled is not None:
            self.mirroring_enabled = mirroring_enabled
        if endpoint_uuid is not None:
            self.endpoint_uuid = endpoint_uuid
        if sync_branch_type is not None:
            self.sync_branch_type = sync_branch_type

    @property
    def url(self):
        r"""Gets the url of this UpdateRepositoryRemoteMirrorResponse.

        **参数解释：**  源仓地址。 **约束限制：** 不涉及。

        :return: The url of this UpdateRepositoryRemoteMirrorResponse.
        :rtype: str
        """
        return self._url

    @url.setter
    def url(self, url):
        r"""Sets the url of this UpdateRepositoryRemoteMirrorResponse.

        **参数解释：**  源仓地址。 **约束限制：** 不涉及。

        :param url: The url of this UpdateRepositoryRemoteMirrorResponse.
        :type url: str
        """
        self._url = url

    @property
    def mirroring_enabled(self):
        r"""Gets the mirroring_enabled of this UpdateRepositoryRemoteMirrorResponse.

        **参数解释：**  开启定时同步 **取值范围：** - true，不开启定时同步。 - false，开启定时同步。 **约束限制：** 不涉及。

        :return: The mirroring_enabled of this UpdateRepositoryRemoteMirrorResponse.
        :rtype: bool
        """
        return self._mirroring_enabled

    @mirroring_enabled.setter
    def mirroring_enabled(self, mirroring_enabled):
        r"""Sets the mirroring_enabled of this UpdateRepositoryRemoteMirrorResponse.

        **参数解释：**  开启定时同步 **取值范围：** - true，不开启定时同步。 - false，开启定时同步。 **约束限制：** 不涉及。

        :param mirroring_enabled: The mirroring_enabled of this UpdateRepositoryRemoteMirrorResponse.
        :type mirroring_enabled: bool
        """
        self._mirroring_enabled = mirroring_enabled

    @property
    def endpoint_uuid(self):
        r"""Gets the endpoint_uuid of this UpdateRepositoryRemoteMirrorResponse.

        **参数解释：**  拓展点UUID。 **约束限制：** 不涉及。

        :return: The endpoint_uuid of this UpdateRepositoryRemoteMirrorResponse.
        :rtype: str
        """
        return self._endpoint_uuid

    @endpoint_uuid.setter
    def endpoint_uuid(self, endpoint_uuid):
        r"""Sets the endpoint_uuid of this UpdateRepositoryRemoteMirrorResponse.

        **参数解释：**  拓展点UUID。 **约束限制：** 不涉及。

        :param endpoint_uuid: The endpoint_uuid of this UpdateRepositoryRemoteMirrorResponse.
        :type endpoint_uuid: str
        """
        self._endpoint_uuid = endpoint_uuid

    @property
    def sync_branch_type(self):
        r"""Gets the sync_branch_type of this UpdateRepositoryRemoteMirrorResponse.

        **参数解释：**  分支同步。 **取值范围：** - all，同步全部分支。 - default，同步默认分支。 **约束限制：** 不涉及。

        :return: The sync_branch_type of this UpdateRepositoryRemoteMirrorResponse.
        :rtype: str
        """
        return self._sync_branch_type

    @sync_branch_type.setter
    def sync_branch_type(self, sync_branch_type):
        r"""Sets the sync_branch_type of this UpdateRepositoryRemoteMirrorResponse.

        **参数解释：**  分支同步。 **取值范围：** - all，同步全部分支。 - default，同步默认分支。 **约束限制：** 不涉及。

        :param sync_branch_type: The sync_branch_type of this UpdateRepositoryRemoteMirrorResponse.
        :type sync_branch_type: str
        """
        self._sync_branch_type = sync_branch_type

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
        if not isinstance(other, UpdateRepositoryRemoteMirrorResponse):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
