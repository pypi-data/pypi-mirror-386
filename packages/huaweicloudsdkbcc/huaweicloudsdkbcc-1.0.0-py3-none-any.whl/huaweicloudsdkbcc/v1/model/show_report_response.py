# coding: utf-8

import six

from huaweicloudsdkcore.sdk_response import SdkResponse
from huaweicloudsdkcore.utils.http_utils import sanitize_for_serialization


class ShowReportResponse(SdkResponse):

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    sensitive_list = []

    openapi_types = {
        'report_download_url': 'str',
        'report_info': 'ReportEntity'
    }

    attribute_map = {
        'report_download_url': 'report_download_url',
        'report_info': 'report_info'
    }

    def __init__(self, report_download_url=None, report_info=None):
        r"""ShowReportResponse

        The model defined in huaweicloud sdk

        :param report_download_url: 报告下载链接
        :type report_download_url: str
        :param report_info: 
        :type report_info: :class:`huaweicloudsdkbcc.v1.ReportEntity`
        """
        
        super(ShowReportResponse, self).__init__()

        self._report_download_url = None
        self._report_info = None
        self.discriminator = None

        if report_download_url is not None:
            self.report_download_url = report_download_url
        if report_info is not None:
            self.report_info = report_info

    @property
    def report_download_url(self):
        r"""Gets the report_download_url of this ShowReportResponse.

        报告下载链接

        :return: The report_download_url of this ShowReportResponse.
        :rtype: str
        """
        return self._report_download_url

    @report_download_url.setter
    def report_download_url(self, report_download_url):
        r"""Sets the report_download_url of this ShowReportResponse.

        报告下载链接

        :param report_download_url: The report_download_url of this ShowReportResponse.
        :type report_download_url: str
        """
        self._report_download_url = report_download_url

    @property
    def report_info(self):
        r"""Gets the report_info of this ShowReportResponse.

        :return: The report_info of this ShowReportResponse.
        :rtype: :class:`huaweicloudsdkbcc.v1.ReportEntity`
        """
        return self._report_info

    @report_info.setter
    def report_info(self, report_info):
        r"""Sets the report_info of this ShowReportResponse.

        :param report_info: The report_info of this ShowReportResponse.
        :type report_info: :class:`huaweicloudsdkbcc.v1.ReportEntity`
        """
        self._report_info = report_info

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
        if not isinstance(other, ShowReportResponse):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
