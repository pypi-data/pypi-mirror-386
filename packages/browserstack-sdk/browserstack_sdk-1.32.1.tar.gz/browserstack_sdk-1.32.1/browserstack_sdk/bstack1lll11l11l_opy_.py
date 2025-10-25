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
import json
import multiprocessing
import os
from bstack_utils.config import Config
class bstack1ll11l11ll_opy_():
  def __init__(self, args, logger, bstack1111l1l111_opy_, bstack1111l11lll_opy_, bstack111111l111_opy_):
    self.args = args
    self.logger = logger
    self.bstack1111l1l111_opy_ = bstack1111l1l111_opy_
    self.bstack1111l11lll_opy_ = bstack1111l11lll_opy_
    self.bstack111111l111_opy_ = bstack111111l111_opy_
  def bstack1l1l1111l_opy_(self, bstack1111l11l1l_opy_, bstack11l111111l_opy_, bstack1111111lll_opy_=False):
    bstack11l111ll_opy_ = []
    manager = multiprocessing.Manager()
    bstack1111l11l11_opy_ = manager.list()
    bstack111ll1ll1_opy_ = Config.bstack111l11l11_opy_()
    if bstack1111111lll_opy_:
      for index, platform in enumerate(self.bstack1111l1l111_opy_[bstack111l1ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰࡷࠬ႔")]):
        if index == 0:
          bstack11l111111l_opy_[bstack111l1ll_opy_ (u"ࠪࡪ࡮ࡲࡥࡠࡰࡤࡱࡪ࠭႕")] = self.args
        bstack11l111ll_opy_.append(multiprocessing.Process(name=str(index),
                                                    target=bstack1111l11l1l_opy_,
                                                    args=(bstack11l111111l_opy_, bstack1111l11l11_opy_)))
    else:
      for index, platform in enumerate(self.bstack1111l1l111_opy_[bstack111l1ll_opy_ (u"ࠫࡵࡲࡡࡵࡨࡲࡶࡲࡹࠧ႖")]):
        bstack11l111ll_opy_.append(multiprocessing.Process(name=str(index),
                                                    target=bstack1111l11l1l_opy_,
                                                    args=(bstack11l111111l_opy_, bstack1111l11l11_opy_)))
    i = 0
    for t in bstack11l111ll_opy_:
      try:
        if bstack111ll1ll1_opy_.get_property(bstack111l1ll_opy_ (u"ࠬࡨࡳࡵࡣࡦ࡯ࡤࡹࡥࡴࡵ࡬ࡳࡳ࠭႗")):
          os.environ[bstack111l1ll_opy_ (u"࠭ࡃࡖࡔࡕࡉࡓ࡚࡟ࡑࡎࡄࡘࡋࡕࡒࡎࡡࡇࡅ࡙ࡇࠧ႘")] = json.dumps(self.bstack1111l1l111_opy_[bstack111l1ll_opy_ (u"ࠧࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡵࠪ႙")][i % self.bstack111111l111_opy_])
      except Exception as e:
        self.logger.debug(bstack111l1ll_opy_ (u"ࠣࡇࡵࡶࡴࡸࠠࡸࡪ࡬ࡰࡪࠦࡳࡵࡱࡵ࡭ࡳ࡭ࠠࡤࡷࡵࡶࡪࡴࡴࠡࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࠣࡨࡪࡺࡡࡪ࡮ࡶ࠾ࠥࢁࡽࠣႚ").format(str(e)))
      i += 1
      t.start()
    for t in bstack11l111ll_opy_:
      t.join()
    return list(bstack1111l11l11_opy_)