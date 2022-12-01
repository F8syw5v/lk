#!/usr/bin/python3
# -- coding: utf-8 --
# -------------------------------
# @Author : github@limoruirui https://github.com/limoruirui
# @Time : 2022/9/12 16:10
# -------------------------------
# cron "1 12 * * *"
# const $ = new Env('电信签到兑换话费');
"""
1. 电信签到 不需要抓包 脚本仅供学习交流使用, 请在下载后24h内删除
2. 环境变量说明:
    必须  TELECOM_PHONE : 电信手机号
    选填  TELECOM_FOOD  : 给宠物喂食次数 默认为0 不喂食 根据用户在网时长 每天可以喂食5-9次
3. 必须登录过 电信营业厅 app的账号才能正常运行
"""
import threading
from os import environ
from datetime import date, datetime

from time import sleep
from random import randint, uniform,shuffle

from json import dumps
from requests import get, post
from base64 import b64encode

from tools.aes_encrypt import AES_Ctypt
from tools.rsa_encrypt import RSA_Encrypt
from tools.tool import timestamp, get_environ, print_now
from tools.send_msg import push
from sendNotify import send


phone_nums = environ.get("TELECOM_PHONE") if environ.get("TELECOM_PHONE") else ""
foods = int(float(get_environ("TELECOM_FOOD", 5, False)))
if phone_nums.find('\n') != -1:
    phone_numArr = phone_nums.split('\n')
else:
    phone_numArr = phone_nums


