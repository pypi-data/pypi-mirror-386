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
from datetime import datetime, timezone
from uuid import uuid4
from typing import Dict, List, Any, Tuple
from browserstack_sdk.sdk_cli.bstack1lllll1111l_opy_ import bstack1llllll11l1_opy_
from browserstack_sdk.sdk_cli.utils.bstack11llll11ll_opy_ import bstack11llllll1ll_opy_
from browserstack_sdk.sdk_cli.test_framework import (
    TestFramework,
    bstack1lll11ll1ll_opy_,
    bstack1ll1l1l1lll_opy_,
    bstack1llll11l111_opy_,
    bstack1l111111ll1_opy_,
    bstack1ll1l1l11ll_opy_,
)
from pathlib import Path
import grpc
from browserstack_sdk import sdk_pb2 as structs
from datetime import datetime, timezone
from typing import List, Dict, Any
import traceback
from bstack_utils.helper import bstack1l1ll11111l_opy_
from bstack_utils.bstack1l1111l1l1_opy_ import bstack1ll1ll1ll11_opy_
from bstack_utils.constants import EVENTS
from browserstack_sdk.sdk_cli.bstack11111111l1_opy_ import bstack1111111111_opy_
from browserstack_sdk.sdk_cli.utils.bstack1lll1l1llll_opy_ import bstack1ll1l1l111l_opy_
from bstack_utils.bstack111ll11lll_opy_ import bstack11l1l1111l_opy_
bstack1l1ll11l1ll_opy_ = bstack1l1ll11111l_opy_()
bstack1l1111ll111_opy_ = 1.0
bstack1l1l1l1llll_opy_ = bstack111l1ll_opy_ (u"࡙ࠥࡵࡲ࡯ࡢࡦࡨࡨࡆࡺࡴࡢࡥ࡫ࡱࡪࡴࡴࡴ࠯ࠥᓵ")
bstack11llll1l1l1_opy_ = bstack111l1ll_opy_ (u"࡙ࠦ࡫ࡳࡵࡎࡨࡺࡪࡲࠢᓶ")
bstack11llll1l111_opy_ = bstack111l1ll_opy_ (u"ࠧࡈࡵࡪ࡮ࡧࡐࡪࡼࡥ࡭ࠤᓷ")
bstack11llll11ll1_opy_ = bstack111l1ll_opy_ (u"ࠨࡈࡰࡱ࡮ࡐࡪࡼࡥ࡭ࠤᓸ")
bstack11llll11lll_opy_ = bstack111l1ll_opy_ (u"ࠢࡃࡷ࡬ࡰࡩࡒࡥࡷࡧ࡯ࡌࡴࡵ࡫ࡆࡸࡨࡲࡹࠨᓹ")
_1l1ll11l11l_opy_ = set()
class bstack1ll1l11ll11_opy_(TestFramework):
    bstack1l1111l111l_opy_ = bstack111l1ll_opy_ (u"ࠣࡶࡨࡷࡹࡥࡦࡪࡺࡷࡹࡷ࡫ࡳࠣᓺ")
    bstack11llll1ll1l_opy_ = bstack111l1ll_opy_ (u"ࠤࡷࡩࡸࡺ࡟ࡩࡱࡲ࡯ࡸࡥࡳࡵࡣࡵࡸࡪࡪࠢᓻ")
    bstack1l1111l11ll_opy_ = bstack111l1ll_opy_ (u"ࠥࡸࡪࡹࡴࡠࡪࡲࡳࡰࡹ࡟ࡧ࡫ࡱ࡭ࡸ࡮ࡥࡥࠤᓼ")
    bstack1l11111ll11_opy_ = bstack111l1ll_opy_ (u"ࠦࡹ࡫ࡳࡵࡡ࡫ࡳࡴࡱ࡟࡭ࡣࡶࡸࡤࡹࡴࡢࡴࡷࡩࡩࠨᓽ")
    bstack1l1111111ll_opy_ = bstack111l1ll_opy_ (u"ࠧࡺࡥࡴࡶࡢ࡬ࡴࡵ࡫ࡠ࡮ࡤࡷࡹࡥࡦࡪࡰ࡬ࡷ࡭࡫ࡤࠣᓾ")
    bstack1l111ll11l1_opy_: bool
    bstack11111111l1_opy_: bstack1111111111_opy_  = None
    bstack1ll1ll1ll1l_opy_ = None
    bstack1l1111l1111_opy_ = [
        bstack1lll11ll1ll_opy_.BEFORE_ALL,
        bstack1lll11ll1ll_opy_.AFTER_ALL,
        bstack1lll11ll1ll_opy_.BEFORE_EACH,
        bstack1lll11ll1ll_opy_.AFTER_EACH,
    ]
    def __init__(
        self,
        bstack11lllll11ll_opy_: Dict[str, str],
        bstack1ll11l1l1l1_opy_: List[str]=[bstack111l1ll_opy_ (u"ࠨࡰࡺࡶࡨࡷࡹࠨᓿ")],
        bstack11111111l1_opy_: bstack1111111111_opy_=None,
        bstack1ll1ll1ll1l_opy_=None
    ):
        super().__init__(bstack1ll11l1l1l1_opy_, bstack11lllll11ll_opy_, bstack11111111l1_opy_)
        self.bstack1l111ll11l1_opy_ = any(bstack111l1ll_opy_ (u"ࠢࡱࡻࡷࡩࡸࡺࠢᔀ") in item.lower() for item in bstack1ll11l1l1l1_opy_)
        self.bstack1ll1ll1ll1l_opy_ = bstack1ll1ll1ll1l_opy_
    def track_event(
        self,
        context: bstack1l111111ll1_opy_,
        test_framework_state: bstack1lll11ll1ll_opy_,
        test_hook_state: bstack1llll11l111_opy_,
        *args,
        **kwargs,
    ):
        super().track_event(self, context, test_framework_state, test_hook_state, *args, **kwargs)
        if test_framework_state == bstack1lll11ll1ll_opy_.TEST or test_framework_state in bstack1ll1l11ll11_opy_.bstack1l1111l1111_opy_:
            bstack11llllll1ll_opy_(test_framework_state, test_hook_state)
        if test_framework_state == bstack1lll11ll1ll_opy_.NONE:
            self.logger.warning(bstack111l1ll_opy_ (u"ࠣ࡫ࡪࡲࡴࡸࡥࡥࠢࡦࡥࡱࡲࡢࡢࡥ࡮ࠤࡹ࡫ࡳࡵࡡࡩࡶࡦࡳࡥࡸࡱࡵ࡯ࡤࡹࡴࡢࡶࡨࡁࢀࡺࡥࡴࡶࡢࡪࡷࡧ࡭ࡦࡹࡲࡶࡰࡥࡳࡵࡣࡷࡩࢂࠦࡴࡦࡵࡷࡣ࡭ࡵ࡯࡬ࡡࡶࡸࡦࡺࡥ࠾ࠤᔁ") + str(test_hook_state) + bstack111l1ll_opy_ (u"ࠤࠥᔂ"))
            return
        if not self.bstack1l111ll11l1_opy_:
            self.logger.warning(bstack111l1ll_opy_ (u"ࠥࡸࡷࡧࡣ࡬ࡡࡨࡺࡪࡴࡴ࠻ࠢࡸࡲࡸࡻࡰࡱࡱࡵࡸࡪࡪࠠࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡀࠦᔃ") + str(str(self.bstack1ll11l1l1l1_opy_)) + bstack111l1ll_opy_ (u"ࠦࠧᔄ"))
            return
        if not isinstance(args, tuple) or len(args) == 0:
            self.logger.warning(bstack111l1ll_opy_ (u"ࠧࡺࡲࡢࡥ࡮ࡣࡪࡼࡥ࡯ࡶ࠽ࠤࡺࡴࡥࡹࡲࡨࡧࡹ࡫ࡤࠡࡣࡵ࡫ࡸࡃࡻࡢࡴࡪࡷࢂࠦ࡫ࡸࡣࡵ࡫ࡸࡃࠢᔅ") + str(kwargs) + bstack111l1ll_opy_ (u"ࠨࠢᔆ"))
            return
        instance = self.__1l1111ll11l_opy_(context, test_framework_state, test_hook_state, *args, **kwargs)
        if not instance:
            self.logger.debug(bstack111l1ll_opy_ (u"ࠢࡵࡴࡤࡧࡰࡥࡥࡷࡧࡱࡸ࠿ࠦࡵ࡯ࡪࡤࡲࡩࡲࡥࡥࠢࡨࡺࡪࡴࡴ࠾ࡽࡷࡩࡸࡺ࡟ࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡷࡹࡧࡴࡦࡿ࠱ࡿࡹ࡫ࡳࡵࡡ࡫ࡳࡴࡱ࡟ࡴࡶࡤࡸࡪࢃࠠࡢࡴࡪࡷࡂࠨᔇ") + str(args) + bstack111l1ll_opy_ (u"ࠣࠤᔈ"))
            return
        try:
            if instance!= None and test_framework_state in bstack1ll1l11ll11_opy_.bstack1l1111l1111_opy_ and test_hook_state == bstack1llll11l111_opy_.PRE:
                bstack1ll11llll11_opy_ = bstack1ll1ll1ll11_opy_.bstack1ll1l1111l1_opy_(EVENTS.bstack1ll1l1l1_opy_.value)
                name = str(EVENTS.bstack1ll1l1l1_opy_.name)+bstack111l1ll_opy_ (u"ࠤ࠽ࠦᔉ")+str(test_framework_state.name)
                TestFramework.bstack1l11111l1ll_opy_(instance, name, bstack1ll11llll11_opy_)
        except Exception as e:
            self.logger.debug(bstack111l1ll_opy_ (u"ࠥࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡩ࡯ࠢ࡫ࡳࡴࡱࠠࡦࡴࡵࡳࡷࠦࡰࡳࡧ࠽ࠤࢀࢃࠢᔊ").format(e))
        try:
            if not TestFramework.bstack1llll11llll_opy_(instance, TestFramework.bstack1l111llll1l_opy_) and test_hook_state == bstack1llll11l111_opy_.PRE:
                test = bstack1ll1l11ll11_opy_.__1l1111lll1l_opy_(args[0])
                if test:
                    instance.data.update(test)
                    self.logger.debug(bstack111l1ll_opy_ (u"ࠦࡱࡵࡡࡥࡧࡧࠤ࡮ࡴࡳࡵࡣࡱࡧࡪࡃࡻࡪࡰࡶࡸࡦࡴࡣࡦ࠰ࡵࡩ࡫࠮ࠩࡾࠢࡨࡺࡪࡴࡴ࠾ࡽࡷࡩࡸࡺ࡟ࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡷࡹࡧࡴࡦࡿ࠱ࠦᔋ") + str(test_hook_state) + bstack111l1ll_opy_ (u"ࠧࠨᔌ"))
            if test_framework_state == bstack1lll11ll1ll_opy_.TEST:
                if test_hook_state == bstack1llll11l111_opy_.PRE and not TestFramework.bstack1llll11llll_opy_(instance, TestFramework.bstack1l1ll1l1ll1_opy_):
                    TestFramework.bstack1llllll1lll_opy_(instance, TestFramework.bstack1l1ll1l1ll1_opy_, datetime.now(tz=timezone.utc))
                    self.logger.debug(bstack111l1ll_opy_ (u"ࠨࡳࡦࡶࠣࡸࡪࡹࡴ࠮ࡵࡷࡥࡷࡺࠠࡧࡱࡵࠤ࡮ࡴࡳࡵࡣࡱࡧࡪࡃࡻࡪࡰࡶࡸࡦࡴࡣࡦ࠰ࡵࡩ࡫࠮ࠩࡾࠢࡨࡺࡪࡴࡴ࠾ࡽࡷࡩࡸࡺ࡟ࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡷࡹࡧࡴࡦࡿ࠱ࠦᔍ") + str(test_hook_state) + bstack111l1ll_opy_ (u"ࠢࠣᔎ"))
                elif test_hook_state == bstack1llll11l111_opy_.POST and not TestFramework.bstack1llll11llll_opy_(instance, TestFramework.bstack1l1lll11ll1_opy_):
                    TestFramework.bstack1llllll1lll_opy_(instance, TestFramework.bstack1l1lll11ll1_opy_, datetime.now(tz=timezone.utc))
                    self.logger.debug(bstack111l1ll_opy_ (u"ࠣࡵࡨࡸࠥࡺࡥࡴࡶ࠰ࡩࡳࡪࠠࡧࡱࡵࠤ࡮ࡴࡳࡵࡣࡱࡧࡪࡃࡻࡪࡰࡶࡸࡦࡴࡣࡦ࠰ࡵࡩ࡫࠮ࠩࡾࠢࡨࡺࡪࡴࡴ࠾ࡽࡷࡩࡸࡺ࡟ࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡷࡹࡧࡴࡦࡿ࠱ࠦᔏ") + str(test_hook_state) + bstack111l1ll_opy_ (u"ࠤࠥᔐ"))
            elif test_framework_state == bstack1lll11ll1ll_opy_.LOG and test_hook_state == bstack1llll11l111_opy_.POST:
                bstack1ll1l11ll11_opy_.__1l111l11lll_opy_(instance, *args)
            elif test_framework_state == bstack1lll11ll1ll_opy_.LOG_REPORT and test_hook_state == bstack1llll11l111_opy_.POST:
                self.__1l111ll1l11_opy_(instance, *args)
                self.__1l111l1ll1l_opy_(instance)
            elif test_framework_state in bstack1ll1l11ll11_opy_.bstack1l1111l1111_opy_:
                self.__1l111l1l111_opy_(instance, test_framework_state, test_hook_state, *args)
            self.logger.debug(bstack111l1ll_opy_ (u"ࠥࡸࡷࡧࡣ࡬ࡡࡨࡺࡪࡴࡴ࠻ࠢ࡫ࡥࡳࡪ࡬ࡦࡦࠣࡩࡻ࡫࡮ࡵ࠿ࡾࡸࡪࡹࡴࡠࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࡣࡸࡺࡡࡵࡧࢀ࠲ࢀࡺࡥࡴࡶࡢ࡬ࡴࡵ࡫ࡠࡵࡷࡥࡹ࡫ࡽࠡ࡫ࡱࡷࡹࡧ࡮ࡤࡧࡀࠦᔑ") + str(instance.ref()) + bstack111l1ll_opy_ (u"ࠦࠧᔒ"))
        except Exception as e:
            self.logger.error(e)
            traceback.print_exc()
        self.bstack1l111111111_opy_(instance, (test_framework_state, test_hook_state), *args, **kwargs)
        try:
            if instance!= None and test_framework_state in bstack1ll1l11ll11_opy_.bstack1l1111l1111_opy_ and test_hook_state == bstack1llll11l111_opy_.POST:
                name = str(EVENTS.bstack1ll1l1l1_opy_.name)+bstack111l1ll_opy_ (u"ࠧࡀࠢᔓ")+str(test_framework_state.name)
                bstack1ll11llll11_opy_ = TestFramework.bstack1l1111l1l1l_opy_(instance, name)
                bstack1ll1ll1ll11_opy_.end(EVENTS.bstack1ll1l1l1_opy_.value, bstack1ll11llll11_opy_+bstack111l1ll_opy_ (u"ࠨ࠺ࡴࡶࡤࡶࡹࠨᔔ"), bstack1ll11llll11_opy_+bstack111l1ll_opy_ (u"ࠢ࠻ࡧࡱࡨࠧᔕ"), True, None, test_framework_state.name)
        except Exception as e:
            self.logger.debug(bstack111l1ll_opy_ (u"ࠣࡇࡻࡧࡪࡶࡴࡪࡱࡱࠤ࡮ࡴࠠࡩࡱࡲ࡯ࠥ࡫ࡲࡳࡱࡵ࠾ࠥࢁࡽࠣᔖ").format(e))
    def bstack1l1l1lll1ll_opy_(self):
        return self.bstack1l111ll11l1_opy_
    def __11llll1llll_opy_(self, *args):
        if len(args) > 2 and callable(getattr(args[2], bstack111l1ll_opy_ (u"ࠤࡪࡩࡹࡥࡲࡦࡵࡸࡰࡹࠨᔗ"), None)):
            rep = args[2].get_result()
            if rep:
                return TestFramework.bstack1l1ll1111ll_opy_(rep, [bstack111l1ll_opy_ (u"ࠥࡻ࡭࡫࡮ࠣᔘ"), bstack111l1ll_opy_ (u"ࠦࡴࡻࡴࡤࡱࡰࡩࠧᔙ"), bstack111l1ll_opy_ (u"ࠧࡶࡡࡴࡵࡨࡨࠧᔚ"), bstack111l1ll_opy_ (u"ࠨࡦࡢ࡫࡯ࡩࡩࠨᔛ"), bstack111l1ll_opy_ (u"ࠢࡴ࡭࡬ࡴࡵ࡫ࡤࠣᔜ"), bstack111l1ll_opy_ (u"ࠣ࡮ࡲࡲ࡬ࡸࡥࡱࡴࡷࡩࡽࡺࠢᔝ")])
        return None
    def __1l111ll1l11_opy_(self, instance: bstack1ll1l1l1lll_opy_, *args):
        result = self.__11llll1llll_opy_(*args)
        if not result:
            return
        failure = None
        bstack1111111ll1_opy_ = None
        if result.get(bstack111l1ll_opy_ (u"ࠤࡲࡹࡹࡩ࡯࡮ࡧࠥᔞ"), None) == bstack111l1ll_opy_ (u"ࠥࡪࡦ࡯࡬ࡦࡦࠥᔟ") and len(args) > 1 and getattr(args[1], bstack111l1ll_opy_ (u"ࠦࡪࡾࡣࡪࡰࡩࡳࠧᔠ"), None) is not None:
            failure = [{bstack111l1ll_opy_ (u"ࠬࡨࡡࡤ࡭ࡷࡶࡦࡩࡥࠨᔡ"): [args[1].excinfo.exconly(), result.get(bstack111l1ll_opy_ (u"ࠨ࡬ࡰࡰࡪࡶࡪࡶࡲࡵࡧࡻࡸࠧᔢ"), None)]}]
            bstack1111111ll1_opy_ = bstack111l1ll_opy_ (u"ࠢࡂࡵࡶࡩࡷࡺࡩࡰࡰࡈࡶࡷࡵࡲࠣᔣ") if bstack111l1ll_opy_ (u"ࠣࡃࡶࡷࡪࡸࡴࡪࡱࡱࠦᔤ") in getattr(args[1].excinfo, bstack111l1ll_opy_ (u"ࠤࡷࡽࡵ࡫࡮ࡢ࡯ࡨࠦᔥ"), bstack111l1ll_opy_ (u"ࠥࠦᔦ")) else bstack111l1ll_opy_ (u"࡚ࠦࡴࡨࡢࡰࡧࡰࡪࡪࡅࡳࡴࡲࡶࠧᔧ")
        bstack11lllll1111_opy_ = result.get(bstack111l1ll_opy_ (u"ࠧࡵࡵࡵࡥࡲࡱࡪࠨᔨ"), TestFramework.bstack1l111llll11_opy_)
        if bstack11lllll1111_opy_ != TestFramework.bstack1l111llll11_opy_:
            TestFramework.bstack1llllll1lll_opy_(instance, TestFramework.bstack1l1ll1l111l_opy_, datetime.now(tz=timezone.utc))
        TestFramework.bstack1l111lll11l_opy_(instance, {
            TestFramework.bstack1l11llll1l1_opy_: failure,
            TestFramework.bstack11llll1lll1_opy_: bstack1111111ll1_opy_,
            TestFramework.bstack1l1l111111l_opy_: bstack11lllll1111_opy_,
        })
    def __1l1111ll11l_opy_(
        self,
        context: bstack1l111111ll1_opy_,
        test_framework_state: bstack1lll11ll1ll_opy_,
        test_hook_state: bstack1llll11l111_opy_,
        *args,
        **kwargs,
    ):
        instance = None
        if test_framework_state == bstack1lll11ll1ll_opy_.SETUP_FIXTURE:
            instance = self.__1l111ll1l1l_opy_(context, test_framework_state, test_hook_state, *args, **kwargs)
        else:
            target = None # bstack11llllll11l_opy_ bstack1l111111l11_opy_ this to be bstack111l1ll_opy_ (u"ࠨ࡮ࡰࡦࡨ࡭ࡩࠨᔩ")
            if test_framework_state == bstack1lll11ll1ll_opy_.INIT_TEST:
                target = args[0] if isinstance(args[0], str) else None
                if target:
                    self.__1l1111lllll_opy_(context, test_framework_state, target, *args)
            elif test_framework_state == bstack1lll11ll1ll_opy_.LOG:
                nodeid = getattr(getattr(args[0], bstack111l1ll_opy_ (u"ࠢ࡯ࡱࡧࡩࠧᔪ"), None), bstack111l1ll_opy_ (u"ࠣࡰࡲࡨࡪ࡯ࡤࠣᔫ"), None) if args else None
                if isinstance(nodeid, str):
                    target = nodeid
            elif getattr(args[0], bstack111l1ll_opy_ (u"ࠤࡱࡳࡩ࡫ࡩࡥࠤᔬ"), None):
                target = args[0].nodeid
            instance = TestFramework.bstack1lllll1l1ll_opy_(target) if target else None
        return instance
    def __1l111l1l111_opy_(
        self,
        instance: bstack1ll1l1l1lll_opy_,
        test_framework_state: bstack1lll11ll1ll_opy_,
        test_hook_state: bstack1llll11l111_opy_,
        *args,
    ):
        key = test_framework_state.name
        bstack1l111lll111_opy_ = TestFramework.bstack1llll1lllll_opy_(instance, bstack1ll1l11ll11_opy_.bstack11llll1ll1l_opy_, {})
        if not key in bstack1l111lll111_opy_:
            bstack1l111lll111_opy_[key] = []
        bstack1l11111l1l1_opy_ = TestFramework.bstack1llll1lllll_opy_(instance, bstack1ll1l11ll11_opy_.bstack1l1111l11ll_opy_, {})
        if not key in bstack1l11111l1l1_opy_:
            bstack1l11111l1l1_opy_[key] = []
        bstack1l111l1ll11_opy_ = {
            bstack1ll1l11ll11_opy_.bstack11llll1ll1l_opy_: bstack1l111lll111_opy_,
            bstack1ll1l11ll11_opy_.bstack1l1111l11ll_opy_: bstack1l11111l1l1_opy_,
        }
        if test_hook_state == bstack1llll11l111_opy_.PRE:
            hook = {
                bstack111l1ll_opy_ (u"ࠥ࡯ࡪࡿࠢᔭ"): key,
                TestFramework.bstack11lllll1ll1_opy_: uuid4().__str__(),
                TestFramework.bstack1l111l1l1ll_opy_: TestFramework.bstack1l11111lll1_opy_,
                TestFramework.bstack11llllllll1_opy_: datetime.now(tz=timezone.utc),
                TestFramework.bstack1l111ll1lll_opy_: [],
                TestFramework.bstack1l1111111l1_opy_: args[1] if len(args) > 1 else bstack111l1ll_opy_ (u"ࠫࠬᔮ"),
                TestFramework.bstack11llllll1l1_opy_: bstack1ll1l1l111l_opy_.bstack1l111l11ll1_opy_()
            }
            bstack1l111lll111_opy_[key].append(hook)
            bstack1l111l1ll11_opy_[bstack1ll1l11ll11_opy_.bstack1l11111ll11_opy_] = key
        elif test_hook_state == bstack1llll11l111_opy_.POST:
            bstack1l111ll11ll_opy_ = bstack1l111lll111_opy_.get(key, [])
            hook = bstack1l111ll11ll_opy_.pop() if bstack1l111ll11ll_opy_ else None
            if hook:
                result = self.__11llll1llll_opy_(*args)
                if result:
                    bstack11lllll111l_opy_ = result.get(bstack111l1ll_opy_ (u"ࠧࡵࡵࡵࡥࡲࡱࡪࠨᔯ"), TestFramework.bstack1l11111lll1_opy_)
                    if bstack11lllll111l_opy_ != TestFramework.bstack1l11111lll1_opy_:
                        hook[TestFramework.bstack1l111l1l1ll_opy_] = bstack11lllll111l_opy_
                hook[TestFramework.bstack1l111lll1ll_opy_] = datetime.now(tz=timezone.utc)
                hook[TestFramework.bstack11llllll1l1_opy_]= bstack1ll1l1l111l_opy_.bstack1l111l11ll1_opy_()
                self.bstack1l111ll111l_opy_(hook)
                logs = hook.get(TestFramework.bstack1l11111l11l_opy_, [])
                if logs: self.bstack1l1l1l111ll_opy_(instance, logs)
                bstack1l11111l1l1_opy_[key].append(hook)
                bstack1l111l1ll11_opy_[bstack1ll1l11ll11_opy_.bstack1l1111111ll_opy_] = key
        TestFramework.bstack1l111lll11l_opy_(instance, bstack1l111l1ll11_opy_)
        self.logger.debug(bstack111l1ll_opy_ (u"ࠨࡴࡳࡣࡦ࡯ࡤ࡮࡯ࡰ࡭ࡢࡩࡻ࡫࡮ࡵ࠼ࠣࡸࡪࡹࡴࡠࡪࡲࡳࡰࡥࡳࡵࡣࡷࡩࡂࢁ࡫ࡦࡻࢀ࠲ࢀࡺࡥࡴࡶࡢ࡬ࡴࡵ࡫ࡠࡵࡷࡥࡹ࡫ࡽࠡࡪࡲࡳࡰࡹ࡟ࡴࡶࡤࡶࡹ࡫ࡤ࠾ࡽ࡫ࡳࡴࡱࡳࡠࡵࡷࡥࡷࡺࡥࡥࡿࠣ࡬ࡴࡵ࡫ࡴࡡࡩ࡭ࡳ࡯ࡳࡩࡧࡧࡁࠧᔰ") + str(bstack1l11111l1l1_opy_) + bstack111l1ll_opy_ (u"ࠢࠣᔱ"))
    def __1l111ll1l1l_opy_(
        self,
        context: bstack1l111111ll1_opy_,
        test_framework_state: bstack1lll11ll1ll_opy_,
        test_hook_state: bstack1llll11l111_opy_,
        *args,
        **kwargs,
    ):
        fixturedef = TestFramework.bstack1l1ll1111ll_opy_(args[0], [bstack111l1ll_opy_ (u"ࠣࡵࡦࡳࡵ࡫ࠢᔲ"), bstack111l1ll_opy_ (u"ࠤࡤࡶ࡬ࡴࡡ࡮ࡧࠥᔳ"), bstack111l1ll_opy_ (u"ࠥࡴࡦࡸࡡ࡮ࡵࠥᔴ"), bstack111l1ll_opy_ (u"ࠦ࡮ࡪࡳࠣᔵ"), bstack111l1ll_opy_ (u"ࠧࡻ࡮ࡪࡶࡷࡩࡸࡺࠢᔶ"), bstack111l1ll_opy_ (u"ࠨࡢࡢࡵࡨ࡭ࡩࠨᔷ")]) if len(args) > 0 else {}
        request = args[1] if len(args) > 1 else None
        scope = request.scope if hasattr(request, bstack111l1ll_opy_ (u"ࠢࡴࡥࡲࡴࡪࠨᔸ")) else fixturedef.get(bstack111l1ll_opy_ (u"ࠣࡵࡦࡳࡵ࡫ࠢᔹ"), None)
        fixturename = request.fixturename if hasattr(request, bstack111l1ll_opy_ (u"ࠤࡩ࡭ࡽࡺࡵࡳࡧࡱࡥࡲ࡫ࠢᔺ")) else None
        node = request.node if hasattr(request, bstack111l1ll_opy_ (u"ࠥࡲࡴࡪࡥࠣᔻ")) else None
        target = request.node.nodeid if hasattr(node, bstack111l1ll_opy_ (u"ࠦࡳࡵࡤࡦ࡫ࡧࠦᔼ")) else None
        baseid = fixturedef.get(bstack111l1ll_opy_ (u"ࠧࡨࡡࡴࡧ࡬ࡨࠧᔽ"), None) or bstack111l1ll_opy_ (u"ࠨࠢᔾ")
        if (not target or len(baseid) > 0) and hasattr(request, bstack111l1ll_opy_ (u"ࠢࡠࡲࡼࡪࡺࡴࡣࡪࡶࡨࡱࠧᔿ")):
            target = bstack1ll1l11ll11_opy_.__11llllll111_opy_(request._pyfuncitem.location) if hasattr(request._pyfuncitem, bstack111l1ll_opy_ (u"ࠣ࡮ࡲࡧࡦࡺࡩࡰࡰࠥᕀ")) else None
            if target and not TestFramework.bstack1lllll1l1ll_opy_(target):
                self.__1l1111lllll_opy_(context, test_framework_state, target, (target, request._pyfuncitem.location))
                node = request._pyfuncitem
                self.logger.debug(bstack111l1ll_opy_ (u"ࠤࡷࡶࡦࡩ࡫ࡠࡨ࡬ࡼࡹࡻࡲࡦࡡࡨࡺࡪࡴࡴ࠻ࠢࡩࡥࡱࡲࡢࡢࡥ࡮ࠤࡹࡧࡲࡨࡧࡷࡁࢀࡺࡡࡳࡩࡨࡸࢂࠦࡦࡪࡺࡷࡹࡷ࡫࡮ࡢ࡯ࡨࡁࢀ࡬ࡩࡹࡶࡸࡶࡪࡴࡡ࡮ࡧࢀࠤࡳࡵࡤࡦ࠿ࡾࡲࡴࡪࡥࡾࠢࡨࡺࡪࡴࡴ࠾ࡽࡷࡩࡸࡺ࡟ࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡷࡹࡧࡴࡦࡿ࠱ࠦᕁ") + str(test_hook_state) + bstack111l1ll_opy_ (u"ࠥࠦᕂ"))
        if not fixturedef or not scope or not target:
            self.logger.warning(bstack111l1ll_opy_ (u"ࠦࡹࡸࡡࡤ࡭ࡢࡪ࡮ࡾࡴࡶࡴࡨࡣࡪࡼࡥ࡯ࡶ࠽ࠤࡺࡴࡨࡢࡰࡧࡰࡪࡪࠠࡦࡸࡨࡲࡹࡃࡻࡵࡧࡶࡸࡤ࡬ࡲࡢ࡯ࡨࡻࡴࡸ࡫ࡠࡵࡷࡥࡹ࡫ࡽ࠯ࡽࡷࡩࡸࡺ࡟ࡩࡱࡲ࡯ࡤࡹࡴࡢࡶࡨࢁࠥ࡬ࡩࡹࡶࡸࡶࡪࡪࡥࡧ࠿ࡾࡪ࡮ࡾࡴࡶࡴࡨࡨࡪ࡬ࡽࠡࡵࡦࡳࡵ࡫࠽ࡼࡵࡦࡳࡵ࡫ࡽࠡࡶࡤࡶ࡬࡫ࡴ࠾ࠤᕃ") + str(target) + bstack111l1ll_opy_ (u"ࠧࠨᕄ"))
            return None
        instance = TestFramework.bstack1lllll1l1ll_opy_(target)
        if not instance:
            self.logger.warning(bstack111l1ll_opy_ (u"ࠨࡴࡳࡣࡦ࡯ࡤ࡬ࡩࡹࡶࡸࡶࡪࡥࡥࡷࡧࡱࡸ࠿ࠦࡵ࡯ࡪࡤࡲࡩࡲࡥࡥࠢࡨࡺࡪࡴࡴ࠾ࡽࡷࡩࡸࡺ࡟ࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡷࡹࡧࡴࡦࡿ࠱ࡿࡹ࡫ࡳࡵࡡ࡫ࡳࡴࡱ࡟ࡴࡶࡤࡸࡪࢃࠠࡧ࡫ࡻࡸࡺࡸࡥ࡯ࡣࡰࡩࡂࢁࡦࡪࡺࡷࡹࡷ࡫࡮ࡢ࡯ࡨࢁࠥࡹࡣࡰࡲࡨࡁࢀࡹࡣࡰࡲࡨࢁࠥࡨࡡࡴࡧ࡬ࡨࡂࢁࡢࡢࡵࡨ࡭ࡩࢃࠠࡵࡣࡵ࡫ࡪࡺ࠽ࠣᕅ") + str(target) + bstack111l1ll_opy_ (u"ࠢࠣᕆ"))
            return None
        bstack1l111l1l1l1_opy_ = TestFramework.bstack1llll1lllll_opy_(instance, bstack1ll1l11ll11_opy_.bstack1l1111l111l_opy_, {})
        if os.getenv(bstack111l1ll_opy_ (u"ࠣࡕࡇࡏࡤࡉࡌࡊࡡࡉࡐࡆࡍ࡟ࡇࡋ࡛ࡘ࡚ࡘࡅࡔࠤᕇ"), bstack111l1ll_opy_ (u"ࠤ࠴ࠦᕈ")) == bstack111l1ll_opy_ (u"ࠥ࠵ࠧᕉ"):
            bstack1l1111lll11_opy_ = bstack111l1ll_opy_ (u"ࠦ࠿ࠨᕊ").join((scope, fixturename))
            bstack1l111l1llll_opy_ = datetime.now(tz=timezone.utc)
            bstack11llll1ll11_opy_ = {
                bstack111l1ll_opy_ (u"ࠧࡱࡥࡺࠤᕋ"): bstack1l1111lll11_opy_,
                bstack111l1ll_opy_ (u"ࠨࡴࡢࡩࡶࠦᕌ"): bstack1ll1l11ll11_opy_.__1l1111l1lll_opy_(request.node),
                bstack111l1ll_opy_ (u"ࠢࡧ࡫ࡻࡸࡺࡸࡥࠣᕍ"): fixturedef,
                bstack111l1ll_opy_ (u"ࠣࡵࡦࡳࡵ࡫ࠢᕎ"): scope,
                bstack111l1ll_opy_ (u"ࠤࡷࡽࡵ࡫ࠢᕏ"): None,
            }
            try:
                if test_hook_state == bstack1llll11l111_opy_.POST and callable(getattr(args[-1], bstack111l1ll_opy_ (u"ࠥ࡫ࡪࡺ࡟ࡳࡧࡶࡹࡱࡺࠢᕐ"), None)):
                    bstack11llll1ll11_opy_[bstack111l1ll_opy_ (u"ࠦࡹࡿࡰࡦࠤᕑ")] = TestFramework.bstack1l1l1l1l111_opy_(args[-1].get_result())
            except Exception as e:
                pass
            if test_hook_state == bstack1llll11l111_opy_.PRE:
                bstack11llll1ll11_opy_[bstack111l1ll_opy_ (u"ࠧࡻࡵࡪࡦࠥᕒ")] = uuid4().__str__()
                bstack11llll1ll11_opy_[bstack1ll1l11ll11_opy_.bstack11llllllll1_opy_] = bstack1l111l1llll_opy_
            elif test_hook_state == bstack1llll11l111_opy_.POST:
                bstack11llll1ll11_opy_[bstack1ll1l11ll11_opy_.bstack1l111lll1ll_opy_] = bstack1l111l1llll_opy_
            if bstack1l1111lll11_opy_ in bstack1l111l1l1l1_opy_:
                bstack1l111l1l1l1_opy_[bstack1l1111lll11_opy_].update(bstack11llll1ll11_opy_)
                self.logger.debug(bstack111l1ll_opy_ (u"ࠨࡵࡱࡦࡤࡸࡪࡪࠠࡧ࡫ࡻࡸࡺࡸࡥ࡯ࡣࡰࡩࡂࢁࡦࡪࡺࡷࡹࡷ࡫࡮ࡢ࡯ࡨࢁࠥࡹࡣࡰࡲࡨࡁࢀࡹࡣࡰࡲࡨࢁࠥ࡬ࡩࡹࡶࡸࡶࡪࡃࠢᕓ") + str(bstack1l111l1l1l1_opy_[bstack1l1111lll11_opy_]) + bstack111l1ll_opy_ (u"ࠢࠣᕔ"))
            else:
                bstack1l111l1l1l1_opy_[bstack1l1111lll11_opy_] = bstack11llll1ll11_opy_
                self.logger.debug(bstack111l1ll_opy_ (u"ࠣࡵࡤࡺࡪࡪࠠࡧ࡫ࡻࡸࡺࡸࡥ࡯ࡣࡰࡩࡂࢁࡦࡪࡺࡷࡹࡷ࡫࡮ࡢ࡯ࡨࢁࠥࡹࡣࡰࡲࡨࡁࢀࡹࡣࡰࡲࡨࢁࠥ࡬ࡩࡹࡶࡸࡶࡪࡃࡻࡵࡧࡶࡸࡤ࡬ࡩࡹࡶࡸࡶࡪࢃࠠࡵࡴࡤࡧࡰ࡫ࡤࡠࡨ࡬ࡼࡹࡻࡲࡦࡵࡀࠦᕕ") + str(len(bstack1l111l1l1l1_opy_)) + bstack111l1ll_opy_ (u"ࠤࠥᕖ"))
        TestFramework.bstack1llllll1lll_opy_(instance, bstack1ll1l11ll11_opy_.bstack1l1111l111l_opy_, bstack1l111l1l1l1_opy_)
        self.logger.debug(bstack111l1ll_opy_ (u"ࠥࡷࡦࡼࡥࡥࠢࡩ࡭ࡽࡺࡵࡳࡧࡶࡁࢀࡲࡥ࡯ࠪࡷࡶࡦࡩ࡫ࡦࡦࡢࡪ࡮ࡾࡴࡶࡴࡨࡷ࠮ࢃࠠࡪࡰࡶࡸࡦࡴࡣࡦ࠿ࠥᕗ") + str(instance.ref()) + bstack111l1ll_opy_ (u"ࠦࠧᕘ"))
        return instance
    def __1l1111lllll_opy_(
        self,
        context: bstack1l111111ll1_opy_,
        test_framework_state: bstack1lll11ll1ll_opy_,
        target: Any,
        *args,
    ):
        ctx = bstack1llllll11l1_opy_.create_context(target)
        ob = bstack1ll1l1l1lll_opy_(ctx, self.bstack1ll11l1l1l1_opy_, self.bstack11lllll11ll_opy_, test_framework_state)
        TestFramework.bstack1l111lll11l_opy_(ob, {
            TestFramework.bstack1ll1111ll1l_opy_: context.test_framework_name,
            TestFramework.bstack1l1l1l1l11l_opy_: context.test_framework_version,
            TestFramework.bstack11lllll1lll_opy_: [],
            bstack1ll1l11ll11_opy_.bstack1l1111l111l_opy_: {},
            bstack1ll1l11ll11_opy_.bstack1l1111l11ll_opy_: {},
            bstack1ll1l11ll11_opy_.bstack11llll1ll1l_opy_: {},
        })
        if len(args) > 1 and isinstance(args[1], tuple):
            TestFramework.bstack1llllll1lll_opy_(ob, TestFramework.bstack1l11111ll1l_opy_, str(args[1][0]))
        if context.platform_index >= 0:
            TestFramework.bstack1llllll1lll_opy_(ob, TestFramework.bstack1ll111lllll_opy_, context.platform_index)
        TestFramework.bstack1lllllll1l1_opy_[ctx.id] = ob
        self.logger.debug(bstack111l1ll_opy_ (u"ࠧࡹࡡࡷࡧࡧࠤ࡮ࡴࡳࡵࡣࡱࡧࡪࠦࡣࡵࡺ࠱࡭ࡩࡃࡻࡤࡶࡻ࠲࡮ࡪࡽࠡࡶࡤࡶ࡬࡫ࡴ࠾ࡽࡷࡥࡷ࡭ࡥࡵࡿࠣࡥࡷ࡭ࡳ࠾ࡽࡤࡶ࡬ࡹࡽࠡ࡫ࡱࡷࡹࡧ࡮ࡤࡧࡶࡁࠧᕙ") + str(TestFramework.bstack1lllllll1l1_opy_.keys()) + bstack111l1ll_opy_ (u"ࠨࠢᕚ"))
        return ob
    def bstack1l1l1l1ll1l_opy_(self, instance: bstack1ll1l1l1lll_opy_, bstack1lllll11111_opy_: Tuple[bstack1lll11ll1ll_opy_, bstack1llll11l111_opy_]):
        bstack1l111ll1ll1_opy_ = (
            bstack1ll1l11ll11_opy_.bstack1l11111ll11_opy_
            if bstack1lllll11111_opy_[1] == bstack1llll11l111_opy_.PRE
            else bstack1ll1l11ll11_opy_.bstack1l1111111ll_opy_
        )
        hook = bstack1ll1l11ll11_opy_.bstack1l111l1111l_opy_(instance, bstack1l111ll1ll1_opy_)
        entries = hook.get(TestFramework.bstack1l111ll1lll_opy_, []) if isinstance(hook, dict) else []
        entries.extend(TestFramework.bstack1llll1lllll_opy_(instance, TestFramework.bstack11lllll1lll_opy_, []))
        return entries
    def bstack1l1ll11lll1_opy_(self, instance: bstack1ll1l1l1lll_opy_, bstack1lllll11111_opy_: Tuple[bstack1lll11ll1ll_opy_, bstack1llll11l111_opy_]):
        bstack1l111ll1ll1_opy_ = (
            bstack1ll1l11ll11_opy_.bstack1l11111ll11_opy_
            if bstack1lllll11111_opy_[1] == bstack1llll11l111_opy_.PRE
            else bstack1ll1l11ll11_opy_.bstack1l1111111ll_opy_
        )
        bstack1ll1l11ll11_opy_.bstack1l1111ll1ll_opy_(instance, bstack1l111ll1ll1_opy_)
        TestFramework.bstack1llll1lllll_opy_(instance, TestFramework.bstack11lllll1lll_opy_, []).clear()
    def bstack1l111ll111l_opy_(self, hook: Dict[str, Any]) -> None:
        bstack111l1ll_opy_ (u"ࠢࠣࠤࠍࠤࠥࠦࠠࠡࠢࠣࠤࡕࡸ࡯ࡤࡧࡶࡷࡪࡹࠠࡵࡪࡨࠤࡍࡵ࡯࡬ࡎࡨࡺࡪࡲࠠࡢࡶࡷࡥࡨ࡮࡭ࡦࡰࡷࡷࠥࡹࡩ࡮࡫࡯ࡥࡷࠦࡴࡰࠢࡷ࡬ࡪࠦࡊࡢࡸࡤࠤ࡮ࡳࡰ࡭ࡧࡰࡩࡳࡺࡡࡵ࡫ࡲࡲ࠳ࠐࠠࠡࠢࠣࠤࠥࠦࠠࡕࡪ࡬ࡷࠥࡳࡥࡵࡪࡲࡨ࠿ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢ࠰ࠤࡈ࡮ࡥࡤ࡭ࡶࠤࡹ࡮ࡥࠡࡊࡲࡳࡰࡒࡥࡷࡧ࡯ࠤࡩ࡯ࡲࡦࡥࡷࡳࡷࡿࠠࡪࡰࡶ࡭ࡩ࡫ࠠࡿ࠱࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠱ࡘࡴࡱࡵࡡࡥࡧࡧࡅࡹࡺࡡࡤࡪࡰࡩࡳࡺࡳ࠯ࠌࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥ࠳ࠠࡇࡱࡵࠤࡪࡧࡣࡩࠢࡩ࡭ࡱ࡫ࠠࡪࡰࠣ࡬ࡴࡵ࡫ࡠ࡮ࡨࡺࡪࡲ࡟ࡧ࡫࡯ࡩࡸ࠲ࠠࡳࡧࡳࡰࡦࡩࡥࡴࠢࠥࡘࡪࡹࡴࡍࡧࡹࡩࡱࠨࠠࡸ࡫ࡷ࡬ࠥࠨࡈࡰࡱ࡮ࡐࡪࡼࡥ࡭ࠤࠣ࡭ࡳࠦࡩࡵࡵࠣࡴࡦࡺࡨ࠯ࠌࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥ࠳ࠠࡊࡨࠣࡥࠥ࡬ࡩ࡭ࡧࠣ࡭ࡳࠦࡴࡩࡧࠣࡨ࡮ࡸࡥࡤࡶࡲࡶࡾࠦ࡭ࡢࡶࡦ࡬ࡪࡹࠠࡢࠢࡰࡳࡩ࡯ࡦࡪࡧࡧࠤ࡭ࡵ࡯࡬࠯࡯ࡩࡻ࡫࡬ࠡࡨ࡬ࡰࡪ࠲ࠠࡪࡶࠣࡧࡷ࡫ࡡࡵࡧࡶࠤࡦࠦࡌࡰࡩࡈࡲࡹࡸࡹࠡࡱࡥ࡮ࡪࡩࡴࠡࡹ࡬ࡸ࡭ࠦࡡࡵࡶࡤࡧ࡭ࡳࡥ࡯ࡶࠣࡨࡪࡺࡡࡪ࡮ࡶ࠲ࠏࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡ࠯ࠣࡗ࡮ࡳࡩ࡭ࡣࡵࡰࡾ࠲ࠠࡪࡶࠣࡴࡷࡵࡣࡦࡵࡶࡩࡸࠦࡂࡶ࡫࡯ࡨࡑ࡫ࡶࡦ࡮ࠣࡥࡹࡺࡡࡤࡪࡰࡩࡳࡺࡳࠡ࡮ࡲࡧࡦࡺࡥࡥࠢ࡬ࡲࠥࡎ࡯ࡰ࡭ࡏࡩࡻ࡫࡬࠰ࡄࡸ࡭ࡱࡪࡌࡦࡸࡨࡰࡍࡵ࡯࡬ࡇࡹࡩࡳࡺࠠࡣࡻࠣࡶࡪࡶ࡬ࡢࡥ࡬ࡲ࡬ࠦࠢࡃࡷ࡬ࡰࡩࡒࡥࡷࡧ࡯ࠦࠥࡽࡩࡵࡪࠣࠦࡍࡵ࡯࡬ࡎࡨࡺࡪࡲ࠯ࡃࡷ࡬ࡰࡩࡒࡥࡷࡧ࡯ࡌࡴࡵ࡫ࡆࡸࡨࡲࡹࠨ࠮ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤ࠲ࠦࡔࡩࡧࠣࡧࡷ࡫ࡡࡵࡧࡧࠤࡑࡵࡧࡆࡰࡷࡶࡾࠦ࡯ࡣ࡬ࡨࡧࡹࡹࠠࡢࡴࡨࠤࡦࡪࡤࡦࡦࠣࡸࡴࠦࡴࡩࡧࠣ࡬ࡴࡵ࡫ࠨࡵࠣࠦࡱࡵࡧࡴࠤࠣࡰ࡮ࡹࡴ࠯ࠌࠣࠤࠥࠦࠠࠡࠢࠣࡅࡷ࡭ࡳ࠻ࠌࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࡩࡱࡲ࡯࠿ࠦࡔࡩࡧࠣࡩࡻ࡫࡮ࡵࠢࡧ࡭ࡨࡺࡩࡰࡰࡤࡶࡾࠦࡣࡰࡰࡷࡥ࡮ࡴࡩ࡯ࡩࠣࡩࡽ࡯ࡳࡵ࡫ࡱ࡫ࠥࡲ࡯ࡨࡵࠣࡥࡳࡪࠠࡩࡱࡲ࡯ࠥ࡯࡮ࡧࡱࡵࡱࡦࡺࡩࡰࡰ࠱ࠎࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢ࡫ࡳࡴࡱ࡟࡭ࡧࡹࡩࡱࡥࡦࡪ࡮ࡨࡷ࠿ࠦࡌࡪࡵࡷࠤࡴ࡬ࠠࡑࡣࡷ࡬ࠥࡵࡢ࡫ࡧࡦࡸࡸࠦࡦࡳࡱࡰࠤࡹ࡮ࡥࠡࡖࡨࡷࡹࡒࡥࡷࡧ࡯ࠤࡲࡵ࡮ࡪࡶࡲࡶ࡮ࡴࡧ࠯ࠌࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࡣࡷ࡬ࡰࡩࡥ࡬ࡦࡸࡨࡰࡤ࡬ࡩ࡭ࡧࡶ࠾ࠥࡒࡩࡴࡶࠣࡳ࡫ࠦࡐࡢࡶ࡫ࠤࡴࡨࡪࡦࡥࡷࡷࠥ࡬ࡲࡰ࡯ࠣࡸ࡭࡫ࠠࡃࡷ࡬ࡰࡩࡒࡥࡷࡧ࡯ࠤࡲࡵ࡮ࡪࡶࡲࡶ࡮ࡴࡧ࠯ࠌࠣࠤࠥࠦࠠࠡࠢࠣࠦࠧࠨᕛ")
        global _1l1ll11l11l_opy_
        platform_index = os.environ[bstack111l1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡑࡎࡄࡘࡋࡕࡒࡎࡡࡌࡒࡉࡋࡘࠨᕜ")]
        bstack1l1ll1l11l1_opy_ = os.path.join(bstack1l1ll11l1ll_opy_, (bstack1l1l1l1llll_opy_ + str(platform_index)), bstack11llll11ll1_opy_)
        if not os.path.exists(bstack1l1ll1l11l1_opy_) or not os.path.isdir(bstack1l1ll1l11l1_opy_):
            self.logger.debug(bstack111l1ll_opy_ (u"ࠤࡇ࡭ࡷ࡫ࡣࡵࡱࡵࡽࠥࡪ࡯ࡦࡵࠣࡲࡴࡺࠠࡦࡺ࡬ࡷࡹࡹࠠࡵࡱࠣࡴࡷࡵࡣࡦࡵࡶࠤࢀࢃࠢᕝ").format(bstack1l1ll1l11l1_opy_))
            return
        logs = hook.get(bstack111l1ll_opy_ (u"ࠥࡰࡴ࡭ࡳࠣᕞ"), [])
        with os.scandir(bstack1l1ll1l11l1_opy_) as entries:
            for entry in entries:
                abs_path = os.path.abspath(entry.path)
                if abs_path in _1l1ll11l11l_opy_:
                    self.logger.info(bstack111l1ll_opy_ (u"ࠦࡕࡧࡴࡩࠢࡤࡰࡷ࡫ࡡࡥࡻࠣࡴࡷࡵࡣࡦࡵࡶࡩࡩࠦࡻࡾࠤᕟ").format(abs_path))
                    continue
                if entry.is_file():
                    try:
                        timestamp = datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc).isoformat()
                    except Exception:
                        timestamp = bstack111l1ll_opy_ (u"ࠧࠨᕠ")
                    log_entry = bstack1ll1l1l11ll_opy_(
                        kind=bstack111l1ll_opy_ (u"ࠨࡔࡆࡕࡗࡣࡆ࡚ࡔࡂࡅࡋࡑࡊࡔࡔࠣᕡ"),
                        message=bstack111l1ll_opy_ (u"ࠢࠣᕢ"),
                        level=bstack111l1ll_opy_ (u"ࠣࠤᕣ"),
                        timestamp=timestamp,
                        fileName=entry.name,
                        bstack1l1l1lll111_opy_=entry.stat().st_size,
                        bstack1l1ll1ll1ll_opy_=bstack111l1ll_opy_ (u"ࠤࡐࡅࡓ࡛ࡁࡍࡡࡘࡔࡑࡕࡁࡅࠤᕤ"),
                        bstack1l1l1l1_opy_=os.path.abspath(entry.path),
                        bstack11lllll1l1l_opy_=hook.get(TestFramework.bstack11lllll1ll1_opy_)
                    )
                    logs.append(log_entry)
                    _1l1ll11l11l_opy_.add(abs_path)
        platform_index = os.environ[bstack111l1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡓࡐࡆ࡚ࡆࡐࡔࡐࡣࡎࡔࡄࡆ࡚ࠪᕥ")]
        bstack11lllll11l1_opy_ = os.path.join(bstack1l1ll11l1ll_opy_, (bstack1l1l1l1llll_opy_ + str(platform_index)), bstack11llll11ll1_opy_, bstack11llll11lll_opy_)
        if not os.path.exists(bstack11lllll11l1_opy_) or not os.path.isdir(bstack11lllll11l1_opy_):
            self.logger.info(bstack111l1ll_opy_ (u"ࠦࡓࡵࠠࡃࡷ࡬ࡰࡩࡒࡥࡷࡧ࡯ࡌࡴࡵ࡫ࡆࡸࡨࡲࡹࠦࡡࡵࡶࡤࡧ࡭ࡳࡥ࡯ࡶࡶࠤࡩ࡯ࡲࡦࡥࡷࡳࡷࡿࠠࡧࡱࡸࡲࡩࠦࡡࡵ࠼ࠣࡿࢂࠨᕦ").format(bstack11lllll11l1_opy_))
        else:
            self.logger.info(bstack111l1ll_opy_ (u"ࠧࡖࡲࡰࡥࡨࡷࡸ࡯࡮ࡨࠢࡅࡹ࡮ࡲࡤࡍࡧࡹࡩࡱࡎ࡯ࡰ࡭ࡈࡺࡪࡴࡴࠡࡣࡷࡸࡦࡩࡨ࡮ࡧࡱࡸࡸࠦࡦࡳࡱࡰࠤࡩ࡯ࡲࡦࡥࡷࡳࡷࡿ࠺ࠡࡽࢀࠦᕧ").format(bstack11lllll11l1_opy_))
            with os.scandir(bstack11lllll11l1_opy_) as entries:
                for entry in entries:
                    abs_path = os.path.abspath(entry.path)
                    if abs_path in _1l1ll11l11l_opy_:
                        self.logger.info(bstack111l1ll_opy_ (u"ࠨࡐࡢࡶ࡫ࠤࡦࡲࡲࡦࡣࡧࡽࠥࡶࡲࡰࡥࡨࡷࡸ࡫ࡤࠡࡽࢀࠦᕨ").format(abs_path))
                        continue
                    if entry.is_file():
                        try:
                            timestamp = datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc).isoformat()
                        except Exception:
                            timestamp = bstack111l1ll_opy_ (u"ࠢࠣᕩ")
                        log_entry = bstack1ll1l1l11ll_opy_(
                            kind=bstack111l1ll_opy_ (u"ࠣࡖࡈࡗ࡙ࡥࡁࡕࡖࡄࡇࡍࡓࡅࡏࡖࠥᕪ"),
                            message=bstack111l1ll_opy_ (u"ࠤࠥᕫ"),
                            level=bstack111l1ll_opy_ (u"ࠥࡆࡺ࡯࡬ࡥࡎࡨࡺࡪࡲࠢᕬ"),
                            timestamp=timestamp,
                            fileName=entry.name,
                            bstack1l1l1lll111_opy_=entry.stat().st_size,
                            bstack1l1ll1ll1ll_opy_=bstack111l1ll_opy_ (u"ࠦࡒࡇࡎࡖࡃࡏࡣ࡚ࡖࡌࡐࡃࡇࠦᕭ"),
                            bstack1l1l1l1_opy_=os.path.abspath(entry.path),
                            bstack1l1lll11111_opy_=hook.get(TestFramework.bstack11lllll1ll1_opy_)
                        )
                        logs.append(log_entry)
                        _1l1ll11l11l_opy_.add(abs_path)
        hook[bstack111l1ll_opy_ (u"ࠧࡲ࡯ࡨࡵࠥᕮ")] = logs
    def bstack1l1l1l111ll_opy_(
        self,
        bstack1l1l1ll11l1_opy_: bstack1ll1l1l1lll_opy_,
        entries: List[bstack1ll1l1l11ll_opy_],
    ):
        req = structs.LogCreatedEventRequest()
        req.bin_session_id = os.environ.get(bstack111l1ll_opy_ (u"ࠨࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡉࡌࡊࡡࡅࡍࡓࡥࡓࡆࡕࡖࡍࡔࡔ࡟ࡊࡆࠥᕯ"))
        req.platform_index = TestFramework.bstack1llll1lllll_opy_(bstack1l1l1ll11l1_opy_, TestFramework.bstack1ll111lllll_opy_)
        req.execution_context.hash = str(bstack1l1l1ll11l1_opy_.context.hash)
        req.execution_context.thread_id = str(bstack1l1l1ll11l1_opy_.context.thread_id)
        req.execution_context.process_id = str(bstack1l1l1ll11l1_opy_.context.process_id)
        for entry in entries:
            log_entry = req.logs.add()
            log_entry.test_framework_name = TestFramework.bstack1llll1lllll_opy_(bstack1l1l1ll11l1_opy_, TestFramework.bstack1ll1111ll1l_opy_)
            log_entry.test_framework_version = TestFramework.bstack1llll1lllll_opy_(bstack1l1l1ll11l1_opy_, TestFramework.bstack1l1l1l1l11l_opy_)
            log_entry.uuid = entry.bstack11lllll1l1l_opy_
            log_entry.test_framework_state = bstack1l1l1ll11l1_opy_.state.name
            log_entry.message = entry.message.encode(bstack111l1ll_opy_ (u"ࠢࡶࡶࡩ࠱࠽ࠨᕰ"))
            log_entry.kind = entry.kind
            log_entry.timestamp = (
                entry.timestamp.isoformat()
                if isinstance(entry.timestamp, datetime)
                else datetime.now(tz=timezone.utc).isoformat()
            )
            log_entry.level = bstack111l1ll_opy_ (u"ࠣࠤᕱ")
            if entry.kind == bstack111l1ll_opy_ (u"ࠤࡗࡉࡘ࡚࡟ࡂࡖࡗࡅࡈࡎࡍࡆࡐࡗࠦᕲ"):
                log_entry.file_name = entry.fileName
                log_entry.file_size = entry.bstack1l1l1lll111_opy_
                log_entry.file_path = entry.bstack1l1l1l1_opy_
        def bstack1l1ll1l1l11_opy_():
            bstack1l1ll1l1l1_opy_ = datetime.now()
            try:
                self.bstack1ll1ll1ll1l_opy_.LogCreatedEvent(req)
                bstack1l1l1ll11l1_opy_.bstack1l1ll11lll_opy_(bstack111l1ll_opy_ (u"ࠥ࡫ࡷࡶࡣ࠻ࡵࡨࡲࡩࡥ࡬ࡰࡩࡢࡧࡷ࡫ࡡࡵࡧࡧࡣࡪࡼࡥ࡯ࡶࡢࡥࡹࡺࡡࡤࡪࡰࡩࡳࡺࠢᕳ"), datetime.now() - bstack1l1ll1l1l1_opy_)
            except grpc.RpcError as e:
                self.log_error(bstack111l1ll_opy_ (u"ࠦࡷࡶࡣ࠮ࡧࡵࡶࡴࡸ࠺ࠡࡵࡨࡲࡩࡥ࡬ࡰࡩࡢࡧࡷ࡫ࡡࡵࡧࡧࡣࡪࡼࡥ࡯ࡶࡢࡥࡹࡺࡡࡤࡪࡰࡩࡳࡺࠠࡼࡿࠥᕴ").format(str(e)))
                traceback.print_exc()
        self.bstack11111111l1_opy_.enqueue(bstack1l1ll1l1l11_opy_)
    def __1l111l1ll1l_opy_(self, instance) -> None:
        bstack111l1ll_opy_ (u"ࠧࠨࠢࠋࠢࠣࠤࠥࠦࠠࠡࠢࡏࡳࡦࡪࡳࠡࡥࡸࡷࡹࡵ࡭ࠡࡶࡤ࡫ࡸࠦࡦࡰࡴࠣࡸ࡭࡫ࠠࡨ࡫ࡹࡩࡳࠦࡴࡦࡵࡷࠤ࡫ࡸࡡ࡮ࡧࡺࡳࡷࡱࠠࡪࡰࡶࡸࡦࡴࡣࡦ࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤࡈࡸࡥࡢࡶࡨࡷࠥࡧࠠࡥ࡫ࡦࡸࠥࡩ࡯࡯ࡶࡤ࡭ࡳ࡯࡮ࡨࠢࡷࡩࡸࡺࠠ࡭ࡧࡹࡩࡱࠦࡣࡶࡵࡷࡳࡲࠦ࡭ࡦࡶࡤࡨࡦࡺࡡࠡࡴࡨࡸࡷ࡯ࡥࡷࡧࡧࠤ࡫ࡸ࡯࡮ࠌࠣࠤࠥࠦࠠࠡࠢࠣࡇࡺࡹࡴࡰ࡯ࡗࡥ࡬ࡓࡡ࡯ࡣࡪࡩࡷࠦࡡ࡯ࡦࠣࡹࡵࡪࡡࡵࡧࡶࠤࡹ࡮ࡥࠡ࡫ࡱࡷࡹࡧ࡮ࡤࡧࠣࡷࡹࡧࡴࡦࠢࡸࡷ࡮ࡴࡧࠡࡵࡨࡸࡤࡹࡴࡢࡶࡨࡣࡪࡴࡴࡳ࡫ࡨࡷ࠳ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠣࠤࠥᕵ")
        bstack1l111l1ll11_opy_ = {bstack111l1ll_opy_ (u"ࠨࡣࡶࡵࡷࡳࡲࡥ࡭ࡦࡶࡤࡨࡦࡺࡡࠣᕶ"): bstack1ll1l1l111l_opy_.bstack1l111l11ll1_opy_()}
        from browserstack_sdk.sdk_cli.test_framework import TestFramework
        TestFramework.bstack1l111lll11l_opy_(instance, bstack1l111l1ll11_opy_)
    @staticmethod
    def bstack1l111l1111l_opy_(instance: bstack1ll1l1l1lll_opy_, bstack1l111ll1ll1_opy_: str):
        bstack1l111l11l1l_opy_ = (
            bstack1ll1l11ll11_opy_.bstack1l1111l11ll_opy_
            if bstack1l111ll1ll1_opy_ == bstack1ll1l11ll11_opy_.bstack1l1111111ll_opy_
            else bstack1ll1l11ll11_opy_.bstack11llll1ll1l_opy_
        )
        bstack11lllll1l11_opy_ = TestFramework.bstack1llll1lllll_opy_(instance, bstack1l111ll1ll1_opy_, None)
        bstack1l111l111ll_opy_ = TestFramework.bstack1llll1lllll_opy_(instance, bstack1l111l11l1l_opy_, None) if bstack11lllll1l11_opy_ else None
        return (
            bstack1l111l111ll_opy_[bstack11lllll1l11_opy_][-1]
            if isinstance(bstack1l111l111ll_opy_, dict) and len(bstack1l111l111ll_opy_.get(bstack11lllll1l11_opy_, [])) > 0
            else None
        )
    @staticmethod
    def bstack1l1111ll1ll_opy_(instance: bstack1ll1l1l1lll_opy_, bstack1l111ll1ll1_opy_: str):
        hook = bstack1ll1l11ll11_opy_.bstack1l111l1111l_opy_(instance, bstack1l111ll1ll1_opy_)
        if isinstance(hook, dict):
            hook.get(TestFramework.bstack1l111ll1lll_opy_, []).clear()
    @staticmethod
    def __1l111l11lll_opy_(instance: bstack1ll1l1l1lll_opy_, *args):
        if len(args) < 2 or not callable(getattr(args[1], bstack111l1ll_opy_ (u"ࠢࡨࡧࡷࡣࡷ࡫ࡣࡰࡴࡧࡷࠧᕷ"), None)):
            return
        if os.getenv(bstack111l1ll_opy_ (u"ࠣࡕࡇࡏࡤࡉࡌࡊࡡࡉࡐࡆࡍ࡟ࡍࡑࡊࡗࠧᕸ"), bstack111l1ll_opy_ (u"ࠤ࠴ࠦᕹ")) != bstack111l1ll_opy_ (u"ࠥ࠵ࠧᕺ"):
            bstack1ll1l11ll11_opy_.logger.warning(bstack111l1ll_opy_ (u"ࠦ࡮࡭࡮ࡰࡴ࡬ࡲ࡬ࠦࡣࡢࡲ࡯ࡳ࡬ࠨᕻ"))
            return
        bstack1l1111llll1_opy_ = {
            bstack111l1ll_opy_ (u"ࠧࡹࡥࡵࡷࡳࠦᕼ"): (bstack1ll1l11ll11_opy_.bstack1l11111ll11_opy_, bstack1ll1l11ll11_opy_.bstack11llll1ll1l_opy_),
            bstack111l1ll_opy_ (u"ࠨࡴࡦࡣࡵࡨࡴࡽ࡮ࠣᕽ"): (bstack1ll1l11ll11_opy_.bstack1l1111111ll_opy_, bstack1ll1l11ll11_opy_.bstack1l1111l11ll_opy_),
        }
        for when in (bstack111l1ll_opy_ (u"ࠢࡴࡧࡷࡹࡵࠨᕾ"), bstack111l1ll_opy_ (u"ࠣࡥࡤࡰࡱࠨᕿ"), bstack111l1ll_opy_ (u"ࠤࡷࡩࡦࡸࡤࡰࡹࡱࠦᖀ")):
            bstack1l111111lll_opy_ = args[1].get_records(when)
            if not bstack1l111111lll_opy_:
                continue
            records = [
                bstack1ll1l1l11ll_opy_(
                    kind=TestFramework.bstack1l1ll1llll1_opy_,
                    message=r.message,
                    level=r.levelname if hasattr(r, bstack111l1ll_opy_ (u"ࠥࡰࡪࡼࡥ࡭ࡰࡤࡱࡪࠨᖁ")) and r.levelname else None,
                    timestamp=(
                        datetime.fromtimestamp(r.created, tz=timezone.utc)
                        if hasattr(r, bstack111l1ll_opy_ (u"ࠦࡨࡸࡥࡢࡶࡨࡨࠧᖂ")) and r.created
                        else None
                    ),
                )
                for r in bstack1l111111lll_opy_
                if isinstance(getattr(r, bstack111l1ll_opy_ (u"ࠧࡳࡥࡴࡵࡤ࡫ࡪࠨᖃ"), None), str) and r.message.strip()
            ]
            if not records:
                continue
            bstack1l1111l11l1_opy_, bstack1l111l11l1l_opy_ = bstack1l1111llll1_opy_.get(when, (None, None))
            bstack1l11111llll_opy_ = TestFramework.bstack1llll1lllll_opy_(instance, bstack1l1111l11l1_opy_, None) if bstack1l1111l11l1_opy_ else None
            bstack1l111l111ll_opy_ = TestFramework.bstack1llll1lllll_opy_(instance, bstack1l111l11l1l_opy_, None) if bstack1l11111llll_opy_ else None
            if isinstance(bstack1l111l111ll_opy_, dict) and len(bstack1l111l111ll_opy_.get(bstack1l11111llll_opy_, [])) > 0:
                hook = bstack1l111l111ll_opy_[bstack1l11111llll_opy_][-1]
                if isinstance(hook, dict) and TestFramework.bstack1l111ll1lll_opy_ in hook:
                    hook[TestFramework.bstack1l111ll1lll_opy_].extend(records)
                    continue
            logs = TestFramework.bstack1llll1lllll_opy_(instance, TestFramework.bstack11lllll1lll_opy_, [])
            logs.extend(records)
    @staticmethod
    def __1l1111lll1l_opy_(test) -> Dict[str, Any]:
        bstack1111ll1l_opy_ = bstack1ll1l11ll11_opy_.__11llllll111_opy_(test.location) if hasattr(test, bstack111l1ll_opy_ (u"ࠨ࡬ࡰࡥࡤࡸ࡮ࡵ࡮ࠣᖄ")) else getattr(test, bstack111l1ll_opy_ (u"ࠢ࡯ࡱࡧࡩ࡮ࡪࠢᖅ"), None)
        test_name = test.name if hasattr(test, bstack111l1ll_opy_ (u"ࠣࡰࡤࡱࡪࠨᖆ")) else None
        bstack11lllllllll_opy_ = test.fspath.strpath if hasattr(test, bstack111l1ll_opy_ (u"ࠤࡩࡷࡵࡧࡴࡩࠤᖇ")) and test.fspath else None
        if not bstack1111ll1l_opy_ or not test_name or not bstack11lllllllll_opy_:
            return None
        code = None
        if hasattr(test, bstack111l1ll_opy_ (u"ࠥࡳࡧࡰࠢᖈ")):
            try:
                import inspect
                code = inspect.getsource(test.obj)
            except:
                pass
        bstack11llll1l1ll_opy_ = []
        try:
            bstack11llll1l1ll_opy_ = bstack11l1l1111l_opy_.bstack1111ll1l1l_opy_(test)
        except:
            bstack1ll1l11ll11_opy_.logger.warning(bstack111l1ll_opy_ (u"࡚ࠦࡴࡡࡣ࡮ࡨࠤࡹࡵࠠࡧ࡫ࡱࡨࠥࡺࡥࡴࡶࠣࡷࡨࡵࡰࡦࡵ࠯ࠤࡹ࡫ࡳࡵࠢࡶࡧࡴࡶࡥࡴࠢࡺ࡭ࡱࡲࠠࡣࡧࠣࡶࡪࡹ࡯࡭ࡸࡨࡨࠥ࡯࡮ࠡࡅࡏࡍࠧᖉ"))
        return {
            TestFramework.bstack1ll111l1ll1_opy_: uuid4().__str__(),
            TestFramework.bstack1l111llll1l_opy_: bstack1111ll1l_opy_,
            TestFramework.bstack1ll111lll1l_opy_: test_name,
            TestFramework.bstack1l1l11lll11_opy_: getattr(test, bstack111l1ll_opy_ (u"ࠧࡴ࡯ࡥࡧ࡬ࡨࠧᖊ"), None),
            TestFramework.bstack1l11111l111_opy_: bstack11lllllllll_opy_,
            TestFramework.bstack1l11111111l_opy_: bstack1ll1l11ll11_opy_.__1l1111l1lll_opy_(test),
            TestFramework.bstack11lllllll11_opy_: code,
            TestFramework.bstack1l1l111111l_opy_: TestFramework.bstack1l111llll11_opy_,
            TestFramework.bstack1l11l1l1111_opy_: bstack1111ll1l_opy_,
            TestFramework.bstack11llll1l11l_opy_: bstack11llll1l1ll_opy_
        }
    @staticmethod
    def __1l1111l1lll_opy_(test) -> List[str]:
        markers = []
        current = test
        while current:
            own_markers = getattr(current, bstack111l1ll_opy_ (u"ࠨ࡯ࡸࡰࡢࡱࡦࡸ࡫ࡦࡴࡶࠦᖋ"), [])
            markers.extend([getattr(m, bstack111l1ll_opy_ (u"ࠢ࡯ࡣࡰࡩࠧᖌ"), None) for m in own_markers if getattr(m, bstack111l1ll_opy_ (u"ࠣࡰࡤࡱࡪࠨᖍ"), None)])
            current = getattr(current, bstack111l1ll_opy_ (u"ࠤࡳࡥࡷ࡫࡮ࡵࠤᖎ"), None)
        return markers
    @staticmethod
    def __11llllll111_opy_(location):
        return bstack111l1ll_opy_ (u"ࠥ࠾࠿ࠨᖏ").join(filter(lambda x: isinstance(x, str), location))