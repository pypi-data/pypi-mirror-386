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
from uuid import uuid4
from bstack_utils.helper import bstack11l1llll11_opy_, bstack11l11l1ll11_opy_
from bstack_utils.bstack1l1lll1l_opy_ import bstack1llllll1lll1_opy_
class bstack111l111111_opy_:
    def __init__(self, name=None, code=None, uuid=None, file_path=None, started_at=None, framework=None, tags=[], scope=[], bstack1lllll111l11_opy_=None, bstack1llll1ll1ll1_opy_=True, bstack1l111l11111_opy_=None, bstack1l1llll111_opy_=None, result=None, duration=None, bstack111l1ll111_opy_=None, meta={}):
        self.bstack111l1ll111_opy_ = bstack111l1ll111_opy_
        self.name = name
        self.code = code
        self.file_path = file_path
        self.uuid = uuid
        if not self.uuid and bstack1llll1ll1ll1_opy_:
            self.uuid = uuid4().__str__()
        self.started_at = started_at
        self.framework = framework
        self.tags = tags
        self.scope = scope
        self.bstack1lllll111l11_opy_ = bstack1lllll111l11_opy_
        self.bstack1l111l11111_opy_ = bstack1l111l11111_opy_
        self.bstack1l1llll111_opy_ = bstack1l1llll111_opy_
        self.result = result
        self.duration = duration
        self.meta = meta
        self.hooks = []
    def bstack111l11l11l_opy_(self):
        if self.uuid:
            return self.uuid
        self.uuid = uuid4().__str__()
        return self.uuid
    def bstack111ll11ll1_opy_(self, meta):
        self.meta = meta
    def bstack111ll1l1l1_opy_(self, hooks):
        self.hooks = hooks
    def bstack1lllll1111l1_opy_(self):
        bstack1llll1lll111_opy_ = os.path.relpath(self.file_path, start=os.getcwd())
        return {
            bstack111l1ll_opy_ (u"ࠪࡪ࡮ࡲࡥࡠࡰࡤࡱࡪ࠭⁜"): bstack1llll1lll111_opy_,
            bstack111l1ll_opy_ (u"ࠫࡱࡵࡣࡢࡶ࡬ࡳࡳ࠭⁝"): bstack1llll1lll111_opy_,
            bstack111l1ll_opy_ (u"ࠬࡼࡣࡠࡨ࡬ࡰࡪࡶࡡࡵࡪࠪ⁞"): bstack1llll1lll111_opy_
        }
    def set(self, **kwargs):
        for key, val in kwargs.items():
            if not hasattr(self, key):
                raise TypeError(bstack111l1ll_opy_ (u"ࠨࡕ࡯ࡧࡻࡴࡪࡩࡴࡦࡦࠣࡥࡷ࡭ࡵ࡮ࡧࡱࡸ࠿ࠦࠢ ") + key)
            setattr(self, key, val)
    def bstack1llll1lll11l_opy_(self):
        return {
            bstack111l1ll_opy_ (u"ࠧ࡯ࡣࡰࡩࠬ⁠"): self.name,
            bstack111l1ll_opy_ (u"ࠨࡤࡲࡨࡾ࠭⁡"): {
                bstack111l1ll_opy_ (u"ࠩ࡯ࡥࡳ࡭ࠧ⁢"): bstack111l1ll_opy_ (u"ࠪࡴࡾࡺࡨࡰࡰࠪ⁣"),
                bstack111l1ll_opy_ (u"ࠫࡨࡵࡤࡦࠩ⁤"): self.code
            },
            bstack111l1ll_opy_ (u"ࠬࡹࡣࡰࡲࡨࡷࠬ⁥"): self.scope,
            bstack111l1ll_opy_ (u"࠭ࡴࡢࡩࡶࠫ⁦"): self.tags,
            bstack111l1ll_opy_ (u"ࠧࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࠪ⁧"): self.framework,
            bstack111l1ll_opy_ (u"ࠨࡵࡷࡥࡷࡺࡥࡥࡡࡤࡸࠬ⁨"): self.started_at
        }
    def bstack1llll1lll1l1_opy_(self):
        return {
         bstack111l1ll_opy_ (u"ࠩࡰࡩࡹࡧࠧ⁩"): self.meta
        }
    def bstack1lllll111ll1_opy_(self):
        return {
            bstack111l1ll_opy_ (u"ࠪࡧࡺࡹࡴࡰ࡯ࡕࡩࡷࡻ࡮ࡑࡣࡵࡥࡲ࠭⁪"): {
                bstack111l1ll_opy_ (u"ࠫࡷ࡫ࡲࡶࡰࡢࡲࡦࡳࡥࠨ⁫"): self.bstack1lllll111l11_opy_
            }
        }
    def bstack1lllll11111l_opy_(self, bstack1llll1lllll1_opy_, details):
        step = next(filter(lambda st: st[bstack111l1ll_opy_ (u"ࠬ࡯ࡤࠨ⁬")] == bstack1llll1lllll1_opy_, self.meta[bstack111l1ll_opy_ (u"࠭ࡳࡵࡧࡳࡷࠬ⁭")]), None)
        step.update(details)
    def bstack1l1l111l_opy_(self, bstack1llll1lllll1_opy_):
        step = next(filter(lambda st: st[bstack111l1ll_opy_ (u"ࠧࡪࡦࠪ⁮")] == bstack1llll1lllll1_opy_, self.meta[bstack111l1ll_opy_ (u"ࠨࡵࡷࡩࡵࡹࠧ⁯")]), None)
        step.update({
            bstack111l1ll_opy_ (u"ࠩࡶࡸࡦࡸࡴࡦࡦࡢࡥࡹ࠭⁰"): bstack11l1llll11_opy_()
        })
    def bstack111ll1111l_opy_(self, bstack1llll1lllll1_opy_, result, duration=None):
        bstack1l111l11111_opy_ = bstack11l1llll11_opy_()
        if bstack1llll1lllll1_opy_ is not None and self.meta.get(bstack111l1ll_opy_ (u"ࠪࡷࡹ࡫ࡰࡴࠩⁱ")):
            step = next(filter(lambda st: st[bstack111l1ll_opy_ (u"ࠫ࡮ࡪࠧ⁲")] == bstack1llll1lllll1_opy_, self.meta[bstack111l1ll_opy_ (u"ࠬࡹࡴࡦࡲࡶࠫ⁳")]), None)
            step.update({
                bstack111l1ll_opy_ (u"࠭ࡦࡪࡰ࡬ࡷ࡭࡫ࡤࡠࡣࡷࠫ⁴"): bstack1l111l11111_opy_,
                bstack111l1ll_opy_ (u"ࠧࡥࡷࡵࡥࡹ࡯࡯࡯ࠩ⁵"): duration if duration else bstack11l11l1ll11_opy_(step[bstack111l1ll_opy_ (u"ࠨࡵࡷࡥࡷࡺࡥࡥࡡࡤࡸࠬ⁶")], bstack1l111l11111_opy_),
                bstack111l1ll_opy_ (u"ࠩࡵࡩࡸࡻ࡬ࡵࠩ⁷"): result.result,
                bstack111l1ll_opy_ (u"ࠪࡪࡦ࡯࡬ࡶࡴࡨࠫ⁸"): str(result.exception) if result.exception else None
            })
    def add_step(self, bstack1llll1lll1ll_opy_):
        if self.meta.get(bstack111l1ll_opy_ (u"ࠫࡸࡺࡥࡱࡵࠪ⁹")):
            self.meta[bstack111l1ll_opy_ (u"ࠬࡹࡴࡦࡲࡶࠫ⁺")].append(bstack1llll1lll1ll_opy_)
        else:
            self.meta[bstack111l1ll_opy_ (u"࠭ࡳࡵࡧࡳࡷࠬ⁻")] = [ bstack1llll1lll1ll_opy_ ]
    def bstack1llll1llllll_opy_(self):
        return {
            bstack111l1ll_opy_ (u"ࠧࡶࡷ࡬ࡨࠬ⁼"): self.bstack111l11l11l_opy_(),
            **self.bstack1llll1lll11l_opy_(),
            **self.bstack1lllll1111l1_opy_(),
            **self.bstack1llll1lll1l1_opy_()
        }
    def bstack1lllll111111_opy_(self):
        if not self.result:
            return {}
        data = {
            bstack111l1ll_opy_ (u"ࠨࡨ࡬ࡲ࡮ࡹࡨࡦࡦࡢࡥࡹ࠭⁽"): self.bstack1l111l11111_opy_,
            bstack111l1ll_opy_ (u"ࠩࡧࡹࡷࡧࡴࡪࡱࡱࡣ࡮ࡴ࡟࡮ࡵࠪ⁾"): self.duration,
            bstack111l1ll_opy_ (u"ࠪࡶࡪࡹࡵ࡭ࡶࠪⁿ"): self.result.result
        }
        if data[bstack111l1ll_opy_ (u"ࠫࡷ࡫ࡳࡶ࡮ࡷࠫ₀")] == bstack111l1ll_opy_ (u"ࠬ࡬ࡡࡪ࡮ࡨࡨࠬ₁"):
            data[bstack111l1ll_opy_ (u"࠭ࡦࡢ࡫࡯ࡹࡷ࡫࡟ࡵࡻࡳࡩࠬ₂")] = self.result.bstack1111111ll1_opy_()
            data[bstack111l1ll_opy_ (u"ࠧࡧࡣ࡬ࡰࡺࡸࡥࠨ₃")] = [{bstack111l1ll_opy_ (u"ࠨࡤࡤࡧࡰࡺࡲࡢࡥࡨࠫ₄"): self.result.bstack111lll11lll_opy_()}]
        return data
    def bstack1llll1llll11_opy_(self):
        return {
            bstack111l1ll_opy_ (u"ࠩࡸࡹ࡮ࡪࠧ₅"): self.bstack111l11l11l_opy_(),
            **self.bstack1llll1lll11l_opy_(),
            **self.bstack1lllll1111l1_opy_(),
            **self.bstack1lllll111111_opy_(),
            **self.bstack1llll1lll1l1_opy_()
        }
    def bstack111l11ll11_opy_(self, event, result=None):
        if result:
            self.result = result
        if bstack111l1ll_opy_ (u"ࠪࡗࡹࡧࡲࡵࡧࡧࠫ₆") in event:
            return self.bstack1llll1llllll_opy_()
        elif bstack111l1ll_opy_ (u"ࠫࡋ࡯࡮ࡪࡵ࡫ࡩࡩ࠭₇") in event:
            return self.bstack1llll1llll11_opy_()
    def bstack1111l1ll1l_opy_(self):
        pass
    def stop(self, time=None, duration=None, result=None):
        self.bstack1l111l11111_opy_ = time if time else bstack11l1llll11_opy_()
        self.duration = duration if duration else bstack11l11l1ll11_opy_(self.started_at, self.bstack1l111l11111_opy_)
        if result:
            self.result = result
