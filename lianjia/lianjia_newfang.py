import json
import math
import os
import random
import re
import time

import redis
import requests
import pymongo
from bs4 import BeautifulSoup
from pyquery import PyQuery as pq

from lianjia.html_from_url import html_from_uri, html_from_url

r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)


class Model():
    """
    基类, 用来显示类的信息
    """
    db = pymongo.MongoClient()['LianjiaNew']

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
        self.img = ''
        self.location = ''
        self.community = ''
        self.address = ''
        self.area = ''
        self.type = ''
        self.status = ''
        self.lat = ''
        self.lng = ''
        self.precise = 0
        self.confidence = 0
        self.number = ''

    def save(self):
        name = self.__class__.__name__
        print('save', self.__dict__)
        # self.db[name].save(self.__dict__)
        print(self.db[name].find({"number": self.number}).count())
        if self.db[name].find({"number": self.number}).count():  # 如果找到number,则只更新
            self.db[name].update({"number": self.number}, self.__dict__, upsert=True)
        else:  # 如果没有找到number,则插入新的数据
            self.db[name].save(self.__dict__)

    def address_of_location(self):
        address = '深圳' + self.location + self.community + self.address + self.title
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


def house_from_li(li):
    """
    从一个 li 里面获取到一个房源信息
    """
    e = pq(li)

    h = House()
    h.title = e('.resblock-name').find('a').text()
    h.type = e('.resblock-type').text()
    h.status = e('.sale-status').text()
    url = e('.resblock-name').find('a').attr('href')
    h.url = 'https://sz.fang.lianjia.com' + url
    h.total_price = e('.second').text()
    h.unit_price = e('.number').text()
    h.img = e('.lj-lazy').attr('data-original')
    h.area = e('.resblock-area').find('span').text()
    h.location = e('.resblock-location').find('span').eq(0).text()
    h.community = e('.resblock-location').find('span').eq(1).text()
    h.address = e('.resblock-location').find('a').text()
    h.getlocation()
    h.number = e.attr('data-project-name')
    h.save()
    return h


headers = {
    'user-agent': 'Mozilla / 5.0(Windows NT 10.0;WOW64)'
                  'AppleWebKit / 537.36(KHTML, likeGecko)'
                  'Chrome / 66.0.3359.139'
                  'Safari / 537.36',
    }


def houses_from_url(url):
    """
    从 url 中下载网页并解析出页面内所有的房源
    """
    print('houses_from_url url :{}'.format(url))
    r = requests.get(url, headers=headers)
    page = r.content
    # page = html_from_url(url)
    e = pq(page)
    items = e('.resblock-list-wrapper').find('li')
    # 调用 house_from_li
    houses = []
    for i in items:
        e = pq(i)
        if e.attr('data-project-name') is not None:
            if not e('.resblock-name a').attr('href'):
                print("e('.resblock-name a').attr('href') {}".format(e('.resblock-name a').attr('href')))
                return houses_from_url(url)
            print('before houses.append:{}'.format(i))
            houses.append(house_from_li(i))
            print('after houses.append:{}'.format(i))
            print('\n' * 2)
    # houses = [house_from_li(i) for i in items if pq(i).attr('data-project-name') is not None]
    return houses


def get_url(starturl):
    # page = html_from_url(starturl)
    page = requests.get(starturl, headers=headers).content
    e = pq(page)
    totalurl = [starturl + pq(a).attr('data-district-spell') for a in e(".district-wrapper li")[0:10]]
    print('totalurl 1:{}'.format(totalurl))
    # totalurl = []
    # for url in totalurl[:]:
    #     print('for url in totalurl:{}'.format(url))
    #     # totalurl.append(url)
    #     time.sleep(random.randint(2, 5))
    #     page = html_from_url(url)
    #     e = pq(page)
    #     totalurl += ['https://sz.lianjia.com' + pq(a).attr('href') for a in e("div[data-role='ershoufang'] div:last a")]
    #     print('totalurl 2:{}'.format(totalurl))

    # totalurl += [starturl]
    r.set('totalurl_lianjia_new', json.dumps(totalurl))
    return totalurl


def main():
    starturl = 'https://sz.fang.lianjia.com/loupan/'
    if r.exists('totalurl_lianjia_new'):
        print('r.exists(totalurl_lianjia_new):{}'.format(r.exists('totalurl_lianjia_new')))
        totalurl = json.loads(r.get('totalurl_lianjia_new'))
    else:
        totalurl = get_url(starturl)
    print(totalurl)
    for u in totalurl:
        baseurl = u + '/'
        time.sleep(random.randint(2, 5))
        print('baseurl :{}'.format(baseurl))
        # basepage = html_from_url(baseurl)
        basepage = requests.get(baseurl, headers=headers).content
        e = pq(basepage)
        maxpage = 0
        if e('.page-box'):
            maxpage = math.ceil(float(e('.page-box').attr('data-total-count')) / 10)
            # maxpage = int(e('.PageLink').eq(-1).attr('data-ga-page'))
        # elif 0 < e('#shop-all-list li').length <= 15:
        # elif e('.pager strong').text():
        #     maxpage = 1
        else:
            print('maxpage in else: {}'.format(maxpage))
            continue
        print('maxpage: {}'.format(maxpage))
        for i in range(1, maxpage + 1):
            url = baseurl + 'pg' + str(i)
            time.sleep(random.randint(5, 10))
            houses = houses_from_url(url)
            # print('链家新房源', houses)
    # for i in range(1, 96):
    #     url = 'https://sz.fang.lianjia.com/loupan/pg{}/'.format(i)
    #     houses = houses_from_url(url)
    #     # print('链家新房源', houses)


if __name__ == '__main__':
    main()
