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
import time
from bstack_utils.bstack11ll1111lll_opy_ import bstack11ll1111ll1_opy_
from bstack_utils.constants import bstack11l1ll1l1ll_opy_
from bstack_utils.helper import get_host_info, bstack111lll11ll1_opy_
class bstack111l11l1111_opy_:
    bstack111l1ll_opy_ (u"ࠥࠦࠧࠐࠠࠡࠢࠣࡌࡦࡴࡤ࡭ࡧࡶࠤࡹ࡫ࡳࡵࠢࡲࡶࡩ࡫ࡲࡪࡰࡪࠤࡴࡸࡣࡩࡧࡶࡸࡷࡧࡴࡪࡱࡱࠤࡼ࡯ࡴࡩࠢࡷ࡬ࡪࠦࡂࡳࡱࡺࡷࡪࡸࡓࡵࡣࡦ࡯ࠥࡹࡥࡳࡸࡨࡶ࠳ࠐࠠࠡࠢࠣࠦࠧࠨₛ")
    def __init__(self, config, logger):
        bstack111l1ll_opy_ (u"ࠦࠧࠨࠊࠡࠢࠣࠤࠥࠦࠠࠡ࠼ࡳࡥࡷࡧ࡭ࠡࡥࡲࡲ࡫࡯ࡧ࠻ࠢࡧ࡭ࡨࡺࠬࠡࡶࡨࡷࡹࠦ࡯ࡳࡥ࡫ࡩࡸࡺࡲࡢࡶ࡬ࡳࡳࠦࡣࡰࡰࡩ࡭࡬ࠐࠠࠡࠢࠣࠤࠥࠦࠠ࠻ࡲࡤࡶࡦࡳࠠࡰࡴࡦ࡬ࡪࡹࡴࡳࡣࡷ࡭ࡴࡴ࡟ࡴࡶࡵࡥࡹ࡫ࡧࡺ࠼ࠣࡷࡹࡸࠬࠡࡶࡨࡷࡹࠦ࡯ࡳࡦࡨࡶ࡮ࡴࡧࠡࡵࡷࡶࡦࡺࡥࡨࡻࠣࡲࡦࡳࡥࠋࠢࠣࠤࠥࠦࠠࠡࠢࠥࠦࠧₜ")
        self.config = config
        self.logger = logger
        self.bstack1llll1l1ll11_opy_ = bstack111l1ll_opy_ (u"ࠧࡺࡥࡴࡶࡲࡶࡨ࡮ࡥࡴࡶࡵࡥࡹ࡯࡯࡯࠱ࡤࡴ࡮࠵ࡶ࠲࠱ࡶࡴࡱ࡯ࡴ࠮ࡶࡨࡷࡹࡹࠢ₝")
        self.bstack1llll1l11ll1_opy_ = None
        self.bstack1llll1ll111l_opy_ = 60
        self.bstack1llll1l1l111_opy_ = 5
        self.bstack1llll1l1llll_opy_ = 0
    def bstack111l111l1ll_opy_(self, test_files, orchestration_strategy, bstack1ll1l1l1111_opy_={}):
        bstack111l1ll_opy_ (u"ࠨࠢࠣࠌࠣࠤࠥࠦࠠࠡࠢࠣࡍࡳ࡯ࡴࡪࡣࡷࡩࡸࠦࡴࡩࡧࠣࡷࡵࡲࡩࡵࠢࡷࡩࡸࡺࡳࠡࡴࡨࡵࡺ࡫ࡳࡵࠢࡤࡲࡩࠦࡳࡵࡱࡵࡩࡸࠦࡴࡩࡧࠣࡶࡪࡹࡰࡰࡰࡶࡩࠥࡪࡡࡵࡣࠣࡪࡴࡸࠠࡱࡱ࡯ࡰ࡮ࡴࡧ࠯ࠌࠣࠤࠥࠦࠠࠡࠢࠣࠦࠧࠨ₞")
        self.logger.debug(bstack111l1ll_opy_ (u"ࠢ࡜ࡵࡳࡰ࡮ࡺࡔࡦࡵࡷࡷࡢࠦࡉ࡯࡫ࡷ࡭ࡦࡺࡩ࡯ࡩࠣࡷࡵࡲࡩࡵࠢࡷࡩࡸࡺࡳࠡࡹ࡬ࡸ࡭ࠦࡳࡵࡴࡤࡸࡪ࡭ࡹ࠻ࠢࡾࢁࠧ₟").format(orchestration_strategy))
        try:
            bstack1llll1ll11l1_opy_ = []
            bstack111l1ll_opy_ (u"ࠣࠤ࡛ࠥࡪࠦࡷࡪ࡮࡯ࠤࡳࡵࡴࠡࡨࡨࡸࡨ࡮ࠠࡨ࡫ࡷࠤࡲ࡫ࡴࡢࡦࡤࡸࡦࠦࡩࡴࠢࡶࡳࡺࡸࡣࡦࠢ࡬ࡷࠥࡺࡹࡱࡧࠣࡳ࡫ࠦࡡࡳࡴࡤࡽࠥࡧ࡮ࡥࠢ࡬ࡸࠬࡹࠠࡦ࡮ࡨࡱࡪࡴࡴࡴࠢࡤࡶࡪࠦ࡯ࡧࠢࡷࡽࡵ࡫ࠠࡥ࡫ࡦࡸࠏࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࡦࡪࡩࡡࡶࡵࡨࠤ࡮ࡴࠠࡵࡪࡤࡸࠥࡩࡡࡴࡧ࠯ࠤࡺࡹࡥࡳࠢ࡫ࡥࡸࠦࡰࡳࡱࡹ࡭ࡩ࡫ࡤࠡ࡯ࡸࡰࡹ࡯࠭ࡳࡧࡳࡳࠥࡹ࡯ࡶࡴࡦࡩࠥࡽࡩࡵࡪࠣࡪࡪࡧࡴࡶࡴࡨࡆࡷࡧ࡮ࡤࡪࠣ࡭ࡳࠦࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࠧࠨࠢ₠")
            source = bstack1ll1l1l1111_opy_[bstack111l1ll_opy_ (u"ࠩࡵࡹࡳࡥࡳ࡮ࡣࡵࡸࡤࡹࡥ࡭ࡧࡦࡸ࡮ࡵ࡮ࠨ₡")].get(bstack111l1ll_opy_ (u"ࠪࡷࡴࡻࡲࡤࡧࠪ₢"), [])
            bstack1llll1l1l1l1_opy_ = isinstance(source, list) and all(isinstance(src, dict) and src is not None for src in source) and len(source) > 0
            if bstack1ll1l1l1111_opy_[bstack111l1ll_opy_ (u"ࠫࡷࡻ࡮ࡠࡵࡰࡥࡷࡺ࡟ࡴࡧ࡯ࡩࡨࡺࡩࡰࡰࠪ₣")].get(bstack111l1ll_opy_ (u"ࠬ࡫࡮ࡢࡤ࡯ࡩࡩ࠭₤"), False) and not bstack1llll1l1l1l1_opy_:
                bstack1llll1ll11l1_opy_ = bstack111lll11ll1_opy_(source) # bstack111lll11111_opy_-repo is handled bstack1llll1l1ll1l_opy_
            payload = {
                bstack111l1ll_opy_ (u"ࠨࡴࡦࡵࡷࡷࠧ₥"): [{bstack111l1ll_opy_ (u"ࠢࡧ࡫࡯ࡩࡕࡧࡴࡩࠤ₦"): f} for f in test_files],
                bstack111l1ll_opy_ (u"ࠣࡱࡵࡧ࡭࡫ࡳࡵࡴࡤࡸ࡮ࡵ࡮ࡔࡶࡵࡥࡹ࡫ࡧࡺࠤ₧"): orchestration_strategy,
                bstack111l1ll_opy_ (u"ࠤࡲࡶࡨ࡮ࡥࡴࡶࡵࡥࡹ࡯࡯࡯ࡏࡨࡸࡦࡪࡡࡵࡣࠥ₨"): bstack1ll1l1l1111_opy_,
                bstack111l1ll_opy_ (u"ࠥࡲࡴࡪࡥࡊࡰࡧࡩࡽࠨ₩"): int(os.environ.get(bstack111l1ll_opy_ (u"ࠦࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡒࡔࡊࡅࡠࡋࡑࡈࡊ࡞ࠢ₪")) or bstack111l1ll_opy_ (u"ࠧ࠶ࠢ₫")),
                bstack111l1ll_opy_ (u"ࠨࡴࡰࡶࡤࡰࡓࡵࡤࡦࡵࠥ€"): int(os.environ.get(bstack111l1ll_opy_ (u"ࠢࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡐࡖࡄࡐࡤࡔࡏࡅࡇࡢࡇࡔ࡛ࡎࡕࠤ₭")) or bstack111l1ll_opy_ (u"ࠣ࠳ࠥ₮")),
                bstack111l1ll_opy_ (u"ࠤࡳࡶࡴࡰࡥࡤࡶࡑࡥࡲ࡫ࠢ₯"): self.config.get(bstack111l1ll_opy_ (u"ࠪࡴࡷࡵࡪࡦࡥࡷࡒࡦࡳࡥࠨ₰"), bstack111l1ll_opy_ (u"ࠫࠬ₱")),
                bstack111l1ll_opy_ (u"ࠧࡨࡵࡪ࡮ࡧࡒࡦࡳࡥࠣ₲"): self.config.get(bstack111l1ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡓࡧ࡭ࡦࠩ₳"), os.path.basename(os.path.abspath(os.getcwd()))),
                bstack111l1ll_opy_ (u"ࠢࡣࡷ࡬ࡰࡩࡘࡵ࡯ࡋࡧࡩࡳࡺࡩࡧ࡫ࡨࡶࠧ₴"): os.environ.get(bstack111l1ll_opy_ (u"ࠣࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡃࡗࡌࡐࡉࡥࡒࡖࡐࡢࡍࡉࡋࡎࡕࡋࡉࡍࡊࡘࠢ₵"), bstack111l1ll_opy_ (u"ࠤࠥ₶")),
                bstack111l1ll_opy_ (u"ࠥ࡬ࡴࡹࡴࡊࡰࡩࡳࠧ₷"): get_host_info(),
                bstack111l1ll_opy_ (u"ࠦࡵࡸࡄࡦࡶࡤ࡭ࡱࡹࠢ₸"): bstack1llll1ll11l1_opy_
            }
            self.logger.debug(bstack111l1ll_opy_ (u"ࠧࡡࡳࡱ࡮࡬ࡸ࡙࡫ࡳࡵࡵࡠࠤࡘ࡫࡮ࡥ࡫ࡱ࡫ࠥࡺࡥࡴࡶࠣࡪ࡮ࡲࡥࡴ࠼ࠣࡿࢂࠨ₹").format(payload))
            response = bstack11ll1111ll1_opy_.bstack1lllll1l1ll1_opy_(self.bstack1llll1l1ll11_opy_, payload)
            if response:
                self.bstack1llll1l11ll1_opy_ = self._1llll1l11lll_opy_(response)
                self.logger.debug(bstack111l1ll_opy_ (u"ࠨ࡛ࡴࡲ࡯࡭ࡹ࡚ࡥࡴࡶࡶࡡ࡙ࠥࡰ࡭࡫ࡷࠤࡹ࡫ࡳࡵࡵࠣࡶࡪࡹࡰࡰࡰࡶࡩ࠿ࠦࡻࡾࠤ₺").format(self.bstack1llll1l11ll1_opy_))
            else:
                self.logger.error(bstack111l1ll_opy_ (u"ࠢ࡜ࡵࡳࡰ࡮ࡺࡔࡦࡵࡷࡷࡢࠦࡆࡢ࡫࡯ࡩࡩࠦࡴࡰࠢࡪࡩࡹࠦࡳࡱ࡮࡬ࡸࠥࡺࡥࡴࡶࡶࠤࡷ࡫ࡳࡱࡱࡱࡷࡪ࠴ࠢ₻"))
        except Exception as e:
            self.logger.error(bstack111l1ll_opy_ (u"ࠣ࡝ࡶࡴࡱ࡯ࡴࡕࡧࡶࡸࡸࡣࠠࡆࡺࡦࡩࡵࡺࡩࡰࡰࠣ࡭ࡳࠦࡳࡦࡰࡧ࡭ࡳ࡭ࠠࡵࡧࡶࡸࠥ࡬ࡩ࡭ࡧࡶ࠾࠿ࠦࡻࡾࠤ₼").format(e))
    def _1llll1l11lll_opy_(self, response):
        bstack111l1ll_opy_ (u"ࠤࠥࠦࠏࠦࠠࠡࠢࠣࠤࠥࠦࡐࡳࡱࡦࡩࡸࡹࡥࡴࠢࡷ࡬ࡪࠦࡳࡱ࡮࡬ࡸࠥࡺࡥࡴࡶࡶࠤࡆࡖࡉࠡࡴࡨࡷࡵࡵ࡮ࡴࡧࠣࡥࡳࡪࠠࡦࡺࡷࡶࡦࡩࡴࡴࠢࡵࡩࡱ࡫ࡶࡢࡰࡷࠤ࡫࡯ࡥ࡭ࡦࡶ࠲ࠏࠦࠠࠡࠢࠣࠤࠥࠦࠢࠣࠤ₽")
        bstack11l1ll1lll_opy_ = {}
        bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠥࡸ࡮ࡳࡥࡰࡷࡷࠦ₾")] = response.get(bstack111l1ll_opy_ (u"ࠦࡹ࡯࡭ࡦࡱࡸࡸࠧ₿"), self.bstack1llll1ll111l_opy_)
        bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠧࡺࡩ࡮ࡧࡲࡹࡹࡏ࡮ࡵࡧࡵࡺࡦࡲࠢ⃀")] = response.get(bstack111l1ll_opy_ (u"ࠨࡴࡪ࡯ࡨࡳࡺࡺࡉ࡯ࡶࡨࡶࡻࡧ࡬ࠣ⃁"), self.bstack1llll1l1l111_opy_)
        bstack1llll1ll1l1l_opy_ = response.get(bstack111l1ll_opy_ (u"ࠢࡳࡧࡶࡹࡱࡺࡕࡳ࡮ࠥ⃂"))
        bstack1llll1l1l11l_opy_ = response.get(bstack111l1ll_opy_ (u"ࠣࡶ࡬ࡱࡪࡵࡵࡵࡗࡵࡰࠧ⃃"))
        if bstack1llll1ll1l1l_opy_:
            bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠤࡵࡩࡸࡻ࡬ࡵࡗࡵࡰࠧ⃄")] = bstack1llll1ll1l1l_opy_.split(bstack11l1ll1l1ll_opy_ + bstack111l1ll_opy_ (u"ࠥ࠳ࠧ⃅"))[1] if bstack11l1ll1l1ll_opy_ + bstack111l1ll_opy_ (u"ࠦ࠴ࠨ⃆") in bstack1llll1ll1l1l_opy_ else bstack1llll1ll1l1l_opy_
        else:
            bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠧࡸࡥࡴࡷ࡯ࡸ࡚ࡸ࡬ࠣ⃇")] = None
        if bstack1llll1l1l11l_opy_:
            bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠨࡴࡪ࡯ࡨࡳࡺࡺࡕࡳ࡮ࠥ⃈")] = bstack1llll1l1l11l_opy_.split(bstack11l1ll1l1ll_opy_ + bstack111l1ll_opy_ (u"ࠢ࠰ࠤ⃉"))[1] if bstack11l1ll1l1ll_opy_ + bstack111l1ll_opy_ (u"ࠣ࠱ࠥ⃊") in bstack1llll1l1l11l_opy_ else bstack1llll1l1l11l_opy_
        else:
            bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠤࡷ࡭ࡲ࡫࡯ࡶࡶࡘࡶࡱࠨ⃋")] = None
        if (
            response.get(bstack111l1ll_opy_ (u"ࠥࡸ࡮ࡳࡥࡰࡷࡷࠦ⃌")) is None or
            response.get(bstack111l1ll_opy_ (u"ࠦࡹ࡯࡭ࡦࡱࡸࡸࡎࡴࡴࡦࡴࡹࡥࡱࠨ⃍")) is None or
            response.get(bstack111l1ll_opy_ (u"ࠧࡺࡩ࡮ࡧࡲࡹࡹ࡛ࡲ࡭ࠤ⃎")) is None or
            response.get(bstack111l1ll_opy_ (u"ࠨࡲࡦࡵࡸࡰࡹ࡛ࡲ࡭ࠤ⃏")) is None
        ):
            self.logger.debug(bstack111l1ll_opy_ (u"ࠢ࡜ࡲࡵࡳࡨ࡫ࡳࡴࡡࡶࡴࡱ࡯ࡴࡠࡶࡨࡷࡹࡹ࡟ࡳࡧࡶࡴࡴࡴࡳࡦ࡟ࠣࡖࡪࡩࡥࡪࡸࡨࡨࠥࡴࡵ࡭࡮ࠣࡺࡦࡲࡵࡦࠪࡶ࠭ࠥ࡬࡯ࡳࠢࡶࡳࡲ࡫ࠠࡢࡶࡷࡶ࡮ࡨࡵࡵࡧࡶࠤ࡮ࡴࠠࡴࡲ࡯࡭ࡹࠦࡴࡦࡵࡷࡷࠥࡇࡐࡊࠢࡵࡩࡸࡶ࡯࡯ࡵࡨࠦ⃐"))
        return bstack11l1ll1lll_opy_
    def bstack111l111llll_opy_(self):
        if not self.bstack1llll1l11ll1_opy_:
            self.logger.error(bstack111l1ll_opy_ (u"ࠣ࡝ࡪࡩࡹࡕࡲࡥࡧࡵࡩࡩ࡚ࡥࡴࡶࡉ࡭ࡱ࡫ࡳ࡞ࠢࡑࡳࠥࡸࡥࡲࡷࡨࡷࡹࠦࡤࡢࡶࡤࠤࡦࡼࡡࡪ࡮ࡤࡦࡱ࡫ࠠࡵࡱࠣࡪࡪࡺࡣࡩࠢࡲࡶࡩ࡫ࡲࡦࡦࠣࡸࡪࡹࡴࠡࡨ࡬ࡰࡪࡹ࠮ࠣ⃑"))
            return None
        bstack1llll1ll1111_opy_ = None
        test_files = []
        bstack1llll1ll11ll_opy_ = int(time.time() * 1000) # bstack1llll1l1lll1_opy_ sec
        bstack1llll1ll1l11_opy_ = int(self.bstack1llll1l11ll1_opy_.get(bstack111l1ll_opy_ (u"ࠤࡷ࡭ࡲ࡫࡯ࡶࡶࡌࡲࡹ࡫ࡲࡷࡣ࡯⃒ࠦ"), self.bstack1llll1l1l111_opy_))
        bstack1llll1l1l1ll_opy_ = int(self.bstack1llll1l11ll1_opy_.get(bstack111l1ll_opy_ (u"ࠥࡸ࡮ࡳࡥࡰࡷࡷ⃓ࠦ"), self.bstack1llll1ll111l_opy_)) * 1000
        bstack1llll1l1l11l_opy_ = self.bstack1llll1l11ll1_opy_.get(bstack111l1ll_opy_ (u"ࠦࡹ࡯࡭ࡦࡱࡸࡸ࡚ࡸ࡬ࠣ⃔"), None)
        bstack1llll1ll1l1l_opy_ = self.bstack1llll1l11ll1_opy_.get(bstack111l1ll_opy_ (u"ࠧࡸࡥࡴࡷ࡯ࡸ࡚ࡸ࡬ࠣ⃕"), None)
        if bstack1llll1ll1l1l_opy_ is None and bstack1llll1l1l11l_opy_ is None:
            return None
        try:
            while bstack1llll1ll1l1l_opy_ and (time.time() * 1000 - bstack1llll1ll11ll_opy_) < bstack1llll1l1l1ll_opy_:
                response = bstack11ll1111ll1_opy_.bstack1lllll1l1111_opy_(bstack1llll1ll1l1l_opy_, {})
                if response and response.get(bstack111l1ll_opy_ (u"ࠨࡴࡦࡵࡷࡷࠧ⃖")):
                    bstack1llll1ll1111_opy_ = response.get(bstack111l1ll_opy_ (u"ࠢࡵࡧࡶࡸࡸࠨ⃗"))
                self.bstack1llll1l1llll_opy_ += 1
                if bstack1llll1ll1111_opy_:
                    break
                time.sleep(bstack1llll1ll1l11_opy_)
                self.logger.debug(bstack111l1ll_opy_ (u"ࠣ࡝ࡪࡩࡹࡕࡲࡥࡧࡵࡩࡩ࡚ࡥࡴࡶࡉ࡭ࡱ࡫ࡳ࡞ࠢࡉࡩࡹࡩࡨࡪࡰࡪࠤࡴࡸࡤࡦࡴࡨࡨࠥࡺࡥࡴࡶࡶࠤ࡫ࡸ࡯࡮ࠢࡵࡩࡸࡻ࡬ࡵࠢࡘࡖࡑࠦࡡࡧࡶࡨࡶࠥࡽࡡࡪࡶ࡬ࡲ࡬ࠦࡦࡰࡴࠣࡿࢂࠦࡳࡦࡥࡲࡲࡩࡹ࠮⃘ࠣ").format(bstack1llll1ll1l11_opy_))
            if bstack1llll1l1l11l_opy_ and not bstack1llll1ll1111_opy_:
                self.logger.debug(bstack111l1ll_opy_ (u"ࠤ࡞࡫ࡪࡺࡏࡳࡦࡨࡶࡪࡪࡔࡦࡵࡷࡊ࡮ࡲࡥࡴ࡟ࠣࡊࡪࡺࡣࡩ࡫ࡱ࡫ࠥࡵࡲࡥࡧࡵࡩࡩࠦࡴࡦࡵࡷࡷࠥ࡬ࡲࡰ࡯ࠣࡸ࡮ࡳࡥࡰࡷࡷࠤ࡚ࡘࡌ⃙ࠣ"))
                response = bstack11ll1111ll1_opy_.bstack1lllll1l1111_opy_(bstack1llll1l1l11l_opy_, {})
                if response and response.get(bstack111l1ll_opy_ (u"ࠥࡸࡪࡹࡴࡴࠤ⃚")):
                    bstack1llll1ll1111_opy_ = response.get(bstack111l1ll_opy_ (u"ࠦࡹ࡫ࡳࡵࡵࠥ⃛"))
            if bstack1llll1ll1111_opy_ and len(bstack1llll1ll1111_opy_) > 0:
                for bstack111ll11l11_opy_ in bstack1llll1ll1111_opy_:
                    file_path = bstack111ll11l11_opy_.get(bstack111l1ll_opy_ (u"ࠧ࡬ࡩ࡭ࡧࡓࡥࡹ࡮ࠢ⃜"))
                    if file_path:
                        test_files.append(file_path)
            if not bstack1llll1ll1111_opy_:
                return None
            self.logger.debug(bstack111l1ll_opy_ (u"ࠨ࡛ࡨࡧࡷࡓࡷࡪࡥࡳࡧࡧࡘࡪࡹࡴࡇ࡫࡯ࡩࡸࡣࠠࡐࡴࡧࡩࡷ࡫ࡤࠡࡶࡨࡷࡹࠦࡦࡪ࡮ࡨࡷࠥࡸࡥࡤࡧ࡬ࡺࡪࡪ࠺ࠡࡽࢀࠦ⃝").format(test_files))
            return test_files
        except Exception as e:
            self.logger.error(bstack111l1ll_opy_ (u"ࠢ࡜ࡩࡨࡸࡔࡸࡤࡦࡴࡨࡨ࡙࡫ࡳࡵࡈ࡬ࡰࡪࡹ࡝ࠡࡇࡻࡧࡪࡶࡴࡪࡱࡱࠤ࡮ࡴࠠࡧࡧࡷࡧ࡭࡯࡮ࡨࠢࡲࡶࡩ࡫ࡲࡦࡦࠣࡸࡪࡹࡴࠡࡨ࡬ࡰࡪࡹ࠺ࠡࡽࢀࠦ⃞").format(e))
            return None
    def bstack111l11ll1l1_opy_(self):
        bstack111l1ll_opy_ (u"ࠣࠤࠥࠎࠥࠦࠠࠡࠢࠣࠤࠥࡘࡥࡵࡷࡵࡲࡸࠦࡴࡩࡧࠣࡧࡴࡻ࡮ࡵࠢࡲࡪࠥࡹࡰ࡭࡫ࡷࠤࡹ࡫ࡳࡵࡵࠣࡅࡕࡏࠠࡤࡣ࡯ࡰࡸࠦ࡭ࡢࡦࡨ࠲ࠏࠦࠠࠡࠢࠣࠤࠥࠦࠢࠣࠤ⃟")
        return self.bstack1llll1l1llll_opy_