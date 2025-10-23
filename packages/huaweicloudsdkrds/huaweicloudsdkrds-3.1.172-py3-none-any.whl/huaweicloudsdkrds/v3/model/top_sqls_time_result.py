# coding: utf-8

import six

from huaweicloudsdkcore.utils.http_utils import sanitize_for_serialization


class TopSqlsTimeResult:

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    sensitive_list = []

    openapi_types = {
        'id': 'str',
        'data_type': 'str',
        'value': 'str'
    }

    attribute_map = {
        'id': 'id',
        'data_type': 'data_type',
        'value': 'value'
    }

    def __init__(self, id=None, data_type=None, value=None):
        r"""TopSqlsTimeResult

        The model defined in huaweicloud sdk

        :param id: 对查询计算的二进制哈希值，用于标识具有类似逻辑的查询。
        :type id: str
        :param data_type: 数据类型。取值范围： AvgWorkerTime 平均CPU开销 AvgDuration 平均执行耗时 TotalWorkerTime 总CPU开销 TotalDuration 总执行耗时
        :type data_type: str
        :param value: 耗时时间，单位ms。
        :type value: str
        """
        
        

        self._id = None
        self._data_type = None
        self._value = None
        self.discriminator = None

        if id is not None:
            self.id = id
        if data_type is not None:
            self.data_type = data_type
        if value is not None:
            self.value = value

    @property
    def id(self):
        r"""Gets the id of this TopSqlsTimeResult.

        对查询计算的二进制哈希值，用于标识具有类似逻辑的查询。

        :return: The id of this TopSqlsTimeResult.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        r"""Sets the id of this TopSqlsTimeResult.

        对查询计算的二进制哈希值，用于标识具有类似逻辑的查询。

        :param id: The id of this TopSqlsTimeResult.
        :type id: str
        """
        self._id = id

    @property
    def data_type(self):
        r"""Gets the data_type of this TopSqlsTimeResult.

        数据类型。取值范围： AvgWorkerTime 平均CPU开销 AvgDuration 平均执行耗时 TotalWorkerTime 总CPU开销 TotalDuration 总执行耗时

        :return: The data_type of this TopSqlsTimeResult.
        :rtype: str
        """
        return self._data_type

    @data_type.setter
    def data_type(self, data_type):
        r"""Sets the data_type of this TopSqlsTimeResult.

        数据类型。取值范围： AvgWorkerTime 平均CPU开销 AvgDuration 平均执行耗时 TotalWorkerTime 总CPU开销 TotalDuration 总执行耗时

        :param data_type: The data_type of this TopSqlsTimeResult.
        :type data_type: str
        """
        self._data_type = data_type

    @property
    def value(self):
        r"""Gets the value of this TopSqlsTimeResult.

        耗时时间，单位ms。

        :return: The value of this TopSqlsTimeResult.
        :rtype: str
        """
        return self._value

    @value.setter
    def value(self, value):
        r"""Sets the value of this TopSqlsTimeResult.

        耗时时间，单位ms。

        :param value: The value of this TopSqlsTimeResult.
        :type value: str
        """
        self._value = value

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
        if not isinstance(other, TopSqlsTimeResult):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
