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
import re
import sys
import json
import time
import shutil
import tempfile
import requests
import subprocess
from threading import Thread
from os.path import expanduser
from bstack_utils.constants import *
from requests.auth import HTTPBasicAuth
from bstack_utils.helper import bstack11111lll1_opy_
from bstack_utils.measure import measure
from bstack_utils.bstack111111111_opy_ import bstack1l11l11l11_opy_
class bstack1ll1l1l111_opy_:
  working_dir = os.getcwd()
  bstack111ll11l1_opy_ = False
  config = {}
  bstack111lll11l1l_opy_ = bstack111l1ll_opy_ (u"ࠨࠩỠ")
  binary_path = bstack111l1ll_opy_ (u"ࠩࠪỡ")
  bstack1111l11l1l1_opy_ = bstack111l1ll_opy_ (u"ࠪࠫỢ")
  bstack11l11111l_opy_ = False
  bstack111111l111l_opy_ = None
  bstack111111l1l1l_opy_ = {}
  bstack11111ll11l1_opy_ = 300
  bstack11111ll1lll_opy_ = False
  logger = None
  bstack11111l1l1l1_opy_ = False
  bstack1ll1llll1_opy_ = False
  percy_build_id = None
  bstack111111l1ll1_opy_ = bstack111l1ll_opy_ (u"ࠫࠬợ")
  bstack111111ll1l1_opy_ = {
    bstack111l1ll_opy_ (u"ࠬࡩࡨࡳࡱࡰࡩࠬỤ") : 1,
    bstack111l1ll_opy_ (u"࠭ࡦࡪࡴࡨࡪࡴࡾࠧụ") : 2,
    bstack111l1ll_opy_ (u"ࠧࡦࡦࡪࡩࠬỦ") : 3,
    bstack111l1ll_opy_ (u"ࠨࡵࡤࡪࡦࡸࡩࠨủ") : 4
  }
  def __init__(self) -> None: pass
  def bstack1111l11l111_opy_(self):
    bstack11111l1l1ll_opy_ = bstack111l1ll_opy_ (u"ࠩࠪỨ")
    bstack111111l1lll_opy_ = sys.platform
    bstack1111l1111ll_opy_ = bstack111l1ll_opy_ (u"ࠪࡴࡪࡸࡣࡺࠩứ")
    if re.match(bstack111l1ll_opy_ (u"ࠦࡩࡧࡲࡸ࡫ࡱࢀࡲࡧࡣࠡࡱࡶࠦỪ"), bstack111111l1lll_opy_) != None:
      bstack11111l1l1ll_opy_ = bstack11l1ll11lll_opy_ + bstack111l1ll_opy_ (u"ࠧ࠵ࡰࡦࡴࡦࡽ࠲ࡵࡳࡹ࠰ࡽ࡭ࡵࠨừ")
      self.bstack111111l1ll1_opy_ = bstack111l1ll_opy_ (u"࠭࡭ࡢࡥࠪỬ")
    elif re.match(bstack111l1ll_opy_ (u"ࠢ࡮ࡵࡺ࡭ࡳࢂ࡭ࡴࡻࡶࢀࡲ࡯࡮ࡨࡹࡿࡧࡾ࡭ࡷࡪࡰࡿࡦࡨࡩࡷࡪࡰࡿࡻ࡮ࡴࡣࡦࡾࡨࡱࡨࢂࡷࡪࡰ࠶࠶ࠧử"), bstack111111l1lll_opy_) != None:
      bstack11111l1l1ll_opy_ = bstack11l1ll11lll_opy_ + bstack111l1ll_opy_ (u"ࠣ࠱ࡳࡩࡷࡩࡹ࠮ࡹ࡬ࡲ࠳ࢀࡩࡱࠤỮ")
      bstack1111l1111ll_opy_ = bstack111l1ll_opy_ (u"ࠤࡳࡩࡷࡩࡹ࠯ࡧࡻࡩࠧữ")
      self.bstack111111l1ll1_opy_ = bstack111l1ll_opy_ (u"ࠪࡻ࡮ࡴࠧỰ")
    else:
      bstack11111l1l1ll_opy_ = bstack11l1ll11lll_opy_ + bstack111l1ll_opy_ (u"ࠦ࠴ࡶࡥࡳࡥࡼ࠱ࡱ࡯࡮ࡶࡺ࠱ࡾ࡮ࡶࠢự")
      self.bstack111111l1ll1_opy_ = bstack111l1ll_opy_ (u"ࠬࡲࡩ࡯ࡷࡻࠫỲ")
    return bstack11111l1l1ll_opy_, bstack1111l1111ll_opy_
  def bstack1111l1l111l_opy_(self):
    try:
      bstack11111lll1l1_opy_ = [os.path.join(expanduser(bstack111l1ll_opy_ (u"ࠨࡾࠣỳ")), bstack111l1ll_opy_ (u"ࠧ࠯ࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࠧỴ")), self.working_dir, tempfile.gettempdir()]
      for path in bstack11111lll1l1_opy_:
        if(self.bstack11111l11l11_opy_(path)):
          return path
      raise bstack111l1ll_opy_ (u"ࠣࡗࡱࡥࡧࡲࡥࠡࡶࡲࠤࡩࡵࡷ࡯࡮ࡲࡥࡩࠦࡰࡦࡴࡦࡽࠥࡨࡩ࡯ࡣࡵࡽࠧỵ")
    except Exception as e:
      self.logger.error(bstack111l1ll_opy_ (u"ࠤࡉࡥ࡮ࡲࡥࡥࠢࡷࡳࠥ࡬ࡩ࡯ࡦࠣࡥࡻࡧࡩ࡭ࡣࡥࡰࡪࠦࡰࡢࡶ࡫ࠤ࡫ࡵࡲࠡࡲࡨࡶࡨࡿࠠࡥࡱࡺࡲࡱࡵࡡࡥ࠮ࠣࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦ࠭ࠡࡽࢀࠦỶ").format(e))
  def bstack11111l11l11_opy_(self, path):
    try:
      if not os.path.exists(path):
        os.makedirs(path)
      return True
    except:
      return False
  def bstack111111lllll_opy_(self, bstack111111l1111_opy_):
    return os.path.join(bstack111111l1111_opy_, self.bstack111lll11l1l_opy_ + bstack111l1ll_opy_ (u"ࠥ࠲ࡪࡺࡡࡨࠤỷ"))
  def bstack11111l1llll_opy_(self, bstack111111l1111_opy_, bstack11111ll111l_opy_):
    if not bstack11111ll111l_opy_: return
    try:
      bstack111111lll11_opy_ = self.bstack111111lllll_opy_(bstack111111l1111_opy_)
      with open(bstack111111lll11_opy_, bstack111l1ll_opy_ (u"ࠦࡼࠨỸ")) as f:
        f.write(bstack11111ll111l_opy_)
        self.logger.debug(bstack111l1ll_opy_ (u"࡙ࠧࡡࡷࡧࡧࠤࡳ࡫ࡷࠡࡇࡗࡥ࡬ࠦࡦࡰࡴࠣࡴࡪࡸࡣࡺࠤỹ"))
    except Exception as e:
      self.logger.error(bstack111l1ll_opy_ (u"ࠨࡕ࡯ࡣࡥࡰࡪࠦࡴࡰࠢࡶࡥࡻ࡫ࠠࡵࡪࡨࠤࡪࡺࡡࡨ࠮ࠣࡩࡷࡸ࡯ࡳ࠼ࠣࡿࢂࠨỺ").format(e))
  def bstack1111l11l11l_opy_(self, bstack111111l1111_opy_):
    try:
      bstack111111lll11_opy_ = self.bstack111111lllll_opy_(bstack111111l1111_opy_)
      if os.path.exists(bstack111111lll11_opy_):
        with open(bstack111111lll11_opy_, bstack111l1ll_opy_ (u"ࠢࡳࠤỻ")) as f:
          bstack11111ll111l_opy_ = f.read().strip()
          return bstack11111ll111l_opy_ if bstack11111ll111l_opy_ else None
    except Exception as e:
      self.logger.error(bstack111l1ll_opy_ (u"ࠣࡈࡤ࡭ࡱ࡫ࡤࠡ࡮ࡲࡥࡩ࡯࡮ࡨࠢࡈࡘࡦ࡭ࠬࠡࡧࡵࡶࡴࡸ࠺ࠡࡽࢀࠦỼ").format(e))
  def bstack1111l11111l_opy_(self, bstack111111l1111_opy_, bstack11111l1l1ll_opy_):
    bstack11111l1ll1l_opy_ = self.bstack1111l11l11l_opy_(bstack111111l1111_opy_)
    if bstack11111l1ll1l_opy_:
      try:
        bstack1111l111lll_opy_ = self.bstack11111l11lll_opy_(bstack11111l1ll1l_opy_, bstack11111l1l1ll_opy_)
        if not bstack1111l111lll_opy_:
          self.logger.debug(bstack111l1ll_opy_ (u"ࠤࡓࡩࡷࡩࡹࠡࡤ࡬ࡲࡦࡸࡹࠡ࡫ࡶࠤࡺࡶࠠࡵࡱࠣࡨࡦࡺࡥࠡࠪࡈࡘࡦ࡭ࠠࡶࡰࡦ࡬ࡦࡴࡧࡦࡦࠬࠦỽ"))
          return True
        self.logger.debug(bstack111l1ll_opy_ (u"ࠥࡒࡪࡽࠠࡑࡧࡵࡧࡾࠦࡢࡪࡰࡤࡶࡾࠦࡶࡦࡴࡶ࡭ࡴࡴࠠࡢࡸࡤ࡭ࡱࡧࡢ࡭ࡧ࠯ࠤࡩࡵࡷ࡯࡮ࡲࡥࡩ࡯࡮ࡨࠢࡸࡴࡩࡧࡴࡦࠤỾ"))
        return False
      except Exception as e:
        self.logger.warn(bstack111l1ll_opy_ (u"ࠦࡋࡧࡩ࡭ࡧࡧࠤࡹࡵࠠࡤࡪࡨࡧࡰࠦࡦࡰࡴࠣࡦ࡮ࡴࡡࡳࡻࠣࡹࡵࡪࡡࡵࡧࡶ࠰ࠥࡻࡳࡪࡰࡪࠤࡪࡾࡩࡴࡶ࡬ࡲ࡬ࠦࡢࡪࡰࡤࡶࡾࡀࠠࡼࡿࠥỿ").format(e))
    return False
  def bstack11111l11lll_opy_(self, bstack11111l1ll1l_opy_, bstack11111l1l1ll_opy_):
    try:
      headers = {
        bstack111l1ll_opy_ (u"ࠧࡏࡦ࠮ࡐࡲࡲࡪ࠳ࡍࡢࡶࡦ࡬ࠧἀ"): bstack11111l1ll1l_opy_
      }
      response = bstack11111lll1_opy_(bstack111l1ll_opy_ (u"࠭ࡇࡆࡖࠪἁ"), bstack11111l1l1ll_opy_, {}, {bstack111l1ll_opy_ (u"ࠢࡩࡧࡤࡨࡪࡸࡳࠣἂ"): headers})
      if response.status_code == 304:
        return False
      return True
    except Exception as e:
      raise(bstack111l1ll_opy_ (u"ࠣࡇࡵࡶࡴࡸࠠࡤࡪࡨࡧࡰ࡯࡮ࡨࠢࡩࡳࡷࠦࡐࡦࡴࡦࡽࠥࡨࡩ࡯ࡣࡵࡽࠥࡻࡰࡥࡣࡷࡩࡸࡀࠠࡼࡿࠥἃ").format(e))
  @measure(event_name=EVENTS.bstack11l1l1ll1l1_opy_, stage=STAGE.bstack1l11lllll1_opy_)
  def bstack1111l1l11l1_opy_(self, bstack11111l1l1ll_opy_, bstack1111l1111ll_opy_):
    try:
      bstack11111l111ll_opy_ = self.bstack1111l1l111l_opy_()
      bstack111111llll1_opy_ = os.path.join(bstack11111l111ll_opy_, bstack111l1ll_opy_ (u"ࠩࡳࡩࡷࡩࡹ࠯ࡼ࡬ࡴࠬἄ"))
      bstack11111llll1l_opy_ = os.path.join(bstack11111l111ll_opy_, bstack1111l1111ll_opy_)
      if self.bstack1111l11111l_opy_(bstack11111l111ll_opy_, bstack11111l1l1ll_opy_): # if bstack111111ll111_opy_, bstack1l1l11l11ll_opy_ bstack11111ll111l_opy_ is bstack11111lllll1_opy_ to bstack11l111111l1_opy_ version available (response 304)
        if os.path.exists(bstack11111llll1l_opy_):
          self.logger.info(bstack111l1ll_opy_ (u"ࠥࡔࡪࡸࡣࡺࠢࡥ࡭ࡳࡧࡲࡺࠢࡩࡳࡺࡴࡤࠡ࡫ࡱࠤࢀࢃࠬࠡࡵ࡮࡭ࡵࡶࡩ࡯ࡩࠣࡨࡴࡽ࡮࡭ࡱࡤࡨࠧἅ").format(bstack11111llll1l_opy_))
          return bstack11111llll1l_opy_
        if os.path.exists(bstack111111llll1_opy_):
          self.logger.info(bstack111l1ll_opy_ (u"ࠦࡕ࡫ࡲࡤࡻࠣࡾ࡮ࡶࠠࡧࡱࡸࡲࡩࠦࡩ࡯ࠢࡾࢁ࠱ࠦࡵ࡯ࡼ࡬ࡴࡵ࡯࡮ࡨࠤἆ").format(bstack111111llll1_opy_))
          return self.bstack11111ll1111_opy_(bstack111111llll1_opy_, bstack1111l1111ll_opy_)
      self.logger.info(bstack111l1ll_opy_ (u"ࠧࡊ࡯ࡸࡰ࡯ࡳࡦࡪࡩ࡯ࡩࠣࡴࡪࡸࡣࡺࠢࡥ࡭ࡳࡧࡲࡺࠢࡩࡶࡴࡳࠠࡼࡿࠥἇ").format(bstack11111l1l1ll_opy_))
      response = bstack11111lll1_opy_(bstack111l1ll_opy_ (u"࠭ࡇࡆࡖࠪἈ"), bstack11111l1l1ll_opy_, {}, {})
      if response.status_code == 200:
        bstack111111l11ll_opy_ = response.headers.get(bstack111l1ll_opy_ (u"ࠢࡆࡖࡤ࡫ࠧἉ"), bstack111l1ll_opy_ (u"ࠣࠤἊ"))
        if bstack111111l11ll_opy_:
          self.bstack11111l1llll_opy_(bstack11111l111ll_opy_, bstack111111l11ll_opy_)
        with open(bstack111111llll1_opy_, bstack111l1ll_opy_ (u"ࠩࡺࡦࠬἋ")) as file:
          file.write(response.content)
        self.logger.info(bstack111l1ll_opy_ (u"ࠥࡈࡴࡽ࡮࡭ࡱࡤࡨࡪࡪࠠࡱࡧࡵࡧࡾࠦࡢࡪࡰࡤࡶࡾࠦࡡ࡯ࡦࠣࡷࡦࡼࡥࡥࠢࡤࡸࠥࢁࡽࠣἌ").format(bstack111111llll1_opy_))
        return self.bstack11111ll1111_opy_(bstack111111llll1_opy_, bstack1111l1111ll_opy_)
      else:
        raise(bstack111l1ll_opy_ (u"ࠦࡋࡧࡩ࡭ࡧࡧࠤࡹࡵࠠࡥࡱࡺࡲࡱࡵࡡࡥࠢࡷ࡬ࡪࠦࡦࡪ࡮ࡨ࠲࡙ࠥࡴࡢࡶࡸࡷࠥࡩ࡯ࡥࡧ࠽ࠤࢀࢃࠢἍ").format(response.status_code))
    except Exception as e:
      self.logger.error(bstack111l1ll_opy_ (u"࡛ࠧ࡮ࡢࡤ࡯ࡩࠥࡺ࡯ࠡࡦࡲࡻࡳࡲ࡯ࡢࡦࠣࡴࡪࡸࡣࡺࠢࡥ࡭ࡳࡧࡲࡺ࠼ࠣࡿࢂࠨἎ").format(e))
  def bstack11111l1111l_opy_(self, bstack11111l1l1ll_opy_, bstack1111l1111ll_opy_):
    try:
      retry = 2
      bstack11111llll1l_opy_ = None
      bstack1111l1l1111_opy_ = False
      while retry > 0:
        bstack11111llll1l_opy_ = self.bstack1111l1l11l1_opy_(bstack11111l1l1ll_opy_, bstack1111l1111ll_opy_)
        bstack1111l1l1111_opy_ = self.bstack111111ll11l_opy_(bstack11111l1l1ll_opy_, bstack1111l1111ll_opy_, bstack11111llll1l_opy_)
        if bstack1111l1l1111_opy_:
          break
        retry -= 1
      return bstack11111llll1l_opy_, bstack1111l1l1111_opy_
    except Exception as e:
      self.logger.error(bstack111l1ll_opy_ (u"ࠨࡕ࡯ࡣࡥࡰࡪࠦࡴࡰࠢࡪࡩࡹࠦࡰࡦࡴࡦࡽࠥࡨࡩ࡯ࡣࡵࡽࠥࡶࡡࡵࡪࠥἏ").format(e))
    return bstack11111llll1l_opy_, False
  def bstack111111ll11l_opy_(self, bstack11111l1l1ll_opy_, bstack1111l1111ll_opy_, bstack11111llll1l_opy_, bstack111111lll1l_opy_ = 0):
    if bstack111111lll1l_opy_ > 1:
      return False
    if bstack11111llll1l_opy_ == None or os.path.exists(bstack11111llll1l_opy_) == False:
      self.logger.warn(bstack111l1ll_opy_ (u"ࠢࡑࡧࡵࡧࡾࠦࡰࡢࡶ࡫ࠤࡳࡵࡴࠡࡨࡲࡹࡳࡪࠬࠡࡴࡨࡸࡷࡿࡩ࡯ࡩࠣࡨࡴࡽ࡮࡭ࡱࡤࡨࠧἐ"))
      return False
    bstack1111l11ll1l_opy_ = bstack111l1ll_opy_ (u"ࡳࠤࡡ࠲࠯ࡆࡰࡦࡴࡦࡽ࠴ࡩ࡬ࡪࠢ࡟ࡨ࠰ࡢ࠮࡝ࡦ࠮ࡠ࠳ࡢࡤࠬࠤἑ")
    command = bstack111l1ll_opy_ (u"ࠩࡾࢁࠥ࠳࠭ࡷࡧࡵࡷ࡮ࡵ࡮ࠨἒ").format(bstack11111llll1l_opy_)
    bstack1111l111ll1_opy_ = subprocess.check_output(command, shell=True, text=True)
    if re.match(bstack1111l11ll1l_opy_, bstack1111l111ll1_opy_) != None:
      return True
    else:
      self.logger.error(bstack111l1ll_opy_ (u"ࠥࡔࡪࡸࡣࡺࠢࡹࡩࡷࡹࡩࡰࡰࠣࡧ࡭࡫ࡣ࡬ࠢࡩࡥ࡮ࡲࡥࡥࠤἓ"))
      return False
  def bstack11111ll1111_opy_(self, bstack111111llll1_opy_, bstack1111l1111ll_opy_):
    try:
      working_dir = os.path.dirname(bstack111111llll1_opy_)
      shutil.unpack_archive(bstack111111llll1_opy_, working_dir)
      bstack11111llll1l_opy_ = os.path.join(working_dir, bstack1111l1111ll_opy_)
      os.chmod(bstack11111llll1l_opy_, 0o755)
      return bstack11111llll1l_opy_
    except Exception as e:
      self.logger.error(bstack111l1ll_opy_ (u"࡚ࠦࡴࡡࡣ࡮ࡨࠤࡹࡵࠠࡶࡰࡽ࡭ࡵࠦࡰࡦࡴࡦࡽࠥࡨࡩ࡯ࡣࡵࡽࠧἔ"))
  def bstack11111llllll_opy_(self):
    try:
      bstack111111l1l11_opy_ = self.config.get(bstack111l1ll_opy_ (u"ࠬࡶࡥࡳࡥࡼࠫἕ"))
      bstack11111llllll_opy_ = bstack111111l1l11_opy_ or (bstack111111l1l11_opy_ is None and self.bstack111ll11l1_opy_)
      if not bstack11111llllll_opy_ or self.config.get(bstack111l1ll_opy_ (u"࠭ࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࠩ἖"), None) not in bstack11l1llll11l_opy_:
        return False
      self.bstack11l11111l_opy_ = True
      return True
    except Exception as e:
      self.logger.error(bstack111l1ll_opy_ (u"ࠢࡖࡰࡤࡦࡱ࡫ࠠࡵࡱࠣࡨࡪࡺࡥࡤࡶࠣࡴࡪࡸࡣࡺ࠮ࠣࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡻࡾࠤ἗").format(e))
  def bstack11111l11l1l_opy_(self):
    try:
      bstack11111l11l1l_opy_ = self.percy_capture_mode
      return bstack11111l11l1l_opy_
    except Exception as e:
      self.logger.error(bstack111l1ll_opy_ (u"ࠣࡗࡱࡥࡧࡲࡥࠡࡶࡲࠤࡩ࡫ࡴࡦࡥࡷࠤࡵ࡫ࡲࡤࡻࠣࡧࡦࡶࡴࡶࡴࡨࠤࡲࡵࡤࡦ࠮ࠣࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡻࡾࠤἘ").format(e))
  def init(self, bstack111ll11l1_opy_, config, logger):
    self.bstack111ll11l1_opy_ = bstack111ll11l1_opy_
    self.config = config
    self.logger = logger
    if not self.bstack11111llllll_opy_():
      return
    self.bstack111111l1l1l_opy_ = config.get(bstack111l1ll_opy_ (u"ࠩࡳࡩࡷࡩࡹࡐࡲࡷ࡭ࡴࡴࡳࠨἙ"), {})
    self.percy_capture_mode = config.get(bstack111l1ll_opy_ (u"ࠪࡴࡪࡸࡣࡺࡅࡤࡴࡹࡻࡲࡦࡏࡲࡨࡪ࠭Ἒ"))
    try:
      bstack11111l1l1ll_opy_, bstack1111l1111ll_opy_ = self.bstack1111l11l111_opy_()
      self.bstack111lll11l1l_opy_ = bstack1111l1111ll_opy_
      bstack11111llll1l_opy_, bstack1111l1l1111_opy_ = self.bstack11111l1111l_opy_(bstack11111l1l1ll_opy_, bstack1111l1111ll_opy_)
      if bstack1111l1l1111_opy_:
        self.binary_path = bstack11111llll1l_opy_
        thread = Thread(target=self.bstack11111ll11ll_opy_)
        thread.start()
      else:
        self.bstack11111l1l1l1_opy_ = True
        self.logger.error(bstack111l1ll_opy_ (u"ࠦࡎࡴࡶࡢ࡮࡬ࡨࠥࡶࡥࡳࡥࡼࠤࡵࡧࡴࡩࠢࡩࡳࡺࡴࡤࠡ࠯ࠣࡿࢂ࠲ࠠࡖࡰࡤࡦࡱ࡫ࠠࡵࡱࠣࡷࡹࡧࡲࡵࠢࡓࡩࡷࡩࡹࠣἛ").format(bstack11111llll1l_opy_))
    except Exception as e:
      self.logger.error(bstack111l1ll_opy_ (u"࡛ࠧ࡮ࡢࡤ࡯ࡩࠥࡺ࡯ࠡࡵࡷࡥࡷࡺࠠࡱࡧࡵࡧࡾ࠲ࠠࡆࡺࡦࡩࡵࡺࡩࡰࡰࠣࡿࢂࠨἜ").format(e))
  def bstack111111ll1ll_opy_(self):
    try:
      logfile = os.path.join(self.working_dir, bstack111l1ll_opy_ (u"࠭࡬ࡰࡩࠪἝ"), bstack111l1ll_opy_ (u"ࠧࡱࡧࡵࡧࡾ࠴࡬ࡰࡩࠪ἞"))
      os.makedirs(os.path.dirname(logfile)) if not os.path.exists(os.path.dirname(logfile)) else None
      self.logger.debug(bstack111l1ll_opy_ (u"ࠣࡒࡸࡷ࡭࡯࡮ࡨࠢࡳࡩࡷࡩࡹࠡ࡮ࡲ࡫ࡸࠦࡡࡵࠢࡾࢁࠧ἟").format(logfile))
      self.bstack1111l11l1l1_opy_ = logfile
    except Exception as e:
      self.logger.error(bstack111l1ll_opy_ (u"ࠤࡘࡲࡦࡨ࡬ࡦࠢࡷࡳࠥࡹࡥࡵࠢࡳࡩࡷࡩࡹࠡ࡮ࡲ࡫ࠥࡶࡡࡵࡪ࠯ࠤࡊࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡼࡿࠥἠ").format(e))
  @measure(event_name=EVENTS.bstack11l1ll1111l_opy_, stage=STAGE.bstack1l11lllll1_opy_)
  def bstack11111ll11ll_opy_(self):
    bstack111111l11l1_opy_ = self.bstack11111l11ll1_opy_()
    if bstack111111l11l1_opy_ == None:
      self.bstack11111l1l1l1_opy_ = True
      self.logger.error(bstack111l1ll_opy_ (u"ࠥࡔࡪࡸࡣࡺࠢࡷࡳࡰ࡫࡮ࠡࡰࡲࡸࠥ࡬࡯ࡶࡰࡧ࠰ࠥࡌࡡࡪ࡮ࡨࡨࠥࡺ࡯ࠡࡵࡷࡥࡷࡺࠠࡱࡧࡵࡧࡾࠨἡ"))
      return False
    bstack11111l1lll1_opy_ = [bstack111l1ll_opy_ (u"ࠦࡦࡶࡰ࠻ࡧࡻࡩࡨࡀࡳࡵࡣࡵࡸࠧἢ") if self.bstack111ll11l1_opy_ else bstack111l1ll_opy_ (u"ࠬ࡫ࡸࡦࡥ࠽ࡷࡹࡧࡲࡵࠩἣ")]
    bstack111l1ll11ll_opy_ = self.bstack1111l111111_opy_()
    if bstack111l1ll11ll_opy_ != None:
      bstack11111l1lll1_opy_.append(bstack111l1ll_opy_ (u"ࠨ࠭ࡤࠢࡾࢁࠧἤ").format(bstack111l1ll11ll_opy_))
    env = os.environ.copy()
    env[bstack111l1ll_opy_ (u"ࠢࡑࡇࡕࡇ࡞ࡥࡔࡐࡍࡈࡒࠧἥ")] = bstack111111l11l1_opy_
    env[bstack111l1ll_opy_ (u"ࠣࡖࡋࡣࡇ࡛ࡉࡍࡆࡢ࡙࡚ࡏࡄࠣἦ")] = os.environ.get(bstack111l1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡎࡕࡃࡡࡘ࡙ࡎࡊࠧἧ"), bstack111l1ll_opy_ (u"ࠪࠫἨ"))
    bstack1111l111l11_opy_ = [self.binary_path]
    self.bstack111111ll1ll_opy_()
    self.bstack111111l111l_opy_ = self.bstack11111l111l1_opy_(bstack1111l111l11_opy_ + bstack11111l1lll1_opy_, env)
    self.logger.debug(bstack111l1ll_opy_ (u"ࠦࡘࡺࡡࡳࡶ࡬ࡲ࡬ࠦࡈࡦࡣ࡯ࡸ࡭ࠦࡃࡩࡧࡦ࡯ࠧἩ"))
    bstack111111lll1l_opy_ = 0
    while self.bstack111111l111l_opy_.poll() == None:
      bstack1111l11lll1_opy_ = self.bstack11111ll1l11_opy_()
      if bstack1111l11lll1_opy_:
        self.logger.debug(bstack111l1ll_opy_ (u"ࠧࡎࡥࡢ࡮ࡷ࡬ࠥࡉࡨࡦࡥ࡮ࠤࡸࡻࡣࡤࡧࡶࡷ࡫ࡻ࡬ࠣἪ"))
        self.bstack11111ll1lll_opy_ = True
        return True
      bstack111111lll1l_opy_ += 1
      self.logger.debug(bstack111l1ll_opy_ (u"ࠨࡈࡦࡣ࡯ࡸ࡭ࠦࡃࡩࡧࡦ࡯ࠥࡘࡥࡵࡴࡼࠤ࠲ࠦࡻࡾࠤἫ").format(bstack111111lll1l_opy_))
      time.sleep(2)
    self.logger.error(bstack111l1ll_opy_ (u"ࠢࡇࡣ࡬ࡰࡪࡪࠠࡵࡱࠣࡷࡹࡧࡲࡵࠢࡳࡩࡷࡩࡹ࠭ࠢࡋࡩࡦࡲࡴࡩࠢࡆ࡬ࡪࡩ࡫ࠡࡈࡤ࡭ࡱ࡫ࡤࠡࡣࡩࡸࡪࡸࠠࡼࡿࠣࡥࡹࡺࡥ࡮ࡲࡷࡷࠧἬ").format(bstack111111lll1l_opy_))
    self.bstack11111l1l1l1_opy_ = True
    return False
  def bstack11111ll1l11_opy_(self, bstack111111lll1l_opy_ = 0):
    if bstack111111lll1l_opy_ > 10:
      return False
    try:
      bstack1111l1111l1_opy_ = os.environ.get(bstack111l1ll_opy_ (u"ࠨࡒࡈࡖࡈ࡟࡟ࡔࡇࡕ࡚ࡊࡘ࡟ࡂࡆࡇࡖࡊ࡙ࡓࠨἭ"), bstack111l1ll_opy_ (u"ࠩ࡫ࡸࡹࡶ࠺࠰࠱࡯ࡳࡨࡧ࡬ࡩࡱࡶࡸ࠿࠻࠳࠴࠺ࠪἮ"))
      bstack11111l1ll11_opy_ = bstack1111l1111l1_opy_ + bstack11l1l1llll1_opy_
      response = requests.get(bstack11111l1ll11_opy_)
      data = response.json()
      self.percy_build_id = data.get(bstack111l1ll_opy_ (u"ࠪࡦࡺ࡯࡬ࡥࠩἯ"), {}).get(bstack111l1ll_opy_ (u"ࠫ࡮ࡪࠧἰ"), None)
      return True
    except:
      self.logger.debug(bstack111l1ll_opy_ (u"ࠧࡋࡲࡳࡱࡵࠤࡴࡩࡣࡶࡴࡵࡩࡩࠦࡷࡩ࡫࡯ࡩࠥࡶࡲࡰࡥࡨࡷࡸ࡯࡮ࡨࠢ࡫ࡩࡦࡲࡴࡩࠢࡦ࡬ࡪࡩ࡫ࠡࡴࡨࡷࡵࡵ࡮ࡴࡧࠥἱ"))
      return False
  def bstack11111l11ll1_opy_(self):
    bstack11111lll11l_opy_ = bstack111l1ll_opy_ (u"࠭ࡡࡱࡲࠪἲ") if self.bstack111ll11l1_opy_ else bstack111l1ll_opy_ (u"ࠧࡢࡷࡷࡳࡲࡧࡴࡦࠩἳ")
    bstack11111l1l11l_opy_ = bstack111l1ll_opy_ (u"ࠣࡷࡱࡨࡪ࡬ࡩ࡯ࡧࡧࠦἴ") if self.config.get(bstack111l1ll_opy_ (u"ࠩࡳࡩࡷࡩࡹࠨἵ")) is None else True
    bstack11ll111ll11_opy_ = bstack111l1ll_opy_ (u"ࠥࡥࡵ࡯࠯ࡢࡲࡳࡣࡵ࡫ࡲࡤࡻ࠲࡫ࡪࡺ࡟ࡱࡴࡲ࡮ࡪࡩࡴࡠࡶࡲ࡯ࡪࡴ࠿࡯ࡣࡰࡩࡂࢁࡽࠧࡶࡼࡴࡪࡃࡻࡾࠨࡳࡩࡷࡩࡹ࠾ࡽࢀࠦἶ").format(self.config[bstack111l1ll_opy_ (u"ࠫࡵࡸ࡯࡫ࡧࡦࡸࡓࡧ࡭ࡦࠩἷ")], bstack11111lll11l_opy_, bstack11111l1l11l_opy_)
    if self.percy_capture_mode:
      bstack11ll111ll11_opy_ += bstack111l1ll_opy_ (u"ࠧࠬࡰࡦࡴࡦࡽࡤࡩࡡࡱࡶࡸࡶࡪࡥ࡭ࡰࡦࡨࡁࢀࢃࠢἸ").format(self.percy_capture_mode)
    uri = bstack1l11l11l11_opy_(bstack11ll111ll11_opy_)
    try:
      response = bstack11111lll1_opy_(bstack111l1ll_opy_ (u"࠭ࡇࡆࡖࠪἹ"), uri, {}, {bstack111l1ll_opy_ (u"ࠧࡢࡷࡷ࡬ࠬἺ"): (self.config[bstack111l1ll_opy_ (u"ࠨࡷࡶࡩࡷࡔࡡ࡮ࡧࠪἻ")], self.config[bstack111l1ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡳࡴࡍࡨࡽࠬἼ")])})
      if response.status_code == 200:
        data = response.json()
        self.bstack11l11111l_opy_ = data.get(bstack111l1ll_opy_ (u"ࠪࡷࡺࡩࡣࡦࡵࡶࠫἽ"))
        self.percy_capture_mode = data.get(bstack111l1ll_opy_ (u"ࠫࡵ࡫ࡲࡤࡻࡢࡧࡦࡶࡴࡶࡴࡨࡣࡲࡵࡤࡦࠩἾ"))
        os.environ[bstack111l1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡕࡋࡒࡄ࡛ࠪἿ")] = str(self.bstack11l11111l_opy_)
        os.environ[bstack111l1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡖࡅࡓࡅ࡜ࡣࡈࡇࡐࡕࡗࡕࡉࡤࡓࡏࡅࡇࠪὀ")] = str(self.percy_capture_mode)
        if bstack11111l1l11l_opy_ == bstack111l1ll_opy_ (u"ࠢࡶࡰࡧࡩ࡫࡯࡮ࡦࡦࠥὁ") and str(self.bstack11l11111l_opy_).lower() == bstack111l1ll_opy_ (u"ࠣࡶࡵࡹࡪࠨὂ"):
          self.bstack1ll1llll1_opy_ = True
        if bstack111l1ll_opy_ (u"ࠤࡷࡳࡰ࡫࡮ࠣὃ") in data:
          return data[bstack111l1ll_opy_ (u"ࠥࡸࡴࡱࡥ࡯ࠤὄ")]
        else:
          raise bstack111l1ll_opy_ (u"࡙ࠫࡵ࡫ࡦࡰࠣࡒࡴࡺࠠࡇࡱࡸࡲࡩࠦ࠭ࠡࡽࢀࠫὅ").format(data)
      else:
        raise bstack111l1ll_opy_ (u"ࠧࡌࡡࡪ࡮ࡨࡨࠥࡺ࡯ࠡࡨࡨࡸࡨ࡮ࠠࡱࡧࡵࡧࡾࠦࡴࡰ࡭ࡨࡲ࠱ࠦࡒࡦࡵࡳࡳࡳࡹࡥࠡࡵࡷࡥࡹࡻࡳࠡ࠯ࠣࡿࢂ࠲ࠠࡓࡧࡶࡴࡴࡴࡳࡦࠢࡅࡳࡩࡿࠠ࠮ࠢࡾࢁࠧ὆").format(response.status_code, response.json())
    except Exception as e:
      self.logger.error(bstack111l1ll_opy_ (u"ࠨࡅࡹࡥࡨࡴࡹ࡯࡯࡯ࠢ࡬ࡲࠥࡩࡲࡦࡣࡷ࡭ࡳ࡭ࠠࡱࡧࡵࡧࡾࠦࡰࡳࡱ࡭ࡩࡨࡺࠢ὇").format(e))
  def bstack1111l111111_opy_(self):
    bstack11111lll111_opy_ = os.path.join(tempfile.gettempdir(), bstack111l1ll_opy_ (u"ࠢࡱࡧࡵࡧࡾࡉ࡯࡯ࡨ࡬࡫࠳ࡰࡳࡰࡰࠥὈ"))
    try:
      if bstack111l1ll_opy_ (u"ࠨࡸࡨࡶࡸ࡯࡯࡯ࠩὉ") not in self.bstack111111l1l1l_opy_:
        self.bstack111111l1l1l_opy_[bstack111l1ll_opy_ (u"ࠩࡹࡩࡷࡹࡩࡰࡰࠪὊ")] = 2
      with open(bstack11111lll111_opy_, bstack111l1ll_opy_ (u"ࠪࡻࠬὋ")) as fp:
        json.dump(self.bstack111111l1l1l_opy_, fp)
      return bstack11111lll111_opy_
    except Exception as e:
      self.logger.error(bstack111l1ll_opy_ (u"࡚ࠦࡴࡡࡣ࡮ࡨࠤࡹࡵࠠࡤࡴࡨࡥࡹ࡫ࠠࡱࡧࡵࡧࡾࠦࡣࡰࡰࡩ࠰ࠥࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡࡽࢀࠦὌ").format(e))
  def bstack11111l111l1_opy_(self, cmd, env = os.environ.copy()):
    try:
      if self.bstack111111l1ll1_opy_ == bstack111l1ll_opy_ (u"ࠬࡽࡩ࡯ࠩὍ"):
        bstack11111ll1l1l_opy_ = [bstack111l1ll_opy_ (u"࠭ࡣ࡮ࡦ࠱ࡩࡽ࡫ࠧ὎"), bstack111l1ll_opy_ (u"ࠧ࠰ࡥࠪ὏")]
        cmd = bstack11111ll1l1l_opy_ + cmd
      cmd = bstack111l1ll_opy_ (u"ࠨࠢࠪὐ").join(cmd)
      self.logger.debug(bstack111l1ll_opy_ (u"ࠤࡕࡹࡳࡴࡩ࡯ࡩࠣࡿࢂࠨὑ").format(cmd))
      with open(self.bstack1111l11l1l1_opy_, bstack111l1ll_opy_ (u"ࠥࡥࠧὒ")) as bstack1111l111l1l_opy_:
        process = subprocess.Popen(cmd, shell=True, stdout=bstack1111l111l1l_opy_, text=True, stderr=bstack1111l111l1l_opy_, env=env, universal_newlines=True)
      return process
    except Exception as e:
      self.bstack11111l1l1l1_opy_ = True
      self.logger.error(bstack111l1ll_opy_ (u"ࠦࡋࡧࡩ࡭ࡧࡧࠤࡹࡵࠠࡴࡶࡤࡶࡹࠦࡰࡦࡴࡦࡽࠥࡽࡩࡵࡪࠣࡧࡲࡪࠠ࠮ࠢࡾࢁ࠱ࠦࡅࡹࡥࡨࡴࡹ࡯࡯࡯࠼ࠣࡿࢂࠨὓ").format(cmd, e))
  def shutdown(self):
    try:
      if self.bstack11111ll1lll_opy_:
        self.logger.info(bstack111l1ll_opy_ (u"࡙ࠧࡴࡰࡲࡳ࡭ࡳ࡭ࠠࡑࡧࡵࡧࡾࠨὔ"))
        cmd = [self.binary_path, bstack111l1ll_opy_ (u"ࠨࡥࡹࡧࡦ࠾ࡸࡺ࡯ࡱࠤὕ")]
        self.bstack11111l111l1_opy_(cmd)
        self.bstack11111ll1lll_opy_ = False
    except Exception as e:
      self.logger.error(bstack111l1ll_opy_ (u"ࠢࡇࡣ࡬ࡰࡪࡪࠠࡵࡱࠣࡷࡹࡵࡰࠡࡵࡨࡷࡸ࡯࡯࡯ࠢࡺ࡭ࡹ࡮ࠠࡤࡱࡰࡱࡦࡴࡤࠡ࠯ࠣࡿࢂ࠲ࠠࡆࡺࡦࡩࡵࡺࡩࡰࡰ࠽ࠤࢀࢃࠢὖ").format(cmd, e))
  def bstack1l1llllll_opy_(self):
    if not self.bstack11l11111l_opy_:
      return
    try:
      bstack11111llll11_opy_ = 0
      while not self.bstack11111ll1lll_opy_ and bstack11111llll11_opy_ < self.bstack11111ll11l1_opy_:
        if self.bstack11111l1l1l1_opy_:
          self.logger.info(bstack111l1ll_opy_ (u"ࠣࡒࡨࡶࡨࡿࠠࡴࡧࡷࡹࡵࠦࡦࡢ࡫࡯ࡩࡩࠨὗ"))
          return
        time.sleep(1)
        bstack11111llll11_opy_ += 1
      os.environ[bstack111l1ll_opy_ (u"ࠩࡓࡉࡗࡉ࡙ࡠࡄࡈࡗ࡙ࡥࡐࡍࡃࡗࡊࡔࡘࡍࠨ὘")] = str(self.bstack1111l11llll_opy_())
      self.logger.info(bstack111l1ll_opy_ (u"ࠥࡔࡪࡸࡣࡺࠢࡶࡩࡹࡻࡰࠡࡥࡲࡱࡵࡲࡥࡵࡧࡧࠦὙ"))
    except Exception as e:
      self.logger.error(bstack111l1ll_opy_ (u"࡚ࠦࡴࡡࡣ࡮ࡨࠤࡹࡵࠠࡴࡧࡷࡹࡵࠦࡰࡦࡴࡦࡽ࠱ࠦࡅࡹࡥࡨࡴࡹ࡯࡯࡯ࠢࡾࢁࠧ὚").format(e))
  def bstack1111l11llll_opy_(self):
    if self.bstack111ll11l1_opy_:
      return
    try:
      bstack1111l11l1ll_opy_ = [platform[bstack111l1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡔࡡ࡮ࡧࠪὛ")].lower() for platform in self.config.get(bstack111l1ll_opy_ (u"࠭ࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡴࠩ὜"), [])]
      bstack11111ll1ll1_opy_ = sys.maxsize
      bstack11111lll1ll_opy_ = bstack111l1ll_opy_ (u"ࠧࠨὝ")
      for browser in bstack1111l11l1ll_opy_:
        if browser in self.bstack111111ll1l1_opy_:
          bstack11111l11111_opy_ = self.bstack111111ll1l1_opy_[browser]
        if bstack11111l11111_opy_ < bstack11111ll1ll1_opy_:
          bstack11111ll1ll1_opy_ = bstack11111l11111_opy_
          bstack11111lll1ll_opy_ = browser
      return bstack11111lll1ll_opy_
    except Exception as e:
      self.logger.error(bstack111l1ll_opy_ (u"ࠣࡗࡱࡥࡧࡲࡥࠡࡶࡲࠤ࡫࡯࡮ࡥࠢࡥࡩࡸࡺࠠࡱ࡮ࡤࡸ࡫ࡵࡲ࡮࠮ࠣࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡻࡾࠤ὞").format(e))
  @classmethod
  def bstack1ll11lll1l_opy_(self):
    return os.getenv(bstack111l1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡒࡈࡖࡈ࡟ࠧὟ"), bstack111l1ll_opy_ (u"ࠪࡊࡦࡲࡳࡦࠩὠ")).lower()
  @classmethod
  def bstack11ll1lll1_opy_(self):
    return os.getenv(bstack111l1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡔࡊࡘࡃ࡚ࡡࡆࡅࡕ࡚ࡕࡓࡇࡢࡑࡔࡊࡅࠨὡ"), bstack111l1ll_opy_ (u"ࠬ࠭ὢ"))
  @classmethod
  def bstack1l1l1l111l1_opy_(cls, value):
    cls.bstack1ll1llll1_opy_ = value
  @classmethod
  def bstack1111l11ll11_opy_(cls):
    return cls.bstack1ll1llll1_opy_
  @classmethod
  def bstack1l1l11l1lll_opy_(cls, value):
    cls.percy_build_id = value
  @classmethod
  def bstack11111l1l111_opy_(cls):
    return cls.percy_build_id