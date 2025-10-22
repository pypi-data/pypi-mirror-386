# -*- coding: utf-8 -*-
# @Project: 芒果测试平台
# @Description:
# @Time   : 2024-04-24 10:43
# @Author : 毛鹏

from typing import Optional

from ..uidrives.android._new_android import NewAndroid
from ..uidrives.pc.new_windows import NewWindows
from ..uidrives.web.async_web._new_browser import AsyncWebNewBrowser
from ..uidrives.web.sync_web._new_browser import SyncWebNewBrowser


class DriverObject:

    def __init__(self, log, is_async=False):
        self.log = log
        self.is_async = is_async
        self.web: Optional[AsyncWebNewBrowser | SyncWebNewBrowser] = None
        self.android: Optional[NewAndroid] = None
        self.windows: Optional[NewWindows] = None

    def set_web(self,
                web_type: int,
                web_path: str | None = None,
                web_max=False,
                web_headers=False,
                web_recording=False,
                web_h5=None,
                is_header_intercept=False,
                web_is_default=False,
                videos_path=None
                ):
        if self.is_async:
            self.web = AsyncWebNewBrowser(
                web_type,
                web_path,
                web_max,
                web_headers,
                web_recording,
                web_h5,
                is_header_intercept,
                web_is_default,
                videos_path,
                log=self.log,
            )
        else:
            self.web = SyncWebNewBrowser(
                web_type,
                web_path,
                web_max,
                web_headers,
                web_recording,
                web_h5,
                is_header_intercept,
                web_is_default,
                videos_path,
                log=self.log,
            )

    def set_android(self, and_equipment: str):
        self.android = NewAndroid(and_equipment)

    def set_windows(self, win_path: str, win_title: str):
        self.windows = NewWindows(win_path, win_title)
