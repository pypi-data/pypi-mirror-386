# coding: UTF-8
import sys
bstack1l1llll_opy_ = sys.version_info [0] == 2
bstack1ll1l1l_opy_ = 2048
bstack11l1l_opy_ = 7
def bstack111l1ll_opy_ (bstack11l1111_opy_):
    global bstack1l1ll_opy_
    bstack1llll11_opy_ = ord (bstack11l1111_opy_ [-1])
    bstack1111lll_opy_ = bstack11l1111_opy_ [:-1]
    bstack1lll_opy_ = bstack1llll11_opy_ % len (bstack1111lll_opy_)
    bstack1l11_opy_ = bstack1111lll_opy_ [:bstack1lll_opy_] + bstack1111lll_opy_ [bstack1lll_opy_:]
    if bstack1l1llll_opy_:
        bstack1l111ll_opy_ = unicode () .join ([unichr (ord (char) - bstack1ll1l1l_opy_ - (bstack111l11l_opy_ + bstack1llll11_opy_) % bstack11l1l_opy_) for bstack111l11l_opy_, char in enumerate (bstack1l11_opy_)])
    else:
        bstack1l111ll_opy_ = str () .join ([chr (ord (char) - bstack1ll1l1l_opy_ - (bstack111l11l_opy_ + bstack1llll11_opy_) % bstack11l1l_opy_) for bstack111l11l_opy_, char in enumerate (bstack1l11_opy_)])
    return eval (bstack1l111ll_opy_)
class bstack1l1l1l1ll1_opy_:
    def __init__(self, handler):
        self._1lllll11ll1l_opy_ = None
        self.handler = handler
        self._1lllll11lll1_opy_ = self.bstack1lllll11ll11_opy_()
        self.patch()
    def patch(self):
        self._1lllll11ll1l_opy_ = self._1lllll11lll1_opy_.execute
        self._1lllll11lll1_opy_.execute = self.bstack1lllll11l1ll_opy_()
    def bstack1lllll11l1ll_opy_(self):
        def execute(this, driver_command, *args, **kwargs):
            self.handler(bstack111l1ll_opy_ (u"ࠧࡨࡥࡧࡱࡵࡩࠧ…"), driver_command, None, this, args)
            response = self._1lllll11ll1l_opy_(this, driver_command, *args, **kwargs)
            self.handler(bstack111l1ll_opy_ (u"ࠨࡡࡧࡶࡨࡶࠧ‧"), driver_command, response)
            return response
        return execute
    def reset(self):
        self._1lllll11lll1_opy_.execute = self._1lllll11ll1l_opy_
    @staticmethod
    def bstack1lllll11ll11_opy_():
        from selenium.webdriver.remote.webdriver import WebDriver
        return WebDriver