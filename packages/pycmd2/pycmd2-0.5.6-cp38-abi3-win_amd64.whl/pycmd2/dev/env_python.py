"""功能: 初始化 python 环境变量."""

import logging
import re
from pathlib import Path

from typer import Option
from typing_extensions import Annotated

from pycmd2.client import get_client

cli = get_client()
logger = logging.getLogger(__name__)

# 用户文件夹
BASHRC_PATH = cli.home / ".bashrc"

# pip 配置信息
PIP_CONF_CONTENT = """[global]
index-url = http://mirrors.aliyun.com/pypi/simple/
[install]
trusted-host = mirrors.aliyun.com
"""


def _set_chmod(filepath: Path) -> None:
    # 设置安全权限 (仅限 Unix 系统)
    if not cli.is_windows:
        if not filepath.exists():
            cli.run_cmd(["touch", str(filepath)])

        try:
            filepath.chmod(0o600)
            logger.info(f"设置文件权限: {oct(filepath.stat().st_mode)[-3:]}")
        except OSError:
            logger.exception(f"设置文件权限失败: {filepath}")
    else:
        logger.info("Windows系统, 跳过权限设置")


def add_env_to_bashrc(
    variable: str,
    value: str,
    comment: str = "",
    *,
    override: bool = False,
) -> bool:
    """安全添加或覆盖环境变量到.bashrc文件(优化空行问题).

    Parameters:
        variable: 变量名 (如 "UV_INDEX_URL")
        value: 变量值 (如 "http://mirrors.aliyun.com/pypi/simple/")
        comment: 可选注释说明
        override: 是否覆盖已有配置 (默认: False)

    Returns:
        操作是否成功.
    """
    export_line = f'export {variable}="{value}"'
    entry = (
        f"\n# {comment}\n{export_line}\n" if comment else f"\n{export_line}\n"
    )

    try:
        # 读取现有内容
        content = (
            BASHRC_PATH.read_text(encoding="utf-8")
            if BASHRC_PATH.exists()
            else ""
        )

        # 匹配现有配置的正则模式
        pattern = re.compile(
            r"^export\s+" + re.escape(variable) + r"=.*$",
            flags=re.MULTILINE,
        )

        if pattern.search(content):
            if override:
                # 改进点1: 删除旧配置及其后的空行.
                new_content = re.sub(pattern, "", content)

                # 改进点2: 清理多余空行(3+换行 -> 2换行).
                new_content = re.sub(r"\n{3,}", "\n\n", new_content)

                # 改进点3: 确保末尾换行后添加新条目.
                new_content = new_content.rstrip("\n") + "\n"
                new_content += entry.lstrip("\n")

                BASHRC_PATH.write_text(new_content, encoding="utf-8")
                logger.info(f"✅ 成功覆盖 {variable} 配置")
                return True
            logger.warning(f"⚠️ 已存在 {variable} 配置, 跳过添加")
            return False
        # 改进点4: 处理文件末尾空行后追加.
        if content:
            last_char = content[-1]
            entry = entry if last_char == "\n" else "\n" + entry.lstrip("\n")

        with BASHRC_PATH.open("a", encoding="utf-8") as f:
            f.write(entry)
        logger.info(f"✅ 成功添加 {variable} 到 {BASHRC_PATH}")
    except OSError as e:
        msg = f"❌ 操作失败: [red]{e.__class__.__name__}: {e}"
        logger.exception(msg)
        return False
    else:
        return True


def setup_uv(*, override: bool = True) -> None:
    logger.info("配置 [purple bold]uv 环境变量")

    uv_envs = {
        "UV_INDEX_URL": "http://mirrors.aliyun.com/pypi/simple/",
        "UV_DEFALT_INDEX": "http://mirrors.aliyun.com/pypi/simple/",
        "UV_HTTP_TIMEOUT": 60,
        "UV_LINK_MODE": "copy",
    }

    if cli.is_windows:
        for k, v in uv_envs.items():
            cli.run_cmd(["setx", str(k), str(v)])
    else:
        for k, v in uv_envs.items():
            add_env_to_bashrc(str(k), str(v), override=override)


def setup_hatch_token(
    token: str,
    *,
    override: bool = True,
) -> None:
    """永久配置 Hatch 的 PyPI Token.

    :param token: PyPI API Token (格式: pypi-xxxxxxxx)
    """
    hatch_envs = {
        "HATCH_INDEX_USER": "__token__",
        "HATCH_INDEX_AUTH": token,
    }
    if cli.is_windows:
        for k, v in hatch_envs.items():
            cli.run_cmd(["setx", str(k), str(v)])
    else:
        for k, v in hatch_envs.items():
            add_env_to_bashrc(str(k), str(v), override=override)


def setup_pip() -> None:
    pip_dir = cli.home / "pip" if cli.is_windows else cli.home / ".pip"
    pip_conf = pip_dir / "pip.ini" if cli.is_windows else pip_dir / "pip.conf"

    if not pip_dir.exists():
        logger.info(f"创建 pip 文件夹: [green bold]{pip_dir}")
        pip_dir.mkdir(parents=True)
    else:
        logger.info(f"已存在 pip 文件夹: [green bold]{pip_dir}")

    _set_chmod(pip_conf)

    logger.info(f"写入文件: [green bold]{pip_conf}")
    pip_conf.write_text(PIP_CONF_CONTENT)


@cli.app.command()
def main(
    pypi_token: Annotated[str, Option(help="pypi token")] = "",
    *,
    override: Annotated[bool, Option(help="是否覆盖已存在选项")] = True,
) -> None:
    setup_pip()
    setup_uv(override=override)

    if pypi_token:
        logger.info("设置 [purple bold]pypi token")
        setup_hatch_token(pypi_token, override=override)
