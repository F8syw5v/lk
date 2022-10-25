'''

cron: 6 14 * * * ct_haluo.py
new Env('哈啰签到');

'''


import requests
import os

from sendNotify import send
from os import environ

url = "https://api.hellobike.com/api?common.welfare.signAndRecommend="
# URL+参数,参数值为空

headers = {
    'Host': 'api.hellobike.com',
'Content-Type': 'application/json',
'Origin': 'https://m.hellobike.com',
'Accept-Encoding': 'gzip, deflate, br',
'Connection': 'keep-alive',
'requestId': '3D4Oa5WsvTouceD',
'Accept': 'application/json, text/plain, */*',
'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148; app=easybike; version=6.25.0',
'Referer': 'https://m.hellobike.com/AppPlatformH5/latest/pr_index_bounty.html',
'Content-Length': '147',
'Accept-Language': 'zh-cn',
}
# 请求体headers参数

data = '{"platform" : 4,  "version" : "6.25.0",  "action" : "common.welfare.signAndRecommend",  "systemCode" : 61,  "token" : "bd8ce7b5659a4997b2a4d3a1f7a413f9",  "from" : "h5"}'
# 请求体Text内容，'全部内容'

response = requests.post(url=url, headers = headers, data = data).json()
# 使用post请求执行并把内容赋值给response变量
# print(response.text)
# 打印响应参数Text全部内容
rep = response['data']['bountyCountToday']
print("获得奖励金:", rep)
title = "哈啰签到通知"
content = "获得奖励金: " + rep
send(title,content)
