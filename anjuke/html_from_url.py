import random
import time
from random import choice
import requests
from lxml import etree
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from requests_html import HTMLSession
from urllib3.util.retry import Retry
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import string
import zipfile

# 代理服务器
proxyHost = "http-dyn.abuyun.com"
proxyPort = "9020"

# 代理隧道验证信息
proxyUser = "H3284R82886KX1YD"
proxyPass = "350E9CA792A1B7BB"


def create_proxy_auth_extension(proxy_host, proxy_port,
                                proxy_username, proxy_password,
                                scheme='http', plugin_path=None):
    if plugin_path is None:
        plugin_path = r'D:/{}_{}@http-dyn.abuyun.com_9020.zip'.format(proxy_username, proxy_password)

    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Abuyun Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = string.Template(
        """
        var config = {
            mode: "fixed_servers",
            rules: {
                singleProxy: {
                    scheme: "${scheme}",
                    host: "${host}",
                    port: parseInt(${port})
                },
                bypassList: ["foobar.com"]
            }
          };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "${username}",
                    password: "${password}"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
        );
        """
    ).substitute(
        host=proxy_host,
        port=proxy_port,
        username=proxy_username,
        password=proxy_password,
        scheme=scheme,
    )

    with zipfile.ZipFile(plugin_path, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    return plugin_path


def html_from_url_selenium(url):
    proxy_auth_plugin_path = create_proxy_auth_extension(
        proxy_host=proxyHost,
        proxy_port=proxyPort,
        proxy_username=proxyUser,
        proxy_password=proxyPass)

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument("--start-maximized")
    # chrome_options.add_extension(proxy_auth_plugin_path)
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get(url)
    html = driver.page_source
    print('driver.page_source:{}'.format(driver.page_source))
    return html


def cookie_from_url(url):
    proxy_auth_plugin_path = create_proxy_auth_extension(
        proxy_host=proxyHost,
        proxy_port=proxyPort,
        proxy_username=proxyUser,
        proxy_password=proxyPass)

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument("--start-maximized")
    # chrome_options.add_extension(proxy_auth_plugin_path)
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get(url)
    cookies = {}
    for cookie in driver.get_cookies():
        cookies.update({cookie['name']: cookie['value']})
    return cookies


# 把浏览器的cookies字符串转成字典
def cookies2dict(cookies):
    items = cookies.split(';')
    d = {}
    for item in items:
        kv = item.split('=', 1)
        k = kv[0]
        v = kv[1]
        d[k] = v
    return d


def html_prase(url):
    r = requests.get(url).content
    return r


# def html_from_url(url):
#     """
#     从 url 中解析出html页面
#     """
#     # time.sleep(random.randint(3, 5))
#     proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
#         "host": proxyHost,
#         "port": proxyPort,
#         "user": proxyUser,
#         "pass": proxyPass,
#     }
#
#     proxies = {
#         "http": proxyMeta,
#         "https": proxyMeta,
#     }
#
#     # proxy = html_prase('http://123.56.28.190:8000/get/').decode('utf-8')
#     # proxies = {"http": "http://{}".format(proxy)}
#     cookiestring1 = 'sessid=D1ABA930-5747-822C-A0DD-D4FDC3324BEC; aQQ_ajkguid=8D807759-B87B-5B16-9F2D-011B1B89B9AA; lps=http%3A%2F%2Fshenzhen.anjuke.com%2F%7Chttps%3A%2F%2Fshenzhen.anjuke.com%2Fsale%2F; ctid=13; twe=2; 58tj_uuid=c29b2e4b-1a90-4da1-9ba6-575f6a654599; new_session=0; init_refer=https%253A%252F%252Fshenzhen.anjuke.com%252Fsale%252F; new_uv=3; als=0; __xsptplus8=8.3.1532483400.1532483414.2%234%7C%7C%7C%7C%7C%23%23OCqenBwYbPbf1crz05jds4VXKkX8zFRU%23; _ga=GA1.2.1375191642.1532338925; _gid=GA1.2.2090140773.1532338925'
#     cookiestring2 = 'aQQ_ajkguid=F0D027A8-D80F-2B7B-8C02-46B6BB6E2416; _ga=GA1.2.530918494.1528195167; 58tj_uuid=d9ba5bc8-1ce3-40ea-996b-2e708fda0fd1; als=0; isp=true; ctid=13; sessid=2EBAF33A-6DBF-23E3-F873-SX0719103000; twe=2; Hm_lvt_c5899c8768ebee272710c9c5f365a6d8=1531967403; _gid=GA1.2.1024232329.1532339102; browse_comm_ids=843112%7C599063%7C95306%7C907378%7C95024; propertys=lpwdqv-pcbcfj_; ajk_member_captcha=98dace4d56901a03978b788b29e9c906; Hm_lpvt_c5899c8768ebee272710c9c5f365a6d8=1532425353; lps=http%3A%2F%2Fshenzhen.anjuke.com%2Fsale%2Fa31-b36-p3%2F%7C; __xsptplusUT_8=1; init_refer=https%253A%252F%252Fshenzhen.anjuke.com%252Fsale%252F; new_uv=21; __xsptplus8=8.25.1532485214.1532485275.2%232%7Cwww.baidu.com%7C%7C%7C%25E5%25AE%2589%25E5%25B1%2585%25E5%25AE%25A2%7C%23%23KtbUotU6rqCZPp_tzCMizvoRzFWZ1izm%23; _gat=1; new_session=0'
#     # cookiestring2 = 'aQQ_ajkguid=F0D027A8-D80F-2B7B-8C02-46B6BB6E2416; _ga=GA1.2.530918494.1528195167; 58tj_uuid=d9ba5bc8-1ce3-40ea-996b-2e708fda0fd1; als=0; isp=true; ctid=13; sessid=2EBAF33A-6DBF-23E3-F873-SX0719103000; twe=2; Hm_lvt_c5899c8768ebee272710c9c5f365a6d8=1531967403; Hm_lpvt_c5899c8768ebee272710c9c5f365a6d8=1531967403; _gid=GA1.2.1024232329.1532339102; browse_comm_ids=843112%7C599063%7C95306%7C907378%7C95024; propertys=lpwdqv-pcbcfj_; ajk_member_captcha=98dace4d56901a03978b788b29e9c906; lps=http%3A%2F%2Fshenzhen.anjuke.com%2Fsale%2Fp49%2F%7C; init_refer=https%253A%252F%252Fshenzhen.anjuke.com%252Fsale%252Fpingshanq%252Fa24-b39-m26%252F; new_uv=17; new_session=0; __xsptplusUT_8=1; _gat=1; __xsptplus8=8.19.1532412598.1532418516.76%233%7Csz.58.com%7C%7C%7C%7C%23%23rm-Nshzu7h0eO285Di6io0bS0_wrr7k_%23'
#     cookiestring3 = 'aQQ_ajkguid=1D91A71E-3160-6FA3-F856-4BD24DED58AC; ctid=13; twe=2; sessid=38153BF8-68F2-1ACD-566E-2B875DC9ADB9; _ga=GA1.2.1500179364.1532418666; _gid=GA1.2.1066935492.1532418666; 58tj_uuid=a311c6cd-3150-42e4-bdec-b6d1a3303b75; als=0; lps=http%3A%2F%2Fshenzhen.anjuke.com%2F%7Chttps%3A%2F%2Fshenzhen.anjuke.com%2Fsale%2F%3Ffrom%3Dnavigation; __xsptplusUT_8=1; _gat=1; new_session=1; init_refer=https%253A%252F%252Fshenzhen.anjuke.com%252Fsale%252F%253Ffrom%253Dnavigation; new_uv=2; __xsptplus8=8.2.1532485474.1532485474.1%232%7Cwww.baidu.com%7C%7C%7C%25E5%25AE%2589%25E5%25B1%2585%25E5%25AE%25A2%7C%23%23r-gOZAeBh5TUbt2N37bNkwlkGvvbDxYu%23'
#     # cookiestring3 = 'aQQ_ajkguid=1D91A71E-3160-6FA3-F856-4BD24DED58AC; lps=http%3A%2F%2Fwww.anjuke.com%2F%3Fpi%3DPZ-baidu-pc-all-biaoti%7Chttps%3A%2F%2Fwww.baidu.com%2Fs%3Fie%3Dutf-8%26f%3D8%26rsv_bp%3D1%26ch%3D3%26tn%3D98010089_dg%26wd%3D%25E5%25AE%2589%25E5%25B1%2585%25E5%25AE%25A2%26oq%3D%2525E5%2525A4%2525A7%2525E4%2525BC%252597%2525E7%252582%2525B9%2525E8%2525AF%252584%26rsv_pq%3Dfdda013c00007af2%26rsv_t%3D4768STDxLxXJ6Um5MJ5Ez2bfwV%252BGQAYe3yHTZfFdYk5IC9EKeaRWaOK6f6r1Qtg%252Fb4M%26rqlang%3Dcn%26rsv_enter%3D1%26bs%3D%25E5%25A4%25A7%25E4%25BC%2597%25E7%2582%25B9%25E8%25AF%2584; ctid=13; twe=2; sessid=38153BF8-68F2-1ACD-566E-2B875DC9ADB9; __xsptplusUT_8=1; _ga=GA1.2.1500179364.1532418666; _gid=GA1.2.1066935492.1532418666; _gat=1; 58tj_uuid=a311c6cd-3150-42e4-bdec-b6d1a3303b75; init_refer=https%253A%252F%252Fwww.baidu.com%252Fs%253Fie%253Dutf-8%2526f%253D8%2526rsv_bp%253D1%2526ch%253D3%2526tn%253D98010089_dg%2526wd%253D%2525E5%2525AE%252589%2525E5%2525B1%252585%2525E5%2525AE%2525A2%2526oq%253D%252525E5%252525A4%252525A7%252525E4%252525BC%25252597%252525E7%25252582%252525B9%252525E8%252525AF%25252584%2526rsv_pq%253Dfdda013c00007af2%2526rsv_t%253D4768STDxLxXJ6Um5MJ5Ez2bfwV%25252BGQAYe3yHTZfFdYk5IC9EKeaRWaOK6f6r1Qtg%25252Fb4M%2526rqlang%253Dcn%2526rsv_enter%253D1%2526bs%253D%2525E5%2525A4%2525A7%2525E4%2525BC%252597%2525E7%252582%2525B9%2525E8%2525AF%252584; new_uv=1; als=0; __xsptplus8=8.1.1532418666.1532418672.2%232%7Cwww.baidu.com%7C%7C%7C%25E5%25AE%2589%25E5%25B1%2585%25E5%25AE%25A2%7C%23%23PAJyIqhgMs0T8yCypjH8m5LLXfZChey7%23; new_session=0'
#     cookiestring4 = 'aQQ_ajkguid=9625C105-2BF7-AE4B-D111-81535CFCA987; ctid=13; twe=2; sessid=76B96246-7784-189F-FAAC-0461E41FBC67; 58tj_uuid=d906afd4-3b10-4d8d-a6bb-71a6943b88bc; als=0; _ga=GA1.2.1805033355.1532418813; _gid=GA1.2.861278800.1532418813; isp=true; Hm_lvt_c5899c8768ebee272710c9c5f365a6d8=1532418816; Hm_lpvt_c5899c8768ebee272710c9c5f365a6d8=1532418816; browse_comm_ids=862612; propertys=lsfpzv-pcd3hj_; ajk_member_captcha=4ef3d9b512bd0d8db4cafa8f993ad12b; lps=http%3A%2F%2Fshenzhen.anjuke.com%2Fsale%2Fa24-b30-p4%2F%7C; _gat=1; __xsptplusUT_8=1; new_session=1; init_refer=https%253A%252F%252Fwww.baidu.com%252Fs%253Fwd%253D%2525E5%2525AE%252589%2525E5%2525B1%252585%2525E5%2525AE%2525A2%2526ie%253DUTF-8; new_uv=5; __xsptplus8=8.5.1532485591.1532485591.1%232%7Cwww.baidu.com%7C%7C%7C%25E5%25AE%2589%25E5%25B1%2585%25E5%25AE%25A2%7C%23%23SSTTFY4xKL6S6Eu8-muTlVXAu1tWHLkr%23'
#     # cookiestring4 = 'aQQ_ajkguid=9625C105-2BF7-AE4B-D111-81535CFCA987; ctid=13; twe=2; sessid=76B96246-7784-189F-FAAC-0461E41FBC67; 58tj_uuid=d906afd4-3b10-4d8d-a6bb-71a6943b88bc; als=0; lps=http%3A%2F%2Fwww.anjuke.com%2F%3Fpi%3DPZ-baidu-pc-all-biaoti%7Chttps%3A%2F%2Fwww.baidu.com%2Fs%3Fie%3Dutf-8%26f%3D8%26rsv_bp%3D1%26tn%3Dbaidu%26wd%3D%25E5%25AE%2589%25E5%25B1%2585%25E5%25AE%25A2%26oq%3Djquery%252520%2525E5%25258D%25259A%2525E5%2525AE%2525A2%2525E5%25259B%2525AD%26rsv_pq%3De2d3a4980005afcd%26rsv_t%3D473b%252B7FkDL9MCidKgZPC%252BoDOFjWJVNgRDjsZ1HevwzyakK%252BiRuTTO61sNEY%26rqlang%3Dcn%26rsv_enter%3D1%26inputT%3D4106%26rsv_sug3%3D8%26bs%3Djquery%2520%25E5%258D%259A%25E5%25AE%25A2%25E5%259B%25AD; _ga=GA1.2.1805033355.1532418813; _gid=GA1.2.861278800.1532418813; _gat=1; __xsptplusUT_8=1; init_refer=https%253A%252F%252Fwww.baidu.com%252Fs%253Fie%253Dutf-8%2526f%253D8%2526rsv_bp%253D1%2526tn%253Dbaidu%2526wd%253D%2525E5%2525AE%252589%2525E5%2525B1%252585%2525E5%2525AE%2525A2%2526oq%253Djquery%25252520%252525E5%2525258D%2525259A%252525E5%252525AE%252525A2%252525E5%2525259B%252525AD%2526rsv_pq%253De2d3a4980005afcd%2526rsv_t%253D473b%25252B7FkDL9MCidKgZPC%25252BoDOFjWJVNgRDjsZ1HevwzyakK%25252BiRuTTO61sNEY%2526rqlang%253Dcn%2526rsv_enter%253D1%2526inputT%253D4106%2526rsv_sug3%253D8%2526bs%253Djquery%252520%2525E5%25258D%25259A%2525E5%2525AE%2525A2%2525E5%25259B%2525AD; new_uv=2; isp=true; new_session=0; Hm_lvt_c5899c8768ebee272710c9c5f365a6d8=1532418816; Hm_lpvt_c5899c8768ebee272710c9c5f365a6d8=1532418816; __xsptplus8=8.2.1532418814.1532418818.2%232%7Cwww.baidu.com%7C%7C%7C%25E5%25AE%2589%25E5%25B1%2585%25E5%25AE%25A2%7C%23%23nVR1kHZjdbjRi2g7GfG8HlCZC45MpjwU%23'
#     cookiestring5 = 'aQQ_ajkguid=1D91A71E-3160-6FA3-F856-4BD24DED58AC; ctid=13; twe=2; sessid=38153BF8-68F2-1ACD-566E-2B875DC9ADB9; _ga=GA1.2.1500179364.1532418666; _gid=GA1.2.1066935492.1532418666; 58tj_uuid=a311c6cd-3150-42e4-bdec-b6d1a3303b75; als=0; lps=http%3A%2F%2Fshenzhen.anjuke.com%2F%7Chttps%3A%2F%2Fshenzhen.anjuke.com%2Fsale%2F%3Ffrom%3Dnavigation; __xsptplusUT_8=1; init_refer=https%253A%252F%252Fshenzhen.anjuke.com%252Fsale%252F%253Ffrom%253Dnavigation; new_uv=2; __xsptplus8=8.2.1532485474.1532485503.2%232%7Cwww.baidu.com%7C%7C%7C%25E5%25AE%2589%25E5%25B1%2585%25E5%25AE%25A2%7C%23%23r-gOZAeBh5TUbt2N37bNkwlkGvvbDxYu%23; new_session=0'
#     # cookiestring5 = 'sessid=1A1580B9-22F7-3AF5-1C0A-E12AF782E33E; aQQ_ajkguid=CB94359A-3CDD-719E-A665-81957085407B; lps=http%3A%2F%2Fwww.anjuke.com%2F%3Fpi%3DPZ-baidu-pc-all-biaoti%7Chttps%3A%2F%2Fwww.baidu.com%2Fs%3Fie%3Dutf-8%26f%3D8%26rsv_bp%3D1%26tn%3Dmonline_dg%26wd%3D%25E5%25AE%2589%25E5%25B1%2585%25E5%25AE%25A2%26oq%3D%2525E5%2525A4%2525A7%2525E4%2525BC%252597%2525E7%252582%2525B9%2525E8%2525AF%252584%26rsv_pq%3D9fb7da7e0000513d%26rsv_t%3D23665UITeN%252FtpxL0eYCmlaKZaQCrWa%252FjX0k7%252F7FttC5vq7CI6UnK8p4WEP3bJkY7jQ%26rqlang%3Dcn%26rsv_enter%3D1%26rsv_sug3%3D3%26rsv_sug1%3D2%26rsv_sug7%3D100%26bs%3D%25E5%25A4%25A7%25E4%25BC%2597%25E7%2582%25B9%25E8%25AF%2584; ctid=13; twe=2; 58tj_uuid=7f768738-3aad-44d2-922b-5c5eeb21158e; new_session=0; init_refer=https%253A%252F%252Fwww.baidu.com%252Fs%253Fie%253Dutf-8%2526f%253D8%2526rsv_bp%253D1%2526tn%253Dmonline_dg%2526wd%253D%2525E5%2525AE%252589%2525E5%2525B1%252585%2525E5%2525AE%2525A2%2526oq%253D%252525E5%252525A4%252525A7%252525E4%252525BC%25252597%252525E7%25252582%252525B9%252525E8%252525AF%25252584%2526rsv_pq%253D9fb7da7e0000513d%2526rsv_t%253D23665UITeN%25252FtpxL0eYCmlaKZaQCrWa%25252FjX0k7%25252F7FttC5vq7CI6UnK8p4WEP3bJkY7jQ%2526rqlang%253Dcn%2526rsv_enter%253D1%2526rsv_sug3%253D3%2526rsv_sug1%253D2%2526rsv_sug7%253D100%2526bs%253D%2525E5%2525A4%2525A7%2525E4%2525BC%252597%2525E7%252582%2525B9%2525E8%2525AF%252584; new_uv=1; als=0; __xsptplus8=8.1.1532418988.1532418992.2%232%7Cwww.baidu.com%7C%7C%7C%25E5%25AE%2589%25E5%25B1%2585%25E5%25AE%25A2%7C%23%23Iwk7gyvGFXkpA-eee7x9I-tQpvJQ-Mr-%23; _ga=GA1.2.1538979153.1532418988; _gid=GA1.2.1619595185.1532418988'
#     cookiestring6 = 'aQQ_ajkguid=8AB8B7F0-209E-125C-8820-5B52B87415BC; ctid=13; twe=2; sessid=B6E0C8DC-1C88-B155-F510-595C68A31F27; 58tj_uuid=886e0406-baf4-45f8-ba84-1e0cd51d2689; new_uv=1; als=0; _ga=GA1.2.756586716.1532419516; _gid=GA1.2.1680880881.1532419516; __xsptplus8=8.1.1532419516.1532419540.3%232%7Cwww.baidu.com%7C%7C%7C%25E5%25AE%2589%25E5%25B1%2585%25E5%25AE%25A2%7C%23%23y1wC__C5YNWExfi6n5sNQ5cfYGlb67Tt%23'
#     # cookiestring6 = 'aQQ_ajkguid=8AB8B7F0-209E-125C-8820-5B52B87415BC; lps=http%3A%2F%2Fwww.anjuke.com%2F%3Fpi%3DPZ-baidu-pc-all-biaoti%7Chttps%3A%2F%2Fwww.baidu.com%2Fs%3Fie%3Dutf-8%26f%3D8%26rsv_bp%3D1%26tn%3Dcnopera%26wd%3D%25E5%25AE%2589%25E5%25B1%2585%25E5%25AE%25A2%26oq%3D58%26rsv_pq%3Dd2be7af200016217%26rsv_t%3D86431RWOAQ8FGRSMiS%252Fp%252BUs06xQm9Q9wdtgypuyDEcM3w2eW7csjG0ekRafYtg%26rqlang%3Dcn%26rsv_enter%3D1%26bs%3D58; ctid=13; twe=2; sessid=B6E0C8DC-1C88-B155-F510-595C68A31F27; __xsptplusUT_8=1; 58tj_uuid=886e0406-baf4-45f8-ba84-1e0cd51d2689; init_refer=https%253A%252F%252Fwww.baidu.com%252Fs%253Fie%253Dutf-8%2526f%253D8%2526rsv_bp%253D1%2526tn%253Dcnopera%2526wd%253D%2525E5%2525AE%252589%2525E5%2525B1%252585%2525E5%2525AE%2525A2%2526oq%253D58%2526rsv_pq%253Dd2be7af200016217%2526rsv_t%253D86431RWOAQ8FGRSMiS%25252Fp%25252BUs06xQm9Q9wdtgypuyDEcM3w2eW7csjG0ekRafYtg%2526rqlang%253Dcn%2526rsv_enter%253D1%2526bs%253D58; new_uv=1; als=0; _ga=GA1.2.756586716.1532419516; _gid=GA1.2.1680880881.1532419516; _gat=1; __xsptplus8=8.1.1532419516.1532419522.2%232%7Cwww.baidu.com%7C%7C%7C%25E5%25AE%2589%25E5%25B1%2585%25E5%25AE%25A2%7C%23%23y1wC__C5YNWExfi6n5sNQ5cfYGlb67Tt%23; new_session=0'
#     cookiestring = [cookiestring1, cookiestring2, cookiestring3, cookiestring4, cookiestring5, cookiestring6]
#     # cookies = cookie_from_url(url)
#     cookies = cookies2dict(choice(cookiestring))
#     print("cookies is : {} ".format(cookies))
#     ua = UserAgent()
#     headers = {
#         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
#         'Accept-Encoding': 'gzip, deflate, br',
#         'Accept-Language': 'zh-CN,zh;q=0.9',
#         'Cache-Control': 'no-cache',
#         'Connection': 'close',
#         'Host': 'shenzhen.anjuke.com',
#         'Referer': 'https://shenzhen.anjuke.com/?pi=PZ-baidu-pc-all-biaoti',
#         'Upgrade-Insecure-Requests': '1',
#         'User-Agent': ua.random,
#         # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Safari/537.36',
#     }
#     print(url)
#     print(headers['User-Agent'])
#
#     with requests.Session() as s:
#         s.keep_alive = False
#         print("2 s.keep_alive:{}".format(s.keep_alive))
#         retries = Retry(total=5,
#                         backoff_factor=0.1,
#                         status_forcelist=[403, 500, 502, 503, 504])
#         s.mount('http://', HTTPAdapter(max_retries=retries))
#         s.mount('https://', HTTPAdapter(max_retries=retries))
#
#         try:
#             with s.get(url, stream=False, headers=headers, cookies=cookies, proxies=proxies) as r:
#                 # with s.get(url, stream=False, headers=headers, cookies=cookies) as r:
#                 print('r:{}'.format(r))
#                 print('r.status_code:{}'.format(r.status_code))
#                 if not 200 <= r.status_code < 300:
#                     print('r.status_code in if:{}'.format(r.status_code))
#                     return html_from_url(url)
#                 print('1 r.encoding:{}'.format(r.encoding))
#                 encoding = r.encoding
#                 if encoding in [None, 'ISO-8859-1']:
#                     encodings = requests.utils.get_encodings_from_content(r.text)
#                     if encodings:
#                         encoding = encodings[0]
#                     else:
#                         encoding = r.apparent_encoding
#                     print('2 encoding:{}'.format(encoding))
#                     page = r.content.decode(encoding)
#                     print('2 encoding page:{}'.format(page))
#                 else:
#                     page = r.text
#                     # print('page in else:{}'.format(page))
#                 # selector = etree.HTML(page)
#                 # if selector.xpath('//div[contains(@id, "not-found")]'):
#                 #     return html_from_url(url)
#                 r.close()
#                 print('html_from_url before return page :{}'.format(r))
#                 return page
#         except Exception as e:
#             print('Exception: {}'.format(e))
#             return html_from_url(url)
def html_from_url(url):
    print('html_from_url url: {}'.format(url))
    try:
        if url is None:
            return
        session = HTMLSession()
        r = session.get(url)
        return r.html.html
    except Exception as e:
        print('Exception: {}'.format(e))
        return html_from_url(url)


def html_from_url2(url):
    """
    从 url 中解析出html页面
    """
    proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
        "host": proxyHost,
        "port": proxyPort,
        "user": proxyUser,
        "pass": proxyPass,
    }

    proxies = {
        "http": proxyMeta,
        "https": proxyMeta,
    }

    # proxy = html_prase('http://123.56.28.190:8000/get/').decode('utf-8')
    # proxies = {"http": "http://{}".format(proxy)}
    cookiestring1 = 'uamo=18312529671; _hc.v=189ee497-f45e-1164-648f-48ae8571b6e4.1531304312; ctu=5b6309d42a05ae4dd213481415b102b4b1c4c0ac0443e489402f03016e53d50d; _lxsdk_cuid=16488d97e71c8-04b82251d8a779-784a5037-1fa400-16488d97e72c8; _lxsdk=16488d97e71c8-04b82251d8a779-784a5037-1fa400-16488d97e72c8; ua=wangqian6151; _lx_utm=utm_source%3DBaidu%26utm_medium%3Dorganic; cye=shenzhen; _lxsdk_s=164ab477cc9-0a2-51b-f1c%7C%7C43; cy=7; lgtoken=0b9a40890-9d88-44ab-87aa-292c1a66f571; dper=ccab61fe549d84a8f4e11374b614ba650fe038f0e99e0637232f076ed78fb0b1d7287af4934c308d8d109722b03db5c8f1db87d2901503e14b11e5431fd7c88a66ef1d8a610796e7eecd5f7312f91fc68123d608f67990a97d5aa87581c5267c; ll=7fd06e815b796be3df069dec7836c3df; ctu=a128b8ba9b1f9c7f5c3151a5c407c42f42cb62f856b71604cc7f241c3648f7f076e7934256734e27cc0b5b8ceaebf473'
    cookiestring2 = 'cye=shenzhen; _lxsdk_cuid=163dcf4d2f3c8-0183cdb3d20aca-5e4b2519-1fa400-163dcf4d2f3c8; _lxsdk=163dcf4d2f3c8-0183cdb3d20aca-5e4b2519-1fa400-163dcf4d2f3c8; _hc.v=4b138761-b7c0-a8ad-c357-a6dd990451c1.1528420422; s_ViewType=10; ctu=5b6309d42a05ae4dd213481415b102b41b10ffbde57840e084f7ee09eab0b8cb; aburl=1; cy=7; Hm_lvt_dbeeb675516927da776beeb1d9802bd4=1530066838,1530517916,1530588829,1530868655; cy=7; cityid=7; cye=shenzhen; Hm_lvt_4c4fc10949f0d691f3a2cc4ca5065397=1528971283,1530176708,1530950732; Hm_lpvt_4c4fc10949f0d691f3a2cc4ca5065397=1530950732; lastVisitUrl=%2Fshenzhen%2Fhotel%2Fr31; __mta=214923560.1528964249753.1531124184220.1531129100944.124; thirdtoken=9A26A175B640CF8C437D0290137C0760; JSESSIONID=B9857D9A439B375F8ACF8F93041E9AC6; bind_feed=Sina; _dp.ac.v=41b6401b-c777-4eba-9ea3-6d7709a3976f; Hm_lpvt_dbeeb675516927da776beeb1d9802bd4=1531356479; uamo=15012603932; ctu=986f8347443b5584c2cc3e784eb6caad52244495290d1d3e56fea31bc737b689dca3b622f93681987341fd532fe4aeb0; catBrowserName=catBrowserValue; apollo-agent-pc-static-user-lonin-cookie-time-oneDay=Tue%20Jul%2017%202018%2018:00:03%20GMT+0800%20(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4); lgtoken=0a175ae63-7510-45c3-9377-3d7d48d1b127; dper=5f99c6ab1b74572017f7c31799d57f8a88cef35d61fbf99b2e6506169d7213034fbaaddf2c7870909b080c81bf82d214868a85ab37d860b84e87fa34323ca04ce734639416315badb9196c9025f5b67412c08e8125832e0086b9e110de64004f; ll=7fd06e815b796be3df069dec7836c3df; ua=15200730164; _lxsdk_s=164ab4a3fe5-311-90a-345%7C%7C13'
    cookiestring3 = 'cy=7; cye=shenzhen; _lxsdk_cuid=1648c1b10b9c8-050881ab1e64f8-3351427c-1fa400-1648c1b10b944; _lxsdk=1648c1b10b9c8-050881ab1e64f8-3351427c-1fa400-1648c1b10b944; _hc.v=590d7836-b4f0-1060-da20-92b1c3fa0954.1531358942; _dp.ac.v=7e331984-7611-4c67-a3ab-0995c8a0d548; ctu=3b0560417a4dd025ae35ec69dafae5b53d752b6ef4b8d7a300e6d2b19a83cdf4; _lx_utm=utm_source%3DBaidu%26utm_medium%3Dorganic; ctu=c014b184cb4be38a7ec7abf02ffeb91f2cd21e10d84bf2da3957eb2e9f21741580457dad7d86647c231718de2db65ba5; dper=e180cb2cf7d577604dbb06239a1925b9345be954de2df08a19aa7c3f2c2b24e005d478616818cfe495d96e0a2d2653ea243477d31065d69a6fcd7b99ac821dc714345a4f878ef477a70618f7d4b93c4b93ff9bfa1c9eb42a24999994d62982cd; ll=7fd06e815b796be3df069dec7836c3df; ua=dpuser_5837056877; uamo=13048905567; _lxsdk_s=164ab4e37fd-7a0-6e0-639%7C%7C48'
    cookiestring4 = 'cy=7; cye=shenzhen; _lxsdk_cuid=16488d3fcd69-0ef7d447345ba18-4c312b7b-1fa400-16488d3fcd7c8; _lxsdk=16488d3fcd69-0ef7d447345ba18-4c312b7b-1fa400-16488d3fcd7c8; _hc.v=72331155-2353-253c-3bc4-3df4ada336ef.1531303952; ua=dpuser_2460430632; ctu=068b5cc7e339b23a8684d9a2bf474d58ef6054778b51d575544cf4a7af3994ee; _lx_utm=utm_source%3DBaidu%26utm_medium%3Dorganic; ctu=81b521e8c94606b4281a32d4bbab10487611da4f276f9298eba0af9a7f348644cecc62600a1bc355fc66476b6f6f15ff; _lxsdk_s=164ab51f388-d3d-0d0-15e%7C%7C23; lgtoken=05b1be2be-5c3e-4a9a-9340-235dd5c9a04b; dper=12648f0f54f5d8703da385e59e5769bbb19212f9aac92eb8f33864b9389f5af8f2d0f1c53bae5ab60b28903581c17ac5133c8e1ce6b89b137b4069bc912368e07d5df895a2c94693dc1a68a129a26a2ac9929a012b584f3fe2137cf6c73cee05; ll=7fd06e815b796be3df069dec7836c3df; uamo=15012603932'
    cookiestring5 = 'cy=7; cye=shenzhen; _lx_utm=utm_source%3DBaidu%26utm_medium%3Dorganic; _lxsdk_cuid=1648c1e5eb27-0b23c592533ba6-61231d53-1fa400-1648c1e5eb3c8; _lxsdk=1648c1e5eb27-0b23c592533ba6-61231d53-1fa400-1648c1e5eb3c8; _hc.v=26340449-dc9c-7c12-18a7-87ae84c15df7.1531359158; ctu=cf30eb3a2208bf59e731f2c124c569b02d322e3e888bac4670646dc26b28776e; s_ViewType=10; cityInfo=%7B%22cityId%22%3A7%2C%22cityEnName%22%3A%22shenzhen%22%2C%22cityName%22%3A%22%E6%B7%B1%E5%9C%B3%22%7D; lastVisitUrl=%2Fshenzhen%2Fhotel%2Fr12036; selectLevel=%7B%22level1%22%3A%222%22%7D; Hm_lvt_dbeeb675516927da776beeb1d9802bd4=1531710699; Hm_lpvt_dbeeb675516927da776beeb1d9802bd4=1531710810; __mta=21426948.1531710700162.1531710700162.1531710810487.2; ctu=2bd1431edf381eaa9ad290f1c2cf6b8e81dde1f953989171ca62396a21815a4eb690546bcc312943b61652e3fc00c2d5; lgtoken=0abf73723-c1b3-4dce-b6d3-c6d6ad67ff1b; dper=6e6b885ec5f7076dd41202e43d50f6fae6be5688507b426187be71bb6c6b5202293b42323ea274a24a828f28d13be20f23db8519fb84c1a995c138db0309440c3c5c2909be1ea883123a3120a7fb8043d396adca5d202222d2901a40d10fe419; ll=7fd06e815b796be3df069dec7836c3df; ua=dpuser_69178432071; uamo=18603012947; _lxsdk_s=164ab54feb5-6a8-6ec-c31%7C%7C22'
    cookiestring = [cookiestring1, cookiestring2, cookiestring3, cookiestring4, cookiestring5]
    # cookies = cookie_from_url(url)
    cookies = cookies2dict(choice(cookiestring))
    print("cookies is : {} ".format(cookies))
    ua = UserAgent()
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'close',
        'Host': 'www.dianping.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': ua.random,
    }
    print(url)
    print(headers['User-Agent'])
    # try:
    #     with requests.get(url, headers=headers, cookies=cookies, proxies=proxies) as r:
    #         # with s.get(url, stream=False, headers=headers, cookies=cookies) as r:
    #         print('r:{}'.format(r))
    #         print('r.status_code:{}'.format(r.status_code))
    #         if not 200 <= r.status_code < 300:
    #             print('r.status_code in if:{}'.format(r.status_code))
    #             return html_from_url(url)
    #         print('1 r.encoding:{}'.format(r.encoding))
    #         encoding = r.encoding
    #         if encoding in [None, 'ISO-8859-1']:
    #             encodings = requests.utils.get_encodings_from_content(r.text)
    #             if encodings:
    #                 encoding = encodings[0]
    #             else:
    #                 encoding = r.apparent_encoding
    #             print('2 encoding:{}'.format(encoding))
    #             page = r.content.decode(encoding)
    #             print('2 encoding page:{}'.format(page))
    #         else:
    #             page = r.text
    #         selector = etree.HTML(page)
    #         if selector.xpath('//div[contains(@id, "not-found")]'):
    #             return html_from_url2(url)
    #         return page
    # except Exception as e:
    #     print('Exception: {}'.format(e))
    #     return html_from_url2(url)
    # with requests.get(url, headers=headers, cookies=cookies, proxies=proxies) as r:
    # with s.get(url, headers=headers, cookies=cookies) as r:
    r = requests.get(url, headers=headers, cookies=cookies, proxies=proxies)
    print('r:{}'.format(r))
    print('r.status_code:{}'.format(r.status_code))
    if not 200 <= r.status_code < 300:
        print('r.status_code in if:{}'.format(r.status_code))
        return html_from_url2(url)
    print('1 r.encoding:{}'.format(r.encoding))
    encoding = r.encoding
    if encoding in [None, 'ISO-8859-1']:
        encodings = requests.utils.get_encodings_from_content(r.text)
        if encodings:
            encoding = encodings[0]
        else:
            encoding = r.apparent_encoding
        print('2 encoding:{}'.format(encoding))
        page = r.content.decode(encoding)
        print('2 encoding page:{}'.format(page))
    else:
        page = r.text
    selector = etree.HTML(page)
    if selector.xpath('//div[contains(@id, "not-found")]'):
        return html_from_url2(url)
    r.close()
    return page


