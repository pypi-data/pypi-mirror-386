# -*- coding: UTF-8 -*-
import json
import os
import random
import time

import kobo.conf
import koji
from git import Repo
from kobo.shortcuts import force_list
from productmd import ComposeInfo

from kyutil.config import BUILD_PATH, ROOT_PATH_ISO_PATH, ALLOWED_STATUSES
from kyutil.date_utils import get_today
from kyutil.paths import BasePaths


class PungiKojiBase(object):
    """集成构建基类"""

    def __init__(self, **kwargs):
        """init初始化函数-基类"""
        self.config_repo_dir = f"{ROOT_PATH_ISO_PATH}auto_os/"
        self.config_dir = os.path.join(self.config_repo_dir, kwargs.get('config_dir', '').lstrip("/"))
        self.config_name = kwargs.get('config_name')
        self.config_filepath = os.path.join(self.config_dir, self.config_name)
        self.conf = self.load_config()
        self.ci_base = ComposeInfo()
        self.load_compose()
        self.path = BasePaths(kwargs.get('work_dir', self.get_work_dir()))
        self.profile = None

    def check(self):
        self.check_koji_profile()

    def check_koji_profile(self):
        try:
            self.profile = self.conf.get("koji_profile", None)
            if not self.profile:
                raise RuntimeError(f"koji_profile必须指定，请检查 {self.config_filepath} 中是否配置 koji_profile ！")
            koji.read_config(self.profile)
        except Exception as e:
            raise RuntimeError(f"{e}，检查{self.config_filepath} 中配置的 koji_profile是否在编译机配置 ！")

    def load_compose(self):
        res = self.get_old_compose()
        if res:
            self.ci_base.load(res)
        else:
            self.ci_base = None

    def load_config(self, defaults=None):
        """Open and load configuration file form .conf or .json file."""
        if not os.path.exists(self.config_filepath):
            return None
        conf = kobo.conf.PyConfigParser()
        conf.load_from_dict(defaults)
        if self.config_filepath.endswith(".json"):
            with open(self.config_filepath) as f:
                conf.load_from_dict(json.load(f))
            conf.opened_files = [self.config_filepath]
            conf._open_file = self.config_filepath
        else:
            conf.load_from_file(self.config_filepath)
        return conf

    def get_work_dir(self, topdir="/mnt/koji/compose/", compose_type="production", compose_date=None,
                     compose_respin=None, compose_label=None):
        respin = None
        if self.ci_base:
            if self.ci_base.compose.date == time.strftime("%Y%m%d", time.localtime()):
                respin = int(self.ci_base.compose.respin) + 1
            else:
                respin = None
        if compose_respin:
            respin = compose_respin
        ci = get_compose_info(self.conf, compose_type, compose_date, respin, compose_label)
        ci.compose.id = ci.create_compose_id()
        compose_dir = os.path.join(topdir, ci.compose.id)

        return compose_dir

    def get_old_compose(self):
        res = find_old_compose("/mt/koji/compose/", self.conf)
        if not res or not os.path.exists(res):
            return None
        conf = BasePaths(res).work.composeinfo()
        if not os.path.exists(conf):
            return None
        return conf

    def link_compose(self, compose_dir):
        """
        :param compose_dir:
        """
        work_dir = self.path.topdir()
        try:
            os.symlink(work_dir, compose_dir.rstrip('/'))
            print(f"Symbolic link created: {work_dir} -> {compose_dir}")
        except OSError as e:
            print(f"Failed to create symbolic link: {e}")

    def update_config_repo(self, commit='HEAD'):
        """
        """
        config_repo = Repo(self.config_repo_dir)
        config_repo.git.reset('--hard', commit)
        current_commit = config_repo.commit()
        config_repo.remote().fetch()
        config_repo.remote().pull()
        latest_commit = config_repo.commit()
        if current_commit != latest_commit:
            print(f"config_repo updated: {current_commit} -> {latest_commit}")

    def generate_image_build_info(self):
        res = []
        image_build_conf = self.conf.get("image_build", {})  # 读取配置文件image_build
        if not image_build_conf:
            return
        for v in image_build_conf.values():
            for conf in v:
                data = {}
                sub_conf = conf.get('image-build', {})
                factory_conf = conf.get("factory-parameters", {})
                archs = sub_conf.get('arches', [])
                archs = self._format_image_build_arch_info(archs)
                data['image_name'] = sub_conf.get('name', '')
                data['image_tag'] = factory_conf.get('tag', '')
                data['build_id'] = factory_conf.get('build_id', '')
                data['label'] = factory_conf.get('docker_set_arch_label', '')
                if sub_conf.get('format', '') != 'docker':
                    continue
                for arch in archs:
                    data['arch'] = arch
                    res.append(data)
        return res


