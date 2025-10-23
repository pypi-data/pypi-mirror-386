# coding: utf-8

import six

from huaweicloudsdkcore.utils.http_utils import sanitize_for_serialization


class RestartConfiguration:

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    sensitive_list = []

    openapi_types = {
        'restart_server': 'bool',
        'forcible': 'bool',
        'delay': 'bool',
        'restart_policy': 'RestartPolicy'
    }

    attribute_map = {
        'restart_server': 'restart_server',
        'forcible': 'forcible',
        'delay': 'delay',
        'restart_policy': 'restart_policy'
    }

    def __init__(self, restart_server=None, forcible=None, delay=None, restart_policy=None):
        r"""RestartConfiguration

        The model defined in huaweicloud sdk

        :param restart_server: 是否重启虚拟机。
        :type restart_server: bool
        :param forcible: 是否强制重启, 强制重启会导致数据库服务中未提交的事务强制中断。
        :type forcible: bool
        :param delay: 是否在可维护时间段内重启。
        :type delay: bool
        :param restart_policy: 
        :type restart_policy: :class:`huaweicloudsdkrds.v3.RestartPolicy`
        """
        
        

        self._restart_server = None
        self._forcible = None
        self._delay = None
        self._restart_policy = None
        self.discriminator = None

        if restart_server is not None:
            self.restart_server = restart_server
        if forcible is not None:
            self.forcible = forcible
        if delay is not None:
            self.delay = delay
        if restart_policy is not None:
            self.restart_policy = restart_policy

    @property
    def restart_server(self):
        r"""Gets the restart_server of this RestartConfiguration.

        是否重启虚拟机。

        :return: The restart_server of this RestartConfiguration.
        :rtype: bool
        """
        return self._restart_server

    @restart_server.setter
    def restart_server(self, restart_server):
        r"""Sets the restart_server of this RestartConfiguration.

        是否重启虚拟机。

        :param restart_server: The restart_server of this RestartConfiguration.
        :type restart_server: bool
        """
        self._restart_server = restart_server

    @property
    def forcible(self):
        r"""Gets the forcible of this RestartConfiguration.

        是否强制重启, 强制重启会导致数据库服务中未提交的事务强制中断。

        :return: The forcible of this RestartConfiguration.
        :rtype: bool
        """
        return self._forcible

    @forcible.setter
    def forcible(self, forcible):
        r"""Sets the forcible of this RestartConfiguration.

        是否强制重启, 强制重启会导致数据库服务中未提交的事务强制中断。

        :param forcible: The forcible of this RestartConfiguration.
        :type forcible: bool
        """
        self._forcible = forcible

    @property
    def delay(self):
        r"""Gets the delay of this RestartConfiguration.

        是否在可维护时间段内重启。

        :return: The delay of this RestartConfiguration.
        :rtype: bool
        """
        return self._delay

    @delay.setter
    def delay(self, delay):
        r"""Sets the delay of this RestartConfiguration.

        是否在可维护时间段内重启。

        :param delay: The delay of this RestartConfiguration.
        :type delay: bool
        """
        self._delay = delay

    @property
    def restart_policy(self):
        r"""Gets the restart_policy of this RestartConfiguration.

        :return: The restart_policy of this RestartConfiguration.
        :rtype: :class:`huaweicloudsdkrds.v3.RestartPolicy`
        """
        return self._restart_policy

    @restart_policy.setter
    def restart_policy(self, restart_policy):
        r"""Sets the restart_policy of this RestartConfiguration.

        :param restart_policy: The restart_policy of this RestartConfiguration.
        :type restart_policy: :class:`huaweicloudsdkrds.v3.RestartPolicy`
        """
        self._restart_policy = restart_policy

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
        if not isinstance(other, RestartConfiguration):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
