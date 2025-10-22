# -*- coding: utf-8 -*-
# @Project: 芒果测试平台
# @Description: # @Time   : 2023-04-29 12:11
# @Author : 毛鹏

from mangotools.decorator import async_method_callback
from mangotools.models import MethodModel
from ....tools import Meta
from ....uidrives._base_data import BaseData


class AsyncWebDeviceInput(metaclass=Meta):
    """输入设备"""

    def __init__(self, base_data: BaseData):
        self.base_data = base_data

    @async_method_callback('web', '输入设备', 0, [
        MethodModel(n='按键值', f='keyboard', p='请输入键盘名称，首字母大写', d=True)])
    async def w_keys(self, keyboard: str):
        """模拟按下指定的键"""
        await self.base_data.page.keyboard.press(str(keyboard))

    @async_method_callback('web', '输入设备', 1, [
        MethodModel(n='滚动像素', f='y', p='请输入向上滚动像素', d=True)])
    async def w_wheel(self, y):
        """鼠标上下滚动像素，负数代表向上"""
        await self.base_data.page.mouse.wheel(0, int(y))

    @async_method_callback('web', '输入设备', 2, [
        MethodModel(n='x坐标', f='x', p='请输入点击的x轴', d=True),
        MethodModel(n='y坐标', f='y', p='请输入点击的y轴', d=True)])
    async def w_mouse_click(self, x: float, y: float):
        """鼠标点击坐标"""
        await self.base_data.page.mouse.click(float(x), float(y))

    @async_method_callback('web', '输入设备', 3)
    async def w_mouse_center(self):
        """鼠标移动到中间"""

        viewport_size = await self.base_data.page.evaluate('''() => {
            return {
                width: window.innerWidth,
                height: window.innerHeight
            }
        }''')
        center_x = viewport_size['width'] / 2
        center_y = viewport_size['height'] / 2
        await self.base_data.page.mouse.move(center_x, center_y)

    @async_method_callback('web', '输入设备', 4)
    async def w_mouse_center(self):
        """鼠标移动到中间并点击"""

        viewport_size = await self.base_data.page.evaluate('''() => {
            return {
                width: window.innerWidth,
                height: window.innerHeight
            }
        }''')
        center_x = viewport_size['width'] / 2
        center_y = viewport_size['height'] / 2
        await self.base_data.page.mouse.click(center_x, center_y)

    @async_method_callback('web', '输入设备', 5, [
        MethodModel(n='输入文本', f='text', p='请输入键盘输入的内容', d=True)])
    async def w_keyboard_type_text(self, text: str):
        """模拟人工输入文字"""
        await self.base_data.page.keyboard.type(str(text))

    @async_method_callback('web', '输入设备', 6, [
        MethodModel(n='输入文本', f='text', p='请输入键盘输入的内容', d=True)])
    async def w_keyboard_insert_text(self, text: str):
        """直接输入文字"""
        await self.base_data.page.keyboard.insert_text(str(text))

    @async_method_callback('web', '输入设备', 7, [
        MethodModel(n='删除个数', f='count', p='请输入要删除字符串的个数', d=True)])
    async def w_keyboard_delete_text(self, count: int):
        """删除光标左侧的字符"""
        for _ in range(0, int(count) + 1):
            await self.base_data.page.keyboard.press("Backspace")
