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
from urllib.parse import urlparse
from bstack_utils.config import Config
from bstack_utils.messages import bstack111l11lllll_opy_
bstack111ll1ll1_opy_ = Config.bstack111l11l11_opy_()
def bstack1llllllll111_opy_(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
def bstack1lllllll1lll_opy_(bstack1lllllll11ll_opy_, bstack1lllllll1ll1_opy_):
    from pypac import get_pac
    from pypac import PACSession
    from pypac.parser import PACFile
    import socket
    if os.path.isfile(bstack1lllllll11ll_opy_):
        with open(bstack1lllllll11ll_opy_) as f:
            pac = PACFile(f.read())
    elif bstack1llllllll111_opy_(bstack1lllllll11ll_opy_):
        pac = get_pac(url=bstack1lllllll11ll_opy_)
    else:
        raise Exception(bstack111l1ll_opy_ (u"ࠫࡕࡧࡣࠡࡨ࡬ࡰࡪࠦࡤࡰࡧࡶࠤࡳࡵࡴࠡࡧࡻ࡭ࡸࡺ࠺ࠡࡽࢀࠫώ").format(bstack1lllllll11ll_opy_))
    session = PACSession(pac)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((bstack111l1ll_opy_ (u"ࠧ࠾࠮࠹࠰࠻࠲࠽ࠨ὾"), 80))
        bstack1lllllll11l1_opy_ = s.getsockname()[0]
        s.close()
    except:
        bstack1lllllll11l1_opy_ = bstack111l1ll_opy_ (u"࠭࠰࠯࠲࠱࠴࠳࠶ࠧ὿")
    proxy_url = session.get_pac().find_proxy_for_url(bstack1lllllll1ll1_opy_, bstack1lllllll11l1_opy_)
    return proxy_url
def bstack1l11l1ll11_opy_(config):
    return bstack111l1ll_opy_ (u"ࠧࡩࡶࡷࡴࡕࡸ࡯ࡹࡻࠪᾀ") in config or bstack111l1ll_opy_ (u"ࠨࡪࡷࡸࡵࡹࡐࡳࡱࡻࡽࠬᾁ") in config
def bstack11l1l1ll11_opy_(config):
    if not bstack1l11l1ll11_opy_(config):
        return
    if config.get(bstack111l1ll_opy_ (u"ࠩ࡫ࡸࡹࡶࡐࡳࡱࡻࡽࠬᾂ")):
        return config.get(bstack111l1ll_opy_ (u"ࠪ࡬ࡹࡺࡰࡑࡴࡲࡼࡾ࠭ᾃ"))
    if config.get(bstack111l1ll_opy_ (u"ࠫ࡭ࡺࡴࡱࡵࡓࡶࡴࡾࡹࠨᾄ")):
        return config.get(bstack111l1ll_opy_ (u"ࠬ࡮ࡴࡵࡲࡶࡔࡷࡵࡸࡺࠩᾅ"))
def bstack1ll1l111l_opy_(config, bstack1lllllll1ll1_opy_):
    proxy = bstack11l1l1ll11_opy_(config)
    proxies = {}
    if config.get(bstack111l1ll_opy_ (u"࠭ࡨࡵࡶࡳࡔࡷࡵࡸࡺࠩᾆ")) or config.get(bstack111l1ll_opy_ (u"ࠧࡩࡶࡷࡴࡸࡖࡲࡰࡺࡼࠫᾇ")):
        if proxy.endswith(bstack111l1ll_opy_ (u"ࠨ࠰ࡳࡥࡨ࠭ᾈ")):
            proxies = bstack1ll111ll_opy_(proxy, bstack1lllllll1ll1_opy_)
        else:
            proxies = {
                bstack111l1ll_opy_ (u"ࠩ࡫ࡸࡹࡶࡳࠨᾉ"): proxy
            }
    bstack111ll1ll1_opy_.bstack111l1l1ll_opy_(bstack111l1ll_opy_ (u"ࠪࡴࡷࡵࡸࡺࡕࡨࡸࡹ࡯࡮ࡨࡵࠪᾊ"), proxies)
    return proxies
def bstack1ll111ll_opy_(bstack1lllllll11ll_opy_, bstack1lllllll1ll1_opy_):
    proxies = {}
    global bstack1lllllll1l1l_opy_
    if bstack111l1ll_opy_ (u"ࠫࡕࡇࡃࡠࡒࡕࡓ࡝࡟ࠧᾋ") in globals():
        return bstack1lllllll1l1l_opy_
    try:
        proxy = bstack1lllllll1lll_opy_(bstack1lllllll11ll_opy_, bstack1lllllll1ll1_opy_)
        if bstack111l1ll_opy_ (u"ࠧࡊࡉࡓࡇࡆࡘࠧᾌ") in proxy:
            proxies = {}
        elif bstack111l1ll_opy_ (u"ࠨࡈࡕࡖࡓࠦᾍ") in proxy or bstack111l1ll_opy_ (u"ࠢࡉࡖࡗࡔࡘࠨᾎ") in proxy or bstack111l1ll_opy_ (u"ࠣࡕࡒࡇࡐ࡙ࠢᾏ") in proxy:
            bstack1lllllll1l11_opy_ = proxy.split(bstack111l1ll_opy_ (u"ࠤࠣࠦᾐ"))
            if bstack111l1ll_opy_ (u"ࠥ࠾࠴࠵ࠢᾑ") in bstack111l1ll_opy_ (u"ࠦࠧᾒ").join(bstack1lllllll1l11_opy_[1:]):
                proxies = {
                    bstack111l1ll_opy_ (u"ࠬ࡮ࡴࡵࡲࡶࠫᾓ"): bstack111l1ll_opy_ (u"ࠨࠢᾔ").join(bstack1lllllll1l11_opy_[1:])
                }
            else:
                proxies = {
                    bstack111l1ll_opy_ (u"ࠧࡩࡶࡷࡴࡸ࠭ᾕ"): str(bstack1lllllll1l11_opy_[0]).lower() + bstack111l1ll_opy_ (u"ࠣ࠼࠲࠳ࠧᾖ") + bstack111l1ll_opy_ (u"ࠤࠥᾗ").join(bstack1lllllll1l11_opy_[1:])
                }
        elif bstack111l1ll_opy_ (u"ࠥࡔࡗࡕࡘ࡚ࠤᾘ") in proxy:
            bstack1lllllll1l11_opy_ = proxy.split(bstack111l1ll_opy_ (u"ࠦࠥࠨᾙ"))
            if bstack111l1ll_opy_ (u"ࠧࡀ࠯࠰ࠤᾚ") in bstack111l1ll_opy_ (u"ࠨࠢᾛ").join(bstack1lllllll1l11_opy_[1:]):
                proxies = {
                    bstack111l1ll_opy_ (u"ࠧࡩࡶࡷࡴࡸ࠭ᾜ"): bstack111l1ll_opy_ (u"ࠣࠤᾝ").join(bstack1lllllll1l11_opy_[1:])
                }
            else:
                proxies = {
                    bstack111l1ll_opy_ (u"ࠩ࡫ࡸࡹࡶࡳࠨᾞ"): bstack111l1ll_opy_ (u"ࠥ࡬ࡹࡺࡰ࠻࠱࠲ࠦᾟ") + bstack111l1ll_opy_ (u"ࠦࠧᾠ").join(bstack1lllllll1l11_opy_[1:])
                }
        else:
            proxies = {
                bstack111l1ll_opy_ (u"ࠬ࡮ࡴࡵࡲࡶࠫᾡ"): proxy
            }
    except Exception as e:
        print(bstack111l1ll_opy_ (u"ࠨࡳࡰ࡯ࡨࠤࡪࡸࡲࡰࡴࠥᾢ"), bstack111l11lllll_opy_.format(bstack1lllllll11ll_opy_, str(e)))
    bstack1lllllll1l1l_opy_ = proxies
    return proxies