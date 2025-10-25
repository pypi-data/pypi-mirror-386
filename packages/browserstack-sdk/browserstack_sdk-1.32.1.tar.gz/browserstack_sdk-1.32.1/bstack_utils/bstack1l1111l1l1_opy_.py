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
from filelock import FileLock
import json
import os
import time
import uuid
import logging
from typing import Dict, List, Optional
from bstack_utils.bstack1lllll11l1_opy_ import get_logger
logger = get_logger(__name__)
bstack111111111l1_opy_: Dict[str, float] = {}
bstack1lllllllllll_opy_: List = []
bstack1llllllllll1_opy_ = 5
bstack1l1111111l_opy_ = os.path.join(os.getcwd(), bstack111l1ll_opy_ (u"ࠧ࡭ࡱࡪࠫὤ"), bstack111l1ll_opy_ (u"ࠨ࡭ࡨࡽ࠲ࡳࡥࡵࡴ࡬ࡧࡸ࠴ࡪࡴࡱࡱࠫὥ"))
logging.getLogger(bstack111l1ll_opy_ (u"ࠩࡩ࡭ࡱ࡫࡬ࡰࡥ࡮ࠫὦ")).setLevel(logging.WARNING)
lock = FileLock(bstack1l1111111l_opy_+bstack111l1ll_opy_ (u"ࠥ࠲ࡱࡵࡣ࡬ࠤὧ"))
class bstack1llllllll1l1_opy_:
    duration: float
    name: str
    startTime: float
    worker: int
    status: bool
    failure: str
    details: Optional[str]
    entryType: str
    platform: Optional[int]
    command: Optional[str]
    hookType: Optional[str]
    cli: Optional[bool]
    def __init__(self, duration: float, name: str, start_time: float, bstack1111111111l_opy_: int, status: bool, failure: str, details: Optional[str] = None, platform: Optional[int] = None, command: Optional[str] = None, test_name: Optional[str] = None, hook_type: Optional[str] = None, cli: Optional[bool] = False) -> None:
        self.duration = duration
        self.name = name
        self.startTime = start_time
        self.worker = bstack1111111111l_opy_
        self.status = status
        self.failure = failure
        self.details = details
        self.entryType = bstack111l1ll_opy_ (u"ࠦࡲ࡫ࡡࡴࡷࡵࡩࠧὨ")
        self.platform = platform
        self.command = command
        self.testName = test_name
        self.hookType = hook_type
        self.cli = cli
