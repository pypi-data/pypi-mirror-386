#!/usr/bin/env python3
# encoding=utf-8
# 描述：组件维护工具
# Copyright (c) 2024 Huawei Technologies Co., Ltd.
# openUBMC is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#         http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
import os
import subprocess
import json
import re
import yaml

from bmcgo import errors
from bmcgo import misc
from bmcgo.misc import CommandInfo
from bmcgo.utils.tools import Tools
from bmcgo.bmcgo_config import BmcgoConfig

tool = Tools("conanIdx")
log = tool.log
command_info: CommandInfo = CommandInfo(
    group="Conan Index commmands",
    name="build",
    description=["构建conan index仓下的组件"],
    hidden=False
)


def if_available(bconfig: BmcgoConfig):
    return bconfig.conan_index is not None and bconfig.manifest is None


class Function:
    """功能类, 用于做一些通用操作
    """
    @classmethod
    def git_check(cls, tag_list: list):
        """检查 tag 是否在远端 url 内

        Args:
            tag_list (list): 依赖仓列表

        Raises:
            AttributeError: 如果其中有一个不是 tag, 则报错
        """
        check = True
        for tag in tag_list:
            cmd = f"git ls-remote {tag['url']} --tags {tag['tag']} | grep tags"
            ret = subprocess.getstatusoutput(cmd)
            if ret[0] != 0:
                log.error("%s not a tag in %s", tag['tag'], tag['url'])
                check = False
        if check is True:
            log.info("tag list check successfully !!!")
        else:
            raise AttributeError("tag list check fail !!!")


