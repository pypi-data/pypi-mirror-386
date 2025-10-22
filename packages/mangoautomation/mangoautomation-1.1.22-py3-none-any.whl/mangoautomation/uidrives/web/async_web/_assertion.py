# -*- coding: utf-8 -*-
# @Project: 芒果测试平台
# @Description: # @Time   : 2023-04-26 22:25
# @Author : 毛鹏

from playwright.async_api import Locator, expect as exp

from mangotools.decorator import async_method_callback
from mangotools.models import MethodModel
from ....exceptions import MangoAutomationError
from ....exceptions.error_msg import ERROR_MSG_0021
from ....tools import Meta
from ....uidrives._base_data import BaseData


class AsyncWebAssertion(metaclass=Meta):
    """元素断言"""

    def __init__(self, base_data: BaseData):
        self.base_data = base_data

    @async_method_callback('ass_web', '元素断言', 0, [
        MethodModel(f='actual'),
        MethodModel(n='预期值', f='expect', p='请输入元素个数', d=True)])
    async def w_to_have_count(self, actual: Locator, expect: str):
        """元素是几个"""
        try:
            await exp(actual).to_have_count(int(expect))
        except AssertionError as e:
            raise AssertionError(f'实际={await actual.count()}, 预期={expect}') from e
        return f'实际={await actual.count()}, 预期={expect}'

    @async_method_callback('ass_web', '元素断言', 1, [MethodModel(f='actual')])
    async def w_all_not_to_be_empty(self, actual: Locator):
        """元素存在"""
        count = await actual.count()
        if count == 0:
            assert False, f'实际={count}, 预期>0'
        return f'实际={count}, 预期>0'

    @async_method_callback('ass_web', '元素断言', 1, [
        MethodModel(f='actual'),
        MethodModel(n='预期值', f='expect', p='请输入元素存输入1，不存输入0', d=True)])
    async def w_to_element_count(self, actual: Locator, expect: int):
        """元素是否存在"""
        if int(expect) == 0:
            assert actual is None, f'实际={actual}, 预期={expect}'
            return f'实际={actual}, 预期={expect}'

        else:
            if actual:
                try:
                    await exp(actual).to_have_count(int(expect))
                    return f'实际={actual.count()}, 预期={expect}'
                except AssertionError as e:
                    raise AssertionError(f'实际={actual.count()}, 预期={expect}') from e
            else:
                raise MangoAutomationError(*ERROR_MSG_0021)

    @async_method_callback('ass_web', '元素断言', 2, [
        MethodModel(f='actual'),
        MethodModel(n='预期值', f='expect', p='请输入不包含的文本', d=True)])
    async def w_not_to_contain_text(self, actual: Locator, expect: str):
        """元素不包含文本"""
        try:
            await exp(actual).not_to_contain_text(expect)
        except AssertionError as e:
            raise AssertionError(f'实际={actual}, 预期={expect}') from e
        return f'实际={actual}, 预期={expect}'

    @async_method_callback('ass_web', '元素断言', 3, [MethodModel(f='actual')])
    async def w_not_to_be_empty(self, actual: Locator):
        """元素不为空"""
        try:
            await exp(actual).not_to_be_empty()
        except AssertionError as e:
            raise AssertionError(f'实际={actual}, 预期=不为空') from e
        return f'实际={actual}, 预期=不为空'

    @async_method_callback('ass_web', '元素断言', 4, [MethodModel(f='actual')])
    async def w_not_to_be_enabled(self, actual: Locator):
        """元素不启用"""
        try:
            await exp(actual).not_to_be_enabled()
        except AssertionError as e:
            raise AssertionError(f'实际={actual}, 预期=不启用') from e
        return f'实际={actual}, 预期=不启用'

    @async_method_callback('ass_web', '元素断言', 5, [MethodModel(f='actual')])
    async def w_not_to_be_focused(self, actual: Locator):
        """元素不聚焦"""
        try:
            await exp(actual).not_to_be_focused()
        except AssertionError as e:
            raise AssertionError(f'实际={actual}, 预期=不聚焦') from e
        return f'实际={actual}, 预期=不聚焦'

    @async_method_callback('ass_web', '元素断言', 6, [MethodModel(f='actual')])
    async def w_not_to_be_hidden(self, actual: Locator):
        """元素不可隐藏"""
        try:
            await exp(actual).not_to_be_hidden()
        except AssertionError as e:
            raise AssertionError(f'实际={actual}, 预期=不可隐藏') from e
        return f'实际={actual}, 预期=不可隐藏'

    @async_method_callback('ass_web', '元素断言', 7, [MethodModel(f='actual')])
    async def w_not_to_be_in_viewport(self, actual: Locator):
        """元素不在视窗中"""
        try:
            await exp(actual).not_to_be_in_viewport()
        except AssertionError as e:
            raise AssertionError(f'实际={actual}, 预期=不在视窗中') from e
        return f'实际={actual}, 预期=不在视窗中'

    @async_method_callback('ass_web', '元素断言', 8, [MethodModel(f='actual')])
    async def w_not_to_be_visible(self, actual: Locator):
        """元素不可见"""
        try:
            await exp(actual).not_to_be_visible()
        except AssertionError as e:
            raise AssertionError(f'实际={actual}, 预期=不可见') from e
        return f'实际={actual}, 预期=不可见'

    @async_method_callback('ass_web', '元素断言', 9, [
        MethodModel(f='actual'),
        MethodModel(n='预期值', f='expect', p='请输入样式', d=True)])
    async def w_not_to_have_class(self, actual: Locator, expect: str):
        """元素没有阶级"""
        try:
            await exp(actual).not_to_have_class(expect)
        except AssertionError as e:
            raise AssertionError(f'实际={actual}, 预期=没有阶级') from e
        return f'实际={actual}, 预期=没有阶级'

    @async_method_callback('ass_web', '元素断言', 10, [MethodModel(f='actual')])
    async def w_to_be_checked(self, actual: Locator):
        """复选框已选中"""
        try:
            await exp(actual).to_be_checked()
        except AssertionError as e:
            raise AssertionError(f'实际={actual}, 预期=复选框已选中') from e
        return f'实际={actual}, 预期=复选框已选中'

    @async_method_callback('ass_web', '元素断言', 11, [MethodModel(f='actual')])
    async def w_to_be_disabled(self, actual: Locator):
        """元素已禁用"""
        try:
            await exp(actual).to_be_disabled()
        except AssertionError as e:
            raise AssertionError(f'实际={actual}, 预期=已禁用') from e
        return f'实际={actual}, 预期=已禁用'

    @async_method_callback('ass_web', '元素断言', 12, [MethodModel(f='actual')])
    async def w_not_to_be_editable(self, actual: Locator):
        """元素已启用"""
        try:
            await exp(actual).to_be_editable()
        except AssertionError as e:
            raise AssertionError(f'实际={actual}, 预期=已启用') from e
        return f'实际={actual}, 预期=已启用'

    @async_method_callback('ass_web', '元素断言', 13, [MethodModel(f='actual')])
    async def w_to_be_empty(self, actual: Locator | list | None):
        """元素为空"""
        if actual is None:
            assert True, f'实际={actual}, 预期=为空'
            return f'实际={actual}, 预期=为空'
        else:
            try:
                await exp(actual).to_be_empty()
                return f'实际={actual}, 预期=为空'
            except AssertionError as e:
                raise AssertionError(f'实际={actual}, 预期=为空') from e

    @async_method_callback('ass_web', '元素断言', 14, [MethodModel(f='actual')])
    async def w_to_be_visible(self, actual: Locator):
        """元素可见"""
        try:
            await exp(actual).to_be_visible()
        except AssertionError as e:
            raise AssertionError(f'实际={actual}, 预期=可见') from e
        return f'实际={actual}, 预期=可见'
    # @staticmethod
    # async def w_not_to_have_actuals(actual: Locator, actuals: list):
    #     """选择已选择选项"""
    #     await exp(actual).to_have_actuals(actuals)

    # @staticmethod
    # def w_not_to_have_attribute(locating: Locator, name: str, actual: str):
    #     """元素不具有属性"""
    #     exp(locating).not_to_have_attribute(name, actual)
    # @staticmethod

    # @staticmethod
    # def w_not_to_have_css(locating: Locator, name: str, actual: str):
    #     """元素不使用CSS"""
    #     exp(locating).not_to_have_css(name, actual)

    # @staticmethod
    # def w_not_to_have_id(locating: Locator, _id: str):
    #     """元素没有ID"""
    #     exp(locating).not_to_have_id(_id)
    #
    # @staticmethod
    # def w_not_to_have_js_property(locating: Locator, name: str, actual):
    #     """元素不具有js属性"""
    #     exp(locating).not_to_have_js_property(name, actual)
    #
    # @staticmethod
    # def w_not_to_have_text(locating: Locator, expected: str):
    #     """元素没有文本"""
    #     exp(locating).not_to_have_text(expected)

    # @staticmethod
    # def w_not_to_have_actual(locating: Locator, actual: str):
    #     """元素无价值"""
    #     exp(locating).not_to_have_actual(actual)

    #
    # def w_to_be_attached(self, hidden_text: str):
    #     """待连接"""
    #     exp(self.page.get_by_text(hidden_text)).to_be_attached()

    #
    # def w_to_be_editable(self, hidden_text: str):
    #     """可编辑"""
    #     locator = self.page.get_by_role("textbox")
    #     exp(locator).to_be_editable()

    # def w_to_be_enabled(self, hidden_text: str):
    #     """为空"""
    #     locator = self.page.locator("button.submit")
    #     exp(locator).to_be_enabled()

    # def w_to_be_focused(self, hidden_text: str):
    #     """聚焦"""
    #     locator = self.page.get_by_role("textbox")
    #     exp(locator).to_be_focused()
    #
    # def w_to_be_hidden(self, hidden_text: str):
    #     """隐藏"""
    #     locator = self.page.locator('.my-element')
    #     exp(locator).to_be_hidden()
    #
    # def w_to_be_in_viewport(self, hidden_text: str):
    #     """待在视口中"""
    #     locator = self.page.get_by_role("button")
    #     # Make sure at least some part of element intersects viewport.
    #     exp(locator).to_be_in_viewport()
    #     # Make sure element is fully outside of viewport.
    #     exp(locator).not_to_be_in_viewport()
    #     # Make sure that at least half of the element intersects viewport.
    #     exp(locator).to_be_in_viewport(ratio=0.5)
    #

    # def w_to_contain_text(self, hidden_text: str):
    #     """包含文本"""
    #     locator = self.page.locator('.title')
    #     exp(locator).to_contain_text("substring")
    #     exp(locator).to_contain_text(re.compile(r"\d messages"))
    #
    # def w_to_have_attribute(self, hidden_text: str):
    #     """具有属性"""
    #     locator = self.page.locator("input")
    #     exp(locator).to_have_attribute("type", "text")
    #
    # def w_to_have_class(self, hidden_text: str):
    #     """到保存类别"""
    #     locator = self.page.locator("#component")
    #     exp(locator).to_have_class(re.compile(r"selected"))
    #     exp(locator).to_have_class("selected row")
    #
    # def w_to_have_count(self, hidden_text: str):
    #     """有计数"""
    #     locator = self.page.locator("list > .component")
    #     exp(locator).to_have_count(3)
    #
    # def w_to_have_css(self, hidden_text: str):
    #     """使用CSS"""
    #     locator = self.page.get_by_role("button")
    #     exp(locator).to_have_css("display", "flex")
    #
    # def w_to_have_id(self, hidden_text: str):
    #     """到id"""
    #     locator = self.page.get_by_role("textbox")
    #     exp(locator).to_have_id("lastname")
    #
    # def w_to_have_js_property(self, hidden_text: str):
    #     """拥有js属性"""
    #     locator = self.page.locator(".component")
    #     exp(locator).to_have_js_property("loaded", True)
    #
    # def w_to_have_text(self, hidden_text: str):
    #     """有文本"""
    #     locator = self.page.locator(".title")
    #     exp(locator).to_have_text(re.compile(r"Welcome, Test User"))
    #     exp(locator).to_have_text(re.compile(r"Welcome, .*"))
    #
    # def w_to_have_actual(self, hidden_text: str):
    #     """有价值"""
    #     locator = self.page.locator("input[type=number]")
    #     exp(locator).to_have_actual(re.compile(r"[0-9]"))
