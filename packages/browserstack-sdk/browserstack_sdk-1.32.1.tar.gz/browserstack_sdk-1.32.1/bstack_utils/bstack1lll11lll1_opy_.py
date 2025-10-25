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
import tempfile
import math
from bstack_utils import bstack1lllll11l1_opy_
from bstack_utils.constants import bstack1lllll1lll_opy_, bstack11l1ll11ll1_opy_
from bstack_utils.helper import bstack111lll11ll1_opy_, get_host_info
from bstack_utils.bstack11ll1111lll_opy_ import bstack11ll1111ll1_opy_
import json
import re
import sys
bstack111l111l11l_opy_ = bstack111l1ll_opy_ (u"ࠨࡲࡦࡶࡵࡽ࡙࡫ࡳࡵࡵࡒࡲࡋࡧࡩ࡭ࡷࡵࡩࠧṧ")
bstack1111ll11l11_opy_ = bstack111l1ll_opy_ (u"ࠢࡢࡤࡲࡶࡹࡈࡵࡪ࡮ࡧࡓࡳࡌࡡࡪ࡮ࡸࡶࡪࠨṨ")
bstack1111llllll1_opy_ = bstack111l1ll_opy_ (u"ࠣࡴࡸࡲࡕࡸࡥࡷ࡫ࡲࡹࡸࡲࡹࡇࡣ࡬ࡰࡪࡪࡆࡪࡴࡶࡸࠧṩ")
bstack111l111l111_opy_ = bstack111l1ll_opy_ (u"ࠤࡵࡩࡷࡻ࡮ࡑࡴࡨࡺ࡮ࡵࡵࡴ࡮ࡼࡊࡦ࡯࡬ࡦࡦࠥṪ")
bstack1111l1ll11l_opy_ = bstack111l1ll_opy_ (u"ࠥࡷࡰ࡯ࡰࡇ࡮ࡤ࡯ࡾࡧ࡮ࡥࡈࡤ࡭ࡱ࡫ࡤࠣṫ")
bstack1111l1l1lll_opy_ = bstack111l1ll_opy_ (u"ࠦࡷࡻ࡮ࡔ࡯ࡤࡶࡹ࡙ࡥ࡭ࡧࡦࡸ࡮ࡵ࡮ࠣṬ")
bstack1111ll11111_opy_ = {
    bstack111l111l11l_opy_,
    bstack1111ll11l11_opy_,
    bstack1111llllll1_opy_,
    bstack111l111l111_opy_,
    bstack1111l1ll11l_opy_,
    bstack1111l1l1lll_opy_
}
bstack1111ll1llll_opy_ = {bstack111l1ll_opy_ (u"ࠬࡶࡹࡵࡧࡶࡸࠬṭ")}
logger = bstack1lllll11l1_opy_.get_logger(__name__, bstack1lllll1lll_opy_)
class bstack1111ll1l1ll_opy_:
    def __init__(self):
        self.enabled = False
        self.name = None
    def enable(self, name):
        self.enabled = True
        self.name = name
    def disable(self):
        self.enabled = False
        self.name = None
    def bstack1111l1l11ll_opy_(self):
        return self.enabled
    def get_name(self):
        return self.name
