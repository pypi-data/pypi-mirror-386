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
import requests
from urllib.parse import urljoin, urlencode
from datetime import datetime
import os
import logging
import json
from bstack_utils.constants import bstack11l1ll1l1ll_opy_
logger = logging.getLogger(__name__)
class bstack11ll1111ll1_opy_:
    @staticmethod
    def results(builder,params=None):
        bstack1lllll1ll111_opy_ = urljoin(builder, bstack111l1ll_opy_ (u"ࠧࡪࡵࡶࡹࡪࡹࠧΊ"))
        if params:
            bstack1lllll1ll111_opy_ += bstack111l1ll_opy_ (u"ࠣࡁࡾࢁࠧ῜").format(urlencode({bstack111l1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡳࡷࡱࡣࡺࡻࡩࡥࠩ῝"): params.get(bstack111l1ll_opy_ (u"ࠪࡸࡪࡹࡴࡠࡴࡸࡲࡤࡻࡵࡪࡦࠪ῞"))}))
        return bstack11ll1111ll1_opy_.bstack1lllll1l1lll_opy_(bstack1lllll1ll111_opy_)
    @staticmethod
    def bstack11ll1111l1l_opy_(builder,params=None):
        bstack1lllll1ll111_opy_ = urljoin(builder, bstack111l1ll_opy_ (u"ࠫ࡮ࡹࡳࡶࡧࡶ࠱ࡸࡻ࡭࡮ࡣࡵࡽࠬ῟"))
        if params:
            bstack1lllll1ll111_opy_ += bstack111l1ll_opy_ (u"ࠧࡅࡻࡾࠤῠ").format(urlencode({bstack111l1ll_opy_ (u"࠭ࡴࡦࡵࡷࡣࡷࡻ࡮ࡠࡷࡸ࡭ࡩ࠭ῡ"): params.get(bstack111l1ll_opy_ (u"ࠧࡵࡧࡶࡸࡤࡸࡵ࡯ࡡࡸࡹ࡮ࡪࠧῢ"))}))
        return bstack11ll1111ll1_opy_.bstack1lllll1l1lll_opy_(bstack1lllll1ll111_opy_)
    @staticmethod
    def bstack1lllll1l1lll_opy_(bstack1lllll11llll_opy_):
        bstack1lllll1l1l11_opy_ = os.environ.get(bstack111l1ll_opy_ (u"ࠨࡄࡖࡣࡆ࠷࠱࡚ࡡࡍ࡛࡙࠭ΰ"), os.environ.get(bstack111l1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡎࡕࡃࡡࡍ࡛࡙࠭ῤ"), bstack111l1ll_opy_ (u"ࠪࠫῥ")))
        headers = {bstack111l1ll_opy_ (u"ࠫࡆࡻࡴࡩࡱࡵ࡭ࡿࡧࡴࡪࡱࡱࠫῦ"): bstack111l1ll_opy_ (u"ࠬࡈࡥࡢࡴࡨࡶࠥࢁࡽࠨῧ").format(bstack1lllll1l1l11_opy_)}
        response = requests.get(bstack1lllll11llll_opy_, headers=headers)
        bstack1lllll1l11l1_opy_ = {}
        try:
            bstack1lllll1l11l1_opy_ = response.json()
        except Exception as e:
            logger.debug(bstack111l1ll_opy_ (u"ࠨࡆࡢ࡫࡯ࡩࡩࠦࡴࡰࠢࡳࡥࡷࡹࡥࠡࡌࡖࡓࡓࠦࡲࡦࡵࡳࡳࡳࡹࡥ࠻ࠢࡾࢁࠧῨ").format(e))
            pass
        if bstack1lllll1l11l1_opy_ is not None:
            bstack1lllll1l11l1_opy_[bstack111l1ll_opy_ (u"ࠧ࡯ࡧࡻࡸࡤࡶ࡯࡭࡮ࡢࡸ࡮ࡳࡥࠨῩ")] = response.headers.get(bstack111l1ll_opy_ (u"ࠨࡰࡨࡼࡹࡥࡰࡰ࡮࡯ࡣࡹ࡯࡭ࡦࠩῪ"), str(int(datetime.now().timestamp() * 1000)))
            bstack1lllll1l11l1_opy_[bstack111l1ll_opy_ (u"ࠩࡶࡸࡦࡺࡵࡴࠩΎ")] = response.status_code
        return bstack1lllll1l11l1_opy_
    @staticmethod
    def bstack1lllll1l1ll1_opy_(bstack1lllll1l11ll_opy_, data):
        logger.debug(bstack111l1ll_opy_ (u"ࠥࡔࡷࡵࡣࡦࡵࡶ࡭ࡳ࡭ࠠࡓࡧࡴࡹࡪࡹࡴࠡࡨࡲࡶࠥࡺࡥࡴࡶࡒࡶࡨ࡮ࡥࡴࡶࡵࡥࡹ࡯࡯࡯ࡕࡳࡰ࡮ࡺࡔࡦࡵࡷࡷࠧῬ"))
        return bstack11ll1111ll1_opy_.bstack1lllll1l111l_opy_(bstack111l1ll_opy_ (u"ࠫࡕࡕࡓࡕࠩ῭"), bstack1lllll1l11ll_opy_, data=data)
    @staticmethod
    def bstack1lllll1l1111_opy_(bstack1lllll1l11ll_opy_, data):
        logger.debug(bstack111l1ll_opy_ (u"ࠧࡖࡲࡰࡥࡨࡷࡸ࡯࡮ࡨࠢࡕࡩࡶࡻࡥࡴࡶࠣࡪࡴࡸࠠࡨࡧࡷࡘࡪࡹࡴࡐࡴࡦ࡬ࡪࡹࡴࡳࡣࡷ࡭ࡴࡴࡏࡳࡦࡨࡶࡪࡪࡔࡦࡵࡷࡷࠧ΅"))
        res = bstack11ll1111ll1_opy_.bstack1lllll1l111l_opy_(bstack111l1ll_opy_ (u"࠭ࡇࡆࡖࠪ`"), bstack1lllll1l11ll_opy_, data=data)
        return res
    @staticmethod
    def bstack1lllll1l111l_opy_(method, bstack1lllll1l11ll_opy_, data=None, params=None, extra_headers=None):
        bstack1lllll1l1l11_opy_ = os.environ.get(bstack111l1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡋ࡙ࡗࠫ῰"), bstack111l1ll_opy_ (u"ࠨࠩ῱"))
        headers = {
            bstack111l1ll_opy_ (u"ࠩࡤࡹࡹ࡮࡯ࡳ࡫ࡽࡥࡹ࡯࡯࡯ࠩῲ"): bstack111l1ll_opy_ (u"ࠪࡆࡪࡧࡲࡦࡴࠣࡿࢂ࠭ῳ").format(bstack1lllll1l1l11_opy_),
            bstack111l1ll_opy_ (u"ࠫࡈࡵ࡮ࡵࡧࡱࡸ࠲࡚ࡹࡱࡧࠪῴ"): bstack111l1ll_opy_ (u"ࠬࡧࡰࡱ࡮࡬ࡧࡦࡺࡩࡰࡰ࠲࡮ࡸࡵ࡮ࠨ῵"),
            bstack111l1ll_opy_ (u"࠭ࡁࡤࡥࡨࡴࡹ࠭ῶ"): bstack111l1ll_opy_ (u"ࠧࡢࡲࡳࡰ࡮ࡩࡡࡵ࡫ࡲࡲ࠴ࡰࡳࡰࡰࠪῷ")
        }
        if extra_headers:
            headers.update(extra_headers)
        url = bstack11l1ll1l1ll_opy_ + bstack111l1ll_opy_ (u"ࠣ࠱ࠥῸ") + bstack1lllll1l11ll_opy_.lstrip(bstack111l1ll_opy_ (u"ࠩ࠲ࠫΌ"))
        try:
            if method == bstack111l1ll_opy_ (u"ࠪࡋࡊ࡚ࠧῺ"):
                response = requests.get(url, headers=headers, params=params, json=data)
            elif method == bstack111l1ll_opy_ (u"ࠫࡕࡕࡓࡕࠩΏ"):
                response = requests.post(url, headers=headers, json=data)
            elif method == bstack111l1ll_opy_ (u"ࠬࡖࡕࡕࠩῼ"):
                response = requests.put(url, headers=headers, json=data)
            else:
                raise ValueError(bstack111l1ll_opy_ (u"ࠨࡕ࡯ࡵࡸࡴࡵࡵࡲࡵࡧࡧࠤࡍ࡚ࡔࡑࠢࡰࡩࡹ࡮࡯ࡥ࠼ࠣࡿࢂࠨ´").format(method))
            logger.debug(bstack111l1ll_opy_ (u"ࠢࡐࡴࡦ࡬ࡪࡹࡴࡳࡣࡷ࡭ࡴࡴࠠࡳࡧࡴࡹࡪࡹࡴࠡ࡯ࡤࡨࡪࠦࡴࡰࠢࡘࡖࡑࡀࠠࡼࡿࠣࡻ࡮ࡺࡨࠡ࡯ࡨࡸ࡭ࡵࡤ࠻ࠢࡾࢁࠧ῾").format(url, method))
            bstack1lllll1l11l1_opy_ = {}
            try:
                bstack1lllll1l11l1_opy_ = response.json()
            except Exception as e:
                logger.debug(bstack111l1ll_opy_ (u"ࠣࡈࡤ࡭ࡱ࡫ࡤࠡࡶࡲࠤࡵࡧࡲࡴࡧࠣࡎࡘࡕࡎࠡࡴࡨࡷࡵࡵ࡮ࡴࡧ࠽ࠤࢀࢃࠠ࠮ࠢࡾࢁࠧ῿").format(e, response.text))
            if bstack1lllll1l11l1_opy_ is not None:
                bstack1lllll1l11l1_opy_[bstack111l1ll_opy_ (u"ࠩࡱࡩࡽࡺ࡟ࡱࡱ࡯ࡰࡤࡺࡩ࡮ࡧࠪ ")] = response.headers.get(
                    bstack111l1ll_opy_ (u"ࠪࡲࡪࡾࡴࡠࡲࡲࡰࡱࡥࡴࡪ࡯ࡨࠫ "), str(int(datetime.now().timestamp() * 1000))
                )
                bstack1lllll1l11l1_opy_[bstack111l1ll_opy_ (u"ࠫࡸࡺࡡࡵࡷࡶࠫ ")] = response.status_code
            return bstack1lllll1l11l1_opy_
        except Exception as e:
            logger.error(bstack111l1ll_opy_ (u"ࠧࡕࡲࡤࡪࡨࡷࡹࡸࡡࡵ࡫ࡲࡲࠥࡸࡥࡲࡷࡨࡷࡹࠦࡦࡢ࡫࡯ࡩࡩࡀࠠࡼࡿࠣ࠱ࠥࢁࡽࠣ ").format(e, url))
            return None
    @staticmethod
    def bstack11l1l111l1l_opy_(bstack1lllll11llll_opy_, data):
        bstack111l1ll_opy_ (u"ࠨࠢࠣࠌࠣࠤࠥࠦࠠࠡࠢࠣࡗࡪࡴࡤࡴࠢࡤࠤࡕ࡛ࡔࠡࡴࡨࡵࡺ࡫ࡳࡵࠢࡷࡳࠥࡹࡴࡰࡴࡨࠤࡹ࡮ࡥࠡࡨࡤ࡭ࡱ࡫ࡤࠡࡶࡨࡷࡹࡹࠊࠡࠢࠣࠤࠥࠦࠠࠡࠤࠥࠦ ")
        bstack1lllll1l1l11_opy_ = os.environ.get(bstack111l1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡋ࡙ࡗࠫ "), bstack111l1ll_opy_ (u"ࠨࠩ "))
        headers = {
            bstack111l1ll_opy_ (u"ࠩࡤࡹࡹ࡮࡯ࡳ࡫ࡽࡥࡹ࡯࡯࡯ࠩ "): bstack111l1ll_opy_ (u"ࠪࡆࡪࡧࡲࡦࡴࠣࡿࢂ࠭ ").format(bstack1lllll1l1l11_opy_),
            bstack111l1ll_opy_ (u"ࠫࡈࡵ࡮ࡵࡧࡱࡸ࠲࡚ࡹࡱࡧࠪ "): bstack111l1ll_opy_ (u"ࠬࡧࡰࡱ࡮࡬ࡧࡦࡺࡩࡰࡰ࠲࡮ࡸࡵ࡮ࠨ ")
        }
        response = requests.put(bstack1lllll11llll_opy_, headers=headers, json=data)
        bstack1lllll1l11l1_opy_ = {}
        try:
            bstack1lllll1l11l1_opy_ = response.json()
        except Exception as e:
            logger.debug(bstack111l1ll_opy_ (u"ࠨࡆࡢ࡫࡯ࡩࡩࠦࡴࡰࠢࡳࡥࡷࡹࡥࠡࡌࡖࡓࡓࠦࡲࡦࡵࡳࡳࡳࡹࡥ࠻ࠢࡾࢁࠧ​").format(e))
            pass
        logger.debug(bstack111l1ll_opy_ (u"ࠢࡓࡧࡴࡹࡪࡹࡴࡖࡶ࡬ࡰࡸࡀࠠࡱࡷࡷࡣ࡫ࡧࡩ࡭ࡧࡧࡣࡹ࡫ࡳࡵࡵࠣࡶࡪࡹࡰࡰࡰࡶࡩ࠿ࠦࡻࡾࠤ‌").format(bstack1lllll1l11l1_opy_))
        if bstack1lllll1l11l1_opy_ is not None:
            bstack1lllll1l11l1_opy_[bstack111l1ll_opy_ (u"ࠨࡰࡨࡼࡹࡥࡰࡰ࡮࡯ࡣࡹ࡯࡭ࡦࠩ‍")] = response.headers.get(
                bstack111l1ll_opy_ (u"ࠩࡱࡩࡽࡺ࡟ࡱࡱ࡯ࡰࡤࡺࡩ࡮ࡧࠪ‎"), str(int(datetime.now().timestamp() * 1000))
            )
            bstack1lllll1l11l1_opy_[bstack111l1ll_opy_ (u"ࠪࡷࡹࡧࡴࡶࡵࠪ‏")] = response.status_code
        return bstack1lllll1l11l1_opy_
    @staticmethod
    def bstack11l1l111ll1_opy_(bstack1lllll11llll_opy_):
        bstack111l1ll_opy_ (u"ࠦࠧࠨࠊࠡࠢࠣࠤࠥࠦࠠࠡࡕࡨࡲࡩࡹࠠࡢࠢࡊࡉ࡙ࠦࡲࡦࡳࡸࡩࡸࡺࠠࡵࡱࠣ࡫ࡪࡺࠠࡵࡪࡨࠤࡨࡵࡵ࡯ࡶࠣࡳ࡫ࠦࡦࡢ࡫࡯ࡩࡩࠦࡴࡦࡵࡷࡷࠏࠦࠠࠡࠢࠣࠤࠥࠦࠢࠣࠤ‐")
        bstack1lllll1l1l11_opy_ = os.environ.get(bstack111l1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡊࡘࡆࡤࡐࡗࡕࠩ‑"), bstack111l1ll_opy_ (u"࠭ࠧ‒"))
        headers = {
            bstack111l1ll_opy_ (u"ࠧࡢࡷࡷ࡬ࡴࡸࡩࡻࡣࡷ࡭ࡴࡴࠧ–"): bstack111l1ll_opy_ (u"ࠨࡄࡨࡥࡷ࡫ࡲࠡࡽࢀࠫ—").format(bstack1lllll1l1l11_opy_),
            bstack111l1ll_opy_ (u"ࠩࡆࡳࡳࡺࡥ࡯ࡶ࠰ࡘࡾࡶࡥࠨ―"): bstack111l1ll_opy_ (u"ࠪࡥࡵࡶ࡬ࡪࡥࡤࡸ࡮ࡵ࡮࠰࡬ࡶࡳࡳ࠭‖")
        }
        response = requests.get(bstack1lllll11llll_opy_, headers=headers)
        bstack1lllll1l11l1_opy_ = {}
        try:
            bstack1lllll1l11l1_opy_ = response.json()
            logger.debug(bstack111l1ll_opy_ (u"ࠦࡗ࡫ࡱࡶࡧࡶࡸ࡚ࡺࡩ࡭ࡵ࠽ࠤ࡬࡫ࡴࡠࡨࡤ࡭ࡱ࡫ࡤࡠࡶࡨࡷࡹࡹࠠࡳࡧࡶࡴࡴࡴࡳࡦ࠼ࠣࡿࢂࠨ‗").format(bstack1lllll1l11l1_opy_))
        except Exception as e:
            logger.debug(bstack111l1ll_opy_ (u"ࠧࡌࡡࡪ࡮ࡨࡨࠥࡺ࡯ࠡࡲࡤࡶࡸ࡫ࠠࡋࡕࡒࡒࠥࡸࡥࡴࡲࡲࡲࡸ࡫࠺ࠡࡽࢀࠤ࠲ࠦࡻࡾࠤ‘").format(e, response.text))
            pass
        if bstack1lllll1l11l1_opy_ is not None:
            bstack1lllll1l11l1_opy_[bstack111l1ll_opy_ (u"࠭࡮ࡦࡺࡷࡣࡵࡵ࡬࡭ࡡࡷ࡭ࡲ࡫ࠧ’")] = response.headers.get(
                bstack111l1ll_opy_ (u"ࠧ࡯ࡧࡻࡸࡤࡶ࡯࡭࡮ࡢࡸ࡮ࡳࡥࠨ‚"), str(int(datetime.now().timestamp() * 1000))
            )
            bstack1lllll1l11l1_opy_[bstack111l1ll_opy_ (u"ࠨࡵࡷࡥࡹࡻࡳࠨ‛")] = response.status_code
        return bstack1lllll1l11l1_opy_
    @staticmethod
    def bstack1111llll1ll_opy_(bstack11ll111ll11_opy_, payload):
        bstack111l1ll_opy_ (u"ࠤࠥࠦࠏࠦࠠࠡࠢࠣࠤࠥࠦࡍࡢ࡭ࡨࡷࠥࡧࠠࡑࡑࡖࡘࠥࡸࡥࡲࡷࡨࡷࡹࠦࡴࡰࠢࡷ࡬ࡪࠦࡣࡰ࡮࡯ࡩࡨࡺ࠭ࡣࡷ࡬ࡰࡩ࠳ࡤࡢࡶࡤࠤࡪࡴࡤࡱࡱ࡬ࡲࡹ࠴ࠊࠡࠢࠣࠤࠥࠦࠠࠡࡃࡵ࡫ࡸࡀࠊࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥ࡫࡮ࡥࡲࡲ࡭ࡳࡺࠠࠩࡵࡷࡶ࠮ࡀࠠࡕࡪࡨࠤࡆࡖࡉࠡࡧࡱࡨࡵࡵࡩ࡯ࡶࠣࡴࡦࡺࡨ࠯ࠌࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࡱࡣࡼࡰࡴࡧࡤࠡࠪࡧ࡭ࡨࡺࠩ࠻ࠢࡗ࡬ࡪࠦࡲࡦࡳࡸࡩࡸࡺࠠࡱࡣࡼࡰࡴࡧࡤ࠯ࠌࠣࠤࠥࠦࠠࠡࠢࠣࡖࡪࡺࡵࡳࡰࡶ࠾ࠏࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࡨ࡮ࡩࡴ࠻ࠢࡕࡩࡸࡶ࡯࡯ࡵࡨࠤ࡫ࡸ࡯࡮ࠢࡷ࡬ࡪࠦࡁࡑࡋ࠯ࠤࡴࡸࠠࡏࡱࡱࡩࠥ࡯ࡦࠡࡨࡤ࡭ࡱ࡫ࡤ࠯ࠌࠣࠤࠥࠦࠠࠡࠢࠣࠦࠧࠨ“")
        try:
            url = bstack111l1ll_opy_ (u"ࠥࡿࢂ࠵ࡻࡾࠤ”").format(bstack11l1ll1l1ll_opy_, bstack11ll111ll11_opy_)
            bstack1lllll1l1l11_opy_ = os.environ.get(bstack111l1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡘࡊ࡙ࡔࡉࡗࡅࡣࡏ࡝ࡔࠨ„"), bstack111l1ll_opy_ (u"ࠬ࠭‟"))
            headers = {
                bstack111l1ll_opy_ (u"࠭ࡡࡶࡶ࡫ࡳࡷ࡯ࡺࡢࡶ࡬ࡳࡳ࠭†"): bstack111l1ll_opy_ (u"ࠧࡃࡧࡤࡶࡪࡸࠠࡼࡿࠪ‡").format(bstack1lllll1l1l11_opy_),
                bstack111l1ll_opy_ (u"ࠨࡅࡲࡲࡹ࡫࡮ࡵ࠯ࡗࡽࡵ࡫ࠧ•"): bstack111l1ll_opy_ (u"ࠩࡤࡴࡵࡲࡩࡤࡣࡷ࡭ࡴࡴ࠯࡫ࡵࡲࡲࠬ‣")
            }
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            bstack1lllll1l1l1l_opy_ = [200, 202]
            if response.status_code in bstack1lllll1l1l1l_opy_:
                return response.json()
            else:
                logger.error(bstack111l1ll_opy_ (u"ࠥࡊࡦ࡯࡬ࡦࡦࠣࡸࡴࠦࡣࡰ࡮࡯ࡩࡨࡺࠠࡣࡷ࡬ࡰࡩࠦࡤࡢࡶࡤ࠲࡙ࠥࡴࡢࡶࡸࡷ࠿ࠦࡻࡾ࠮ࠣࡖࡪࡹࡰࡰࡰࡶࡩ࠿ࠦࡻࡾࠤ․").format(
                    response.status_code, response.text))
                return None
        except Exception as e:
            logger.error(bstack111l1ll_opy_ (u"ࠦࡊࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡪࡰࠣࡴࡴࡹࡴࡠࡥࡲࡰࡱ࡫ࡣࡵࡡࡥࡹ࡮ࡲࡤࡠࡦࡤࡸࡦࡀࠠࡼࡿࠥ‥").format(e))
            return None