class bstack111l1lll1l_opy_(bstack111l111111_opy_):
    def __init__(self, hooks=[], bstack111ll11l1l_opy_={}, *args, **kwargs):
        self.hooks = hooks
        self.bstack111ll11l1l_opy_ = bstack111ll11l1l_opy_
        super().__init__(*args, **kwargs, bstack1l1llll111_opy_=bstack111l1ll_opy_ (u"ࠬࡺࡥࡴࡶࠪ₈"))
    @classmethod
    def bstack1lllll1111ll_opy_(cls, scenario, feature, test, **kwargs):
        steps = []
        for step in scenario.steps:
            steps.append({
                bstack111l1ll_opy_ (u"࠭ࡩࡥࠩ₉"): id(step),
                bstack111l1ll_opy_ (u"ࠧࡵࡧࡻࡸࠬ₊"): step.name,
                bstack111l1ll_opy_ (u"ࠨ࡭ࡨࡽࡼࡵࡲࡥࠩ₋"): step.keyword,
            })
        return bstack111l1lll1l_opy_(
            **kwargs,
            meta={
                bstack111l1ll_opy_ (u"ࠩࡩࡩࡦࡺࡵࡳࡧࠪ₌"): {
                    bstack111l1ll_opy_ (u"ࠪࡲࡦࡳࡥࠨ₍"): feature.name,
                    bstack111l1ll_opy_ (u"ࠫࡵࡧࡴࡩࠩ₎"): feature.filename,
                    bstack111l1ll_opy_ (u"ࠬࡪࡥࡴࡥࡵ࡭ࡵࡺࡩࡰࡰࠪ₏"): feature.description
                },
                bstack111l1ll_opy_ (u"࠭ࡳࡤࡧࡱࡥࡷ࡯࡯ࠨₐ"): {
                    bstack111l1ll_opy_ (u"ࠧ࡯ࡣࡰࡩࠬₑ"): scenario.name
                },
                bstack111l1ll_opy_ (u"ࠨࡵࡷࡩࡵࡹࠧₒ"): steps,
                bstack111l1ll_opy_ (u"ࠩࡨࡼࡦࡳࡰ࡭ࡧࡶࠫₓ"): bstack1llllll1lll1_opy_(test)
            }
        )
    def bstack1llll1llll1l_opy_(self):
        return {
            bstack111l1ll_opy_ (u"ࠪ࡬ࡴࡵ࡫ࡴࠩₔ"): self.hooks
        }
    def bstack1llll1ll1lll_opy_(self):
        if self.bstack111ll11l1l_opy_:
            return {
                bstack111l1ll_opy_ (u"ࠫ࡮ࡴࡴࡦࡩࡵࡥࡹ࡯࡯࡯ࡵࠪₕ"): self.bstack111ll11l1l_opy_
            }
        return {}
    def bstack1llll1llll11_opy_(self):
        return {
            **super().bstack1llll1llll11_opy_(),
            **self.bstack1llll1llll1l_opy_()
        }
    def bstack1llll1llllll_opy_(self):
        return {
            **super().bstack1llll1llllll_opy_(),
            **self.bstack1llll1ll1lll_opy_()
        }
    def bstack1111l1ll1l_opy_(self):
        return bstack111l1ll_opy_ (u"ࠬࡺࡥࡴࡶࡢࡶࡺࡴࠧₖ")
