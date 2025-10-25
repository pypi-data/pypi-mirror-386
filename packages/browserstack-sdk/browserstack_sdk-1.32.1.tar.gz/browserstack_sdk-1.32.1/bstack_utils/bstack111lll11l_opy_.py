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
import json
import logging
import datetime
import threading
from bstack_utils.helper import bstack11ll11l1ll1_opy_, bstack1l111lll_opy_, get_host_info, bstack11l11l1ll1l_opy_, \
 bstack11lll1l11l_opy_, bstack1111llll1_opy_, error_handler, bstack111lll111l1_opy_, bstack11l1llll11_opy_
import bstack_utils.accessibility as bstack1ll1l1ll_opy_
from bstack_utils.bstack1lll11lll1_opy_ import bstack1111lll1_opy_
from bstack_utils.bstack111ll11lll_opy_ import bstack11l1l1111l_opy_
from bstack_utils.percy import bstack1ll1l1l111_opy_
from bstack_utils.config import Config
bstack111ll1ll1_opy_ = Config.bstack111l11l11_opy_()
logger = logging.getLogger(__name__)
percy = bstack1ll1l1l111_opy_()
@error_handler(class_method=False)
def bstack1llll11l11l1_opy_(bs_config, bstack11l1111l1_opy_):
  try:
    data = {
        bstack111l1ll_opy_ (u"ࠪࡪࡴࡸ࡭ࡢࡶࠪ⇝"): bstack111l1ll_opy_ (u"ࠫ࡯ࡹ࡯࡯ࠩ⇞"),
        bstack111l1ll_opy_ (u"ࠬࡶࡲࡰ࡬ࡨࡧࡹࡥ࡮ࡢ࡯ࡨࠫ⇟"): bs_config.get(bstack111l1ll_opy_ (u"࠭ࡰࡳࡱ࡭ࡩࡨࡺࡎࡢ࡯ࡨࠫ⇠"), bstack111l1ll_opy_ (u"ࠧࠨ⇡")),
        bstack111l1ll_opy_ (u"ࠨࡰࡤࡱࡪ࠭⇢"): bs_config.get(bstack111l1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡏࡣࡰࡩࠬ⇣"), os.path.basename(os.path.abspath(os.getcwd()))),
        bstack111l1ll_opy_ (u"ࠪࡦࡺ࡯࡬ࡥࡡ࡬ࡨࡪࡴࡴࡪࡨ࡬ࡩࡷ࠭⇤"): bs_config.get(bstack111l1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡌࡨࡪࡴࡴࡪࡨ࡬ࡩࡷ࠭⇥")),
        bstack111l1ll_opy_ (u"ࠬࡪࡥࡴࡥࡵ࡭ࡵࡺࡩࡰࡰࠪ⇦"): bs_config.get(bstack111l1ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡉ࡫ࡳࡤࡴ࡬ࡴࡹ࡯࡯࡯ࠩ⇧"), bstack111l1ll_opy_ (u"ࠧࠨ⇨")),
        bstack111l1ll_opy_ (u"ࠨࡵࡷࡥࡷࡺࡥࡥࡡࡤࡸࠬ⇩"): bstack11l1llll11_opy_(),
        bstack111l1ll_opy_ (u"ࠩࡷࡥ࡬ࡹࠧ⇪"): bstack11l11l1ll1l_opy_(bs_config),
        bstack111l1ll_opy_ (u"ࠪ࡬ࡴࡹࡴࡠ࡫ࡱࡪࡴ࠭⇫"): get_host_info(),
        bstack111l1ll_opy_ (u"ࠫࡨ࡯࡟ࡪࡰࡩࡳࠬ⇬"): bstack1l111lll_opy_(),
        bstack111l1ll_opy_ (u"ࠬࡨࡵࡪ࡮ࡧࡣࡷࡻ࡮ࡠ࡫ࡧࡩࡳࡺࡩࡧ࡫ࡨࡶࠬ⇭"): os.environ.get(bstack111l1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡈࡕࡊࡎࡇࡣࡗ࡛ࡎࡠࡋࡇࡉࡓ࡚ࡉࡇࡋࡈࡖࠬ⇮")),
        bstack111l1ll_opy_ (u"ࠧࡧࡣ࡬ࡰࡪࡪ࡟ࡵࡧࡶࡸࡸࡥࡲࡦࡴࡸࡲࠬ⇯"): os.environ.get(bstack111l1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡓࡇࡕ࡙ࡓ࠭⇰"), False),
        bstack111l1ll_opy_ (u"ࠩࡹࡩࡷࡹࡩࡰࡰࡢࡧࡴࡴࡴࡳࡱ࡯ࠫ⇱"): bstack11ll11l1ll1_opy_(),
        bstack111l1ll_opy_ (u"ࠪࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࠪ⇲"): bstack1llll111l1l1_opy_(bs_config),
        bstack111l1ll_opy_ (u"ࠫ࡫ࡸࡡ࡮ࡧࡺࡳࡷࡱ࡟ࡥࡧࡷࡥ࡮ࡲࡳࠨ⇳"): bstack1llll111l111_opy_(bstack11l1111l1_opy_),
        bstack111l1ll_opy_ (u"ࠬࡶࡲࡰࡦࡸࡧࡹࡥ࡭ࡢࡲࠪ⇴"): bstack1llll11111ll_opy_(bs_config, bstack11l1111l1_opy_.get(bstack111l1ll_opy_ (u"࠭ࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࡡࡸࡷࡪࡪࠧ⇵"), bstack111l1ll_opy_ (u"ࠧࠨ⇶"))),
        bstack111l1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࡁࡶࡶࡲࡱࡦࡺࡩࡰࡰࠪ⇷"): bstack11lll1l11l_opy_(bs_config),
        bstack111l1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡰࡴࡦ࡬ࡪࡹࡴࡳࡣࡷ࡭ࡴࡴࠧ⇸"): bstack1lll1lllllll_opy_(bs_config)
    }
    return data
  except Exception as error:
    logger.error(bstack111l1ll_opy_ (u"ࠥࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡷࡩ࡫࡯ࡩࠥࡩࡲࡦࡣࡷ࡭ࡳ࡭ࠠࡱࡣࡼࡰࡴࡧࡤࠡࡨࡲࡶ࡚ࠥࡥࡴࡶࡋࡹࡧࡀࠠࠡࡽࢀࠦ⇹").format(str(error)))
    return None
def bstack1llll111l111_opy_(framework):
  return {
    bstack111l1ll_opy_ (u"ࠫ࡫ࡸࡡ࡮ࡧࡺࡳࡷࡱࡎࡢ࡯ࡨࠫ⇺"): framework.get(bstack111l1ll_opy_ (u"ࠬ࡬ࡲࡢ࡯ࡨࡻࡴࡸ࡫ࡠࡰࡤࡱࡪ࠭⇻"), bstack111l1ll_opy_ (u"࠭ࡐࡺࡶࡨࡷࡹ࠭⇼")),
    bstack111l1ll_opy_ (u"ࠧࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭࡙ࡩࡷࡹࡩࡰࡰࠪ⇽"): framework.get(bstack111l1ll_opy_ (u"ࠨࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࡣࡻ࡫ࡲࡴ࡫ࡲࡲࠬ⇾")),
    bstack111l1ll_opy_ (u"ࠩࡶࡨࡰ࡜ࡥࡳࡵ࡬ࡳࡳ࠭⇿"): framework.get(bstack111l1ll_opy_ (u"ࠪࡷࡩࡱ࡟ࡷࡧࡵࡷ࡮ࡵ࡮ࠨ∀")),
    bstack111l1ll_opy_ (u"ࠫࡱࡧ࡮ࡨࡷࡤ࡫ࡪ࠭∁"): bstack111l1ll_opy_ (u"ࠬࡶࡹࡵࡪࡲࡲࠬ∂"),
    bstack111l1ll_opy_ (u"࠭ࡴࡦࡵࡷࡊࡷࡧ࡭ࡦࡹࡲࡶࡰ࠭∃"): framework.get(bstack111l1ll_opy_ (u"ࠧࡵࡧࡶࡸࡋࡸࡡ࡮ࡧࡺࡳࡷࡱࠧ∄"))
  }
def bstack1lll1lllllll_opy_(bs_config):
  bstack111l1ll_opy_ (u"ࠣࠤࠥࠎࠥࠦࡒࡦࡶࡸࡶࡳࡹࠠࡵࡪࡨࠤࡹ࡫ࡳࡵࠢࡲࡶࡨ࡮ࡥࡴࡶࡵࡥࡹ࡯࡯࡯ࠢࡧࡥࡹࡧࠠࡧࡱࡵࠤࡧࡻࡩ࡭ࡦࠣࡷࡹࡧࡲࡵ࠰ࠍࠤࠥࠨࠢࠣ∅")
  if not bs_config:
    return {}
  bstack111l11111l1_opy_ = bstack1111lll1_opy_(bs_config).bstack1111lll1ll1_opy_(bs_config)
  return bstack111l11111l1_opy_
def bstack1111111ll_opy_(bs_config, framework):
  bstack11l1llll_opy_ = False
  bstack11ll111111_opy_ = False
  bstack1llll111l11l_opy_ = False
  if bstack111l1ll_opy_ (u"ࠩࡷࡹࡷࡨ࡯ࡔࡥࡤࡰࡪ࠭∆") in bs_config:
    bstack1llll111l11l_opy_ = True
  elif bstack111l1ll_opy_ (u"ࠪࡥࡵࡶࠧ∇") in bs_config:
    bstack11l1llll_opy_ = True
  else:
    bstack11ll111111_opy_ = True
  bstack1l11111ll_opy_ = {
    bstack111l1ll_opy_ (u"ࠫࡴࡨࡳࡦࡴࡹࡥࡧ࡯࡬ࡪࡶࡼࠫ∈"): bstack11l1l1111l_opy_.bstack1lll1llllll1_opy_(bs_config, framework),
    bstack111l1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬ∉"): bstack1ll1l1ll_opy_.bstack1ll11111ll_opy_(bs_config),
    bstack111l1ll_opy_ (u"࠭ࡰࡦࡴࡦࡽࠬ∊"): bs_config.get(bstack111l1ll_opy_ (u"ࠧࡱࡧࡵࡧࡾ࠭∋"), False),
    bstack111l1ll_opy_ (u"ࠨࡣࡸࡸࡴࡳࡡࡵࡧࠪ∌"): bstack11ll111111_opy_,
    bstack111l1ll_opy_ (u"ࠩࡤࡴࡵࡥࡡࡶࡶࡲࡱࡦࡺࡥࠨ∍"): bstack11l1llll_opy_,
    bstack111l1ll_opy_ (u"ࠪࡸࡺࡸࡢࡰࡵࡦࡥࡱ࡫ࠧ∎"): bstack1llll111l11l_opy_
  }
  return bstack1l11111ll_opy_
@error_handler(class_method=False)
def bstack1llll111l1l1_opy_(bs_config):
  try:
    bstack1llll1111l1l_opy_ = json.loads(os.getenv(bstack111l1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡘࡊ࡙ࡔࡠࡃࡆࡇࡊ࡙ࡓࡊࡄࡌࡐࡎ࡚࡙ࡠࡅࡒࡒࡋࡏࡇࡖࡔࡄࡘࡎࡕࡎࡠ࡛ࡐࡐࠬ∏"), bstack111l1ll_opy_ (u"ࠬࢁࡽࠨ∐")))
    bstack1llll1111l1l_opy_ = bstack1llll11111l1_opy_(bs_config, bstack1llll1111l1l_opy_)
    return {
        bstack111l1ll_opy_ (u"࠭ࡳࡦࡶࡷ࡭ࡳ࡭ࡳࠨ∑"): bstack1llll1111l1l_opy_
    }
  except Exception as error:
    logger.error(bstack111l1ll_opy_ (u"ࠢࡆࡺࡦࡩࡵࡺࡩࡰࡰࠣࡻ࡭࡯࡬ࡦࠢࡦࡶࡪࡧࡴࡪࡰࡪࠤ࡬࡫ࡴࡠࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࡠࡵࡨࡸࡹ࡯࡮ࡨࡵࠣࡪࡴࡸࠠࡕࡧࡶࡸࡍࡻࡢ࠻ࠢࠣࡿࢂࠨ−").format(str(error)))
    return {}
def bstack1llll11111l1_opy_(bs_config, bstack1llll1111l1l_opy_):
  if ((bstack111l1ll_opy_ (u"ࠨࡶࡸࡶࡧࡵࡓࡤࡣ࡯ࡩࠬ∓") in bs_config or not bstack11lll1l11l_opy_(bs_config)) and bstack1ll1l1ll_opy_.bstack1ll11111ll_opy_(bs_config)):
    bstack1llll1111l1l_opy_[bstack111l1ll_opy_ (u"ࠤ࡬ࡲࡨࡲࡵࡥࡧࡈࡲࡨࡵࡤࡦࡦࡈࡼࡹ࡫࡮ࡴ࡫ࡲࡲࠧ∔")] = True
  return bstack1llll1111l1l_opy_
def bstack1llll11l1ll1_opy_(array, bstack1llll111111l_opy_, bstack1llll1111ll1_opy_):
  result = {}
  for o in array:
    key = o[bstack1llll111111l_opy_]
    result[key] = o[bstack1llll1111ll1_opy_]
  return result
def bstack1llll11lllll_opy_(bstack1l1llll111_opy_=bstack111l1ll_opy_ (u"ࠪࠫ∕")):
  bstack1llll111l1ll_opy_ = bstack1ll1l1ll_opy_.on()
  bstack1llll1111l11_opy_ = bstack11l1l1111l_opy_.on()
  bstack1llll1111111_opy_ = percy.bstack1ll11lll1l_opy_()
  if bstack1llll1111111_opy_ and not bstack1llll1111l11_opy_ and not bstack1llll111l1ll_opy_:
    return bstack1l1llll111_opy_ not in [bstack111l1ll_opy_ (u"ࠫࡈࡈࡔࡔࡧࡶࡷ࡮ࡵ࡮ࡄࡴࡨࡥࡹ࡫ࡤࠨ∖"), bstack111l1ll_opy_ (u"ࠬࡒ࡯ࡨࡅࡵࡩࡦࡺࡥࡥࠩ∗")]
  elif bstack1llll111l1ll_opy_ and not bstack1llll1111l11_opy_:
    return bstack1l1llll111_opy_ not in [bstack111l1ll_opy_ (u"࠭ࡈࡰࡱ࡮ࡖࡺࡴࡓࡵࡣࡵࡸࡪࡪࠧ∘"), bstack111l1ll_opy_ (u"ࠧࡉࡱࡲ࡯ࡗࡻ࡮ࡇ࡫ࡱ࡭ࡸ࡮ࡥࡥࠩ∙"), bstack111l1ll_opy_ (u"ࠨࡎࡲ࡫ࡈࡸࡥࡢࡶࡨࡨࠬ√")]
  return bstack1llll111l1ll_opy_ or bstack1llll1111l11_opy_ or bstack1llll1111111_opy_
@error_handler(class_method=False)
def bstack1llll11l1l11_opy_(bstack1l1llll111_opy_, test=None):
  bstack1llll1111lll_opy_ = bstack1ll1l1ll_opy_.on()
  if not bstack1llll1111lll_opy_ or bstack1l1llll111_opy_ not in [bstack111l1ll_opy_ (u"ࠩࡗࡩࡸࡺࡒࡶࡰࡉ࡭ࡳ࡯ࡳࡩࡧࡧࠫ∛")] or test == None:
    return None
  return {
    bstack111l1ll_opy_ (u"ࠪࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࠪ∜"): bstack1llll1111lll_opy_ and bstack1111llll1_opy_(threading.current_thread(), bstack111l1ll_opy_ (u"ࠫࡦ࠷࠱ࡺࡒ࡯ࡥࡹ࡬࡯ࡳ࡯ࠪ∝"), None) == True and bstack1ll1l1ll_opy_.bstack1l1lllll1_opy_(test[bstack111l1ll_opy_ (u"ࠬࡺࡡࡨࡵࠪ∞")])
  }
def bstack1llll11111ll_opy_(bs_config, framework):
  bstack11l1llll_opy_ = False
  bstack11ll111111_opy_ = False
  bstack1llll111l11l_opy_ = False
  if bstack111l1ll_opy_ (u"࠭ࡴࡶࡴࡥࡳࡘࡩࡡ࡭ࡧࠪ∟") in bs_config:
    bstack1llll111l11l_opy_ = True
  elif bstack111l1ll_opy_ (u"ࠧࡢࡲࡳࠫ∠") in bs_config:
    bstack11l1llll_opy_ = True
  else:
    bstack11ll111111_opy_ = True
  bstack1l11111ll_opy_ = {
    bstack111l1ll_opy_ (u"ࠨࡱࡥࡷࡪࡸࡶࡢࡤ࡬ࡰ࡮ࡺࡹࠨ∡"): bstack11l1l1111l_opy_.bstack1lll1llllll1_opy_(bs_config, framework),
    bstack111l1ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠩ∢"): bstack1ll1l1ll_opy_.bstack1ll111l1l_opy_(bs_config),
    bstack111l1ll_opy_ (u"ࠪࡴࡪࡸࡣࡺࠩ∣"): bs_config.get(bstack111l1ll_opy_ (u"ࠫࡵ࡫ࡲࡤࡻࠪ∤"), False),
    bstack111l1ll_opy_ (u"ࠬࡧࡵࡵࡱࡰࡥࡹ࡫ࠧ∥"): bstack11ll111111_opy_,
    bstack111l1ll_opy_ (u"࠭ࡡࡱࡲࡢࡥࡺࡺ࡯࡮ࡣࡷࡩࠬ∦"): bstack11l1llll_opy_,
    bstack111l1ll_opy_ (u"ࠧࡵࡷࡵࡦࡴࡹࡣࡢ࡮ࡨࠫ∧"): bstack1llll111l11l_opy_
  }
  return bstack1l11111ll_opy_