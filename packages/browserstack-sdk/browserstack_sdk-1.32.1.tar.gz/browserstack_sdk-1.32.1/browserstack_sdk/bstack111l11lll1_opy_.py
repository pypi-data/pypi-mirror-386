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
import os
class RobotHandler():
    def __init__(self, args, logger, bstack1111l1l111_opy_, bstack1111l11lll_opy_):
        self.args = args
        self.logger = logger
        self.bstack1111l1l111_opy_ = bstack1111l1l111_opy_
        self.bstack1111l11lll_opy_ = bstack1111l11lll_opy_
    @staticmethod
    def version():
        import robot
        return robot.__version__
    @staticmethod
    def bstack1111ll1l1l_opy_(bstack11111111ll_opy_):
        bstack1111111l1l_opy_ = []
        if bstack11111111ll_opy_:
            tokens = str(os.path.basename(bstack11111111ll_opy_)).split(bstack111l1ll_opy_ (u"ࠤࡢࠦႛ"))
            camelcase_name = bstack111l1ll_opy_ (u"ࠥࠤࠧႜ").join(t.title() for t in tokens)
            suite_name, bstack1111111l11_opy_ = os.path.splitext(camelcase_name)
            bstack1111111l1l_opy_.append(suite_name)
        return bstack1111111l1l_opy_
    @staticmethod
    def bstack1111111ll1_opy_(typename):
        if bstack111l1ll_opy_ (u"ࠦࡆࡹࡳࡦࡴࡷ࡭ࡴࡴࠢႝ") in typename:
            return bstack111l1ll_opy_ (u"ࠧࡇࡳࡴࡧࡵࡸ࡮ࡵ࡮ࡆࡴࡵࡳࡷࠨ႞")
        return bstack111l1ll_opy_ (u"ࠨࡕ࡯ࡪࡤࡲࡩࡲࡥࡥࡇࡵࡶࡴࡸࠢ႟")