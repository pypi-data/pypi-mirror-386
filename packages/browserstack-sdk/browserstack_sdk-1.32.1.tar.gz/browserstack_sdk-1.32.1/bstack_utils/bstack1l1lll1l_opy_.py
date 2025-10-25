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
from bstack_utils.bstack1l11l11l1l_opy_ import bstack1llllll1ll1l_opy_
def bstack1llllll11l11_opy_(fixture_name):
    if fixture_name.startswith(bstack111l1ll_opy_ (u"ࠧࡠࡺࡸࡲ࡮ࡺ࡟ࡴࡧࡷࡹࡵࡥࡦࡶࡰࡦࡸ࡮ࡵ࡮ࡠࡨ࡬ࡼࡹࡻࡲࡦࠩᾣ")):
        return bstack111l1ll_opy_ (u"ࠨࡵࡨࡸࡺࡶ࠭ࡧࡷࡱࡧࡹ࡯࡯࡯ࠩᾤ")
    elif fixture_name.startswith(bstack111l1ll_opy_ (u"ࠩࡢࡼࡺࡴࡩࡵࡡࡶࡩࡹࡻࡰࡠ࡯ࡲࡨࡺࡲࡥࡠࡨ࡬ࡼࡹࡻࡲࡦࠩᾥ")):
        return bstack111l1ll_opy_ (u"ࠪࡷࡪࡺࡵࡱ࠯ࡰࡳࡩࡻ࡬ࡦࠩᾦ")
    elif fixture_name.startswith(bstack111l1ll_opy_ (u"ࠫࡤࡾࡵ࡯࡫ࡷࡣࡹ࡫ࡡࡳࡦࡲࡻࡳࡥࡦࡶࡰࡦࡸ࡮ࡵ࡮ࡠࡨ࡬ࡼࡹࡻࡲࡦࠩᾧ")):
        return bstack111l1ll_opy_ (u"ࠬࡺࡥࡢࡴࡧࡳࡼࡴ࠭ࡧࡷࡱࡧࡹ࡯࡯࡯ࠩᾨ")
    elif fixture_name.startswith(bstack111l1ll_opy_ (u"࠭࡟ࡹࡷࡱ࡭ࡹࡥࡴࡦࡣࡵࡨࡴࡽ࡮ࡠࡨࡸࡲࡨࡺࡩࡰࡰࡢࡪ࡮ࡾࡴࡶࡴࡨࠫᾩ")):
        return bstack111l1ll_opy_ (u"ࠧࡵࡧࡤࡶࡩࡵࡷ࡯࠯ࡰࡳࡩࡻ࡬ࡦࠩᾪ")
def bstack1llllll1l1ll_opy_(fixture_name):
    return bool(re.match(bstack111l1ll_opy_ (u"ࠨࡠࡢࡼࡺࡴࡩࡵࡡࠫࡷࡪࡺࡵࡱࡾࡷࡩࡦࡸࡤࡰࡹࡱ࠭ࡤ࠮ࡦࡶࡰࡦࡸ࡮ࡵ࡮ࡽ࡯ࡲࡨࡺࡲࡥࠪࡡࡩ࡭ࡽࡺࡵࡳࡧࡢ࠲࠯࠭ᾫ"), fixture_name))
def bstack1llllll1llll_opy_(fixture_name):
    return bool(re.match(bstack111l1ll_opy_ (u"ࠩࡡࡣࡽࡻ࡮ࡪࡶࡢࠬࡸ࡫ࡴࡶࡲࡿࡸࡪࡧࡲࡥࡱࡺࡲ࠮ࡥ࡭ࡰࡦࡸࡰࡪࡥࡦࡪࡺࡷࡹࡷ࡫࡟࠯ࠬࠪᾬ"), fixture_name))
def bstack1lllllll1111_opy_(fixture_name):
    return bool(re.match(bstack111l1ll_opy_ (u"ࠪࡢࡤࡾࡵ࡯࡫ࡷࡣ࠭ࡹࡥࡵࡷࡳࢀࡹ࡫ࡡࡳࡦࡲࡻࡳ࠯࡟ࡤ࡮ࡤࡷࡸࡥࡦࡪࡺࡷࡹࡷ࡫࡟࠯ࠬࠪᾭ"), fixture_name))
