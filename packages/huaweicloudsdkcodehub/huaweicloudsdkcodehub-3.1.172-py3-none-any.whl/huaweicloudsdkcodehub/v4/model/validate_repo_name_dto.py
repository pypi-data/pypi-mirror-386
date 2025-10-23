# coding: utf-8

import six

from huaweicloudsdkcore.utils.http_utils import sanitize_for_serialization


class ValidateRepoNameDto:

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    sensitive_list = []

    openapi_types = {
        'name': 'str',
        'project_id': 'str',
        'group_id': 'int'
    }

    attribute_map = {
        'name': 'name',
        'project_id': 'project_id',
        'group_id': 'group_id'
    }

    def __init__(self, name=None, project_id=None, group_id=None):
        r"""ValidateRepoNameDto

        The model defined in huaweicloud sdk

        :param name: **参数解释：** 仓库名。 **约束限制：** - 必填。 - 大小写字母、数字、下划线开头，可包含大小写字母、数字、中划线、下划线、英文句点，但不能以.git、.atom或.结尾 - 代码总路径长度（代码组名称和仓库名称总长度）不超过256字符 **取值范围：** 不涉及。 **默认取值：** 不涉及。
        :type name: str
        :param project_id: **参数解释：** 项目ID。 **约束限制：** 必填。 **取值范围：** 不涉及。 **默认取值：** 不涉及。
        :type project_id: str
        :param group_id: **参数解释：** 代码组ID，若需要检查的仓库名称在项目根目录下可不传此参数。 **约束限制：** 不涉及。 **取值范围：** 不涉及。 **默认取值：** 1-2147483647
        :type group_id: int
        """
        
        

        self._name = None
        self._project_id = None
        self._group_id = None
        self.discriminator = None

        if name is not None:
            self.name = name
        if project_id is not None:
            self.project_id = project_id
        if group_id is not None:
            self.group_id = group_id

    @property
    def name(self):
        r"""Gets the name of this ValidateRepoNameDto.

        **参数解释：** 仓库名。 **约束限制：** - 必填。 - 大小写字母、数字、下划线开头，可包含大小写字母、数字、中划线、下划线、英文句点，但不能以.git、.atom或.结尾 - 代码总路径长度（代码组名称和仓库名称总长度）不超过256字符 **取值范围：** 不涉及。 **默认取值：** 不涉及。

        :return: The name of this ValidateRepoNameDto.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        r"""Sets the name of this ValidateRepoNameDto.

        **参数解释：** 仓库名。 **约束限制：** - 必填。 - 大小写字母、数字、下划线开头，可包含大小写字母、数字、中划线、下划线、英文句点，但不能以.git、.atom或.结尾 - 代码总路径长度（代码组名称和仓库名称总长度）不超过256字符 **取值范围：** 不涉及。 **默认取值：** 不涉及。

        :param name: The name of this ValidateRepoNameDto.
        :type name: str
        """
        self._name = name

    @property
    def project_id(self):
        r"""Gets the project_id of this ValidateRepoNameDto.

        **参数解释：** 项目ID。 **约束限制：** 必填。 **取值范围：** 不涉及。 **默认取值：** 不涉及。

        :return: The project_id of this ValidateRepoNameDto.
        :rtype: str
        """
        return self._project_id

    @project_id.setter
    def project_id(self, project_id):
        r"""Sets the project_id of this ValidateRepoNameDto.

        **参数解释：** 项目ID。 **约束限制：** 必填。 **取值范围：** 不涉及。 **默认取值：** 不涉及。

        :param project_id: The project_id of this ValidateRepoNameDto.
        :type project_id: str
        """
        self._project_id = project_id

    @property
    def group_id(self):
        r"""Gets the group_id of this ValidateRepoNameDto.

        **参数解释：** 代码组ID，若需要检查的仓库名称在项目根目录下可不传此参数。 **约束限制：** 不涉及。 **取值范围：** 不涉及。 **默认取值：** 1-2147483647

        :return: The group_id of this ValidateRepoNameDto.
        :rtype: int
        """
        return self._group_id

    @group_id.setter
    def group_id(self, group_id):
        r"""Sets the group_id of this ValidateRepoNameDto.

        **参数解释：** 代码组ID，若需要检查的仓库名称在项目根目录下可不传此参数。 **约束限制：** 不涉及。 **取值范围：** 不涉及。 **默认取值：** 1-2147483647

        :param group_id: The group_id of this ValidateRepoNameDto.
        :type group_id: int
        """
        self._group_id = group_id

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
        if not isinstance(other, ValidateRepoNameDto):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
