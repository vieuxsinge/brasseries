# -*- coding: utf-8 -*-
from pyquery import PyQuery as pq


class Brasserie(object):
    def __init__(self, name, address, postal_code, city, tel, email, contact,
                 website, creation_date, history):
        self.name = name
        self.address = address
        self.postal_code = postal_code
        self.city = city
        self.tel = tel
        self.email = email
        self.contact = contact
        self.website = website
        self.creation_date = creation_date
        self.history = history


class BeerScrapper(object):

    url = 'http://projet.amertume.free.fr/html/liste_brasseries.htm'

    def __init__(self, start, end):
        self.brasseries = []

    def scrap(self):
        """Scrap a page, put the results in the self.tracks attribute."""
        d = pq(url=self.url)
        from pdb import set_trace; set_trace()
        for item in d.find('.cestquoicetitre_results>div').items():
            artist = item('.artiste a').text()
            if artist is None:
                artist = item('.artiste').text()

            title = item('.titre').text()
            ts_class = (item('.time').parent().parent()[0]
                        .attrib['class'].split()[0])
            ts = ts_class.split('_')[-1]

            if ts not in self.tracks:
                track = Track(artist=artist, title=title, ts=ts)
                self.tracks[ts] = track


def render_geojson(brasseries):
    """Converts the list of brasseries into geojson."""
    for brasserie in brasseries:
        pass

if __name__ == '__main__':
    scrapper = BeerScrapper()
    print render_geojson(scrapper.scrap())