class ChinaTelecom:
    def __init__(self, phone):
        self.phone = phone

    def init(self):
        self.msg = ""
        self.headers = {
            "Host": "wapside.189.cn:9001",
            "Referer": "https://wapside.189.cn:9001/resources/dist/signInActivity.html",
            "User-Agent": f"CtClient;9.5.1;Android;12;SM-G9860;{b64encode(self.phone[5:11].encode()).decode().strip('=+')}!#!{b64encode(self.phone[0:5].encode()).decode().strip('=+')}"
        }
        self.key = "-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC+ugG5A8cZ3FqUKDwM57GM4io6\nJGcStivT8UdGt67PEOihLZTw3P7371+N47PrmsCpnTRzbTgcupKtUv8ImZalYk65\ndU8rjC/ridwhw9ffW2LBwvkEnDkkKKRi2liWIItDftJVBiWOh17o6gfbPoNrWORc\nAdcbpk2L+udld5kZNwIDAQAB\n-----END PUBLIC KEY-----"

    def req(self, url, method, data=None):
        if method == "GET":
            data = get(url, headers=self.headers).json()
            return data
        elif method.upper() == "POST":
            data = post(url, headers=self.headers, json=data).json()
            return data
        else:
            print_now("您当前使用的请求方式有误,请检查")

    # 长明文分段rsa加密
    def telecom_encrypt(self, text):
        if len(text) <= 32:
            return RSA_Encrypt(self.key).encrypt(text)
        else:
            encrypt_text = ""
            for i in range(int(len(text) / 32) + 1):
                split_text = text[(32 * i):(32 * (i + 1))]
                encrypt_text += RSA_Encrypt(self.key).encrypt(split_text)
            return encrypt_text

    # 签到
    def chech_in(self):
        url = "https://wapside.189.cn:9001/jt-sign/api/home/sign"
        data = {
            "encode": AES_Ctypt("34d7cb0bcdf07523").encrypt(
                f'{{"phone":{self.phone},"date":{timestamp()},"signSource":"smlprgrm"}}')
        }
        print_now(self.req(url, "post", data))

    # 获取任务列表
    def get_task(self):
        url = "https://wapside.189.cn:9001/jt-sign/paradise/getTask"
        data = {
            "para": self.telecom_encrypt(f'{{"phone":{self.phone}}}')
        }
        msg = self.req(url, "post", data)
        # print_now(dumps(msg, indent=2, ensure_ascii=False))
        if msg["resoultCode"] == "0":
            self.task_list = msg["data"]
        else:
            print_now("获取任务列表失败")
            print_now(msg)
            return

    # 做每日任务
    def do_task(self):
        url = "https://wapside.189.cn:9001/jt-sign/paradise/polymerize"
        for task in self.task_list:
            if "翻牌抽好礼" in task["title"] or "查看我的订单" in task["title"] or "查看我的云盘" in task["title"]:
                print_now(f'{task["title"]}----{task["taskId"]}')
                decrept_para = f'{{"phone":"{self.phone}","jobId":"{task["taskId"]}"}}'
                data = {
                    "para": self.telecom_encrypt(decrept_para)
                }
                data = self.req(url, "POST", data)
                if data["data"]["code"] == 0:
                    # print(data["resoultMsg"])
                    print_now(data)
                else:
                    print_now(f'聚合任务完成失败,原因是{data["resoultMsg"]}')

    # 给宠物喂食
    def food(self):
        url = "https://wapside.189.cn:9001/jt-sign/paradise/food"
        data = {
            "para": self.telecom_encrypt(f'{{"phone":{self.phone}}}')
        }
        res_data = self.req(url, "POST", data)
        if res_data["resoultCode"] == "0":
            print_now(res_data["resoultMsg"])
        else:
            print_now(f'聚合任务完成失败,原因是{res_data["resoultMsg"]}')

    # 查询宠物等级
    def get_level(self):
        url = "https://wapside.189.cn:9001/jt-sign/paradise/getParadiseInfo"
        body = {
            "para": self.telecom_encrypt(f'{{"phone":{self.phone}}}')
        }
        data = self.req(url, "POST", body)
        self.level = int(data["userInfo"]["paradiseDressup"]["level"])
        if self.level < 5:
            print_now("当前等级小于5级 不领取等级权益")
            return
        url = "https://wapside.189.cn:9001/jt-sign/paradise/getLevelRightsList"
        right_list = self.req(url, "POST", body)[f"V{self.level}"]
        for data in right_list:
            # print(dumps(data, indent=2, ensure_ascii=0))
            if "00金豆" in data["righstName"] or "话费" in data["righstName"]:
                rightsId = data["id"]
                self.level_ex(rightsId)
                continue
        # print(self.rightsId)

    # 每月领取等级金豆
    def level_ex(self, rightsId):
        # self.get_level()
        url = "https://wapside.189.cn:9001/jt-sign/paradise/conversionRights"
        data = {
            "para": self.telecom_encrypt(f'{{"phone":{self.phone},"rightsId":"{rightsId}"}},"receiveCount":1')
        }
        print_now(self.req(url, "POST", data))

    # 查询连续签到天数
    def query_signinfo(self):
        url = "https://wapside.189.cn:9001/jt-sign/reward/activityMsg"
        body = {
            "para": self.telecom_encrypt(f'{{"phone":{self.phone}}}')
        }
        #print(self.telecom_encrypt(f'{{"phone":{self.phone}}}'))
        data = self.req(url, "post", body)
        # print(dumps(data, indent=2, ensure_ascii=0))
        
        if 'recordNum' in data:
            recordNum = data["recordNum"]
            totalday = data['totalDay']
            print(f'当前可兑换次数：{recordNum}')
            print(f'当前已签到天数：{totalday}')
            self.msg += f'当前可兑换次数：{recordNum}\n当前已签到天数：{totalday}\n'
            if recordNum != 0:
                print('准备去兑换话费。。。')
                return data["date"]["id"]
            return ""
        else:
            print('接口未返回正确数据')
            print('尝试使用固定id兑换')
            print(data)
            return "baadc927c6ed4d8a95e28fa3fc68cb9"

    # 若连续签到为7天 则兑换
    def convert_reward(self):
        url = "https://wapside.189.cn:9001/jt-sign/reward/convertReward"
        rewardId = self.query_signinfo()  # "baadc927c6ed4d8a95e28fa3fc68cb9"
        if rewardId == "":
            print('不兑换，退出')
            return
        body = {
            "para": self.telecom_encrypt(
                f'{{"phone":"{self.phone}","rewardId":"{rewardId}","month":"{date.today().__format__("%Y%m")}"}}')
        }
        for i in range(12):
            data = self.req(url, "post", body)
            print_now(data)
            if data["code"] == "0":
                break
            if '已完成兑换' in data['msg'] or '成功' in data['msg'] or  '点以后开始兑换' in data['msg']:
                break
            sleep(8)
        rewardId = self.query_signinfo()
        if rewardId == "":
            self.msg += f"账号{self.phone}连续签到7天兑换话费成功\n"
            print_now(self.msg)
        else:
            self.msg += f"账号{self.phone}连续签到7天兑换话费失败 明天会继续尝试兑换\n"
            print_now(self.msg)


    # 查询金豆数量
    def coin_info(self):
        url = "https://wapside.189.cn:9001/jt-sign/api/home/userCoinInfo"
        data = {
            "para": self.telecom_encrypt(f'{{"phone":{self.phone}}}')
        }
        self.coin_count = self.req(url, "post", data)
        print_now(self.coin_count)

    def main(self):
        self.init()
        self.coin_info()
        '''
        self.chech_in()
        self.get_task()
        self.do_task()
        print('aaaa'+str(foods))
        if self.coin_count['totalCoin'] > 2000:
            print('开始喂食。。。')
            for i in range(foods):
                self.food()
                '''
        self.convert_reward()
        '''
        if datetime.now().day == 1:
            self.get_level()
            '''
        self.coin_info()
        print(f"账号{self.phone} 当前有金豆{self.coin_count['totalCoin']}")
        self.msg += f"账号{self.phone} 当前有金豆{self.coin_count['totalCoin']}"
        #print(self.msg + '\n\n')
        #return self.msg + '\n\n'
        push("电信app签到", self.msg)




if __name__ == "__main__":
    print('共' + str(len(phone_numArr)) + '个账户')
    c = 0
    l = []
    msg = ''
    #shuffle(phone_numArr)
    print(phone_numArr)
    u = []
    for i in phone_numArr:
        #c = c + 1
        #print('\n账户' + str(c) + '：' + str(i) + '\n')
        u.append(
            threading.Thread(target=ChinaTelecom(i.split('@')[0]).main)
        )
    for thread in u:
        thread.start()
    for thread in u:
        thread.join()
        

    exit(0)
    
