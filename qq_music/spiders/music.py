import json
import math
import os
import urllib

import scrapy
from scrapy import Request


class MusicSpider(scrapy.Spider):
    name = 'music'
    allowed_domains = ['qq.com', '113.113.69.173']
    singer_list_url = 'https://u.y.qq.com/cgi-bin/musicu.fcg'
    start_urls = []
    singer_list_params_data = '{"comm": {"ct": 24, "cv": 0},"singerList": {"module": "Music.SingerListServer", "method": "get_singer_list","param": {"area": -100, "sex": -100, "genre": -100, "index": %s, "sin": %s,"cur_page": %s}}}'
    singer_lsit_params = {
        'data': ''
    }
    print(start_urls)
    singer_songs_url = 'https://c.y.qq.com/v8/fcg-bin/fcg_v8_singer_track_cp.fcg'
    singer_songs_params = {
        'singermid': '',
        'begin': 0,
        'num': 1
    }
    song_info_url = singer_list_url
    song_info_params_data = '{"req":{"module":"CDN.SrfCdnDispatchServer","method":"GetCdnDispatch","param":{"guid":"1007049558","calltype":0,"userip":""}},"req_0":{"module":"vkey.GetVkeyServer","method":"CgiGetVkey","param":{"guid":"1007049558","songmid":["%s"],"songtype":[0],"uin":"1165101043","loginflag":1,"platform":"20"}},"comm":{"uin":1165101043,"format":"json","ct":24,"cv":0}}'
    song_info_params = {
        'data': ''
    }
    download_url = 'http://113.113.69.173/amobile.music.tc.qq.com/'
    path = os.path.abspath(__file__).split("music.py")[0]

    def start_requests(self):
        """
        循环每个字母
        :return:
        """
        for index in range(1, 27):
            page = 1
            print("第" + str(index) + "个字母")
            yield Request(self.singer_list_url + "?data=" + self.singer_list_params_data % (str(index), str(0), str(1)),
                          meta={"index": index}, callback=self.parse_singer_pages)

    def parse_singer_pages(self, response):
        """
        循环每一页歌手
        :param response:
        :return:
        """
        singer_list_dict = json.loads(response.text)
        total = singer_list_dict["singerList"]["data"]["total"]
        page_num = [n for n in range(math.ceil(total / 80))]
        for page in page_num:
            yield Request(self.singer_list_url + "?data=" + self.singer_list_params_data % (
                str(response.meta["index"]), str(page * 80), str(page + 1)), callback=self.parse_singers)

    def parse_singers(self, response):
        """
        循环每一位歌手
        :param response:
        :return:
        """
        singer_list_dict = json.loads(response.text)
        singer_list = singer_list_dict["singerList"]["data"]["singerlist"]
        for singer in singer_list:
            print("歌手：" + singer["singer_mid"])
            self.singer_songs_params["singermid"] = singer["singer_mid"]
            self.singer_songs_params["begin"] = 0
            self.singer_songs_params["num"] = 1
            yield Request(self.singer_songs_url + "?" + urllib.parse.urlencode(self.singer_songs_params),
                          meta={"singermid": singer["singer_mid"]}, dont_filter=True, callback=self.parse_song_pages)

    def parse_song_pages(self, response):
        """
        循环每一页歌曲
        :param response:
        :return:
        """
        singer_songs_dict = json.loads(response.text)
        total = singer_songs_dict["data"]["total"]
        if total > 1000:
            # 邓丽君同学的歌曲有1948首，但你只能拿到1000首，所以1000为上限
            total = 1000
        page_num = [n for n in range(math.ceil(total / 10))]
        for page in page_num:
            self.singer_songs_params["singermid"] = response.meta["singermid"]
            self.singer_songs_params["begin"] = page * 10
            self.singer_songs_params["num"] = (page + 1) * 10
            yield Request(self.singer_songs_url + "?" + urllib.parse.urlencode(self.singer_songs_params),
                          callback=self.parse_songs)

    def parse_songs(self, response):
        """
        循环每一首歌
        :param response:
        :return:
        """
        singer_songs_dict = json.loads(response.text)
        singer_songs = singer_songs_dict["data"]["list"]
        for song in singer_songs:
            print("歌曲：" + song["musicData"]["songmid"])
            self.song_info_params['data'] = self.song_info_params_data % (song["musicData"]["songmid"])
            yield Request(self.song_info_url + "?" + urllib.parse.urlencode(self.song_info_params),
                          dont_filter=True, callback=self.parse_song_info)

    def parse_song_info(self, response):
        """
        解析歌曲信息
        :param response:
        :return:
        """
        song_info_dict = json.loads(response.text)
        filename = song_info_dict["req_0"]["data"]["midurlinfo"][0]["filename"]
        purl = song_info_dict["req_0"]["data"]["midurlinfo"][0]["purl"]
        print("下载：" + filename + "，" + self.download_url + purl)
        return Request(self.download_url + purl, meta={"filename": filename}, callback=self.parse_download)

    def parse_download(self, response):
        """
        下载歌曲
        :param response:
        :return:
        """
        with open(self.path + "songs\\" + response.meta["filename"], "wb") as f:
            f.write(response.body)
            f.close()
