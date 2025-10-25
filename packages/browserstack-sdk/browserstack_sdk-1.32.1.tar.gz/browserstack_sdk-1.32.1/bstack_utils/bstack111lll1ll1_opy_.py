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
import threading
import tempfile
import os
import time
from datetime import datetime
from bstack_utils.bstack11ll1111lll_opy_ import bstack11ll1111ll1_opy_
from bstack_utils.constants import bstack11l1ll1l1ll_opy_, bstack1lllll1lll_opy_
from bstack_utils.bstack1lll11lll1_opy_ import bstack1111lll1_opy_
from bstack_utils import bstack1lllll11l1_opy_
bstack11l11llll11_opy_ = 10
class bstack1llll11ll1_opy_:
    def __init__(self, bstack1l11lll1_opy_, config, bstack11l1l111lll_opy_=0):
        self.bstack11l1l1l1111_opy_ = set()
        self.lock = threading.Lock()
        self.bstack11l1l1111ll_opy_ = bstack111l1ll_opy_ (u"ࠧࢁࡽ࠰ࡶࡨࡷࡹࡵࡲࡤࡪࡨࡷࡹࡸࡡࡵ࡫ࡲࡲ࠴ࡧࡰࡪ࠱ࡹ࠵࠴࡬ࡡࡪ࡮ࡨࡨ࠲ࡺࡥࡴࡶࡶࠦ᫦").format(bstack11l1ll1l1ll_opy_)
        self.bstack11l1l11llll_opy_ = os.path.join(tempfile.gettempdir(), bstack111l1ll_opy_ (u"ࠨࡡࡣࡱࡵࡸࡤࡨࡵࡪ࡮ࡧࡣࢀࢃࠢ᫧").format(os.environ.get(bstack111l1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡖࡗࡌࡈࠬ᫨"))))
        self.bstack11l1l11ll11_opy_ = os.path.join(tempfile.gettempdir(), bstack111l1ll_opy_ (u"ࠣࡨࡤ࡭ࡱ࡫ࡤࡠࡶࡨࡷࡹࡹ࡟ࡼࡿ࠱ࡸࡽࡺࠢ᫩").format(os.environ.get(bstack111l1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡎࡕࡃࡡࡘ࡙ࡎࡊࠧ᫪"))))
        self.bstack11l1l1111l1_opy_ = 2
        self.bstack1l11lll1_opy_ = bstack1l11lll1_opy_
        self.config = config
        self.logger = bstack1lllll11l1_opy_.get_logger(__name__, bstack1lllll1lll_opy_)
        self.bstack11l1l111lll_opy_ = bstack11l1l111lll_opy_
        self.bstack11l11lllll1_opy_ = False
        self.bstack11l11llllll_opy_ = not (
                            os.environ.get(bstack111l1ll_opy_ (u"ࠥࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡅ࡙ࡎࡒࡄࡠࡔࡘࡒࡤࡏࡄࡆࡐࡗࡍࡋࡏࡅࡓࠤ᫫")) and
                            os.environ.get(bstack111l1ll_opy_ (u"ࠦࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡒࡔࡊࡅࡠࡋࡑࡈࡊ࡞ࠢ᫬")) and
                            os.environ.get(bstack111l1ll_opy_ (u"ࠧࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡕࡔࡂࡎࡢࡒࡔࡊࡅࡠࡅࡒ࡙ࡓ࡚ࠢ᫭"))
                        )
        if bstack1111lll1_opy_.bstack11l1l111l11_opy_(config):
            self.bstack11l1l1111l1_opy_ = bstack1111lll1_opy_.bstack11l11llll1l_opy_(config, self.bstack11l1l111lll_opy_)
            self.bstack11l1l111111_opy_()
    def bstack11l1l11l11l_opy_(self):
        return bstack111l1ll_opy_ (u"ࠨࡻࡾࡡࡾࢁࠧ᫮").format(self.config.get(bstack111l1ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡔࡡ࡮ࡧࠪ᫯")), os.environ.get(bstack111l1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡃࡗࡌࡐࡉࡥࡒࡖࡐࡢࡍࡉࡋࡎࡕࡋࡉࡍࡊࡘࠧ᫰")))
    def bstack11l1l11l1ll_opy_(self):
        try:
            if self.bstack11l11llllll_opy_:
                return
            with self.lock:
                try:
                    with open(self.bstack11l1l11ll11_opy_, bstack111l1ll_opy_ (u"ࠤࡵࠦ᫱")) as f:
                        bstack11l1l11ll1l_opy_ = set(line.strip() for line in f if line.strip())
                except FileNotFoundError:
                    bstack11l1l11ll1l_opy_ = set()
                bstack11l1l11l111_opy_ = bstack11l1l11ll1l_opy_ - self.bstack11l1l1l1111_opy_
                if not bstack11l1l11l111_opy_:
                    return
                self.bstack11l1l1l1111_opy_.update(bstack11l1l11l111_opy_)
                data = {bstack111l1ll_opy_ (u"ࠥࡪࡦ࡯࡬ࡦࡦࡗࡩࡸࡺࡳࠣ᫲"): list(self.bstack11l1l1l1111_opy_), bstack111l1ll_opy_ (u"ࠦࡧࡻࡩ࡭ࡦࡑࡥࡲ࡫ࠢ᫳"): self.config.get(bstack111l1ll_opy_ (u"ࠬࡨࡵࡪ࡮ࡧࡒࡦࡳࡥࠨ᫴")), bstack111l1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡗࡻ࡮ࡊࡦࡨࡲࡹ࡯ࡦࡪࡧࡵࠦ᫵"): os.environ.get(bstack111l1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡂࡖࡋࡏࡈࡤࡘࡕࡏࡡࡌࡈࡊࡔࡔࡊࡈࡌࡉࡗ࠭᫶")), bstack111l1ll_opy_ (u"ࠣࡲࡵࡳ࡯࡫ࡣࡵࡐࡤࡱࡪࠨ᫷"): self.config.get(bstack111l1ll_opy_ (u"ࠩࡳࡶࡴࡰࡥࡤࡶࡑࡥࡲ࡫ࠧ᫸"))}
            response = bstack11ll1111ll1_opy_.bstack11l1l111l1l_opy_(self.bstack11l1l1111ll_opy_, data)
            if response.get(bstack111l1ll_opy_ (u"ࠥࡷࡹࡧࡴࡶࡵࠥ᫹")) == 200:
                self.logger.debug(bstack111l1ll_opy_ (u"ࠦࡘࡻࡣࡤࡧࡶࡷ࡫ࡻ࡬࡭ࡻࠣࡷࡪࡴࡴࠡࡨࡤ࡭ࡱ࡫ࡤࠡࡶࡨࡷࡹࡹ࠺ࠡࡽࢀࠦ᫺").format(data))
            else:
                self.logger.debug(bstack111l1ll_opy_ (u"ࠧࡌࡡࡪ࡮ࡨࡨࠥࡺ࡯ࠡࡵࡨࡲࡩࠦࡦࡢ࡫࡯ࡩࡩࠦࡴࡦࡵࡷࡷ࠿ࠦࡻࡾࠤ᫻").format(response))
        except Exception as e:
            self.logger.debug(bstack111l1ll_opy_ (u"ࠨࡅࡹࡥࡨࡴࡹ࡯࡯࡯ࠢࡧࡹࡷ࡯࡮ࡨࠢࡶࡩࡳࡪࡩ࡯ࡩࠣࡪࡦ࡯࡬ࡦࡦࠣࡸࡪࡹࡴࡴ࠼ࠣࡿࢂࠨ᫼").format(e))
    def bstack11l1l111ll1_opy_(self):
        if self.bstack11l11llllll_opy_:
            with self.lock:
                try:
                    with open(self.bstack11l1l11ll11_opy_, bstack111l1ll_opy_ (u"ࠢࡳࠤ᫽")) as f:
                        bstack11l1l11l1l1_opy_ = set(line.strip() for line in f if line.strip())
                    failed_count = len(bstack11l1l11l1l1_opy_)
                except FileNotFoundError:
                    failed_count = 0
                self.logger.debug(bstack111l1ll_opy_ (u"ࠣࡒࡲࡰࡱ࡫ࡤࠡࡨࡤ࡭ࡱ࡫ࡤࠡࡶࡨࡷࡹࡹࠠࡤࡱࡸࡲࡹࠦࠨ࡭ࡱࡦࡥࡱ࠯࠺ࠡࡽࢀࠦ᫾").format(failed_count))
                if failed_count >= self.bstack11l1l1111l1_opy_:
                    self.logger.info(bstack111l1ll_opy_ (u"ࠤࡗ࡬ࡷ࡫ࡳࡩࡱ࡯ࡨࠥࡩࡲࡰࡵࡶࡩࡩࠦࠨ࡭ࡱࡦࡥࡱ࠯࠺ࠡࡽࢀࠤࡃࡃࠠࡼࡿࠥ᫿").format(failed_count, self.bstack11l1l1111l1_opy_))
                    self.bstack11l1l1l111l_opy_(failed_count)
                    self.bstack11l11lllll1_opy_ = True
            return
        try:
            response = bstack11ll1111ll1_opy_.bstack11l1l111ll1_opy_(bstack111l1ll_opy_ (u"ࠥࡿࢂࡅࡢࡶ࡫࡯ࡨࡓࡧ࡭ࡦ࠿ࡾࢁࠫࡨࡵࡪ࡮ࡧࡖࡺࡴࡉࡥࡧࡱࡸ࡮࡬ࡩࡦࡴࡀࡿࢂࠬࡰࡳࡱ࡭ࡩࡨࡺࡎࡢ࡯ࡨࡁࢀࢃࠢᬀ").format(self.bstack11l1l1111ll_opy_, self.config.get(bstack111l1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡑࡥࡲ࡫ࠧᬁ")), os.environ.get(bstack111l1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡇ࡛ࡉࡍࡆࡢࡖ࡚ࡔ࡟ࡊࡆࡈࡒ࡙ࡏࡆࡊࡇࡕࠫᬂ")), self.config.get(bstack111l1ll_opy_ (u"࠭ࡰࡳࡱ࡭ࡩࡨࡺࡎࡢ࡯ࡨࠫᬃ"))))
            if response.get(bstack111l1ll_opy_ (u"ࠢࡴࡶࡤࡸࡺࡹࠢᬄ")) == 200:
                failed_count = response.get(bstack111l1ll_opy_ (u"ࠣࡨࡤ࡭ࡱ࡫ࡤࡕࡧࡶࡸࡸࡉ࡯ࡶࡰࡷࠦᬅ"), 0)
                self.logger.debug(bstack111l1ll_opy_ (u"ࠤࡓࡳࡱࡲࡥࡥࠢࡩࡥ࡮ࡲࡥࡥࠢࡷࡩࡸࡺࡳࠡࡥࡲࡹࡳࡺ࠺ࠡࡽࢀࠦᬆ").format(failed_count))
                if failed_count >= self.bstack11l1l1111l1_opy_:
                    self.logger.info(bstack111l1ll_opy_ (u"ࠥࡘ࡭ࡸࡥࡴࡪࡲࡰࡩࠦࡣࡳࡱࡶࡷࡪࡪ࠺ࠡࡽࢀࠤࡃࡃࠠࡼࡿࠥᬇ").format(failed_count, self.bstack11l1l1111l1_opy_))
                    self.bstack11l1l1l111l_opy_(failed_count)
                    self.bstack11l11lllll1_opy_ = True
            else:
                self.logger.error(bstack111l1ll_opy_ (u"ࠦࡋࡧࡩ࡭ࡧࡧࠤࡹࡵࠠࡱࡱ࡯ࡰࠥ࡬ࡡࡪ࡮ࡨࡨࠥࡺࡥࡴࡶࡶ࠾ࠥࢁࡽࠣᬈ").format(response))
        except Exception as e:
            self.logger.error(bstack111l1ll_opy_ (u"ࠧࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡࡦࡸࡶ࡮ࡴࡧࠡࡲࡲࡰࡱ࡯࡮ࡨ࠼ࠣࡿࢂࠨᬉ").format(e))
    def bstack11l1l1l111l_opy_(self, failed_count):
        with open(self.bstack11l1l11llll_opy_, bstack111l1ll_opy_ (u"ࠨࡷࠣᬊ")) as f:
            f.write(bstack111l1ll_opy_ (u"ࠢࡕࡪࡵࡩࡸ࡮࡯࡭ࡦࠣࡧࡷࡵࡳࡴࡧࡧࠤࡦࡺࠠࡼࡿ࡟ࡲࠧᬋ").format(datetime.now()))
            f.write(bstack111l1ll_opy_ (u"ࠣࡈࡤ࡭ࡱ࡫ࡤࠡࡶࡨࡷࡹࡹࠠࡤࡱࡸࡲࡹࡀࠠࡼࡿ࡟ࡲࠧᬌ").format(failed_count))
        self.logger.debug(bstack111l1ll_opy_ (u"ࠤࡄࡦࡴࡸࡴࠡࡄࡸ࡭ࡱࡪࠠࡧ࡫࡯ࡩࠥࡩࡲࡦࡣࡷࡩࡩࡀࠠࡼࡿࠥᬍ").format(self.bstack11l1l11llll_opy_))
    def bstack11l1l111111_opy_(self):
        def bstack11l1l11lll1_opy_():
            while not self.bstack11l11lllll1_opy_:
                time.sleep(bstack11l11llll11_opy_)
                self.bstack11l1l11l1ll_opy_()
                self.bstack11l1l111ll1_opy_()
        bstack11l1l11111l_opy_ = threading.Thread(target=bstack11l1l11lll1_opy_, daemon=True)
        bstack11l1l11111l_opy_.start()