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
import threading
from bstack_utils.helper import bstack1l1l11l1ll_opy_
from bstack_utils.constants import bstack11l1ll1l11l_opy_, EVENTS, STAGE
from bstack_utils.bstack1lllll11l1_opy_ import get_logger
logger = get_logger(__name__)
class bstack11l1l1111l_opy_:
    bstack1llllll111ll_opy_ = None
    @classmethod
    def bstack111111ll_opy_(cls):
        if cls.on() and os.getenv(bstack111l1ll_opy_ (u"ࠣࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡕࡇࡖࡘࡍ࡛ࡂࡠࡗࡘࡍࡉࠨ∨")):
            logger.info(
                bstack111l1ll_opy_ (u"࡙ࠩ࡭ࡸ࡯ࡴࠡࡪࡷࡸࡵࡹ࠺࠰࠱ࡤࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡩ࡯࡮࠱ࡥࡹ࡮ࡲࡤࡴ࠱ࡾࢁࠥࡺ࡯ࠡࡸ࡬ࡩࡼࠦࡢࡶ࡫࡯ࡨࠥࡸࡥࡱࡱࡵࡸ࠱ࠦࡩ࡯ࡵ࡬࡫࡭ࡺࡳ࠭ࠢࡤࡲࡩࠦ࡭ࡢࡰࡼࠤࡲࡵࡲࡦࠢࡧࡩࡧࡻࡧࡨ࡫ࡱ࡫ࠥ࡯࡮ࡧࡱࡵࡱࡦࡺࡩࡰࡰࠣࡥࡱࡲࠠࡢࡶࠣࡳࡳ࡫ࠠࡱ࡮ࡤࡧࡪࠧ࡜࡯ࠩ∩").format(os.getenv(bstack111l1ll_opy_ (u"ࠥࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡗࡉࡘ࡚ࡈࡖࡄࡢ࡙࡚ࡏࡄࠣ∪"))))
    @classmethod
    def on(cls):
        if os.environ.get(bstack111l1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡘࡊ࡙ࡔࡉࡗࡅࡣࡏ࡝ࡔࠨ∫"), None) is None or os.environ[bstack111l1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡊࡘࡆࡤࡐࡗࡕࠩ∬")] == bstack111l1ll_opy_ (u"ࠨ࡮ࡶ࡮࡯ࠦ∭"):
            return False
        return True
    @classmethod
    def bstack1lll1llllll1_opy_(cls, bs_config, framework=bstack111l1ll_opy_ (u"ࠢࠣ∮")):
        bstack11l1llll1ll_opy_ = False
        for fw in bstack11l1ll1l11l_opy_:
            if fw in framework:
                bstack11l1llll1ll_opy_ = True
        return bstack1l1l11l1ll_opy_(bs_config.get(bstack111l1ll_opy_ (u"ࠨࡶࡨࡷࡹࡕࡢࡴࡧࡵࡺࡦࡨࡩ࡭࡫ࡷࡽࠬ∯"), bstack11l1llll1ll_opy_))
    @classmethod
    def bstack1lll1llll1ll_opy_(cls, framework):
        return framework in bstack11l1ll1l11l_opy_
    @classmethod
    def bstack1llll111llll_opy_(cls, bs_config, framework):
        return cls.bstack1lll1llllll1_opy_(bs_config, framework) is True and cls.bstack1lll1llll1ll_opy_(framework)
    @staticmethod
    def current_hook_uuid():
        return getattr(threading.current_thread(), bstack111l1ll_opy_ (u"ࠩࡦࡹࡷࡸࡥ࡯ࡶࡢ࡬ࡴࡵ࡫ࡠࡷࡸ࡭ࡩ࠭∰"), None)
    @staticmethod
    def bstack111ll1llll_opy_():
        if getattr(threading.current_thread(), bstack111l1ll_opy_ (u"ࠪࡧࡺࡸࡲࡦࡰࡷࡣࡹ࡫ࡳࡵࡡࡸࡹ࡮ࡪࠧ∱"), None):
            return {
                bstack111l1ll_opy_ (u"ࠫࡹࡿࡰࡦࠩ∲"): bstack111l1ll_opy_ (u"ࠬࡺࡥࡴࡶࠪ∳"),
                bstack111l1ll_opy_ (u"࠭ࡴࡦࡵࡷࡣࡷࡻ࡮ࡠࡷࡸ࡭ࡩ࠭∴"): getattr(threading.current_thread(), bstack111l1ll_opy_ (u"ࠧࡤࡷࡵࡶࡪࡴࡴࡠࡶࡨࡷࡹࡥࡵࡶ࡫ࡧࠫ∵"), None)
            }
        if getattr(threading.current_thread(), bstack111l1ll_opy_ (u"ࠨࡥࡸࡶࡷ࡫࡮ࡵࡡ࡫ࡳࡴࡱ࡟ࡶࡷ࡬ࡨࠬ∶"), None):
            return {
                bstack111l1ll_opy_ (u"ࠩࡷࡽࡵ࡫ࠧ∷"): bstack111l1ll_opy_ (u"ࠪ࡬ࡴࡵ࡫ࠨ∸"),
                bstack111l1ll_opy_ (u"ࠫ࡭ࡵ࡯࡬ࡡࡵࡹࡳࡥࡵࡶ࡫ࡧࠫ∹"): getattr(threading.current_thread(), bstack111l1ll_opy_ (u"ࠬࡩࡵࡳࡴࡨࡲࡹࡥࡨࡰࡱ࡮ࡣࡺࡻࡩࡥࠩ∺"), None)
            }
        return None
    @staticmethod
    def bstack1lll1lllll11_opy_(func):
        def wrap(*args, **kwargs):
            if bstack11l1l1111l_opy_.on():
                return func(*args, **kwargs)
            return
        return wrap
    @staticmethod
    def bstack1111ll1l1l_opy_(test, hook_name=None):
        bstack1lll1llll11l_opy_ = test.parent
        if hook_name in [bstack111l1ll_opy_ (u"࠭ࡳࡦࡶࡸࡴࡤࡩ࡬ࡢࡵࡶࠫ∻"), bstack111l1ll_opy_ (u"ࠧࡵࡧࡤࡶࡩࡵࡷ࡯ࡡࡦࡰࡦࡹࡳࠨ∼"), bstack111l1ll_opy_ (u"ࠨࡵࡨࡸࡺࡶ࡟࡮ࡱࡧࡹࡱ࡫ࠧ∽"), bstack111l1ll_opy_ (u"ࠩࡷࡩࡦࡸࡤࡰࡹࡱࡣࡲࡵࡤࡶ࡮ࡨࠫ∾")]:
            bstack1lll1llll11l_opy_ = test
        scope = []
        while bstack1lll1llll11l_opy_ is not None:
            scope.append(bstack1lll1llll11l_opy_.name)
            bstack1lll1llll11l_opy_ = bstack1lll1llll11l_opy_.parent
        scope.reverse()
        return scope[2:]
    @staticmethod
    def bstack1lll1lllll1l_opy_(hook_type):
        if hook_type == bstack111l1ll_opy_ (u"ࠥࡆࡊࡌࡏࡓࡇࡢࡉࡆࡉࡈࠣ∿"):
            return bstack111l1ll_opy_ (u"ࠦࡘ࡫ࡴࡶࡲࠣ࡬ࡴࡵ࡫ࠣ≀")
        elif hook_type == bstack111l1ll_opy_ (u"ࠧࡇࡆࡕࡇࡕࡣࡊࡇࡃࡉࠤ≁"):
            return bstack111l1ll_opy_ (u"ࠨࡔࡦࡣࡵࡨࡴࡽ࡮ࠡࡪࡲࡳࡰࠨ≂")
    @staticmethod
    def bstack1lll1llll1l1_opy_(bstack11l11l11l1_opy_):
        try:
            if not bstack11l1l1111l_opy_.on():
                return bstack11l11l11l1_opy_
            if os.environ.get(bstack111l1ll_opy_ (u"ࠢࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡒࡆࡔࡘࡒࠧ≃"), None) == bstack111l1ll_opy_ (u"ࠣࡶࡵࡹࡪࠨ≄"):
                tests = os.environ.get(bstack111l1ll_opy_ (u"ࠤࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡔࡈࡖ࡚ࡔ࡟ࡕࡇࡖࡘࡘࠨ≅"), None)
                if tests is None or tests == bstack111l1ll_opy_ (u"ࠥࡲࡺࡲ࡬ࠣ≆"):
                    return bstack11l11l11l1_opy_
                bstack11l11l11l1_opy_ = tests.split(bstack111l1ll_opy_ (u"ࠫ࠱࠭≇"))
                return bstack11l11l11l1_opy_
        except Exception as exc:
            logger.debug(bstack111l1ll_opy_ (u"ࠧࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡ࡫ࡱࠤࡷ࡫ࡲࡶࡰࠣ࡬ࡦࡴࡤ࡭ࡧࡵ࠾ࠥࠨ≈") + str(str(exc)) + bstack111l1ll_opy_ (u"ࠨࠢ≉"))
        return bstack11l11l11l1_opy_