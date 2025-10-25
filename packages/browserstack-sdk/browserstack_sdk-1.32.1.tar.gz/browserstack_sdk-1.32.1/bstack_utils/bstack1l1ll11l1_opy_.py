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
from time import sleep
from datetime import datetime
from urllib.parse import urlencode
from bstack_utils.bstack11ll1111lll_opy_ import bstack11ll1111ll1_opy_
from bstack_utils.constants import *
import json
class bstack11l1ll11ll_opy_:
    def __init__(self, bstack1llll11l_opy_, bstack11ll11111ll_opy_):
        self.bstack1llll11l_opy_ = bstack1llll11l_opy_
        self.bstack11ll11111ll_opy_ = bstack11ll11111ll_opy_
        self.bstack11ll111l1ll_opy_ = None
    def __call__(self):
        bstack11ll111l1l1_opy_ = {}
        while True:
            self.bstack11ll111l1ll_opy_ = bstack11ll111l1l1_opy_.get(
                bstack111l1ll_opy_ (u"ࠨࡰࡨࡼࡹࡥࡰࡰ࡮࡯ࡣࡹ࡯࡭ࡦࠩច"),
                int(datetime.now().timestamp() * 1000)
            )
            bstack11ll111l11l_opy_ = self.bstack11ll111l1ll_opy_ - int(datetime.now().timestamp() * 1000)
            if bstack11ll111l11l_opy_ > 0:
                sleep(bstack11ll111l11l_opy_ / 1000)
            params = {
                bstack111l1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡳࡷࡱࡣࡺࡻࡩࡥࠩឆ"): self.bstack1llll11l_opy_,
                bstack111l1ll_opy_ (u"ࠪࡸ࡮ࡳࡥࡴࡶࡤࡱࡵ࠭ជ"): int(datetime.now().timestamp() * 1000)
            }
            bstack11ll1111l11_opy_ = bstack111l1ll_opy_ (u"ࠦ࡭ࡺࡴࡱࡵ࠽࠳࠴ࠨឈ") + bstack11ll111l111_opy_ + bstack111l1ll_opy_ (u"ࠧ࠵ࡡࡶࡶࡲࡱࡦࡺࡥ࠰ࡣࡳ࡭࠴ࡼ࠱࠰ࠤញ")
            if self.bstack11ll11111ll_opy_.lower() == bstack111l1ll_opy_ (u"ࠨࡲࡦࡵࡸࡰࡹࡹࠢដ"):
                bstack11ll111l1l1_opy_ = bstack11ll1111ll1_opy_.results(bstack11ll1111l11_opy_, params)
            else:
                bstack11ll111l1l1_opy_ = bstack11ll1111ll1_opy_.bstack11ll1111l1l_opy_(bstack11ll1111l11_opy_, params)
            if str(bstack11ll111l1l1_opy_.get(bstack111l1ll_opy_ (u"ࠧࡴࡶࡤࡸࡺࡹࠧឋ"), bstack111l1ll_opy_ (u"ࠨ࠴࠳࠴ࠬឌ"))) != bstack111l1ll_opy_ (u"ࠩ࠷࠴࠹࠭ឍ"):
                break
        return bstack11ll111l1l1_opy_.get(bstack111l1ll_opy_ (u"ࠪࡨࡦࡺࡡࠨណ"), bstack11ll111l1l1_opy_)