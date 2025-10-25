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
import collections
import datetime
import json
import os
import platform
import re
import subprocess
import traceback
import tempfile
import multiprocessing
import threading
import sys
import logging
from math import ceil
from unittest import result
import urllib
from urllib.parse import urlparse
import copy
import zipfile
import git
import requests
from packaging import version
from bstack_utils.config import Config
from bstack_utils.constants import (bstack1l11l111ll_opy_, bstack1lll1lll1l_opy_, bstack1llll1l1l_opy_,
                                    bstack11l1lll11l1_opy_, bstack11l1ll1lll1_opy_, bstack11l1lll1l11_opy_, bstack11l1l1l11l1_opy_)
from bstack_utils.measure import measure
from bstack_utils.messages import bstack11lll11l1l_opy_, bstack11l1ll11l1_opy_
from bstack_utils.proxy import bstack1ll1l111l_opy_, bstack11l1l1ll11_opy_
from bstack_utils.constants import *
from bstack_utils import bstack1lllll11l1_opy_
from bstack_utils.bstack111111111_opy_ import bstack1l11l11l11_opy_
from browserstack_sdk._version import __version__
bstack111ll1ll1_opy_ = Config.bstack111l11l11_opy_()
logger = bstack1lllll11l1_opy_.get_logger(__name__, bstack1lllll11l1_opy_.bstack1lll1l1l1l1_opy_())
def bstack11ll1l11l1l_opy_(config):
    return config[bstack111l1ll_opy_ (u"ࠨࡷࡶࡩࡷࡔࡡ࡮ࡧࠪᬚ")]
