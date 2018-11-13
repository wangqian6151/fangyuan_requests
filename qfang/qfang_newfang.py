import json
import os
import random
import time

import requests
import pymongo
from bs4 import BeautifulSoup
from pyquery import PyQuery as pq

from qfang.html_from_url import html_from_uri


class Model():
    """
    基类, 用来显示类的信息
    """
    db = pymongo.MongoClient()['QfangNew']

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
        self.unit_price = ''
        self.total_price = ''
        self.img = ''
        self.area = ''
        self.layout = ''
        self.district = ''
        self.location = ''
        self.address = ''
        self.phone = ''
        self.status = ''
        self.type = ''
        self.decoration = ''
        self.time = ''
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
        address = '深圳' + self.district + self.location + self.address
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


def house_from_div(div):
    """
    从一个 div 里面获取到一个房源信息
    """
    # time.sleep(random.randint(2, 3))
    e = pq(div)

    h = House()
    if e('.alias-text').text():
        h.title = e('.house-title').find('a').text().strip() + e('.alias-text').text()
    else:
        h.title = e('.house-title').find('a').text().strip()
    h.url = 'https://shenzhen.qfang.com' + e('.house-title').find('a').attr('href')
    h.status = e('.state-label').text()
    h.unit_price = e('.sale-price').text()
    if e('.show-price').find('p').text():
        h.total_price = e('.show-price').find('p').text()
    h.img = e('img').attr('src').strip()
    h.district = e('.natures').find('span').eq(0).text().split()[0]
    h.location = e('.natures').find('span').eq(0).text().split()[1]
    h.type = e('.natures').find('span').eq(1).text().strip()
    h.decoration = e('.natures').find('span').eq(2).text().strip()
    h.layout = e('.new-house-dsp').find('p').eq(0).text().strip()
    h.area = e('.new-house-dsp').find('p').eq(1).find('span').text()
    h.time = e('.new-house-dsp').find('p').eq(2).text().strip()
    h.address = e('.new-house-dsp').find('p').eq(3).find('span').text().strip()
    h.phone = e('.new-house-phone').text().replace('"', '').strip()
    h.getlocation()
    h.number = h.url.split('/')[-1].split('?')[0]
    h.save()
    return h


def houses_from_url(url):
    """
    从 url 中下载网页并解析出页面内所有的房源
    """
    headers = {
        'user-agent': 'Mozilla / 5.0(Windows NT 10.0;WOW64)'
                      'AppleWebKit / 537.36(KHTML, likeGecko)'
                      'Chrome / 66.0.3359.139'
                      'Safari / 537.36',
    }
    r = requests.get(url, headers=headers)
    page = r.content
    e = pq(page)
    items = e('#newhouse-list').find('li')
    houses = [house_from_div(i) for i in items if pq(i).attr('class') != 'hot-recommend-listings']
    return houses


def main():
    for i in range(1, 11):
        url = 'https://shenzhen.qfang.com/newhouse/list/n{}'.format(i)
        # time.sleep(random.randint(2, 3))
        houses = houses_from_url(url)
        print('Q房网新房源', houses)


if __name__ == '__main__':
    main()
