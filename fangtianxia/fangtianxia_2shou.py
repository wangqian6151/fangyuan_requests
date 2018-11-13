import json
import random
import re
import time

import redis
import requests
import pymongo
from bs4 import BeautifulSoup
from pyquery import PyQuery as pq

from fangtianxia.html_from_url import html_from_uri, html_from_url

r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)


class Model():
    """
    基类, 用来显示类的信息
    """
    db = pymongo.MongoClient()['Fangtianxia2Shou']

    def __repr__(self):
        name = self.__class__.__name__
        properties = ('{}=({})'.format(k, v) for k, v in self.__dict__.items())
        s = '\n<{} \n  {}>'.format(name, '\n  '.join(properties))
        return s


class House(Model):
    """
    存储房源信息
    """

    def __init__(self):
        self.title = ''
        self.url = ''
        self.total_price = ''
        self.unit_price = ''
        self.community = ''
        self.img = ''
        self.area = ''
        self.layout = ''
        self.orientation = ''
        self.floor = ''
        self.build_year = ''
        self.location = ''
        self.address = ''
        self.distance = ''
        self.lat = ''
        self.lng = ''
        self.precise = 0
        self.confidence = 0
        self.number = ''

    def save(self):
        name = self.__class__.__name__
        print('save', self.__dict__)
        # self.db[name].save(self.__dict__)
        print('mongodb status', self.db[name].find({"number": self.number}).count())
        if self.db[name].find({"number": self.number}).count():  # 如果找到number,则只更新
            self.db[name].update({"number": self.number}, self.__dict__, upsert=True)
        else:  # 如果没有找到number,则插入新的数据
            self.db[name].save(self.__dict__)

    def address_of_location(self):
        address = '深圳' + self.address
        print('address_of_location 1: {}'.format(address))
        b = bytes(address, encoding='utf8')
        if len(b) > 84:  # 地址最多支持84个字节
            # address = bytes.decode(b[:84])
            address = address[:28]
        print('address_of_location 2: {}'.format(address))
        return address

    def getlocation(self):
        address = self.address_of_location()
        url = 'http://api.map.baidu.com/geocoder/v2/'
        output = 'json'
        ak = '12346789445566556655555545455123'#自己的百度ak
        uri = url + '?' + 'address=' + address + '&output=' + output + '&ak=' + ak
        temp = html_from_uri(uri)
        soup = BeautifulSoup(temp, 'lxml')
        print(soup.prettify())
        my_location = json.loads(soup.find('p').text)
        print('my_location: {}'.format(my_location))
        if my_location['status'] == 0:  # 服务请求正常召回
            self.lat = my_location['result']['location']['lat']  # 纬度
            self.lng = my_location['result']['location']['lng']  # 经度
            self.precise = my_location['result']['precise']
            # 位置的附加信息，是否精确查找。1为精确查找，即准确打点；0为不精确，即模糊打点（模糊打点无法保证准确度，不建议使用）。
            self.confidence = my_location['result']['confidence']
            # 可信度，描述打点准确度，大于80表示误差小于100m。该字段仅作参考，返回结果准确度主要参考precise参数。
        print('precise: {},confidence: {},lat: {},lng: {}'.format(self.precise, self.confidence, self.lat, self.lng))
        print('{},{}'.format(self.lat, self.lng))
        print('{},{}'.format(self.lng, self.lat))

    def getaddress(self):
        print('lat : {},lng : {}'.format(self.lat, self.lng))
        print('enter  getaddress: {},{}'.format(self.lat, self.lng))
        url = 'http://api.map.baidu.com/geocoder/v2/'
        output = 'json'
        ak = '12346789445566556655555545455123'#自己的百度ak
        uri = url + '?' + 'location=' + str(self.lat) + ',' + str(
            self.lng) + '&output=' + output + '&pois=1' + '&ak=' + ak
        temp = html_from_uri(uri)
        soup = BeautifulSoup(temp, 'lxml')
        print(soup.prettify())
        my_address = json.loads(soup.find('p').text)
        print('my_address: {}'.format(my_address))
        if my_address['status'] == 0:  # 服务请求正常召回
            address = my_address['result']['formatted_address']
            print('address in getaddress:{}'.format(address))


