# """BasePage"""
# import time
#
# from dui_automation.da.common.by import By
# from dui_automation.da.common.selector import Selector
# from dui_automation.da.core.exception import ControlNotFoundError
# from dui_automation.da.core.exception import WindowNotFoundError
#
# # from dui_auto_pc_test.utils import log
# from dui_automation.da.core.exception import WindowNotFoundError
# from dui_automation.da.common.keycode import Keycode
# # import pygetwindow as gw
# from dui_automation.da.mixins.uia.window import DAUIa
# from dui_automation.da.mixins.uia.window import window_control
# import logging
# logger = logging
#
# logger.basicConfig(level=logging.INFO)
#
#
# class BasePage(object):
#     _WINDOW_CLASS = None
#     _WINDOW_NAME = None
#
#
#     @property
#     def window(self):
#         window = window_control(self._WINDOW_CLASS,self._WINDOW_NAME)
#         return window
#
#     def find_control(self, selector):
#         """
#         通用的元素定位方法，支持多种定位方式
#         :param selector:
#         :return:
#         """
#         control = self.window.find_ui_control(selector)
#         return control
#
#     def wait_control_and_click(self, selector):
#         """
#         等待元素可见并点击
#         :param selector:
#         :return:
#         """
#         logger.info(f"==>等待元素可见并点击：{selector.value}")
#         control = self.find_control(selector)
#         self.wait_for_control_visible(control)
#         # 元素可见后刷新元素
#         control.refresh()
#         control.click()
#         logger.info(f"<==等待元素可见并点击：{selector.value}点击成功")
#
#     def wait_control(self, selector):
#         """
#         等待元素可见并返回元素
#         :param selector:
#         :return:
#         """
#         logger.info(f"==>等待元素可见：{selector.value}")
#         control = self.find_control(selector)
#         self.wait_for_control_visible(control)
#         logger.info(f"<==等待元素可见：{selector.value}返回元素成功")
#         return control
#
#     def find_control_and_click(self, selector):
#         """
#         查找元素并点击
#         :param selector:
#         :return:
#         """
#         logger.info(f"==>点击元素：{selector.value}")
#         self.window.find_control_and_click(selector,simulateMove=True)
#         logger.info(f"<==点击元素：{selector.value}成功")
#
#     def find_control_and_set_text(self, selector, text):
#         """
#         查找元素并输入文本
#         :param text:
#         :param selector:
#         :return:
#         """
#         logger.info(f"==>找到元素{selector.value}，输入文本：{text}")
#         control = self.find_control(selector)
#         self.wait_for_control_visible(control)
#         control.set_text(text)
#         logger.info(f"<==输入文本：{text}成功")
#
#     def is_control_visible(self, selector):
#         """
#         判断元素是否可见
#         :param selector:
#         :return:
#         """
#         logger.info(f"==>判断元素是否可见：{selector.value}")
#         try:
#             control = self.find_control(selector)
#         except ControlNotFoundError:
#             logger.info(f"<==元素不存在：{selector.value}")
#             return False
#         if control.visible == 1:
#             logger.info(f"<==元素可见：{selector.value}")
#             return True
#         else:
#             logger.info(f"<==元素不可见：{selector}")
#             return False
#
#     def set_control_visible(self, selector, condition=True):
#         """
#         设置元素可见或不可见
#         :param selector:
#         :param condition:1:设置元素可见，0：设置元素不可见
#         :return:
#         """
#
#         control = self.find_control(selector)
#         if condition:
#             logger.info(f"==>设置元素可见：{control}")
#             control.set_visible(condition)
#             logger.info(f"<==设置元素可见成功：{control}")
#         else:
#             logger.info(f"==>设置元素不可见：{control}")
#             control.set_visible(condition)
#             logger.info(f"<==设置元素不可见成功：{control}")
#
#     def wait_for_visible(self, selector, timeout=10):
#         """
#         等待元素可见
#         :param selector:
#         :param timeout:
#         :return:
#         """
#         logger.info(f"==>等待元素可见：{selector.value}")
#         if self.window.wait_for_visible(selector, timeout=timeout):
#             logger.info(f"<==元素可见：{selector.value}")
#             return True
#         logger.info(f"<==元素不可见：{selector.value}，已等待{timeout}s")
#         return False
#
#     def wait_for_invisible(self, selector, timeout=10) -> bool:
#         """
#         等待元素不见
#         :param selector:
#         :param timeout:
#         :return:
#         """
#         logger.info(f"==>等待元素不可见：{selector.value}")
#         if self.window.wait_for_invisible(selector, timeout=timeout):
#             logger.info(f"<==元素不可见：{selector.value}")
#             return True
#         else:
#             logger.info(f"<==元素可见：{selector.value}，继续等待1s")
#             return False
#
#     @staticmethod
#     def wait_for_control_visible(
#         control, timeout: int = 10, interval: float = 0.5
#     ) -> bool:
#         """
#         等待control可见
#         :param interval: 时间间隔
#         :param control: control对象
#         :param timeout: 超时时间,默认10s
#         :return: True:可见，False:不可见
#         """
#         logger.info(f"==>等待元素可见：{control.name}")
#         start_time = time.time()
#         while time.time() - start_time < timeout:
#             control.refresh()
#             if control.visible & (control.x != 0 or control.y != 0):
#                 logger.info(f"<==元素可见：{control.name}")
#                 return True
#             time.sleep(interval)
#         logger.info(f"<==元素不可见：{control.name}，已等待{timeout}s")
#         return False
#
#     def find_parent_control(self, selector):
#         """
#         查找selector的父元素
#         :param selector:
#         :return:
#         """
#         control = self.find_control(selector)
#         return control.parent
#
#     def find_parent_control_click(self, selector):
#         """
#         查找selector的父元素， 并点击
#         :param selector:
#         :return:
#         """
#         logger.info(f"==>点击元素：{selector}的父元素")
#         control = self.find_parent_control(selector)
#         control.click()
#         logger.info(f"<==点击元素：{selector}成功")
#
#     def find_control_and_get_text(self, selector):
#         """
#         查找元素并返回元素的text
#         :return:
#         """
#         logger.info(f"==>获取元素：{selector.value}的文本")
#         control = self.find_control(selector)
#         logger.info(f"==>文本信息为：{control.Name}")
#         return control.Name
#
#     def is_control_selected(self, selector):
#         """
#         查找元素并返回元素的text
#         :return:
#         """
#         logger.info(f"==>判断元素是否被选中：{selector}")
#         control = self.find_control(selector)
#         if control.selected == 1:
#             logger.info(f"==>元素处于被选中状态：{selector}")
#             return True
#         else:
#             logger.info(f"==>元素没有被选中状态：{selector}")
#             return False
#
#     def find_controls(self, selector):
#         """
#         查找满足条件的多个元素
#         :param selector:
#         :return:
#         """
#         controls = self.window.find_controls(selector)
#         return controls
#
#     def click_by_xy(self, control_x, control_y):
#         """
#         点击坐标
#         :param control_x:
#         :param control_y:
#         :return:
#         """
#         logger.info(f"==>点击坐标：{control_x}, {control_y}")
#         self.window.click_xy(control_x, control_y)
#         logger.info(f"<==点击坐标：{control_x}, {control_y}成功")
#
#     def find_subcontrols(self, parent_control, by, value):
#         """
#         查找子元素
#         :param parent_control:
#         :param by:
#         :param value:
#         :return:
#         """
#         controls = self.window.find_subcontrols(parent_control, by, value)
#         return controls
#
#     def find_child_control_and_get_text(self, selector, num):
#         """查找selector索引为num的的子元素，返回子元素的text
#         :param selector:
#         :param num: int 子元素索引
#         :return:
#         """
#         control = self.find_control(selector)
#         self.wait_for_control_visible(control)
#         logger.info(f"==>获取元素：{selector}索引为{num}的元素的文本")
#         child_control = control.child_controls[num]
#         self.wait_for_control_visible(child_control)
#         logger.info(f"<==文本信息为：{child_control.text}")
#         return child_control.text
#
#     def click_child_control(self, selector, num):
#         """查找selector索引为num的子元素，， 并点击
#         :param selector:
#         :param num: int 子元素索引
#         :return:
#         """
#         control = self.find_control(selector)
#         self.wait_for_control_visible(control)
#         logger.info(f"==>点击元素：{selector}索引为{num}的子元素")
#         child_control = control.child_controls[num]
#         self.wait_for_control_visible(child_control)
#         child_control.click()
#         logger.info(f"<==点击元素：{selector}索引为{num}的子元素成功")
#
#     def find_child_control_num(self, selector, num):
#         """查找selector索引为num的子元素
#         :param selector:
#         :param num: int 子元素索引
#         :return:
#         """
#         control = self.find_control(selector)
#         return control.child_controls[num]
#
#     def find_control_by_id(self, control_id):
#         """
#         根据id查找元素
#         :param control_id:
#         :return:
#         """
#         control = self.window.find_control_by_id(control_id)
#         return control
#
#     def press_key(self, keycode):
#         """
#         按键
#         :param keycode:
#         :return:
#         """
#         logger.info(f"==>按键：{keycode}")
#         self.window.press_key(keycode)
#         logger.info(f"<==按键：{keycode}成功")
#
#     def slide_mouse_wheel(self, slide, x, y):
#         """
#         滑动鼠标滚轮
#         :param slide:
#         :param x:
#         :param y:
#         :return:
#         """
#         self.window.mouse_wheel(slide, x, y)
#
#     def is_visible(self, selector):
#         """
#         判断窗口是否可见
#         :return:
#         """
#         return self.window.is_visible(selector)
#
#     def is_select(self, selector):
#         """
#         判断元素是否被选中
#         :return:
#         """
#         control = self.window.find_control(selector)
#         return control.selected
#
#     def wait_for_select(
#         self, selector, timeout: int = 10, interval: float = 0.5
#     ) -> bool:
#         """
#         等待元素被选中
#         :param selector:
#         :param timeout:
#         :param interval:
#         :return:
#         """
#         start_time = time.time()
#         logger.info(f"==>等待元素被选中：{selector.value}")
#         while time.time() - start_time < timeout:
#             try:
#                 if self.is_select(selector):
#                     logger.info(f"<==元素被选中：{selector.value}")
#                     return True
#             except WindowNotFoundError:
#                 time.sleep(interval)
#         logger.info(f"<==元素未被选中：{selector.value}，已等待{timeout}s")
#         return False
#
#     def wait_for_not_selected(
#         self, selector, timeout: int = 10, interval: float = 0.5
#     ) -> bool:
#         """
#         等待元素未被选中
#         :param selector:
#         :param timeout:
#         :param interval:
#         :return:
#         """
#         start_time = time.time()
#         logger.info(f"==>等待元素不被选中：{selector.value}")
#         while time.time() - start_time < timeout:
#             try:
#                 if self.is_select(selector) is False:
#                     logger.info(f"<==元素未被选中：{selector.value}")
#                     return True
#             except WindowNotFoundError:
#                 time.sleep(interval)
#         logger.info(f"<==等待失败，元素还是选中：{selector.value}，已等待{timeout}s")
#         return False
#
#     def wait_window_visible(
#         self,
#         window_name: str = None,
#         window_class: str = None,
#         timeout: int = 10,
#         interval: float = 0.5,
#     ) -> bool:
#         """
#         等待窗口可见并返回窗口
#         :param interval:
#         :param timeout:
#         :param window_name:
#         :param window_class:
#         :return:
#         """
#         if window_class is None and window_name is None:
#             window_class = self._WINDOW_CLASS
#             window_name = self._WINDOW_NAME
#         start_time = time.time()
#         logger.info(f"==>等待窗口：{window_name} 出现")
#         while time.time() - start_time < timeout:
#             try:
#                 self.driver.find_window_hwnd(window_class, window_name)
#                 logger.info(f"<==窗口出现：{window_name}")
#                 return True
#             except WindowNotFoundError:
#                 time.sleep(interval)
#         logger.info(f"<==窗口未找到：{window_name}，已等待{timeout}s")
#         return False
#
#     def wait_window_invisible(
#         self,
#         window_name: str = None,
#         window_class: str = None,
#         timeout: int = 10,
#         interval: float = 0.5,
#     ) -> bool:
#         """
#         等待窗口不可见
#         :param interval:
#         :param timeout:
#         :param window_name:
#         :param window_class:
#         :return:
#         """
#         if window_class is None and window_name is None:
#             window_class = self._WINDOW_CLASS
#             window_name = self._WINDOW_NAME
#         start_time = time.time()
#         logger.info(f"==>等待窗口：{window_name}消失")
#         while time.time() - start_time < timeout:
#             try:
#                 self.driver.find_window_hwnd(window_class, window_name)
#                 logger.info(f"<==窗口存在：{window_name}， 继续等待{interval}s")
#                 time.sleep(interval)
#             except WindowNotFoundError:
#                 logger.info(f"<==窗口消失：{window_name}")
#                 return True
#         logger.info(f"<==窗口依然存在：{window_name}，已等待{timeout}s")
#         return False
#
#     def get_window_size(self):
#         """
#         获取窗口尺寸
#         :return:
#         """
#         # 获取所有打开的窗口
#         logger.info(f"==>获取窗口尺寸")
#         size = self.window.window_size
#         logger.info(f"<==窗口尺寸为：{size}")
#         return size
#
#     def wait_selector_visible_and_get_text(self, selector):
#         """
#         等待元素可见并返回元素的text
#         :return:
#         """
#         control = self.find_control(selector)
#         if self.wait_for_control_visible(control):
#             control.refresh()
#             return control.text
#         else:
#             return None
# if __name__ == '__main__':
#
#     page = BasePage()
#     # page._WINDOW_CLASS='QeeYouMainWindow'
#     # # page.find_control_and_click(Selector(By.NAT_NAME, "searched_local_games_host"))
#     # back_btn = page.find_control(Selector(By.NAT_NAME, "main_back_btn"))
#     page._WINDOW_NAME = '计算器'
#     text = page.find_control_and_get_text(Selector(By.ID,"CalculatorResults"))
#
#     print(text)
#     # 'MemoryLabel'
#     #
#     # c= page.find_control(Selector(By.ID, "ClearMemoryButton"))
#     # b= page.find_control(Selector(By.ID, "MemPlus"))
#     # print(c.ClassName)
#     # print(c)
#     # print(c.IsEnabled)
#     # print(c.GetClickablePoint())
#     #
#     # print(b.IsEnabled)
#     # print(b.GetClickablePoint())
#     # a = page.find_control(Selector(By.ID, "SettingsItem"))
#     # print(a.Exists(3))
#     # print(a.GetClickablePoint())
# python
import re
import uiautomation as auto
from typing import List

