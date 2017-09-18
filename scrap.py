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
import geocoder
import requests

URL_BRASSERIES_ACTIVES = 'http://projet.amertume.free.fr/html/liste_brasseries.htm'
URL_BRASSERIES_FERMEES = 'http://projet.amertume.free.fr/html/liste_brasseries_fermees.htm'


class Brasserie(object):
    def __init__(self, name, address, postal_code, city, tel, portable, fax,
                 email, contact, website, tasted, farm, barley, hops,
                 malting, bio, food, education, creation_date, close_date,
                 history=None, fallback_creation_date=None,
                 fallback_close_date=None):
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

        self.creation_date = parse_date(creation_date, fallback=fallback_creation_date)
        if history:
            self.close_date = parse_date(close_date, fallback=fallback_close_date)
        else:
            history = close_date
            self.close_date = parse_date(fallback_close_date)
        self.history = history

    def get_popup_content(self):
        return u"\n".join([self.tel, self.website, self.email, self.history])


class BeerScrapper(object):

    def __init__(self, url, fallback_creation_date=None, fallback_close_date=None):
        self.url = url
        self.retrieved = []
        self.fallback_creation_date = fallback_creation_date
        self.fallback_close_date = fallback_close_date

    def scrap(self):
        """Scrap a page, put the results in the self.tracks attribute."""
        def clean_text(txt):
            return (txt.replace('\n', '')
                       .replace('\t', ''))
            # XXX Need to change encoding.

	    print('Loading URL %s' % self.url)
        d = pq(url=self.url)
        for col in list(d.find('#table1>tr'))[1:]:
            self.retrieved.append(
                Brasserie(*[clean_text(c.text_content()) for c in col],
                          fallback_creation_date=self.fallback_creation_date,
                          fallback_close_date=self.fallback_close_date))
        return self.retrieved


def parse_date(string, fallback=False):
    try:
        parsed = arrow.get(string, ["MMMM YYYY", "YYYY"], locale="fr")
    except:
        if fallback:
            parsed = arrow.get(fallback, ["MMMM YYYY", "YYYY"], locale="fr")
        else:
            parsed = None
    return parsed


def geocode(brasserie, session):
    # return Point((0,0))
    address = u"%s, %s" % (brasserie.city, brasserie.postal_code)
    try:
        g = geocoder.google(address, session=session)
        if g.ok:
            return Point((g.lng, g.lat))
        return None
    except Exception as e:
        print(e)
        return None


def render_geojson(brasseries):
    """Converts the list of brasseries into geojson."""
    features = []
    not_found = []
    print('Geocoding %s adresses' % len(brasseries))
    bar = progressbar.ProgressBar()
    with requests.Session() as session:
        for brasserie in bar(brasseries):
            point = geocode(brasserie, session)
            if point:
                features.append(Feature(geometry=point, properties={
                    "name": brasserie.name,
                    "tel": brasserie.tel,
                    "website": brasserie.website,
                    "email": brasserie.email,
                    "history": brasserie.history,
                    "start": brasserie.creation_date.isoformat(),
                    "end": brasserie.close_date.isoformat(),
                }))
            else:
                not_found.append(brasserie)
    return FeatureCollection(features), not_found


def save_to_geojson(scrapped, destination):
    features, not_found = render_geojson(scrapped)
    with codecs.open(destination, 'w', encoding='utf-8') as f:
        f.write('onLoadData(');
        geojson.dump(features, f)
        f.write(');');

    print('impossible de localiser %s brasseries.' % len(not_found))


def has_start_and_end(brewery):
    """Return only closed breweries when we know the creation and close date"""
    return brewery.creation_date is not None and brewery.close_date is not None


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
    closed_scrapper = BeerScrapper(URL_BRASSERIES_FERMEES)
    closed_scrapper.scrap()
    closed_breweries = filter(has_start_and_end, closed_scrapper.retrieved)

    active_scrapper = BeerScrapper(URL_BRASSERIES_ACTIVES, fallback_creation_date='Janvier 2016', fallback_close_date='Novembre 2017')
    scrapped = active_scrapper.scrap()

    if len(sys.argv) >= 2 and sys.argv[1] == 'graph':
        generate_creation_graph(scrapped, 'brasseries.html')
    else:
        save_to_geojson(active_scrapper.retrieved + closed_breweries, 'timeline/brasseries.geojson.jsonp')
