# -*- coding: utf-8 -*-
import codecs
from pyquery import PyQuery as pq
import urllib
import json
from geojson import Feature, Point, FeatureCollection


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

    def get_popup_content(self):
        return u"\n".join([self.get_address(), self.tel, self.website,
                           self.email])


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
    url = u"http://nominatim.openstreetmap.org/search/%s?format=json" % address
    results = json.loads(urllib.urlopen(url.encode("utf-8")).read())
    if results:
        lat = float(results[0]["lat"])
        lng = float(results[0]["lon"])
        return Point((lng, lat))
    return None


def render_geojson(brasseries):
    """Converts the list of brasseries into geojson."""
    features = []
    not_found = []
    for brasserie in brasseries:
        point = geocode(brasserie.get_address())
        if point:
            features.append(Feature(geometry=point, properties={
                "name": brasserie.name,
                "description": brasserie.get_popup_content()
            }))
        else:
            not_found.append(brasserie)
    return FeatureCollection(features), not_found

if __name__ == '__main__':
    scrapper = BeerScrapper()
    features, not_found = render_geojson(scrapper.scrap())
    with codecs.open('brasseries.geojson', 'w', encoding='utf-8') as f:
        f.write(features)

    print('impossible de localiser ces brasseries:')
    print(', '.join([br.get_address() for br in not_found]))