def del_note(s):
    return s.split("#")[0].strip().strip('"').strip("'")


def get_pattern(config_filepath) -> str:
    release_short, release_version, release_type_suffix = "", "", ""
    if not os.path.isfile(config_filepath):
        return ""

    for i in open(config_filepath, "r"):
        if i.strip() and i.find("release_short") >= 0 and not release_short:
            release_short = del_note(i.split("=")[-1].strip() or "")
        elif i.strip() and i.find("release_version") >= 0 and not release_version:
            release_version = del_note(i.split("=")[-1].strip() or "")
        elif i.strip() and i.find("release_type_suffix") >= 0 and not release_type_suffix:
            release_type_suffix = del_note(i.split("=")[-1].strip() or "")
    return "%s-%s%s" % (release_short, release_version, release_type_suffix)


def get_work_dir(task_id, config_filepath, root_path_build=BUILD_PATH, product_code="", fmt="%m%d%H%M%S") -> str:
    """
    通过配置获取工作目录
    Args:
        task_id:
        config_filepath:
        root_path_build:
        product_code: 产品代号,类似V11
        fmt: 时间格式化模板

    Returns:
        /mnt/iso_builder/isobuild/v11/Kylin-Server-V11-202505151200-8888.0/  # 以V11为例
    """
    pattern = get_pattern(config_filepath)
    if not pattern:
        return ""
    return f'{root_path_build}/{product_code}/{pattern}-{get_today(ts=time.time(), fmt=fmt)}-{task_id[:2]}.{str(random.randint(10, 99))}/'


def get_compose_info(
        conf,
        compose_type="production",
        compose_date=None,
        compose_respin=None,
        compose_label=None,
):
    """
       Creates inncomplete ComposeInfo to generate Compose ID
    """
    ci = ComposeInfo()
    ci.release.name = conf["release_name"]
    ci.release.short = conf["release_short"]
    ci.release.version = conf["release_version"]
    ci.release.is_layered = True if conf.get("base_product_name", "") else False
    ci.release.type = conf.get("release_type", "ga").lower()
    ci.release.internal = bool(conf.get("release_internal", False))
    if ci.release.is_layered:
        ci.base_product.name = conf["base_product_name"]
        ci.base_product.short = conf["base_product_short"]
        ci.base_product.version = conf["base_product_version"]
        ci.base_product.type = conf.get("base_product_type", "ga").lower()

    ci.compose.label = compose_label
    ci.compose.type = compose_type
    ci.compose.date = compose_date or time.strftime("%Y%m%d", time.localtime())
    ci.compose.respin = compose_respin or 0
    ci.compose.id = ci.create_compose_id()
    return ci


def sortable(compose_id):
    """Convert ID to tuple where respin is an integer for proper sorting."""
    try:
        prefix, respin = compose_id.rsplit(".", 1)
        return prefix, int(respin)
    except Exception:
        return compose_id


def find_old_compose(old_compose_dirs, conf):
    composes = []
    release_short = conf['release_short']
    release_version = conf['release_version']
    release_type_suffix = conf.get("release_type_suffix", "")
    pattern = "%s-%s%s" % (release_short, release_version, release_type_suffix)
    for compose_dir in force_list(old_compose_dirs):
        if not os.path.isdir(compose_dir):
            continue
        # get all finished composes
        for i in list_files_starting_with(compose_dir, pattern):
            suffix = i[len(pattern):]
            if len(suffix) < 2 or not suffix[1].isdigit():
                continue
            path = os.path.join(compose_dir, i)
            status_path = os.path.join(path, "STATUS")
            if read_compose_status(status_path):
                composes.append((sortable(i), os.path.abspath(path)))
    if not composes:
        return None

    return sorted(composes)[-1][1]


def list_files_starting_with(directory, prefix):
    return [f for f in os.listdir(directory) if f.startswith(prefix)]


def read_compose_status(status_path):
    if not os.path.exists(status_path) or not os.path.isfile(status_path):
        return False
    try:
        with open(status_path, "r") as f:
            if f.read().strip() in ALLOWED_STATUSES:
                return True
    except Exception as e:
        print(e)
        return False
