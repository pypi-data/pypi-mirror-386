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
from browserstack_sdk.sdk_cli.bstack1lll1ll1111_opy_ import bstack1ll1lll1l11_opy_
from browserstack_sdk.sdk_cli.bstack1llll1l11ll_opy_ import (
    bstack1lllll1lll1_opy_,
    bstack1llll1ll1ll_opy_,
    bstack1llllll1l1l_opy_,
    bstack1lllll1ll1l_opy_,
)
from browserstack_sdk.sdk_cli.bstack1lll1111ll1_opy_ import bstack1lll1llll11_opy_
from browserstack_sdk.sdk_cli.bstack1ll1l1ll111_opy_ import bstack1lll11lll11_opy_
from browserstack_sdk.sdk_cli.bstack1lllll1111l_opy_ import bstack1llllll1111_opy_
from typing import Tuple, Dict, Any, List, Callable
from browserstack_sdk.sdk_cli.bstack1lll1ll1111_opy_ import bstack1ll1lll1l11_opy_
import weakref
class bstack1l1lll1l1ll_opy_(bstack1ll1lll1l11_opy_):
    bstack1l1llll11l1_opy_: str
    frameworks: List[str]
    drivers: Dict[str, Tuple[Callable, bstack1lllll1ll1l_opy_]]
    pages: Dict[str, Tuple[Callable, bstack1lllll1ll1l_opy_]]
    def __init__(self, bstack1l1llll11l1_opy_: str, frameworks: List[str]):
        super().__init__()
        self.drivers = dict()
        self.pages = dict()
        self.bstack1l1llll111l_opy_ = dict()
        self.bstack1l1llll11l1_opy_ = bstack1l1llll11l1_opy_
        self.frameworks = frameworks
        bstack1lll11lll11_opy_.bstack1ll1111l11l_opy_((bstack1lllll1lll1_opy_.bstack1llll1l1l1l_opy_, bstack1llll1ll1ll_opy_.POST), self.__1l1lll1ll1l_opy_)
        if any(bstack1lll1llll11_opy_.NAME in f.lower().strip() for f in frameworks):
            bstack1lll1llll11_opy_.bstack1ll1111l11l_opy_(
                (bstack1lllll1lll1_opy_.bstack1lllllll1ll_opy_, bstack1llll1ll1ll_opy_.PRE), self.__1l1llll1l1l_opy_
            )
            bstack1lll1llll11_opy_.bstack1ll1111l11l_opy_(
                (bstack1lllll1lll1_opy_.QUIT, bstack1llll1ll1ll_opy_.POST), self.__1l1llll1111_opy_
            )
    def __1l1lll1ll1l_opy_(
        self,
        f: bstack1lll11lll11_opy_,
        bstack1l1llll1lll_opy_: object,
        exec: Tuple[bstack1lllll1ll1l_opy_, str],
        bstack1lllll11111_opy_: Tuple[bstack1lllll1lll1_opy_, bstack1llll1ll1ll_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        try:
            instance, method_name = exec
            if method_name != bstack111l1ll_opy_ (u"ࠨ࡮ࡦࡹࡢࡴࡦ࡭ࡥࠣ቟"):
                return
            contexts = bstack1l1llll1lll_opy_.browser.contexts
            if contexts:
                for context in contexts:
                    if context.pages:
                        for page in context.pages:
                            if bstack111l1ll_opy_ (u"ࠢࡢࡤࡲࡹࡹࡀࡢ࡭ࡣࡱ࡯ࠧበ") in page.url:
                                self.logger.debug(bstack111l1ll_opy_ (u"ࠣࡕࡷࡳࡷ࡯࡮ࡨࠢࡷ࡬ࡪࠦ࡮ࡦࡹࠣࡴࡦ࡭ࡥࠡ࡫ࡱࡷࡹࡧ࡮ࡤࡧࠥቡ"))
                                self.pages[instance.ref()] = weakref.ref(page), instance
                                bstack1llllll1l1l_opy_.bstack1llllll1lll_opy_(instance, self.bstack1l1llll11l1_opy_, True)
                                self.logger.debug(bstack111l1ll_opy_ (u"ࠤࡢࡣࡴࡴ࡟ࡱࡣࡪࡩࡤ࡯࡮ࡪࡶ࠽ࠤ࡮ࡴࡳࡵࡣࡱࡧࡪࡃࠢቢ") + str(instance.ref()) + bstack111l1ll_opy_ (u"ࠥࠦባ"))
        except Exception as e:
            self.logger.debug(bstack111l1ll_opy_ (u"ࠦࡊࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡪࡰࠣࡷࡹࡵࡲࡪࡰࡪࠤࡳ࡫ࡷࠡࡲࡤ࡫ࡪࠦ࠺ࠣቤ"),e)
    def __1l1llll1l1l_opy_(
        self,
        f: bstack1lll1llll11_opy_,
        driver: object,
        exec: Tuple[bstack1lllll1ll1l_opy_, str],
        bstack1lllll11111_opy_: Tuple[bstack1lllll1lll1_opy_, bstack1llll1ll1ll_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        instance, _ = exec
        if instance.ref() in self.drivers or bstack1llllll1l1l_opy_.bstack1llll1lllll_opy_(instance, self.bstack1l1llll11l1_opy_, False):
            return
        if not f.bstack1l1lllll11l_opy_(f.hub_url(driver)):
            self.bstack1l1llll111l_opy_[instance.ref()] = weakref.ref(driver), instance
            bstack1llllll1l1l_opy_.bstack1llllll1lll_opy_(instance, self.bstack1l1llll11l1_opy_, True)
            self.logger.debug(bstack111l1ll_opy_ (u"ࠧࡥ࡟ࡰࡰࡢࡷࡪࡲࡥ࡯࡫ࡸࡱࡤ࡯࡮ࡪࡶ࠽ࠤࡳࡵ࡮ࡠࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࡟ࡥࡴ࡬ࡺࡪࡸࠠࡪࡰࡶࡸࡦࡴࡣࡦ࠿ࠥብ") + str(instance.ref()) + bstack111l1ll_opy_ (u"ࠨࠢቦ"))
            return
        self.drivers[instance.ref()] = weakref.ref(driver), instance
        bstack1llllll1l1l_opy_.bstack1llllll1lll_opy_(instance, self.bstack1l1llll11l1_opy_, True)
        self.logger.debug(bstack111l1ll_opy_ (u"ࠢࡠࡡࡲࡲࡤࡹࡥ࡭ࡧࡱ࡭ࡺࡳ࡟ࡪࡰ࡬ࡸ࠿ࠦࡩ࡯ࡵࡷࡥࡳࡩࡥ࠾ࠤቧ") + str(instance.ref()) + bstack111l1ll_opy_ (u"ࠣࠤቨ"))
    def __1l1llll1111_opy_(
        self,
        f: bstack1lll1llll11_opy_,
        driver: object,
        exec: Tuple[bstack1lllll1ll1l_opy_, str],
        bstack1lllll11111_opy_: Tuple[bstack1lllll1lll1_opy_, bstack1llll1ll1ll_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        instance, _ = exec
        if not instance.ref() in self.drivers:
            return
        self.bstack1l1llll1l11_opy_(instance)
        self.logger.debug(bstack111l1ll_opy_ (u"ࠤࡢࡣࡴࡴ࡟ࡴࡧ࡯ࡩࡳ࡯ࡵ࡮ࡡࡴࡹ࡮ࡺ࠺ࠡ࡫ࡱࡷࡹࡧ࡮ࡤࡧࡀࠦቩ") + str(instance.ref()) + bstack111l1ll_opy_ (u"ࠥࠦቪ"))
    def bstack1l1lll1ll11_opy_(self, context: bstack1llllll1111_opy_, reverse=True) -> List[Tuple[Callable, bstack1lllll1ll1l_opy_]]:
        matches = []
        if self.pages:
            for data in self.pages.values():
                if data[1].bstack1l1lll1llll_opy_(context):
                    matches.append(data)
        if self.drivers:
            for data in self.drivers.values():
                if (
                    bstack1lll1llll11_opy_.bstack1l1lll1l1l1_opy_(data[1])
                    and data[1].bstack1l1lll1llll_opy_(context)
                    and getattr(data[0](), bstack111l1ll_opy_ (u"ࠦࡸ࡫ࡳࡴ࡫ࡲࡲࡤ࡯ࡤࠣቫ"), False)
                ):
                    matches.append(data)
        return sorted(matches, key=lambda d: d[1].bstack1lllll111l1_opy_, reverse=reverse)
    def bstack1l1lll1lll1_opy_(self, context: bstack1llllll1111_opy_, reverse=True) -> List[Tuple[Callable, bstack1lllll1ll1l_opy_]]:
        matches = []
        for data in self.bstack1l1llll111l_opy_.values():
            if (
                data[1].bstack1l1lll1llll_opy_(context)
                and getattr(data[0](), bstack111l1ll_opy_ (u"ࠧࡹࡥࡴࡵ࡬ࡳࡳࡥࡩࡥࠤቬ"), False)
            ):
                matches.append(data)
        return sorted(matches, key=lambda d: d[1].bstack1lllll111l1_opy_, reverse=reverse)
    def bstack1l1llll11ll_opy_(self, instance: bstack1lllll1ll1l_opy_) -> bool:
        return instance and instance.ref() in self.drivers
    def bstack1l1llll1l11_opy_(self, instance: bstack1lllll1ll1l_opy_) -> bool:
        if self.bstack1l1llll11ll_opy_(instance):
            self.drivers.pop(instance.ref())
            bstack1llllll1l1l_opy_.bstack1llllll1lll_opy_(instance, self.bstack1l1llll11l1_opy_, False)
            return True
        return False