def _matches(control: auto.Control, conditions: dict) -> bool:
    for key, expect in conditions.items():
        try:
            if key == 'AutomationId':
                actual = control.AutomationId
            elif key == 'Name' or key == 'RegexName':
                actual = control.Name
            elif key == 'ClassName':
                actual = control.ClassName
            elif key == 'ControlType':
                # allow matching by name or numeric id
                actual = control.ControlTypeName if isinstance(expect, str) else control.ControlType
            else:
                actual = getattr(control, key, None)
        except Exception:
            actual = None

        if actual is None:
            return False

        if isinstance(expect, str) and expect.startswith('re:'):
            if not re.search(expect[3:], actual or ''):
                return False
        else:
            if actual != expect:
                return False
    return True

def find_controls(root: auto.Control = None, max_depth: int = 9999, **conditions) -> List[auto.Control]:
    """
    返回满足 conditions 的所有控件列表。
    root: 起始搜索控件，None 表示桌面根 (auto.Control())。
    max_depth: 最大深度。
    conditions: 属性=期望值，字符串以 're:' 开头表示正则。
    """
    if root is None:
        root = auto.Control()
    found = []

    def dfs(ctrl: auto.Control, depth: int):
        if depth > max_depth or ctrl is None:
            return
        try:
            if _matches(ctrl, conditions):
                found.append(ctrl)
        except Exception:
            pass
        # 可靠遍历子节点与兄弟节点
        child = ctrl.GetFirstChildControl()
        while child:
            dfs(child, depth + 1)
            child = child.GetNextSiblingControl()

    dfs(root, 0)
    return found

# 使用示例：查找所有 AutomationId 为 name_label 的控件并输出数量
controls = find_controls(AutomationId='name_label')
print('找到控件数：', len(controls))


