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
import json
from bstack_utils.bstack1lllll11l1_opy_ import get_logger
logger = get_logger(__name__)
class bstack11ll111lll1_opy_(object):
  bstack11l1ll1111_opy_ = os.path.join(os.path.expanduser(bstack111l1ll_opy_ (u"ࠪࢂࠬᝤ")), bstack111l1ll_opy_ (u"ࠫ࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࠫᝥ"))
  bstack11ll11l1111_opy_ = os.path.join(bstack11l1ll1111_opy_, bstack111l1ll_opy_ (u"ࠬࡩ࡯࡮࡯ࡤࡲࡩࡹ࠮࡫ࡵࡲࡲࠬᝦ"))
  commands_to_wrap = None
  perform_scan = None
  bstack11ll11lll1_opy_ = None
  bstack1ll1l1l1l1_opy_ = None
  bstack11ll11lll1l_opy_ = None
  bstack11ll1l11ll1_opy_ = None
  def __new__(cls):
    if not hasattr(cls, bstack111l1ll_opy_ (u"࠭ࡩ࡯ࡵࡷࡥࡳࡩࡥࠨᝧ")):
      cls.instance = super(bstack11ll111lll1_opy_, cls).__new__(cls)
      cls.instance.bstack11ll11l111l_opy_()
    return cls.instance
  def bstack11ll11l111l_opy_(self):
    try:
      with open(self.bstack11ll11l1111_opy_, bstack111l1ll_opy_ (u"ࠧࡳࠩᝨ")) as bstack1lll1l1ll1_opy_:
        bstack11ll111llll_opy_ = bstack1lll1l1ll1_opy_.read()
        data = json.loads(bstack11ll111llll_opy_)
        if bstack111l1ll_opy_ (u"ࠨࡥࡲࡱࡲࡧ࡮ࡥࡵࠪᝩ") in data:
          self.bstack11ll1l111ll_opy_(data[bstack111l1ll_opy_ (u"ࠩࡦࡳࡲࡳࡡ࡯ࡦࡶࠫᝪ")])
        if bstack111l1ll_opy_ (u"ࠪࡷࡨࡸࡩࡱࡶࡶࠫᝫ") in data:
          self.bstack1llllll1ll_opy_(data[bstack111l1ll_opy_ (u"ࠫࡸࡩࡲࡪࡲࡷࡷࠬᝬ")])
        if bstack111l1ll_opy_ (u"ࠬࡴ࡯࡯ࡄࡖࡸࡦࡩ࡫ࡊࡰࡩࡶࡦࡇ࠱࠲ࡻࡆ࡬ࡷࡵ࡭ࡦࡑࡳࡸ࡮ࡵ࡮ࡴࠩ᝭") in data:
          self.bstack11ll11l11l1_opy_(data[bstack111l1ll_opy_ (u"࠭࡮ࡰࡰࡅࡗࡹࡧࡣ࡬ࡋࡱࡪࡷࡧࡁ࠲࠳ࡼࡇ࡭ࡸ࡯࡮ࡧࡒࡴࡹ࡯࡯࡯ࡵࠪᝮ")])
    except:
      pass
  def bstack11ll11l11l1_opy_(self, bstack11ll1l11ll1_opy_):
    if bstack11ll1l11ll1_opy_ != None:
      self.bstack11ll1l11ll1_opy_ = bstack11ll1l11ll1_opy_
  def bstack1llllll1ll_opy_(self, scripts):
    if scripts != None:
      self.perform_scan = scripts.get(bstack111l1ll_opy_ (u"ࠧࡴࡥࡤࡲࠬᝯ"),bstack111l1ll_opy_ (u"ࠨࠩᝰ"))
      self.bstack11ll11lll1_opy_ = scripts.get(bstack111l1ll_opy_ (u"ࠩࡪࡩࡹࡘࡥࡴࡷ࡯ࡸࡸ࠭᝱"),bstack111l1ll_opy_ (u"ࠪࠫᝲ"))
      self.bstack1ll1l1l1l1_opy_ = scripts.get(bstack111l1ll_opy_ (u"ࠫ࡬࡫ࡴࡓࡧࡶࡹࡱࡺࡳࡔࡷࡰࡱࡦࡸࡹࠨᝳ"),bstack111l1ll_opy_ (u"ࠬ࠭᝴"))
      self.bstack11ll11lll1l_opy_ = scripts.get(bstack111l1ll_opy_ (u"࠭ࡳࡢࡸࡨࡖࡪࡹࡵ࡭ࡶࡶࠫ᝵"),bstack111l1ll_opy_ (u"ࠧࠨ᝶"))
  def bstack11ll1l111ll_opy_(self, commands_to_wrap):
    if commands_to_wrap != None and len(commands_to_wrap) != 0:
      self.commands_to_wrap = commands_to_wrap
  def store(self):
    try:
      with open(self.bstack11ll11l1111_opy_, bstack111l1ll_opy_ (u"ࠨࡹࠪ᝷")) as file:
        json.dump({
          bstack111l1ll_opy_ (u"ࠤࡦࡳࡲࡳࡡ࡯ࡦࡶࠦ᝸"): self.commands_to_wrap,
          bstack111l1ll_opy_ (u"ࠥࡷࡨࡸࡩࡱࡶࡶࠦ᝹"): {
            bstack111l1ll_opy_ (u"ࠦࡸࡩࡡ࡯ࠤ᝺"): self.perform_scan,
            bstack111l1ll_opy_ (u"ࠧ࡭ࡥࡵࡔࡨࡷࡺࡲࡴࡴࠤ᝻"): self.bstack11ll11lll1_opy_,
            bstack111l1ll_opy_ (u"ࠨࡧࡦࡶࡕࡩࡸࡻ࡬ࡵࡵࡖࡹࡲࡳࡡࡳࡻࠥ᝼"): self.bstack1ll1l1l1l1_opy_,
            bstack111l1ll_opy_ (u"ࠢࡴࡣࡹࡩࡗ࡫ࡳࡶ࡮ࡷࡷࠧ᝽"): self.bstack11ll11lll1l_opy_
          },
          bstack111l1ll_opy_ (u"ࠣࡰࡲࡲࡇ࡙ࡴࡢࡥ࡮ࡍࡳ࡬ࡲࡢࡃ࠴࠵ࡾࡉࡨࡳࡱࡰࡩࡔࡶࡴࡪࡱࡱࡷࠧ᝾"): self.bstack11ll1l11ll1_opy_
        }, file)
    except Exception as e:
      logger.error(bstack111l1ll_opy_ (u"ࠤࡈࡶࡷࡵࡲࠡࡹ࡫࡭ࡱ࡫ࠠࡴࡶࡲࡶ࡮ࡴࡧࠡࡥࡲࡱࡲࡧ࡮ࡥࡵ࠽ࠤࢀࢃࠢ᝿").format(e))
      pass
  def bstack11ll1l1ll_opy_(self, command_name):
    try:
      return any(command.get(bstack111l1ll_opy_ (u"ࠪࡲࡦࡳࡥࠨក")) == command_name for command in self.commands_to_wrap)
    except:
      return False
bstack11llll111l_opy_ = bstack11ll111lll1_opy_()