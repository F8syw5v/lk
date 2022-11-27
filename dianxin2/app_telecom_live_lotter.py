#!/usr/bin/python3
# -- coding: utf-8 --
# -------------------------------
# @Author : github@limoruirui https://github.com/limoruirui
# @Time : 2022/11/11 10:42
# -------------------------------
# cron "*/30 10-20 * * *"
# const $ = new Env('某营业厅直播抽奖');
"""
1. 脚本仅供学习交流使用, 请在下载后24h内删除
2. 环境变量说明:
    必须  TELECOM_PHONE : 电信手机号
    必须  TELECOM_PASSWORD : 电信服务密码
3. 必须登录过 电信营业厅 app的账号才能正常运行
"""
import requests
from random import randint, uniform,shuffle, choices
from re import findall
from time import mktime, strptime, strftime, sleep as time_sleep
from requests import post, get
from datetime import datetime
from base64 import b64encode
from os import environ
from tools.tool import timestamp, get_environ
from app_telecom_task import ChinaTelecom
from sendNotify import send
from asyncio import get_event_loop, wait, sleep, run
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
phone_nums = environ.get("TELECOM_PHONE") if environ.get("TELECOM_PHONE") else ""
foods = int(float(get_environ("TELECOM_FOOD", 10, False)))
if phone_nums.find('\n') != -1:
    phone_numArr = phone_nums.split('\n')
else:
    phone_numArr = phone_nums

class TelecomLotter:
    def __init__(self, phone, password):
        self.msg = ''
        self.phone = phone
        chinaTelecom = ChinaTelecom(phone, password)
        chinaTelecom.init()
        chinaTelecom.author()
        self.authorization = chinaTelecom.authorization
        self.ua = chinaTelecom.ua
        self.token = chinaTelecom.token

    def get_action_id(self, liveId):
        url = "https://appkefu.189.cn:8301/query/getWaresList"
        body = {
            "headerInfos": {
                "code": "getWaresList",
                "timestamp": datetime.now().__format__("%Y%m%d%H%M%S"),
                "broadAccount": "",
                "broadToken": "",
                "clientType": "#9.6.1#channel128#samsung SM-G9860#",
                "shopId": "20002",
                "source": "110003",
                "sourcePassword": "Sid98s",
                "token": self.token,
                "userLoginName": self.phone
            },
            "content": {
                "attach": "test",
                "fieldData": {
                    "limit": "",
                    "page": "1",
                    "liveId": liveId
                }
            }
        }
        headers = {
            "User-Agent": self.ua,
            "authorization": self.authorization
        }
        data = post(url, headers=headers, json=body).json()
        try:
            for waresInfo in data["responseData"]["data"]["waresInfos"]:
                print(waresInfo["title"])
                if "转盘" in waresInfo["title"] or "抽奖" in waresInfo["title"]:
                    active_code = findall(r"active_code\u003d(.*?)\u0026", waresInfo["link"])[0]
                    return active_code
            return None
        except:
            return None
    def get_action_id_other(self, liveId):
        def encrypt_phone():
            result = ""
            for i in self.phone:
                result += chr(ord(i) + 2)
            return result
        url = "https://wapmkt.189.cn:8301/query/directSeedingInfo"
        body = {
            "headerInfos": {
                "code": "directSeedingInfo",
                "timestamp": datetime.now().__format__("%Y%m%d%H%M%S"),
                "broadAccount": "",
                "broadToken": "",
                "clientType": "#9.6.1#channel128#samsung SM-G9860#",
                "shopId": "20002",
                "source": "110003",
                "sourcePassword": "Sid98s",
                "token": self.token,
                "userLoginName": self.phone
            },
            "content": {
                "attach": "test",
                "fieldData": {
                    "liveId": liveId,
                    "account": encrypt_phone()
                }
            }
        }
        headers = {
            "User-Agent": self.ua,
            "authorization": self.authorization
        }
        data = post(url, headers=headers, json=body).json()["responseData"]["data"]
        try:
            if data["buoyLink"] is None:
                return None
            active_code = findall(r"active_code\u003d(.*?)\u0026", data["buoyLink"])[0]
            return active_code
        except:
            return None
    async def lotter(self, liveId, period):
        """
        :param liveId: 直播间id
        :param period: 某个参数 暂不明意义 查询直播间信息时会返回
        :return:
        """
        print(f"当前执行的直播间id为{liveId}")
        
        for i in range(1):
            # active_code1 查询直播间购物车中的大转盘活动id
            active_code1 = self.get_action_id(liveId)
            # active_code2 查询直播间非购物车 而是右上角的大转盘活动id
            active_code2 = self.get_action_id_other(liveId)
            if active_code1 is not None or active_code2 is not None:
                break
            print(f"此直播间暂无抽奖活动, 等待10秒后再次查询 剩余查询次数{2 - i}")
            #await sleep(1)
            continue
            
        if active_code1 is None and active_code2 is None:
            print("查询结束 本直播间暂无抽奖活动")
            return
        elif active_code1 is None or active_code2 is None:
            active_code = active_code1 if active_code2 is None else active_code2
            active_code_list = [active_code]
        else:
            active_code_list = [active_code1, active_code2]
        for active_code in active_code_list:
            url = "https://xbk.189.cn/xbkapi/active/v2/lottery/do"
            body = {
                "active_code": active_code,
                "liveId": liveId,
                "period": period
            }
            headers = {
                "User-Agent": self.ua,
                "authorization": self.authorization
            }
            data = post(url, headers=headers, json=body).json()
            print(data)
            if data['data']:
                self.msg += f'\n账户 {self.phone} 抽奖结果：\n'
                self.msg += data['data']['title'] + '\n'
        print(self.msg)
        #await sleep(2)
        if self.msg:
            send("电信app直播间抽奖", self.msg)
            
            #return self.msg


