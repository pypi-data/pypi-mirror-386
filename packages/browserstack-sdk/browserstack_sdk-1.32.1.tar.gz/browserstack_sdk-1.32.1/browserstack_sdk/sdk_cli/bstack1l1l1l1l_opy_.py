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
from collections import defaultdict
from threading import Lock
from dataclasses import dataclass
import logging
import traceback
from typing import List, Dict, Any
import os
@dataclass
class bstack1lllll1ll1_opy_:
    sdk_version: str
    path_config: str
    path_project: str
    test_framework: str
    frameworks: List[str]
    framework_versions: Dict[str, str]
    bs_config: Dict[str, Any]
@dataclass
class bstack1l1lll111_opy_:
    pass
class bstack1l11l1l1l_opy_:
    bstack1l1ll1l1ll_opy_ = bstack111l1ll_opy_ (u"ࠤࡥࡳࡴࡺࡳࡵࡴࡤࡴࠧᅻ")
    CONNECT = bstack111l1ll_opy_ (u"ࠥࡧࡴࡴ࡮ࡦࡥࡷࠦᅼ")
    bstack11l1l11l_opy_ = bstack111l1ll_opy_ (u"ࠦࡸ࡮ࡵࡵࡦࡲࡻࡳࠨᅽ")
    CONFIG = bstack111l1ll_opy_ (u"ࠧࡩ࡯࡯ࡨ࡬࡫ࠧᅾ")
    bstack1ll1l111l11_opy_ = bstack111l1ll_opy_ (u"ࠨࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࡵࠥᅿ")
    bstack11l1lll11_opy_ = bstack111l1ll_opy_ (u"ࠢࡦࡺ࡬ࡸࠧᆀ")
class bstack1ll1l111lll_opy_:
    bstack1ll1l11l1l1_opy_ = bstack111l1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪ࡟ࡴࡶࡤࡶࡹ࡫ࡤࠣᆁ")
    FINISHED = bstack111l1ll_opy_ (u"ࠤࡥࡹ࡮ࡲࡤࡠࡨ࡬ࡲ࡮ࡹࡨࡦࡦࠥᆂ")
class bstack1ll1l111l1l_opy_:
    bstack1ll1l11l1l1_opy_ = bstack111l1ll_opy_ (u"ࠥࡸࡪࡹࡴࡠࡴࡸࡲࡤࡹࡴࡢࡴࡷࡩࡩࠨᆃ")
    FINISHED = bstack111l1ll_opy_ (u"ࠦࡹ࡫ࡳࡵࡡࡵࡹࡳࡥࡦࡪࡰ࡬ࡷ࡭࡫ࡤࠣᆄ")
class bstack1ll1l11l1ll_opy_:
    bstack1ll1l11l1l1_opy_ = bstack111l1ll_opy_ (u"ࠧ࡮࡯ࡰ࡭ࡢࡶࡺࡴ࡟ࡴࡶࡤࡶࡹ࡫ࡤࠣᆅ")
    FINISHED = bstack111l1ll_opy_ (u"ࠨࡨࡰࡱ࡮ࡣࡷࡻ࡮ࡠࡨ࡬ࡲ࡮ࡹࡨࡦࡦࠥᆆ")
class bstack1ll1l11l11l_opy_:
    bstack1ll1l111ll1_opy_ = bstack111l1ll_opy_ (u"ࠢࡤࡤࡷࡣࡸ࡫ࡳࡴ࡫ࡲࡲࡤࡩࡲࡦࡣࡷࡩࡩࠨᆇ")