def bstack1lllllll111l_opy_(fixture_name):
    if fixture_name.startswith(bstack111l1ll_opy_ (u"ࠫࡤࡾࡵ࡯࡫ࡷࡣࡸ࡫ࡴࡶࡲࡢࡪࡺࡴࡣࡵ࡫ࡲࡲࡤ࡬ࡩࡹࡶࡸࡶࡪ࠭ᾮ")):
        return bstack111l1ll_opy_ (u"ࠬࡹࡥࡵࡷࡳ࠱࡫ࡻ࡮ࡤࡶ࡬ࡳࡳ࠭ᾯ"), bstack111l1ll_opy_ (u"࠭ࡂࡆࡈࡒࡖࡊࡥࡅࡂࡅࡋࠫᾰ")
    elif fixture_name.startswith(bstack111l1ll_opy_ (u"ࠧࡠࡺࡸࡲ࡮ࡺ࡟ࡴࡧࡷࡹࡵࡥ࡭ࡰࡦࡸࡰࡪࡥࡦࡪࡺࡷࡹࡷ࡫ࠧᾱ")):
        return bstack111l1ll_opy_ (u"ࠨࡵࡨࡸࡺࡶ࠭࡮ࡱࡧࡹࡱ࡫ࠧᾲ"), bstack111l1ll_opy_ (u"ࠩࡅࡉࡋࡕࡒࡆࡡࡄࡐࡑ࠭ᾳ")
    elif fixture_name.startswith(bstack111l1ll_opy_ (u"ࠪࡣࡽࡻ࡮ࡪࡶࡢࡸࡪࡧࡲࡥࡱࡺࡲࡤ࡬ࡵ࡯ࡥࡷ࡭ࡴࡴ࡟ࡧ࡫ࡻࡸࡺࡸࡥࠨᾴ")):
        return bstack111l1ll_opy_ (u"ࠫࡹ࡫ࡡࡳࡦࡲࡻࡳ࠳ࡦࡶࡰࡦࡸ࡮ࡵ࡮ࠨ᾵"), bstack111l1ll_opy_ (u"ࠬࡇࡆࡕࡇࡕࡣࡊࡇࡃࡉࠩᾶ")
    elif fixture_name.startswith(bstack111l1ll_opy_ (u"࠭࡟ࡹࡷࡱ࡭ࡹࡥࡴࡦࡣࡵࡨࡴࡽ࡮ࡠ࡯ࡲࡨࡺࡲࡥࡠࡨ࡬ࡼࡹࡻࡲࡦࠩᾷ")):
        return bstack111l1ll_opy_ (u"ࠧࡵࡧࡤࡶࡩࡵࡷ࡯࠯ࡰࡳࡩࡻ࡬ࡦࠩᾸ"), bstack111l1ll_opy_ (u"ࠨࡃࡉࡘࡊࡘ࡟ࡂࡎࡏࠫᾹ")
    return None, None
def bstack1llllll11lll_opy_(hook_name):
    if hook_name in [bstack111l1ll_opy_ (u"ࠩࡶࡩࡹࡻࡰࠨᾺ"), bstack111l1ll_opy_ (u"ࠪࡸࡪࡧࡲࡥࡱࡺࡲࠬΆ")]:
        return hook_name.capitalize()
    return hook_name
