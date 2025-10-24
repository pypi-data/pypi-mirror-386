from wxauto4 import uia
from wxauto4.utils.win32 import (
    FindWindow,
    GetAllWindows,
    SetClipboardText,
    ReadClipboardData
)
from wxauto4.utils.tools import (
    find_window_from_root,
    is_valid_image,
    get_file_dir,
    now_time,
)
from .base import BaseUISubWnd
from wxauto4.param import WxParam, WxResponse
from wxauto4.logger import wxlog
from pathlib import Path
from typing import (
    List,
    Literal
)
import traceback
import shutil
import time
import os

class UpdateWindow(BaseUISubWnd):
    _ui_cls_name: str = "mmui::XView"
    _win_cls_name: str = "Qt51514QWindowIcon"
    _win_name: str = "微信"

    def __init__(self):
        wins = GetAllWindows(name=self._win_name, classname=self._win_cls_name)
        for win in wins:
            self.control = uia.ControlFromHandle(win[0])
            if (
                (text:=self.control.TextControl()).Exists(0)
                and text.Name=='新版本'
            ):
                break

    def ignore(self):
        ignore_btn = self.control.ButtonControl(
            ClassName="mmui::XOutlineButton", 
            Name="忽略本次更新"
        )
        if ignore_btn.Exists(0):
            ignore_btn.Click()

class Menu(BaseUISubWnd):
    _ui_cls_name:str="mmui::XMenu"
    _win_cls_name:str = "Qt51514QWindowToolSaveBits"
    _win_name: str="Weixin"

    def __init__(self, parent, timeout=2):
        self.parent = parent
        self.root = parent.root
        t0 = time.time()
        while True:
            if time.time() - t0 > timeout:
                break
            wins = GetAllWindows(classname=self._win_cls_name,name=self._win_name)
            _find = False
            for win in wins:
                self.control = uia.ControlFromHandle(win[0])
                if self.control.ClassName == self._ui_cls_name:
                    _find = True
                    break
            if _find:
                break
    
    @property
    def option_controls(self):
        return [
            i for i in
            self.control.GetChildren()
            if i.ControlTypeName == 'MenuItemControl'
        ]
    
    @property
    def option_names(self):
        return [c.Name for c in self.option_controls]
    
    def select(self, item):
        if not self.exists(0):
            return WxResponse.failure('菜单窗口不存在')
        if isinstance(item, int):
            self.option_controls[item].Click()
            return WxResponse.success()
        
        for c in self.option_controls:
            if c.Name == item:
                c.Click()
                return WxResponse.success()
        if self.exists(0):
            self.close()
        return WxResponse.failure(f'未找到选项：{item}')

class SelectContactWnd(BaseUISubWnd):
    _ui_cls_name:str="mmui::SessionPickerWindow"
    _ui_name: str="微信发送给"
    _win_cls_name:str = "Qt51514QWindowIcon"
    _win_name: str="微信发送给"

    def __init__(self, parent, timeout=2):
        self.parent = parent
        self.root = parent.root
        t0 = time.time()
        while True:
            if time.time() - t0 > timeout:
                break
            wins = GetAllWindows(classname=self._win_cls_name,name=self._win_name)
            _find = False
            for win in wins:
                self.control = uia.ControlFromHandle(win[0])
                if self.control.ClassName == self._ui_cls_name:
                    _find = True
                    break
            if _find:
                break
        if _find:
            self.confirm_btn = self.control.ButtonControl(AutomationId="confirm_btn")
            self.confirm_btn_rect = self.confirm_btn.BoundingRectangle

    def search(self, keyword, interval=0.1):
        """搜索并选择，需完全匹配"""
        # SearchContactView = self.control.GroupControl(ClassName="mmui::SearchContactView")
        search_control = self.control.EditControl(ClassName="mmui::XValidatorTextEdit")
        SetClipboardText(keyword)
        search_control.Click()
        search_control.SendKeys('{Ctrl}a')
        search_control.RightClick()
        menu = Menu(self)
        menu.select('粘贴')
        time.sleep(interval)
        all_controls = []
        for c, d in uia.WalkControl(self.control):
            all_controls.append(c)
        for target in all_controls:
            if (
                target.ControlTypeName == 'CheckBoxControl'
                and target.Name == keyword
            ):
                target.Click()
                return True

    def confirm(self):
        # self.root.control.winapi.click_by_bbox(self.confirm_btn_bbox)
        self.confirm_btn.Click()

    def send(self, target, interval=0.1):
        if isinstance(target, str):
            target = [target]

        for i in target:
            self.search(i, interval)

        self.confirm()