class bstack1ll1l11l111_opy_:
    _1lll1ll1l1l_opy_ = None
    def __new__(cls):
        if not cls._1lll1ll1l1l_opy_:
            cls._1lll1ll1l1l_opy_ = super(bstack1ll1l11l111_opy_, cls).__new__(cls)
        return cls._1lll1ll1l1l_opy_
    def __init__(self):
        self._hooks = defaultdict(lambda: defaultdict(list))
        self._lock = Lock()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
    def clear(self):
        with self._lock:
            self._hooks = defaultdict(list)
    def register(self, event_name, callback):
        with self._lock:
            if not callable(callback):
                raise ValueError(bstack111l1ll_opy_ (u"ࠣࡅࡤࡰࡱࡨࡡࡤ࡭ࠣࡱࡺࡹࡴࠡࡤࡨࠤࡨࡧ࡬࡭ࡣࡥࡰࡪࠦࡦࡰࡴࠣࠦᆈ") + event_name)
            pid = os.getpid()
            self.logger.debug(bstack111l1ll_opy_ (u"ࠤࡕࡩ࡬࡯ࡳࡵࡧࡵ࡭ࡳ࡭ࠠࡤࡣ࡯ࡰࡧࡧࡣ࡬ࠢࡩࡳࡷࠦࡥࡷࡧࡱࡸࠥ࠭ࡻࡦࡸࡨࡲࡹࡥ࡮ࡢ࡯ࡨࢁࠬࠦࡷࡪࡶ࡫ࠤࡵ࡯ࡤࠡࠤᆉ") + str(pid) + bstack111l1ll_opy_ (u"ࠥࠦᆊ"))
            self._hooks[event_name][pid].append(callback)
    def invoke(self, event_name, *args, **kwargs):
        with self._lock:
            pid = os.getpid()
            callbacks = self._hooks.get(event_name, {}).get(pid, [])
            if not callbacks:
                self.logger.warning(bstack111l1ll_opy_ (u"ࠦࡓࡵࠠࡤࡣ࡯ࡰࡧࡧࡣ࡬ࡵࠣࡪࡴࡸࠠࡦࡸࡨࡲࡹࠦࠧࡼࡧࡹࡩࡳࡺ࡟࡯ࡣࡰࡩࢂ࠭ࠠࡸ࡫ࡷ࡬ࠥࡶࡩࡥࠢࠥᆋ") + str(pid) + bstack111l1ll_opy_ (u"ࠧࠨᆌ"))
                return
            self.logger.debug(bstack111l1ll_opy_ (u"ࠨࡉ࡯ࡸࡲ࡯࡮ࡴࡧࠡࡽ࡯ࡩࡳ࠮ࡣࡢ࡮࡯ࡦࡦࡩ࡫ࡴࠫࢀࠤࡨࡧ࡬࡭ࡤࡤࡧࡰࡹࠠࡧࡱࡵࠤࡪࡼࡥ࡯ࡶࠣࠫࢀ࡫ࡶࡦࡰࡷࡣࡳࡧ࡭ࡦࡿࠪࠤࡼ࡯ࡴࡩࠢࡳ࡭ࡩࠦࠢᆍ") + str(pid) + bstack111l1ll_opy_ (u"ࠢࠣᆎ"))
            for callback in callbacks:
                try:
                    self.logger.debug(bstack111l1ll_opy_ (u"ࠣࡋࡱࡺࡴࡱࡥࡥࠢࡦࡥࡱࡲࡢࡢࡥ࡮ࠤ࡫ࡵࡲࠡࡧࡹࡩࡳࡺࠠࠨࡽࡨࡺࡪࡴࡴࡠࡰࡤࡱࡪࢃࠧࠡࡹ࡬ࡸ࡭ࠦࡰࡪࡦࠣࠦᆏ") + str(pid) + bstack111l1ll_opy_ (u"ࠤࠥᆐ"))
                    callback(event_name, *args, **kwargs)
                except Exception as e:
                    self.logger.error(bstack111l1ll_opy_ (u"ࠥࡉࡷࡸ࡯ࡳࠢ࡬ࡲࡻࡵ࡫ࡪࡰࡪࠤࡨࡧ࡬࡭ࡤࡤࡧࡰࠦࡦࡰࡴࠣࡩࡻ࡫࡮ࡵࠢࠪࡿࡪࡼࡥ࡯ࡶࡢࡲࡦࡳࡥࡾࠩࠣࡻ࡮ࡺࡨࠡࡲ࡬ࡨࠥࢁࡰࡪࡦࢀ࠾ࠥࠨᆑ") + str(e) + bstack111l1ll_opy_ (u"ࠦࠧᆒ"))
                    traceback.print_exc()
bstack1l1l1l1l_opy_ = bstack1ll1l11l111_opy_()