def bstack1llllll1l111_opy_(hook_name):
    if hook_name in [bstack111l1ll_opy_ (u"ࠫࡸ࡫ࡴࡶࡲࡢࡪࡺࡴࡣࡵ࡫ࡲࡲࠬᾼ"), bstack111l1ll_opy_ (u"ࠬࡹࡥࡵࡷࡳࡣࡲ࡫ࡴࡩࡱࡧࠫ᾽")]:
        return bstack111l1ll_opy_ (u"࠭ࡂࡆࡈࡒࡖࡊࡥࡅࡂࡅࡋࠫι")
    elif hook_name in [bstack111l1ll_opy_ (u"ࠧࡴࡧࡷࡹࡵࡥ࡭ࡰࡦࡸࡰࡪ࠭᾿"), bstack111l1ll_opy_ (u"ࠨࡵࡨࡸࡺࡶ࡟ࡤ࡮ࡤࡷࡸ࠭῀")]:
        return bstack111l1ll_opy_ (u"ࠩࡅࡉࡋࡕࡒࡆࡡࡄࡐࡑ࠭῁")
    elif hook_name in [bstack111l1ll_opy_ (u"ࠪࡸࡪࡧࡲࡥࡱࡺࡲࡤ࡬ࡵ࡯ࡥࡷ࡭ࡴࡴࠧῂ"), bstack111l1ll_opy_ (u"ࠫࡹ࡫ࡡࡳࡦࡲࡻࡳࡥ࡭ࡦࡶ࡫ࡳࡩ࠭ῃ")]:
        return bstack111l1ll_opy_ (u"ࠬࡇࡆࡕࡇࡕࡣࡊࡇࡃࡉࠩῄ")
    elif hook_name in [bstack111l1ll_opy_ (u"࠭ࡴࡦࡣࡵࡨࡴࡽ࡮ࡠ࡯ࡲࡨࡺࡲࡥࠨ῅"), bstack111l1ll_opy_ (u"ࠧࡵࡧࡤࡶࡩࡵࡷ࡯ࡡࡦࡰࡦࡹࡳࠨῆ")]:
        return bstack111l1ll_opy_ (u"ࠨࡃࡉࡘࡊࡘ࡟ࡂࡎࡏࠫῇ")
    return hook_name
def bstack1llllll1ll11_opy_(node, scenario):
    if hasattr(node, bstack111l1ll_opy_ (u"ࠩࡦࡥࡱࡲࡳࡱࡧࡦࠫῈ")):
        parts = node.nodeid.rsplit(bstack111l1ll_opy_ (u"ࠥ࡟ࠧΈ"))
        params = parts[-1]
        return bstack111l1ll_opy_ (u"ࠦࢀࢃࠠ࡜ࡽࢀࠦῊ").format(scenario.name, params)
    return scenario.name
def bstack1llllll1lll1_opy_(node):
    try:
        examples = []
        if hasattr(node, bstack111l1ll_opy_ (u"ࠬࡩࡡ࡭࡮ࡶࡴࡪࡩࠧΉ")):
            examples = list(node.callspec.params[bstack111l1ll_opy_ (u"࠭࡟ࡱࡻࡷࡩࡸࡺ࡟ࡣࡦࡧࡣࡪࡾࡡ࡮ࡲ࡯ࡩࠬῌ")].values())
        return examples
    except:
        return []
def bstack1llllll1l11l_opy_(feature, scenario):
    return list(feature.tags) + list(scenario.tags)
def bstack1llllll11ll1_opy_(report):
    try:
        status = bstack111l1ll_opy_ (u"ࠧࡧࡣ࡬ࡰࡪࡪࠧ῍")
        if report.passed or (report.failed and hasattr(report, bstack111l1ll_opy_ (u"ࠣࡹࡤࡷࡽ࡬ࡡࡪ࡮ࠥ῎"))):
            status = bstack111l1ll_opy_ (u"ࠩࡳࡥࡸࡹࡥࡥࠩ῏")
        elif report.skipped:
            status = bstack111l1ll_opy_ (u"ࠪࡷࡰ࡯ࡰࡱࡧࡧࠫῐ")
        bstack1llllll1ll1l_opy_(status)
    except:
        pass
def bstack1lll1l11ll_opy_(status):
    try:
        bstack1llllll1l1l1_opy_ = bstack111l1ll_opy_ (u"ࠫ࡫ࡧࡩ࡭ࡧࡧࠫῑ")
        if status == bstack111l1ll_opy_ (u"ࠬࡶࡡࡴࡵࡨࡨࠬῒ"):
            bstack1llllll1l1l1_opy_ = bstack111l1ll_opy_ (u"࠭ࡰࡢࡵࡶࡩࡩ࠭ΐ")
        elif status == bstack111l1ll_opy_ (u"ࠧࡴ࡭࡬ࡴࡵ࡫ࡤࠨ῔"):
            bstack1llllll1l1l1_opy_ = bstack111l1ll_opy_ (u"ࠨࡵ࡮࡭ࡵࡶࡥࡥࠩ῕")
        bstack1llllll1ll1l_opy_(bstack1llllll1l1l1_opy_)
    except:
        pass
def bstack1llllll11l1l_opy_(item=None, report=None, summary=None, extra=None):
    return