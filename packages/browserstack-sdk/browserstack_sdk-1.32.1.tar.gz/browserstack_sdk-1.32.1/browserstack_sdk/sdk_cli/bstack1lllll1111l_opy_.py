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
import os
from typing import Dict, Any
from dataclasses import dataclass
from collections import defaultdict
from datetime import timedelta
@dataclass
class bstack1llllll1111_opy_:
    id: str
    hash: str
    thread_id: int
    process_id: int
    type: str
class bstack1llllll11l1_opy_:
    bstack11lll1ll1l1_opy_ = bstack111l1ll_opy_ (u"ࠤࡥࡩࡳࡩࡨ࡮ࡣࡵ࡯ࠧᗷ")
    context: bstack1llllll1111_opy_
    data: Dict[str, Any]
    platform_index: int
    def __init__(self, context: bstack1llllll1111_opy_):
        self.context = context
        self.data = dict({bstack1llllll11l1_opy_.bstack11lll1ll1l1_opy_: defaultdict(lambda: timedelta(microseconds=0))})
        self.platform_index = int(os.environ.get(bstack111l1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡓࡐࡆ࡚ࡆࡐࡔࡐࡣࡎࡔࡄࡆ࡚ࠪᗸ"), bstack111l1ll_opy_ (u"ࠫ࠵࠭ᗹ")))
    def ref(self) -> str:
        return str(self.context.id)
    def bstack1lllll1l1l1_opy_(self, target: object):
        return bstack1llllll11l1_opy_.create_context(target) == self.context
    def bstack1l1lll1llll_opy_(self, context: bstack1llllll1111_opy_):
        return context and context.thread_id == self.context.thread_id and context.process_id == self.context.process_id
    def bstack1l1ll11lll_opy_(self, key: str, value: timedelta):
        self.data[bstack1llllll11l1_opy_.bstack11lll1ll1l1_opy_][key] += value
    def bstack1lll11llll1_opy_(self) -> dict:
        return self.data[bstack1llllll11l1_opy_.bstack11lll1ll1l1_opy_]
    @staticmethod
    def create_context(
        target: object,
        thread_id=threading.get_ident(),
        process_id=os.getpid(),
    ):
        return bstack1llllll1111_opy_(
            id=hash(target),
            hash=hash(target),
            thread_id=thread_id,
            process_id=process_id,
            type=target,
        )