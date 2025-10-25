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
import abc
from browserstack_sdk.sdk_cli.bstack11111111l1_opy_ import bstack1111111111_opy_
class bstack1ll1lll1l11_opy_(abc.ABC):
    bin_session_id: str
    bstack11111111l1_opy_: bstack1111111111_opy_
    def __init__(self):
        self.bstack1ll1ll1ll1l_opy_ = None
        self.config = None
        self.bin_session_id = None
        self.bstack11111111l1_opy_ = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
    def bstack1lll11l111l_opy_(self):
        return (self.bstack1ll1ll1ll1l_opy_ != None and self.bin_session_id != None and self.bstack11111111l1_opy_ != None)
    def configure(self, bstack1ll1ll1ll1l_opy_, config, bin_session_id: str, bstack11111111l1_opy_: bstack1111111111_opy_):
        self.bstack1ll1ll1ll1l_opy_ = bstack1ll1ll1ll1l_opy_
        self.config = config
        self.bin_session_id = bin_session_id
        self.bstack11111111l1_opy_ = bstack11111111l1_opy_
        if self.bin_session_id:
            self.logger.debug(bstack111l1ll_opy_ (u"ࠥ࡟ࢀ࡯ࡤࠩࡵࡨࡰ࡫࠯ࡽ࡞ࠢࡦࡳࡳ࡬ࡩࡨࡷࡵࡩࡩࠦ࡭ࡰࡦࡸࡰࡪࠦࡻࡴࡧ࡯ࡪ࠳ࡥ࡟ࡤ࡮ࡤࡷࡸࡥ࡟࠯ࡡࡢࡲࡦࡳࡥࡠࡡࢀ࠾ࠥࡨࡩ࡯ࡡࡶࡩࡸࡹࡩࡰࡰࡢ࡭ࡩࡃࠢቜ") + str(self.bin_session_id) + bstack111l1ll_opy_ (u"ࠦࠧቝ"))
    def bstack1ll11l1l111_opy_(self):
        if not self.bin_session_id:
            raise ValueError(bstack111l1ll_opy_ (u"ࠧࡨࡩ࡯ࡡࡶࡩࡸࡹࡩࡰࡰࡢ࡭ࡩࠦࡣࡢࡰࡱࡳࡹࠦࡢࡦࠢࡑࡳࡳ࡫ࠢ቞"))
    @abc.abstractmethod
    def is_enabled(self) -> bool:
        return False