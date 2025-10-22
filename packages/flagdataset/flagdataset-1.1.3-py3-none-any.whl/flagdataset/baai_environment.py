import logging

import pathlib
import platform

import psutil
import requests

from .baai_config import config_update, print_config

logger = logging.getLogger(__name__)

def show_environment(cmd_args):
    try:
        private = "https://baai-datasets.ks3-cn-beijing-internal.ksyuncs.com/public/internal/speed/readme.md"
        requests.get(private, timeout=1)
    except requests.exceptions.ReadTimeout:
        network = "public"
    else:
        network = "private"

    config_data = {
        "network": network,
    }
    config_update(config_data)

    print_config()
    logger.info("show_environment")

    logical_cpus = psutil.cpu_count(logical=True)
    print(f"{platform.platform()}: {psutil.cpu_count(logical=False)}u{logical_cpus}c, {psutil.virtual_memory().total / 1024 ** 3:.0f}G")
    runtime_dir = pathlib.Path.cwd()
    print(f"pwd: {runtime_dir}")
    print(f"disk: {psutil.disk_usage(runtime_dir.__str__()).total / 1024 ** 3:.0f}G")


def setup_environment(cmd_args):
    try:
        private = "https://baai-datasets.ks3-cn-beijing-internal.ksyuncs.com/public/internal/speed/readme.md"
        requests.get(private, timeout=1)
    except requests.exceptions.ReadTimeout:
        network = "public"
    else:
        network = "private"

    config_data = {
        "network": network,
    }
    config_update(config_data)

    show_environment(cmd_args)
