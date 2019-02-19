# coding: utf-8
import os
path = os.getcwd()
os.chdir(path)
import urllib
import urllib.parse
import urllib.request
from xml.dom import minidom


class RequestURL:
    def __init__(self):
        self.dom = None


    def get_request(self, url):
        try:
            self.dom = minidom.parse(urllib.request.urlopen(url))
        except urllib.error.HTTPError as e:
            print(e.code)
            raise
        except urllib.error.URLError as e:
            print(e.reason)
            raise

        return self.dom


    @staticmethod
    def encode_url(url):
        return urllib.parse.quote(url)


    def domunlink(self):
        self.dom.unlink()


    def getElementsByTagName(self, tag):
        return self.dom.getElementsByTagName(tag)