class bstack1111lll1_opy_:
    _1lll1ll1l1l_opy_ = None
    def __init__(self, config):
        self.bstack1111l1l1ll1_opy_ = False
        self.bstack1111llll111_opy_ = False
        self.bstack1111lll1111_opy_ = False
        self.bstack111l1111l1l_opy_ = False
        self.bstack1111l1l1l11_opy_ = None
        self.bstack111l1111111_opy_ = bstack1111ll1l1ll_opy_()
        self.bstack1111lll1l11_opy_ = None
        opts = config.get(bstack111l1ll_opy_ (u"࠭ࡴࡦࡵࡷࡓࡷࡩࡨࡦࡵࡷࡶࡦࡺࡩࡰࡰࡒࡴࡹ࡯࡯࡯ࡵࠪṮ"), {})
        self.bstack1111lll111l_opy_ = config.get(bstack111l1ll_opy_ (u"ࠧࡴ࡯ࡤࡶࡹ࡙ࡥ࡭ࡧࡦࡸ࡮ࡵ࡮ࡇࡧࡤࡸࡺࡸࡥࡃࡴࡤࡲࡨ࡮ࡥࡴࡇࡑ࡚ࠬṯ"), bstack111l1ll_opy_ (u"ࠣࠤṰ"))
        self.bstack1111ll1lll1_opy_ = config.get(bstack111l1ll_opy_ (u"ࠩࡶࡱࡦࡸࡴࡔࡧ࡯ࡩࡨࡺࡩࡰࡰࡉࡩࡦࡺࡵࡳࡧࡅࡶࡦࡴࡣࡩࡧࡶࡇࡑࡏࠧṱ"), bstack111l1ll_opy_ (u"ࠥࠦṲ"))
        bstack1111lllll1l_opy_ = opts.get(bstack1111l1l1lll_opy_, {})
        bstack1111ll1l111_opy_ = None
        if bstack111l1ll_opy_ (u"ࠫࡸࡵࡵࡳࡥࡨࠫṳ") in bstack1111lllll1l_opy_:
            bstack1111ll1l111_opy_ = bstack1111lllll1l_opy_[bstack111l1ll_opy_ (u"ࠬࡹ࡯ࡶࡴࡦࡩࠬṴ")]
            if bstack1111ll1l111_opy_ is None:
                bstack1111ll1l111_opy_ = []
        self.__111l111l1l1_opy_(
            bstack1111lllll1l_opy_.get(bstack111l1ll_opy_ (u"࠭ࡥ࡯ࡣࡥࡰࡪࡪࠧṵ"), False),
            bstack1111lllll1l_opy_.get(bstack111l1ll_opy_ (u"ࠧ࡮ࡱࡧࡩࠬṶ"), bstack111l1ll_opy_ (u"ࠨࡴࡨࡰࡪࡼࡡ࡯ࡶࡉ࡭ࡷࡹࡴࠨṷ")),
            bstack1111ll1l111_opy_
        )
        self.__111l1111l11_opy_(opts.get(bstack1111llllll1_opy_, False))
        self.__1111l1ll1ll_opy_(opts.get(bstack111l111l111_opy_, False))
        self.__1111lllllll_opy_(opts.get(bstack1111l1ll11l_opy_, False))
    @classmethod
    def bstack111l11l11_opy_(cls, config=None):
        if cls._1lll1ll1l1l_opy_ is None and config is not None:
            cls._1lll1ll1l1l_opy_ = bstack1111lll1_opy_(config)
        return cls._1lll1ll1l1l_opy_
    @staticmethod
    def bstack11ll11l111_opy_(config: dict) -> bool:
        bstack1111ll111ll_opy_ = config.get(bstack111l1ll_opy_ (u"ࠩࡷࡩࡸࡺࡏࡳࡥ࡫ࡩࡸࡺࡲࡢࡶ࡬ࡳࡳࡕࡰࡵ࡫ࡲࡲࡸ࠭Ṹ"), {}).get(bstack111l111l11l_opy_, {})
        return bstack1111ll111ll_opy_.get(bstack111l1ll_opy_ (u"ࠪࡩࡳࡧࡢ࡭ࡧࡧࠫṹ"), False)
    @staticmethod
    def bstack1ll111l1_opy_(config: dict) -> int:
        bstack1111ll111ll_opy_ = config.get(bstack111l1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡑࡵࡧ࡭࡫ࡳࡵࡴࡤࡸ࡮ࡵ࡮ࡐࡲࡷ࡭ࡴࡴࡳࠨṺ"), {}).get(bstack111l111l11l_opy_, {})
        retries = 0
        if bstack1111lll1_opy_.bstack11ll11l111_opy_(config):
            retries = bstack1111ll111ll_opy_.get(bstack111l1ll_opy_ (u"ࠬࡳࡡࡹࡔࡨࡸࡷ࡯ࡥࡴࠩṻ"), 1)
        return retries
    @staticmethod
    def bstack11ll11ll11_opy_(config: dict) -> dict:
        bstack111l11111l1_opy_ = config.get(bstack111l1ll_opy_ (u"࠭ࡴࡦࡵࡷࡓࡷࡩࡨࡦࡵࡷࡶࡦࡺࡩࡰࡰࡒࡴࡹ࡯࡯࡯ࡵࠪṼ"), {})
        return {
            key: value for key, value in bstack111l11111l1_opy_.items() if key in bstack1111ll11111_opy_
        }
    @staticmethod
    def bstack1111l1lll11_opy_():
        bstack111l1ll_opy_ (u"ࠢࠣࠤࠍࠤࠥࠦࠠࠡࠢࠣࠤࡈ࡮ࡥࡤ࡭ࠣ࡭࡫ࠦࡴࡩࡧࠣࡥࡧࡵࡲࡵࠢࡥࡹ࡮ࡲࡤࠡࡨ࡬ࡰࡪࠦࡥࡹ࡫ࡶࡸࡸ࠴ࠊࠡࠢࠣࠤࠥࠦࠠࠡࠤࠥࠦṽ")
        return os.path.exists(os.path.join(tempfile.gettempdir(), bstack111l1ll_opy_ (u"ࠣࡣࡥࡳࡷࡺ࡟ࡣࡷ࡬ࡰࡩࡥࡻࡾࠤṾ").format(os.getenv(bstack111l1ll_opy_ (u"ࠤࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡎࡕࡃࡡࡘ࡙ࡎࡊࠢṿ")))))
    @staticmethod
    def bstack1111lllll11_opy_(test_name: str):
        bstack111l1ll_opy_ (u"ࠥࠦࠧࠐࠠࠡࠢࠣࠤࠥࠦࠠࡄࡪࡨࡧࡰࠦࡩࡧࠢࡷ࡬ࡪࠦࡡࡣࡱࡵࡸࠥࡨࡵࡪ࡮ࡧࠤ࡫࡯࡬ࡦࠢࡨࡼ࡮ࡹࡴࡴ࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤࠧࠨࠢẀ")
        bstack1111l1lll1l_opy_ = os.path.join(tempfile.gettempdir(), bstack111l1ll_opy_ (u"ࠦ࡫ࡧࡩ࡭ࡧࡧࡣࡹ࡫ࡳࡵࡵࡢࡿࢂ࠴ࡴࡹࡶࠥẁ").format(os.getenv(bstack111l1ll_opy_ (u"ࠧࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡊࡘࡆࡤ࡛ࡕࡊࡆࠥẂ"))))
        with open(bstack1111l1lll1l_opy_, bstack111l1ll_opy_ (u"࠭ࡡࠨẃ")) as file:
            file.write(bstack111l1ll_opy_ (u"ࠢࡼࡿ࡟ࡲࠧẄ").format(test_name))
    @staticmethod
    def bstack1111lll1l1l_opy_(framework: str) -> bool:
       return framework.lower() in bstack1111ll1llll_opy_
    @staticmethod
    def bstack11l1l111l11_opy_(config: dict) -> bool:
        bstack1111l1lllll_opy_ = config.get(bstack111l1ll_opy_ (u"ࠨࡶࡨࡷࡹࡕࡲࡤࡪࡨࡷࡹࡸࡡࡵ࡫ࡲࡲࡔࡶࡴࡪࡱࡱࡷࠬẅ"), {}).get(bstack1111ll11l11_opy_, {})
        return bstack1111l1lllll_opy_.get(bstack111l1ll_opy_ (u"ࠩࡨࡲࡦࡨ࡬ࡦࡦࠪẆ"), False)
    @staticmethod
    def bstack11l11llll1l_opy_(config: dict, bstack11l1l111lll_opy_: int = 0) -> int:
        bstack111l1ll_opy_ (u"ࠥࠦࠧࠐࠠࠡࠢࠣࠤࠥࠦࠠࡈࡧࡷࠤࡹ࡮ࡥࠡࡨࡤ࡭ࡱࡻࡲࡦࠢࡷ࡬ࡷ࡫ࡳࡩࡱ࡯ࡨ࠱ࠦࡷࡩ࡫ࡦ࡬ࠥࡩࡡ࡯ࠢࡥࡩࠥࡧ࡮ࠡࡣࡥࡷࡴࡲࡵࡵࡧࠣࡲࡺࡳࡢࡦࡴࠣࡳࡷࠦࡡࠡࡲࡨࡶࡨ࡫࡮ࡵࡣࡪࡩ࠳ࠐࠠࠡࠢࠣࠤࠥࠦࠠࡂࡴࡪࡷ࠿ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࡨࡵ࡮ࡧ࡫ࡪࠤ࠭ࡪࡩࡤࡶࠬ࠾࡚ࠥࡨࡦࠢࡦࡳࡳ࡬ࡩࡨࡷࡵࡥࡹ࡯࡯࡯ࠢࡧ࡭ࡨࡺࡩࡰࡰࡤࡶࡾ࠴ࠊࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࡺ࡯ࡵࡣ࡯ࡣࡹ࡫ࡳࡵࡵࠣࠬ࡮ࡴࡴࠪ࠼ࠣࡘ࡭࡫ࠠࡵࡱࡷࡥࡱࠦ࡮ࡶ࡯ࡥࡩࡷࠦ࡯ࡧࠢࡷࡩࡸࡺࡳࠡࠪࡵࡩࡶࡻࡩࡳࡧࡧࠤ࡫ࡵࡲࠡࡲࡨࡶࡨ࡫࡮ࡵࡣࡪࡩ࠲ࡨࡡࡴࡧࡧࠤࡹ࡮ࡲࡦࡵ࡫ࡳࡱࡪࡳࠪ࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤࡗ࡫ࡴࡶࡴࡱࡷ࠿ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤ࡮ࡴࡴ࠻ࠢࡗ࡬ࡪࠦࡦࡢ࡫࡯ࡹࡷ࡫ࠠࡵࡪࡵࡩࡸ࡮࡯࡭ࡦ࠱ࠎࠥࠦࠠࠡࠢࠣࠤࠥࠨࠢࠣẇ")
        bstack1111l1lllll_opy_ = config.get(bstack111l1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡑࡵࡧ࡭࡫ࡳࡵࡴࡤࡸ࡮ࡵ࡮ࡐࡲࡷ࡭ࡴࡴࡳࠨẈ"), {}).get(bstack111l1ll_opy_ (u"ࠬࡧࡢࡰࡴࡷࡆࡺ࡯࡬ࡥࡑࡱࡊࡦ࡯࡬ࡶࡴࡨࠫẉ"), {})
        bstack1111llll1l1_opy_ = 0
        bstack1111l1l1l1l_opy_ = 0
        if bstack1111lll1_opy_.bstack11l1l111l11_opy_(config):
            bstack1111l1l1l1l_opy_ = bstack1111l1lllll_opy_.get(bstack111l1ll_opy_ (u"࠭࡭ࡢࡺࡉࡥ࡮ࡲࡵࡳࡧࡶࠫẊ"), 5)
            if isinstance(bstack1111l1l1l1l_opy_, str) and bstack1111l1l1l1l_opy_.endswith(bstack111l1ll_opy_ (u"ࠧࠦࠩẋ")):
                try:
                    percentage = int(bstack1111l1l1l1l_opy_.strip(bstack111l1ll_opy_ (u"ࠨࠧࠪẌ")))
                    if bstack11l1l111lll_opy_ > 0:
                        bstack1111llll1l1_opy_ = math.ceil((percentage * bstack11l1l111lll_opy_) / 100)
                    else:
                        raise ValueError(bstack111l1ll_opy_ (u"ࠤࡗࡳࡹࡧ࡬ࠡࡶࡨࡷࡹࡹࠠ࡮ࡷࡶࡸࠥࡨࡥࠡࡲࡵࡳࡻ࡯ࡤࡦࡦࠣࡪࡴࡸࠠࡱࡧࡵࡧࡪࡴࡴࡢࡩࡨ࠱ࡧࡧࡳࡦࡦࠣࡸ࡭ࡸࡥࡴࡪࡲࡰࡩࡹ࠮ࠣẍ"))
                except ValueError as e:
                    raise ValueError(bstack111l1ll_opy_ (u"ࠥࡍࡳࡼࡡ࡭࡫ࡧࠤࡵ࡫ࡲࡤࡧࡱࡸࡦ࡭ࡥࠡࡸࡤࡰࡺ࡫ࠠࡧࡱࡵࠤࡲࡧࡸࡇࡣ࡬ࡰࡺࡸࡥࡴ࠼ࠣࡿࢂࠨẎ").format(bstack1111l1l1l1l_opy_)) from e
            else:
                bstack1111llll1l1_opy_ = int(bstack1111l1l1l1l_opy_)
        logger.info(bstack111l1ll_opy_ (u"ࠦࡒࡧࡸࠡࡨࡤ࡭ࡱࡻࡲࡦࡵࠣࡸ࡭ࡸࡥࡴࡪࡲࡰࡩࠦࡳࡦࡶࠣࡸࡴࡀࠠࡼࡿࠣࠬ࡫ࡸ࡯࡮ࠢࡦࡳࡳ࡬ࡩࡨ࠼ࠣࡿࢂ࠯ࠢẏ").format(bstack1111llll1l1_opy_, bstack1111l1l1l1l_opy_))
        return bstack1111llll1l1_opy_
    def bstack1111ll11lll_opy_(self):
        return self.bstack111l1111l1l_opy_
    def bstack111l1111ll1_opy_(self):
        return self.bstack1111l1l1l11_opy_
    def bstack1111ll1ll11_opy_(self):
        return self.bstack1111lll1l11_opy_
    def __111l111l1l1_opy_(self, enabled, mode, source=None):
        try:
            self.bstack111l1111l1l_opy_ = bool(enabled)
            if mode not in [bstack111l1ll_opy_ (u"ࠬࡸࡥ࡭ࡧࡹࡥࡳࡺࡆࡪࡴࡶࡸࠬẐ"), bstack111l1ll_opy_ (u"࠭ࡲࡦ࡮ࡨࡺࡦࡴࡴࡐࡰ࡯ࡽࠬẑ")]:
                logger.warning(bstack111l1ll_opy_ (u"ࠢࡊࡰࡹࡥࡱ࡯ࡤࠡࡵࡰࡥࡷࡺࠠࡴࡧ࡯ࡩࡨࡺࡩࡰࡰࠣࡱࡴࡪࡥࠡࠩࡾࢁࠬࠦࡰࡳࡱࡹ࡭ࡩ࡫ࡤ࠯ࠢࡇࡩ࡫ࡧࡵ࡭ࡶ࡬ࡲ࡬ࠦࡴࡰࠢࠪࡶࡪࡲࡥࡷࡣࡱࡸࡋ࡯ࡲࡴࡶࠪ࠲ࠧẒ").format(mode))
                mode = bstack111l1ll_opy_ (u"ࠨࡴࡨࡰࡪࡼࡡ࡯ࡶࡉ࡭ࡷࡹࡴࠨẓ")
            self.bstack1111l1l1l11_opy_ = mode
            if source is None:
                self.bstack1111lll1l11_opy_ = None
            elif isinstance(source, list):
                self.bstack1111lll1l11_opy_ = source
            elif isinstance(source, str) and source.endswith(bstack111l1ll_opy_ (u"ࠩ࠱࡮ࡸࡵ࡮ࠨẔ")):
                self.bstack1111lll1l11_opy_ = self._1111l1ll1l1_opy_(source)
            self.__1111lll1lll_opy_()
        except Exception as e:
            logger.error(bstack111l1ll_opy_ (u"ࠥࡊࡦ࡯࡬ࡦࡦࠣࡸࡴࠦࡳࡦࡶࠣࡷࡲࡧࡲࡵࠢࡶࡩࡱ࡫ࡣࡵ࡫ࡲࡲࠥࡩ࡯࡯ࡨ࡬࡫ࡺࡸࡡࡵ࡫ࡲࡲࠥ࠳ࠠࡦࡰࡤࡦࡱ࡫ࡤ࠻ࠢࡾࢁ࠱ࠦ࡭ࡰࡦࡨ࠾ࠥࢁࡽ࠭ࠢࡶࡳࡺࡸࡣࡦ࠼ࠣࡿࢂ࠴ࠠࡆࡴࡵࡳࡷࡀࠠࡼࡿࠥẕ").format(enabled, mode, source, e))
    def bstack1111lll11l1_opy_(self):
        return self.bstack1111l1l1ll1_opy_
    def __111l1111l11_opy_(self, value):
        self.bstack1111l1l1ll1_opy_ = bool(value)
        self.__1111lll1lll_opy_()
    def bstack1111l1llll1_opy_(self):
        return self.bstack1111llll111_opy_
    def __1111l1ll1ll_opy_(self, value):
        self.bstack1111llll111_opy_ = bool(value)
        self.__1111lll1lll_opy_()
    def bstack111l11111ll_opy_(self):
        return self.bstack1111lll1111_opy_
    def __1111lllllll_opy_(self, value):
        self.bstack1111lll1111_opy_ = bool(value)
        self.__1111lll1lll_opy_()
    def __1111lll1lll_opy_(self):
        if self.bstack111l1111l1l_opy_:
            self.bstack1111l1l1ll1_opy_ = False
            self.bstack1111llll111_opy_ = False
            self.bstack1111lll1111_opy_ = False
            self.bstack111l1111111_opy_.enable(bstack1111l1l1lll_opy_)
        elif self.bstack1111l1l1ll1_opy_:
            self.bstack1111llll111_opy_ = False
            self.bstack1111lll1111_opy_ = False
            self.bstack111l1111l1l_opy_ = False
            self.bstack111l1111111_opy_.enable(bstack1111llllll1_opy_)
        elif self.bstack1111llll111_opy_:
            self.bstack1111l1l1ll1_opy_ = False
            self.bstack1111lll1111_opy_ = False
            self.bstack111l1111l1l_opy_ = False
            self.bstack111l1111111_opy_.enable(bstack111l111l111_opy_)
        elif self.bstack1111lll1111_opy_:
            self.bstack1111l1l1ll1_opy_ = False
            self.bstack1111llll111_opy_ = False
            self.bstack111l1111l1l_opy_ = False
            self.bstack111l1111111_opy_.enable(bstack1111l1ll11l_opy_)
        else:
            self.bstack111l1111111_opy_.disable()
    def bstack11ll111lll_opy_(self):
        return self.bstack111l1111111_opy_.bstack1111l1l11ll_opy_()
    def bstack11111111_opy_(self):
        if self.bstack111l1111111_opy_.bstack1111l1l11ll_opy_():
            return self.bstack111l1111111_opy_.get_name()
        return None
    def _1111l1ll1l1_opy_(self, bstack1111llll11l_opy_):
        bstack111l1ll_opy_ (u"ࠦࠧࠨࠊࠡࠢࠣࠤࠥࠦࠠࠡࡒࡤࡶࡸ࡫ࠠࡋࡕࡒࡒࠥࡹ࡯ࡶࡴࡦࡩࠥࡩ࡯࡯ࡨ࡬࡫ࡺࡸࡡࡵ࡫ࡲࡲࠥ࡬ࡩ࡭ࡧࠣࡥࡳࡪࠠࡧࡱࡵࡱࡦࡺࠠࡪࡶࠣࡪࡴࡸࠠࡴ࡯ࡤࡶࡹࠦࡳࡦ࡮ࡨࡧࡹ࡯࡯࡯࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤࡆࡸࡧࡴ࠼ࠍࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࡵࡲࡹࡷࡩࡥࡠࡨ࡬ࡰࡪࡥࡰࡢࡶ࡫ࠤ࠭ࡹࡴࡳࠫ࠽ࠤࡕࡧࡴࡩࠢࡷࡳࠥࡺࡨࡦࠢࡍࡗࡔࡔࠠࡤࡱࡱࡪ࡮࡭ࡵࡳࡣࡷ࡭ࡴࡴࠠࡧ࡫࡯ࡩࠏࠦࠠࠡࠢࠣࠤࠥࠦࡒࡦࡶࡸࡶࡳࡹ࠺ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦ࡬ࡪࡵࡷ࠾ࠥࡌ࡯ࡳ࡯ࡤࡸࡹ࡫ࡤࠡ࡮࡬ࡷࡹࠦ࡯ࡧࠢࡵࡩࡵࡵࡳࡪࡶࡲࡶࡾࠦࡣࡰࡰࡩ࡭࡬ࡻࡲࡢࡶ࡬ࡳࡳࡹࠊࠡࠢࠣࠤࠥࠦࠠࠡࠤࠥࠦẖ")
        if not os.path.isfile(bstack1111llll11l_opy_):
            logger.error(bstack111l1ll_opy_ (u"࡙ࠧ࡯ࡶࡴࡦࡩࠥ࡬ࡩ࡭ࡧࠣࠫࢀࢃࠧࠡࡦࡲࡩࡸࠦ࡮ࡰࡶࠣࡩࡽ࡯ࡳࡵ࠰ࠥẗ").format(bstack1111llll11l_opy_))
            return []
        data = None
        try:
            with open(bstack1111llll11l_opy_, bstack111l1ll_opy_ (u"ࠨࡲࠣẘ")) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(bstack111l1ll_opy_ (u"ࠢࡆࡴࡵࡳࡷࠦࡰࡢࡴࡶ࡭ࡳ࡭ࠠࡋࡕࡒࡒࠥ࡬ࡲࡰ࡯ࠣࡷࡴࡻࡲࡤࡧࠣࡪ࡮ࡲࡥࠡࠩࡾࢁࠬࡀࠠࡼࡿࠥẙ").format(bstack1111llll11l_opy_, e))
            return []
        _1111ll111l1_opy_ = None
        _111l111111l_opy_ = None
        def _1111ll1111l_opy_():
            bstack1111lll11ll_opy_ = {}
            bstack1111ll11ll1_opy_ = {}
            try:
                if self.bstack1111lll111l_opy_.startswith(bstack111l1ll_opy_ (u"ࠨࡽࠪẚ")) and self.bstack1111lll111l_opy_.endswith(bstack111l1ll_opy_ (u"ࠩࢀࠫẛ")):
                    bstack1111lll11ll_opy_ = json.loads(self.bstack1111lll111l_opy_)
                else:
                    bstack1111lll11ll_opy_ = dict(item.split(bstack111l1ll_opy_ (u"ࠪ࠾ࠬẜ")) for item in self.bstack1111lll111l_opy_.split(bstack111l1ll_opy_ (u"ࠫ࠱࠭ẝ")) if bstack111l1ll_opy_ (u"ࠬࡀࠧẞ") in item) if self.bstack1111lll111l_opy_ else {}
                if self.bstack1111ll1lll1_opy_.startswith(bstack111l1ll_opy_ (u"࠭ࡻࠨẟ")) and self.bstack1111ll1lll1_opy_.endswith(bstack111l1ll_opy_ (u"ࠧࡾࠩẠ")):
                    bstack1111ll11ll1_opy_ = json.loads(self.bstack1111ll1lll1_opy_)
                else:
                    bstack1111ll11ll1_opy_ = dict(item.split(bstack111l1ll_opy_ (u"ࠨ࠼ࠪạ")) for item in self.bstack1111ll1lll1_opy_.split(bstack111l1ll_opy_ (u"ࠩ࠯ࠫẢ")) if bstack111l1ll_opy_ (u"ࠪ࠾ࠬả") in item) if self.bstack1111ll1lll1_opy_ else {}
            except json.JSONDecodeError as e:
                logger.error(bstack111l1ll_opy_ (u"ࠦࡊࡸࡲࡰࡴࠣࡴࡦࡸࡳࡪࡰࡪࠤ࡫࡫ࡡࡵࡷࡵࡩࠥࡨࡲࡢࡰࡦ࡬ࠥࡳࡡࡱࡲ࡬ࡲ࡬ࡹ࠺ࠡࡽࢀࠦẤ").format(e))
            logger.debug(bstack111l1ll_opy_ (u"ࠧࡌࡥࡢࡶࡸࡶࡪࠦࡢࡳࡣࡱࡧ࡭ࠦ࡭ࡢࡲࡳ࡭ࡳ࡭ࡳࠡࡨࡵࡳࡲࠦࡥ࡯ࡸ࠽ࠤࢀࢃࠬࠡࡅࡏࡍ࠿ࠦࡻࡾࠤấ").format(bstack1111lll11ll_opy_, bstack1111ll11ll1_opy_))
            return bstack1111lll11ll_opy_, bstack1111ll11ll1_opy_
        if _1111ll111l1_opy_ is None or _111l111111l_opy_ is None:
            _1111ll111l1_opy_, _111l111111l_opy_ = _1111ll1111l_opy_()
        def bstack1111ll11l1l_opy_(name, bstack1111l1ll111_opy_):
            if name in _111l111111l_opy_:
                return _111l111111l_opy_[name]
            if name in _1111ll111l1_opy_:
                return _1111ll111l1_opy_[name]
            if bstack1111l1ll111_opy_.get(bstack111l1ll_opy_ (u"࠭ࡦࡦࡣࡷࡹࡷ࡫ࡂࡳࡣࡱࡧ࡭࠭Ầ")):
                return bstack1111l1ll111_opy_[bstack111l1ll_opy_ (u"ࠧࡧࡧࡤࡸࡺࡸࡥࡃࡴࡤࡲࡨ࡮ࠧầ")]
            return None
        if isinstance(data, dict):
            bstack1111ll1l11l_opy_ = []
            bstack1111ll1ll1l_opy_ = re.compile(bstack111l1ll_opy_ (u"ࡳࠩࡡ࡟ࡆ࠳࡚࠱࠯࠼ࡣࡢ࠱ࠤࠨẨ"))
            for name, bstack1111l1ll111_opy_ in data.items():
                if not isinstance(bstack1111l1ll111_opy_, dict):
                    continue
                if not bstack1111l1ll111_opy_.get(bstack111l1ll_opy_ (u"ࠩࡸࡶࡱ࠭ẩ")):
                    logger.warning(bstack111l1ll_opy_ (u"ࠥࡖࡪࡶ࡯ࡴ࡫ࡷࡳࡷࡿࠠࡖࡔࡏࠤ࡮ࡹࠠ࡮࡫ࡶࡷ࡮ࡴࡧࠡࡨࡲࡶࠥࡹ࡯ࡶࡴࡦࡩࠥ࠭ࡻࡾࠩ࠽ࠤࢀࢃࠢẪ").format(name, bstack1111l1ll111_opy_))
                    continue
                if not bstack1111ll1ll1l_opy_.match(name):
                    logger.warning(bstack111l1ll_opy_ (u"ࠦࡎࡴࡶࡢ࡮࡬ࡨࠥࡹ࡯ࡶࡴࡦࡩࠥ࡯ࡤࡦࡰࡷ࡭࡫࡯ࡥࡳࠢࡩࡳࡷࡳࡡࡵࠢࡩࡳࡷࠦࠧࡼࡿࠪ࠾ࠥࢁࡽࠣẫ").format(name, bstack1111l1ll111_opy_))
                    continue
                if len(name) > 30 or len(name) < 1:
                    logger.warning(bstack111l1ll_opy_ (u"࡙ࠧ࡯ࡶࡴࡦࡩࠥ࡯ࡤࡦࡰࡷ࡭࡫࡯ࡥࡳࠢࠪࡿࢂ࠭ࠠ࡮ࡷࡶࡸࠥ࡮ࡡࡷࡧࠣࡥࠥࡲࡥ࡯ࡩࡷ࡬ࠥࡨࡥࡵࡹࡨࡩࡳࠦ࠱ࠡࡣࡱࡨࠥ࠹࠰ࠡࡥ࡫ࡥࡷࡧࡣࡵࡧࡵࡷ࠳ࠨẬ").format(name))
                    continue
                bstack1111l1ll111_opy_ = bstack1111l1ll111_opy_.copy()
                bstack1111l1ll111_opy_[bstack111l1ll_opy_ (u"࠭࡮ࡢ࡯ࡨࠫậ")] = name
                bstack1111l1ll111_opy_[bstack111l1ll_opy_ (u"ࠧࡧࡧࡤࡸࡺࡸࡥࡃࡴࡤࡲࡨ࡮ࠧẮ")] = bstack1111ll11l1l_opy_(name, bstack1111l1ll111_opy_)
                if not bstack1111l1ll111_opy_.get(bstack111l1ll_opy_ (u"ࠨࡨࡨࡥࡹࡻࡲࡦࡄࡵࡥࡳࡩࡨࠨắ")):
                    logger.warning(bstack111l1ll_opy_ (u"ࠤࡉࡩࡦࡺࡵࡳࡧࠣࡦࡷࡧ࡮ࡤࡪࠣࡲࡴࡺࠠࡴࡲࡨࡧ࡮࡬ࡩࡦࡦࠣࡪࡴࡸࠠࡴࡱࡸࡶࡨ࡫ࠠࠨࡽࢀࠫ࠿ࠦࡻࡾࠤẰ").format(name, bstack1111l1ll111_opy_))
                    continue
                if bstack1111l1ll111_opy_.get(bstack111l1ll_opy_ (u"ࠪࡦࡦࡹࡥࡃࡴࡤࡲࡨ࡮ࠧằ")) and bstack1111l1ll111_opy_[bstack111l1ll_opy_ (u"ࠫࡧࡧࡳࡦࡄࡵࡥࡳࡩࡨࠨẲ")] == bstack1111l1ll111_opy_[bstack111l1ll_opy_ (u"ࠬ࡬ࡥࡢࡶࡸࡶࡪࡈࡲࡢࡰࡦ࡬ࠬẳ")]:
                    logger.warning(bstack111l1ll_opy_ (u"ࠨࡆࡦࡣࡷࡹࡷ࡫ࠠࡣࡴࡤࡲࡨ࡮ࠠࡢࡰࡧࠤࡧࡧࡳࡦࠢࡥࡶࡦࡴࡣࡩࠢࡦࡥࡳࡴ࡯ࡵࠢࡥࡩࠥࡺࡨࡦࠢࡶࡥࡲ࡫ࠠࡧࡱࡵࠤࡸࡵࡵࡳࡥࡨࠤࠬࢁࡽࠨ࠼ࠣࡿࢂࠨẴ").format(name, bstack1111l1ll111_opy_))
                    continue
                bstack1111ll1l11l_opy_.append(bstack1111l1ll111_opy_)
            return bstack1111ll1l11l_opy_
        return data
    def bstack111l111lll1_opy_(self):
        data = {
            bstack111l1ll_opy_ (u"ࠧࡳࡷࡱࡣࡸࡳࡡࡳࡶࡢࡷࡪࡲࡥࡤࡶ࡬ࡳࡳ࠭ẵ"): {
                bstack111l1ll_opy_ (u"ࠨࡧࡱࡥࡧࡲࡥࡥࠩẶ"): self.bstack1111ll11lll_opy_(),
                bstack111l1ll_opy_ (u"ࠩࡰࡳࡩ࡫ࠧặ"): self.bstack111l1111ll1_opy_(),
                bstack111l1ll_opy_ (u"ࠪࡷࡴࡻࡲࡤࡧࠪẸ"): self.bstack1111ll1ll11_opy_()
            }
        }
        return data
    def bstack1111lll1ll1_opy_(self, config):
        bstack111l1111lll_opy_ = {}
        bstack111l1111lll_opy_[bstack111l1ll_opy_ (u"ࠫࡷࡻ࡮ࡠࡵࡰࡥࡷࡺ࡟ࡴࡧ࡯ࡩࡨࡺࡩࡰࡰࠪẹ")] = {
            bstack111l1ll_opy_ (u"ࠬ࡫࡮ࡢࡤ࡯ࡩࡩ࠭Ẻ"): self.bstack1111ll11lll_opy_(),
            bstack111l1ll_opy_ (u"࠭࡭ࡰࡦࡨࠫẻ"): self.bstack111l1111ll1_opy_()
        }
        bstack111l1111lll_opy_[bstack111l1ll_opy_ (u"ࠧࡳࡧࡵࡹࡳࡥࡰࡳࡧࡹ࡭ࡴࡻࡳ࡭ࡻࡢࡪࡦ࡯࡬ࡦࡦࠪẼ")] = {
            bstack111l1ll_opy_ (u"ࠨࡧࡱࡥࡧࡲࡥࡥࠩẽ"): self.bstack1111l1llll1_opy_()
        }
        bstack111l1111lll_opy_[bstack111l1ll_opy_ (u"ࠩࡵࡹࡳࡥࡰࡳࡧࡹ࡭ࡴࡻࡳ࡭ࡻࡢࡪࡦ࡯࡬ࡦࡦࡢࡪ࡮ࡸࡳࡵࠩẾ")] = {
            bstack111l1ll_opy_ (u"ࠪࡩࡳࡧࡢ࡭ࡧࡧࠫế"): self.bstack1111lll11l1_opy_()
        }
        bstack111l1111lll_opy_[bstack111l1ll_opy_ (u"ࠫࡸࡱࡩࡱࡡࡩࡥ࡮ࡲࡩ࡯ࡩࡢࡥࡳࡪ࡟ࡧ࡮ࡤ࡯ࡾ࠭Ề")] = {
            bstack111l1ll_opy_ (u"ࠬ࡫࡮ࡢࡤ࡯ࡩࡩ࠭ề"): self.bstack111l11111ll_opy_()
        }
        if self.bstack11ll11l111_opy_(config):
            bstack111l1111lll_opy_[bstack111l1ll_opy_ (u"࠭ࡲࡦࡶࡵࡽࡤࡺࡥࡴࡶࡶࡣࡴࡴ࡟ࡧࡣ࡬ࡰࡺࡸࡥࠨỂ")] = {
                bstack111l1ll_opy_ (u"ࠧࡦࡰࡤࡦࡱ࡫ࡤࠨể"): True,
                bstack111l1ll_opy_ (u"ࠨ࡯ࡤࡼࡤࡸࡥࡵࡴ࡬ࡩࡸ࠭Ễ"): self.bstack1ll111l1_opy_(config)
            }
        if self.bstack11l1l111l11_opy_(config):
            bstack111l1111lll_opy_[bstack111l1ll_opy_ (u"ࠩࡤࡦࡴࡸࡴࡠࡤࡸ࡭ࡱࡪ࡟ࡰࡰࡢࡪࡦ࡯࡬ࡶࡴࡨࠫễ")] = {
                bstack111l1ll_opy_ (u"ࠪࡩࡳࡧࡢ࡭ࡧࡧࠫỆ"): True,
                bstack111l1ll_opy_ (u"ࠫࡲࡧࡸࡠࡨࡤ࡭ࡱࡻࡲࡦࡵࠪệ"): self.bstack11l11llll1l_opy_(config)
            }
        return bstack111l1111lll_opy_
    def bstack1l1l1lllll_opy_(self, config):
        bstack111l1ll_opy_ (u"ࠧࠨࠢࠋࠢࠣࠤࠥࠦࠠࠡࠢࡆࡳࡱࡲࡥࡤࡶࡶࠤࡧࡻࡩ࡭ࡦࠣࡨࡦࡺࡡࠡࡤࡼࠤࡲࡧ࡫ࡪࡰࡪࠤࡦࠦࡣࡢ࡮࡯ࠤࡹࡵࠠࡵࡪࡨࠤࡨࡵ࡬࡭ࡧࡦࡸ࠲ࡨࡵࡪ࡮ࡧ࠱ࡩࡧࡴࡢࠢࡨࡲࡩࡶ࡯ࡪࡰࡷ࠲ࠏࠦࠠࠡࠢࠣࠤࠥࠦࡁࡳࡩࡶ࠾ࠏࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࡦࡺ࡯࡬ࡥࡡࡸࡹ࡮ࡪࠠࠩࡵࡷࡶ࠮ࡀࠠࡕࡪࡨࠤ࡚࡛ࡉࡅࠢࡲࡪࠥࡺࡨࡦࠢࡥࡹ࡮ࡲࡤࠡࡶࡲࠤࡨࡵ࡬࡭ࡧࡦࡸࠥࡪࡡࡵࡣࠣࡪࡴࡸ࠮ࠋࠢࠣࠤࠥࠦࠠࠡࠢࡕࡩࡹࡻࡲ࡯ࡵ࠽ࠎࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࡧ࡭ࡨࡺ࠺ࠡࡔࡨࡷࡵࡵ࡮ࡴࡧࠣࡪࡷࡵ࡭ࠡࡶ࡫ࡩࠥࡩ࡯࡭࡮ࡨࡧࡹ࠳ࡢࡶ࡫࡯ࡨ࠲ࡪࡡࡵࡣࠣࡩࡳࡪࡰࡰ࡫ࡱࡸ࠱ࠦ࡯ࡳࠢࡑࡳࡳ࡫ࠠࡪࡨࠣࡪࡦ࡯࡬ࡦࡦ࠱ࠎࠥࠦࠠࠡࠢࠣࠤࠥࠨࠢࠣỈ")
        if not (config.get(bstack111l1ll_opy_ (u"࠭ࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࠩỉ"), None) in bstack11l1ll11ll1_opy_ and self.bstack1111ll11lll_opy_()):
            return None
        bstack1111ll1l1l1_opy_ = os.environ.get(bstack111l1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡖࡗࡌࡈࠬỊ"), None)
        logger.debug(bstack111l1ll_opy_ (u"ࠣ࡝ࡦࡳࡱࡲࡥࡤࡶࡅࡹ࡮ࡲࡤࡅࡣࡷࡥࡢࠦࡃࡰ࡮࡯ࡩࡨࡺࡩ࡯ࡩࠣࡦࡺ࡯࡬ࡥࠢࡧࡥࡹࡧࠠࡧࡱࡵࠤࡧࡻࡩ࡭ࡦ࡙࡚ࠣࡏࡄ࠻ࠢࡾࢁࠧị").format(bstack1111ll1l1l1_opy_))
        try:
            bstack11ll111ll11_opy_ = bstack111l1ll_opy_ (u"ࠤࡷࡩࡸࡺ࡯ࡳࡥ࡫ࡩࡸࡺࡲࡢࡶ࡬ࡳࡳ࠵ࡡࡱ࡫࠲ࡺ࠶࠵ࡢࡶ࡫࡯ࡨࡸ࠵ࡻࡾ࠱ࡦࡳࡱࡲࡥࡤࡶ࠰ࡦࡺ࡯࡬ࡥ࠯ࡧࡥࡹࡧࠢỌ").format(bstack1111ll1l1l1_opy_)
            payload = {
                bstack111l1ll_opy_ (u"ࠥࡴࡷࡵࡪࡦࡥࡷࡒࡦࡳࡥࠣọ"): config.get(bstack111l1ll_opy_ (u"ࠫࡵࡸ࡯࡫ࡧࡦࡸࡓࡧ࡭ࡦࠩỎ"), bstack111l1ll_opy_ (u"ࠬ࠭ỏ")),
                bstack111l1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡓࡧ࡭ࡦࠤỐ"): config.get(bstack111l1ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡔࡡ࡮ࡧࠪố"), os.path.basename(os.path.abspath(os.getcwd()))),
                bstack111l1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪࡒࡶࡰࡌࡨࡪࡴࡴࡪࡨ࡬ࡩࡷࠨỒ"): os.environ.get(bstack111l1ll_opy_ (u"ࠤࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡄࡘࡍࡑࡊ࡟ࡓࡗࡑࡣࡎࡊࡅࡏࡖࡌࡊࡎࡋࡒࠣồ"), bstack111l1ll_opy_ (u"ࠥࠦỔ")),
                bstack111l1ll_opy_ (u"ࠦࡳࡵࡤࡦࡋࡱࡨࡪࡾࠢổ"): int(os.environ.get(bstack111l1ll_opy_ (u"ࠧࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡓࡕࡄࡆࡡࡌࡒࡉࡋࡘࠣỖ")) or bstack111l1ll_opy_ (u"ࠨ࠰ࠣỗ")),
                bstack111l1ll_opy_ (u"ࠢࡵࡱࡷࡥࡱࡔ࡯ࡥࡧࡶࠦỘ"): int(os.environ.get(bstack111l1ll_opy_ (u"ࠣࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡕࡑࡗࡅࡑࡥࡎࡐࡆࡈࡣࡈࡕࡕࡏࡖࠥộ")) or bstack111l1ll_opy_ (u"ࠤ࠴ࠦỚ")),
                bstack111l1ll_opy_ (u"ࠥ࡬ࡴࡹࡴࡊࡰࡩࡳࠧớ"): get_host_info(),
            }
            logger.debug(bstack111l1ll_opy_ (u"ࠦࡠࡩ࡯࡭࡮ࡨࡧࡹࡈࡵࡪ࡮ࡧࡈࡦࡺࡡ࡞ࠢࡖࡩࡳࡪࡩ࡯ࡩࠣࡦࡺ࡯࡬ࡥࠢࡧࡥࡹࡧࠠࡱࡣࡼࡰࡴࡧࡤ࠻ࠢࡾࢁࠧỜ").format(payload))
            response = bstack11ll1111ll1_opy_.bstack1111llll1ll_opy_(bstack11ll111ll11_opy_, payload)
            if response:
                logger.debug(bstack111l1ll_opy_ (u"ࠧࡡࡣࡰ࡮࡯ࡩࡨࡺࡂࡶ࡫࡯ࡨࡉࡧࡴࡢ࡟ࠣࡆࡺ࡯࡬ࡥࠢࡧࡥࡹࡧࠠࡤࡱ࡯ࡰࡪࡩࡴࡪࡱࡱࠤࡷ࡫ࡳࡱࡱࡱࡷࡪࡀࠠࡼࡿࠥờ").format(response))
                return response
            else:
                logger.error(bstack111l1ll_opy_ (u"ࠨ࡛ࡤࡱ࡯ࡰࡪࡩࡴࡃࡷ࡬ࡰࡩࡊࡡࡵࡣࡠࠤࡋࡧࡩ࡭ࡧࡧࠤࡹࡵࠠࡤࡱ࡯ࡰࡪࡩࡴࠡࡤࡸ࡭ࡱࡪࠠࡥࡣࡷࡥࠥ࡬࡯ࡳࠢࡥࡹ࡮ࡲࡤࠡࡗࡘࡍࡉࡀࠠࡼࡿࠥỞ").format(bstack1111ll1l1l1_opy_))
                return None
        except Exception as e:
            logger.error(bstack111l1ll_opy_ (u"ࠢ࡜ࡥࡲࡰࡱ࡫ࡣࡵࡄࡸ࡭ࡱࡪࡄࡢࡶࡤࡡࠥࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡ࡫ࡱࠤࡨࡵ࡬࡭ࡧࡦࡸ࡮ࡴࡧࠡࡤࡸ࡭ࡱࡪࠠࡥࡣࡷࡥࠥ࡬࡯ࡳࠢࡥࡹ࡮ࡲࡤࠡࡗࡘࡍࡉࠦࡻࡾ࠼ࠣࡿࢂࠨở").format(bstack1111ll1l1l1_opy_, e))
            return None