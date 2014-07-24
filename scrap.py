# -*- coding: utf-8 -*-
from pyquery import PyQuery as pq
import urllib
import json
from geojson import Point

GOOGLE_SERVER_API_KEY = "XXXXXX"


class Brasserie(object):
    def __init__(self, name, address, postal_code, city, tel, portable, fax,
                 email, contact, website, bio, creation_date, history):
        self.name = name
        self.address = address
        self.postal_code = postal_code
        self.city = city
        self.tel = tel
        self.portable = portable
        self.fax = fax
        self.email = email
        self.contact = contact
        self.website = website
        self.creation_date = creation_date
        self.history = history

    def get_address(self):
        return u"%s, %s %s" % (self.address, self.postal_code, self.city)


class BeerScrapper(object):

    url = 'http://projet.amertume.free.fr/html/liste_brasseries.htm'

    def __init__(self):
        self.brasseries = []

    def scrap(self):
        """Scrap a page, put the results in the self.tracks attribute."""
        def clean_text(txt):
            return (txt.replace('\n', '')
                       .replace('\t', ''))
            # XXX Need to change encoding.

        d = pq(url=self.url)
        for col in list(d.find('#table1>tr'))[1:]:
            self.brasseries.append(
                Brasserie(*[clean_text(c.text_content()) for c in col]))
        return self.brasseries


def geocode(address):
    url = u"https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=%s" % (address, GOOGLE_SERVER_API_KEY)
    content = json.loads(urllib.urlopen(url.encode("utf-8")).read())
    try:
        lat = content["results"][0]["geometry"]["location"]["lat"]
        lng = content["results"][0]["geometry"]["location"]["lng"]
        return Point((lat, lng))
    except IndexError:
        return None


def render_geojson(brasseries):
    """Converts the list of brasseries into geojson."""
    for brasserie in brasseries:
        point = geocode(brasserie.get_address())
        if point:
            print point
        else:
            # can't find ...
            pass

if __name__ == '__main__':
    scrapper = BeerScrapper()
    print render_geojson(scrapper.scrap())
