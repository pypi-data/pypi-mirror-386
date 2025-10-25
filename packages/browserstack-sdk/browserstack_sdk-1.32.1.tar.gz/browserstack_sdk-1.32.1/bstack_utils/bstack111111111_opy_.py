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
from bstack_utils.constants import bstack11ll111ll1l_opy_
def bstack1l11l11l11_opy_(bstack11ll111ll11_opy_):
    from browserstack_sdk.sdk_cli.cli import cli
    from bstack_utils.helper import bstack111ll11l_opy_
    host = bstack111ll11l_opy_(cli.config, [bstack111l1ll_opy_ (u"ࠦࡦࡶࡩࡴࠤខ"), bstack111l1ll_opy_ (u"ࠧࡧࡵࡵࡱࡰࡥࡹ࡫ࠢគ"), bstack111l1ll_opy_ (u"ࠨࡡࡱ࡫ࠥឃ")], bstack11ll111ll1l_opy_)
    return bstack111l1ll_opy_ (u"ࠧࡼࡿ࠲ࡿࢂ࠭ង").format(host, bstack11ll111ll11_opy_)