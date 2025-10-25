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
import bstack_utils.accessibility as bstack1ll1l1ll_opy_
from bstack_utils.helper import bstack1111llll1_opy_
logger = logging.getLogger(__name__)
def bstack1ll11l1lll_opy_(bstack1111111l_opy_):
  return True if bstack1111111l_opy_ in threading.current_thread().__dict__.keys() else False
def bstack1ll1l11l11_opy_(context, *args):
    tags = getattr(args[0], bstack111l1ll_opy_ (u"ࠫࡹࡧࡧࡴࠩត"), [])
    bstack1l1l1l111l_opy_ = bstack1ll1l1ll_opy_.bstack1l1lllll1_opy_(tags)
    threading.current_thread().isA11yTest = bstack1l1l1l111l_opy_
    try:
      bstack11ll1ll11_opy_ = threading.current_thread().bstackSessionDriver if bstack1ll11l1lll_opy_(bstack111l1ll_opy_ (u"ࠬࡨࡳࡵࡣࡦ࡯ࡘ࡫ࡳࡴ࡫ࡲࡲࡉࡸࡩࡷࡧࡵࠫថ")) else context.browser
      if bstack11ll1ll11_opy_ and bstack11ll1ll11_opy_.session_id and bstack1l1l1l111l_opy_ and bstack1111llll1_opy_(
              threading.current_thread(), bstack111l1ll_opy_ (u"࠭ࡡ࠲࠳ࡼࡔࡱࡧࡴࡧࡱࡵࡱࠬទ"), None):
          threading.current_thread().isA11yTest = bstack1ll1l1ll_opy_.bstack11l11111ll_opy_(bstack11ll1ll11_opy_, bstack1l1l1l111l_opy_)
    except Exception as e:
       logger.debug(bstack111l1ll_opy_ (u"ࠧࡇࡣ࡬ࡰࡪࡪࠠࡵࡱࠣࡷࡹࡧࡲࡵࠢࡤ࠵࠶ࡿࠠࡪࡰࠣࡦࡪ࡮ࡡࡷࡧ࠽ࠤࢀࢃࠧធ").format(str(e)))
def bstack1ll1lll11_opy_(bstack11ll1ll11_opy_):
    if bstack1111llll1_opy_(threading.current_thread(), bstack111l1ll_opy_ (u"ࠨ࡫ࡶࡅ࠶࠷ࡹࡕࡧࡶࡸࠬន"), None) and bstack1111llll1_opy_(
      threading.current_thread(), bstack111l1ll_opy_ (u"ࠩࡤ࠵࠶ࡿࡐ࡭ࡣࡷࡪࡴࡸ࡭ࠨប"), None) and not bstack1111llll1_opy_(threading.current_thread(), bstack111l1ll_opy_ (u"ࠪࡥ࠶࠷ࡹࡠࡵࡷࡳࡵ࠭ផ"), False):
      threading.current_thread().a11y_stop = True
      bstack1ll1l1ll_opy_.bstack11l1l111_opy_(bstack11ll1ll11_opy_, name=bstack111l1ll_opy_ (u"ࠦࠧព"), path=bstack111l1ll_opy_ (u"ࠧࠨភ"))