import requests
import time
import threadpool as thread_pool
from pyquery import PyQuery as pq
import ssl
import gc

cross_files = "cross_shop.txt"
cross_start = 1000000000
shop_list = []

# 读取旧记录
try:
    with open(cross_files, "r+", encoding='utf-8') as f:
        for codes in f.readlines():
            if codes:
                curr_code = codes.split('\t')[0]
                if curr_code.isdigit():
                    tmp_code = int(curr_code)
                    if tmp_code > cross_start:
                        cross_start = tmp_code
        print("数据读取结束")

except IOError:
    with open(cross_files, "a+", encoding='utf-8') as f:
        f.close()


def make_data():
    for i in range(cross_start, 1001000000):
        shop_list.append(i)
    print("数据准备结束")


def run_page(shopId):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36"
    }
    strShopId = str(shopId)
    if shopId < 99999:
        strShopId = strShopId.zfill(6)
    ssl._create_default_https_context = ssl._create_unverified_context
    url = "https://mall.jd.com/index-" + strShopId + ".html"
    time.sleep(3)
    try:
        response = requests.get(url, headers=headers)
        response.encoding = "utf-8"
        doc = pq(response.text)
        shop_name = doc("head > title").text()
        # print(response.text)
        msg = ""
        vender_id = ""
        if len(shop_name) > 0 and '共<span id="J_resCount">0</span>件商品' not in response.text:
            msg = shop_name
            vender_id = doc("#vender_id").val()
            if vender_id and len(vender_id) > 0:
                print(shop_name)
            else:
                msg = '空'
        else:
            msg = '无'
        file_info = str(shopId) + "\t" + str(vender_id) + "\t" + msg
        with open(cross_files, "a+", encoding='utf-8') as w:
            w.write(file_info)
            w.write('\n')

        gc.collect()
    except IOError:
        gc.collect()
        time.sleep(3)
        run_page(shopId)


make_data()

del cross_start
pool = thread_pool.ThreadPool(15)
rt = thread_pool.makeRequests(run_page, shop_list)
[pool.putRequest(req) for req in rt]
pool.wait()
print('Done！')
