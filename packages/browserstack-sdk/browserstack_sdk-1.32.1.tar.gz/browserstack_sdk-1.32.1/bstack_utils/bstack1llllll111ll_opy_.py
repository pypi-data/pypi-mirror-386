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
import logging
logger = logging.getLogger(__name__)
bstack1lllll1lllll_opy_ = 1000
bstack1lllll1ll11l_opy_ = 2
class bstack1lllll1lll11_opy_:
    def __init__(self, handler, bstack1lllll1ll1l1_opy_=bstack1lllll1lllll_opy_, bstack1llllll111l1_opy_=bstack1lllll1ll11l_opy_):
        self.queue = []
        self.handler = handler
        self.bstack1lllll1ll1l1_opy_ = bstack1lllll1ll1l1_opy_
        self.bstack1llllll111l1_opy_ = bstack1llllll111l1_opy_
        self.lock = threading.Lock()
        self.timer = None
        self.bstack1lllllllll1_opy_ = None
    def start(self):
        if not (self.timer and self.timer.is_alive()):
            self.bstack1lllll1llll1_opy_()
    def bstack1lllll1llll1_opy_(self):
        self.bstack1lllllllll1_opy_ = threading.Event()
        def bstack1lllll1ll1ll_opy_():
            self.bstack1lllllllll1_opy_.wait(self.bstack1llllll111l1_opy_)
            if not self.bstack1lllllllll1_opy_.is_set():
                self.bstack1lllll1lll1l_opy_()
        self.timer = threading.Thread(target=bstack1lllll1ll1ll_opy_, daemon=True)
        self.timer.start()
    def bstack1llllll11111_opy_(self):
        try:
            if self.bstack1lllllllll1_opy_ and not self.bstack1lllllllll1_opy_.is_set():
                self.bstack1lllllllll1_opy_.set()
            if self.timer and self.timer.is_alive() and self.timer != threading.current_thread():
                self.timer.join()
        except Exception as e:
            logger.debug(bstack111l1ll_opy_ (u"ࠩ࡞ࡷࡹࡵࡰࡠࡶ࡬ࡱࡪࡸ࡝ࠡࡇࡻࡧࡪࡶࡴࡪࡱࡱ࠾ࠥ࠭ῖ") + (str(e) or bstack111l1ll_opy_ (u"ࠥࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡣࡰࡷ࡯ࡨࠥࡴ࡯ࡵࠢࡥࡩࠥࡩ࡯࡯ࡸࡨࡶࡹ࡫ࡤࠡࡶࡲࠤࡸࡺࡲࡪࡰࡪࠦῗ")))
        finally:
            self.timer = None
    def bstack1llllll1111l_opy_(self):
        if self.timer:
            self.bstack1llllll11111_opy_()
        self.bstack1lllll1llll1_opy_()
    def add(self, event):
        with self.lock:
            self.queue.append(event)
            if len(self.queue) >= self.bstack1lllll1ll1l1_opy_:
                threading.Thread(target=self.bstack1lllll1lll1l_opy_).start()
    def bstack1lllll1lll1l_opy_(self, source = bstack111l1ll_opy_ (u"ࠫࠬῘ")):
        with self.lock:
            if not self.queue:
                self.bstack1llllll1111l_opy_()
                return
            data = self.queue[:self.bstack1lllll1ll1l1_opy_]
            del self.queue[:self.bstack1lllll1ll1l1_opy_]
        self.handler(data)
        if source != bstack111l1ll_opy_ (u"ࠬࡹࡨࡶࡶࡧࡳࡼࡴࠧῙ"):
            self.bstack1llllll1111l_opy_()
    def shutdown(self):
        self.bstack1llllll11111_opy_()
        while self.queue:
            self.bstack1lllll1lll1l_opy_(source=bstack111l1ll_opy_ (u"࠭ࡳࡩࡷࡷࡨࡴࡽ࡮ࠨῚ"))