def bstack11ll1l1l1l1_opy_(config):
    return config[bstack111l1ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡳࡴࡍࡨࡽࠬᬛ")]
def bstack1llll111_opy_():
    try:
        import playwright
        return True
    except ImportError:
        return False
def bstack11l11l11l1l_opy_(obj):
    values = []
    bstack111llll1lll_opy_ = re.compile(bstack111l1ll_opy_ (u"ࡵࠦࡣࡉࡕࡔࡖࡒࡑࡤ࡚ࡁࡈࡡ࡟ࡨ࠰ࠪࠢᬜ"), re.I)
    for key in obj.keys():
        if bstack111llll1lll_opy_.match(key):
            values.append(obj[key])
    return values
def bstack11l11l1ll1l_opy_(config):
    tags = []
    tags.extend(bstack11l11l11l1l_opy_(os.environ))
    tags.extend(bstack11l11l11l1l_opy_(config))
    return tags
def bstack11l111ll1ll_opy_(markers):
    tags = []
    for marker in markers:
        tags.append(marker.name)
    return tags
def bstack11l1111llll_opy_(bstack11l11l11l11_opy_):
    if not bstack11l11l11l11_opy_:
        return bstack111l1ll_opy_ (u"ࠫࠬᬝ")
    return bstack111l1ll_opy_ (u"ࠧࢁࡽࠡࠪࡾࢁ࠮ࠨᬞ").format(bstack11l11l11l11_opy_.name, bstack11l11l11l11_opy_.email)
def bstack11ll11l1ll1_opy_():
    try:
        repo = git.Repo(search_parent_directories=True)
        bstack11l11l1l1ll_opy_ = repo.common_dir
        info = {
            bstack111l1ll_opy_ (u"ࠨࡳࡩࡣࠥᬟ"): repo.head.commit.hexsha,
            bstack111l1ll_opy_ (u"ࠢࡴࡪࡲࡶࡹࡥࡳࡩࡣࠥᬠ"): repo.git.rev_parse(repo.head.commit, short=True),
            bstack111l1ll_opy_ (u"ࠣࡤࡵࡥࡳࡩࡨࠣᬡ"): repo.active_branch.name,
            bstack111l1ll_opy_ (u"ࠤࡷࡥ࡬ࠨᬢ"): repo.git.describe(all=True, tags=True, exact_match=True),
            bstack111l1ll_opy_ (u"ࠥࡧࡴࡳ࡭ࡪࡶࡷࡩࡷࠨᬣ"): bstack11l1111llll_opy_(repo.head.commit.committer),
            bstack111l1ll_opy_ (u"ࠦࡨࡵ࡭࡮࡫ࡷࡸࡪࡸ࡟ࡥࡣࡷࡩࠧᬤ"): repo.head.commit.committed_datetime.isoformat(),
            bstack111l1ll_opy_ (u"ࠧࡧࡵࡵࡪࡲࡶࠧᬥ"): bstack11l1111llll_opy_(repo.head.commit.author),
            bstack111l1ll_opy_ (u"ࠨࡡࡶࡶ࡫ࡳࡷࡥࡤࡢࡶࡨࠦᬦ"): repo.head.commit.authored_datetime.isoformat(),
            bstack111l1ll_opy_ (u"ࠢࡤࡱࡰࡱ࡮ࡺ࡟࡮ࡧࡶࡷࡦ࡭ࡥࠣᬧ"): repo.head.commit.message,
            bstack111l1ll_opy_ (u"ࠣࡴࡲࡳࡹࠨᬨ"): repo.git.rev_parse(bstack111l1ll_opy_ (u"ࠤ࠰࠱ࡸ࡮࡯ࡸ࠯ࡷࡳࡵࡲࡥࡷࡧ࡯ࠦᬩ")),
            bstack111l1ll_opy_ (u"ࠥࡧࡴࡳ࡭ࡰࡰࡢ࡫࡮ࡺ࡟ࡥ࡫ࡵࠦᬪ"): bstack11l11l1l1ll_opy_,
            bstack111l1ll_opy_ (u"ࠦࡼࡵࡲ࡬ࡶࡵࡩࡪࡥࡧࡪࡶࡢࡨ࡮ࡸࠢᬫ"): subprocess.check_output([bstack111l1ll_opy_ (u"ࠧ࡭ࡩࡵࠤᬬ"), bstack111l1ll_opy_ (u"ࠨࡲࡦࡸ࠰ࡴࡦࡸࡳࡦࠤᬭ"), bstack111l1ll_opy_ (u"ࠢ࠮࠯ࡪ࡭ࡹ࠳ࡣࡰ࡯ࡰࡳࡳ࠳ࡤࡪࡴࠥᬮ")]).strip().decode(
                bstack111l1ll_opy_ (u"ࠨࡷࡷࡪ࠲࠾ࠧᬯ")),
            bstack111l1ll_opy_ (u"ࠤ࡯ࡥࡸࡺ࡟ࡵࡣࡪࠦᬰ"): repo.git.describe(tags=True, abbrev=0, always=True),
            bstack111l1ll_opy_ (u"ࠥࡧࡴࡳ࡭ࡪࡶࡶࡣࡸ࡯࡮ࡤࡧࡢࡰࡦࡹࡴࡠࡶࡤ࡫ࠧᬱ"): repo.git.rev_list(
                bstack111l1ll_opy_ (u"ࠦࢀࢃ࠮࠯ࡽࢀࠦᬲ").format(repo.head.commit, repo.git.describe(tags=True, abbrev=0, always=True)), count=True)
        }
        remotes = repo.remotes
        bstack11l1111l111_opy_ = []
        for remote in remotes:
            bstack111lll1ll11_opy_ = {
                bstack111l1ll_opy_ (u"ࠧࡴࡡ࡮ࡧࠥᬳ"): remote.name,
                bstack111l1ll_opy_ (u"ࠨࡵࡳ࡮᬴ࠥ"): remote.url,
            }
            bstack11l1111l111_opy_.append(bstack111lll1ll11_opy_)
        bstack11l11ll1ll1_opy_ = {
            bstack111l1ll_opy_ (u"ࠢ࡯ࡣࡰࡩࠧᬵ"): bstack111l1ll_opy_ (u"ࠣࡩ࡬ࡸࠧᬶ"),
            **info,
            bstack111l1ll_opy_ (u"ࠤࡵࡩࡲࡵࡴࡦࡵࠥᬷ"): bstack11l1111l111_opy_
        }
        bstack11l11ll1ll1_opy_ = bstack111ll1ll111_opy_(bstack11l11ll1ll1_opy_)
        return bstack11l11ll1ll1_opy_
    except git.InvalidGitRepositoryError:
        return {}
    except Exception as err:
        print(bstack111l1ll_opy_ (u"ࠥࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡩ࡯ࠢࡳࡳࡵࡻ࡬ࡢࡶ࡬ࡲ࡬ࠦࡇࡪࡶࠣࡱࡪࡺࡡࡥࡣࡷࡥࠥࡽࡩࡵࡪࠣࡩࡷࡸ࡯ࡳ࠼ࠣࡿࢂࠨᬸ").format(err))
        return {}
def bstack111lll11ll1_opy_(bstack111lll11l11_opy_=None):
    bstack111l1ll_opy_ (u"ࠦࠧࠨࠊࠡࠢࠣࠤࡌ࡫ࡴࠡࡩ࡬ࡸࠥࡳࡥࡵࡣࡧࡥࡹࡧࠠࡴࡲࡨࡧ࡮࡬ࡩࡤࡣ࡯ࡰࡾࠦࡦࡰࡴࡰࡥࡹࡺࡥࡥࠢࡩࡳࡷࠦࡁࡊࠢࡶࡩࡱ࡫ࡣࡵ࡫ࡲࡲࠥࡻࡳࡦࠢࡦࡥࡸ࡫ࡳࠡࡨࡲࡶࠥ࡫ࡡࡤࡪࠣࡪࡴࡲࡤࡦࡴࠣ࡭ࡳࠦࡴࡩࡧࠣࡰ࡮ࡹࡴ࠯ࠌࠣࠤࠥࠦࡁࡳࡩࡶ࠾ࠏࠦࠠࠡࠢࠣࠤࠥࠦࡦࡰ࡮ࡧࡩࡷࡹࠠࠩ࡮࡬ࡷࡹ࠲ࠠࡰࡲࡷ࡭ࡴࡴࡡ࡭ࠫ࠽ࠤࡑ࡯ࡳࡵࠢࡲࡪࠥ࡬࡯࡭ࡦࡨࡶࠥࡶࡡࡵࡪࡶࠤࡹࡵࠠࡦࡺࡷࡶࡦࡩࡴࠡࡩ࡬ࡸࠥࡳࡥࡵࡣࡧࡥࡹࡧࠠࡧࡴࡲࡱ࠳ࠦࡄࡦࡨࡤࡹࡱࡺࡳࠡࡶࡲࠤࡠࡵࡳ࠯ࡩࡨࡸࡨࡽࡤࠩࠫࡠ࠲ࠏࠦࠠࠡࠢࡕࡩࡹࡻࡲ࡯ࡵ࠽ࠎࠥࠦࠠࠡࠢࠣࠤࠥࡲࡩࡴࡶ࠽ࠤࡑ࡯ࡳࡵࠢࡲࡪࠥࡪࡩࡤࡶࡶ࠰ࠥ࡫ࡡࡤࡪࠣࡧࡴࡴࡴࡢ࡫ࡱ࡭ࡳ࡭ࠠࡨ࡫ࡷࠤࡲ࡫ࡴࡢࡦࡤࡸࡦࠦࡦࡰࡴࠣࡥࠥ࡬࡯࡭ࡦࡨࡶ࠳ࠐࠠࠡࠢࠣࠦࠧࠨᬹ")
    if bstack111lll11l11_opy_ == None: # bstack11l111llll1_opy_ for bstack111lll11111_opy_-repo
        bstack111lll11l11_opy_ = [os.getcwd()]
    results = []
    for folder in bstack111lll11l11_opy_:
        try:
            repo = git.Repo(folder, search_parent_directories=True)
            result = {
                bstack111l1ll_opy_ (u"ࠧࡶࡲࡊࡦࠥᬺ"): bstack111l1ll_opy_ (u"ࠨࠢᬻ"),
                bstack111l1ll_opy_ (u"ࠢࡧ࡫࡯ࡩࡸࡉࡨࡢࡰࡪࡩࡩࠨᬼ"): [],
                bstack111l1ll_opy_ (u"ࠣࡣࡸࡸ࡭ࡵࡲࡴࠤᬽ"): [],
                bstack111l1ll_opy_ (u"ࠤࡳࡶࡉࡧࡴࡦࠤᬾ"): bstack111l1ll_opy_ (u"ࠥࠦᬿ"),
                bstack111l1ll_opy_ (u"ࠦࡨࡵ࡭࡮࡫ࡷࡑࡪࡹࡳࡢࡩࡨࡷࠧᭀ"): [],
                bstack111l1ll_opy_ (u"ࠧࡶࡲࡕ࡫ࡷࡰࡪࠨᭁ"): bstack111l1ll_opy_ (u"ࠨࠢᭂ"),
                bstack111l1ll_opy_ (u"ࠢࡱࡴࡇࡩࡸࡩࡲࡪࡲࡷ࡭ࡴࡴࠢᭃ"): bstack111l1ll_opy_ (u"ࠣࠤ᭄"),
                bstack111l1ll_opy_ (u"ࠤࡳࡶࡗࡧࡷࡅ࡫ࡩࡪࠧᭅ"): bstack111l1ll_opy_ (u"ࠥࠦᭆ")
            }
            bstack111lll1llll_opy_ = repo.active_branch.name
            bstack11l111111ll_opy_ = repo.head.commit
            result[bstack111l1ll_opy_ (u"ࠦࡵࡸࡉࡥࠤᭇ")] = bstack11l111111ll_opy_.hexsha
            bstack111ll1ll1l1_opy_ = _111ll1l111l_opy_(repo)
            logger.debug(bstack111l1ll_opy_ (u"ࠧࡈࡡࡴࡧࠣࡦࡷࡧ࡮ࡤࡪࠣࡪࡴࡸࠠࡤࡱࡰࡴࡦࡸࡩࡴࡱࡱ࠾ࠥࠨᭈ") + str(bstack111ll1ll1l1_opy_) + bstack111l1ll_opy_ (u"ࠨࠢᭉ"))
            if bstack111ll1ll1l1_opy_:
                try:
                    bstack11l11lll111_opy_ = repo.git.diff(bstack111l1ll_opy_ (u"ࠢ࠮࠯ࡱࡥࡲ࡫࠭ࡰࡰ࡯ࡽࠧᭊ"), bstack1111l11ll1_opy_ (u"ࠣࡽࡥࡥࡸ࡫࡟ࡣࡴࡤࡲࡨ࡮ࡽ࠯࠰࠱ࡿࡨࡻࡲࡳࡧࡱࡸࡤࡨࡲࡢࡰࡦ࡬ࢂࠨᭋ")).split(bstack111l1ll_opy_ (u"ࠩ࡟ࡲࠬᭌ"))
                    logger.debug(bstack111l1ll_opy_ (u"ࠥࡇ࡭ࡧ࡮ࡨࡧࡧࠤ࡫࡯࡬ࡦࡵࠣࡦࡪࡺࡷࡦࡧࡱࠤࢀࡨࡡࡴࡧࡢࡦࡷࡧ࡮ࡤࡪࢀࠤࡦࡴࡤࠡࡽࡦࡹࡷࡸࡥ࡯ࡶࡢࡦࡷࡧ࡮ࡤࡪࢀ࠾ࠥࠨ᭍") + str(bstack11l11lll111_opy_) + bstack111l1ll_opy_ (u"ࠦࠧ᭎"))
                    result[bstack111l1ll_opy_ (u"ࠧ࡬ࡩ࡭ࡧࡶࡇ࡭ࡧ࡮ࡨࡧࡧࠦ᭏")] = [f.strip() for f in bstack11l11lll111_opy_ if f.strip()]
                    commits = list(repo.iter_commits(bstack1111l11ll1_opy_ (u"ࠨࡻࡣࡣࡶࡩࡤࡨࡲࡢࡰࡦ࡬ࢂ࠴࠮ࡼࡥࡸࡶࡷ࡫࡮ࡵࡡࡥࡶࡦࡴࡣࡩࡿࠥ᭐")))
                except Exception:
                    logger.debug(bstack111l1ll_opy_ (u"ࠢࡇࡣ࡬ࡰࡪࡪࠠࡵࡱࠣ࡫ࡪࡺࠠࡤࡪࡤࡲ࡬࡫ࡤࠡࡨ࡬ࡰࡪࡹࠠࡧࡴࡲࡱࠥࡨࡲࡢࡰࡦ࡬ࠥࡩ࡯࡮ࡲࡤࡶ࡮ࡹ࡯࡯࠰ࠣࡊࡦࡲ࡬ࡪࡰࡪࠤࡧࡧࡣ࡬ࠢࡷࡳࠥࡸࡥࡤࡧࡱࡸࠥࡩ࡯࡮࡯࡬ࡸࡸ࠴ࠢ᭑"))
                    commits = list(repo.iter_commits(max_count=10))
                    if commits:
                        result[bstack111l1ll_opy_ (u"ࠣࡨ࡬ࡰࡪࡹࡃࡩࡣࡱ࡫ࡪࡪࠢ᭒")] = _11l11l1l111_opy_(commits[:5])
            else:
                commits = list(repo.iter_commits(max_count=10))
                if commits:
                    result[bstack111l1ll_opy_ (u"ࠤࡩ࡭ࡱ࡫ࡳࡄࡪࡤࡲ࡬࡫ࡤࠣ᭓")] = _11l11l1l111_opy_(commits[:5])
            bstack11l11111l1l_opy_ = set()
            bstack11l1111l1ll_opy_ = []
            for commit in commits:
                logger.debug(bstack111l1ll_opy_ (u"ࠥࡔࡷࡵࡣࡦࡵࡶ࡭ࡳ࡭ࠠࡤࡱࡰࡱ࡮ࡺ࠺ࠡࠤ᭔") + str(commit.message) + bstack111l1ll_opy_ (u"ࠦࠧ᭕"))
                bstack111ll1lll1l_opy_ = commit.author.name if commit.author else bstack111l1ll_opy_ (u"࡛ࠧ࡮࡬ࡰࡲࡻࡳࠨ᭖")
                bstack11l11111l1l_opy_.add(bstack111ll1lll1l_opy_)
                bstack11l1111l1ll_opy_.append({
                    bstack111l1ll_opy_ (u"ࠨ࡭ࡦࡵࡶࡥ࡬࡫ࠢ᭗"): commit.message.strip(),
                    bstack111l1ll_opy_ (u"ࠢࡶࡵࡨࡶࠧ᭘"): bstack111ll1lll1l_opy_
                })
            result[bstack111l1ll_opy_ (u"ࠣࡣࡸࡸ࡭ࡵࡲࡴࠤ᭙")] = list(bstack11l11111l1l_opy_)
            result[bstack111l1ll_opy_ (u"ࠤࡦࡳࡲࡳࡩࡵࡏࡨࡷࡸࡧࡧࡦࡵࠥ᭚")] = bstack11l1111l1ll_opy_
            result[bstack111l1ll_opy_ (u"ࠥࡴࡷࡊࡡࡵࡧࠥ᭛")] = bstack11l111111ll_opy_.committed_datetime.strftime(bstack111l1ll_opy_ (u"ࠦࠪ࡟࠭ࠦ࡯࠰ࠩࡩࠨ᭜"))
            if (not result[bstack111l1ll_opy_ (u"ࠧࡶࡲࡕ࡫ࡷࡰࡪࠨ᭝")] or result[bstack111l1ll_opy_ (u"ࠨࡰࡳࡖ࡬ࡸࡱ࡫ࠢ᭞")].strip() == bstack111l1ll_opy_ (u"ࠢࠣ᭟")) and bstack11l111111ll_opy_.message:
                bstack11l11ll1111_opy_ = bstack11l111111ll_opy_.message.strip().splitlines()
                result[bstack111l1ll_opy_ (u"ࠣࡲࡵࡘ࡮ࡺ࡬ࡦࠤ᭠")] = bstack11l11ll1111_opy_[0] if bstack11l11ll1111_opy_ else bstack111l1ll_opy_ (u"ࠤࠥ᭡")
                if len(bstack11l11ll1111_opy_) > 2:
                    result[bstack111l1ll_opy_ (u"ࠥࡴࡷࡊࡥࡴࡥࡵ࡭ࡵࡺࡩࡰࡰࠥ᭢")] = bstack111l1ll_opy_ (u"ࠫࡡࡴࠧ᭣").join(bstack11l11ll1111_opy_[2:]).strip()
            results.append(result)
        except Exception as err:
            logger.error(bstack111l1ll_opy_ (u"ࠧࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡ࡫ࡱࠤࡵࡵࡰࡶ࡮ࡤࡸ࡮ࡴࡧࠡࡉ࡬ࡸࠥࡳࡥࡵࡣࡧࡥࡹࡧࠠࡧࡱࡵࠤࡆࡏࠠࡴࡧ࡯ࡩࡨࡺࡩࡰࡰࠣࠬ࡫ࡵ࡬ࡥࡧࡵ࠾ࠥࢁࡦࡰ࡮ࡧࡩࡷࢃࠩ࠻ࠢࠥ᭤") + str(err) + bstack111l1ll_opy_ (u"ࠨࠢ᭥"))
    filtered_results = [
        result
        for result in results
        if _111ll1lll11_opy_(result)
    ]
    return filtered_results
def _111ll1lll11_opy_(result):
    bstack111l1ll_opy_ (u"ࠢࠣࠤࠍࠤࠥࠦࠠࡉࡧ࡯ࡴࡪࡸࠠࡵࡱࠣࡧ࡭࡫ࡣ࡬ࠢ࡬ࡪࠥࡧࠠࡨ࡫ࡷࠤࡲ࡫ࡴࡢࡦࡤࡸࡦࠦࡲࡦࡵࡸࡰࡹࠦࡩࡴࠢࡹࡥࡱ࡯ࡤࠡࠪࡱࡳࡳ࠳ࡥ࡮ࡲࡷࡽࠥ࡬ࡩ࡭ࡧࡶࡇ࡭ࡧ࡮ࡨࡧࡧࠤࡦࡴࡤࠡࡣࡸࡸ࡭ࡵࡲࡴࠫ࠱ࠎࠥࠦࠠࠡࠤࠥࠦ᭦")
    return (
        isinstance(result.get(bstack111l1ll_opy_ (u"ࠣࡨ࡬ࡰࡪࡹࡃࡩࡣࡱ࡫ࡪࡪࠢ᭧"), None), list)
        and len(result[bstack111l1ll_opy_ (u"ࠤࡩ࡭ࡱ࡫ࡳࡄࡪࡤࡲ࡬࡫ࡤࠣ᭨")]) > 0
        and isinstance(result.get(bstack111l1ll_opy_ (u"ࠥࡥࡺࡺࡨࡰࡴࡶࠦ᭩"), None), list)
        and len(result[bstack111l1ll_opy_ (u"ࠦࡦࡻࡴࡩࡱࡵࡷࠧ᭪")]) > 0
    )
def _111ll1l111l_opy_(repo):
    bstack111l1ll_opy_ (u"ࠧࠨࠢࠋࠢࠣࠤ࡚ࠥࡲࡺࠢࡷࡳࠥࡪࡥࡵࡧࡵࡱ࡮ࡴࡥࠡࡶ࡫ࡩࠥࡨࡡࡴࡧࠣࡦࡷࡧ࡮ࡤࡪࠣࡪࡴࡸࠠࡵࡪࡨࠤ࡬࡯ࡶࡦࡰࠣࡶࡪࡶ࡯ࠡࡹ࡬ࡸ࡭ࡵࡵࡵࠢ࡫ࡥࡷࡪࡣࡰࡦࡨࡨࠥࡴࡡ࡮ࡧࡶࠤࡦࡴࡤࠡࡹࡲࡶࡰࠦࡷࡪࡶ࡫ࠤࡦࡲ࡬ࠡࡘࡆࡗࠥࡶࡲࡰࡸ࡬ࡨࡪࡸࡳ࠯ࠌࠣࠤࠥࠦࡒࡦࡶࡸࡶࡳࡹࠠࡵࡪࡨࠤࡩ࡫ࡦࡢࡷ࡯ࡸࠥࡨࡲࡢࡰࡦ࡬ࠥ࡯ࡦࠡࡲࡲࡷࡸ࡯ࡢ࡭ࡧ࠯ࠤࡪࡲࡳࡦࠢࡑࡳࡳ࡫࠮ࠋࠢࠣࠤࠥࠨࠢࠣ᭫")
    try:
        try:
            origin = repo.remotes.origin
            bstack11l111l111l_opy_ = origin.refs[bstack111l1ll_opy_ (u"࠭ࡈࡆࡃࡇ᭬ࠫ")]
            target = bstack11l111l111l_opy_.reference.name
            if target.startswith(bstack111l1ll_opy_ (u"ࠧࡰࡴ࡬࡫࡮ࡴ࠯ࠨ᭭")):
                return target
        except Exception:
            pass
        if repo.remotes and repo.remotes.origin.refs:
            for ref in repo.remotes.origin.refs:
                if ref.name.startswith(bstack111l1ll_opy_ (u"ࠨࡱࡵ࡭࡬࡯࡮࠰ࠩ᭮")):
                    return ref.name
        if repo.heads:
            return repo.heads[0].name
    except Exception:
        pass
    return None
def _11l11l1l111_opy_(commits):
    bstack111l1ll_opy_ (u"ࠤࠥࠦࠏࠦࠠࠡࠢࡊࡩࡹࠦ࡬ࡪࡵࡷࠤࡴ࡬ࠠࡤࡪࡤࡲ࡬࡫ࡤࠡࡨ࡬ࡰࡪࡹࠠࡧࡴࡲࡱࠥࡧࠠ࡭࡫ࡶࡸࠥࡵࡦࠡࡥࡲࡱࡲ࡯ࡴࡴ࠰ࠍࠤࠥࠦࠠࠣࠤࠥ᭯")
    bstack11l11lll111_opy_ = set()
    try:
        for commit in commits:
            if commit.parents:
                for parent in commit.parents:
                    diff = commit.diff(parent)
                    for bstack11l11lll11l_opy_ in diff:
                        if bstack11l11lll11l_opy_.a_path:
                            bstack11l11lll111_opy_.add(bstack11l11lll11l_opy_.a_path)
                        if bstack11l11lll11l_opy_.b_path:
                            bstack11l11lll111_opy_.add(bstack11l11lll11l_opy_.b_path)
    except Exception:
        pass
    return list(bstack11l11lll111_opy_)
def bstack111ll1ll111_opy_(bstack11l11ll1ll1_opy_):
    bstack111lllll111_opy_ = bstack11l11ll11l1_opy_(bstack11l11ll1ll1_opy_)
    if bstack111lllll111_opy_ and bstack111lllll111_opy_ > bstack11l1lll11l1_opy_:
        bstack11l11l1lll1_opy_ = bstack111lllll111_opy_ - bstack11l1lll11l1_opy_
        bstack111llll11l1_opy_ = bstack111ll11l11l_opy_(bstack11l11ll1ll1_opy_[bstack111l1ll_opy_ (u"ࠥࡧࡴࡳ࡭ࡪࡶࡢࡱࡪࡹࡳࡢࡩࡨࠦ᭰")], bstack11l11l1lll1_opy_)
        bstack11l11ll1ll1_opy_[bstack111l1ll_opy_ (u"ࠦࡨࡵ࡭࡮࡫ࡷࡣࡲ࡫ࡳࡴࡣࡪࡩࠧ᭱")] = bstack111llll11l1_opy_
        logger.info(bstack111l1ll_opy_ (u"࡚ࠧࡨࡦࠢࡦࡳࡲࡳࡩࡵࠢ࡫ࡥࡸࠦࡢࡦࡧࡱࠤࡹࡸࡵ࡯ࡥࡤࡸࡪࡪ࠮ࠡࡕ࡬ࡾࡪࠦ࡯ࡧࠢࡦࡳࡲࡳࡩࡵࠢࡤࡪࡹ࡫ࡲࠡࡶࡵࡹࡳࡩࡡࡵ࡫ࡲࡲࠥ࡯ࡳࠡࡽࢀࠤࡐࡈࠢ᭲")
                    .format(bstack11l11ll11l1_opy_(bstack11l11ll1ll1_opy_) / 1024))
    return bstack11l11ll1ll1_opy_
def bstack11l11ll11l1_opy_(bstack1ll1lllll1_opy_):
    try:
        if bstack1ll1lllll1_opy_:
            bstack111ll11l111_opy_ = json.dumps(bstack1ll1lllll1_opy_)
            bstack111lll1l1ll_opy_ = sys.getsizeof(bstack111ll11l111_opy_)
            return bstack111lll1l1ll_opy_
    except Exception as e:
        logger.debug(bstack111l1ll_opy_ (u"ࠨࡓࡰ࡯ࡨࡸ࡭࡯࡮ࡨࠢࡺࡩࡳࡺࠠࡸࡴࡲࡲ࡬ࠦࡷࡩ࡫࡯ࡩࠥࡩࡡ࡭ࡥࡸࡰࡦࡺࡩ࡯ࡩࠣࡷ࡮ࢀࡥࠡࡱࡩࠤࡏ࡙ࡏࡏࠢࡲࡦ࡯࡫ࡣࡵ࠼ࠣࡿࢂࠨ᭳").format(e))
    return -1
def bstack111ll11l11l_opy_(field, bstack11l111l1lll_opy_):
    try:
        bstack111lll1l1l1_opy_ = len(bytes(bstack11l1ll1lll1_opy_, bstack111l1ll_opy_ (u"ࠧࡶࡶࡩ࠱࠽࠭᭴")))
        bstack111ll11ll1l_opy_ = bytes(field, bstack111l1ll_opy_ (u"ࠨࡷࡷࡪ࠲࠾ࠧ᭵"))
        bstack11l11111111_opy_ = len(bstack111ll11ll1l_opy_)
        bstack11l1111l1l1_opy_ = ceil(bstack11l11111111_opy_ - bstack11l111l1lll_opy_ - bstack111lll1l1l1_opy_)
        if bstack11l1111l1l1_opy_ > 0:
            bstack11l1111111l_opy_ = bstack111ll11ll1l_opy_[:bstack11l1111l1l1_opy_].decode(bstack111l1ll_opy_ (u"ࠩࡸࡸ࡫࠳࠸ࠨ᭶"), errors=bstack111l1ll_opy_ (u"ࠪ࡭࡬ࡴ࡯ࡳࡧࠪ᭷")) + bstack11l1ll1lll1_opy_
            return bstack11l1111111l_opy_
    except Exception as e:
        logger.debug(bstack111l1ll_opy_ (u"ࠦࡊࡸࡲࡰࡴࠣࡻ࡭࡯࡬ࡦࠢࡷࡶࡺࡴࡣࡢࡶ࡬ࡲ࡬ࠦࡦࡪࡧ࡯ࡨ࠱ࠦ࡮ࡰࡶ࡫࡭ࡳ࡭ࠠࡸࡣࡶࠤࡹࡸࡵ࡯ࡥࡤࡸࡪࡪࠠࡩࡧࡵࡩ࠿ࠦࡻࡾࠤ᭸").format(e))
    return field
def bstack1l111lll_opy_():
    env = os.environ
    if (bstack111l1ll_opy_ (u"ࠧࡐࡅࡏࡍࡌࡒࡘࡥࡕࡓࡎࠥ᭹") in env and len(env[bstack111l1ll_opy_ (u"ࠨࡊࡆࡐࡎࡍࡓ࡙࡟ࡖࡔࡏࠦ᭺")]) > 0) or (
            bstack111l1ll_opy_ (u"ࠢࡋࡇࡑࡏࡎࡔࡓࡠࡊࡒࡑࡊࠨ᭻") in env and len(env[bstack111l1ll_opy_ (u"ࠣࡌࡈࡒࡐࡏࡎࡔࡡࡋࡓࡒࡋࠢ᭼")]) > 0):
        return {
            bstack111l1ll_opy_ (u"ࠤࡱࡥࡲ࡫ࠢ᭽"): bstack111l1ll_opy_ (u"ࠥࡎࡪࡴ࡫ࡪࡰࡶࠦ᭾"),
            bstack111l1ll_opy_ (u"ࠦࡧࡻࡩ࡭ࡦࡢࡹࡷࡲࠢ᭿"): env.get(bstack111l1ll_opy_ (u"ࠧࡈࡕࡊࡎࡇࡣ࡚ࡘࡌࠣᮀ")),
            bstack111l1ll_opy_ (u"ࠨࡪࡰࡤࡢࡲࡦࡳࡥࠣᮁ"): env.get(bstack111l1ll_opy_ (u"ࠢࡋࡑࡅࡣࡓࡇࡍࡆࠤᮂ")),
            bstack111l1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪ࡟࡯ࡷࡰࡦࡪࡸࠢᮃ"): env.get(bstack111l1ll_opy_ (u"ࠤࡅ࡙ࡎࡒࡄࡠࡐࡘࡑࡇࡋࡒࠣᮄ"))
        }
    if env.get(bstack111l1ll_opy_ (u"ࠥࡇࡎࠨᮅ")) == bstack111l1ll_opy_ (u"ࠦࡹࡸࡵࡦࠤᮆ") and bstack1l1l11l1ll_opy_(env.get(bstack111l1ll_opy_ (u"ࠧࡉࡉࡓࡅࡏࡉࡈࡏࠢᮇ"))):
        return {
            bstack111l1ll_opy_ (u"ࠨ࡮ࡢ࡯ࡨࠦᮈ"): bstack111l1ll_opy_ (u"ࠢࡄ࡫ࡵࡧࡱ࡫ࡃࡊࠤᮉ"),
            bstack111l1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪ࡟ࡶࡴ࡯ࠦᮊ"): env.get(bstack111l1ll_opy_ (u"ࠤࡆࡍࡗࡉࡌࡆࡡࡅ࡙ࡎࡒࡄࡠࡗࡕࡐࠧᮋ")),
            bstack111l1ll_opy_ (u"ࠥ࡮ࡴࡨ࡟࡯ࡣࡰࡩࠧᮌ"): env.get(bstack111l1ll_opy_ (u"ࠦࡈࡏࡒࡄࡎࡈࡣࡏࡕࡂࠣᮍ")),
            bstack111l1ll_opy_ (u"ࠧࡨࡵࡪ࡮ࡧࡣࡳࡻ࡭ࡣࡧࡵࠦᮎ"): env.get(bstack111l1ll_opy_ (u"ࠨࡃࡊࡔࡆࡐࡊࡥࡂࡖࡋࡏࡈࡤࡔࡕࡎࠤᮏ"))
        }
    if env.get(bstack111l1ll_opy_ (u"ࠢࡄࡋࠥᮐ")) == bstack111l1ll_opy_ (u"ࠣࡶࡵࡹࡪࠨᮑ") and bstack1l1l11l1ll_opy_(env.get(bstack111l1ll_opy_ (u"ࠤࡗࡖࡆ࡜ࡉࡔࠤᮒ"))):
        return {
            bstack111l1ll_opy_ (u"ࠥࡲࡦࡳࡥࠣᮓ"): bstack111l1ll_opy_ (u"࡙ࠦࡸࡡࡷ࡫ࡶࠤࡈࡏࠢᮔ"),
            bstack111l1ll_opy_ (u"ࠧࡨࡵࡪ࡮ࡧࡣࡺࡸ࡬ࠣᮕ"): env.get(bstack111l1ll_opy_ (u"ࠨࡔࡓࡃ࡙ࡍࡘࡥࡂࡖࡋࡏࡈࡤ࡝ࡅࡃࡡࡘࡖࡑࠨᮖ")),
            bstack111l1ll_opy_ (u"ࠢ࡫ࡱࡥࡣࡳࡧ࡭ࡦࠤᮗ"): env.get(bstack111l1ll_opy_ (u"ࠣࡖࡕࡅ࡛ࡏࡓࡠࡌࡒࡆࡤࡔࡁࡎࡇࠥᮘ")),
            bstack111l1ll_opy_ (u"ࠤࡥࡹ࡮ࡲࡤࡠࡰࡸࡱࡧ࡫ࡲࠣᮙ"): env.get(bstack111l1ll_opy_ (u"ࠥࡘࡗࡇࡖࡊࡕࡢࡆ࡚ࡏࡌࡅࡡࡑ࡙ࡒࡈࡅࡓࠤᮚ"))
        }
    if env.get(bstack111l1ll_opy_ (u"ࠦࡈࡏࠢᮛ")) == bstack111l1ll_opy_ (u"ࠧࡺࡲࡶࡧࠥᮜ") and env.get(bstack111l1ll_opy_ (u"ࠨࡃࡊࡡࡑࡅࡒࡋࠢᮝ")) == bstack111l1ll_opy_ (u"ࠢࡤࡱࡧࡩࡸ࡮ࡩࡱࠤᮞ"):
        return {
            bstack111l1ll_opy_ (u"ࠣࡰࡤࡱࡪࠨᮟ"): bstack111l1ll_opy_ (u"ࠤࡆࡳࡩ࡫ࡳࡩ࡫ࡳࠦᮠ"),
            bstack111l1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡸࡶࡱࠨᮡ"): None,
            bstack111l1ll_opy_ (u"ࠦ࡯ࡵࡢࡠࡰࡤࡱࡪࠨᮢ"): None,
            bstack111l1ll_opy_ (u"ࠧࡨࡵࡪ࡮ࡧࡣࡳࡻ࡭ࡣࡧࡵࠦᮣ"): None
        }
    if env.get(bstack111l1ll_opy_ (u"ࠨࡂࡊࡖࡅ࡙ࡈࡑࡅࡕࡡࡅࡖࡆࡔࡃࡉࠤᮤ")) and env.get(bstack111l1ll_opy_ (u"ࠢࡃࡋࡗࡆ࡚ࡉࡋࡆࡖࡢࡇࡔࡓࡍࡊࡖࠥᮥ")):
        return {
            bstack111l1ll_opy_ (u"ࠣࡰࡤࡱࡪࠨᮦ"): bstack111l1ll_opy_ (u"ࠤࡅ࡭ࡹࡨࡵࡤ࡭ࡨࡸࠧᮧ"),
            bstack111l1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡸࡶࡱࠨᮨ"): env.get(bstack111l1ll_opy_ (u"ࠦࡇࡏࡔࡃࡗࡆࡏࡊ࡚࡟ࡈࡋࡗࡣࡍ࡚ࡔࡑࡡࡒࡖࡎࡍࡉࡏࠤᮩ")),
            bstack111l1ll_opy_ (u"ࠧࡰ࡯ࡣࡡࡱࡥࡲ࡫᮪ࠢ"): None,
            bstack111l1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡴࡵ࡮ࡤࡨࡶ᮫ࠧ"): env.get(bstack111l1ll_opy_ (u"ࠢࡃࡋࡗࡆ࡚ࡉࡋࡆࡖࡢࡆ࡚ࡏࡌࡅࡡࡑ࡙ࡒࡈࡅࡓࠤᮬ"))
        }
    if env.get(bstack111l1ll_opy_ (u"ࠣࡅࡌࠦᮭ")) == bstack111l1ll_opy_ (u"ࠤࡷࡶࡺ࡫ࠢᮮ") and bstack1l1l11l1ll_opy_(env.get(bstack111l1ll_opy_ (u"ࠥࡈࡗࡕࡎࡆࠤᮯ"))):
        return {
            bstack111l1ll_opy_ (u"ࠦࡳࡧ࡭ࡦࠤ᮰"): bstack111l1ll_opy_ (u"ࠧࡊࡲࡰࡰࡨࠦ᮱"),
            bstack111l1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡻࡲ࡭ࠤ᮲"): env.get(bstack111l1ll_opy_ (u"ࠢࡅࡔࡒࡒࡊࡥࡂࡖࡋࡏࡈࡤࡒࡉࡏࡍࠥ᮳")),
            bstack111l1ll_opy_ (u"ࠣ࡬ࡲࡦࡤࡴࡡ࡮ࡧࠥ᮴"): None,
            bstack111l1ll_opy_ (u"ࠤࡥࡹ࡮ࡲࡤࡠࡰࡸࡱࡧ࡫ࡲࠣ᮵"): env.get(bstack111l1ll_opy_ (u"ࠥࡈࡗࡕࡎࡆࡡࡅ࡙ࡎࡒࡄࡠࡐࡘࡑࡇࡋࡒࠣ᮶"))
        }
    if env.get(bstack111l1ll_opy_ (u"ࠦࡈࡏࠢ᮷")) == bstack111l1ll_opy_ (u"ࠧࡺࡲࡶࡧࠥ᮸") and bstack1l1l11l1ll_opy_(env.get(bstack111l1ll_opy_ (u"ࠨࡓࡆࡏࡄࡔࡍࡕࡒࡆࠤ᮹"))):
        return {
            bstack111l1ll_opy_ (u"ࠢ࡯ࡣࡰࡩࠧᮺ"): bstack111l1ll_opy_ (u"ࠣࡕࡨࡱࡦࡶࡨࡰࡴࡨࠦᮻ"),
            bstack111l1ll_opy_ (u"ࠤࡥࡹ࡮ࡲࡤࡠࡷࡵࡰࠧᮼ"): env.get(bstack111l1ll_opy_ (u"ࠥࡗࡊࡓࡁࡑࡊࡒࡖࡊࡥࡏࡓࡉࡄࡒࡎࡠࡁࡕࡋࡒࡒࡤ࡛ࡒࡍࠤᮽ")),
            bstack111l1ll_opy_ (u"ࠦ࡯ࡵࡢࡠࡰࡤࡱࡪࠨᮾ"): env.get(bstack111l1ll_opy_ (u"࡙ࠧࡅࡎࡃࡓࡌࡔࡘࡅࡠࡌࡒࡆࡤࡔࡁࡎࡇࠥᮿ")),
            bstack111l1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡴࡵ࡮ࡤࡨࡶࠧᯀ"): env.get(bstack111l1ll_opy_ (u"ࠢࡔࡇࡐࡅࡕࡎࡏࡓࡇࡢࡎࡔࡈ࡟ࡊࡆࠥᯁ"))
        }
    if env.get(bstack111l1ll_opy_ (u"ࠣࡅࡌࠦᯂ")) == bstack111l1ll_opy_ (u"ࠤࡷࡶࡺ࡫ࠢᯃ") and bstack1l1l11l1ll_opy_(env.get(bstack111l1ll_opy_ (u"ࠥࡋࡎ࡚ࡌࡂࡄࡢࡇࡎࠨᯄ"))):
        return {
            bstack111l1ll_opy_ (u"ࠦࡳࡧ࡭ࡦࠤᯅ"): bstack111l1ll_opy_ (u"ࠧࡍࡩࡵࡎࡤࡦࠧᯆ"),
            bstack111l1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡻࡲ࡭ࠤᯇ"): env.get(bstack111l1ll_opy_ (u"ࠢࡄࡋࡢࡎࡔࡈ࡟ࡖࡔࡏࠦᯈ")),
            bstack111l1ll_opy_ (u"ࠣ࡬ࡲࡦࡤࡴࡡ࡮ࡧࠥᯉ"): env.get(bstack111l1ll_opy_ (u"ࠤࡆࡍࡤࡐࡏࡃࡡࡑࡅࡒࡋࠢᯊ")),
            bstack111l1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡱࡹࡲࡨࡥࡳࠤᯋ"): env.get(bstack111l1ll_opy_ (u"ࠦࡈࡏ࡟ࡋࡑࡅࡣࡎࡊࠢᯌ"))
        }
    if env.get(bstack111l1ll_opy_ (u"ࠧࡉࡉࠣᯍ")) == bstack111l1ll_opy_ (u"ࠨࡴࡳࡷࡨࠦᯎ") and bstack1l1l11l1ll_opy_(env.get(bstack111l1ll_opy_ (u"ࠢࡃࡗࡌࡐࡉࡑࡉࡕࡇࠥᯏ"))):
        return {
            bstack111l1ll_opy_ (u"ࠣࡰࡤࡱࡪࠨᯐ"): bstack111l1ll_opy_ (u"ࠤࡅࡹ࡮ࡲࡤ࡬࡫ࡷࡩࠧᯑ"),
            bstack111l1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡸࡶࡱࠨᯒ"): env.get(bstack111l1ll_opy_ (u"ࠦࡇ࡛ࡉࡍࡆࡎࡍ࡙ࡋ࡟ࡃࡗࡌࡐࡉࡥࡕࡓࡎࠥᯓ")),
            bstack111l1ll_opy_ (u"ࠧࡰ࡯ࡣࡡࡱࡥࡲ࡫ࠢᯔ"): env.get(bstack111l1ll_opy_ (u"ࠨࡂࡖࡋࡏࡈࡐࡏࡔࡆࡡࡏࡅࡇࡋࡌࠣᯕ")) or env.get(bstack111l1ll_opy_ (u"ࠢࡃࡗࡌࡐࡉࡑࡉࡕࡇࡢࡔࡎࡖࡅࡍࡋࡑࡉࡤࡔࡁࡎࡇࠥᯖ")),
            bstack111l1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪ࡟࡯ࡷࡰࡦࡪࡸࠢᯗ"): env.get(bstack111l1ll_opy_ (u"ࠤࡅ࡙ࡎࡒࡄࡌࡋࡗࡉࡤࡈࡕࡊࡎࡇࡣࡓ࡛ࡍࡃࡇࡕࠦᯘ"))
        }
    if bstack1l1l11l1ll_opy_(env.get(bstack111l1ll_opy_ (u"ࠥࡘࡋࡥࡂࡖࡋࡏࡈࠧᯙ"))):
        return {
            bstack111l1ll_opy_ (u"ࠦࡳࡧ࡭ࡦࠤᯚ"): bstack111l1ll_opy_ (u"ࠧ࡜ࡩࡴࡷࡤࡰ࡙ࠥࡴࡶࡦ࡬ࡳ࡚ࠥࡥࡢ࡯ࠣࡗࡪࡸࡶࡪࡥࡨࡷࠧᯛ"),
            bstack111l1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡻࡲ࡭ࠤᯜ"): bstack111l1ll_opy_ (u"ࠢࡼࡿࡾࢁࠧᯝ").format(env.get(bstack111l1ll_opy_ (u"ࠨࡕ࡜ࡗ࡙ࡋࡍࡠࡖࡈࡅࡒࡌࡏࡖࡐࡇࡅ࡙ࡏࡏࡏࡕࡈࡖ࡛ࡋࡒࡖࡔࡌࠫᯞ")), env.get(bstack111l1ll_opy_ (u"ࠩࡖ࡝ࡘ࡚ࡅࡎࡡࡗࡉࡆࡓࡐࡓࡑࡍࡉࡈ࡚ࡉࡅࠩᯟ"))),
            bstack111l1ll_opy_ (u"ࠥ࡮ࡴࡨ࡟࡯ࡣࡰࡩࠧᯠ"): env.get(bstack111l1ll_opy_ (u"ࠦࡘ࡟ࡓࡕࡇࡐࡣࡉࡋࡆࡊࡐࡌࡘࡎࡕࡎࡊࡆࠥᯡ")),
            bstack111l1ll_opy_ (u"ࠧࡨࡵࡪ࡮ࡧࡣࡳࡻ࡭ࡣࡧࡵࠦᯢ"): env.get(bstack111l1ll_opy_ (u"ࠨࡂࡖࡋࡏࡈࡤࡈࡕࡊࡎࡇࡍࡉࠨᯣ"))
        }
    if bstack1l1l11l1ll_opy_(env.get(bstack111l1ll_opy_ (u"ࠢࡂࡒࡓ࡚ࡊ࡟ࡏࡓࠤᯤ"))):
        return {
            bstack111l1ll_opy_ (u"ࠣࡰࡤࡱࡪࠨᯥ"): bstack111l1ll_opy_ (u"ࠤࡄࡴࡵࡼࡥࡺࡱࡵ᯦ࠦ"),
            bstack111l1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡸࡶࡱࠨᯧ"): bstack111l1ll_opy_ (u"ࠦࢀࢃ࠯ࡱࡴࡲ࡮ࡪࡩࡴ࠰ࡽࢀ࠳ࢀࢃ࠯ࡣࡷ࡬ࡰࡩࡹ࠯ࡼࡿࠥᯨ").format(env.get(bstack111l1ll_opy_ (u"ࠬࡇࡐࡑࡘࡈ࡝ࡔࡘ࡟ࡖࡔࡏࠫᯩ")), env.get(bstack111l1ll_opy_ (u"࠭ࡁࡑࡒ࡙ࡉ࡞ࡕࡒࡠࡃࡆࡇࡔ࡛ࡎࡕࡡࡑࡅࡒࡋࠧᯪ")), env.get(bstack111l1ll_opy_ (u"ࠧࡂࡒࡓ࡚ࡊ࡟ࡏࡓࡡࡓࡖࡔࡐࡅࡄࡖࡢࡗࡑ࡛ࡇࠨᯫ")), env.get(bstack111l1ll_opy_ (u"ࠨࡃࡓࡔ࡛ࡋ࡙ࡐࡔࡢࡆ࡚ࡏࡌࡅࡡࡌࡈࠬᯬ"))),
            bstack111l1ll_opy_ (u"ࠤ࡭ࡳࡧࡥ࡮ࡢ࡯ࡨࠦᯭ"): env.get(bstack111l1ll_opy_ (u"ࠥࡅࡕࡖࡖࡆ࡛ࡒࡖࡤࡐࡏࡃࡡࡑࡅࡒࡋࠢᯮ")),
            bstack111l1ll_opy_ (u"ࠦࡧࡻࡩ࡭ࡦࡢࡲࡺࡳࡢࡦࡴࠥᯯ"): env.get(bstack111l1ll_opy_ (u"ࠧࡇࡐࡑࡘࡈ࡝ࡔࡘ࡟ࡃࡗࡌࡐࡉࡥࡎࡖࡏࡅࡉࡗࠨᯰ"))
        }
    if env.get(bstack111l1ll_opy_ (u"ࠨࡁ࡛ࡗࡕࡉࡤࡎࡔࡕࡒࡢ࡙ࡘࡋࡒࡠࡃࡊࡉࡓ࡚ࠢᯱ")) and env.get(bstack111l1ll_opy_ (u"ࠢࡕࡈࡢࡆ࡚ࡏࡌࡅࠤ᯲")):
        return {
            bstack111l1ll_opy_ (u"ࠣࡰࡤࡱࡪࠨ᯳"): bstack111l1ll_opy_ (u"ࠤࡄࡾࡺࡸࡥࠡࡅࡌࠦ᯴"),
            bstack111l1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡸࡶࡱࠨ᯵"): bstack111l1ll_opy_ (u"ࠦࢀࢃࡻࡾ࠱ࡢࡦࡺ࡯࡬ࡥ࠱ࡵࡩࡸࡻ࡬ࡵࡵࡂࡦࡺ࡯࡬ࡥࡋࡧࡁࢀࢃࠢ᯶").format(env.get(bstack111l1ll_opy_ (u"࡙࡙ࠬࡔࡖࡈࡑࡤ࡚ࡅࡂࡏࡉࡓ࡚ࡔࡄࡂࡖࡌࡓࡓ࡙ࡅࡓࡘࡈࡖ࡚ࡘࡉࠨ᯷")), env.get(bstack111l1ll_opy_ (u"࠭ࡓ࡚ࡕࡗࡉࡒࡥࡔࡆࡃࡐࡔࡗࡕࡊࡆࡅࡗࠫ᯸")), env.get(bstack111l1ll_opy_ (u"ࠧࡃࡗࡌࡐࡉࡥࡂࡖࡋࡏࡈࡎࡊࠧ᯹"))),
            bstack111l1ll_opy_ (u"ࠣ࡬ࡲࡦࡤࡴࡡ࡮ࡧࠥ᯺"): env.get(bstack111l1ll_opy_ (u"ࠤࡅ࡙ࡎࡒࡄࡠࡄࡘࡍࡑࡊࡉࡅࠤ᯻")),
            bstack111l1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡱࡹࡲࡨࡥࡳࠤ᯼"): env.get(bstack111l1ll_opy_ (u"ࠦࡇ࡛ࡉࡍࡆࡢࡆ࡚ࡏࡌࡅࡋࡇࠦ᯽"))
        }
    if any([env.get(bstack111l1ll_opy_ (u"ࠧࡉࡏࡅࡇࡅ࡙ࡎࡒࡄࡠࡄࡘࡍࡑࡊ࡟ࡊࡆࠥ᯾")), env.get(bstack111l1ll_opy_ (u"ࠨࡃࡐࡆࡈࡆ࡚ࡏࡌࡅࡡࡕࡉࡘࡕࡌࡗࡇࡇࡣࡘࡕࡕࡓࡅࡈࡣ࡛ࡋࡒࡔࡋࡒࡒࠧ᯿")), env.get(bstack111l1ll_opy_ (u"ࠢࡄࡑࡇࡉࡇ࡛ࡉࡍࡆࡢࡗࡔ࡛ࡒࡄࡇࡢ࡚ࡊࡘࡓࡊࡑࡑࠦᰀ"))]):
        return {
            bstack111l1ll_opy_ (u"ࠣࡰࡤࡱࡪࠨᰁ"): bstack111l1ll_opy_ (u"ࠤࡄ࡛ࡘࠦࡃࡰࡦࡨࡆࡺ࡯࡬ࡥࠤᰂ"),
            bstack111l1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡸࡶࡱࠨᰃ"): env.get(bstack111l1ll_opy_ (u"ࠦࡈࡕࡄࡆࡄࡘࡍࡑࡊ࡟ࡑࡗࡅࡐࡎࡉ࡟ࡃࡗࡌࡐࡉࡥࡕࡓࡎࠥᰄ")),
            bstack111l1ll_opy_ (u"ࠧࡰ࡯ࡣࡡࡱࡥࡲ࡫ࠢᰅ"): env.get(bstack111l1ll_opy_ (u"ࠨࡃࡐࡆࡈࡆ࡚ࡏࡌࡅࡡࡅ࡙ࡎࡒࡄࡠࡋࡇࠦᰆ")),
            bstack111l1ll_opy_ (u"ࠢࡣࡷ࡬ࡰࡩࡥ࡮ࡶ࡯ࡥࡩࡷࠨᰇ"): env.get(bstack111l1ll_opy_ (u"ࠣࡅࡒࡈࡊࡈࡕࡊࡎࡇࡣࡇ࡛ࡉࡍࡆࡢࡍࡉࠨᰈ"))
        }
    if env.get(bstack111l1ll_opy_ (u"ࠤࡥࡥࡲࡨ࡯ࡰࡡࡥࡹ࡮ࡲࡤࡏࡷࡰࡦࡪࡸࠢᰉ")):
        return {
            bstack111l1ll_opy_ (u"ࠥࡲࡦࡳࡥࠣᰊ"): bstack111l1ll_opy_ (u"ࠦࡇࡧ࡭ࡣࡱࡲࠦᰋ"),
            bstack111l1ll_opy_ (u"ࠧࡨࡵࡪ࡮ࡧࡣࡺࡸ࡬ࠣᰌ"): env.get(bstack111l1ll_opy_ (u"ࠨࡢࡢ࡯ࡥࡳࡴࡥࡢࡶ࡫࡯ࡨࡗ࡫ࡳࡶ࡮ࡷࡷ࡚ࡸ࡬ࠣᰍ")),
            bstack111l1ll_opy_ (u"ࠢ࡫ࡱࡥࡣࡳࡧ࡭ࡦࠤᰎ"): env.get(bstack111l1ll_opy_ (u"ࠣࡤࡤࡱࡧࡵ࡯ࡠࡵ࡫ࡳࡷࡺࡊࡰࡤࡑࡥࡲ࡫ࠢᰏ")),
            bstack111l1ll_opy_ (u"ࠤࡥࡹ࡮ࡲࡤࡠࡰࡸࡱࡧ࡫ࡲࠣᰐ"): env.get(bstack111l1ll_opy_ (u"ࠥࡦࡦࡳࡢࡰࡱࡢࡦࡺ࡯࡬ࡥࡐࡸࡱࡧ࡫ࡲࠣᰑ"))
        }
    if env.get(bstack111l1ll_opy_ (u"ࠦ࡜ࡋࡒࡄࡍࡈࡖࠧᰒ")) or env.get(bstack111l1ll_opy_ (u"ࠧ࡝ࡅࡓࡅࡎࡉࡗࡥࡍࡂࡋࡑࡣࡕࡏࡐࡆࡎࡌࡒࡊࡥࡓࡕࡃࡕࡘࡊࡊࠢᰓ")):
        return {
            bstack111l1ll_opy_ (u"ࠨ࡮ࡢ࡯ࡨࠦᰔ"): bstack111l1ll_opy_ (u"ࠢࡘࡧࡵࡧࡰ࡫ࡲࠣᰕ"),
            bstack111l1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪ࡟ࡶࡴ࡯ࠦᰖ"): env.get(bstack111l1ll_opy_ (u"ࠤ࡚ࡉࡗࡉࡋࡆࡔࡢࡆ࡚ࡏࡌࡅࡡࡘࡖࡑࠨᰗ")),
            bstack111l1ll_opy_ (u"ࠥ࡮ࡴࡨ࡟࡯ࡣࡰࡩࠧᰘ"): bstack111l1ll_opy_ (u"ࠦࡒࡧࡩ࡯ࠢࡓ࡭ࡵ࡫࡬ࡪࡰࡨࠦᰙ") if env.get(bstack111l1ll_opy_ (u"ࠧ࡝ࡅࡓࡅࡎࡉࡗࡥࡍࡂࡋࡑࡣࡕࡏࡐࡆࡎࡌࡒࡊࡥࡓࡕࡃࡕࡘࡊࡊࠢᰚ")) else None,
            bstack111l1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡴࡵ࡮ࡤࡨࡶࠧᰛ"): env.get(bstack111l1ll_opy_ (u"ࠢࡘࡇࡕࡇࡐࡋࡒࡠࡉࡌࡘࡤࡉࡏࡎࡏࡌࡘࠧᰜ"))
        }
    if any([env.get(bstack111l1ll_opy_ (u"ࠣࡉࡆࡔࡤࡖࡒࡐࡌࡈࡇ࡙ࠨᰝ")), env.get(bstack111l1ll_opy_ (u"ࠤࡊࡇࡑࡕࡕࡅࡡࡓࡖࡔࡐࡅࡄࡖࠥᰞ")), env.get(bstack111l1ll_opy_ (u"ࠥࡋࡔࡕࡇࡍࡇࡢࡇࡑࡕࡕࡅࡡࡓࡖࡔࡐࡅࡄࡖࠥᰟ"))]):
        return {
            bstack111l1ll_opy_ (u"ࠦࡳࡧ࡭ࡦࠤᰠ"): bstack111l1ll_opy_ (u"ࠧࡍ࡯ࡰࡩ࡯ࡩࠥࡉ࡬ࡰࡷࡧࠦᰡ"),
            bstack111l1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡻࡲ࡭ࠤᰢ"): None,
            bstack111l1ll_opy_ (u"ࠢ࡫ࡱࡥࡣࡳࡧ࡭ࡦࠤᰣ"): env.get(bstack111l1ll_opy_ (u"ࠣࡒࡕࡓࡏࡋࡃࡕࡡࡌࡈࠧᰤ")),
            bstack111l1ll_opy_ (u"ࠤࡥࡹ࡮ࡲࡤࡠࡰࡸࡱࡧ࡫ࡲࠣᰥ"): env.get(bstack111l1ll_opy_ (u"ࠥࡆ࡚ࡏࡌࡅࡡࡌࡈࠧᰦ"))
        }
    if env.get(bstack111l1ll_opy_ (u"ࠦࡘࡎࡉࡑࡒࡄࡆࡑࡋࠢᰧ")):
        return {
            bstack111l1ll_opy_ (u"ࠧࡴࡡ࡮ࡧࠥᰨ"): bstack111l1ll_opy_ (u"ࠨࡓࡩ࡫ࡳࡴࡦࡨ࡬ࡦࠤᰩ"),
            bstack111l1ll_opy_ (u"ࠢࡣࡷ࡬ࡰࡩࡥࡵࡳ࡮ࠥᰪ"): env.get(bstack111l1ll_opy_ (u"ࠣࡕࡋࡍࡕࡖࡁࡃࡎࡈࡣࡇ࡛ࡉࡍࡆࡢ࡙ࡗࡒࠢᰫ")),
            bstack111l1ll_opy_ (u"ࠤ࡭ࡳࡧࡥ࡮ࡢ࡯ࡨࠦᰬ"): bstack111l1ll_opy_ (u"ࠥࡎࡴࡨࠠࠤࡽࢀࠦᰭ").format(env.get(bstack111l1ll_opy_ (u"ࠫࡘࡎࡉࡑࡒࡄࡆࡑࡋ࡟ࡋࡑࡅࡣࡎࡊࠧᰮ"))) if env.get(bstack111l1ll_opy_ (u"࡙ࠧࡈࡊࡒࡓࡅࡇࡒࡅࡠࡌࡒࡆࡤࡏࡄࠣᰯ")) else None,
            bstack111l1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡴࡵ࡮ࡤࡨࡶࠧᰰ"): env.get(bstack111l1ll_opy_ (u"ࠢࡔࡊࡌࡔࡕࡇࡂࡍࡇࡢࡆ࡚ࡏࡌࡅࡡࡑ࡙ࡒࡈࡅࡓࠤᰱ"))
        }
    if bstack1l1l11l1ll_opy_(env.get(bstack111l1ll_opy_ (u"ࠣࡐࡈࡘࡑࡏࡆ࡚ࠤᰲ"))):
        return {
            bstack111l1ll_opy_ (u"ࠤࡱࡥࡲ࡫ࠢᰳ"): bstack111l1ll_opy_ (u"ࠥࡒࡪࡺ࡬ࡪࡨࡼࠦᰴ"),
            bstack111l1ll_opy_ (u"ࠦࡧࡻࡩ࡭ࡦࡢࡹࡷࡲࠢᰵ"): env.get(bstack111l1ll_opy_ (u"ࠧࡊࡅࡑࡎࡒ࡝ࡤ࡛ࡒࡍࠤᰶ")),
            bstack111l1ll_opy_ (u"ࠨࡪࡰࡤࡢࡲࡦࡳࡥ᰷ࠣ"): env.get(bstack111l1ll_opy_ (u"ࠢࡔࡋࡗࡉࡤࡔࡁࡎࡇࠥ᰸")),
            bstack111l1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪ࡟࡯ࡷࡰࡦࡪࡸࠢ᰹"): env.get(bstack111l1ll_opy_ (u"ࠤࡅ࡙ࡎࡒࡄࡠࡋࡇࠦ᰺"))
        }
    if bstack1l1l11l1ll_opy_(env.get(bstack111l1ll_opy_ (u"ࠥࡋࡎ࡚ࡈࡖࡄࡢࡅࡈ࡚ࡉࡐࡐࡖࠦ᰻"))):
        return {
            bstack111l1ll_opy_ (u"ࠦࡳࡧ࡭ࡦࠤ᰼"): bstack111l1ll_opy_ (u"ࠧࡍࡩࡵࡊࡸࡦࠥࡇࡣࡵ࡫ࡲࡲࡸࠨ᰽"),
            bstack111l1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡻࡲ࡭ࠤ᰾"): bstack111l1ll_opy_ (u"ࠢࡼࡿ࠲ࡿࢂ࠵ࡡࡤࡶ࡬ࡳࡳࡹ࠯ࡳࡷࡱࡷ࠴ࢁࡽࠣ᰿").format(env.get(bstack111l1ll_opy_ (u"ࠨࡉࡌࡘࡍ࡛ࡂࡠࡕࡈࡖ࡛ࡋࡒࡠࡗࡕࡐࠬ᱀")), env.get(bstack111l1ll_opy_ (u"ࠩࡊࡍ࡙ࡎࡕࡃࡡࡕࡉࡕࡕࡓࡊࡖࡒࡖ࡞࠭᱁")), env.get(bstack111l1ll_opy_ (u"ࠪࡋࡎ࡚ࡈࡖࡄࡢࡖ࡚ࡔ࡟ࡊࡆࠪ᱂"))),
            bstack111l1ll_opy_ (u"ࠦ࡯ࡵࡢࡠࡰࡤࡱࡪࠨ᱃"): env.get(bstack111l1ll_opy_ (u"ࠧࡍࡉࡕࡊࡘࡆࡤ࡝ࡏࡓࡍࡉࡐࡔ࡝ࠢ᱄")),
            bstack111l1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡴࡵ࡮ࡤࡨࡶࠧ᱅"): env.get(bstack111l1ll_opy_ (u"ࠢࡈࡋࡗࡌ࡚ࡈ࡟ࡓࡗࡑࡣࡎࡊࠢ᱆"))
        }
    if env.get(bstack111l1ll_opy_ (u"ࠣࡅࡌࠦ᱇")) == bstack111l1ll_opy_ (u"ࠤࡷࡶࡺ࡫ࠢ᱈") and env.get(bstack111l1ll_opy_ (u"࡚ࠥࡊࡘࡃࡆࡎࠥ᱉")) == bstack111l1ll_opy_ (u"ࠦ࠶ࠨ᱊"):
        return {
            bstack111l1ll_opy_ (u"ࠧࡴࡡ࡮ࡧࠥ᱋"): bstack111l1ll_opy_ (u"ࠨࡖࡦࡴࡦࡩࡱࠨ᱌"),
            bstack111l1ll_opy_ (u"ࠢࡣࡷ࡬ࡰࡩࡥࡵࡳ࡮ࠥᱍ"): bstack111l1ll_opy_ (u"ࠣࡪࡷࡸࡵࡀ࠯࠰ࡽࢀࠦᱎ").format(env.get(bstack111l1ll_opy_ (u"࡙ࠩࡉࡗࡉࡅࡍࡡࡘࡖࡑ࠭ᱏ"))),
            bstack111l1ll_opy_ (u"ࠥ࡮ࡴࡨ࡟࡯ࡣࡰࡩࠧ᱐"): None,
            bstack111l1ll_opy_ (u"ࠦࡧࡻࡩ࡭ࡦࡢࡲࡺࡳࡢࡦࡴࠥ᱑"): None,
        }
    if env.get(bstack111l1ll_opy_ (u"࡚ࠧࡅࡂࡏࡆࡍ࡙࡟࡟ࡗࡇࡕࡗࡎࡕࡎࠣ᱒")):
        return {
            bstack111l1ll_opy_ (u"ࠨ࡮ࡢ࡯ࡨࠦ᱓"): bstack111l1ll_opy_ (u"ࠢࡕࡧࡤࡱࡨ࡯ࡴࡺࠤ᱔"),
            bstack111l1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪ࡟ࡶࡴ࡯ࠦ᱕"): None,
            bstack111l1ll_opy_ (u"ࠤ࡭ࡳࡧࡥ࡮ࡢ࡯ࡨࠦ᱖"): env.get(bstack111l1ll_opy_ (u"ࠥࡘࡊࡇࡍࡄࡋࡗ࡝ࡤࡖࡒࡐࡌࡈࡇ࡙ࡥࡎࡂࡏࡈࠦ᱗")),
            bstack111l1ll_opy_ (u"ࠦࡧࡻࡩ࡭ࡦࡢࡲࡺࡳࡢࡦࡴࠥ᱘"): env.get(bstack111l1ll_opy_ (u"ࠧࡈࡕࡊࡎࡇࡣࡓ࡛ࡍࡃࡇࡕࠦ᱙"))
        }
    if any([env.get(bstack111l1ll_opy_ (u"ࠨࡃࡐࡐࡆࡓ࡚ࡘࡓࡆࠤᱚ")), env.get(bstack111l1ll_opy_ (u"ࠢࡄࡑࡑࡇࡔ࡛ࡒࡔࡇࡢ࡙ࡗࡒࠢᱛ")), env.get(bstack111l1ll_opy_ (u"ࠣࡅࡒࡒࡈࡕࡕࡓࡕࡈࡣ࡚࡙ࡅࡓࡐࡄࡑࡊࠨᱜ")), env.get(bstack111l1ll_opy_ (u"ࠤࡆࡓࡓࡉࡏࡖࡔࡖࡉࡤ࡚ࡅࡂࡏࠥᱝ"))]):
        return {
            bstack111l1ll_opy_ (u"ࠥࡲࡦࡳࡥࠣᱞ"): bstack111l1ll_opy_ (u"ࠦࡈࡵ࡮ࡤࡱࡸࡶࡸ࡫ࠢᱟ"),
            bstack111l1ll_opy_ (u"ࠧࡨࡵࡪ࡮ࡧࡣࡺࡸ࡬ࠣᱠ"): None,
            bstack111l1ll_opy_ (u"ࠨࡪࡰࡤࡢࡲࡦࡳࡥࠣᱡ"): env.get(bstack111l1ll_opy_ (u"ࠢࡃࡗࡌࡐࡉࡥࡊࡐࡄࡢࡒࡆࡓࡅࠣᱢ")) or None,
            bstack111l1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪ࡟࡯ࡷࡰࡦࡪࡸࠢᱣ"): env.get(bstack111l1ll_opy_ (u"ࠤࡅ࡙ࡎࡒࡄࡠࡋࡇࠦᱤ"), 0)
        }
    if env.get(bstack111l1ll_opy_ (u"ࠥࡋࡔࡥࡊࡐࡄࡢࡒࡆࡓࡅࠣᱥ")):
        return {
            bstack111l1ll_opy_ (u"ࠦࡳࡧ࡭ࡦࠤᱦ"): bstack111l1ll_opy_ (u"ࠧࡍ࡯ࡄࡆࠥᱧ"),
            bstack111l1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡻࡲ࡭ࠤᱨ"): None,
            bstack111l1ll_opy_ (u"ࠢ࡫ࡱࡥࡣࡳࡧ࡭ࡦࠤᱩ"): env.get(bstack111l1ll_opy_ (u"ࠣࡉࡒࡣࡏࡕࡂࡠࡐࡄࡑࡊࠨᱪ")),
            bstack111l1ll_opy_ (u"ࠤࡥࡹ࡮ࡲࡤࡠࡰࡸࡱࡧ࡫ࡲࠣᱫ"): env.get(bstack111l1ll_opy_ (u"ࠥࡋࡔࡥࡐࡊࡒࡈࡐࡎࡔࡅࡠࡅࡒ࡙ࡓ࡚ࡅࡓࠤᱬ"))
        }
    if env.get(bstack111l1ll_opy_ (u"ࠦࡈࡌ࡟ࡃࡗࡌࡐࡉࡥࡉࡅࠤᱭ")):
        return {
            bstack111l1ll_opy_ (u"ࠧࡴࡡ࡮ࡧࠥᱮ"): bstack111l1ll_opy_ (u"ࠨࡃࡰࡦࡨࡊࡷ࡫ࡳࡩࠤᱯ"),
            bstack111l1ll_opy_ (u"ࠢࡣࡷ࡬ࡰࡩࡥࡵࡳ࡮ࠥᱰ"): env.get(bstack111l1ll_opy_ (u"ࠣࡅࡉࡣࡇ࡛ࡉࡍࡆࡢ࡙ࡗࡒࠢᱱ")),
            bstack111l1ll_opy_ (u"ࠤ࡭ࡳࡧࡥ࡮ࡢ࡯ࡨࠦᱲ"): env.get(bstack111l1ll_opy_ (u"ࠥࡇࡋࡥࡐࡊࡒࡈࡐࡎࡔࡅࡠࡐࡄࡑࡊࠨᱳ")),
            bstack111l1ll_opy_ (u"ࠦࡧࡻࡩ࡭ࡦࡢࡲࡺࡳࡢࡦࡴࠥᱴ"): env.get(bstack111l1ll_opy_ (u"ࠧࡉࡆࡠࡄࡘࡍࡑࡊ࡟ࡊࡆࠥᱵ"))
        }
    return {bstack111l1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡴࡵ࡮ࡤࡨࡶࠧᱶ"): None}
def get_host_info():
    return {
        bstack111l1ll_opy_ (u"ࠢࡩࡱࡶࡸࡳࡧ࡭ࡦࠤᱷ"): platform.node(),
        bstack111l1ll_opy_ (u"ࠣࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࠥᱸ"): platform.system(),
        bstack111l1ll_opy_ (u"ࠤࡷࡽࡵ࡫ࠢᱹ"): platform.machine(),
        bstack111l1ll_opy_ (u"ࠥࡺࡪࡸࡳࡪࡱࡱࠦᱺ"): platform.version(),
        bstack111l1ll_opy_ (u"ࠦࡦࡸࡣࡩࠤᱻ"): platform.architecture()[0]
    }
def bstack1l11l1l11_opy_():
    try:
        import selenium
        return True
    except ImportError:
        return False
def bstack11l11l11111_opy_():
    if bstack111ll1ll1_opy_.get_property(bstack111l1ll_opy_ (u"ࠬࡨࡳࡵࡣࡦ࡯ࡤࡹࡥࡴࡵ࡬ࡳࡳ࠭ᱼ")):
        return bstack111l1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࠬᱽ")
    return bstack111l1ll_opy_ (u"ࠧࡶࡰ࡮ࡲࡴࡽ࡮ࡠࡩࡵ࡭ࡩ࠭᱾")
def bstack111llll1ll1_opy_(driver):
    info = {
        bstack111l1ll_opy_ (u"ࠨࡥࡤࡴࡦࡨࡩ࡭࡫ࡷ࡭ࡪࡹࠧ᱿"): driver.capabilities,
        bstack111l1ll_opy_ (u"ࠩࡶࡩࡸࡹࡩࡰࡰࡢ࡭ࡩ࠭ᲀ"): driver.session_id,
        bstack111l1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࠫᲁ"): driver.capabilities.get(bstack111l1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡓࡧ࡭ࡦࠩᲂ"), None),
        bstack111l1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡥࡶࡦࡴࡶ࡭ࡴࡴࠧᲃ"): driver.capabilities.get(bstack111l1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡖࡦࡴࡶ࡭ࡴࡴࠧᲄ"), None),
        bstack111l1ll_opy_ (u"ࠧࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࠩᲅ"): driver.capabilities.get(bstack111l1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡑࡥࡲ࡫ࠧᲆ"), None),
        bstack111l1ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰࡣࡻ࡫ࡲࡴ࡫ࡲࡲࠬᲇ"):driver.capabilities.get(bstack111l1ll_opy_ (u"ࠪࡴࡱࡧࡴࡧࡱࡵࡱ࡛࡫ࡲࡴ࡫ࡲࡲࠬᲈ"), None),
    }
    if bstack11l11l11111_opy_() == bstack111l1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࠪᲉ"):
        if bstack111ll11l1_opy_():
            info[bstack111l1ll_opy_ (u"ࠬࡶࡲࡰࡦࡸࡧࡹ࠭ᲊ")] = bstack111l1ll_opy_ (u"࠭ࡡࡱࡲ࠰ࡥࡺࡺ࡯࡮ࡣࡷࡩࠬ᲋")
        elif driver.capabilities.get(bstack111l1ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱ࠺ࡰࡲࡷ࡭ࡴࡴࡳࠨ᲌"), {}).get(bstack111l1ll_opy_ (u"ࠨࡶࡸࡶࡧࡵࡳࡤࡣ࡯ࡩࠬ᲍"), False):
            info[bstack111l1ll_opy_ (u"ࠩࡳࡶࡴࡪࡵࡤࡶࠪ᲎")] = bstack111l1ll_opy_ (u"ࠪࡸࡺࡸࡢࡰࡵࡦࡥࡱ࡫ࠧ᲏")
        else:
            info[bstack111l1ll_opy_ (u"ࠫࡵࡸ࡯ࡥࡷࡦࡸࠬᲐ")] = bstack111l1ll_opy_ (u"ࠬࡧࡵࡵࡱࡰࡥࡹ࡫ࠧᲑ")
    return info
def bstack111ll11l1_opy_():
    if bstack111ll1ll1_opy_.get_property(bstack111l1ll_opy_ (u"࠭ࡡࡱࡲࡢࡥࡺࡺ࡯࡮ࡣࡷࡩࠬᲒ")):
        return True
    if bstack1l1l11l1ll_opy_(os.environ.get(bstack111l1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡉࡔࡡࡄࡔࡕࡥࡁࡖࡖࡒࡑࡆ࡚ࡅࠨᲓ"), None)):
        return True
    return False
def bstack11111lll1_opy_(bstack111lllll1ll_opy_, url, data, config):
    headers = config.get(bstack111l1ll_opy_ (u"ࠨࡪࡨࡥࡩ࡫ࡲࡴࠩᲔ"), None)
    proxies = bstack1ll1l111l_opy_(config, url)
    auth = config.get(bstack111l1ll_opy_ (u"ࠩࡤࡹࡹ࡮ࠧᲕ"), None)
    response = requests.request(
            bstack111lllll1ll_opy_,
            url=url,
            headers=headers,
            auth=auth,
            json=data,
            proxies=proxies
        )
    return response
def bstack1lll111l1_opy_(bstack111llll11_opy_, size):
    bstack1l1l11lll_opy_ = []
    while len(bstack111llll11_opy_) > size:
        bstack1llll11ll_opy_ = bstack111llll11_opy_[:size]
        bstack1l1l11lll_opy_.append(bstack1llll11ll_opy_)
        bstack111llll11_opy_ = bstack111llll11_opy_[size:]
    bstack1l1l11lll_opy_.append(bstack111llll11_opy_)
    return bstack1l1l11lll_opy_
def bstack111lll111l1_opy_(message, bstack11l11111ll1_opy_=False):
    os.write(1, bytes(message, bstack111l1ll_opy_ (u"ࠪࡹࡹ࡬࠭࠹ࠩᲖ")))
    os.write(1, bytes(bstack111l1ll_opy_ (u"ࠫࡡࡴࠧᲗ"), bstack111l1ll_opy_ (u"ࠬࡻࡴࡧ࠯࠻ࠫᲘ")))
    if bstack11l11111ll1_opy_:
        with open(bstack111l1ll_opy_ (u"࠭ࡢࡴࡶࡤࡧࡰ࠳࡯࠲࠳ࡼ࠱ࠬᲙ") + os.environ[bstack111l1ll_opy_ (u"ࠧࡃࡕࡢࡘࡊ࡙ࡔࡐࡒࡖࡣࡇ࡛ࡉࡍࡆࡢࡌࡆ࡙ࡈࡆࡆࡢࡍࡉ࠭Ლ")] + bstack111l1ll_opy_ (u"ࠨ࠰࡯ࡳ࡬࠭Მ"), bstack111l1ll_opy_ (u"ࠩࡤࠫᲜ")) as f:
            f.write(message + bstack111l1ll_opy_ (u"ࠪࡠࡳ࠭Ო"))
def bstack1l1l1ll11ll_opy_():
    return os.environ[bstack111l1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡅ࡚࡚ࡏࡎࡃࡗࡍࡔࡔࠧᲞ")].lower() == bstack111l1ll_opy_ (u"ࠬࡺࡲࡶࡧࠪᲟ")
def bstack11l1llll11_opy_():
    return bstack111l1l11l1_opy_().replace(tzinfo=None).isoformat() + bstack111l1ll_opy_ (u"࡚࠭ࠨᲠ")
def bstack11l11l1ll11_opy_(start, finish):
    return (datetime.datetime.fromisoformat(finish.rstrip(bstack111l1ll_opy_ (u"࡛ࠧࠩᲡ"))) - datetime.datetime.fromisoformat(start.rstrip(bstack111l1ll_opy_ (u"ࠨ࡜ࠪᲢ")))).total_seconds() * 1000
def bstack11l11l111ll_opy_(timestamp):
    return bstack111llllll1l_opy_(timestamp).isoformat() + bstack111l1ll_opy_ (u"ࠩ࡝ࠫᲣ")
def bstack111ll11l1ll_opy_(bstack11l11111lll_opy_):
    date_format = bstack111l1ll_opy_ (u"ࠪࠩ࡞ࠫ࡭ࠦࡦࠣࠩࡍࡀࠥࡎ࠼ࠨࡗ࠳ࠫࡦࠨᲤ")
    bstack111llllllll_opy_ = datetime.datetime.strptime(bstack11l11111lll_opy_, date_format)
    return bstack111llllllll_opy_.isoformat() + bstack111l1ll_opy_ (u"ࠫ࡟࠭Ქ")
def bstack11l111lll1l_opy_(outcome):
    _, exception, _ = outcome.excinfo or (None, None, None)
    if exception:
        return bstack111l1ll_opy_ (u"ࠬ࡬ࡡࡪ࡮ࡨࡨࠬᲦ")
    else:
        return bstack111l1ll_opy_ (u"࠭ࡰࡢࡵࡶࡩࡩ࠭Ყ")
def bstack1l1l11l1ll_opy_(val):
    if val is None:
        return False
    return val.__str__().lower() == bstack111l1ll_opy_ (u"ࠧࡵࡴࡸࡩࠬᲨ")
def bstack111ll1l1111_opy_(val):
    return val.__str__().lower() == bstack111l1ll_opy_ (u"ࠨࡨࡤࡰࡸ࡫ࠧᲩ")
def error_handler(bstack11l111ll111_opy_=Exception, class_method=False, default_value=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except bstack11l111ll111_opy_ as e:
                print(bstack111l1ll_opy_ (u"ࠤࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥ࡯࡮ࠡࡨࡸࡲࡨࡺࡩࡰࡰࠣࡿࢂࠦ࠭࠿ࠢࡾࢁ࠿ࠦࡻࡾࠤᲪ").format(func.__name__, bstack11l111ll111_opy_.__name__, str(e)))
                return default_value
        return wrapper
    def bstack11l1111l11l_opy_(bstack111llll111l_opy_):
        def wrapped(cls, *args, **kwargs):
            try:
                return bstack111llll111l_opy_(cls, *args, **kwargs)
            except bstack11l111ll111_opy_ as e:
                print(bstack111l1ll_opy_ (u"ࠥࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡩ࡯ࠢࡩࡹࡳࡩࡴࡪࡱࡱࠤࢀࢃࠠ࠮ࡀࠣࡿࢂࡀࠠࡼࡿࠥᲫ").format(bstack111llll111l_opy_.__name__, bstack11l111ll111_opy_.__name__, str(e)))
                return default_value
        return wrapped
    if class_method:
        return bstack11l1111l11l_opy_
    else:
        return decorator
def bstack11lll1l11l_opy_(bstack1111l1l111_opy_):
    if os.getenv(bstack111l1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡅ࡚࡚ࡏࡎࡃࡗࡍࡔࡔࠧᲬ")) is not None:
        return bstack1l1l11l1ll_opy_(os.getenv(bstack111l1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡆ࡛ࡔࡐࡏࡄࡘࡎࡕࡎࠨᲭ")))
    if bstack111l1ll_opy_ (u"࠭ࡡࡶࡶࡲࡱࡦࡺࡩࡰࡰࠪᲮ") in bstack1111l1l111_opy_ and bstack111ll1l1111_opy_(bstack1111l1l111_opy_[bstack111l1ll_opy_ (u"ࠧࡢࡷࡷࡳࡲࡧࡴࡪࡱࡱࠫᲯ")]):
        return False
    if bstack111l1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࡁࡶࡶࡲࡱࡦࡺࡩࡰࡰࠪᲰ") in bstack1111l1l111_opy_ and bstack111ll1l1111_opy_(bstack1111l1l111_opy_[bstack111l1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡂࡷࡷࡳࡲࡧࡴࡪࡱࡱࠫᲱ")]):
        return False
    return True
def bstack11l1111l1l_opy_():
    try:
        from pytest_bdd import reporting
        bstack111ll11llll_opy_ = os.environ.get(bstack111l1ll_opy_ (u"ࠥࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡘࡗࡊࡘ࡟ࡇࡔࡄࡑࡊ࡝ࡏࡓࡍࠥᲲ"), None)
        return bstack111ll11llll_opy_ is None or bstack111ll11llll_opy_ == bstack111l1ll_opy_ (u"ࠦࡵࡿࡴࡦࡵࡷ࠱ࡧࡪࡤࠣᲳ")
    except Exception as e:
        return False
def bstack1ll1111l_opy_(hub_url, CONFIG):
    if bstack1l1111lll_opy_() <= version.parse(bstack111l1ll_opy_ (u"ࠬ࠹࠮࠲࠵࠱࠴ࠬᲴ")):
        if hub_url:
            return bstack111l1ll_opy_ (u"ࠨࡨࡵࡶࡳ࠾࠴࠵ࠢᲵ") + hub_url + bstack111l1ll_opy_ (u"ࠢ࠻࠺࠳࠳ࡼࡪ࠯ࡩࡷࡥࠦᲶ")
        return bstack1lll1lll1l_opy_
    if hub_url:
        return bstack111l1ll_opy_ (u"ࠣࡪࡷࡸࡵࡹ࠺࠰࠱ࠥᲷ") + hub_url + bstack111l1ll_opy_ (u"ࠤ࠲ࡻࡩ࠵ࡨࡶࡤࠥᲸ")
    return bstack1llll1l1l_opy_
def bstack111ll11lll1_opy_():
    return isinstance(os.getenv(bstack111l1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡓ࡝࡙ࡋࡓࡕࡡࡓࡐ࡚ࡍࡉࡏࠩᲹ")), str)
def bstack11l11l1l11_opy_(url):
    return urlparse(url).hostname
def bstack1llll1l1ll_opy_(hostname):
    for bstack1l1l11111_opy_ in bstack1l11l111ll_opy_:
        regex = re.compile(bstack1l1l11111_opy_)
        if regex.match(hostname):
            return True
    return False
def bstack11l111l1l11_opy_(bstack111lll111ll_opy_, file_name, logger):
    bstack11l1ll1111_opy_ = os.path.join(os.path.expanduser(bstack111l1ll_opy_ (u"ࠫࢃ࠭Ჺ")), bstack111lll111ll_opy_)
    try:
        if not os.path.exists(bstack11l1ll1111_opy_):
            os.makedirs(bstack11l1ll1111_opy_)
        file_path = os.path.join(os.path.expanduser(bstack111l1ll_opy_ (u"ࠬࢄࠧ᲻")), bstack111lll111ll_opy_, file_name)
        if not os.path.isfile(file_path):
            with open(file_path, bstack111l1ll_opy_ (u"࠭ࡷࠨ᲼")):
                pass
            with open(file_path, bstack111l1ll_opy_ (u"ࠢࡸ࠭ࠥᲽ")) as outfile:
                json.dump({}, outfile)
        return file_path
    except Exception as e:
        logger.debug(bstack11lll11l1l_opy_.format(str(e)))
def bstack11l111l11ll_opy_(file_name, key, value, logger):
    file_path = bstack11l111l1l11_opy_(bstack111l1ll_opy_ (u"ࠨ࠰ࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࠨᲾ"), file_name, logger)
    if file_path != None:
        if os.path.exists(file_path):
            bstack1lllllll11_opy_ = json.load(open(file_path, bstack111l1ll_opy_ (u"ࠩࡵࡦࠬᲿ")))
        else:
            bstack1lllllll11_opy_ = {}
        bstack1lllllll11_opy_[key] = value
        with open(file_path, bstack111l1ll_opy_ (u"ࠥࡻ࠰ࠨ᳀")) as outfile:
            json.dump(bstack1lllllll11_opy_, outfile)
def bstack1l11l11l1_opy_(file_name, logger):
    file_path = bstack11l111l1l11_opy_(bstack111l1ll_opy_ (u"ࠫ࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࠫ᳁"), file_name, logger)
    bstack1lllllll11_opy_ = {}
    if file_path != None and os.path.exists(file_path):
        with open(file_path, bstack111l1ll_opy_ (u"ࠬࡸࠧ᳂")) as bstack1lll1l1ll1_opy_:
            bstack1lllllll11_opy_ = json.load(bstack1lll1l1ll1_opy_)
    return bstack1lllllll11_opy_
def bstack1lll11lll_opy_(file_path, logger):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.debug(bstack111l1ll_opy_ (u"࠭ࡅࡳࡴࡲࡶࠥ࡯࡮ࠡࡦࡨࡰࡪࡺࡩ࡯ࡩࠣࡪ࡮ࡲࡥ࠻ࠢࠪ᳃") + file_path + bstack111l1ll_opy_ (u"ࠧࠡࠩ᳄") + str(e))
def bstack1l1111lll_opy_():
    from selenium import webdriver
    return version.parse(webdriver.__version__)
class Notset:
    def __repr__(self):
        return bstack111l1ll_opy_ (u"ࠣ࠾ࡑࡓ࡙࡙ࡅࡕࡀࠥ᳅")
def bstack1lll1lllll_opy_(config):
    if bstack111l1ll_opy_ (u"ࠩ࡬ࡷࡕࡲࡡࡺࡹࡵ࡭࡬࡮ࡴࠨ᳆") in config:
        del (config[bstack111l1ll_opy_ (u"ࠪ࡭ࡸࡖ࡬ࡢࡻࡺࡶ࡮࡭ࡨࡵࠩ᳇")])
        return False
    if bstack1l1111lll_opy_() < version.parse(bstack111l1ll_opy_ (u"ࠫ࠸࠴࠴࠯࠲ࠪ᳈")):
        return False
    if bstack1l1111lll_opy_() >= version.parse(bstack111l1ll_opy_ (u"ࠬ࠺࠮࠲࠰࠸ࠫ᳉")):
        return True
    if bstack111l1ll_opy_ (u"࠭ࡵࡴࡧ࡚࠷ࡈ࠭᳊") in config and config[bstack111l1ll_opy_ (u"ࠧࡶࡵࡨ࡛࠸ࡉࠧ᳋")] is False:
        return False
    else:
        return True
def bstack1l11l1lll1_opy_(args_list, bstack11l111lll11_opy_):
    index = -1
    for value in bstack11l111lll11_opy_:
        try:
            index = args_list.index(value)
            return index
        except Exception as e:
            return index
    return index
def bstack11ll1l1111l_opy_(a, b):
  for k, v in b.items():
    if isinstance(v, dict) and k in a and isinstance(a[k], dict):
        bstack11ll1l1111l_opy_(a[k], v)
    else:
        a[k] = v
class Result:
    def __init__(self, result=None, duration=None, exception=None, bstack111ll1ll11_opy_=None):
        self.result = result
        self.duration = duration
        self.exception = exception
        self.exception_type = type(self.exception).__name__ if exception else None
        self.bstack111ll1ll11_opy_ = bstack111ll1ll11_opy_
    @classmethod
    def passed(cls):
        return Result(result=bstack111l1ll_opy_ (u"ࠨࡲࡤࡷࡸ࡫ࡤࠨ᳌"))
    @classmethod
    def failed(cls, exception=None):
        return Result(result=bstack111l1ll_opy_ (u"ࠩࡩࡥ࡮ࡲࡥࡥࠩ᳍"), exception=exception)
    def bstack1111111ll1_opy_(self):
        if self.result != bstack111l1ll_opy_ (u"ࠪࡪࡦ࡯࡬ࡦࡦࠪ᳎"):
            return None
        if isinstance(self.exception_type, str) and bstack111l1ll_opy_ (u"ࠦࡆࡹࡳࡦࡴࡷ࡭ࡴࡴࠢ᳏") in self.exception_type:
            return bstack111l1ll_opy_ (u"ࠧࡇࡳࡴࡧࡵࡸ࡮ࡵ࡮ࡆࡴࡵࡳࡷࠨ᳐")
        return bstack111l1ll_opy_ (u"ࠨࡕ࡯ࡪࡤࡲࡩࡲࡥࡥࡇࡵࡶࡴࡸࠢ᳑")
    def bstack111lll11lll_opy_(self):
        if self.result != bstack111l1ll_opy_ (u"ࠧࡧࡣ࡬ࡰࡪࡪࠧ᳒"):
            return None
        if self.bstack111ll1ll11_opy_:
            return self.bstack111ll1ll11_opy_
        return bstack111lll1111l_opy_(self.exception)
def bstack111lll1111l_opy_(exc):
    return [traceback.format_exception(exc)]
def bstack11l111lllll_opy_(message):
    if isinstance(message, str):
        return not bool(message and message.strip())
    return True
def bstack1111llll1_opy_(object, key, default_value):
    if not object or not object.__dict__:
        return default_value
    if key in object.__dict__.keys():
        return object.__dict__.get(key)
    return default_value
def bstack11l1111ll_opy_(config, logger):
    try:
        import playwright
        bstack11l11l1l11l_opy_ = playwright.__file__
        bstack11l11ll1l11_opy_ = os.path.split(bstack11l11l1l11l_opy_)
        bstack11l11ll1l1l_opy_ = bstack11l11ll1l11_opy_[0] + bstack111l1ll_opy_ (u"ࠨ࠱ࡧࡶ࡮ࡼࡥࡳ࠱ࡳࡥࡨࡱࡡࡨࡧ࠲ࡰ࡮ࡨ࠯ࡤ࡮࡬࠳ࡨࡲࡩ࠯࡬ࡶࠫ᳓")
        os.environ[bstack111l1ll_opy_ (u"ࠩࡊࡐࡔࡈࡁࡍࡡࡄࡋࡊࡔࡔࡠࡊࡗࡘࡕࡥࡐࡓࡑ࡛࡝᳔ࠬ")] = bstack11l1l1ll11_opy_(config)
        with open(bstack11l11ll1l1l_opy_, bstack111l1ll_opy_ (u"ࠪࡶ᳕ࠬ")) as f:
            bstack1l1ll1l11_opy_ = f.read()
            bstack11l11ll1lll_opy_ = bstack111l1ll_opy_ (u"ࠫ࡬ࡲ࡯ࡣࡣ࡯࠱ࡦ࡭ࡥ࡯ࡶ᳖ࠪ")
            bstack111llll1l11_opy_ = bstack1l1ll1l11_opy_.find(bstack11l11ll1lll_opy_)
            if bstack111llll1l11_opy_ == -1:
              process = subprocess.Popen(bstack111l1ll_opy_ (u"ࠧࡴࡰ࡮ࠢ࡬ࡲࡸࡺࡡ࡭࡮ࠣ࡫ࡱࡵࡢࡢ࡮࠰ࡥ࡬࡫࡮ࡵࠤ᳗"), shell=True, cwd=bstack11l11ll1l11_opy_[0])
              process.wait()
              bstack11l111l1ll1_opy_ = bstack111l1ll_opy_ (u"࠭ࠢࡶࡵࡨࠤࡸࡺࡲࡪࡥࡷࠦࡀ᳘࠭")
              bstack11l111ll1l1_opy_ = bstack111l1ll_opy_ (u"ࠢࠣࠤࠣࡠࠧࡻࡳࡦࠢࡶࡸࡷ࡯ࡣࡵ࡞ࠥ࠿ࠥࡩ࡯࡯ࡵࡷࠤࢀࠦࡢࡰࡱࡷࡷࡹࡸࡡࡱࠢࢀࠤࡂࠦࡲࡦࡳࡸ࡭ࡷ࡫ࠨࠨࡩ࡯ࡳࡧࡧ࡬࠮ࡣࡪࡩࡳࡺࠧࠪ࠽ࠣ࡭࡫ࠦࠨࡱࡴࡲࡧࡪࡹࡳ࠯ࡧࡱࡺ࠳ࡍࡌࡐࡄࡄࡐࡤࡇࡇࡆࡐࡗࡣࡍ࡚ࡔࡑࡡࡓࡖࡔ࡞࡙ࠪࠢࡥࡳࡴࡺࡳࡵࡴࡤࡴ࠭࠯࠻ࠡࠤ᳙ࠥࠦ")
              bstack111ll1l1ll1_opy_ = bstack1l1ll1l11_opy_.replace(bstack11l111l1ll1_opy_, bstack11l111ll1l1_opy_)
              with open(bstack11l11ll1l1l_opy_, bstack111l1ll_opy_ (u"ࠨࡹࠪ᳚")) as f:
                f.write(bstack111ll1l1ll1_opy_)
    except Exception as e:
        logger.error(bstack11l1ll11l1_opy_.format(str(e)))
def bstack1l111ll11_opy_():
  try:
    bstack111lll1l11l_opy_ = os.path.join(tempfile.gettempdir(), bstack111l1ll_opy_ (u"ࠩࡲࡴࡹ࡯࡭ࡢ࡮ࡢ࡬ࡺࡨ࡟ࡶࡴ࡯࠲࡯ࡹ࡯࡯ࠩ᳛"))
    bstack111ll1llll1_opy_ = []
    if os.path.exists(bstack111lll1l11l_opy_):
      with open(bstack111lll1l11l_opy_) as f:
        bstack111ll1llll1_opy_ = json.load(f)
      os.remove(bstack111lll1l11l_opy_)
    return bstack111ll1llll1_opy_
  except:
    pass
  return []
def bstack11l11l11ll_opy_(bstack1l1l1l11l1_opy_):
  try:
    bstack111ll1llll1_opy_ = []
    bstack111lll1l11l_opy_ = os.path.join(tempfile.gettempdir(), bstack111l1ll_opy_ (u"ࠪࡳࡵࡺࡩ࡮ࡣ࡯ࡣ࡭ࡻࡢࡠࡷࡵࡰ࠳ࡰࡳࡰࡰ᳜ࠪ"))
    if os.path.exists(bstack111lll1l11l_opy_):
      with open(bstack111lll1l11l_opy_) as f:
        bstack111ll1llll1_opy_ = json.load(f)
    bstack111ll1llll1_opy_.append(bstack1l1l1l11l1_opy_)
    with open(bstack111lll1l11l_opy_, bstack111l1ll_opy_ (u"ࠫࡼ᳝࠭")) as f:
        json.dump(bstack111ll1llll1_opy_, f)
  except:
    pass
def bstack11l111llll_opy_(logger, bstack11l111l1l1l_opy_ = False):
  try:
    test_name = os.environ.get(bstack111l1ll_opy_ (u"ࠬࡖ࡙ࡕࡇࡖࡘࡤ࡚ࡅࡔࡖࡢࡒࡆࡓࡅࠨ᳞"), bstack111l1ll_opy_ (u"᳟࠭ࠧ"))
    if test_name == bstack111l1ll_opy_ (u"ࠧࠨ᳠"):
        test_name = threading.current_thread().__dict__.get(bstack111l1ll_opy_ (u"ࠨࡲࡼࡸࡪࡹࡴࡃࡦࡧࡣࡹ࡫ࡳࡵࡡࡱࡥࡲ࡫ࠧ᳡"), bstack111l1ll_opy_ (u"᳢ࠩࠪ"))
    bstack11l111l1111_opy_ = bstack111l1ll_opy_ (u"ࠪ࠰᳣ࠥ࠭").join(threading.current_thread().bstackTestErrorMessages)
    if bstack11l111l1l1l_opy_:
        bstack1l1l1ll111_opy_ = os.environ.get(bstack111l1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡔࡑࡇࡔࡇࡑࡕࡑࡤࡏࡎࡅࡇ᳤࡛ࠫ"), bstack111l1ll_opy_ (u"ࠬ࠶᳥ࠧ"))
        bstack11ll1l111l_opy_ = {bstack111l1ll_opy_ (u"࠭࡮ࡢ࡯ࡨ᳦ࠫ"): test_name, bstack111l1ll_opy_ (u"ࠧࡦࡴࡵࡳࡷ᳧࠭"): bstack11l111l1111_opy_, bstack111l1ll_opy_ (u"ࠨ࡫ࡱࡨࡪࡾ᳨ࠧ"): bstack1l1l1ll111_opy_}
        bstack11l11111l11_opy_ = []
        bstack111llll11ll_opy_ = os.path.join(tempfile.gettempdir(), bstack111l1ll_opy_ (u"ࠩࡳࡽࡹ࡫ࡳࡵࡡࡳࡴࡵࡥࡥࡳࡴࡲࡶࡤࡲࡩࡴࡶ࠱࡮ࡸࡵ࡮ࠨᳩ"))
        if os.path.exists(bstack111llll11ll_opy_):
            with open(bstack111llll11ll_opy_) as f:
                bstack11l11111l11_opy_ = json.load(f)
        bstack11l11111l11_opy_.append(bstack11ll1l111l_opy_)
        with open(bstack111llll11ll_opy_, bstack111l1ll_opy_ (u"ࠪࡻࠬᳪ")) as f:
            json.dump(bstack11l11111l11_opy_, f)
    else:
        bstack11ll1l111l_opy_ = {bstack111l1ll_opy_ (u"ࠫࡳࡧ࡭ࡦࠩᳫ"): test_name, bstack111l1ll_opy_ (u"ࠬ࡫ࡲࡳࡱࡵࠫᳬ"): bstack11l111l1111_opy_, bstack111l1ll_opy_ (u"࠭ࡩ࡯ࡦࡨࡼ᳭ࠬ"): str(multiprocessing.current_process().name)}
        if bstack111l1ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱ࡟ࡦࡴࡵࡳࡷࡥ࡬ࡪࡵࡷࠫᳮ") not in multiprocessing.current_process().__dict__.keys():
            multiprocessing.current_process().bstack_error_list = []
        multiprocessing.current_process().bstack_error_list.append(bstack11ll1l111l_opy_)
  except Exception as e:
      logger.warn(bstack111l1ll_opy_ (u"ࠣࡗࡱࡥࡧࡲࡥࠡࡶࡲࠤࡸࡺ࡯ࡳࡧࠣࡴࡾࡺࡥࡴࡶࠣࡪࡺࡴ࡮ࡦ࡮ࠣࡨࡦࡺࡡ࠻ࠢࡾࢁࠧᳯ").format(e))
def bstack111l111ll_opy_(error_message, test_name, index, logger):
  try:
    from filelock import FileLock
  except ImportError:
    logger.debug(bstack111l1ll_opy_ (u"ࠩࡩ࡭ࡱ࡫࡬ࡰࡥ࡮ࠤࡳࡵࡴࠡࡣࡹࡥ࡮ࡲࡡࡣ࡮ࡨ࠰ࠥࡻࡳࡪࡰࡪࠤࡧࡧࡳࡪࡥࠣࡪ࡮ࡲࡥࠡࡱࡳࡩࡷࡧࡴࡪࡱࡱࡷࠬᳰ"))
    try:
      bstack111ll1l11ll_opy_ = []
      bstack11ll1l111l_opy_ = {bstack111l1ll_opy_ (u"ࠪࡲࡦࡳࡥࠨᳱ"): test_name, bstack111l1ll_opy_ (u"ࠫࡪࡸࡲࡰࡴࠪᳲ"): error_message, bstack111l1ll_opy_ (u"ࠬ࡯࡮ࡥࡧࡻࠫᳳ"): index}
      bstack111ll1ll11l_opy_ = os.path.join(tempfile.gettempdir(), bstack111l1ll_opy_ (u"࠭ࡲࡰࡤࡲࡸࡤ࡫ࡲࡳࡱࡵࡣࡱ࡯ࡳࡵ࠰࡭ࡷࡴࡴࠧ᳴"))
      if os.path.exists(bstack111ll1ll11l_opy_):
          with open(bstack111ll1ll11l_opy_) as f:
              bstack111ll1l11ll_opy_ = json.load(f)
      bstack111ll1l11ll_opy_.append(bstack11ll1l111l_opy_)
      with open(bstack111ll1ll11l_opy_, bstack111l1ll_opy_ (u"ࠧࡸࠩᳵ")) as f:
          json.dump(bstack111ll1l11ll_opy_, f)
    except Exception as e:
      logger.warn(bstack111l1ll_opy_ (u"ࠣࡗࡱࡥࡧࡲࡥࠡࡶࡲࠤࡸࡺ࡯ࡳࡧࠣࡶࡴࡨ࡯ࡵࠢࡩࡹࡳࡴࡥ࡭ࠢࡧࡥࡹࡧ࠺ࠡࡽࢀࠦᳶ").format(e))
    return
  bstack111ll1l11ll_opy_ = []
  bstack11ll1l111l_opy_ = {bstack111l1ll_opy_ (u"ࠩࡱࡥࡲ࡫ࠧ᳷"): test_name, bstack111l1ll_opy_ (u"ࠪࡩࡷࡸ࡯ࡳࠩ᳸"): error_message, bstack111l1ll_opy_ (u"ࠫ࡮ࡴࡤࡦࡺࠪ᳹"): index}
  bstack111ll1ll11l_opy_ = os.path.join(tempfile.gettempdir(), bstack111l1ll_opy_ (u"ࠬࡸ࡯ࡣࡱࡷࡣࡪࡸࡲࡰࡴࡢࡰ࡮ࡹࡴ࠯࡬ࡶࡳࡳ࠭ᳺ"))
  lock_file = bstack111ll1ll11l_opy_ + bstack111l1ll_opy_ (u"࠭࠮࡭ࡱࡦ࡯ࠬ᳻")
  try:
    with FileLock(lock_file, timeout=10):
      if os.path.exists(bstack111ll1ll11l_opy_):
          with open(bstack111ll1ll11l_opy_, bstack111l1ll_opy_ (u"ࠧࡳࠩ᳼")) as f:
              content = f.read().strip()
              if content:
                  bstack111ll1l11ll_opy_ = json.load(open(bstack111ll1ll11l_opy_))
      bstack111ll1l11ll_opy_.append(bstack11ll1l111l_opy_)
      with open(bstack111ll1ll11l_opy_, bstack111l1ll_opy_ (u"ࠨࡹࠪ᳽")) as f:
          json.dump(bstack111ll1l11ll_opy_, f)
  except Exception as e:
    logger.warn(bstack111l1ll_opy_ (u"ࠤࡘࡲࡦࡨ࡬ࡦࠢࡷࡳࠥࡹࡴࡰࡴࡨࠤࡷࡵࡢࡰࡶࠣࡪࡺࡴ࡮ࡦ࡮ࠣࡨࡦࡺࡡࠡࡹ࡬ࡸ࡭ࠦࡦࡪ࡮ࡨࠤࡱࡵࡣ࡬࡫ࡱ࡫࠿ࠦࡻࡾࠤ᳾").format(e))
def bstack1111ll1ll_opy_(bstack1l111lllll_opy_, name, logger):
  try:
    bstack11ll1l111l_opy_ = {bstack111l1ll_opy_ (u"ࠪࡲࡦࡳࡥࠨ᳿"): name, bstack111l1ll_opy_ (u"ࠫࡪࡸࡲࡰࡴࠪᴀ"): bstack1l111lllll_opy_, bstack111l1ll_opy_ (u"ࠬ࡯࡮ࡥࡧࡻࠫᴁ"): str(threading.current_thread()._name)}
    return bstack11ll1l111l_opy_
  except Exception as e:
    logger.warn(bstack111l1ll_opy_ (u"ࠨࡕ࡯ࡣࡥࡰࡪࠦࡴࡰࠢࡶࡸࡴࡸࡥࠡࡤࡨ࡬ࡦࡼࡥࠡࡨࡸࡲࡳ࡫࡬ࠡࡦࡤࡸࡦࡀࠠࡼࡿࠥᴂ").format(e))
  return
def bstack111ll1l11l1_opy_():
    return platform.system() == bstack111l1ll_opy_ (u"ࠧࡘ࡫ࡱࡨࡴࡽࡳࠨᴃ")
def bstack1ll1l1l11l_opy_(bstack111ll1l1l1l_opy_, config, logger):
    bstack11l11l11ll1_opy_ = {}
    try:
        return {key: config[key] for key in config if bstack111ll1l1l1l_opy_.match(key)}
    except Exception as e:
        logger.debug(bstack111l1ll_opy_ (u"ࠣࡗࡱࡥࡧࡲࡥࠡࡶࡲࠤ࡫࡯࡬ࡵࡧࡵࠤࡨࡵ࡮ࡧ࡫ࡪࠤࡰ࡫ࡹࡴࠢࡥࡽࠥࡸࡥࡨࡧࡻࠤࡲࡧࡴࡤࡪ࠽ࠤࢀࢃࠢᴄ").format(e))
    return bstack11l11l11ll1_opy_
def bstack111ll1l1l11_opy_(bstack11l111l11l1_opy_, bstack111llllll11_opy_):
    bstack111lll1ll1l_opy_ = version.parse(bstack11l111l11l1_opy_)
    bstack11l11ll11ll_opy_ = version.parse(bstack111llllll11_opy_)
    if bstack111lll1ll1l_opy_ > bstack11l11ll11ll_opy_:
        return 1
    elif bstack111lll1ll1l_opy_ < bstack11l11ll11ll_opy_:
        return -1
    else:
        return 0
def bstack111l1l11l1_opy_():
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
def bstack111llllll1l_opy_(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).replace(tzinfo=None)
def bstack11l11l1111l_opy_(framework):
    from browserstack_sdk._version import __version__
    return str(framework) + str(__version__)
def bstack1ll11l11l_opy_(options, framework, config, bstack1l11111ll_opy_={}):
    if options is None:
        return
    if getattr(options, bstack111l1ll_opy_ (u"ࠩࡪࡩࡹ࠭ᴅ"), None):
        caps = options
    else:
        caps = options.to_capabilities()
    bstack1l111ll1l_opy_ = caps.get(bstack111l1ll_opy_ (u"ࠪࡦࡸࡺࡡࡤ࡭࠽ࡳࡵࡺࡩࡰࡰࡶࠫᴆ"))
    bstack111ll1ll1ll_opy_ = True
    bstack1l1l1ll11l_opy_ = os.environ[bstack111l1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡘࡊ࡙ࡔࡉࡗࡅࡣ࡚࡛ࡉࡅࠩᴇ")]
    bstack1ll11lllll1_opy_ = config.get(bstack111l1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬᴈ"), False)
    if bstack1ll11lllll1_opy_:
        bstack1lll1lll11l_opy_ = config.get(bstack111l1ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾࡕࡰࡵ࡫ࡲࡲࡸ࠭ᴉ"), {})
        bstack1lll1lll11l_opy_[bstack111l1ll_opy_ (u"ࠧࡢࡷࡷ࡬࡙ࡵ࡫ࡦࡰࠪᴊ")] = os.getenv(bstack111l1ll_opy_ (u"ࠨࡄࡖࡣࡆ࠷࠱࡚ࡡࡍ࡛࡙࠭ᴋ"))
        bstack11ll1lll111_opy_ = json.loads(os.getenv(bstack111l1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡥࡁࡄࡅࡈࡗࡘࡏࡂࡊࡎࡌࡘ࡞ࡥࡃࡐࡐࡉࡍࡌ࡛ࡒࡂࡖࡌࡓࡓࡥ࡙ࡎࡎࠪᴌ"), bstack111l1ll_opy_ (u"ࠪࡿࢂ࠭ᴍ"))).get(bstack111l1ll_opy_ (u"ࠫࡸࡩࡡ࡯ࡰࡨࡶ࡛࡫ࡲࡴ࡫ࡲࡲࠬᴎ"))
    if bstack111ll1l1111_opy_(caps.get(bstack111l1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡺࡹࡥࡘ࠵ࡆࠫᴏ"))) or bstack111ll1l1111_opy_(caps.get(bstack111l1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡻࡳࡦࡡࡺ࠷ࡨ࠭ᴐ"))):
        bstack111ll1ll1ll_opy_ = False
    if bstack1lll1lllll_opy_({bstack111l1ll_opy_ (u"ࠢࡶࡵࡨ࡛࠸ࡉࠢᴑ"): bstack111ll1ll1ll_opy_}):
        bstack1l111ll1l_opy_ = bstack1l111ll1l_opy_ or {}
        bstack1l111ll1l_opy_[bstack111l1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࡓࡅࡍࠪᴒ")] = bstack11l11l1111l_opy_(framework)
        bstack1l111ll1l_opy_[bstack111l1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡂࡷࡷࡳࡲࡧࡴࡪࡱࡱࠫᴓ")] = bstack1l1l1ll11ll_opy_()
        bstack1l111ll1l_opy_[bstack111l1ll_opy_ (u"ࠪࡸࡪࡹࡴࡩࡷࡥࡆࡺ࡯࡬ࡥࡗࡸ࡭ࡩ࠭ᴔ")] = bstack1l1l1ll11l_opy_
        bstack1l111ll1l_opy_[bstack111l1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡓࡶࡴࡪࡵࡤࡶࡐࡥࡵ࠭ᴕ")] = bstack1l11111ll_opy_
        if bstack1ll11lllll1_opy_:
            bstack1l111ll1l_opy_[bstack111l1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬᴖ")] = bstack1ll11lllll1_opy_
            bstack1l111ll1l_opy_[bstack111l1ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾࡕࡰࡵ࡫ࡲࡲࡸ࠭ᴗ")] = bstack1lll1lll11l_opy_
            bstack1l111ll1l_opy_[bstack111l1ll_opy_ (u"ࠧࡢࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࡏࡱࡶ࡬ࡳࡳࡹࠧᴘ")][bstack111l1ll_opy_ (u"ࠨࡵࡦࡥࡳࡴࡥࡳࡘࡨࡶࡸ࡯࡯࡯ࠩᴙ")] = bstack11ll1lll111_opy_
        if getattr(options, bstack111l1ll_opy_ (u"ࠩࡶࡩࡹࡥࡣࡢࡲࡤࡦ࡮ࡲࡩࡵࡻࠪᴚ"), None):
            options.set_capability(bstack111l1ll_opy_ (u"ࠪࡦࡸࡺࡡࡤ࡭࠽ࡳࡵࡺࡩࡰࡰࡶࠫᴛ"), bstack1l111ll1l_opy_)
        else:
            options[bstack111l1ll_opy_ (u"ࠫࡧࡹࡴࡢࡥ࡮࠾ࡴࡶࡴࡪࡱࡱࡷࠬᴜ")] = bstack1l111ll1l_opy_
    else:
        if getattr(options, bstack111l1ll_opy_ (u"ࠬࡹࡥࡵࡡࡦࡥࡵࡧࡢࡪ࡮࡬ࡸࡾ࠭ᴝ"), None):
            options.set_capability(bstack111l1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡗࡉࡑࠧᴞ"), bstack11l11l1111l_opy_(framework))
            options.set_capability(bstack111l1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡆࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࠨᴟ"), bstack1l1l1ll11ll_opy_())
            options.set_capability(bstack111l1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡵࡧࡶࡸ࡭ࡻࡢࡃࡷ࡬ࡰࡩ࡛ࡵࡪࡦࠪᴠ"), bstack1l1l1ll11l_opy_)
            options.set_capability(bstack111l1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡤࡸ࡭ࡱࡪࡐࡳࡱࡧࡹࡨࡺࡍࡢࡲࠪᴡ"), bstack1l11111ll_opy_)
            if bstack1ll11lllll1_opy_:
                options.set_capability(bstack111l1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠩᴢ"), bstack1ll11lllll1_opy_)
                options.set_capability(bstack111l1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࡒࡴࡹ࡯࡯࡯ࡵࠪᴣ"), bstack1lll1lll11l_opy_)
                options.set_capability(bstack111l1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࡓࡵࡺࡩࡰࡰࡶ࠲ࡸࡩࡡ࡯ࡰࡨࡶ࡛࡫ࡲࡴ࡫ࡲࡲࠬᴤ"), bstack11ll1lll111_opy_)
        else:
            options[bstack111l1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡗࡉࡑࠧᴥ")] = bstack11l11l1111l_opy_(framework)
            options[bstack111l1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡆࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࠨᴦ")] = bstack1l1l1ll11ll_opy_()
            options[bstack111l1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡵࡧࡶࡸ࡭ࡻࡢࡃࡷ࡬ࡰࡩ࡛ࡵࡪࡦࠪᴧ")] = bstack1l1l1ll11l_opy_
            options[bstack111l1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡤࡸ࡭ࡱࡪࡐࡳࡱࡧࡹࡨࡺࡍࡢࡲࠪᴨ")] = bstack1l11111ll_opy_
            if bstack1ll11lllll1_opy_:
                options[bstack111l1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠩᴩ")] = bstack1ll11lllll1_opy_
                options[bstack111l1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࡒࡴࡹ࡯࡯࡯ࡵࠪᴪ")] = bstack1lll1lll11l_opy_
                options[bstack111l1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࡓࡵࡺࡩࡰࡰࡶࠫᴫ")][bstack111l1ll_opy_ (u"࠭ࡳࡤࡣࡱࡲࡪࡸࡖࡦࡴࡶ࡭ࡴࡴࠧᴬ")] = bstack11ll1lll111_opy_
    return options
def bstack111lll1l111_opy_(bstack11l1111ll1l_opy_, framework):
    bstack1l11111ll_opy_ = bstack111ll1ll1_opy_.get_property(bstack111l1ll_opy_ (u"ࠢࡑࡎࡄ࡝࡜ࡘࡉࡈࡊࡗࡣࡕࡘࡏࡅࡗࡆࡘࡤࡓࡁࡑࠤᴭ"))
    if bstack11l1111ll1l_opy_ and len(bstack11l1111ll1l_opy_.split(bstack111l1ll_opy_ (u"ࠨࡥࡤࡴࡸࡃࠧᴮ"))) > 1:
        ws_url = bstack11l1111ll1l_opy_.split(bstack111l1ll_opy_ (u"ࠩࡦࡥࡵࡹ࠽ࠨᴯ"))[0]
        if bstack111l1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡦࡳࡲ࠭ᴰ") in ws_url:
            from browserstack_sdk._version import __version__
            bstack111lllllll1_opy_ = json.loads(urllib.parse.unquote(bstack11l1111ll1l_opy_.split(bstack111l1ll_opy_ (u"ࠫࡨࡧࡰࡴ࠿ࠪᴱ"))[1]))
            bstack111lllllll1_opy_ = bstack111lllllll1_opy_ or {}
            bstack1l1l1ll11l_opy_ = os.environ[bstack111l1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡊࡘࡆࡤ࡛ࡕࡊࡆࠪᴲ")]
            bstack111lllllll1_opy_[bstack111l1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡗࡉࡑࠧᴳ")] = str(framework) + str(__version__)
            bstack111lllllll1_opy_[bstack111l1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡆࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࠨᴴ")] = bstack1l1l1ll11ll_opy_()
            bstack111lllllll1_opy_[bstack111l1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡵࡧࡶࡸ࡭ࡻࡢࡃࡷ࡬ࡰࡩ࡛ࡵࡪࡦࠪᴵ")] = bstack1l1l1ll11l_opy_
            bstack111lllllll1_opy_[bstack111l1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡤࡸ࡭ࡱࡪࡐࡳࡱࡧࡹࡨࡺࡍࡢࡲࠪᴶ")] = bstack1l11111ll_opy_
            bstack11l1111ll1l_opy_ = bstack11l1111ll1l_opy_.split(bstack111l1ll_opy_ (u"ࠪࡧࡦࡶࡳ࠾ࠩᴷ"))[0] + bstack111l1ll_opy_ (u"ࠫࡨࡧࡰࡴ࠿ࠪᴸ") + urllib.parse.quote(json.dumps(bstack111lllllll1_opy_))
    return bstack11l1111ll1l_opy_
def bstack1lllll1l1l_opy_():
    global bstack11ll11ll1_opy_
    from playwright._impl._browser_type import BrowserType
    bstack11ll11ll1_opy_ = BrowserType.connect
    return bstack11ll11ll1_opy_
def bstack1l1l1llll1_opy_(framework_name):
    global bstack11l11l1ll_opy_
    bstack11l11l1ll_opy_ = framework_name
    return framework_name
def bstack11lll1ll1l_opy_(self, *args, **kwargs):
    global bstack11ll11ll1_opy_
    try:
        global bstack11l11l1ll_opy_
        if bstack111l1ll_opy_ (u"ࠬࡽࡳࡆࡰࡧࡴࡴ࡯࡮ࡵࠩᴹ") in kwargs:
            kwargs[bstack111l1ll_opy_ (u"࠭ࡷࡴࡇࡱࡨࡵࡵࡩ࡯ࡶࠪᴺ")] = bstack111lll1l111_opy_(
                kwargs.get(bstack111l1ll_opy_ (u"ࠧࡸࡵࡈࡲࡩࡶ࡯ࡪࡰࡷࠫᴻ"), None),
                bstack11l11l1ll_opy_
            )
    except Exception as e:
        logger.error(bstack111l1ll_opy_ (u"ࠣࡇࡵࡶࡴࡸࠠࡸࡪࡨࡲࠥࡶࡲࡰࡥࡨࡷࡸ࡯࡮ࡨࠢࡖࡈࡐࠦࡣࡢࡲࡶ࠾ࠥࢁࡽࠣᴼ").format(str(e)))
    return bstack11ll11ll1_opy_(self, *args, **kwargs)
def bstack111lllll11l_opy_(bstack111ll11l1l1_opy_, proxies):
    proxy_settings = {}
    try:
        if not proxies:
            proxies = bstack1ll1l111l_opy_(bstack111ll11l1l1_opy_, bstack111l1ll_opy_ (u"ࠤࠥᴽ"))
        if proxies and proxies.get(bstack111l1ll_opy_ (u"ࠥ࡬ࡹࡺࡰࡴࠤᴾ")):
            parsed_url = urlparse(proxies.get(bstack111l1ll_opy_ (u"ࠦ࡭ࡺࡴࡱࡵࠥᴿ")))
            if parsed_url and parsed_url.hostname: proxy_settings[bstack111l1ll_opy_ (u"ࠬࡶࡲࡰࡺࡼࡌࡴࡹࡴࠨᵀ")] = str(parsed_url.hostname)
            if parsed_url and parsed_url.port: proxy_settings[bstack111l1ll_opy_ (u"࠭ࡰࡳࡱࡻࡽࡕࡵࡲࡵࠩᵁ")] = str(parsed_url.port)
            if parsed_url and parsed_url.username: proxy_settings[bstack111l1ll_opy_ (u"ࠧࡱࡴࡲࡼࡾ࡛ࡳࡦࡴࠪᵂ")] = str(parsed_url.username)
            if parsed_url and parsed_url.password: proxy_settings[bstack111l1ll_opy_ (u"ࠨࡲࡵࡳࡽࡿࡐࡢࡵࡶࠫᵃ")] = str(parsed_url.password)
        return proxy_settings
    except:
        return proxy_settings
def bstack11l1111l11_opy_(bstack111ll11l1l1_opy_):
    bstack111ll1l1lll_opy_ = {
        bstack11l1l1l11l1_opy_[bstack111lll1lll1_opy_]: bstack111ll11l1l1_opy_[bstack111lll1lll1_opy_]
        for bstack111lll1lll1_opy_ in bstack111ll11l1l1_opy_
        if bstack111lll1lll1_opy_ in bstack11l1l1l11l1_opy_
    }
    bstack111ll1l1lll_opy_[bstack111l1ll_opy_ (u"ࠤࡳࡶࡴࡾࡹࡔࡧࡷࡸ࡮ࡴࡧࡴࠤᵄ")] = bstack111lllll11l_opy_(bstack111ll11l1l1_opy_, bstack111ll1ll1_opy_.get_property(bstack111l1ll_opy_ (u"ࠥࡴࡷࡵࡸࡺࡕࡨࡸࡹ࡯࡮ࡨࡵࠥᵅ")))
    bstack111lllll1l1_opy_ = [element.lower() for element in bstack11l1lll1l11_opy_]
    bstack11l11ll111l_opy_(bstack111ll1l1lll_opy_, bstack111lllll1l1_opy_)
    return bstack111ll1l1lll_opy_
def bstack11l11ll111l_opy_(d, keys):
    for key in list(d.keys()):
        if key.lower() in keys:
            d[key] = bstack111l1ll_opy_ (u"ࠦ࠯࠰ࠪࠫࠤᵆ")
    for value in d.values():
        if isinstance(value, dict):
            bstack11l11ll111l_opy_(value, keys)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    bstack11l11ll111l_opy_(item, keys)
def bstack1l1ll11111l_opy_():
    bstack111ll11ll11_opy_ = [os.environ.get(bstack111l1ll_opy_ (u"ࠧࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡋࡏࡌࡆࡕࡢࡈࡎࡘࠢᵇ")), os.path.join(os.path.expanduser(bstack111l1ll_opy_ (u"ࠨࡾࠣᵈ")), bstack111l1ll_opy_ (u"ࠧ࠯ࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࠧᵉ")), os.path.join(bstack111l1ll_opy_ (u"ࠨ࠱ࡷࡱࡵ࠭ᵊ"), bstack111l1ll_opy_ (u"ࠩ࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࠩᵋ"))]
    for path in bstack111ll11ll11_opy_:
        if path is None:
            continue
        try:
            if os.path.exists(path):
                logger.debug(bstack111l1ll_opy_ (u"ࠥࡊ࡮ࡲࡥࠡࠩࠥᵌ") + str(path) + bstack111l1ll_opy_ (u"ࠦࠬࠦࡥࡹ࡫ࡶࡸࡸ࠴ࠢᵍ"))
                if not os.access(path, os.W_OK):
                    logger.debug(bstack111l1ll_opy_ (u"ࠧࡍࡩࡷ࡫ࡱ࡫ࠥࡶࡥࡳ࡯࡬ࡷࡸ࡯࡯࡯ࡵࠣࡪࡴࡸࠠࠨࠤᵎ") + str(path) + bstack111l1ll_opy_ (u"ࠨࠧࠣᵏ"))
                    os.chmod(path, 0o777)
                else:
                    logger.debug(bstack111l1ll_opy_ (u"ࠢࡇ࡫࡯ࡩࠥ࠭ࠢᵐ") + str(path) + bstack111l1ll_opy_ (u"ࠣࠩࠣࡥࡱࡸࡥࡢࡦࡼࠤ࡭ࡧࡳࠡࡶ࡫ࡩࠥࡸࡥࡲࡷ࡬ࡶࡪࡪࠠࡱࡧࡵࡱ࡮ࡹࡳࡪࡱࡱࡷ࠳ࠨᵑ"))
            else:
                logger.debug(bstack111l1ll_opy_ (u"ࠤࡆࡶࡪࡧࡴࡪࡰࡪࠤ࡫࡯࡬ࡦࠢࠪࠦᵒ") + str(path) + bstack111l1ll_opy_ (u"ࠥࠫࠥࡽࡩࡵࡪࠣࡻࡷ࡯ࡴࡦࠢࡳࡩࡷࡳࡩࡴࡵ࡬ࡳࡳ࠴ࠢᵓ"))
                os.makedirs(path, exist_ok=True)
                os.chmod(path, 0o777)
            logger.debug(bstack111l1ll_opy_ (u"ࠦࡔࡶࡥࡳࡣࡷ࡭ࡴࡴࠠࡴࡷࡦࡧࡪ࡫ࡤࡦࡦࠣࡪࡴࡸࠠࠨࠤᵔ") + str(path) + bstack111l1ll_opy_ (u"ࠧ࠭࠮ࠣᵕ"))
            return path
        except Exception as e:
            logger.debug(bstack111l1ll_opy_ (u"ࠨࡆࡢ࡫࡯ࡩࡩࠦࡴࡰࠢࡶࡩࡹࠦࡵࡱࠢࡩ࡭ࡱ࡫ࠠࠨࡽࡳࡥࡹ࡮ࡽࠨ࠼ࠣࠦᵖ") + str(e) + bstack111l1ll_opy_ (u"ࠢࠣᵗ"))
    logger.debug(bstack111l1ll_opy_ (u"ࠣࡃ࡯ࡰࠥࡶࡡࡵࡪࡶࠤ࡫ࡧࡩ࡭ࡧࡧ࠲ࠧᵘ"))
    return None
@measure(event_name=EVENTS.bstack11l1lll1l1l_opy_, stage=STAGE.bstack1l11lllll1_opy_)
def bstack1ll1lllllll_opy_(binary_path, bstack1lll1l11l1l_opy_, bs_config):
    logger.debug(bstack111l1ll_opy_ (u"ࠤࡆࡹࡷࡸࡥ࡯ࡶࠣࡇࡑࡏࠠࡑࡣࡷ࡬ࠥ࡬࡯ࡶࡰࡧ࠾ࠥࢁࡽࠣᵙ").format(binary_path))
    bstack11l1111ll11_opy_ = bstack111l1ll_opy_ (u"ࠪࠫᵚ")
    bstack11l111ll11l_opy_ = {
        bstack111l1ll_opy_ (u"ࠫࡸࡪ࡫ࡠࡸࡨࡶࡸ࡯࡯࡯ࠩᵛ"): __version__,
        bstack111l1ll_opy_ (u"ࠧࡵࡳࠣᵜ"): platform.system(),
        bstack111l1ll_opy_ (u"ࠨ࡯ࡴࡡࡤࡶࡨ࡮ࠢᵝ"): platform.machine(),
        bstack111l1ll_opy_ (u"ࠢࡤ࡮࡬ࡣࡻ࡫ࡲࡴ࡫ࡲࡲࠧᵞ"): bstack111l1ll_opy_ (u"ࠨ࠲ࠪᵟ"),
        bstack111l1ll_opy_ (u"ࠤࡶࡨࡰࡥ࡬ࡢࡰࡪࡹࡦ࡭ࡥࠣᵠ"): bstack111l1ll_opy_ (u"ࠪࡴࡾࡺࡨࡰࡰࠪᵡ")
    }
    bstack11l11l11lll_opy_(bstack11l111ll11l_opy_)
    try:
        if binary_path:
            bstack11l111ll11l_opy_[bstack111l1ll_opy_ (u"ࠫࡨࡲࡩࡠࡸࡨࡶࡸ࡯࡯࡯ࠩᵢ")] = subprocess.check_output([binary_path, bstack111l1ll_opy_ (u"ࠧࡼࡥࡳࡵ࡬ࡳࡳࠨᵣ")]).strip().decode(bstack111l1ll_opy_ (u"࠭ࡵࡵࡨ࠰࠼ࠬᵤ"))
        response = requests.request(
            bstack111l1ll_opy_ (u"ࠧࡈࡇࡗࠫᵥ"),
            url=bstack1l11l11l11_opy_(bstack11l1ll111l1_opy_),
            headers=None,
            auth=(bs_config[bstack111l1ll_opy_ (u"ࠨࡷࡶࡩࡷࡔࡡ࡮ࡧࠪᵦ")], bs_config[bstack111l1ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡳࡴࡍࡨࡽࠬᵧ")]),
            json=None,
            params=bstack11l111ll11l_opy_
        )
        data = response.json()
        if response.status_code == 200 and bstack111l1ll_opy_ (u"ࠪࡹࡷࡲࠧᵨ") in data.keys() and bstack111l1ll_opy_ (u"ࠫࡺࡶࡤࡢࡶࡨࡨࡤࡩ࡬ࡪࡡࡹࡩࡷࡹࡩࡰࡰࠪᵩ") in data.keys():
            logger.debug(bstack111l1ll_opy_ (u"ࠧࡔࡥࡦࡦࠣࡸࡴࠦࡵࡱࡦࡤࡸࡪࠦࡢࡪࡰࡤࡶࡾ࠲ࠠࡤࡷࡵࡶࡪࡴࡴࠡࡤ࡬ࡲࡦࡸࡹࠡࡸࡨࡶࡸ࡯࡯࡯࠼ࠣࡿࢂࠨᵪ").format(bstack11l111ll11l_opy_[bstack111l1ll_opy_ (u"࠭ࡣ࡭࡫ࡢࡺࡪࡸࡳࡪࡱࡱࠫᵫ")]))
            if bstack111l1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡂࡊࡐࡄࡖ࡞ࡥࡕࡓࡎࠪᵬ") in os.environ:
                logger.debug(bstack111l1ll_opy_ (u"ࠣࡕ࡮࡭ࡵࡶࡩ࡯ࡩࠣࡦ࡮ࡴࡡࡳࡻࠣࡨࡴࡽ࡮࡭ࡱࡤࡨࠥࡧࡳࠡࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡃࡋࡑࡅࡗ࡟࡟ࡖࡔࡏࠤ࡮ࡹࠠࡴࡧࡷࠦᵭ"))
                data[bstack111l1ll_opy_ (u"ࠩࡸࡶࡱ࠭ᵮ")] = os.environ[bstack111l1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡅࡍࡓࡇࡒ࡚ࡡࡘࡖࡑ࠭ᵯ")]
            bstack111lll11l1l_opy_ = bstack111llll1111_opy_(data[bstack111l1ll_opy_ (u"ࠫࡺࡸ࡬ࠨᵰ")], bstack1lll1l11l1l_opy_)
            bstack11l1111ll11_opy_ = os.path.join(bstack1lll1l11l1l_opy_, bstack111lll11l1l_opy_)
            os.chmod(bstack11l1111ll11_opy_, 0o777) # bstack111llll1l1l_opy_ permission
            return bstack11l1111ll11_opy_
    except Exception as e:
        logger.debug(bstack111l1ll_opy_ (u"ࠧࡋࡲࡳࡱࡵࠤࡼ࡮ࡩ࡭ࡧࠣࡨࡴࡽ࡮࡭ࡱࡤࡨ࡮ࡴࡧࠡࡰࡨࡻ࡙ࠥࡄࡌࠢࡾࢁࠧᵱ").format(e))
    return binary_path
def bstack11l11l11lll_opy_(bstack11l111ll11l_opy_):
    try:
        if bstack111l1ll_opy_ (u"࠭࡬ࡪࡰࡸࡼࠬᵲ") not in bstack11l111ll11l_opy_[bstack111l1ll_opy_ (u"ࠧࡰࡵࠪᵳ")].lower():
            return
        if os.path.exists(bstack111l1ll_opy_ (u"ࠣ࠱ࡨࡸࡨ࠵࡯ࡴ࠯ࡵࡩࡱ࡫ࡡࡴࡧࠥᵴ")):
            with open(bstack111l1ll_opy_ (u"ࠤ࠲ࡩࡹࡩ࠯ࡰࡵ࠰ࡶࡪࡲࡥࡢࡵࡨࠦᵵ"), bstack111l1ll_opy_ (u"ࠥࡶࠧᵶ")) as f:
                bstack111ll1lllll_opy_ = {}
                for line in f:
                    if bstack111l1ll_opy_ (u"ࠦࡂࠨᵷ") in line:
                        key, value = line.rstrip().split(bstack111l1ll_opy_ (u"ࠧࡃࠢᵸ"), 1)
                        bstack111ll1lllll_opy_[key] = value.strip(bstack111l1ll_opy_ (u"࠭ࠢ࡝ࠩࠪᵹ"))
                bstack11l111ll11l_opy_[bstack111l1ll_opy_ (u"ࠧࡥ࡫ࡶࡸࡷࡵࠧᵺ")] = bstack111ll1lllll_opy_.get(bstack111l1ll_opy_ (u"ࠣࡋࡇࠦᵻ"), bstack111l1ll_opy_ (u"ࠤࠥᵼ"))
        elif os.path.exists(bstack111l1ll_opy_ (u"ࠥ࠳ࡪࡺࡣ࠰ࡣ࡯ࡴ࡮ࡴࡥ࠮ࡴࡨࡰࡪࡧࡳࡦࠤᵽ")):
            bstack11l111ll11l_opy_[bstack111l1ll_opy_ (u"ࠫࡩ࡯ࡳࡵࡴࡲࠫᵾ")] = bstack111l1ll_opy_ (u"ࠬࡧ࡬ࡱ࡫ࡱࡩࠬᵿ")
    except Exception as e:
        logger.debug(bstack111l1ll_opy_ (u"ࠨࡕ࡯ࡣࡥࡰࡪࠦࡴࡰࠢࡪࡩࡹࠦࡤࡪࡵࡷࡶࡴࠦ࡯ࡧࠢ࡯࡭ࡳࡻࡸࠣᶀ") + e)
@measure(event_name=EVENTS.bstack11l1l1ll111_opy_, stage=STAGE.bstack1l11lllll1_opy_)
def bstack111llll1111_opy_(bstack11l11lll1l1_opy_, bstack11l11lll1ll_opy_):
    logger.debug(bstack111l1ll_opy_ (u"ࠢࡅࡱࡺࡲࡱࡵࡡࡥ࡫ࡱ࡫࡙ࠥࡄࡌࠢࡥ࡭ࡳࡧࡲࡺࠢࡩࡶࡴࡳ࠺ࠡࠤᶁ") + str(bstack11l11lll1l1_opy_) + bstack111l1ll_opy_ (u"ࠣࠤᶂ"))
    zip_path = os.path.join(bstack11l11lll1ll_opy_, bstack111l1ll_opy_ (u"ࠤࡧࡳࡼࡴ࡬ࡰࡣࡧࡩࡩࡥࡦࡪ࡮ࡨ࠲ࡿ࡯ࡰࠣᶃ"))
    bstack111lll11l1l_opy_ = bstack111l1ll_opy_ (u"ࠪࠫᶄ")
    with requests.get(bstack11l11lll1l1_opy_, stream=True) as response:
        response.raise_for_status()
        with open(zip_path, bstack111l1ll_opy_ (u"ࠦࡼࡨࠢᶅ")) as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        logger.debug(bstack111l1ll_opy_ (u"ࠧࡌࡩ࡭ࡧࠣࡨࡴࡽ࡮࡭ࡱࡤࡨࡪࡪࠠࡴࡷࡦࡧࡪࡹࡳࡧࡷ࡯ࡰࡾ࠴ࠢᶆ"))
    with zipfile.ZipFile(zip_path, bstack111l1ll_opy_ (u"࠭ࡲࠨᶇ")) as zip_ref:
        bstack11l11l111l1_opy_ = zip_ref.namelist()
        if len(bstack11l11l111l1_opy_) > 0:
            bstack111lll11l1l_opy_ = bstack11l11l111l1_opy_[0] # bstack11l1111lll1_opy_ bstack11l1l1l1ll1_opy_ will be bstack11111l11ll_opy_ 1 file i.e. the binary in the zip
        zip_ref.extractall(bstack11l11lll1ll_opy_)
        logger.debug(bstack111l1ll_opy_ (u"ࠢࡇ࡫࡯ࡩࡸࠦࡳࡶࡥࡦࡩࡸࡹࡦࡶ࡮࡯ࡽࠥ࡫ࡸࡵࡴࡤࡧࡹ࡫ࡤࠡࡶࡲࠤࠬࠨᶈ") + str(bstack11l11lll1ll_opy_) + bstack111l1ll_opy_ (u"ࠣࠩࠥᶉ"))
    os.remove(zip_path)
    return bstack111lll11l1l_opy_
def get_cli_dir():
    bstack11l11l1l1l1_opy_ = bstack1l1ll11111l_opy_()
    if bstack11l11l1l1l1_opy_:
        bstack1lll1l11l1l_opy_ = os.path.join(bstack11l11l1l1l1_opy_, bstack111l1ll_opy_ (u"ࠤࡦࡰ࡮ࠨᶊ"))
        if not os.path.exists(bstack1lll1l11l1l_opy_):
            os.makedirs(bstack1lll1l11l1l_opy_, mode=0o777, exist_ok=True)
        return bstack1lll1l11l1l_opy_
    else:
        raise FileNotFoundError(bstack111l1ll_opy_ (u"ࠥࡒࡴࠦࡷࡳ࡫ࡷࡥࡧࡲࡥࠡࡦ࡬ࡶࡪࡩࡴࡰࡴࡼࠤࡦࡼࡡࡪ࡮ࡤࡦࡱ࡫ࠠࡧࡱࡵࠤࡹ࡮ࡥࠡࡕࡇࡏࠥࡨࡩ࡯ࡣࡵࡽ࠳ࠨᶋ"))
def bstack1ll1lll1111_opy_(bstack1lll1l11l1l_opy_):
    bstack111l1ll_opy_ (u"ࠦࠧࠨࡇࡦࡶࠣࡸ࡭࡫ࠠࡱࡣࡷ࡬ࠥ࡬࡯ࡳࠢࡷ࡬ࡪࠦࡂࡳࡱࡺࡷࡪࡸࡓࡵࡣࡦ࡯࡙ࠥࡄࡌࠢࡥ࡭ࡳࡧࡲࡺࠢ࡬ࡲࠥࡧࠠࡸࡴ࡬ࡸࡦࡨ࡬ࡦࠢࡧ࡭ࡷ࡫ࡣࡵࡱࡵࡽ࠳ࠨࠢࠣᶌ")
    bstack11l11l1llll_opy_ = [
        os.path.join(bstack1lll1l11l1l_opy_, f)
        for f in os.listdir(bstack1lll1l11l1l_opy_)
        if os.path.isfile(os.path.join(bstack1lll1l11l1l_opy_, f)) and f.startswith(bstack111l1ll_opy_ (u"ࠧࡨࡩ࡯ࡣࡵࡽ࠲ࠨᶍ"))
    ]
    if len(bstack11l11l1llll_opy_) > 0:
        return max(bstack11l11l1llll_opy_, key=os.path.getmtime) # get bstack11l111111l1_opy_ binary
    return bstack111l1ll_opy_ (u"ࠨࠢᶎ")
def bstack11ll1l1l11l_opy_():
  from selenium import webdriver
  return version.parse(webdriver.__version__)
def bstack1ll111l1lll_opy_(d, u):
  for k, v in u.items():
    if isinstance(v, collections.abc.Mapping):
      d[k] = bstack1ll111l1lll_opy_(d.get(k, {}), v)
    else:
      if isinstance(v, list):
        d[k] = d.get(k, []) + v
      else:
        d[k] = v
  return d
def bstack111ll11l_opy_(data, keys, default=None):
    bstack111l1ll_opy_ (u"ࠢࠣࠤࠍࠤࠥࠦࠠࡔࡣࡩࡩࡱࡿࠠࡨࡧࡷࠤࡦࠦ࡮ࡦࡵࡷࡩࡩࠦࡶࡢ࡮ࡸࡩࠥ࡬ࡲࡰ࡯ࠣࡥࠥࡪࡩࡤࡶ࡬ࡳࡳࡧࡲࡺࠢࡲࡶࠥࡲࡩࡴࡶ࠱ࠎࠥࠦࠠࠡ࠼ࡳࡥࡷࡧ࡭ࠡࡦࡤࡸࡦࡀࠠࡕࡪࡨࠤࡩ࡯ࡣࡵ࡫ࡲࡲࡦࡸࡹࠡࡱࡵࠤࡱ࡯ࡳࡵࠢࡷࡳࠥࡺࡲࡢࡸࡨࡶࡸ࡫࠮ࠋࠢࠣࠤࠥࡀࡰࡢࡴࡤࡱࠥࡱࡥࡺࡵ࠽ࠤࡆࠦ࡬ࡪࡵࡷࠤࡴ࡬ࠠ࡬ࡧࡼࡷ࠴࡯࡮ࡥ࡫ࡦࡩࡸࠦࡲࡦࡲࡵࡩࡸ࡫࡮ࡵ࡫ࡱ࡫ࠥࡺࡨࡦࠢࡳࡥࡹ࡮࠮ࠋࠢࠣࠤࠥࡀࡰࡢࡴࡤࡱࠥࡪࡥࡧࡣࡸࡰࡹࡀࠠࡗࡣ࡯ࡹࡪࠦࡴࡰࠢࡵࡩࡹࡻࡲ࡯ࠢ࡬ࡪࠥࡺࡨࡦࠢࡳࡥࡹ࡮ࠠࡥࡱࡨࡷࠥࡴ࡯ࡵࠢࡨࡼ࡮ࡹࡴ࠯ࠌࠣࠤࠥࠦ࠺ࡳࡧࡷࡹࡷࡴ࠺ࠡࡖ࡫ࡩࠥࡼࡡ࡭ࡷࡨࠤࡦࡺࠠࡵࡪࡨࠤࡳ࡫ࡳࡵࡧࡧࠤࡵࡧࡴࡩ࠮ࠣࡳࡷࠦࡤࡦࡨࡤࡹࡱࡺࠠࡪࡨࠣࡲࡴࡺࠠࡧࡱࡸࡲࡩ࠴ࠊࠡࠢࠣࠤࠧࠨࠢᶏ")
    if not data:
        return default
    current = data
    try:
        for key in keys:
            if isinstance(current, dict):
                current = current[key]
            elif isinstance(current, list) and isinstance(key, int):
                current = current[key]
            else:
                return default
        return current
    except (KeyError, IndexError, TypeError):
        return default