def html_from_uri(uri):
    with requests.Session() as s:
        s.keep_alive = False
        # print("uri s.keep_alive:{}".format(s.keep_alive))
        retries = Retry(total=5,
                        backoff_factor=0.1,
                        status_forcelist=[403, 500, 502, 503, 504])
        s.mount('http://', HTTPAdapter(max_retries=retries))
        s.mount('https://', HTTPAdapter(max_retries=retries))
        try:
            with s.get(uri, stream=False) as r:
                # print('uri r:{}'.format(r))
                # print('uri r.status_code:{}'.format(r.status_code))
                if not 200 <= r.status_code < 300:
                    print('uri r.status_code in if:{}'.format(r.status_code))
                    return html_from_uri(uri)
                # print('uri 1 r.encoding:{}'.format(r.encoding))
                encoding = r.encoding
                if encoding in [None, 'ISO-8859-1']:
                    encodings = requests.utils.get_encodings_from_content(r.text)
                    if encodings:
                        encoding = encodings[0]
                    else:
                        encoding = r.apparent_encoding
                    print('uri 2 encoding:{}'.format(encoding))
                    page = r.content.decode(encoding)
                    print('uri 2 encoding page:{}'.format(page))
                else:
                    page = r.text
                r.close()
                return page
        except Exception as e:
            print('Exception in html_from_uri: {}'.format(e))
            return html_from_uri(uri)
