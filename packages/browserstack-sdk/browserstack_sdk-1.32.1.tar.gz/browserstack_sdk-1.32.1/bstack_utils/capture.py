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
import builtins
import logging
class bstack111ll111l1_opy_:
    def __init__(self, handler):
        self._11l1lllllll_opy_ = builtins.print
        self.handler = handler
        self._started = False
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self._11ll111111l_opy_ = {
            level: getattr(self.logger, level)
            for level in [bstack111l1ll_opy_ (u"࠭ࡩ࡯ࡨࡲࠫម"), bstack111l1ll_opy_ (u"ࠧࡥࡧࡥࡹ࡬࠭យ"), bstack111l1ll_opy_ (u"ࠨࡹࡤࡶࡳ࡯࡮ࡨࠩរ"), bstack111l1ll_opy_ (u"ࠩࡨࡶࡷࡵࡲࠨល")]
        }
    def start(self):
        if self._started:
            return
        self._started = True
        builtins.print = self._11ll11111l1_opy_
        self._11ll1111111_opy_()
    def _11ll11111l1_opy_(self, *args, **kwargs):
        self._11l1lllllll_opy_(*args, **kwargs)
        message = bstack111l1ll_opy_ (u"ࠪࠤࠬវ").join(map(str, args)) + bstack111l1ll_opy_ (u"ࠫࡡࡴࠧឝ")
        self._log_message(bstack111l1ll_opy_ (u"ࠬࡏࡎࡇࡑࠪឞ"), message)
    def _log_message(self, level, msg, *args, **kwargs):
        if self.handler:
            self.handler({bstack111l1ll_opy_ (u"࠭࡬ࡦࡸࡨࡰࠬស"): level, bstack111l1ll_opy_ (u"ࠧ࡮ࡧࡶࡷࡦ࡭ࡥࠨហ"): msg})
    def _11ll1111111_opy_(self):
        for level, bstack11l1llllll1_opy_ in self._11ll111111l_opy_.items():
            setattr(logging, level, self._11l1lllll1l_opy_(level, bstack11l1llllll1_opy_))
    def _11l1lllll1l_opy_(self, level, bstack11l1llllll1_opy_):
        def wrapper(msg, *args, **kwargs):
            bstack11l1llllll1_opy_(msg, *args, **kwargs)
            self._log_message(level.upper(), msg)
        return wrapper
    def reset(self):
        if not self._started:
            return
        self._started = False
        builtins.print = self._11l1lllllll_opy_
        for level, bstack11l1llllll1_opy_ in self._11ll111111l_opy_.items():
            setattr(logging, level, bstack11l1llllll1_opy_)