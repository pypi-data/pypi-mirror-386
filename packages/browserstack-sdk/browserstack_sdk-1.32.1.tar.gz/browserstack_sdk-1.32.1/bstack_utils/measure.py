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
import logging
from functools import wraps
from typing import Optional
from bstack_utils.constants import EVENTS, STAGE
from bstack_utils.bstack1lllll11l1_opy_ import get_logger
from bstack_utils.bstack1l1111l1l1_opy_ import bstack1ll1ll1ll11_opy_
bstack1l1111l1l1_opy_ = bstack1ll1ll1ll11_opy_()
logger = get_logger(__name__)
def measure(event_name: EVENTS, stage: STAGE, hook_type: Optional[str] = None, bstack1llll1l111_opy_: Optional[str] = None):
    bstack111l1ll_opy_ (u"ࠨࠢࠣࠌࠣࠤࠥࠦࡄࡦࡥࡲࡶࡦࡺ࡯ࡳࠢࡷࡳࠥࡲ࡯ࡨࠢࡷ࡬ࡪࠦࡳࡵࡣࡵࡸࠥࡺࡩ࡮ࡧࠣࡳ࡫ࠦࡡࠡࡨࡸࡲࡨࡺࡩࡰࡰࠣࡩࡽ࡫ࡣࡶࡶ࡬ࡳࡳࠐࠠࠡࠢࠣࡥࡱࡵ࡮ࡨࠢࡺ࡭ࡹ࡮ࠠࡦࡸࡨࡲࡹࠦ࡮ࡢ࡯ࡨࠤࡦࡴࡤࠡࡵࡷࡥ࡬࡫࠮ࠋࠢࠣࠤࠥࠨࠢࠣ᷾")
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            label: str = event_name.value
            bstack1ll11llll11_opy_: str = bstack1l1111l1l1_opy_.bstack11ll1ll11ll_opy_(label)
            start_mark: str = label + bstack111l1ll_opy_ (u"ࠢ࠻ࡵࡷࡥࡷࡺ᷿ࠢ")
            end_mark: str = label + bstack111l1ll_opy_ (u"ࠣ࠼ࡨࡲࡩࠨḀ")
            result = None
            try:
                if stage.value == STAGE.bstack1l1lll11_opy_.value:
                    bstack1l1111l1l1_opy_.mark(start_mark)
                    result = func(*args, **kwargs)
                elif stage.value == STAGE.END.value:
                    result = func(*args, **kwargs)
                    bstack1l1111l1l1_opy_.end(label, start_mark, end_mark, status=True, failure=None,hook_type=hook_type,test_name=bstack1llll1l111_opy_)
                elif stage.value == STAGE.bstack1l11lllll1_opy_.value:
                    start_mark: str = bstack1ll11llll11_opy_ + bstack111l1ll_opy_ (u"ࠤ࠽ࡷࡹࡧࡲࡵࠤḁ")
                    end_mark: str = bstack1ll11llll11_opy_ + bstack111l1ll_opy_ (u"ࠥ࠾ࡪࡴࡤࠣḂ")
                    bstack1l1111l1l1_opy_.mark(start_mark)
                    result = func(*args, **kwargs)
                    bstack1l1111l1l1_opy_.end(label, start_mark, end_mark, status=True, failure=None, hook_type=hook_type,test_name=bstack1llll1l111_opy_)
            except Exception as e:
                bstack1l1111l1l1_opy_.end(label, start_mark, end_mark, status=False, failure=str(e), hook_type=hook_type,
                                       test_name=bstack1llll1l111_opy_)
            return result
        return wrapper
    return decorator