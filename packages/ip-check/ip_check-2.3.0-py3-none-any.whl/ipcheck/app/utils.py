#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import functools
import ipaddress
import os
import random
from datetime import datetime
import sys
from urllib.parse import urlparse
import requests
from tqdm import tqdm
import re
import socket
import asyncio
import time


class UniqueListAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # 去重并保留顺序
        unique = list(dict.fromkeys(values))
        setattr(namespace, self.dest, unique)

def run_async_in_thread(coro):
    """在子线程中运行 asyncio 协程"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def is_ip_address(ip_str: str):
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip is not None
    except ValueError:
        return False

def parse_url(url: str):
    parsed_url = urlparse(url)
    return parsed_url.hostname, (parsed_url.path + ('?' + parsed_url.query if parsed_url.query else ''))

def is_ip_network(net_str: str):
    try:
        net = ipaddress.ip_network(net_str, strict=False)
        return net is not None
    except ValueError:
        return False


def get_ip_version(ip_str: str):
    ip = ipaddress.ip_address(ip_str)
    return ip.version

def get_net_version(net_str: str):
    net = ipaddress.ip_network(net_str, strict=False)
    return net.version

def is_hostname(name):
    pattern = r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})+$"
    return re.match(pattern, name) is not None

async def async_hostname_lookup(hostname: str, port: int = 80, family=socket.AF_UNSPEC, print_err=False):
    """
    异步解析主机名，支持 A 和 AAAA 记录
    :param hostname: 要解析的域名
    :param port: 端口号
    :param family: 地址族，支持 socket.AF_INET, socket.AF_INET6, 或 socket.AF_UNSPEC（全部）
    :return: List of (family, address)
    """
    loop = asyncio.get_running_loop()
    results = []
    try:
        addr_info = await loop.getaddrinfo(
            host=hostname,
            port=port,
            family=family,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
            flags=socket.AI_ADDRCONFIG
        )
        results = [info[4][0] for info in addr_info]
    except (socket.gaierror, OSError):
        if print_err:
            print(f'resolve {hostname} error!')
    return results

def hostname_lookup(hostname: str, port: int = 80, family=socket.AF_UNSPEC, print_err=False):
    results = []
    try:
        addr_info = socket.getaddrinfo(
            host=hostname,
            port=port,
            family=family,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
            flags=socket.AI_ADDRCONFIG
        )
        results = [info[4][0] for info in addr_info]
    except (socket.gaierror, OSError):
        if print_err:
            print(f'resolve {hostname} error!')
    return results

def get_resolve_ips(hostname, port, family=socket.AF_UNSPEC):
    return hostname_lookup(hostname, port, family)

def is_valid_port(port_str):
    try:
        port = int(port_str)
        return 0 < port <= 65535
    except ValueError:
        return False


def find_txt_in_dir(dir):
    L = []
    if os.path.isdir(dir):
        for f in os.listdir(dir):
            file = os.path.join(dir, f)
            if os.path.isfile(file) and file.endswith('.txt'):
                L.append(file)
    return L

def floyd_sample(n: int, k: int):
    selected = {}
    result = set()
    if n <= k:
        return set(range(n))

    if k > n // 2:
        while len(result) < k:
            result.add(random.randint(0, n - 1))
    else:
        for i in range(n - k, n):
            r = random.randint(0, i)
            val = selected.get(r, r)
            selected[r] = selected.get(i, i)
            result.add(val)

    return result

# 通过指定目标list 大小, 从src_list 生成新的list
def adjust_list_by_size(src_list: list, target_size):
    if (target_size > len(src_list)):
        return src_list
    if target_size < 2 ** 32:
        return random.sample(src_list, target_size)
    else:
        total_size = len(src_list)
        indexes = floyd_sample(total_size, target_size)
        return [src_list[i] for i in indexes]


def gen_time_desc():
    current_time = datetime.now()
    # 格式化时间为字符串, 精确到秒
    return '{}: {}'.format('生成时间为', current_time.strftime("%Y-%m-%d %H:%M:%S"))

def show_freshable_content(content: str):
    print(content, end='\r')
    sys.__stdout__.flush()

def write_file(content: str, path: str):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def download_file(url, path, proxy):
    # 发起请求并获取响应对象
    print('下载代理为: {}'.format(proxy))
    proxies = {}
    if proxy:
        proxies = {
            'http': proxy,
            'https': proxy
        }
    session = requests.Session()
    session.mount('https://', adapter=requests.adapters.HTTPAdapter(max_retries=5))
    try:
        with session.get(url, stream=True, timeout=10, proxies=proxies) as response:
            total_size = int(response.headers.get('content-length', 0))  # 获取文件总大小
            # 使用 tqdm 来显示进度条
            with open(path, 'wb') as file, tqdm(
                desc=path,
                total=total_size,
                unit='K',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(chunk_size=1024):
                    # 写入文件并更新进度条
                    file.write(data)
                    bar.update(len(data))
                return True
    except Exception:
        return False

def get_json_from_net(url: str, proxy=None):
    res = {}
    print('请求代理为: {}'.format(proxy))
    proxies = {}
    if proxy:
        proxies = {
            'http': proxy,
            'https': proxy
        }
    session = requests.Session()
    session.mount('https://', adapter=requests.adapters.HTTPAdapter(max_retries=5))
    try:
        with session.get(url, stream=True, timeout=10, proxies=proxies) as r:
            res = r.json()
    except:
        pass
    return res

def get_current_ts() -> float:
    return time.time()

def get_perfcounter() -> float:
    return time.perf_counter()

def sleep_secs(secs: float):
    time.sleep(secs)

def get_family_addr(host, port):
    family = None
    sockaddr = None
    try:
        addr_info = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        family, _, _, _, sockaddr = addr_info[0]
    except:
        pass
    return family, sockaddr

def singleton(cls):
    """
    将一个类作为单例
    来自 https://wiki.python.org/moin/PythonDecoratorLibrary#Singleton
    """

    cls.__new_original__ = cls.__new__

    @functools.wraps(cls.__new__)
    def singleton_new(cls, *args, **kw):
        it = cls.__dict__.get('__it__')
        if it is not None:
            return it

        cls.__it__ = it = cls.__new_original__(cls, *args, **kw)
        it.__init_original__(*args, **kw)
        return it

    cls.__new__ = singleton_new
    cls.__init_original__ = cls.__init__
    cls.__init__ = object.__init__

    return cls