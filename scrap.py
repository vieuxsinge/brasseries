# -*- coding: utf-8 -*-
from __future__ import print_function
from collections import Counter
import codecs
import datetime
import json
import sys
import urllib
import pickle
import operator
import os.path

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
    def __init__(self, name, address, postal_code, city, website, tasted, farm, barley, hops,
                 malting, bio, food, education, creation_date, close_date,
                 history=None, fallback_creation_date=None,
                 fallback_close_date=None):
        self.name = name
        self.address = address
        self.postal_code = postal_code
        if postal_code.startswith("98") or postal_code.startswith("97"):
            region_code = postal_code[0:3]
        else:
            region_code = postal_code[0:2]
        self.region_code = region_code
        self.city = city
        self.website = website
        self.tasted = tasted
        self.farm = farm
        self.barley = barley
        self.hops = hops
        self.malting = malting
        self.bio = bio
        self.food = food
        self.education = education
        self.longlat = (None, None)

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
            return (g.lng, g.lat)
        return None
    except Exception as e:
        print(e)
        return None


def geocode_brasseries(brasseries):
    not_found = []
    bar = progressbar.ProgressBar()
    with requests.Session() as session:
        for brasserie in bar(brasseries):
            longlat = geocode(brasserie, session)
            brasserie.longlat = longlat
            if not longlat:
                not_found.append(brasserie)
    return brasseries, not_found


def render_geojson(brasseries):
    """Converts the list of brasseries into geojson."""
    features = []
    for brasserie in brasseries:
        if brasserie.longlat:
            features.append(Feature(geometry=Point(brasserie.longlat), properties={
                "name": brasserie.name,
                "website": brasserie.website,
                "history": brasserie.history,
                "start": brasserie.creation_date.isoformat(),
                "end": brasserie.close_date.isoformat(),
            }))
    return FeatureCollection(features)


def save_to_geojson(scrapped, destination):
    features = render_geojson(scrapped)
    with codecs.open(destination, 'w', encoding='utf-8') as f:
        f.write('onLoadData(');
        geojson.dump(features, f)
        f.write(');');


def has_start_and_end(brewery):
    """Return only closed breweries when we know the creation and close date"""
    return brewery.creation_date is not None and brewery.close_date is not None


def enhance_data(data, breweries, population):
    for feature in data['features']:
        region_code = feature['properties']['code']
        population_ = int(population.get(region_code, 0))
        breweries_ = int(breweries.get(region_code, 0))

        feature['properties']['breweries'] = breweries_
        feature['properties']['population'] = population_
        if population_ == 0:
            print("missing data for region", region_code)
        if region_code == '971':
            from pdb import set_trace; set_trace()
        feature['properties']['breweries_per_capita'] = round((breweries_ * 1000000.0 / population_), 2)
    return data

def accumulate(iterable, func=operator.add):
    it = iter(iterable)
    total = next(it)
    yield total
    for element in it:
        total = func(total, element)
        yield total

def generate_creation_graph(scrapped, destination):
    import plotly
    import plotly.graph_objs as go
    # We only need the data for the last 20 years, excluding this year.
    now = datetime.datetime.now()
    then = now.year - 20
    creation_by_year = Counter([s.creation_date.year
                                for s in scrapped if s.creation_date
                                and then <= s.creation_date.year <= now.year])
    # Sort to get the oldest first.
    x, y = zip(*sorted(creation_by_year.items()))
    from pdb import set_trace; set_trace();
    # Accumulate the number of breweries per year
    plotly.offline.plot({
        "data": [go.Scatter(x=x, y=list(accumulate(y)), mode='lines')],
        "layout": go.Layout(title="Création de brasseries par années. Données de http://projet.amertume.free.fr/", )
    }, filename=destination)

if __name__ == '__main__':
    closed_scrapper = BeerScrapper(URL_BRASSERIES_FERMEES)
    closed_scrapper.scrap()
    closed_breweries = filter(has_start_and_end, closed_scrapper.retrieved)

    active_scrapper = BeerScrapper(URL_BRASSERIES_ACTIVES, fallback_creation_date='Janvier 2016', fallback_close_date='Decembre 2018')
    scrapped = active_scrapper.scrap()

    if len(sys.argv) >= 2 and sys.argv[1] == 'graph':
        generate_creation_graph(scrapped, 'app/graph.html')

    elif len(sys.argv) >= 2 and sys.argv[1] == 'departements':
        # Count the breweries by region
        by_departements = Counter([b.region_code for b in active_scrapper.retrieved])
        with open('data/departements.geojson') as f:
            departements = json.load(f)
        with open('data/population.json') as f:
            population = json.load(f)
        data = enhance_data(departements, by_departements, population)
        with open('app/data/breweries_per_department.js', 'w+') as f:
            f.write("var brasseriesData = " + json.dumps(data) + ";");

    elif len(sys.argv) >= 2 and sys.argv[1] == 'timeline':
        if (os.path.exists('pickle.json')):
            with open('pickle.json', 'r') as f:
                brasseries = pickle.load(f)
        brasseries, not_found = geocode_brasseries(active_scrapper.retrieved)
        print('%s brasseries sont impossibles à geolocaliser' % len(not_found))
        with open('pickle.json', 'w+') as f:
            f.write(pickle.dumps(brasseries))
        # save_to_geojson(active_scrapper.retrieved + closed_breweries, 'timeline/brasseries.geojson.jsonp')
        save_to_geojson(brasseries, 'app/data/geocoded_breweries.geojson.jsonp')
