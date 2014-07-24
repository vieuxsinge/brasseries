# -*- coding: utf-8 -*-
from pyquery import PyQuery as pq


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


def render_geojson(brasseries):
    """Converts the list of brasseries into geojson."""
    for brasserie in brasseries:
        pass

if __name__ == '__main__':
    scrapper = BeerScrapper()
    print render_geojson(scrapper.scrap())
