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
import traceback
from typing import Dict, Tuple, Callable, Type, List, Any
from urllib.parse import urlparse
from browserstack_sdk.sdk_cli.bstack1llll1l11ll_opy_ import (
    bstack1llllll1l1l_opy_,
    bstack1lllll1ll1l_opy_,
    bstack1lllll1lll1_opy_,
    bstack1llll1ll1ll_opy_,
)
import copy
from datetime import datetime, timezone, timedelta
class bstack1lll11lll11_opy_(bstack1llllll1l1l_opy_):
    bstack1l11l111111_opy_ = bstack111l1ll_opy_ (u"ࠣࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡑࡎࡄࡘࡋࡕࡒࡎࡡࡌࡒࡉࡋࡘࠣᐨ")
    bstack1l1l1111ll1_opy_ = bstack111l1ll_opy_ (u"ࠤࡩࡶࡦࡳࡥࡸࡱࡵ࡯ࡤࡹࡥࡴࡵ࡬ࡳࡳࡥࡩࡥࠤᐩ")
    bstack1l1l111l11l_opy_ = bstack111l1ll_opy_ (u"ࠥ࡬ࡺࡨ࡟ࡶࡴ࡯ࠦᐪ")
    bstack1l1l11l1l1l_opy_ = bstack111l1ll_opy_ (u"ࠦࡨࡧࡰࡢࡤ࡬ࡰ࡮ࡺࡩࡦࡵࠥᐫ")
    bstack1l11l111lll_opy_ = bstack111l1ll_opy_ (u"ࠧࡽ࠳ࡤࡧࡻࡩࡨࡻࡴࡦࡵࡦࡶ࡮ࡶࡴࠣᐬ")
    bstack1l11l11111l_opy_ = bstack111l1ll_opy_ (u"ࠨࡷ࠴ࡥࡨࡼࡪࡩࡵࡵࡧࡶࡧࡷ࡯ࡰࡵࡣࡶࡽࡳࡩࠢᐭ")
    NAME = bstack111l1ll_opy_ (u"ࠢࡱ࡮ࡤࡽࡼࡸࡩࡨࡪࡷࠦᐮ")
    bstack1l11l111ll1_opy_: Dict[str, List[Callable]] = dict()
    platform_index: int
    options: Any
    desired_capabilities: Any
    bstack1lll11111l1_opy_: Any
    bstack1l11l1111l1_opy_: Dict
    def __init__(
        self,
        platform_index: int,
        framework_name: str,
        framework_version: str,
        classes: List[Type],
        methods=[bstack111l1ll_opy_ (u"ࠣ࡮ࡤࡹࡳࡩࡨࠣᐯ"), bstack111l1ll_opy_ (u"ࠤࡦࡳࡳࡴࡥࡤࡶࠥᐰ"), bstack111l1ll_opy_ (u"ࠥࡲࡪࡽ࡟ࡱࡣࡪࡩࠧᐱ"), bstack111l1ll_opy_ (u"ࠦࡨࡲ࡯ࡴࡧࠥᐲ"), bstack111l1ll_opy_ (u"ࠧࡪࡩࡴࡲࡤࡸࡨ࡮ࠢᐳ")],
    ):
        super().__init__(
            framework_name,
            framework_version,
            classes,
        )
        self.platform_index = platform_index
        self.bstack1lllll1llll_opy_(methods)
    def bstack1llllll1ll1_opy_(self, instance: bstack1lllll1ll1l_opy_, method_name: str, bstack1lllll11ll1_opy_: timedelta, *args, **kwargs):
        pass
    def bstack1llllllll11_opy_(
        self,
        target: object,
        exec: Tuple[bstack1lllll1ll1l_opy_, str],
        bstack1lllll11111_opy_: Tuple[bstack1lllll1lll1_opy_, bstack1llll1ll1ll_opy_],
        result: Any,
        *args,
        **kwargs,
    ) -> Callable[..., Any]:
        instance, method_name = exec
        bstack1llllll1l11_opy_, bstack1l11l111l1l_opy_ = bstack1lllll11111_opy_
        bstack1l111lllll1_opy_ = bstack1lll11lll11_opy_.bstack1l11l1111ll_opy_(bstack1lllll11111_opy_)
        if bstack1l111lllll1_opy_ in bstack1lll11lll11_opy_.bstack1l11l111ll1_opy_:
            bstack1l111llllll_opy_ = None
            for callback in bstack1lll11lll11_opy_.bstack1l11l111ll1_opy_[bstack1l111lllll1_opy_]:
                try:
                    bstack1l11l111l11_opy_ = callback(self, target, exec, bstack1lllll11111_opy_, result, *args, **kwargs)
                    if bstack1l111llllll_opy_ == None:
                        bstack1l111llllll_opy_ = bstack1l11l111l11_opy_
                except Exception as e:
                    self.logger.error(bstack111l1ll_opy_ (u"ࠨࡥࡳࡴࡲࡶࠥ࡯࡮ࡷࡱ࡮࡭ࡳ࡭ࠠࡤࡣ࡯ࡰࡧࡧࡣ࡬࠼ࠣࠦᐴ") + str(e) + bstack111l1ll_opy_ (u"ࠢࠣᐵ"))
                    traceback.print_exc()
            if bstack1l11l111l1l_opy_ == bstack1llll1ll1ll_opy_.PRE and callable(bstack1l111llllll_opy_):
                return bstack1l111llllll_opy_
            elif bstack1l11l111l1l_opy_ == bstack1llll1ll1ll_opy_.POST and bstack1l111llllll_opy_:
                return bstack1l111llllll_opy_
    def bstack1lllll1l111_opy_(
        self, method_name, previous_state: bstack1lllll1lll1_opy_, *args, **kwargs
    ) -> bstack1lllll1lll1_opy_:
        if method_name == bstack111l1ll_opy_ (u"ࠨ࡮ࡤࡹࡳࡩࡨࠨᐶ") or method_name == bstack111l1ll_opy_ (u"ࠩࡦࡳࡳࡴࡥࡤࡶࠪᐷ") or method_name == bstack111l1ll_opy_ (u"ࠪࡲࡪࡽ࡟ࡱࡣࡪࡩࠬᐸ"):
            return bstack1lllll1lll1_opy_.bstack1llll1l1l1l_opy_
        if method_name == bstack111l1ll_opy_ (u"ࠫࡩ࡯ࡳࡱࡣࡷࡧ࡭࠭ᐹ"):
            return bstack1lllll1lll1_opy_.bstack1llll1l1ll1_opy_
        if method_name == bstack111l1ll_opy_ (u"ࠬࡩ࡬ࡰࡵࡨࠫᐺ"):
            return bstack1lllll1lll1_opy_.QUIT
        return bstack1lllll1lll1_opy_.NONE
    @staticmethod
    def bstack1l11l1111ll_opy_(bstack1lllll11111_opy_: Tuple[bstack1lllll1lll1_opy_, bstack1llll1ll1ll_opy_]):
        return bstack111l1ll_opy_ (u"ࠨ࠺ࠣᐻ").join((bstack1lllll1lll1_opy_(bstack1lllll11111_opy_[0]).name, bstack1llll1ll1ll_opy_(bstack1lllll11111_opy_[1]).name))
    @staticmethod
    def bstack1ll1111l11l_opy_(bstack1lllll11111_opy_: Tuple[bstack1lllll1lll1_opy_, bstack1llll1ll1ll_opy_], callback: Callable):
        bstack1l111lllll1_opy_ = bstack1lll11lll11_opy_.bstack1l11l1111ll_opy_(bstack1lllll11111_opy_)
        if not bstack1l111lllll1_opy_ in bstack1lll11lll11_opy_.bstack1l11l111ll1_opy_:
            bstack1lll11lll11_opy_.bstack1l11l111ll1_opy_[bstack1l111lllll1_opy_] = []
        bstack1lll11lll11_opy_.bstack1l11l111ll1_opy_[bstack1l111lllll1_opy_].append(callback)
    @staticmethod
    def bstack1ll111ll11l_opy_(method_name: str):
        return True
    @staticmethod
    def bstack1ll111l11l1_opy_(method_name: str, *args) -> bool:
        return True
    @staticmethod
    def bstack1ll11l1l11l_opy_(instance: bstack1lllll1ll1l_opy_, default_value=None):
        return bstack1llllll1l1l_opy_.bstack1llll1lllll_opy_(instance, bstack1lll11lll11_opy_.bstack1l1l11l1l1l_opy_, default_value)
    @staticmethod
    def bstack1l1lll1l1l1_opy_(instance: bstack1lllll1ll1l_opy_) -> bool:
        return True
    @staticmethod
    def bstack1ll11111lll_opy_(instance: bstack1lllll1ll1l_opy_, default_value=None):
        return bstack1llllll1l1l_opy_.bstack1llll1lllll_opy_(instance, bstack1lll11lll11_opy_.bstack1l1l111l11l_opy_, default_value)
    @staticmethod
    def bstack1ll11ll1l1l_opy_(*args):
        return args[0] if args and type(args) in [list, tuple] and isinstance(args[0], str) else None
    @staticmethod
    def bstack1ll11l11111_opy_(method_name: str, *args):
        if not bstack1lll11lll11_opy_.bstack1ll111ll11l_opy_(method_name):
            return False
        if not bstack1lll11lll11_opy_.bstack1l11l111lll_opy_ in bstack1lll11lll11_opy_.bstack1l11l1lllll_opy_(*args):
            return False
        bstack1l1lllllll1_opy_ = bstack1lll11lll11_opy_.bstack1l1lllll1ll_opy_(*args)
        return bstack1l1lllllll1_opy_ and bstack111l1ll_opy_ (u"ࠢࡴࡥࡵ࡭ࡵࡺࠢᐼ") in bstack1l1lllllll1_opy_ and bstack111l1ll_opy_ (u"ࠣࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࡟ࡦࡺࡨࡧࡺࡺ࡯ࡳࠤᐽ") in bstack1l1lllllll1_opy_[bstack111l1ll_opy_ (u"ࠤࡶࡧࡷ࡯ࡰࡵࠤᐾ")]
    @staticmethod
    def bstack1ll1111llll_opy_(method_name: str, *args):
        if not bstack1lll11lll11_opy_.bstack1ll111ll11l_opy_(method_name):
            return False
        if not bstack1lll11lll11_opy_.bstack1l11l111lll_opy_ in bstack1lll11lll11_opy_.bstack1l11l1lllll_opy_(*args):
            return False
        bstack1l1lllllll1_opy_ = bstack1lll11lll11_opy_.bstack1l1lllll1ll_opy_(*args)
        return (
            bstack1l1lllllll1_opy_
            and bstack111l1ll_opy_ (u"ࠥࡷࡨࡸࡩࡱࡶࠥᐿ") in bstack1l1lllllll1_opy_
            and bstack111l1ll_opy_ (u"ࠦࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࡢࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࡢࡥࡺࡺ࡯࡮ࡣࡷ࡭ࡴࡴ࡟ࡴࡥࡵ࡭ࡵࡺࠢᑀ") in bstack1l1lllllll1_opy_[bstack111l1ll_opy_ (u"ࠧࡹࡣࡳ࡫ࡳࡸࠧᑁ")]
        )
    @staticmethod
    def bstack1l11l1lllll_opy_(*args):
        return str(bstack1lll11lll11_opy_.bstack1ll11ll1l1l_opy_(*args)).lower()