import os
import random
import time
import redis
import requests
import pymongo
from bs4 import BeautifulSoup
import json
from pyquery import PyQuery as pq
from tongcheng.location import sz_area
from tongcheng.html_from_url import html_from_url, html_from_uri

r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)


class Model():
    """
    基类, 用来显示类的信息
    """
    db = pymongo.MongoClient()['582Shou']

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
        self.district = ''
        self.location = ''
        self.lat = ''
        self.lng = ''
        self.precise = 0
        self.confidence = 0
        self.time = ''
        self.number = ''

    def save(self):
        name = self.__class__.__name__
        print('save', self.__dict__)
        # self.db[name].save(self.__dict__)
        # print(self.db[name].find({"number": self.number}).count())
        print('mongodb status', self.db[name].find({"number": self.number}).count())
        if self.db[name].find({"number": self.number}).count():  # 如果找到number,则只更新
            self.db[name].update({"number": self.number}, self.__dict__, upsert=True)
        else:  # 如果没有找到number,则插入新的数据
            self.db[name].save(self.__dict__)

    def address_of_location(self):
        address = '深圳' + self.district + self.location + self.community
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
    # time.sleep(random.randint(3, 5))
    e = pq(li)

    # 小作用域变量用单字符
    h = House()
    h.title = e('.title').find('a').text().strip()
    h.url = e('.title').find('a').attr('href')
    h.total_price = e('.sum').find('b').text()
    h.unit_price = e('.unit').text()
    h.time = e('.time').text()
    h.img = e('img').attr('data-src')
    h.layout = e('.baseinfo').eq(0).find('span').eq(0).text()
    h.area = e('.baseinfo').eq(0).find('span').eq(1).text()
    h.orientation = e('.baseinfo').eq(0).find('span').eq(2).text()
    h.floor = e('.baseinfo').eq(0).find('span').eq(3).text()
    h.community = e('.baseinfo').eq(1).find('a').eq(0).text()
    h.district = e('.baseinfo').eq(1).find('a').eq(1).text().strip()
    h.location = e('.baseinfo').eq(1).find('a').eq(2).text()
    h.getlocation()
    h.number = h.url.split('/')[-1].split('.')[0]
    h.save()
    return h


def houses_from_url(url):
    """
    从 url 中解析出页面内所有的房源
    """
    # url = 'http://sz.58.com/ershoufang/e1i1/pn27'
    page = html_from_url(url)
    # print('page:{}'.format(page))
    e = pq(page)
    items = e('.house-list-wrap').find('li')
    print('houses_from_url items:{}'.format(len(items)))
    # 调用 house_from_li
    houses = []
    for i in items:
        e = pq(i)
        if not e('.title a').attr('href'):
            print("e('.title a').attr('href') {}".format(e('.title a').attr('href')))
            return houses_from_url(url)
        houses.append(house_from_li(i))
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
    totalurl = ['http://sz.58.com' + pq(a).attr('href') for a in e('#qySelectFirst a')]
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
        totalurl += ['http://sz.58.com' + pq(a).attr('href') for a in e('#qySelectSecond a')]
        print('totalurl 2:{}'.format(totalurl))
        # for u in e('#qySelectSecond a').attr('href'):
        #     u = 'http://sz.58.com' + u
        #     print('u : {}'.format(u))
        #     totalurl.append(u)
    r.set('totalurl', json.dumps(totalurl))
    return totalurl


def main():
    starturl = 'http://sz.58.com/ershoufang/'
    if r.exists('totalurl'):
        print('r.exists(totalurl):{}'.format(r.exists('totalurl')))
        totalurl = json.loads(r.get('totalurl'))
    else:
        totalurl = get_url(starturl)
    print(totalurl)
    halltype = ['e1', 'e2', 'e3', 'e4', 'e5']
    pricetype = ['i1', 'i2', 'i3', 'i4', 'i5', 'i6', 'i7', 'i8', 'i9']
    for u in totalurl[::-1]:
        for ht in halltype:
            for pt in pricetype:
                baseurl = u + ht + pt + '/'
                time.sleep(random.randint(2, 5))
                print('baseurl :{}'.format(baseurl))
                basepage = html_from_url(baseurl)
                e = pq(basepage)
                maxpage = 0
                if e('.pager a').text():
                    maxpage = int(e('.pager a').eq(-2).text())
                    # maxpage = int(e('.PageLink').eq(-1).attr('data-ga-page'))
                # elif 0 < e('#shop-all-list li').length <= 15:
                elif e('.pager strong').text():
                    maxpage = 1
                else:
                    print('maxpage in else: {}'.format(maxpage))
                    continue
                print('maxpage: {}'.format(maxpage))
                for i in range(1, maxpage + 1):
                    url = baseurl + 'pn' + str(i)
                    time.sleep(random.randint(5, 10))
                    houses = houses_from_url(url)
                    # print('58二手房源', houses)


if __name__ == '__main__':
    main()
