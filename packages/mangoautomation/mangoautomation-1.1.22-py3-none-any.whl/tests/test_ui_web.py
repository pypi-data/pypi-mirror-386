# -*- coding: utf-8 -*-
# @Project: 芒果测试平台
# @Description: 
# @Time   : 2025-04-12 17:31
# @Author : 毛鹏
import asyncio
import unittest

from mangoautomation.models import ElementModel
from mangoautomation.uidrive import AsyncElement, BaseData, DriverObject, SyncElement
from mangotools.data_processor import DataProcessor
from mangotools.log_collector import set_log

log = set_log('D:\code\mango_automation\logs')
test_data = DataProcessor()
element_model = ElementModel(**{
    "id": 3,
    "type": 0,
    "name": "设置",
    "elements": [
        {
            "exp": 0,
            "loc": "//span[@name=\"tj_settingicon\"]",
            "sub": None,
            "is_iframe": 0
        }
    ],
    "sleep": None,
    "ope_key": "w_hover",
    "ope_value": [
        {
            "f": "locating",
            "n": None,
            "p": None,
            "d": False,
            "v": ""
        }
    ],
    "sql_execute": None,
    "custom": None,
    "condition_value": None,
    "func": None
})


class TestUi(unittest.IsolatedAsyncioTestCase):
    async def test_a(self):
        driver_object = DriverObject(log, True)
        driver_object.set_web(0, r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        base_data = BaseData(test_data, log)
        base_data.log = log
        base_data.url = 'https://www.baidu.com/'

        base_data.context, base_data.page = await driver_object.web.new_web_page()
        element = AsyncElement(base_data, 0)
        await element.open_url()
        await asyncio.sleep(5)
        await element.element_main(element_model, )
        assert element.element_result_model.elements[0].element_text == '设置'


class TestUi2(unittest.TestCase):

    def test_s(self):
        driver_object = DriverObject(log)
        driver_object.set_web(0, r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        base_data = BaseData(test_data, log)
        base_data.url = 'https://www.baidu.com/'
        base_data.context, base_data.page = driver_object.web.new_web_page()
        element = SyncElement(base_data, 0)
        element.open_url()
        element.element_main(element_model, )
        assert element.element_result_model.elements[0].element_text == '设置'