def main(phone, password, live):
    '''
    apiType = 1
    try:
        url = "https://api.ruirui.fun/telecom/getLiveInfo"
        data = get(url, timeout=3).json()
    except:
        try:
            url = "https://raw.githubusercontent.com/limoruirui/Hello-Wolrd/main/telecomLiveInfo.json"
            data = get(url, timeout=3).json()
        except:
            url = "https://xbk.189.cn/xbkapi/lteration/index/recommend/anchorRecommend?provinceCode=01"
            random_phone = f"1537266{randint(1000, 9999)}"
            headers = {
                "referer": "https://xbk.189.cn/xbk/newHome?version=9.4.0&yjz=no&l=card&longitude=%24longitude%24&latitude=%24latitude%24&utm_ch=hg_app&utm_sch=hg_sh_shdbcdl&utm_as=xbk_tj&loginType=1",
                "user-agent": f"CtClient;9.6.1;Android;12;SM-G9860;{b64encode(random_phone[5:11].encode()).decode().strip('=+')}!#!{b64encode(random_phone[0:5].encode()).decode().strip('=+')}"
            }
            data = get(url, headers=headers).json()
            apiType = 2
    #print(data)
    liveListInfo = {}
    allLiveInfo = data.values() if apiType == 1 else data["data"]
    
    allLiveInfo = live
    for liveInfo in allLiveInfo:
        if 1740 > timestamp(True) - int(mktime(strptime(liveInfo["start_time"], "%Y-%m-%d %H:%M:%S"))) + (
                8 - int(strftime("%z")[2])) * 3600 > 0:
            liveListInfo[liveInfo["liveId"]] = liveInfo["period"]
    '''
    liveListInfo = live
    if len(liveListInfo) == 0:
        print("查询结束 没有近期开播的直播间")
    else:
        if len(liveListInfo) >= 1:
            for liveId, period in liveListInfo.items():
                run(TelecomLotter(phone, password).lotter(liveId, period))
                '''
        telecomLotter = TelecomLotter(phone, password)
        all_task = [telecomLotter.lotter(liveId, period) for liveId, period in liveListInfo.items()]
        run(wait(all_task))
        '''


def getroom():
    apiType = 1
    try:
        url = "https://ghproxy.com/https://raw.githubusercontent.com/limoruirui/Hello-World/main/telecomLiveInfo.json"
        data = get(url, timeout=5).json()
    except:
        url = "https://xbk.189.cn/xbkapi/lteration/index/recommend/anchorRecommend?provinceCode=01"
        random_phone = f"1537266{randint(1000, 9999)}"
        headers = {
            "referer": "https://xbk.189.cn/xbk/newHome?version=9.4.0&yjz=no&l=card&longitude=%24longitude%24&latitude=%24latitude%24&utm_ch=hg_app&utm_sch=hg_sh_shdbcdl&utm_as=xbk_tj&loginType=1",
            "user-agent": f"CtClient;9.6.1;Android;12;SM-G9860;{b64encode(random_phone[5:11].encode()).decode().strip('=+')}!#!{b64encode(random_phone[0:5].encode()).decode().strip('=+')}"
        }
        data = get(url, headers=headers).json()
        apiType = 2
    #print(data)
    liveListInfo = {}
    allLiveInfo = data.values() if apiType == 1 else data["data"]
    for liveInfo in allLiveInfo:
        if 1740 > timestamp(True) - int(mktime(strptime(liveInfo["start_time"], "%Y-%m-%d %H:%M:%S"))) + (
                8 - int(strftime("%z")[2])) * 3600 > 0:
            liveListInfo[liveInfo["liveId"]] = liveInfo["period"]
    if len(liveListInfo) == 0:
        print("查询结束 没有近期开播的直播间，退出")
        return ''
    else:
        print('查询到开播直播间\n\n')
        return liveListInfo
        if len(liveListInfo) >= 1:
            for liveId, period in liveListInfo.items():
                run(TelecomLotter(phone, password).lotter(liveId, period))
                '''
        telecomLotter = TelecomLotter(phone, password)
        all_task = [telecomLotter.lotter(liveId, period) for liveId, period in liveListInfo.items()]
        run(wait(all_task))
        '''


if __name__ == "__main__":
    print('共' + str(len(phone_numArr)) + '个账户')
    c = 0
    l = []
    msg = ''
    shuffle(phone_numArr)
    print(phone_numArr)
    print('首先去查询开播直播间。。。')
    live = getroom()
    if not live:
        exit(0)
    for i in phone_numArr:
        c = c + 1
        print('\n账户' + str(c) + '：' + str(i) + '\n')

        if '@' in i and len(i.split('@')[1]) > 4:
            m = ''
            m = main(i.split('@')[0], i.split('@')[1], live)
            if m:
                msg += m
        else:
            print('当前账户未填密码，无法抽奖，退出')
            #msg += ChinaTelecom(i,'').main()

    if msg:
        send("电信app直播间抽奖", msg)
    exit(0)
    

