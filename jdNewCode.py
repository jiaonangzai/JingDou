import requests
import time
from selenium import webdriver
import threadpool as thread_pool
from pyquery import PyQuery as pq
import numpy as np
import ssl
import json
import re
import gc
import os

cookie_str = ""
login_success = False
cookie_file = "cookies.txt"
cross_files = "cross_active.txt"
use_shop_files = "new_use_shop.txt"
shop_list = []
cross_start = 10000
total_jd_count = 0

# 读取旧记录
try:
    with open(use_shop_files, "r+", encoding='utf-8') as f:
        for line in f.readlines():
            curr_line = line.strip()
            if curr_line:
                datas = curr_line.split('\t')
                data = {"shop_id": int(datas[0]), "vender_id": int(datas[1])}
                shop_list.append(data)

except IOError:
    with open(use_shop_files, "a+", encoding='utf-8') as f:
        f.close()


# 获取当前时间
def curr_time():
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))


# 登录
def do_login():
    global cookie_str
    # 使用PhantomJS浏览器创建浏览器对象
    browser = webdriver.Chrome('../chromeDriver/chromedriver.exe')
    browser.get("https://passport.jd.com/new/login.aspx?ReturnUrl=http%3A%2F%2Fhome.jd.com%2F")

    # browser.execute_script("$('#passwordid').val('PANGDA123'); $('input[name=\"userCode\"]').val(10000534);");
    # 等待20秒
    time.sleep(20)

    cookies = browser.get_cookies()
    cookies_infos = []

    for cookie in cookies:
        cookies_infos.append(cookie["name"] + "=" + cookie["value"] + ";")

    cookie_str = " ".join(cookies_infos)
    # 拿到cookie 存入文件中
    with open(cookie_file, "w+") as w:
        w.write(cookie_str)
    browser.quit()
    # 重新验证读取cookie
    print("重新验证读取cookie")
    read_cookie()


# 读Cookie
def read_cookie():
    global cookie_str
    global login_success
    # 读取cookie文件
    with open(cookie_file, "r+") as f:
        cookie_str = f.read()

    # cookie 不为空 验证cookie 过期
    if cookie_str:
        headers = {
            "Cookie": cookie_str,
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36",
            "Referer": "https://www.jd.com/"
        }
        response = requests.get("https://home.jd.com/", headers=headers)
        is_expired = re.search("我的京东", response.text)

        if is_expired:
            login_success = True

    # 需要重新登录
    if not login_success:
        print('需要登录')
        do_login()


# 获取活动信息
def get_vender_gift(shop_info):
    shop_str = str(shop_info["shop_id"])
    vender_str = str(shop_info["vender_id"])
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
        "Host": "f-mall.jd.com",
        "Cookie": cookie_str,
        "Referer": "https://mall.jd.com/index-" + shop_str + ".html"
    }
    ssl._create_default_https_context = ssl._create_unverified_context
    url = "https://f-mall.jd.com/shopGift/getShopGiftInfo?venderId=" + vender_str + "&_=" + str(time.time())
    time.sleep(3)
    rs1 = ''
    try:
        rs1 = requests.get(url, headers=headers)
    except IOError:
        return get_vender_gift(shop_info)

    rs1.encoding = "utf-8"
    if "jshop_token" in rs1.text and "giftList" in rs1.text:
        shopGiftInfo = json.loads(rs1.text)
        jshop_token = shopGiftInfo["jshop_token"]
        activityStr = ""
        has_jd = False
        jd_num = 0
        if shopGiftInfo["giftList"]:
            for gift in shopGiftInfo["giftList"]:
                if gift["prizeType"] == 4:
                    has_jd = True
                    jd_num = gift["discount"]
                    activityStr = str(gift["activityId"])

        if has_jd:
            global total_jd_count
            total_jd_count += jd_num
            msg = '有豆子【' + str(jd_num) + '】\t' + curr_time() + "\t共计【" + str(total_jd_count) + "】"
            ssl._create_default_https_context = ssl._create_unverified_context
            url = "https://f-mall.jd.com/shopGift/drawShopGiftInfo?vId=" + vender_str + "&jshop_token=" + jshop_token + "&aId=" + activityStr + "&_=" + str(
                time.time())
            time.sleep(3)
            response = requests.get(url, headers=headers)
            response.encoding = "utf-8"
            file_info = shop_str + "\t" + msg
            with open(cross_files, "a+", encoding='utf-8') as w:
                w.write(file_info)
                w.write('\n')
            print("*************************************************")
            print(file_info)

    # print(gc.get_count())
    gc.collect()
    # print(gc.get_count())


read_cookie()

print("请求中，请耐心等待。。。")


# 随机排列
def make_data():
    np.random.shuffle(shop_list)


make_data()

pool = thread_pool.ThreadPool(20)
rt = thread_pool.makeRequests(get_vender_gift, shop_list)
[pool.putRequest(req) for req in rt]
pool.wait()
print('Done！')
os.system('shutdown -s -t 3')
