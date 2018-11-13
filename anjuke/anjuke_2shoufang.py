import json
import os
import random
import time
import redis
import requests
import pymongo
from bs4 import BeautifulSoup
from pyquery import PyQuery as pq

from anjuke.html_from_url import html_from_url, html_from_uri

r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)


class Model():
    """
    基类, 用来显示类的信息
    """
    db = pymongo.MongoClient()['Anjuke2Shou']

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
        self.total_price = 0
        self.unit_price = ''
        self.community = ''
        self.img = ''
        self.area = ''
        self.layout = ''
        self.build_year = ''
        self.floor = ''
        self.district = ''
        self.location = ''
        self.address = ''
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
        address = '深圳' + self.district + self.location + self.address + self.community
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

    # 小作用域变量用单字符
    h = House()
    h.title = e('.house-title').find('a').text().strip()
    h.url = e('.house-title').find('a').attr('href')
    h.total_price = float(e('strong').text())
    h.unit_price = e('.unit-price').text()
    h.img = e('img').attr('src')
    h.layout = e('.details-item').eq(0).find('span').eq(0).text()
    h.area = e('.details-item').eq(0).find('span').eq(1).text()
    h.floor = e('.details-item').eq(0).find('span').eq(2).text()
    h.build_year = e('.details-item').eq(0).find('span').eq(3).text()
    comm_address = e('.comm-address').text().strip().replace('&nbsp;', '').split()
    print('comm_address :', comm_address)
    if comm_address:
        h.community = comm_address[0]
        total_adress = comm_address[1].split('-')
        # print('total_adress :', total_adress)
        h.district = total_adress[0]
        h.location = total_adress[1]
        h.address = total_adress[2]
        h.getlocation()
    h.number = h.url.split('/')[-1].split('?')[0]
    h.save()
    return h


def houses_from_url(url):
    """
    从 url 中解析出页面内所有的房源
    """
    # url = 'https://shenzhen.anjuke.com/sale/a31-b36-p3/#filtersort'
    # url = 'https://shenzhen.anjuke.com/sale/a24-b30-p4/#filtersort'
    # url = 'https://shenzhen.anjuke.com/sale/dapengxinqushenzhen-kuiyongw/a29-b37/'
    page = html_from_url(url)
    e = pq(page)
    items = e('.houselist-mod-new li')
    print('houses_from_url items:{}'.format(len(items)))
    # 调用 house_from_li
    houses = []
    for i in items:
        e = pq(i)
        if not e('.house-title a').attr('href'):
            print("e('.house-title a').attr('href'):{}".format(e('.house-title a').attr('href')))
            return houses_from_url(url)
        print('before houses.append:{}'.format(i))
        houses.append(house_from_li(i))
        print('after houses.append:{}'.format(i))
        print('\n' * 2)
    # houses = [house_from_li(i) for i in items]
    return houses


def get_url(starturl):
    page = html_from_url(starturl)
    e = pq(page)
    # bigurl = []
    # for u in e('#qySelectFirst a').attr('href'):
    #     print('1111111111{}'.format(u))
    #     u = 'http://sz.58.com' + u
    #     bigurl.append(u)
    totalurl = ['https://shenzhen.anjuke.com/sale/']
    totalurl += [pq(a).attr('href') for a in e('.items-list .items:first .elems-l a')]
    print('totalurl 1:{}'.format(totalurl))
    # bigurl = [
    #     'http://sz.58.com/luohu/ershoufang/',
    #     'http://sz.58.com/futian/ershoufang/',
    #     'http://sz.58.com/nanshan/ershoufang/',
    #     'http://sz.58.com/yantian/ershoufang/',
    #     'http://sz.58.com/baoan/ershoufang/',
    #     'http://sz.58.com/longgang/ershoufang/',
    #     'http://sz.58.com/buji/ershoufang/',
    #     'http://sz.58.com/pingshanxinqu/ershoufang/',
    #     'http://sz.58.com/guangmingxinqu/ershoufang/',
    #     'http://sz.58.com/szlhxq/ershoufang/',
    #     'http://sz.58.com/dapengxq/ershoufang/',
    #     'http://sz.58.com/shenzhenzhoubian/ershoufang/'
    # ]
    # totalurl = []
    for url in totalurl[1:]:
        print('for url in totalurl:{}'.format(url))
        # totalurl.append(url)
        time.sleep(random.randint(2, 5))
        page = html_from_url(url)
        e = pq(page)
        totalurl += [pq(a).attr('href') for a in e('.items-list .items:first .sub-items a')]
        print('totalurl 2:{}'.format(totalurl))
        # for u in e('#qySelectSecond a').attr('href'):
        #     u = 'http://sz.58.com' + u
        #     print('u : {}'.format(u))
        #     totalurl.append(u)
    r.set('totalurl_anjuke2', json.dumps(totalurl))
    return totalurl


def main():
    starturl = 'https://shenzhen.anjuke.com/sale/'
    if r.exists('totalurl_anjuke2'):
        print('r.exists(totalurl_anjuke2):{}'.format(r.exists('totalurl_anjuke2')))
        totalurl = json.loads(r.get('totalurl_anjuke2'))
    else:
        totalurl = get_url(starturl)
    print(totalurl)
    areatype = ['a24', 'a25', 'a26', 'a27', 'a28', 'a29', 'a30', 'a31', 'a33']
    halltype = ['b28', 'b30', 'b36', 'b37', 'b38', 'b39']
    for url in totalurl:
        for at in areatype:
            for ht in halltype:
                current_url = url + at + '-' + ht + '/'
                print('current_url 1:{}'.format(current_url))
                page_num = 1
                while True:
                    time.sleep(random.randint(2, 5))
                    current_page = html_from_url(current_url)
                    e = pq(current_page)
                    # if e('#houselist-mod-new').children().length == 0:
                    #     print("e('#houselist-mod-new').children().length:{}".format(
                    #         e('#houselist-mod-new').children().length))
                    print("e('.aNxt') : {}".format(e('.aNxt')))
                    if e('.aNxt') or e('.iNxt'):
                        print('current_url 2:{}'.format(current_url))
                        houses_from_url(current_url)
                        if e('.iNxt'):
                            print('222222222222 page')
                            print('page_num : {}'.format(page_num))
                            break
                        current_url = e('.aNxt').attr('href')
                        page_num += 1
                        print('current_url 3:{}'.format(current_url))
                    elif 0 < e('.houselist-mod-new li').length <= 60:
                        print("e('.houselist-mod-new li').length : {}".format(e('.houselist-mod-new li').length))
                        houses_from_url(current_url)
                        print('1111111111111 page')
                        break
                    else:
                        print('0000000000000 page')
                        break
                    # if not e('#houselist-mod-new li').text():
                    #     print('0000000000000 page')
                    #     break
                    # elif not e('.aNxt') and not e('.iNxt'):
                    #     houses_from_url(current_url)
                    #     print('1111111111111 page')
                    #     break
                    # else:
                    #     print('current_url 2:{}'.format(current_url))
                    #     houses_from_url(current_url)
                    #     if e('.iNxt'):
                    #         print('222222222222 page')
                    #         print('page_num : {}'.format(page_num + 1))
                    #         break
                    #     current_url = e('.aNxt').attr('href')
                    #     page_num += 1
                    #     print('current_url 3:{}'.format(current_url))

    # for i in range(1, 51):
    #     url = 'https://shenzhen.anjuke.com/sale/p{}/'.format(i)
    #     time.sleep(random.randint(2, 3))
    #     houses = houses_from_url(url)
    #     print('安居客二手房源', houses)


if __name__ == '__main__':
    main()