def house_from_dl(dl):
    """
    从一个 dl 里面获取到一个房源信息
    """
    e = pq(dl)

    # 小作用域变量用单字符
    h = House()
    h.title = e('.tit_shop').text()
    h.total_price = e('.red>b').text()
    h.unit_price = e('.price_right span:last').text().split('元')[0]
    h.img = e('.floatl img').attr('src2')
    h.url = 'http://esf.sz.fang.com' + e('h4 a').attr('href')
    desc = e('.tel_shop').text().split('|')
    print('desc:{}'.format(desc))
    h.layout = desc[0].strip()
    h.area = re.search(r'[1-9]\d*', desc[1].strip())[0]
    h.floor = desc[2].strip()
    if len(desc) == 6:
        h.orientation = desc[3].strip()
        h.build_year = desc[4].strip()
    else:
        h.orientation = ''
        h.build_year = desc[3].strip()
    h.community = e('.add_shop a').text().strip()
    addr = e('.add_shop span').text().split('-')
    print('addr:{}'.format(addr))
    h.location = addr[0]
    h.address = addr[1]
    if e('.bg_none icon_dt'):
        h.distance = e('.bg_none.icon_dt').text()
    h.getlocation()
    h.number = h.url.split('/')[-1].split('.')[0]
    h.save()
    return h


def houses_from_url(url):
    """
    从 url 中下载网页并解析出页面内所有的房源
    """
    # headers = {
    #     'user-agent': 'Mozilla / 5.0(Windows NT 10.0;WOW64)'
    #                   'AppleWebKit / 537.36(KHTML, likeGecko)'
    #                   'Chrome / 66.0.3359.139'
    #                   'Safari / 537.36',
    # }
    # r = requests.get(url, headers=headers)
    # page = r.content
    # url = 'https://sz.lianjia.com/ershoufang/luohuqu/pg72'
    page = html_from_url(url)
    e = pq(page)
    items = e('.shop_list.shop_list_4>dl')
    print('houses_from_url items:{}'.format(len(items)))
    # 调用 house_from_dl
    houses = []
    for i in items:
        e = pq(i)
        print("e.attr('id') {}".format(e.attr('id')))
        if e.attr('id'):
            print("e('h4 a').attr('href') {}".format(e('h4 a').attr('href')))
            if not e('h4 a').attr('href'):
                print("in if e('h4 a').attr('href') {}".format(e('h4 a').attr('href')))
                return houses_from_url(url)
            houses.append(house_from_dl(i))
    # houses = [house_from_li(i) for i in items]
    return houses


def get_url(starturl):
    page = html_from_url(starturl)
    e = pq(page)
    totalurl = ['http://esf.sz.fang.com' + pq(a).attr('href') for a in e("#list_D02_10 ul a")[0:10]]
    print('totalurl 1:{}'.format(totalurl))
    for url in totalurl[:]:
        print('for url in totalurl:{}'.format(url))
        # totalurl.append(url)
        time.sleep(random.randint(2, 5))
        page = html_from_url(url)
        e = pq(page)
        totalurl += ['http://esf.sz.fang.com' + pq(a).attr('href') for a in e(".area_sq ul a")[1:]]
        print('totalurl 2:{}'.format(totalurl))
    r.set('totalurl_fangtianxia2', json.dumps(totalurl))
    return totalurl


def main():
    starturl = 'http://esf.sz.fang.com'
    if r.exists('totalurl_fangtianxia2'):
        print('r.exists(totalurl_fangtianxia2):{}'.format(r.exists('totalurl_fangtianxia2')))
        totalurl = json.loads(r.get('totalurl_fangtianxia2'))
    else:
        totalurl = get_url(starturl)
    print(totalurl)
    halltype = ['g21', 'g22', 'g23', 'g24', 'g25', 'g299']
    for u in totalurl:
        for ht in halltype:
            baseurl = u + ht
            time.sleep(random.randint(2, 5))
            print('baseurl :{}'.format(baseurl))
            basepage = html_from_url(baseurl)
            e = pq(basepage)
            maxpage = 0
            if e('#list_D10_15'):
                maxpage = int(re.search(r'[1-9]\d*', e('#list_D10_15 p:last').text())[0])
                # maxpage = int(e('.PageLink').eq(-1).attr('data-ga-page'))
            # elif 0 < e('#shop-all-list li').length <= 15:
            # elif e('.pager strong').text():
            #     maxpage = 1
            else:
                print('maxpage in else: {}'.format(maxpage))
                continue
            print('maxpage: {}'.format(maxpage))
            for i in range(1, maxpage + 1):
                url = baseurl + '-i3' + str(i)
                time.sleep(random.randint(5, 10))
                houses = houses_from_url(url)
                # print('链家二手房源', houses)
    # for i in range(1, 101):
    #     url = 'https://sz.lianjia.com/ershoufang/pg{}/'.format(i)
    #     houses = houses_from_url(url)
    #     # print('链家二手房源', houses)


if __name__ == '__main__':
    main()