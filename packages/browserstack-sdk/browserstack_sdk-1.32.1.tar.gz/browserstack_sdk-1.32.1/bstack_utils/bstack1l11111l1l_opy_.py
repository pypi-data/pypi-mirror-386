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
import threading
from collections import deque
from bstack_utils.constants import *
class bstack1ll1ll1lll_opy_:
    def __init__(self):
        self._11111111l1l_opy_ = deque()
        self._11111111lll_opy_ = {}
        self._1111111l11l_opy_ = False
        self._lock = threading.RLock()
    def bstack111111111ll_opy_(self, test_name, bstack11111111ll1_opy_):
        with self._lock:
            bstack11111111l11_opy_ = self._11111111lll_opy_.get(test_name, {})
            return bstack11111111l11_opy_.get(bstack11111111ll1_opy_, 0)
    def bstack1111111l1l1_opy_(self, test_name, bstack11111111ll1_opy_):
        with self._lock:
            bstack1111111ll1l_opy_ = self.bstack111111111ll_opy_(test_name, bstack11111111ll1_opy_)
            self.bstack1111111l111_opy_(test_name, bstack11111111ll1_opy_)
            return bstack1111111ll1l_opy_
    def bstack1111111l111_opy_(self, test_name, bstack11111111ll1_opy_):
        with self._lock:
            if test_name not in self._11111111lll_opy_:
                self._11111111lll_opy_[test_name] = {}
            bstack11111111l11_opy_ = self._11111111lll_opy_[test_name]
            bstack1111111ll1l_opy_ = bstack11111111l11_opy_.get(bstack11111111ll1_opy_, 0)
            bstack11111111l11_opy_[bstack11111111ll1_opy_] = bstack1111111ll1l_opy_ + 1
    def bstack1l1lll11ll_opy_(self, bstack1111111ll11_opy_, bstack1111111lll1_opy_):
        bstack1111111l1ll_opy_ = self.bstack1111111l1l1_opy_(bstack1111111ll11_opy_, bstack1111111lll1_opy_)
        event_name = bstack11l1lll111l_opy_[bstack1111111lll1_opy_]
        bstack1l1l11llll1_opy_ = bstack111l1ll_opy_ (u"ࠨࡻࡾ࠯ࡾࢁ࠲ࢁࡽࠣὣ").format(bstack1111111ll11_opy_, event_name, bstack1111111l1ll_opy_)
        with self._lock:
            self._11111111l1l_opy_.append(bstack1l1l11llll1_opy_)
    def bstack1l1l1l1l1l_opy_(self):
        with self._lock:
            return len(self._11111111l1l_opy_) == 0
    def bstack1ll1111ll1_opy_(self):
        with self._lock:
            if self._11111111l1l_opy_:
                bstack1111111llll_opy_ = self._11111111l1l_opy_.popleft()
                return bstack1111111llll_opy_
            return None
    def capturing(self):
        with self._lock:
            return self._1111111l11l_opy_
    def bstack11lll111l1_opy_(self):
        with self._lock:
            self._1111111l11l_opy_ = True
    def bstack1l1l1111l1_opy_(self):
        with self._lock:
            self._1111111l11l_opy_ = False