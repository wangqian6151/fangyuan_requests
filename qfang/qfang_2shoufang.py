import json
import os
import random
import time

import redis
import requests
import pymongo
from bs4 import BeautifulSoup
from pyquery import PyQuery as pq

from qfang.html_from_url import html_from_uri, html_from_url

r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)


class Model():
    """
    基类, 用来显示类的信息
    """
    db = pymongo.MongoClient()['Qfang2Shou']

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
        self.layout = ''
        self.area = ''
        self.decoration = ''
        self.floor = ''
        self.orientation = ''
        self.build_year = ''
        self.district = ''
        self.location = ''
        self.community = ''
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
        address = '深圳' + self.district + self.location.split('二')[0] + self.community
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
    # time.sleep(random.randint(2, 3))
    e = pq(li)

    h = House()
    h.title = e('.house-title').find('a').text().strip()
    h.url = 'https://shenzhen.qfang.com' + e('.house-title').find('a').attr('href')
    h.total_price = e('.sale-price').text()
    h.unit_price = e('.show-price').find('p').text()
    h.img = e('img').attr('data-original').strip()
    h.layout = e('.house-about').find('span').eq(1).text()
    h.area = e('.house-about').find('span').eq(3).text()
    h.decoration = e('.house-about').find('span').eq(5).text()
    h.floor = e('.house-about').find('span').eq(7).text().strip()
    h.orientation = e('.house-about').find('span').eq(9).text()
    h.build_year = e('.house-about').find('span').eq(11).text()
    h.district = e('.whole-line').find('a').eq(0).text()
    h.location = e('.whole-line').find('a').eq(1).text()
    h.community = e('.whole-line').find('a').eq(2).text()
    h.getlocation()
    h.number = h.url.split('/')[-1].split('?')[0]
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
    page = html_from_url(url)
    e = pq(page)
    items = e('#cycleListings>ul>li')
    print('houses_from_url items:{}'.format(len(items)))
    # 调用 house_from_li
    houses = []
    for i in items:
        e = pq(i)
        if not e('.house-title a').attr('href'):
            print("e('.house-title a').attr('href') {}".format(e('.house-title a').attr('href')))
            return houses_from_url(url)
        houses.append(house_from_li(i))
    # houses = [house_from_li(i) for i in items]
    return houses


def get_url(starturl):
    page = html_from_url(starturl)
    e = pq(page)
    totalurl = ['https://shenzhen.qfang.com' + pq(a).attr('href') for a in e(".search-area-detail a")[1:]]
    print('totalurl 1:{}'.format(totalurl))
    for url in totalurl[:]:
        print('for url in totalurl:{}'.format(url))
        time.sleep(random.randint(2, 5))
        page = html_from_url(url)
        e = pq(page)
        totalurl += ['https://shenzhen.qfang.com' + pq(a).attr('href') for a in e(".search-area-second a")]
        print('totalurl 2:{}'.format(totalurl))
    totalurl += [starturl]
    r.set('totalurl_qfang2', json.dumps(totalurl))
    return totalurl


def main():
    starturl = 'https://shenzhen.qfang.com/sale/'
    if r.exists('totalurl_qfang2'):
        print('r.exists(totalurl_qfang2):{}'.format(r.exists('totalurl_qfang2')))
        totalurl = json.loads(r.get('totalurl_qfang2'))
    else:
        totalurl = get_url(starturl)
    print(totalurl)
    halltype = ['b1', 'b2', 'b3', 'b4', 'b5', 'b6']
    for u in totalurl:
        for ht in halltype:
            baseurl = u + '/' + ht
            time.sleep(random.randint(2, 5))
            print('baseurl :{}'.format(baseurl))
            basepage = html_from_url(baseurl)
            e = pq(basepage)
            maxpage = 0
            if e('.turnpage_num a'):
                maxpage = int(e('.turnpage_num a').eq(-1).text())
            elif 0 < e('#cycleListings>li').length <= 30:
                maxpage = 1
            else:
                print('maxpage in else: {}'.format(maxpage))
                continue
            print('maxpage: {}'.format(maxpage))
            for i in range(1, maxpage + 1):
                url = baseurl + '-f' + str(i)
                time.sleep(random.randint(5, 10))
                houses = houses_from_url(url)
                # print('Q房网二手房源', houses)
    # for i in range(1, 100):
    #     url = 'https://shenzhen.qfang.com/sale/f{}'.format(i)
    #     # time.sleep(random.randint(2, 3))
    #     houses = houses_from_url(url)
    #     print('Q房网二手房源', houses)


if __name__ == '__main__':
    main()