class BmcgoCommand:
    def __init__(self, bconfig: BmcgoConfig, *args):
        self.bconfig = bconfig
        parser = tool.create_common_parser("Conan Index Build")
        parser.add_argument("--conan2", help="是否构建conan2.x版本的组件包", action=misc.STORE_TRUE)
        self.args, _ = parser.parse_known_args(*args)
        self.conan2 = self.args.conan2
        self.path = ""
        self.version = ""
        self.name = ""
        self.user = ""
        self.channel = ""
        self.conan_package = ""
        self.upload = False
        self.remote = None
        self.options = []
        self.stage = self.args.stage
        self.enable_luajit = False
        self.from_source = False
        self.build_type = 'debug'
        self.asan = False
        self.profile = ''
        self.recipe_folder = self.bconfig.conan_index.folder
        if misc.conan_v2():
            recipes2_folder = os.path.join(self.bconfig.conan_index.folder, "..", "recipes2")
            recipes2_folder = os.path.realpath(recipes2_folder)
            if os.path.isdir(recipes2_folder):
                self.recipe_folder = recipes2_folder
        self.initialize()

    @staticmethod
    def run_command(command, ignore_error=False, sudo=False, **kwargs):
        """
        如果ignore_error为False，命令返回码非0时则打印堆栈和日志并触发异常，中断构建
        """
        uptrace = kwargs.get("uptrace", 1)
        kwargs["uptrace"] = uptrace
        return tool.run_command(command, ignore_error, sudo, **kwargs)
    
    @staticmethod
    def check_luac():
        luac_path = os.path.join(os.path.expanduser('~'), ".conan", "bin", "luac")
        if not os.path.isfile(luac_path):
            raise errors.BmcGoException(f"当前环境中未安装luac！请更新manifest仓代码，执行环境初始化脚本init.py重新部署环境！")
        
        conan_bin = os.path.join(os.path.expanduser('~'), ".conan", "bin")
        # 设置PLD_LIBRARY_PATH环境变量，luajit运行时需要加载so动态库
        ld_library_path = conan_bin + ":" + os.environ.get("LD_LIBRARY_PATH", "")
        os.environ["LD_LIBRARY_PATH"] = ld_library_path
        # 设置PATH环境变量，luajit无需指定全路径
        path = conan_bin + ":" + os.environ.get("PATH", "")
        os.environ["PATH"] = path
        os.environ["LUA_PATH"] = f"{conan_bin}/?.lua"

    def initialize(self):
        if not self.args.conan_package:
            msg = "构建参数错误，请指定有效的-cp参数，例：kmc/1.0.1 或 kmc/1.0.1@openubmc/stable"
            raise errors.BmcGoException(msg)
        self.set_package(self.args.conan_package)
        self.upload = self.args.upload_package
        if self.args.remote:
            self.remote = self.args.remote
        if self.args.options:
            self.options = self.args.options
        self.enable_luajit = self.args.enable_luajit
        self.from_source = self.args.from_source
        self.build_type = self.args.build_type
        self.asan = self.args.asan
        self.profile = Tools.get_conan_profile(None, self.build_type, self.enable_luajit)
        if self.args.profile:
            self.profile = self.args.profile

    # 入参可以是huawei_secure_c/1.0.0样式
    def set_package(self, path: str):
        os.chdir(self.recipe_folder)
        split = re.split('/|@', path)
        if len(split) != 2 and len(split) != 4:
            raise errors.BmcGoException(f"包名称({path})错误，例：kmc/1.0.1 或 kmc/1.0.1@openubmc/stable")
        self.name = split[0].lower()
        if len(split) == 2:
            if self.stage == "dev":
                self.user = misc.conan_user_dev()
            else:
                self.user = misc.conan_user()
            self.channel = self.stage
        else:
            self.user = split[2]
            self.channel = split[3]

        if not os.path.isdir(split[0]):
            raise errors.BmcGoException(f"包路径({split[0]})不存在，或不是文件夹")

        config_yaml = os.path.join(self.recipe_folder, split[0], "config.yml")
        with open(config_yaml) as f:
            config_data = yaml.safe_load(f)
            config_data = config_data.get('versions', None)
            if config_data is None:
                raise errors.BmcGoException(f"Config format error, config.yml path: {config_yaml}")
            config_data = config_data.get(split[1], None)
            if config_data is None:
                raise errors.BmcGoException(f"Unkown version, config.yml path: {config_yaml}, version: {split[1]}")
            folder = config_data.get('folder', None)
            if config_data is None:
                raise errors.BmcGoException(f"Unkown folder, config.yml path: {config_yaml}, version: {split[1]}")
            self.path = "{}/{}".format(split[0], folder)
            self.version = split[1]
            if misc.conan_v2():
                self.version = self.version.lower()
            # openubmcsdk采用的不是conandata.yml的方式，需特殊处理
            if self.name == "openubmcsdk":
                return
            if self.stage != "dev":
                self.tag_check()

    def run_v2(self):
        log.info("Start build package")
        if self.build_type == "debug":
            setting = "-s build_type=Debug"
        else:
            setting = "-s build_type=Release"
        options = " "
        if self.asan:
            options += f"-o {self.name}/*:asan=True"
        for option in self.options:
            options += f" -o {option}"

        dt_stat = os.environ.get("BINGO_DT_RUN", "off")
        show_log = True if dt_stat == "off" else False
        pkg = self.name + "/" + self.version + "@" + self.user + "/" + self.channel
        # openubmcsdk通过export发布，需特殊处理
        if self.name == "openubmcsdk":
            cmd = "conan export . --name {} --version {} --user {} --channel {}".format(
                self.name, self.version, self.user, self.channel)
        else:
            append_cmd = f"-r {self.remote}" if self.remote else ""
            cmd = "conan create . --name={} --version={} -pr={} {} {} {}".format(
                self.name, self.version, self.profile, setting, append_cmd, options
            )

            cmd += " --user={} --channel={}".format(self.user, self.channel)
            if self.from_source:
                cmd += " --build=*"
            else:
                cmd += f" --build={self.name}/* --build=missing"
        self.run_command(cmd, show_log=show_log)

        if not self.upload:
            return

        cmd = "conan upload {} -r {}".format(pkg, self.remote)
        self.run_command(cmd)
        log.info("===>>>Upload package successfully, pkg: {}".format(pkg))

    def run_v1(self):
        self.check_luac()
        log.info("Start build package")
        if self.build_type == "dt":
            setting = "-s build_type=Dt"
        else:
            if self.build_type == "debug":
                setting = "-s build_type=Debug"
            else:
                setting = "-s build_type=Release"
        options = " "
        packake_name = self.path.split("/")[0]
        if self.asan:
            options += f"-o {packake_name}:asan=True"
        for option in self.options:
            options += f" -o {option}"

        dt_stat = os.environ.get("BMCGO_DT_RUN", "off")
        show_log = True if dt_stat == "off" else False
        pkg = self.name + "/" + self.version + "@" + self.user + "/" + self.channel
        append_cmd = f"-r {self.remote}" if self.remote else ""
        cmd = "conan create . {} -pr={} -pr:b profile.dt.ini {} {} -tf None {}".format(
            pkg, self.profile, setting, append_cmd, options
        )
        cmd += f" --build={packake_name}"
        if self.from_source:
            cmd += " --build=*"
        else:
            cmd += " --build=missing"
        # openubmcsdk通过export发布，需特殊处理
        if self.name == "openubmcsdk":
            cmd = "conan export . {}".format(pkg)
        self.run_command(cmd, show_log=show_log)

        if not self.upload:
            return

        # openubmcsdk组件无conan info信息，需特殊处理
        if self.name == "openubmcsdk":
            cmd = "conan upload {} -r {}".format(pkg, self.remote)
            self.run_command(cmd)
            log.info("===>>>Upload package successfully, pkg: {}".format(pkg))
            return
        cmd = "conan info {} -pr={} -j".format(pkg, self.profile)
        info_json = self.run_command(cmd, shell=True, capture_output=True).stdout
        for line in info_json.split("\n"):
            if line.startswith("[{"):
                info_json = line
                break
        info = json.loads(info_json)
        for i in info:
            if i["reference"] != pkg:
                continue
            cmd = "conan upload {}:{} -r {} -c --retry=3 --retry-wait 10 --all".format(pkg, i["id"], self.remote)
            self.run_command(cmd)
            log.info("===>>>Upload package successfully, pkg: {}:{}".format(pkg, i["id"]))

    def run(self):
        if self.path == "" or self.version == "":
            raise errors.BmcGoException(f"Path({self.path}) or version({self.version}) error")

        if not self.check_conan(self.conan2):
            return -1
        os.chdir(self.path)
        if misc.conan_v1():
            self.run_v1()
        else:
            self.run_v2()
        return 0

    def tag_check(self):
        yaml_file = f"{self.path}/conandata.yml"
        if os.path.exists(yaml_file) is False:
            log.warning("%s config not exists or does not need config file")
        with open(yaml_file, mode="r") as fp:
            config_data = yaml.safe_load(fp)
        # 这个值是必定存在的
        version_config = config_data['sources'][self.version]
        tag_list = []
        # 单个仓的处理
        if version_config.get('url', None) is not None:
            tag_list.append({"tag": version_config['branch'], "url": version_config['url']})
        # 多个仓的处理
        else:
            for value in version_config.values():
                tag_list.append({"tag": value['branch'], "url": value['url']})
        # 这里的 git 命令的意思是检查远端是否有此 tag, 如果不加 grep, 可能导致分支被认为是 tag
        Function.git_check(tag_list)

    def check_conan(self, need_conan_v2):
        if need_conan_v2 and misc.conan_v1():
            log.warning("检测到依赖conan2.0但仅安装了conan1.0，尝试重新安装conan2.0")
            log.info("  conan_index仓使用参数`--conan2`控制是否构建conan2.0包（conan2.0包配方存储在recipes2目录）")
            self.run_command("pip3 install conan==2.13.0 --break-system-packages")
            log.warning("检测到依赖conan2.0但仅安装了conan1.0，已安装conan2.0，任务退出，请重新执行")
            return False
        if not need_conan_v2 and misc.conan_v2():
            log.warning("检测到依赖conan1.0但仅安装了conan2.0，尝试重新安装conan1.0")
            log.info("  conan_index仓默认（不指定`--conan2`时）构建conan1.0包（conan1.0包配方存储在recipes目录）")
            self.run_command("pip3 install conan==1.62.0 --break-system-packages")
            log.warning("检测到依赖conan1.0但仅安装了conan2.0，已安装conan1.0，任务退出，请重新执行")
            return False
        return True