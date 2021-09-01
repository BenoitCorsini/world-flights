import os
import os.path as osp
import pandas as pd
import numpy as np
from shapefile import Reader

from map import WorldMap


class MapDataset(object):

    def __init__(self,
                 data_folder='data',
                 shapes_folder='ne_110m_land',
                 locations_folder='ne_110m_populated_places',
                 routes_file='1000 Largest City Pairs by Number of Passengers.xlsx'):
    	'''
    	The 'MapDataset' class is useful to generate the airports and flights from the given data.
    	For other types or sources of data, only this code can be adapted.
    	'''
        self.data_folder = data_folder
        self.shapes_folder = shapes_folder
        self.locations_folder = locations_folder
        self.routes_file = routes_file

        self.shapes_map = self.__load__(self.shapes_folder)
        self.locations_map = self.__load__(self.locations_folder)
        self.__locations__()
        self.routes_df = pd.read_excel(osp.join(self.data_folder, self.routes_file))
        self.__routes__()

    def __load__(self, folder, extensions=['cpg', 'dbf', 'prj', 'shp', 'shx']):
    	'''
    	Loads a shapefile object.
    	'''
        kwargs = {}
        for extension in extensions:
            extension_file = osp.join(self.data_folder, folder, folder + '.' + extension)
            if osp.exists(extension_file):
                kwargs[extension] = open(extension_file, 'rb')

        return Reader(**kwargs)

    def __locations__(self):
    	'''
    	Transforms the 'locations_map' into a dictionary.
    	'''
        self.locations = {}
        for record in self.locations_map.records():
            self.locations[record.NAME.lower()] = {
                'coord' : (record.LONGITUDE, record.LATITUDE),
            }

    def __routes__(self, metric='Passenger Miles'):
    	'''
    	Transforms the 'routes_df' into a dictionary.
    	'''
        self.routes = {}
        self.max_metric = 0
        for _, line in self.routes_df.iterrows():
            M = line[metric]
            RO = line['ORIGIN_CITY_NAME - DEST_CITY_NAME'].replace(' Total', '')

            if RO != 'Grand':
                city1, city2 = RO.split(' - ')
                city1 = city1.split(', ')[0].lower()
                city2 = city2.split(', ')[0].lower()
                if (city1 in self.locations) & (city2 in self.locations):
                    self.routes[city1, city2] = {
                        'metric' : M
                    }
                    self.max_metric = max(self.max_metric, M)

        self.max_metric = self.scale(self.max_metric)

    @staticmethod
    def scale(value):
    	'''
    	Rescaling the values of the metric, for aesthetic reasons.
    	'''
        return value **.5

    def to_shapes(self):
    	'''
    	Transforms a class instance into its shapes, used as input of the class 'WorldMap'.
    	'''
        shapes = []
        for shape in self.shapes_map.shapes():
            shapes.append(shape.points)

        return shapes

    def to_airports(self):
    	'''
    	Transforms a class instance into its airports, used as input of the class 'WorldFlights'.
    	'''
        airports = {}
        for cities, infos in self.routes.items():
            ratio = self.scale(infos['metric'])/self.max_metric
            for city in cities:
                if city not in airports:
                    airports[city] = {
                        'coord' : self.locations[city]['coord'],
                        'ratio' : ratio,
                    }
                else:
                    airports[city]['ratio'] = max(airports[city]['ratio'], ratio)

        return airports

    def to_flights(self):
    	'''
    	Transforms a class instance into its flights, used as input of the class 'WorldFlights'.
    	'''
        flights = {}
        for cities, infos in self.routes.items():
            flights[cities] = {
                'ratio' : self.scale(infos['metric'])/self.max_metric
            }

        return flights