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
import logging
import os
import datetime
import threading
from bstack_utils.constants import EVENTS, STAGE
from bstack_utils.helper import bstack11ll1l11l1l_opy_, bstack11ll1l1l1l1_opy_, bstack11111lll1_opy_, error_handler, bstack11l11l11111_opy_, bstack111llll1ll1_opy_, bstack111lll111l1_opy_, bstack11l1llll11_opy_, bstack1111llll1_opy_
from bstack_utils.measure import measure
from bstack_utils.bstack1llllll111ll_opy_ import bstack1lllll1lll11_opy_
import bstack_utils.bstack111lll11l_opy_ as bstack11ll1lll_opy_
from bstack_utils.bstack111ll11lll_opy_ import bstack11l1l1111l_opy_
import bstack_utils.accessibility as bstack1ll1l1ll_opy_
from bstack_utils.bstack11llll111l_opy_ import bstack11llll111l_opy_
from bstack_utils.bstack111ll11l11_opy_ import bstack111l111111_opy_
from bstack_utils.constants import bstack11ll1ll1l_opy_
bstack1llll111ll1l_opy_ = bstack111l1ll_opy_ (u"ࠩ࡫ࡸࡹࡶࡳ࠻࠱࠲ࡧࡴࡲ࡬ࡦࡥࡷࡳࡷ࠳࡯ࡣࡵࡨࡶࡻࡧࡢࡪ࡮࡬ࡸࡾ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡩ࡯࡮ࠩ⃠")
logger = logging.getLogger(__name__)
class bstack111111l1l_opy_:
    bstack1llllll111ll_opy_ = None
    bs_config = None
    bstack11l1111l1_opy_ = None
    @classmethod
    @error_handler(class_method=True)
    @measure(event_name=EVENTS.bstack11l1l1lllll_opy_, stage=STAGE.bstack1l11lllll1_opy_)
    def launch(cls, bs_config, bstack11l1111l1_opy_):
        cls.bs_config = bs_config
        cls.bstack11l1111l1_opy_ = bstack11l1111l1_opy_
        try:
            cls.bstack1llll111lll1_opy_()
            bstack11ll1ll11l1_opy_ = bstack11ll1l11l1l_opy_(bs_config)
            bstack11ll1llll1l_opy_ = bstack11ll1l1l1l1_opy_(bs_config)
            data = bstack11ll1lll_opy_.bstack1llll11l11l1_opy_(bs_config, bstack11l1111l1_opy_)
            config = {
                bstack111l1ll_opy_ (u"ࠪࡥࡺࡺࡨࠨ⃡"): (bstack11ll1ll11l1_opy_, bstack11ll1llll1l_opy_),
                bstack111l1ll_opy_ (u"ࠫ࡭࡫ࡡࡥࡧࡵࡷࠬ⃢"): cls.default_headers()
            }
            response = bstack11111lll1_opy_(bstack111l1ll_opy_ (u"ࠬࡖࡏࡔࡖࠪ⃣"), cls.request_url(bstack111l1ll_opy_ (u"࠭ࡡࡱ࡫࠲ࡺ࠷࠵ࡢࡶ࡫࡯ࡨࡸ࠭⃤")), data, config)
            if response.status_code != 200:
                bstack11l1ll1lll_opy_ = response.json()
                if bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠧࡴࡷࡦࡧࡪࡹࡳࠨ⃥")] == False:
                    cls.bstack1llll111ll11_opy_(bstack11l1ll1lll_opy_)
                    return
                cls.bstack1llll11ll111_opy_(bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠨࡱࡥࡷࡪࡸࡶࡢࡤ࡬ࡰ࡮ࡺࡹࠨ⃦")])
                cls.bstack1llll11l1111_opy_(bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠩ⃧")])
                return None
            bstack1llll1l11111_opy_ = cls.bstack1llll11llll1_opy_(response)
            return bstack1llll1l11111_opy_, response.json()
        except Exception as error:
            logger.error(bstack111l1ll_opy_ (u"ࠥࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡷࡩ࡫࡯ࡩࠥࡩࡲࡦࡣࡷ࡭ࡳ࡭ࠠࡣࡷ࡬ࡰࡩࠦࡦࡰࡴࠣࡘࡪࡹࡴࡉࡷࡥ࠾ࠥࢁࡽ⃨ࠣ").format(str(error)))
            return None
    @classmethod
    @error_handler(class_method=True)
    def stop(cls, bstack1llll1l11l11_opy_=None):
        if not bstack11l1l1111l_opy_.on() and not bstack1ll1l1ll_opy_.on():
            return
        if os.environ.get(bstack111l1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡘࡊ࡙ࡔࡉࡗࡅࡣࡏ࡝ࡔࠨ⃩")) == bstack111l1ll_opy_ (u"ࠧࡴࡵ࡭࡮⃪ࠥ") or os.environ.get(bstack111l1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤ࡚ࡅࡔࡖࡋ࡙ࡇࡥࡕࡖࡋࡇ⃫ࠫ")) == bstack111l1ll_opy_ (u"ࠢ࡯ࡷ࡯ࡰ⃬ࠧ"):
            logger.error(bstack111l1ll_opy_ (u"ࠨࡇࡻࡧࡪࡶࡴࡪࡱࡱࠤ࡮ࡴࠠࡴࡶࡲࡴࠥࡨࡵࡪ࡮ࡧࠤࡷ࡫ࡱࡶࡧࡶࡸࠥࡺ࡯ࠡࡖࡨࡷࡹࡎࡵࡣ࠼ࠣࡑ࡮ࡹࡳࡪࡰࡪࠤࡦࡻࡴࡩࡧࡱࡸ࡮ࡩࡡࡵ࡫ࡲࡲࠥࡺ࡯࡬ࡧࡱ⃭ࠫ"))
            return {
                bstack111l1ll_opy_ (u"ࠩࡶࡸࡦࡺࡵࡴ⃮ࠩ"): bstack111l1ll_opy_ (u"ࠪࡩࡷࡸ࡯ࡳ⃯ࠩ"),
                bstack111l1ll_opy_ (u"ࠫࡲ࡫ࡳࡴࡣࡪࡩࠬ⃰"): bstack111l1ll_opy_ (u"࡚ࠬ࡯࡬ࡧࡱ࠳ࡧࡻࡩ࡭ࡦࡌࡈࠥ࡯ࡳࠡࡷࡱࡨࡪ࡬ࡩ࡯ࡧࡧ࠰ࠥࡨࡵࡪ࡮ࡧࠤࡨࡸࡥࡢࡶ࡬ࡳࡳࠦ࡭ࡪࡩ࡫ࡸࠥ࡮ࡡࡷࡧࠣࡪࡦ࡯࡬ࡦࡦࠪ⃱")
            }
        try:
            cls.bstack1llllll111ll_opy_.shutdown()
            data = {
                bstack111l1ll_opy_ (u"࠭ࡦࡪࡰ࡬ࡷ࡭࡫ࡤࡠࡣࡷࠫ⃲"): bstack11l1llll11_opy_()
            }
            if not bstack1llll1l11l11_opy_ is None:
                data[bstack111l1ll_opy_ (u"ࠧࡧ࡫ࡱ࡭ࡸ࡮ࡥࡥࡡࡰࡩࡹࡧࡤࡢࡶࡤࠫ⃳")] = [{
                    bstack111l1ll_opy_ (u"ࠨࡴࡨࡥࡸࡵ࡮ࠨ⃴"): bstack111l1ll_opy_ (u"ࠩࡸࡷࡪࡸ࡟࡬࡫࡯ࡰࡪࡪࠧ⃵"),
                    bstack111l1ll_opy_ (u"ࠪࡷ࡮࡭࡮ࡢ࡮ࠪ⃶"): bstack1llll1l11l11_opy_
                }]
            config = {
                bstack111l1ll_opy_ (u"ࠫ࡭࡫ࡡࡥࡧࡵࡷࠬ⃷"): cls.default_headers()
            }
            bstack11ll111ll11_opy_ = bstack111l1ll_opy_ (u"ࠬࡧࡰࡪ࠱ࡹ࠵࠴ࡨࡵࡪ࡮ࡧࡷ࠴ࢁࡽ࠰ࡵࡷࡳࡵ࠭⃸").format(os.environ[bstack111l1ll_opy_ (u"ࠨࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤ࡚ࡅࡔࡖࡋ࡙ࡇࡥࡕࡖࡋࡇࠦ⃹")])
            bstack1llll1l11l1l_opy_ = cls.request_url(bstack11ll111ll11_opy_)
            response = bstack11111lll1_opy_(bstack111l1ll_opy_ (u"ࠧࡑࡗࡗࠫ⃺"), bstack1llll1l11l1l_opy_, data, config)
            if not response.ok:
                raise Exception(bstack111l1ll_opy_ (u"ࠣࡕࡷࡳࡵࠦࡲࡦࡳࡸࡩࡸࡺࠠ࡯ࡱࡷࠤࡴࡱࠢ⃻"))
        except Exception as error:
            logger.error(bstack111l1ll_opy_ (u"ࠤࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥ࡯࡮ࠡࡵࡷࡳࡵࠦࡢࡶ࡫࡯ࡨࠥࡸࡥࡲࡷࡨࡷࡹࠦࡴࡰࠢࡗࡩࡸࡺࡈࡶࡤ࠽࠾ࠥࠨ⃼") + str(error))
            return {
                bstack111l1ll_opy_ (u"ࠪࡷࡹࡧࡴࡶࡵࠪ⃽"): bstack111l1ll_opy_ (u"ࠫࡪࡸࡲࡰࡴࠪ⃾"),
                bstack111l1ll_opy_ (u"ࠬࡳࡥࡴࡵࡤ࡫ࡪ࠭⃿"): str(error)
            }
    @classmethod
    @error_handler(class_method=True)
    def bstack1llll11llll1_opy_(cls, response):
        bstack11l1ll1lll_opy_ = response.json() if not isinstance(response, dict) else response
        bstack1llll1l11111_opy_ = {}
        if bstack11l1ll1lll_opy_.get(bstack111l1ll_opy_ (u"࠭ࡪࡸࡶࠪ℀")) is None:
            os.environ[bstack111l1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡋ࡙ࡗࠫ℁")] = bstack111l1ll_opy_ (u"ࠨࡰࡸࡰࡱ࠭ℂ")
        else:
            os.environ[bstack111l1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡎࡕࡃࡡࡍ࡛࡙࠭℃")] = bstack11l1ll1lll_opy_.get(bstack111l1ll_opy_ (u"ࠪ࡮ࡼࡺࠧ℄"), bstack111l1ll_opy_ (u"ࠫࡳࡻ࡬࡭ࠩ℅"))
        os.environ[bstack111l1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡊࡘࡆࡤ࡛ࡕࡊࡆࠪ℆")] = bstack11l1ll1lll_opy_.get(bstack111l1ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡤ࡮ࡡࡴࡪࡨࡨࡤ࡯ࡤࠨℇ"), bstack111l1ll_opy_ (u"ࠧ࡯ࡷ࡯ࡰࠬ℈"))
        logger.info(bstack111l1ll_opy_ (u"ࠨࡖࡨࡷࡹ࡮ࡵࡣࠢࡶࡸࡦࡸࡴࡦࡦࠣࡻ࡮ࡺࡨࠡ࡫ࡧ࠾ࠥ࠭℉") + os.getenv(bstack111l1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡎࡕࡃࡡࡘ࡙ࡎࡊࠧℊ")));
        if bstack11l1l1111l_opy_.bstack1llll111llll_opy_(cls.bs_config, cls.bstack11l1111l1_opy_.get(bstack111l1ll_opy_ (u"ࠪࡪࡷࡧ࡭ࡦࡹࡲࡶࡰࡥࡵࡴࡧࡧࠫℋ"), bstack111l1ll_opy_ (u"ࠫࠬℌ"))) is True:
            bstack1lllll1l1l11_opy_, build_hashed_id, bstack1llll11ll1ll_opy_ = cls.bstack1llll11l111l_opy_(bstack11l1ll1lll_opy_)
            if bstack1lllll1l1l11_opy_ != None and build_hashed_id != None:
                bstack1llll1l11111_opy_[bstack111l1ll_opy_ (u"ࠬࡵࡢࡴࡧࡵࡺࡦࡨࡩ࡭࡫ࡷࡽࠬℍ")] = {
                    bstack111l1ll_opy_ (u"࠭ࡪࡸࡶࡢࡸࡴࡱࡥ࡯ࠩℎ"): bstack1lllll1l1l11_opy_,
                    bstack111l1ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡥࡨࡢࡵ࡫ࡩࡩࡥࡩࡥࠩℏ"): build_hashed_id,
                    bstack111l1ll_opy_ (u"ࠨࡣ࡯ࡰࡴࡽ࡟ࡴࡥࡵࡩࡪࡴࡳࡩࡱࡷࡷࠬℐ"): bstack1llll11ll1ll_opy_
                }
            else:
                bstack1llll1l11111_opy_[bstack111l1ll_opy_ (u"ࠩࡲࡦࡸ࡫ࡲࡷࡣࡥ࡭ࡱ࡯ࡴࡺࠩℑ")] = {}
        else:
            bstack1llll1l11111_opy_[bstack111l1ll_opy_ (u"ࠪࡳࡧࡹࡥࡳࡸࡤࡦ࡮ࡲࡩࡵࡻࠪℒ")] = {}
        bstack1llll11l1lll_opy_, build_hashed_id = cls.bstack1llll11l11ll_opy_(bstack11l1ll1lll_opy_)
        if bstack1llll11l1lll_opy_ != None and build_hashed_id != None:
            bstack1llll1l11111_opy_[bstack111l1ll_opy_ (u"ࠫࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠫℓ")] = {
                bstack111l1ll_opy_ (u"ࠬࡧࡵࡵࡪࡢࡸࡴࡱࡥ࡯ࠩ℔"): bstack1llll11l1lll_opy_,
                bstack111l1ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡤ࡮ࡡࡴࡪࡨࡨࡤ࡯ࡤࠨℕ"): build_hashed_id,
            }
        else:
            bstack1llll1l11111_opy_[bstack111l1ll_opy_ (u"ࠧࡢࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࠧ№")] = {}
        if bstack1llll1l11111_opy_[bstack111l1ll_opy_ (u"ࠨࡱࡥࡷࡪࡸࡶࡢࡤ࡬ࡰ࡮ࡺࡹࠨ℗")].get(bstack111l1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡠࡪࡤࡷ࡭࡫ࡤࡠ࡫ࡧࠫ℘")) != None or bstack1llll1l11111_opy_[bstack111l1ll_opy_ (u"ࠪࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࠪℙ")].get(bstack111l1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡢ࡬ࡦࡹࡨࡦࡦࡢ࡭ࡩ࠭ℚ")) != None:
            cls.bstack1llll11ll11l_opy_(bstack11l1ll1lll_opy_.get(bstack111l1ll_opy_ (u"ࠬࡰࡷࡵࠩℛ")), bstack11l1ll1lll_opy_.get(bstack111l1ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡤ࡮ࡡࡴࡪࡨࡨࡤ࡯ࡤࠨℜ")))
        return bstack1llll1l11111_opy_
    @classmethod
    def bstack1llll11l111l_opy_(cls, bstack11l1ll1lll_opy_):
        if bstack11l1ll1lll_opy_.get(bstack111l1ll_opy_ (u"ࠧࡰࡤࡶࡩࡷࡼࡡࡣ࡫࡯࡭ࡹࡿࠧℝ")) == None:
            cls.bstack1llll11ll111_opy_()
            return [None, None, None]
        if bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠨࡱࡥࡷࡪࡸࡶࡢࡤ࡬ࡰ࡮ࡺࡹࠨ℞")][bstack111l1ll_opy_ (u"ࠩࡶࡹࡨࡩࡥࡴࡵࠪ℟")] != True:
            cls.bstack1llll11ll111_opy_(bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠪࡳࡧࡹࡥࡳࡸࡤࡦ࡮ࡲࡩࡵࡻࠪ℠")])
            return [None, None, None]
        logger.debug(bstack111l1ll_opy_ (u"ࠫࢀࢃࠠࡃࡷ࡬ࡰࡩࠦࡣࡳࡧࡤࡸ࡮ࡵ࡮ࠡࡕࡸࡧࡨ࡫ࡳࡴࡨࡸࡰࠦ࠭℡").format(bstack11ll1ll1l_opy_))
        os.environ[bstack111l1ll_opy_ (u"ࠬࡈࡓࡠࡖࡈࡗ࡙ࡕࡐࡔࡡࡅ࡙ࡎࡒࡄࡠࡅࡒࡑࡕࡒࡅࡕࡇࡇࠫ™")] = bstack111l1ll_opy_ (u"࠭ࡴࡳࡷࡨࠫ℣")
        if bstack11l1ll1lll_opy_.get(bstack111l1ll_opy_ (u"ࠧ࡫ࡹࡷࠫℤ")):
            os.environ[bstack111l1ll_opy_ (u"ࠨࡅࡕࡉࡉࡋࡎࡕࡋࡄࡐࡘࡥࡆࡐࡔࡢࡇࡗࡇࡓࡉࡡࡕࡉࡕࡕࡒࡕࡋࡑࡋࠬ℥")] = json.dumps({
                bstack111l1ll_opy_ (u"ࠩࡸࡷࡪࡸ࡮ࡢ࡯ࡨࠫΩ"): bstack11ll1l11l1l_opy_(cls.bs_config),
                bstack111l1ll_opy_ (u"ࠪࡴࡦࡹࡳࡸࡱࡵࡨࠬ℧"): bstack11ll1l1l1l1_opy_(cls.bs_config)
            })
        if bstack11l1ll1lll_opy_.get(bstack111l1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡢ࡬ࡦࡹࡨࡦࡦࡢ࡭ࡩ࠭ℨ")):
            os.environ[bstack111l1ll_opy_ (u"ࠬࡈࡓࡠࡖࡈࡗ࡙ࡕࡐࡔࡡࡅ࡙ࡎࡒࡄࡠࡊࡄࡗࡍࡋࡄࡠࡋࡇࠫ℩")] = bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡤ࡮ࡡࡴࡪࡨࡨࡤ࡯ࡤࠨK")]
        if bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠧࡰࡤࡶࡩࡷࡼࡡࡣ࡫࡯࡭ࡹࡿࠧÅ")].get(bstack111l1ll_opy_ (u"ࠨࡱࡳࡸ࡮ࡵ࡮ࡴࠩℬ"), {}).get(bstack111l1ll_opy_ (u"ࠩࡤࡰࡱࡵࡷࡠࡵࡦࡶࡪ࡫࡮ࡴࡪࡲࡸࡸ࠭ℭ")):
            os.environ[bstack111l1ll_opy_ (u"ࠪࡆࡘࡥࡔࡆࡕࡗࡓࡕ࡙࡟ࡂࡎࡏࡓ࡜ࡥࡓࡄࡔࡈࡉࡓ࡙ࡈࡐࡖࡖࠫ℮")] = str(bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠫࡴࡨࡳࡦࡴࡹࡥࡧ࡯࡬ࡪࡶࡼࠫℯ")][bstack111l1ll_opy_ (u"ࠬࡵࡰࡵ࡫ࡲࡲࡸ࠭ℰ")][bstack111l1ll_opy_ (u"࠭ࡡ࡭࡮ࡲࡻࡤࡹࡣࡳࡧࡨࡲࡸ࡮࡯ࡵࡵࠪℱ")])
        else:
            os.environ[bstack111l1ll_opy_ (u"ࠧࡃࡕࡢࡘࡊ࡙ࡔࡐࡒࡖࡣࡆࡒࡌࡐ࡙ࡢࡗࡈࡘࡅࡆࡐࡖࡌࡔ࡚ࡓࠨℲ")] = bstack111l1ll_opy_ (u"ࠣࡰࡸࡰࡱࠨℳ")
        return [bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠩ࡭ࡻࡹ࠭ℴ")], bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠪࡦࡺ࡯࡬ࡥࡡ࡫ࡥࡸ࡮ࡥࡥࡡ࡬ࡨࠬℵ")], os.environ[bstack111l1ll_opy_ (u"ࠫࡇ࡙࡟ࡕࡇࡖࡘࡔࡖࡓࡠࡃࡏࡐࡔ࡝࡟ࡔࡅࡕࡉࡊࡔࡓࡉࡑࡗࡗࠬℶ")]]
    @classmethod
    def bstack1llll11l11ll_opy_(cls, bstack11l1ll1lll_opy_):
        if bstack11l1ll1lll_opy_.get(bstack111l1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬℷ")) == None:
            cls.bstack1llll11l1111_opy_()
            return [None, None]
        if bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾ࠭ℸ")][bstack111l1ll_opy_ (u"ࠧࡴࡷࡦࡧࡪࡹࡳࠨℹ")] != True:
            cls.bstack1llll11l1111_opy_(bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࠨ℺")])
            return [None, None]
        if bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠩ℻")].get(bstack111l1ll_opy_ (u"ࠪࡳࡵࡺࡩࡰࡰࡶࠫℼ")):
            logger.debug(bstack111l1ll_opy_ (u"࡙ࠫ࡫ࡳࡵࠢࡄࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠢࡅࡹ࡮ࡲࡤࠡࡥࡵࡩࡦࡺࡩࡰࡰࠣࡗࡺࡩࡣࡦࡵࡶࡪࡺࡲࠡࠨℽ"))
            parsed = json.loads(os.getenv(bstack111l1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡡࡄࡇࡈࡋࡓࡔࡋࡅࡍࡑࡏࡔ࡚ࡡࡆࡓࡓࡌࡉࡈࡗࡕࡅ࡙ࡏࡏࡏࡡ࡜ࡑࡑ࠭ℾ"), bstack111l1ll_opy_ (u"࠭ࡻࡾࠩℿ")))
            capabilities = bstack11ll1lll_opy_.bstack1llll11l1ll1_opy_(bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠧࡢࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࠧ⅀")][bstack111l1ll_opy_ (u"ࠨࡱࡳࡸ࡮ࡵ࡮ࡴࠩ⅁")][bstack111l1ll_opy_ (u"ࠩࡦࡥࡵࡧࡢࡪ࡮࡬ࡸ࡮࡫ࡳࠨ⅂")], bstack111l1ll_opy_ (u"ࠪࡲࡦࡳࡥࠨ⅃"), bstack111l1ll_opy_ (u"ࠫࡻࡧ࡬ࡶࡧࠪ⅄"))
            bstack1llll11l1lll_opy_ = capabilities[bstack111l1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽ࡙ࡵ࡫ࡦࡰࠪⅅ")]
            os.environ[bstack111l1ll_opy_ (u"࠭ࡂࡔࡡࡄ࠵࠶࡟࡟ࡋ࡙ࡗࠫⅆ")] = bstack1llll11l1lll_opy_
            if bstack111l1ll_opy_ (u"ࠢࡢࡷࡷࡳࡲࡧࡴࡦࠤⅇ") in bstack11l1ll1lll_opy_ and bstack11l1ll1lll_opy_.get(bstack111l1ll_opy_ (u"ࠣࡣࡳࡴࡤࡧࡵࡵࡱࡰࡥࡹ࡫ࠢⅈ")) is None:
                parsed[bstack111l1ll_opy_ (u"ࠩࡶࡧࡦࡴ࡮ࡦࡴ࡙ࡩࡷࡹࡩࡰࡰࠪⅉ")] = capabilities[bstack111l1ll_opy_ (u"ࠪࡷࡨࡧ࡮࡯ࡧࡵ࡚ࡪࡸࡳࡪࡱࡱࠫ⅊")]
            os.environ[bstack111l1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡘࡊ࡙ࡔࡠࡃࡆࡇࡊ࡙ࡓࡊࡄࡌࡐࡎ࡚࡙ࡠࡅࡒࡒࡋࡏࡇࡖࡔࡄࡘࡎࡕࡎࡠ࡛ࡐࡐࠬ⅋")] = json.dumps(parsed)
            scripts = bstack11ll1lll_opy_.bstack1llll11l1ll1_opy_(bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬ⅌")][bstack111l1ll_opy_ (u"࠭࡯ࡱࡶ࡬ࡳࡳࡹࠧ⅍")][bstack111l1ll_opy_ (u"ࠧࡴࡥࡵ࡭ࡵࡺࡳࠨⅎ")], bstack111l1ll_opy_ (u"ࠨࡰࡤࡱࡪ࠭⅏"), bstack111l1ll_opy_ (u"ࠩࡦࡳࡲࡳࡡ࡯ࡦࠪ⅐"))
            bstack11llll111l_opy_.bstack1llllll1ll_opy_(scripts)
            commands = bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠪࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࠪ⅑")][bstack111l1ll_opy_ (u"ࠫࡴࡶࡴࡪࡱࡱࡷࠬ⅒")][bstack111l1ll_opy_ (u"ࠬࡩ࡯࡮࡯ࡤࡲࡩࡹࡔࡰ࡙ࡵࡥࡵ࠭⅓")].get(bstack111l1ll_opy_ (u"࠭ࡣࡰ࡯ࡰࡥࡳࡪࡳࠨ⅔"))
            bstack11llll111l_opy_.bstack11ll1l111ll_opy_(commands)
            bstack11ll1l11ll1_opy_ = capabilities.get(bstack111l1ll_opy_ (u"ࠧࡨࡱࡲ࡫࠿ࡩࡨࡳࡱࡰࡩࡔࡶࡴࡪࡱࡱࡷࠬ⅕"))
            bstack11llll111l_opy_.bstack11ll11l11l1_opy_(bstack11ll1l11ll1_opy_)
            bstack11llll111l_opy_.store()
        return [bstack1llll11l1lll_opy_, bstack11l1ll1lll_opy_[bstack111l1ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪ࡟ࡩࡣࡶ࡬ࡪࡪ࡟ࡪࡦࠪ⅖")]]
    @classmethod
    def bstack1llll11ll111_opy_(cls, response=None):
        os.environ[bstack111l1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡎࡕࡃࡡࡘ࡙ࡎࡊࠧ⅗")] = bstack111l1ll_opy_ (u"ࠪࡲࡺࡲ࡬ࠨ⅘")
        os.environ[bstack111l1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡘࡊ࡙ࡔࡉࡗࡅࡣࡏ࡝ࡔࠨ⅙")] = bstack111l1ll_opy_ (u"ࠬࡴࡵ࡭࡮ࠪ⅚")
        os.environ[bstack111l1ll_opy_ (u"࠭ࡂࡔࡡࡗࡉࡘ࡚ࡏࡑࡕࡢࡆ࡚ࡏࡌࡅࡡࡆࡓࡒࡖࡌࡆࡖࡈࡈࠬ⅛")] = bstack111l1ll_opy_ (u"ࠧࡧࡣ࡯ࡷࡪ࠭⅜")
        os.environ[bstack111l1ll_opy_ (u"ࠨࡄࡖࡣ࡙ࡋࡓࡕࡑࡓࡗࡤࡈࡕࡊࡎࡇࡣࡍࡇࡓࡉࡇࡇࡣࡎࡊࠧ⅝")] = bstack111l1ll_opy_ (u"ࠤࡱࡹࡱࡲࠢ⅞")
        os.environ[bstack111l1ll_opy_ (u"ࠪࡆࡘࡥࡔࡆࡕࡗࡓࡕ࡙࡟ࡂࡎࡏࡓ࡜ࡥࡓࡄࡔࡈࡉࡓ࡙ࡈࡐࡖࡖࠫ⅟")] = bstack111l1ll_opy_ (u"ࠦࡳࡻ࡬࡭ࠤⅠ")
        cls.bstack1llll111ll11_opy_(response, bstack111l1ll_opy_ (u"ࠧࡵࡢࡴࡧࡵࡺࡦࡨࡩ࡭࡫ࡷࡽࠧⅡ"))
        return [None, None, None]
    @classmethod
    def bstack1llll11l1111_opy_(cls, response=None):
        os.environ[bstack111l1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤ࡚ࡅࡔࡖࡋ࡙ࡇࡥࡕࡖࡋࡇࠫⅢ")] = bstack111l1ll_opy_ (u"ࠧ࡯ࡷ࡯ࡰࠬⅣ")
        os.environ[bstack111l1ll_opy_ (u"ࠨࡄࡖࡣࡆ࠷࠱࡚ࡡࡍ࡛࡙࠭Ⅴ")] = bstack111l1ll_opy_ (u"ࠩࡱࡹࡱࡲࠧⅥ")
        os.environ[bstack111l1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡗࡉࡘ࡚ࡈࡖࡄࡢࡎ࡜࡚ࠧⅦ")] = bstack111l1ll_opy_ (u"ࠫࡳࡻ࡬࡭ࠩⅧ")
        cls.bstack1llll111ll11_opy_(response, bstack111l1ll_opy_ (u"ࠧࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠧⅨ"))
        return [None, None, None]
    @classmethod
    def bstack1llll11ll11l_opy_(cls, jwt, build_hashed_id):
        os.environ[bstack111l1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤ࡚ࡅࡔࡖࡋ࡙ࡇࡥࡊࡘࡖࠪⅩ")] = jwt
        os.environ[bstack111l1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡖࡗࡌࡈࠬⅪ")] = build_hashed_id
    @classmethod
    def bstack1llll111ll11_opy_(cls, response=None, product=bstack111l1ll_opy_ (u"ࠣࠤⅫ")):
        if response == None or response.get(bstack111l1ll_opy_ (u"ࠩࡨࡶࡷࡵࡲࡴࠩⅬ")) == None:
            logger.error(product + bstack111l1ll_opy_ (u"ࠥࠤࡇࡻࡩ࡭ࡦࠣࡧࡷ࡫ࡡࡵ࡫ࡲࡲࠥ࡬ࡡࡪ࡮ࡨࡨࠧⅭ"))
            return
        for error in response[bstack111l1ll_opy_ (u"ࠫࡪࡸࡲࡰࡴࡶࠫⅮ")]:
            bstack11l111ll111_opy_ = error[bstack111l1ll_opy_ (u"ࠬࡱࡥࡺࠩⅯ")]
            error_message = error[bstack111l1ll_opy_ (u"࠭࡭ࡦࡵࡶࡥ࡬࡫ࠧⅰ")]
            if error_message:
                if bstack11l111ll111_opy_ == bstack111l1ll_opy_ (u"ࠢࡆࡔࡕࡓࡗࡥࡁࡄࡅࡈࡗࡘࡥࡄࡆࡐࡌࡉࡉࠨⅱ"):
                    logger.info(error_message)
                else:
                    logger.error(error_message)
            else:
                logger.error(bstack111l1ll_opy_ (u"ࠣࡆࡤࡸࡦࠦࡵࡱ࡮ࡲࡥࡩࠦࡴࡰࠢࡅࡶࡴࡽࡳࡦࡴࡖࡸࡦࡩ࡫ࠡࠤⅲ") + product + bstack111l1ll_opy_ (u"ࠤࠣࡪࡦ࡯࡬ࡦࡦࠣࡨࡺ࡫ࠠࡵࡱࠣࡷࡴࡳࡥࠡࡧࡵࡶࡴࡸࠢⅳ"))
    @classmethod
    def bstack1llll111lll1_opy_(cls):
        if cls.bstack1llllll111ll_opy_ is not None:
            return
        cls.bstack1llllll111ll_opy_ = bstack1lllll1lll11_opy_(cls.bstack1llll1l111l1_opy_)
        cls.bstack1llllll111ll_opy_.start()
    @classmethod
    def bstack1111lll1ll_opy_(cls):
        if cls.bstack1llllll111ll_opy_ is None:
            return
        cls.bstack1llllll111ll_opy_.shutdown()
    @classmethod
    @error_handler(class_method=True)
    def bstack1llll1l111l1_opy_(cls, bstack1111l1lll1_opy_, event_url=bstack111l1ll_opy_ (u"ࠪࡥࡵ࡯࠯ࡷ࠳࠲ࡦࡦࡺࡣࡩࠩⅴ")):
        config = {
            bstack111l1ll_opy_ (u"ࠫ࡭࡫ࡡࡥࡧࡵࡷࠬⅵ"): cls.default_headers()
        }
        logger.debug(bstack111l1ll_opy_ (u"ࠧࡶ࡯ࡴࡶࡢࡨࡦࡺࡡ࠻ࠢࡖࡩࡳࡪࡩ࡯ࡩࠣࡨࡦࡺࡡࠡࡶࡲࠤࡹ࡫ࡳࡵࡪࡸࡦࠥ࡬࡯ࡳࠢࡨࡺࡪࡴࡴࡴࠢࡾࢁࠧⅶ").format(bstack111l1ll_opy_ (u"࠭ࠬࠡࠩⅷ").join([event[bstack111l1ll_opy_ (u"ࠧࡦࡸࡨࡲࡹࡥࡴࡺࡲࡨࠫⅸ")] for event in bstack1111l1lll1_opy_])))
        response = bstack11111lll1_opy_(bstack111l1ll_opy_ (u"ࠨࡒࡒࡗ࡙࠭ⅹ"), cls.request_url(event_url), bstack1111l1lll1_opy_, config)
        bstack11ll11ll111_opy_ = response.json()
    @classmethod
    def bstack1l111ll11l_opy_(cls, bstack1111l1lll1_opy_, event_url=bstack111l1ll_opy_ (u"ࠩࡤࡴ࡮࠵ࡶ࠲࠱ࡥࡥࡹࡩࡨࠨⅺ")):
        logger.debug(bstack111l1ll_opy_ (u"ࠥࡷࡪࡴࡤࡠࡦࡤࡸࡦࡀࠠࡂࡶࡷࡩࡲࡶࡴࡪࡰࡪࠤࡹࡵࠠࡢࡦࡧࠤࡩࡧࡴࡢࠢࡷࡳࠥࡨࡡࡵࡥ࡫ࠤࡼ࡯ࡴࡩࠢࡨࡺࡪࡴࡴࡠࡶࡼࡴࡪࡀࠠࡼࡿࠥⅻ").format(bstack1111l1lll1_opy_[bstack111l1ll_opy_ (u"ࠫࡪࡼࡥ࡯ࡶࡢࡸࡾࡶࡥࠨⅼ")]))
        if not bstack11ll1lll_opy_.bstack1llll11lllll_opy_(bstack1111l1lll1_opy_[bstack111l1ll_opy_ (u"ࠬ࡫ࡶࡦࡰࡷࡣࡹࡿࡰࡦࠩⅽ")]):
            logger.debug(bstack111l1ll_opy_ (u"ࠨࡳࡦࡰࡧࡣࡩࡧࡴࡢ࠼ࠣࡒࡴࡺࠠࡢࡦࡧ࡭ࡳ࡭ࠠࡥࡣࡷࡥࠥࡽࡩࡵࡪࠣࡩࡻ࡫࡮ࡵࡡࡷࡽࡵ࡫࠺ࠡࡽࢀࠦⅾ").format(bstack1111l1lll1_opy_[bstack111l1ll_opy_ (u"ࠧࡦࡸࡨࡲࡹࡥࡴࡺࡲࡨࠫⅿ")]))
            return
        bstack1l11111ll_opy_ = bstack11ll1lll_opy_.bstack1llll11l1l11_opy_(bstack1111l1lll1_opy_[bstack111l1ll_opy_ (u"ࠨࡧࡹࡩࡳࡺ࡟ࡵࡻࡳࡩࠬↀ")], bstack1111l1lll1_opy_.get(bstack111l1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡳࡷࡱࠫↁ")))
        if bstack1l11111ll_opy_ != None:
            if bstack1111l1lll1_opy_.get(bstack111l1ll_opy_ (u"ࠪࡸࡪࡹࡴࡠࡴࡸࡲࠬↂ")) != None:
                bstack1111l1lll1_opy_[bstack111l1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡡࡵࡹࡳ࠭Ↄ")][bstack111l1ll_opy_ (u"ࠬࡶࡲࡰࡦࡸࡧࡹࡥ࡭ࡢࡲࠪↄ")] = bstack1l11111ll_opy_
            else:
                bstack1111l1lll1_opy_[bstack111l1ll_opy_ (u"࠭ࡰࡳࡱࡧࡹࡨࡺ࡟࡮ࡣࡳࠫↅ")] = bstack1l11111ll_opy_
        if event_url == bstack111l1ll_opy_ (u"ࠧࡢࡲ࡬࠳ࡻ࠷࠯ࡣࡣࡷࡧ࡭࠭ↆ"):
            cls.bstack1llll111lll1_opy_()
            logger.debug(bstack111l1ll_opy_ (u"ࠣࡵࡨࡲࡩࡥࡤࡢࡶࡤ࠾ࠥࡇࡤࡥ࡫ࡱ࡫ࠥࡪࡡࡵࡣࠣࡸࡴࠦࡢࡢࡶࡦ࡬ࠥࡽࡩࡵࡪࠣࡩࡻ࡫࡮ࡵࡡࡷࡽࡵ࡫࠺ࠡࡽࢀࠦↇ").format(bstack1111l1lll1_opy_[bstack111l1ll_opy_ (u"ࠩࡨࡺࡪࡴࡴࡠࡶࡼࡴࡪ࠭ↈ")]))
            cls.bstack1llllll111ll_opy_.add(bstack1111l1lll1_opy_)
        elif event_url == bstack111l1ll_opy_ (u"ࠪࡥࡵ࡯࠯ࡷ࠳࠲ࡷࡨࡸࡥࡦࡰࡶ࡬ࡴࡺࡳࠨ↉"):
            cls.bstack1llll1l111l1_opy_([bstack1111l1lll1_opy_], event_url)
    @classmethod
    @error_handler(class_method=True)
    def bstack1l11l1ll1_opy_(cls, logs):
        for log in logs:
            bstack1llll11lll11_opy_ = {
                bstack111l1ll_opy_ (u"ࠫࡰ࡯࡮ࡥࠩ↊"): bstack111l1ll_opy_ (u"࡚ࠬࡅࡔࡖࡢࡐࡔࡍࠧ↋"),
                bstack111l1ll_opy_ (u"࠭࡬ࡦࡸࡨࡰࠬ↌"): log[bstack111l1ll_opy_ (u"ࠧ࡭ࡧࡹࡩࡱ࠭↍")],
                bstack111l1ll_opy_ (u"ࠨࡶ࡬ࡱࡪࡹࡴࡢ࡯ࡳࠫ↎"): log[bstack111l1ll_opy_ (u"ࠩࡷ࡭ࡲ࡫ࡳࡵࡣࡰࡴࠬ↏")],
                bstack111l1ll_opy_ (u"ࠪ࡬ࡹࡺࡰࡠࡴࡨࡷࡵࡵ࡮ࡴࡧࠪ←"): {},
                bstack111l1ll_opy_ (u"ࠫࡲ࡫ࡳࡴࡣࡪࡩࠬ↑"): log[bstack111l1ll_opy_ (u"ࠬࡳࡥࡴࡵࡤ࡫ࡪ࠭→")],
            }
            if bstack111l1ll_opy_ (u"࠭ࡴࡦࡵࡷࡣࡷࡻ࡮ࡠࡷࡸ࡭ࡩ࠭↓") in log:
                bstack1llll11lll11_opy_[bstack111l1ll_opy_ (u"ࠧࡵࡧࡶࡸࡤࡸࡵ࡯ࡡࡸࡹ࡮ࡪࠧ↔")] = log[bstack111l1ll_opy_ (u"ࠨࡶࡨࡷࡹࡥࡲࡶࡰࡢࡹࡺ࡯ࡤࠨ↕")]
            elif bstack111l1ll_opy_ (u"ࠩ࡫ࡳࡴࡱ࡟ࡳࡷࡱࡣࡺࡻࡩࡥࠩ↖") in log:
                bstack1llll11lll11_opy_[bstack111l1ll_opy_ (u"ࠪ࡬ࡴࡵ࡫ࡠࡴࡸࡲࡤࡻࡵࡪࡦࠪ↗")] = log[bstack111l1ll_opy_ (u"ࠫ࡭ࡵ࡯࡬ࡡࡵࡹࡳࡥࡵࡶ࡫ࡧࠫ↘")]
            cls.bstack1l111ll11l_opy_({
                bstack111l1ll_opy_ (u"ࠬ࡫ࡶࡦࡰࡷࡣࡹࡿࡰࡦࠩ↙"): bstack111l1ll_opy_ (u"࠭ࡌࡰࡩࡆࡶࡪࡧࡴࡦࡦࠪ↚"),
                bstack111l1ll_opy_ (u"ࠧ࡭ࡱࡪࡷࠬ↛"): [bstack1llll11lll11_opy_]
            })
    @classmethod
    @error_handler(class_method=True)
    def bstack1llll11lll1l_opy_(cls, steps):
        bstack1llll1l1111l_opy_ = []
        for step in steps:
            bstack1llll1l111ll_opy_ = {
                bstack111l1ll_opy_ (u"ࠨ࡭࡬ࡲࡩ࠭↜"): bstack111l1ll_opy_ (u"ࠩࡗࡉࡘ࡚࡟ࡔࡖࡈࡔࠬ↝"),
                bstack111l1ll_opy_ (u"ࠪࡰࡪࡼࡥ࡭ࠩ↞"): step[bstack111l1ll_opy_ (u"ࠫࡱ࡫ࡶࡦ࡮ࠪ↟")],
                bstack111l1ll_opy_ (u"ࠬࡺࡩ࡮ࡧࡶࡸࡦࡳࡰࠨ↠"): step[bstack111l1ll_opy_ (u"࠭ࡴࡪ࡯ࡨࡷࡹࡧ࡭ࡱࠩ↡")],
                bstack111l1ll_opy_ (u"ࠧ࡮ࡧࡶࡷࡦ࡭ࡥࠨ↢"): step[bstack111l1ll_opy_ (u"ࠨ࡯ࡨࡷࡸࡧࡧࡦࠩ↣")],
                bstack111l1ll_opy_ (u"ࠩࡧࡹࡷࡧࡴࡪࡱࡱࠫ↤"): step[bstack111l1ll_opy_ (u"ࠪࡨࡺࡸࡡࡵ࡫ࡲࡲࠬ↥")]
            }
            if bstack111l1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡡࡵࡹࡳࡥࡵࡶ࡫ࡧࠫ↦") in step:
                bstack1llll1l111ll_opy_[bstack111l1ll_opy_ (u"ࠬࡺࡥࡴࡶࡢࡶࡺࡴ࡟ࡶࡷ࡬ࡨࠬ↧")] = step[bstack111l1ll_opy_ (u"࠭ࡴࡦࡵࡷࡣࡷࡻ࡮ࡠࡷࡸ࡭ࡩ࠭↨")]
            elif bstack111l1ll_opy_ (u"ࠧࡩࡱࡲ࡯ࡤࡸࡵ࡯ࡡࡸࡹ࡮ࡪࠧ↩") in step:
                bstack1llll1l111ll_opy_[bstack111l1ll_opy_ (u"ࠨࡪࡲࡳࡰࡥࡲࡶࡰࡢࡹࡺ࡯ࡤࠨ↪")] = step[bstack111l1ll_opy_ (u"ࠩ࡫ࡳࡴࡱ࡟ࡳࡷࡱࡣࡺࡻࡩࡥࠩ↫")]
            bstack1llll1l1111l_opy_.append(bstack1llll1l111ll_opy_)
        cls.bstack1l111ll11l_opy_({
            bstack111l1ll_opy_ (u"ࠪࡩࡻ࡫࡮ࡵࡡࡷࡽࡵ࡫ࠧ↬"): bstack111l1ll_opy_ (u"ࠫࡑࡵࡧࡄࡴࡨࡥࡹ࡫ࡤࠨ↭"),
            bstack111l1ll_opy_ (u"ࠬࡲ࡯ࡨࡵࠪ↮"): bstack1llll1l1111l_opy_
        })
    @classmethod
    @error_handler(class_method=True)
    @measure(event_name=EVENTS.bstack11lllll11l_opy_, stage=STAGE.bstack1l11lllll1_opy_)
    def bstack1lll111l1l_opy_(cls, screenshot):
        cls.bstack1l111ll11l_opy_({
            bstack111l1ll_opy_ (u"࠭ࡥࡷࡧࡱࡸࡤࡺࡹࡱࡧࠪ↯"): bstack111l1ll_opy_ (u"ࠧࡍࡱࡪࡇࡷ࡫ࡡࡵࡧࡧࠫ↰"),
            bstack111l1ll_opy_ (u"ࠨ࡮ࡲ࡫ࡸ࠭↱"): [{
                bstack111l1ll_opy_ (u"ࠩ࡮࡭ࡳࡪࠧ↲"): bstack111l1ll_opy_ (u"ࠪࡘࡊ࡙ࡔࡠࡕࡆࡖࡊࡋࡎࡔࡊࡒࡘࠬ↳"),
                bstack111l1ll_opy_ (u"ࠫࡹ࡯࡭ࡦࡵࡷࡥࡲࡶࠧ↴"): datetime.datetime.utcnow().isoformat() + bstack111l1ll_opy_ (u"ࠬࡠࠧ↵"),
                bstack111l1ll_opy_ (u"࠭࡭ࡦࡵࡶࡥ࡬࡫ࠧ↶"): screenshot[bstack111l1ll_opy_ (u"ࠧࡪ࡯ࡤ࡫ࡪ࠭↷")],
                bstack111l1ll_opy_ (u"ࠨࡶࡨࡷࡹࡥࡲࡶࡰࡢࡹࡺ࡯ࡤࠨ↸"): screenshot[bstack111l1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡳࡷࡱࡣࡺࡻࡩࡥࠩ↹")]
            }]
        }, event_url=bstack111l1ll_opy_ (u"ࠪࡥࡵ࡯࠯ࡷ࠳࠲ࡷࡨࡸࡥࡦࡰࡶ࡬ࡴࡺࡳࠨ↺"))
    @classmethod
    @error_handler(class_method=True)
    def bstack1ll1l1ll11_opy_(cls, driver):
        current_test_uuid = cls.current_test_uuid()
        if not current_test_uuid:
            return
        cls.bstack1l111ll11l_opy_({
            bstack111l1ll_opy_ (u"ࠫࡪࡼࡥ࡯ࡶࡢࡸࡾࡶࡥࠨ↻"): bstack111l1ll_opy_ (u"ࠬࡉࡂࡕࡕࡨࡷࡸ࡯࡯࡯ࡅࡵࡩࡦࡺࡥࡥࠩ↼"),
            bstack111l1ll_opy_ (u"࠭ࡴࡦࡵࡷࡣࡷࡻ࡮ࠨ↽"): {
                bstack111l1ll_opy_ (u"ࠢࡶࡷ࡬ࡨࠧ↾"): cls.current_test_uuid(),
                bstack111l1ll_opy_ (u"ࠣ࡫ࡱࡸࡪ࡭ࡲࡢࡶ࡬ࡳࡳࡹࠢ↿"): cls.bstack111ll1l11l_opy_(driver)
            }
        })
    @classmethod
    def bstack111lll1111_opy_(cls, event: str, bstack1111l1lll1_opy_: bstack111l111111_opy_):
        bstack111l1l1ll1_opy_ = {
            bstack111l1ll_opy_ (u"ࠩࡨࡺࡪࡴࡴࡠࡶࡼࡴࡪ࠭⇀"): event,
            bstack1111l1lll1_opy_.bstack1111l1ll1l_opy_(): bstack1111l1lll1_opy_.bstack111l11ll11_opy_(event)
        }
        cls.bstack1l111ll11l_opy_(bstack111l1l1ll1_opy_)
        result = getattr(bstack1111l1lll1_opy_, bstack111l1ll_opy_ (u"ࠪࡶࡪࡹࡵ࡭ࡶࠪ⇁"), None)
        if event == bstack111l1ll_opy_ (u"࡙ࠫ࡫ࡳࡵࡔࡸࡲࡘࡺࡡࡳࡶࡨࡨࠬ⇂"):
            threading.current_thread().bstackTestMeta = {bstack111l1ll_opy_ (u"ࠬࡹࡴࡢࡶࡸࡷࠬ⇃"): bstack111l1ll_opy_ (u"࠭ࡰࡦࡰࡧ࡭ࡳ࡭ࠧ⇄")}
        elif event == bstack111l1ll_opy_ (u"ࠧࡕࡧࡶࡸࡗࡻ࡮ࡇ࡫ࡱ࡭ࡸ࡮ࡥࡥࠩ⇅"):
            threading.current_thread().bstackTestMeta = {bstack111l1ll_opy_ (u"ࠨࡵࡷࡥࡹࡻࡳࠨ⇆"): getattr(result, bstack111l1ll_opy_ (u"ࠩࡵࡩࡸࡻ࡬ࡵࠩ⇇"), bstack111l1ll_opy_ (u"ࠪࠫ⇈"))}
    @classmethod
    def on(cls):
        if (os.environ.get(bstack111l1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡘࡊ࡙ࡔࡉࡗࡅࡣࡏ࡝ࡔࠨ⇉"), None) is None or os.environ[bstack111l1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡊࡘࡆࡤࡐࡗࡕࠩ⇊")] == bstack111l1ll_opy_ (u"ࠨ࡮ࡶ࡮࡯ࠦ⇋")) and (os.environ.get(bstack111l1ll_opy_ (u"ࠧࡃࡕࡢࡅ࠶࠷࡙ࡠࡌ࡚ࡘࠬ⇌"), None) is None or os.environ[bstack111l1ll_opy_ (u"ࠨࡄࡖࡣࡆ࠷࠱࡚ࡡࡍ࡛࡙࠭⇍")] == bstack111l1ll_opy_ (u"ࠤࡱࡹࡱࡲࠢ⇎")):
            return False
        return True
    @staticmethod
    def bstack1llll11ll1l1_opy_(func):
        def wrap(*args, **kwargs):
            if bstack111111l1l_opy_.on():
                return func(*args, **kwargs)
            return
        return wrap
    @staticmethod
    def default_headers():
        headers = {
            bstack111l1ll_opy_ (u"ࠪࡇࡴࡴࡴࡦࡰࡷ࠱࡙ࡿࡰࡦࠩ⇏"): bstack111l1ll_opy_ (u"ࠫࡦࡶࡰ࡭࡫ࡦࡥࡹ࡯࡯࡯࠱࡭ࡷࡴࡴࠧ⇐"),
            bstack111l1ll_opy_ (u"ࠬ࡞࠭ࡃࡕࡗࡅࡈࡑ࠭ࡕࡇࡖࡘࡔࡖࡓࠨ⇑"): bstack111l1ll_opy_ (u"࠭ࡴࡳࡷࡨࠫ⇒")
        }
        if os.environ.get(bstack111l1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡋ࡙ࡗࠫ⇓"), None):
            headers[bstack111l1ll_opy_ (u"ࠨࡃࡸࡸ࡭ࡵࡲࡪࡼࡤࡸ࡮ࡵ࡮ࠨ⇔")] = bstack111l1ll_opy_ (u"ࠩࡅࡩࡦࡸࡥࡳࠢࡾࢁࠬ⇕").format(os.environ[bstack111l1ll_opy_ (u"ࠥࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡗࡉࡘ࡚ࡈࡖࡄࡢࡎ࡜࡚ࠢ⇖")])
        return headers
    @staticmethod
    def request_url(url):
        return bstack111l1ll_opy_ (u"ࠫࢀࢃ࠯ࡼࡿࠪ⇗").format(bstack1llll111ll1l_opy_, url)
    @staticmethod
    def current_test_uuid():
        return getattr(threading.current_thread(), bstack111l1ll_opy_ (u"ࠬࡩࡵࡳࡴࡨࡲࡹࡥࡴࡦࡵࡷࡣࡺࡻࡩࡥࠩ⇘"), None)
    @staticmethod
    def bstack111ll1l11l_opy_(driver):
        return {
            bstack11l11l11111_opy_(): bstack111llll1ll1_opy_(driver)
        }
    @staticmethod
    def bstack1llll11l1l1l_opy_(exception_info, report):
        return [{bstack111l1ll_opy_ (u"࠭ࡢࡢࡥ࡮ࡸࡷࡧࡣࡦࠩ⇙"): [exception_info.exconly(), report.longreprtext]}]
    @staticmethod
    def bstack1111111ll1_opy_(typename):
        if bstack111l1ll_opy_ (u"ࠢࡂࡵࡶࡩࡷࡺࡩࡰࡰࠥ⇚") in typename:
            return bstack111l1ll_opy_ (u"ࠣࡃࡶࡷࡪࡸࡴࡪࡱࡱࡉࡷࡸ࡯ࡳࠤ⇛")
        return bstack111l1ll_opy_ (u"ࠤࡘࡲ࡭ࡧ࡮ࡥ࡮ࡨࡨࡊࡸࡲࡰࡴࠥ⇜")