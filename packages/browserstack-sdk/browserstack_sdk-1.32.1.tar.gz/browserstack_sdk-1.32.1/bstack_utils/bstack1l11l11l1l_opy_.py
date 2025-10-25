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
import json
import os
import threading
from bstack_utils.config import Config
from bstack_utils.constants import EVENTS, STAGE
from bstack_utils.helper import bstack11l111l1l11_opy_, bstack11l11l1l11_opy_, bstack1111llll1_opy_, bstack1llll1l1ll_opy_, \
    bstack11l111l11ll_opy_
from bstack_utils.measure import measure
def bstack1l1l1111ll_opy_(bstack1lllll11l111_opy_):
    for driver in bstack1lllll11l111_opy_:
        try:
            driver.quit()
        except Exception as e:
            pass
@measure(event_name=EVENTS.bstack1111l1l1_opy_, stage=STAGE.bstack1l11lllll1_opy_)
def bstack1ll111ll1_opy_(driver, status, reason=bstack111l1ll_opy_ (u"ࠧࠨ ")):
    bstack111ll1ll1_opy_ = Config.bstack111l11l11_opy_()
    if bstack111ll1ll1_opy_.bstack1111l111ll_opy_():
        return
    bstack111ll1l11_opy_ = bstack1111111l1_opy_(bstack111l1ll_opy_ (u"ࠨࡵࡨࡸࡘ࡫ࡳࡴ࡫ࡲࡲࡘࡺࡡࡵࡷࡶࠫ "), bstack111l1ll_opy_ (u"ࠩࠪ‪"), status, reason, bstack111l1ll_opy_ (u"ࠪࠫ‫"), bstack111l1ll_opy_ (u"ࠫࠬ‬"))
    driver.execute_script(bstack111ll1l11_opy_)
@measure(event_name=EVENTS.bstack1111l1l1_opy_, stage=STAGE.bstack1l11lllll1_opy_)
def bstack11l11llll1_opy_(page, status, reason=bstack111l1ll_opy_ (u"ࠬ࠭‭")):
    try:
        if page is None:
            return
        bstack111ll1ll1_opy_ = Config.bstack111l11l11_opy_()
        if bstack111ll1ll1_opy_.bstack1111l111ll_opy_():
            return
        bstack111ll1l11_opy_ = bstack1111111l1_opy_(bstack111l1ll_opy_ (u"࠭ࡳࡦࡶࡖࡩࡸࡹࡩࡰࡰࡖࡸࡦࡺࡵࡴࠩ‮"), bstack111l1ll_opy_ (u"ࠧࠨ "), status, reason, bstack111l1ll_opy_ (u"ࠨࠩ‰"), bstack111l1ll_opy_ (u"ࠩࠪ‱"))
        page.evaluate(bstack111l1ll_opy_ (u"ࠥࡣࠥࡃ࠾ࠡࡽࢀࠦ′"), bstack111ll1l11_opy_)
    except Exception as e:
        print(bstack111l1ll_opy_ (u"ࠦࡊࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡪࡰࠣࡷࡪࡺࡴࡪࡰࡪࠤࡸ࡫ࡳࡴ࡫ࡲࡲࠥࡹࡴࡢࡶࡸࡷࠥ࡬࡯ࡳࠢࡳࡰࡦࡿࡷࡳ࡫ࡪ࡬ࡹࠦࡻࡾࠤ″"), e)
def bstack1111111l1_opy_(type, name, status, reason, bstack1l111lll11_opy_, bstack11lll11ll_opy_):
    bstack1llll1ll1l_opy_ = {
        bstack111l1ll_opy_ (u"ࠬࡧࡣࡵ࡫ࡲࡲࠬ‴"): type,
        bstack111l1ll_opy_ (u"࠭ࡡࡳࡩࡸࡱࡪࡴࡴࡴࠩ‵"): {}
    }
    if type == bstack111l1ll_opy_ (u"ࠧࡢࡰࡱࡳࡹࡧࡴࡦࠩ‶"):
        bstack1llll1ll1l_opy_[bstack111l1ll_opy_ (u"ࠨࡣࡵ࡫ࡺࡳࡥ࡯ࡶࡶࠫ‷")][bstack111l1ll_opy_ (u"ࠩ࡯ࡩࡻ࡫࡬ࠨ‸")] = bstack1l111lll11_opy_
        bstack1llll1ll1l_opy_[bstack111l1ll_opy_ (u"ࠪࡥࡷ࡭ࡵ࡮ࡧࡱࡸࡸ࠭‹")][bstack111l1ll_opy_ (u"ࠫࡩࡧࡴࡢࠩ›")] = json.dumps(str(bstack11lll11ll_opy_))
    if type == bstack111l1ll_opy_ (u"ࠬࡹࡥࡵࡕࡨࡷࡸ࡯࡯࡯ࡐࡤࡱࡪ࠭※"):
        bstack1llll1ll1l_opy_[bstack111l1ll_opy_ (u"࠭ࡡࡳࡩࡸࡱࡪࡴࡴࡴࠩ‼")][bstack111l1ll_opy_ (u"ࠧ࡯ࡣࡰࡩࠬ‽")] = name
    if type == bstack111l1ll_opy_ (u"ࠨࡵࡨࡸࡘ࡫ࡳࡴ࡫ࡲࡲࡘࡺࡡࡵࡷࡶࠫ‾"):
        bstack1llll1ll1l_opy_[bstack111l1ll_opy_ (u"ࠩࡤࡶ࡬ࡻ࡭ࡦࡰࡷࡷࠬ‿")][bstack111l1ll_opy_ (u"ࠪࡷࡹࡧࡴࡶࡵࠪ⁀")] = status
        if status == bstack111l1ll_opy_ (u"ࠫ࡫ࡧࡩ࡭ࡧࡧࠫ⁁") and str(reason) != bstack111l1ll_opy_ (u"ࠧࠨ⁂"):
            bstack1llll1ll1l_opy_[bstack111l1ll_opy_ (u"࠭ࡡࡳࡩࡸࡱࡪࡴࡴࡴࠩ⁃")][bstack111l1ll_opy_ (u"ࠧࡳࡧࡤࡷࡴࡴࠧ⁄")] = json.dumps(str(reason))
    bstack11ll111l11_opy_ = bstack111l1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࡟ࡦࡺࡨࡧࡺࡺ࡯ࡳ࠼ࠣࡿࢂ࠭⁅").format(json.dumps(bstack1llll1ll1l_opy_))
    return bstack11ll111l11_opy_