class SearchNewFriendWnd(BaseUISubWnd):
    _win_cls_name: str = 'Qt51514QWindowIcon'
    _win_name: str="添加朋友"

    def __init__(self):
        self.control = find_window_from_root(classname=self._win_cls_name, name=self._win_name)
        if self.control:
            self.init()

    def init(self):
        self.apply_btn = self.control.ButtonControl(
            AutomationId="fixed_height_v_view.content_v_view.ContactProfileBottomUi.add_friend_button",
            Name="添加到通讯录",
            ClassName="mmui::XOutlineButton",
            searchDepth=9
        )
        self.search_edit = self.control.EditControl(ClassName="mmui::XValidatorTextEdit", Name="搜索")
        self.search_btn = self.control.ButtonControl(ClassName="mmui::XOutlineButton", Name="搜索")

    def search(self, keyword):
        self.search_edit.SendKeys('{Ctrl}a')
        SetClipboardText(keyword)
        self.search_edit.SendKeys('{Ctrl}v')
        self.search_btn.Click()

    def apply(self):
        if self.apply_btn.Exists(0):
            self.apply_btn.Click()
            return WxResponse.success()
        else:
            return WxResponse.failure('未找到添加按钮')


class WeChatImage(BaseUISubWnd):
    _win_cls_name: str = 'Qt51514QWindowIcon'
    _win_name: str="预览"

    def __init__(self, parent):
        self.parent = parent
        self.root = self.parent.root
        self.control = find_window_from_root(classname=self._win_cls_name, name=self._win_name)
        if self.control:
            self.init()

    def init(self):
        toolbar_control = self.control.GroupControl(ClassName="mmui::PreviewToolbarView")
        self.tools = {
            btn.Name: btn for ele in toolbar_control.GetChildren()
            if (btn := ele.ButtonControl()).Exists(0)
        }
        if self.control.WindowControl(ClassName="mmui::XPlayerControlView").Exists(0):
            self.type = 'video'
        else:
            self.type = 'image'

    def save(self, dir_path=None, timeout=10) -> Path:
        """保存图片/视频

        Args:
            dir_path (str): 保存文件夹路径
            timeout (int, optional): 保存超时时间，默认10秒
        
        Returns:
            Path: 文件保存路径，即savepath
        """
        image_sufix = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'pic']
        if dir_path is None:
            dir_path = WxParam.DEFAULT_SAVE_PATH
        t0 = time.time()

        n = 1
        SetClipboardText('')
        while True:
            if time.time() - t0 > timeout:
                if self.control.Exists(0):
                    self.control.SendKeys('{Esc}')
                return WxResponse.failure('下载超时')
            if self.control.TextControl(Name="图片过期或已被清理").Exists(0):
                return WxResponse.failure('图片过期或已被清理')
            try:
                self.tools['更多'].Click()
                menu = Menu(self.root)
                menu.select('复制')
                if self.type == 'video':
                    for _ in range(30):
                        clipboard_data = ReadClipboardData()
                        wxlog.debug(f"读取到剪贴板数据：{clipboard_data.keys()}")
                        if '15' not in clipboard_data:
                            time.sleep(0.1)
                            continue
                        path = clipboard_data['15'][0]
                        break
                else:
                    clipboard_data = ReadClipboardData()
                    path = clipboard_data['15'][0]
                if not os.path.exists(path):
                    return WxResponse.failure('微信BUG无法获取该图片，请重新获取')
                suffix = os.path.splitext(path)[1]
                if (
                    suffix in image_sufix
                    and not is_valid_image(path)
                ) or not os.path.getsize(path):
                    wxlog.debug("图片格式不正确，删除文件")
                    os.remove(path)
                    continue
                wxlog.debug(f"读取到图片/视频路径[{os.path.exists(path)}, {os.path.getsize(path)}]：{path}")
                break
            except:
                if n > 3:
                    return WxResponse.failure('微信BUG无法获取该图片，请重新获取')
                n += 1
                wxlog.debug(traceback.format_exc())
            time.sleep(0.1)
        filename = f"wxauto_{self.type}_{now_time()}{suffix}"
        filepath = get_file_dir(dir_path) / filename
        wxlog.debug(f"保存到文件：{filepath}")
        shutil.copyfile(path, filepath)
        SetClipboardText('')
        if self.control.Exists(0):
            wxlog.debug("关闭图片窗口")
            self.control.SendKeys('{Esc}')
        return filepath