class bstack1ll1ll1ll11_opy_:
    global bstack111111111l1_opy_
    @staticmethod
    def bstack1ll1l1111l1_opy_(key: str):
        bstack1ll11llll11_opy_ = bstack1ll1ll1ll11_opy_.bstack11ll1ll11ll_opy_(key)
        bstack1ll1ll1ll11_opy_.mark(bstack1ll11llll11_opy_+bstack111l1ll_opy_ (u"ࠧࡀࡳࡵࡣࡵࡸࠧὩ"))
        return bstack1ll11llll11_opy_
    @staticmethod
    def mark(key: str) -> None:
        try:
            bstack111111111l1_opy_[key] = time.time_ns() / 1000000
        except Exception as e:
            logger.debug(bstack111l1ll_opy_ (u"ࠨࡅࡳࡴࡲࡶ࠿ࠦࡻࡾࠤὪ").format(e))
    @staticmethod
    def end(label: str, start: str, end: str, status: bool, failure: Optional[str] = None, hook_type: Optional[str] = None, details: Optional[str] = None, command: Optional[str] = None, test_name: Optional[str] = None) -> None:
        try:
            bstack1ll1ll1ll11_opy_.mark(end)
            bstack1ll1ll1ll11_opy_.measure(label, start, end, status, failure, hook_type, details, command, test_name)
        except Exception as e:
            logger.debug(bstack111l1ll_opy_ (u"ࠢࡆࡴࡵࡳࡷࠦࡩ࡯ࠢ࡮ࡩࡾࠦ࡭ࡦࡶࡵ࡭ࡨࡹ࠺ࠡࡽࢀࠦὫ").format(e))
    @staticmethod
    def measure(label: str, start: str, end: str, status: bool, failure: Optional[str], hook_type: Optional[str] = None, details: Optional[str] = None, command: Optional[str] = None, test_name: Optional[str] = None) -> None:
        try:
            if start not in bstack111111111l1_opy_ or end not in bstack111111111l1_opy_:
                logger.debug(bstack111l1ll_opy_ (u"ࠣࡇࡵࡶࡴࡸࠠࡪࡰࠣࡷࡹࡧࡲࡵࠢ࡮ࡩࡾࠦࡷࡪࡶ࡫ࠤࡻࡧ࡬ࡶࡧࠣࡿࢂࠦ࡯ࡳࠢࡨࡲࡩࠦ࡫ࡦࡻࠣࡻ࡮ࡺࡨࠡࡸࡤࡰࡺ࡫ࠠࡼࡿࠥὬ").format(start,end))
                return
            duration: float = bstack111111111l1_opy_[end] - bstack111111111l1_opy_[start]
            bstack1llllllll11l_opy_ = os.environ.get(bstack111l1ll_opy_ (u"ࠤࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡄࡌࡒࡆࡘ࡙ࡠࡋࡖࡣࡗ࡛ࡎࡏࡋࡑࡋࠧὭ"), bstack111l1ll_opy_ (u"ࠥࡪࡦࡲࡳࡦࠤὮ")).lower() == bstack111l1ll_opy_ (u"ࠦࡹࡸࡵࡦࠤὯ")
            bstack1lllllllll11_opy_: bstack1llllllll1l1_opy_ = bstack1llllllll1l1_opy_(duration, label, bstack111111111l1_opy_[start], os.getpid(), status, failure, details, os.environ.get(bstack111l1ll_opy_ (u"ࠧࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡕࡒࡁࡕࡈࡒࡖࡒࡥࡉࡏࡆࡈ࡜ࠧὰ"), 0), command, test_name, hook_type, bstack1llllllll11l_opy_)
            del bstack111111111l1_opy_[start]
            del bstack111111111l1_opy_[end]
            bstack1ll1ll1ll11_opy_.bstack1llllllll1ll_opy_(bstack1lllllllll11_opy_)
        except Exception as e:
            logger.debug(bstack111l1ll_opy_ (u"ࠨࡅࡳࡴࡲࡶࠥࡽࡨࡪ࡮ࡨࠤࡲ࡫ࡡࡴࡷࡵ࡭ࡳ࡭ࠠ࡬ࡧࡼࠤࡲ࡫ࡴࡳ࡫ࡦࡷ࠿ࠦࡻࡾࠤά").format(e))
    @staticmethod
    def bstack1llllllll1ll_opy_(bstack1lllllllll11_opy_):
        os.makedirs(os.path.dirname(bstack1l1111111l_opy_)) if not os.path.exists(os.path.dirname(bstack1l1111111l_opy_)) else None
        bstack1ll1ll1ll11_opy_.bstack11111111111_opy_()
        try:
            with lock:
                with open(bstack1l1111111l_opy_, bstack111l1ll_opy_ (u"ࠢࡳ࠭ࠥὲ"), encoding=bstack111l1ll_opy_ (u"ࠣࡷࡷࡪ࠲࠾ࠢέ")) as file:
                    try:
                        data = json.load(file)
                    except json.JSONDecodeError:
                        data = []
                    data.append(bstack1lllllllll11_opy_.__dict__)
                    file.seek(0)
                    file.truncate()
                    json.dump(data, file, indent=4)
        except FileNotFoundError as bstack1lllllllll1l_opy_:
            logger.debug(bstack111l1ll_opy_ (u"ࠤࡉ࡭ࡱ࡫ࠠ࡯ࡱࡷࠤ࡫ࡵࡵ࡯ࡦࠣࡿࢂࠨὴ").format(bstack1lllllllll1l_opy_))
            with lock:
                with open(bstack1l1111111l_opy_, bstack111l1ll_opy_ (u"ࠥࡻࠧή"), encoding=bstack111l1ll_opy_ (u"ࠦࡺࡺࡦ࠮࠺ࠥὶ")) as file:
                    data = [bstack1lllllllll11_opy_.__dict__]
                    json.dump(data, file, indent=4)
        except Exception as e:
            logger.debug(bstack111l1ll_opy_ (u"ࠧࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡࡹ࡫࡭ࡱ࡫ࠠ࡬ࡧࡼࠤࡲ࡫ࡴࡳ࡫ࡦࡷࠥࡧࡰࡱࡧࡱࡨࠥࢁࡽࠣί").format(str(e)))
        finally:
            if os.path.exists(bstack1l1111111l_opy_+bstack111l1ll_opy_ (u"ࠨ࠮࡭ࡱࡦ࡯ࠧὸ")):
                os.remove(bstack1l1111111l_opy_+bstack111l1ll_opy_ (u"ࠢ࠯࡮ࡲࡧࡰࠨό"))
    @staticmethod
    def bstack11111111111_opy_():
        attempt = 0
        while (attempt < bstack1llllllllll1_opy_):
            attempt += 1
            if os.path.exists(bstack1l1111111l_opy_+bstack111l1ll_opy_ (u"ࠣ࠰࡯ࡳࡨࡱࠢὺ")):
                time.sleep(0.5)
            else:
                break
    @staticmethod
    def bstack11ll1ll11ll_opy_(label: str) -> str:
        try:
            return bstack111l1ll_opy_ (u"ࠤࡾࢁ࠿ࢁࡽࠣύ").format(label,str(uuid.uuid4().hex)[:6])
        except Exception as e:
            logger.debug(bstack111l1ll_opy_ (u"ࠥࡉࡷࡸ࡯ࡳ࠼ࠣࡿࢂࠨὼ").format(e))