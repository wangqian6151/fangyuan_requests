import json
import os
import random
import time

import requests
import pymongo
from bs4 import BeautifulSoup
from pyquery import PyQuery as pq

from anjuke.html_from_url import html_from_uri, html_from_url


class Model():
    """
    基类, 用来显示类的信息
    """
    db = pymongo.MongoClient()['AnjukeNew']

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
        self.no_price = ''
        self.price = ''
        self.img = ''
        self.area = ''
        self.layout = ''
        self.district = ''
        self.location = ''
        self.address = ''
        self.phone = ''
        self.comment = ''
        self.status = ''
        self.type = ''
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
        address = '深圳' + self.district + self.location + self.address + self.title
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
    time.sleep(random.randint(2, 3))
    e = pq(div)

    h = House()
    h.title = e('.items-name').text()
    h.url = e('.lp-name').attr('href')
    if e('.price-txt').text():
        h.no_price = e('.price-txt').text()
    if e('.price').text():
        h.price = e('.price').text()
    if e('.around-price').text():
        h.price = e('.around-price').text()
    # print('h.price :', h.price)
    h.phone = e('.tel').text()
    h.comment = e('.list-dp').text()
    h.img = e('img').attr('src')
    length = e('.huxing').children('span').length
    h.layout = '/'.join(e('.huxing').find('span').eq(i).text() for i in range(0, length - 1))
    h.area = e('.huxing').find('span').eq(-1).text()
    comm_address = e('.list-map').text().strip().replace('&nbsp;', '').split()
    # print('comm_address :', comm_address)
    h.district = comm_address[1]
    h.location = comm_address[2]
    h.address = comm_address[-1]
    h.status = e('.tag-panel').find('i').eq(0).text()
    h.type = e('.tag-panel').find('i').eq(1).text()
    h.getlocation()
    h.number = h.url.split('/')[-1].split('.')[0]
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

    r = requests.get(url, headers=headers)
    page = r.content
    e = pq(page)
    items = e('.key-list').find('.item-mod')
    houses = [house_from_div(i) for i in items]
    return houses


def main():
    current_url = 'https://sz.fang.anjuke.com/loupan/'
    print('current_url 1:{}'.format(current_url))
    page_num = 1
    while True:
        time.sleep(random.randint(2, 5))
        # current_page = html_from_url(current_url)
        current_page = requests.get(current_url, headers=headers).content
        e = pq(current_page)
        # if not e('.key-list .item-mod').text():
        #     print('0000000000000 page')
        #     break
        # elif not e('.next-link') and not e('.stat-disable'):
        #     houses_from_url(current_url)
        #     print('1111111111111 page')
        #     break
        # else:
        print('current_url 2:{}'.format(current_url))
        houses_from_url(current_url)
        if e('.next-page.stat-disable'):
            print('222222222222 page')
            print('page_num : {}'.format(page_num))
            break
        current_url = e('.next-link').attr('href')
        page_num += 1
        print('current_url 3:{}'.format(current_url))
    # for i in range(1, 25):
    #     url = 'https://sz.fang.anjuke.com/loupan/all/p{}/'.format(i)
    #     time.sleep(random.randint(2, 3))
    #     houses = houses_from_url(url)
    #     print('安居客新房源', houses)


if __name__ == '__main__':
    main()