def bstack1ll1lllll_opy_(url, config, logger, bstack111l1ll11_opy_=False):
    hostname = bstack11l11l1l11_opy_(url)
    is_private = bstack1llll1l1ll_opy_(hostname)
    try:
        if is_private or bstack111l1ll11_opy_:
            file_path = bstack11l111l1l11_opy_(bstack111l1ll_opy_ (u"ࠩ࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࠩ⁆"), bstack111l1ll_opy_ (u"ࠪ࠲ࡧࡹࡴࡢࡥ࡮࠱ࡨࡵ࡮ࡧ࡫ࡪ࠲࡯ࡹ࡯࡯ࠩ⁇"), logger)
            if os.environ.get(bstack111l1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡐࡔࡉࡁࡍࡡࡑࡓ࡙ࡥࡓࡆࡖࡢࡉࡗࡘࡏࡓࠩ⁈")) and eval(
                    os.environ.get(bstack111l1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡑࡕࡃࡂࡎࡢࡒࡔ࡚࡟ࡔࡇࡗࡣࡊࡘࡒࡐࡔࠪ⁉"))):
                return
            if (bstack111l1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡑࡵࡣࡢ࡮ࠪ⁊") in config and not config[bstack111l1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡒ࡯ࡤࡣ࡯ࠫ⁋")]):
                os.environ[bstack111l1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡍࡑࡆࡅࡑࡥࡎࡐࡖࡢࡗࡊ࡚࡟ࡆࡔࡕࡓࡗ࠭⁌")] = str(True)
                bstack1lllll11l11l_opy_ = {bstack111l1ll_opy_ (u"ࠩ࡫ࡳࡸࡺ࡮ࡢ࡯ࡨࠫ⁍"): hostname}
                bstack11l111l11ll_opy_(bstack111l1ll_opy_ (u"ࠪ࠲ࡧࡹࡴࡢࡥ࡮࠱ࡨࡵ࡮ࡧ࡫ࡪ࠲࡯ࡹ࡯࡯ࠩ⁎"), bstack111l1ll_opy_ (u"ࠫࡳࡻࡤࡨࡧࡢࡰࡴࡩࡡ࡭ࠩ⁏"), bstack1lllll11l11l_opy_, logger)
    except Exception as e:
        pass
def bstack11ll1l1l1_opy_(caps, bstack1lllll11l1l1_opy_):
    if bstack111l1ll_opy_ (u"ࠬࡨࡳࡵࡣࡦ࡯࠿ࡵࡰࡵ࡫ࡲࡲࡸ࠭⁐") in caps:
        caps[bstack111l1ll_opy_ (u"࠭ࡢࡴࡶࡤࡧࡰࡀ࡯ࡱࡶ࡬ࡳࡳࡹࠧ⁑")][bstack111l1ll_opy_ (u"ࠧ࡭ࡱࡦࡥࡱ࠭⁒")] = True
        if bstack1lllll11l1l1_opy_:
            caps[bstack111l1ll_opy_ (u"ࠨࡤࡶࡸࡦࡩ࡫࠻ࡱࡳࡸ࡮ࡵ࡮ࡴࠩ⁓")][bstack111l1ll_opy_ (u"ࠩ࡯ࡳࡨࡧ࡬ࡊࡦࡨࡲࡹ࡯ࡦࡪࡧࡵࠫ⁔")] = bstack1lllll11l1l1_opy_
    else:
        caps[bstack111l1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰࡯ࡳࡨࡧ࡬ࠨ⁕")] = True
        if bstack1lllll11l1l1_opy_:
            caps[bstack111l1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡰࡴࡩࡡ࡭ࡋࡧࡩࡳࡺࡩࡧ࡫ࡨࡶࠬ⁖")] = bstack1lllll11l1l1_opy_
def bstack1llllll1ll1l_opy_(bstack1111lll111_opy_):
    bstack1lllll111lll_opy_ = bstack1111llll1_opy_(threading.current_thread(), bstack111l1ll_opy_ (u"ࠬࡺࡥࡴࡶࡖࡸࡦࡺࡵࡴࠩ⁗"), bstack111l1ll_opy_ (u"࠭ࠧ⁘"))
    if bstack1lllll111lll_opy_ == bstack111l1ll_opy_ (u"ࠧࠨ⁙") or bstack1lllll111lll_opy_ == bstack111l1ll_opy_ (u"ࠨࡵ࡮࡭ࡵࡶࡥࡥࠩ⁚"):
        threading.current_thread().testStatus = bstack1111lll111_opy_
    else:
        if bstack1111lll111_opy_ == bstack111l1ll_opy_ (u"ࠩࡩࡥ࡮ࡲࡥࡥࠩ⁛"):
            threading.current_thread().testStatus = bstack1111lll111_opy_