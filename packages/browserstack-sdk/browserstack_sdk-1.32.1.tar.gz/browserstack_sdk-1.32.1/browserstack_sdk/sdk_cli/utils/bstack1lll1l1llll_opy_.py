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
import re
from typing import List, Dict, Any
from bstack_utils.bstack1lllll11l1_opy_ import get_logger
logger = get_logger(__name__)
class bstack1ll1l1l111l_opy_:
    bstack111l1ll_opy_ (u"ࠧࠨࠢࠋࠢࠣࠤࠥࡉࡵࡴࡶࡲࡱ࡙ࡧࡧࡎࡣࡱࡥ࡬࡫ࡲࠡࡲࡵࡳࡻ࡯ࡤࡦࡵࠣࡹࡹ࡯࡬ࡪࡶࡼࠤࡲ࡫ࡴࡩࡱࡧࡷࠥࡺ࡯ࠡࡵࡨࡸࠥࡧ࡮ࡥࠢࡵࡩࡹࡸࡩࡦࡸࡨࠤࡨࡻࡳࡵࡱࡰࠤࡹࡧࡧࠡ࡯ࡨࡸࡦࡪࡡࡵࡣ࠱ࠎࠥࠦࠠࠡࡋࡷࠤࡲࡧࡩ࡯ࡶࡤ࡭ࡳࡹࠠࡵࡹࡲࠤࡸ࡫ࡰࡢࡴࡤࡸࡪࠦ࡭ࡦࡶࡤࡨࡦࡺࡡࠡࡦ࡬ࡧࡹ࡯࡯࡯ࡣࡵ࡭ࡪࡹࠠࡧࡱࡵࠤࡹ࡫ࡳࡵࠢ࡯ࡩࡻ࡫࡬ࠡࡣࡱࡨࠥࡨࡵࡪ࡮ࡧࠤࡱ࡫ࡶࡦ࡮ࠣࡧࡺࡹࡴࡰ࡯ࠣࡸࡦ࡭ࡳ࠯ࠌࠣࠤࠥࠦࡅࡢࡥ࡫ࠤࡲ࡫ࡴࡢࡦࡤࡸࡦࠦࡥ࡯ࡶࡵࡽࠥ࡯ࡳࠡࡧࡻࡴࡪࡩࡴࡦࡦࠣࡸࡴࠦࡢࡦࠢࡶࡸࡷࡻࡣࡵࡷࡵࡩࡩࠦࡡࡴ࠼ࠍࠤࠥࠦࠠࠡࠢࠣ࡯ࡪࡿ࠺ࠡࡽࠍࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠣࡨ࡬ࡩࡱࡪ࡟ࡵࡻࡳࡩࠧࡀࠠࠣ࡯ࡸࡰࡹ࡯࡟ࡥࡴࡲࡴࡩࡵࡷ࡯ࠤ࠯ࠎࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠤࡹࡥࡱࡻࡥࡴࠤ࠽ࠤࡠࡲࡩࡴࡶࠣࡳ࡫ࠦࡴࡢࡩࠣࡺࡦࡲࡵࡦࡵࡠࠎࠥࠦࠠࠡࠢࠣࠤࢂࠐࠠࠡࠢࠣࠦࠧࠨᗺ")
    _11lll1l1l1l_opy_: Dict[str, Dict[str, Any]] = {}
    _11lll1l11l1_opy_: Dict[str, Dict[str, Any]] = {}
    @staticmethod
    def set_custom_tag(bstack1111111l_opy_: str, key_value: str, bstack11lll1l1lll_opy_: bool = False) -> None:
        if not bstack1111111l_opy_ or not key_value or bstack1111111l_opy_.strip() == bstack111l1ll_opy_ (u"ࠨࠢᗻ") or key_value.strip() == bstack111l1ll_opy_ (u"ࠢࠣᗼ"):
            logger.error(bstack111l1ll_opy_ (u"ࠣ࡭ࡨࡽࡤࡴࡡ࡮ࡧࠣࡥࡳࡪࠠ࡬ࡧࡼࡣࡻࡧ࡬ࡶࡧࠣࡱࡺࡹࡴࠡࡤࡨࠤࡳࡵ࡮࠮ࡰࡸࡰࡱࠦࡡ࡯ࡦࠣࡲࡴࡴ࠭ࡦ࡯ࡳࡸࡾࠨᗽ"))
        values: List[str] = bstack1ll1l1l111l_opy_.bstack11lll1l111l_opy_(key_value)
        bstack11lll1l1ll1_opy_ = {bstack111l1ll_opy_ (u"ࠤࡩ࡭ࡪࡲࡤࡠࡶࡼࡴࡪࠨᗾ"): bstack111l1ll_opy_ (u"ࠥࡱࡺࡲࡴࡪࡡࡧࡶࡴࡶࡤࡰࡹࡱࠦᗿ"), bstack111l1ll_opy_ (u"ࠦࡻࡧ࡬ࡶࡧࡶࠦᘀ"): values}
        bstack11lll1l1111_opy_ = bstack1ll1l1l111l_opy_._11lll1l11l1_opy_ if bstack11lll1l1lll_opy_ else bstack1ll1l1l111l_opy_._11lll1l1l1l_opy_
        if bstack1111111l_opy_ in bstack11lll1l1111_opy_:
            bstack11lll1ll11l_opy_ = bstack11lll1l1111_opy_[bstack1111111l_opy_]
            bstack11lll1l1l11_opy_ = bstack11lll1ll11l_opy_.get(bstack111l1ll_opy_ (u"ࠧࡼࡡ࡭ࡷࡨࡷࠧᘁ"), [])
            for val in values:
                if val not in bstack11lll1l1l11_opy_:
                    bstack11lll1l1l11_opy_.append(val)
            bstack11lll1ll11l_opy_[bstack111l1ll_opy_ (u"ࠨࡶࡢ࡮ࡸࡩࡸࠨᘂ")] = bstack11lll1l1l11_opy_
        else:
            bstack11lll1l1111_opy_[bstack1111111l_opy_] = bstack11lll1l1ll1_opy_
    @staticmethod
    def bstack1l111l11ll1_opy_() -> Dict[str, Dict[str, Any]]:
        return bstack1ll1l1l111l_opy_._11lll1l1l1l_opy_
    @staticmethod
    def bstack11lll1ll111_opy_() -> Dict[str, Dict[str, Any]]:
        return bstack1ll1l1l111l_opy_._11lll1l11l1_opy_
    @staticmethod
    def bstack11lll1l111l_opy_(bstack11lll1l11ll_opy_: str) -> List[str]:
        bstack111l1ll_opy_ (u"ࠢࠣࠤࠍࠤࠥࠦࠠࠡࠢࠣࠤࡘࡶ࡬ࡪࡶࡶࠤࡹ࡮ࡥࠡ࡫ࡱࡴࡺࡺࠠࡴࡶࡵ࡭ࡳ࡭ࠠࡣࡻࠣࡧࡴࡳ࡭ࡢࡵࠣࡻ࡭࡯࡬ࡦࠢࡵࡩࡸࡶࡥࡤࡶ࡬ࡲ࡬ࠦࡤࡰࡷࡥࡰࡪ࠳ࡱࡶࡱࡷࡩࡩࠦࡳࡶࡤࡶࡸࡷ࡯࡮ࡨࡵ࠱ࠎࠥࠦࠠࠡࠢࠣࠤࠥࡌ࡯ࡳࠢࡨࡼࡦࡳࡰ࡭ࡧ࠽ࠤࠬࡧࠬࠡࠤࡥ࠰ࡨࠨࠬࠡࡦࠪࠤ࠲ࡄࠠ࡜ࠩࡤࠫ࠱ࠦࠧࡣ࠮ࡦࠫ࠱ࠦࠧࡥࠩࡠࠎࠥࠦࠠࠡࠢࠣࠤࠥࠨࠢࠣᘃ")
        pattern = re.compile(bstack111l1ll_opy_ (u"ࡳࠩࠥࠬࡠࡤࠢ࡞ࠬࠬࠦࢁ࠮࡛࡟࠮ࡠ࠯࠮࠭ᘄ"))
        result = []
        for match in pattern.finditer(bstack11lll1l11ll_opy_):
            if match.group(1) is not None:
                result.append(match.group(1).strip())
            elif match.group(2) is not None:
                result.append(match.group(2).strip())
        return result
    def __new__(cls, *args, **kwargs):
        raise Exception(bstack111l1ll_opy_ (u"ࠤࡘࡸ࡮ࡲࡩࡵࡻࠣࡧࡱࡧࡳࡴࠢࡶ࡬ࡴࡻ࡬ࡥࠢࡱࡳࡹࠦࡢࡦࠢ࡬ࡲࡸࡺࡡ࡯ࡶ࡬ࡥࡹ࡫ࡤࠣᘅ"))