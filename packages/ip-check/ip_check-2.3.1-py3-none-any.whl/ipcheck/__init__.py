#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import importlib_metadata
from enum import Enum, auto


metadata = importlib_metadata.metadata("ip-check")
__version__ = metadata['version']

# ip-check constants
IP_CHECK_DEFAULT_CONFIG = '''# 通用配置
[common]
# 测试端口
ip_port = 443
# 是否存储结果到文件
no_save = False
# cidr 抽样个数
cidr_sample_ip_num = 16

# 可用性检查配置
[valid test]
# 是否测试可用性
enabled = True
# 限制参与valid 测试的ip 数量
ip_limit_count = 100000
# 可用性检测域名
host_name = cloudflare.com
# 使用user-agent
user_agent = False
# 可用性检测路径, 固定的, 取决于cloudflare
path = /cdn-cgi/trace
# 可用性测试多线程数量
thread_num = 64
# 可用性测试时的网络请求重试次数
max_retry = 2
# retry, backoff_factor
retry_factor = 0.3
# 可用性测试的网络请求timeout, 单位 s
timeout = 1.5
# 可用性测试检测的key
check_key = h

# rtt 测试配置
[rtt test]
enabled = True
# 限制参与rtt 测试的ip 数量
ip_limit_count = 100000
# rtt tcpping 间隔
interval = 0.01
# rtt 测试多线程数量
thread_num = 32
# rtt 测试的网络请求timeout, 单位 s
timeout = 0.5
# rtt 测试的延时及格值, 单位 ms
max_rtt = 300
# rtt 测试次数
test_count = 10
# 最大丢包率控制, 单位 百分比
max_loss = 100
# 是否开启快速测试
fast_check = False

# 下载速度测试配置
[speed test]
# 是否开启速度测试
enabled = True
# 限制参与速度测试的ip 数量
ip_limit_count = 100000
# 测试下载文件的url
url = https://speed.cloudflare.com/__down?bytes=500000000
# 使用user-agent
user_agent = False
# 测试下载文件的重试次数
max_retry = 10
# retry, backoff_factor
retry_factor = 0.3
# 下载测试网络请求timeout, 单位 s
timeout = 5
# 下载时长限制, 单位 s
download_time = 10
# 最小达标速度, 单位 kB/s
download_speed = 5000
# 最小平均速度
avg_download_speed = 0
# 是否执行快速测速开关
fast_check = False
# 获取到指定个优选ip 停止
bt_ip_limit = 0
# 是否丢弃测速中途异常ip
rm_err_ip = False'''


USER_AGENTS = [
    # === Windows / Chrome 系列 ===
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',

    # === Windows / Edge 系列 ===
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',

    # === Firefox 系列 ===
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0',

    # === macOS / Safari ===
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',

    # === Android / Chrome ===
    'Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; Samsung Galaxy S22) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 11; Mi 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',

    # === iOS / Safari ===
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',

    # === Opera 浏览器 ===
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 OPR/95.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 OPR/95.0.0.0',

    # === Linux / Chrome ===
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0',
]


# igeo constants
GEO2CITY_DB_NAME = 'GeoLite2-City.mmdb'
GEO2ASN_DB_NAME = 'GeoLite2-ASN.mmdb'
GEO2CITY_DB_PATH = os.path.join(os.path.dirname(__file__), GEO2CITY_DB_NAME)
GEO2ASN_DB_PATH = os.path.join(os.path.dirname(__file__), GEO2ASN_DB_NAME)
GEO_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'geo.ini')
GEO_VERSION_PATH = os.path.join(os.path.dirname(__file__), '.geo_version')
GEO_DEFAULT_CONFIG = '''[common]
# 下载使用代理,格式为 protocol://host:port, 如: socks5://127.0.0.1:1080
proxy =
# asn 数据库下载地址
db_asn_url = https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-ASN.mmdb
# city 数据库下载地址
db_city_url = https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb
# 数据库更新检测API
db_api_url = https://api.github.com/repos/P3TERX/GeoLite.mmdb/releases/latest'''

class WorkMode(Enum):
    IP_CHECK = auto()
    IP_CHECK_CFG = auto()
    IGEO_INFO = auto()
    IGEO_DL = auto()
    IGEO_CFG = auto()
    IP_FILTER = auto()
    DEFAULT = IP_CHECK

class IpcheckStage():
    UNKNOWN = 0
    VALID_TEST = 1
    RTT_TEST = 2
    SPEED_TEST = 3
    TEST_EXIT = 4