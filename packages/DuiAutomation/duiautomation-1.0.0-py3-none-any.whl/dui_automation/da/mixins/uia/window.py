# -*- coding:utf-8 -*-
# @FileName  :window.py
# @Time      :2025/10/10 20:01
# @Author    :wangfei
import logging

import uiautomation as uia


class DAControl:
    def __init__(self, uia_control: uia.Control):
        self._control = uia_control

    def __getattr__(self, name):
        """当调用 DAControl 实例本身没有的属性或方法时，
        此方法会自动从内部的 _control 对象（原始uia.Control）上查找。
        这使得你可以无缝调用所有原始方法，如 .Click(), .SendKeys() 等。"""
        if self._control:
            return getattr(self._control, name)
        raise AttributeError(
            f"'DAControl' has no attribute '{name}' and its internal control is None."
        )

    def __bool__(self) -> bool:
        """
        定义对象的布尔值，使得 `if control:` 这样的判断能正确工作。
        只有当控件有效且在屏幕上时才为 True。
        """
        try:
            # 确保控件存在且在屏幕上可见
            return (
                self._control
                and self._control.Exists()
                and not self._control.IsOffscreen
            )
        except Exception:
            return False

    def __str__(self):
        if self._control:
            return f"DAControl(Name='{self._control.Name}', ClassName='{self._control.ClassName}', AutomationId='{self._control.AutomationId}'), Rect={self._control.BoundingRectangle}"
        return "DAControl(None)"

    @property
    def name(self):
        if self._control:
            return self._control.Name
        return ""

    @property
    def text(self) -> str:
        if self._control:
            return self._control.Name
        return ""

    @property
    def visible(self) -> int:
        """判断控件可见 0 不可见 1 可见"""
        if self._control and self._control.Exists() and not self._control.IsOffscreen:
            return 1
        return 0

    @property
    def exist(self) -> bool:
        """判断控件可见"""
        return bool(self.visible)

    @property
    def selected(self):
        """判断控件是否被选中"""
        if self._control:
            # TODO 没有找到合适的方法判断是否被选中，暂时判断是否存在
            logging.warning(
                "DAControl.selected 属性的实现仅作为占位符，实际逻辑可能需要根据具体控件类型进行调整。"
            )
            return self._control.Exists()
        return False

    @property
    def parent(self):
        """获取父控件"""
        if self._control:
            parent = self._control.GetParentControl()
            return DAControl(parent)
        return None

    def click(self):
        if self._control:
            self._control.Click(simulateMove=False)

    def set_text(self, text: str):
        """写入文本"""
        if self._control:
            # 1. 保存当前剪贴板内容
            original_clipboard = uia.GetClipboardText()
            # 2. 设置剪贴板为要输入的内容
            uia.SetClipboardText(text)
            # 3. 模拟粘贴
            self._control.SendKeys("{Ctrl}v", waitTime=0.5)
            # 4. 恢复原始剪贴板内容
            uia.SetClipboardText(original_clipboard)

    def refresh(self):
        """刷新控件引用"""
        if self._control:
            self._control.Refind()

    def press_key(self, key: str):
        """按下键盘按键"""
        if self._control:
            self._control.SendKey(uia.SpecialKeyNames[key.upper()])

    @property
    def child_controls(self) -> list["DAControl"]:
        """获取子控件列表"""
        if self._control:
            children = self._control.GetChildren()
            return [DAControl(child) for child in children]
        return []

    def click_xy(self, x, y):
        """点击控件中心点"""
        if self._control:
            self._control.Click(x=x, y=y, simulateMove=False)

    def set_visible(self, visible: bool):
        """设置控件可见性"""
        if self._control:
            if visible:
                self._control.Show()
            else:
                self._control.Hide()

    def hover(self):
        """将鼠标悬停在控件上"""
        if self._control:
            self._control.MoveCursorToMyCenter(simulateMove=False)


if __name__ == "__main__":
    pass
    # time.sleep(2)
    # da = DAUIa(class_name="QeeYouMainWindow")
    # a = da.find_ui_control({"NAME": "实时热搜"})
    # p_a = da.find_control_parent(a)
    # print(p_a)
    # win = da.window()
    # elements = da.find_ui_control({"ID": "search_pc_game_option"})
    # print(elements.GetPropertyValue(49402))
    # da.window().SendKey("Enter")
    # size = da.window_size()
    # print(size)
    # for el in elements:
    #     print(el.Name)
    # elements.MoveCursorToMyCenter()
    # a = elements.GetChildren()
    # for _  in a:
    #     print(_.Name)
    # print("win:", win)
    # print(da.find_text({"ID":"qt_chat_content_wnd.mainStackedWidget.mainChat.widget.splitter.widgetRichEditWnd.drich_edit.verticalContentWidget.widget_input_wnd.textEditWidget.textEdit"}))
