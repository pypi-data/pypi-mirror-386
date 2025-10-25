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
from browserstack_sdk.bstack11l11l11l_opy_ import bstack11llllll1l_opy_
from browserstack_sdk.bstack111l11lll1_opy_ import RobotHandler
def bstack11ll11ll1l_opy_(framework):
    if framework.lower() == bstack111l1ll_opy_ (u"ࠪࡴࡾࡺࡥࡴࡶࠪᬎ"):
        return bstack11llllll1l_opy_.version()
    elif framework.lower() == bstack111l1ll_opy_ (u"ࠫࡷࡵࡢࡰࡶࠪᬏ"):
        return RobotHandler.version()
    elif framework.lower() == bstack111l1ll_opy_ (u"ࠬࡨࡥࡩࡣࡹࡩࠬᬐ"):
        import behave
        return behave.__version__
    else:
        return bstack111l1ll_opy_ (u"࠭ࡵ࡯࡭ࡱࡳࡼࡴࠧᬑ")
def bstack1ll111llll_opy_():
    import importlib.metadata
    framework_name = []
    framework_version = []
    try:
        from selenium import webdriver
        framework_name.append(bstack111l1ll_opy_ (u"ࠧࡴࡧ࡯ࡩࡳ࡯ࡵ࡮ࠩᬒ"))
        framework_version.append(importlib.metadata.version(bstack111l1ll_opy_ (u"ࠣࡵࡨࡰࡪࡴࡩࡶ࡯ࠥᬓ")))
    except:
        pass
    try:
        import playwright
        framework_name.append(bstack111l1ll_opy_ (u"ࠩࡳࡰࡦࡿࡷࡳ࡫ࡪ࡬ࡹ࠭ᬔ"))
        framework_version.append(importlib.metadata.version(bstack111l1ll_opy_ (u"ࠥࡴࡱࡧࡹࡸࡴ࡬࡫࡭ࡺࠢᬕ")))
    except:
        pass
    return {
        bstack111l1ll_opy_ (u"ࠫࡳࡧ࡭ࡦࠩᬖ"): bstack111l1ll_opy_ (u"ࠬࡥࠧᬗ").join(framework_name),
        bstack111l1ll_opy_ (u"࠭ࡶࡦࡴࡶ࡭ࡴࡴࠧᬘ"): bstack111l1ll_opy_ (u"ࠧࡠࠩᬙ").join(framework_version)
    }