# -*- coding: utf-8 -*-
# @Project: 芒果测试平台
# @Description: 
# @Time   : 2024-11-30 23:44
# @Author : 毛鹏
from ...tools import Meta
from ...uidrives._base_data import BaseData


class WinDeviceInput(metaclass=Meta):
    """输入设备操作"""

    def __init__(self, base_data: BaseData):
        self.base_data = base_data
