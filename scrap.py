# -*- coding: utf-8 -*-
from __future__ import print_function
from collections import Counter
import codecs
import datetime
import json
import sys
import urllib

from pyquery import PyQuery as pq
from geojson import Feature, Point, FeatureCollection
import arrow
import progressbar
import geojson


class Brasserie(object):
    def __init__(self, name, address, postal_code, city, tel, portable, fax,
                 email, contact, website, tasted, farm, barley, hops,
                 malting, bio, food, education, creation_date, history):
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
        self.tasted = tasted
        self.farm = farm
        self.barley = barley
        self.hops = hops
        self.malting = malting
        self.bio = bio
        self.food = food
        self.education = education
        try:
            self.creation_date = arrow.get(creation_date,
                                           ["MMMM YYYY", "YYYY"], locale="fr")
        except:
            self.creation_date = None
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

	print('Loading URL')
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
    next_year = arrow.now() + datetime.timedelta(days=365)
    print('Geocoding %s adresses' % len(brasseries))
    bar = progressbar.ProgressBar()
    for brasserie in bar(brasseries):
	sys.stdout.flush()
        point = geocode(brasserie.get_address())
        if point:
            features.append(Feature(geometry=point, properties={
                "name": brasserie.name,
                "description": brasserie.get_popup_content(),
                "start": brasserie.creation_date.isoformat(),
                "end": next_year.isoformat(),
            }))
        else:
            not_found.append(brasserie)
    return FeatureCollection(features), not_found


def save_to_geojson(scrapped, destination):
    features, not_found = render_geojson(scrapped)
    with codecs.open(destination, 'w', encoding='utf-8') as f:
        geojson.dump(features, f)

    print('impossible de localiser ces brasseries:')
    print(', '.join([br.get_address() for br in not_found]))


def generate_creation_graph(scrapped, destination):
    import plotly
    import plotly.graph_objs as go
    # We only need the data for the last 20 years, excluding this year.
    now = datetime.datetime.now()
    then = now.year - 20
    creation_by_year = Counter([s.creation_date.year
                                for s in scrapped if s.creation_date
                                and then <= s.creation_date.year < now.year])
    # Sort to get the oldest first.
    x, y = zip(*sorted(creation_by_year.items()))
    plotly.offline.plot({
        "data": [go.Scatter(x=x, y=y, mode='lines')],
        "layout": go.Layout(title="Création de brasseries par années. Données de http://projet.amertume.free.fr/", )
    }, filename=destination)

if __name__ == '__main__':
    import sys
    scrapper = BeerScrapper()
    scrapped = scrapper.scrap()
    if len(sys.argv) >= 2 and sys.argv[1] == 'graph':
        generate_creation_graph(scrapped, 'brasseries.html')
    else:
        save_to_geojson(scrapped, 'brasseries.geojson')