class bstack111ll111ll_opy_(bstack111l111111_opy_):
    def __init__(self, hook_type, *args,bstack111ll11l1l_opy_={}, **kwargs):
        self.hook_type = hook_type
        self.bstack1ll111l1111_opy_ = None
        self.bstack111ll11l1l_opy_ = bstack111ll11l1l_opy_
        super().__init__(*args, **kwargs, bstack1l1llll111_opy_=bstack111l1ll_opy_ (u"࠭ࡨࡰࡱ࡮ࠫₗ"))
    def bstack1111llll1l_opy_(self):
        return self.hook_type
    def bstack1lllll111l1l_opy_(self):
        return {
            bstack111l1ll_opy_ (u"ࠧࡩࡱࡲ࡯ࡤࡺࡹࡱࡧࠪₘ"): self.hook_type
        }
    def bstack1llll1llll11_opy_(self):
        return {
            **super().bstack1llll1llll11_opy_(),
            **self.bstack1lllll111l1l_opy_()
        }
    def bstack1llll1llllll_opy_(self):
        return {
            **super().bstack1llll1llllll_opy_(),
            bstack111l1ll_opy_ (u"ࠨࡶࡨࡷࡹࡥࡲࡶࡰࡢ࡭ࡩ࠭ₙ"): self.bstack1ll111l1111_opy_,
            **self.bstack1lllll111l1l_opy_()
        }
    def bstack1111l1ll1l_opy_(self):
        return bstack111l1ll_opy_ (u"ࠩ࡫ࡳࡴࡱ࡟ࡳࡷࡱࠫₚ")
    def bstack111ll1lll1_opy_(self, bstack1ll111l1111_opy_):
        self.bstack1ll111l1111_opy_ = bstack1ll111l1111_opy_