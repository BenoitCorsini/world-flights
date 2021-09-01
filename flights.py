import os
import os.path as osp
from matplotlib.patches import Ellipse
import numpy as np

from map import WorldMap


class WorldFlights(WorldMap):

    def __init__(self, airports={}, flights={}, **kwargs):
        '''
        The 'WorldFlights' class builds on the 'WorldMap' class
        and adds flights, airplanes, and airports representations.
        The pairs of airports in 'flights' should also belong to 'airports'.

        The dictionaries 'airports' and 'flights' are expected to be as follows:

        ###############################################################
        ##                                                           ##
        ##  airports = {                                             ##
        ##    airport_name : {                                       ##
        ##      'coord' : (longitude_in_degree, latitude_in_degree)  ##
        ##      'ratio' : some_normalized_airport_metric,            ##
        ##    }                                                      ##
        ##  }                                                        ##
        ##                                                           ##
        ###############################################################

        ####################################################
        ##                                                ##
        ##  flights = {                                   ##
        ##    (airport_name_1, airport_name_2) : {        ##
        ##      'ratio' : some_normalized_flight_metric,  ##
        ##    }                                           ##
        ##  }                                             ##
        ##                                                ##
        ####################################################
        '''
        super().__init__(**kwargs)
        self.airports = airports
        self.flights = flights
        self.__path__()

    def __path__(self):
        '''
        Pre-compute the paths of all the flights.
        '''
        for a1, a2 in self.flights:
            pair = self.airports[a1]['coord'], self.airports[a2]['coord']
            self.flights[a1, a2]['path'] = self.to_path(pair)

    def to_path(self, pair):
        '''
        Finds the path between any pair of points.
        '''
        start, end = pair
        xyz = self.coord_to_xyz(np.stack([start, end]))

        n_steps = np.sum((xyz[0,:] - xyz[1,:])**2)**.5/self.params['flights']['delta_step']
        n_steps = int(np.ceil(n_steps))
        path = np.arange(n_steps + 1)/n_steps
        path = np.reshape(path, (-1, 1))
        
        path = xyz[0,:] + path*(xyz[1,:] - xyz[0,:])
        path /= np.reshape((path[:,0]**2 + path[:,1]**2 + path[:,2]**2)**.5, (-1,1))
        path = self.xyz_to_coord(path)

        return path
        
    @staticmethod
    def coord_to_xyz(coord):
        '''
        Transforms coordinates into a 3D point.
        '''
        longitude, latitude = coord[:,0]*np.pi/180, coord[:,1]*np.pi/180
        x = np.cos(longitude)*np.cos(latitude)
        y = np.sin(longitude)*np.cos(latitude)
        z = np.sin(latitude)

        return np.stack([x,y,z], axis=1)

    @staticmethod
    def xyz_to_coord(xyz):
        '''
        Transforms a 3D point into coordinates.
        '''
        latitude = np.arcsin(xyz[:,2])*180/np.pi

        x = xyz[:,0]
        zero_x = (x == 0).astype(float)
        sign_x = (x > 0).astype(float) - (x < 0).astype(float)

        y = xyz[:,1]
        zero_y = (y == 0).astype(float)
        sign_y = (y > 0).astype(float) - (y < 0).astype(float)

        alpha = (x != 0)*np.arctan(y/(x + (x==0)))*180/np.pi # the basic angle
        longitude = zero_x*90*sign_y + zero_y*(90*sign_x - 90) # if one of x or y is zero
        longitude += (1 - zero_x)*(1 - zero_y)*(alpha + sign_y*(90 - 90*sign_x))

        # checking that latitude is in [-90, 90]
        assert np.all((latitude >= -90)*(latitude <= 90))
        # checking that longitude is in [-180,180)
        assert np.all((longitude >= -180)*(longitude < 180))

        return np.stack([longitude, latitude], axis=1)

    @staticmethod
    def to_height(path, max_height=1):
        '''
        Defines the heights from a path.
        '''
        heights = np.arange(np.size(path, axis=0))/(np.size(path, axis=0) - 1)
        heights = heights*(1 - heights)
        heights = heights/np.max(heights)
        heights = 1 + heights*(max_height - 1)

        return heights

    def plot_airports(self, angle):
        '''
        Plots the airports.
        '''
        angle = self.normalize_angle(angle)

        for airport_info in self.airports.values():
            ratio = airport_info['ratio'] # the ratio of the airport
            for turn in [-1, 0, 1]:
                point, unseen = self.project(airport_info['coord'], angle, turn)
                if not unseen:
                    # the distance from the central point of the globe
                    dist = np.arccos((point[0]**2 + point[1]**2)**.5)*2/np.pi
                    # the angle from the central point of the globe
                    if point[0] == 0:
                        if point[1] > 0:
                            ang = 90
                        else:
                            ang = -90
                    else:
                        ang = np.arctan(point[1]/point[0])*180/np.pi

                    self.ax.add_patch(Ellipse(
                        xy=point,
                        width=ratio*self.params['airports']['size']*dist,
                        height=ratio*self.params['airports']['size'],
                        angle=ang,
                        facecolor=self.params['airports']['colour'],
                        edgecolor=self.params['airports']['border_colour'],
                        lw=ratio*self.params['airports']['border'],
                        zorder=self.params['zorder']['airports'],
                        clip_path=self.globe,
                        alpha=ratio,
                    ))

    def plot_flights(self, angle):
        '''
        Plots the flights.
        '''
        angle = self.normalize_angle(angle)

        for flights_info in self.flights.values():
            ratio = flights_info['ratio']
            path = flights_info['path']
            heights = self.to_height(path, max_height=self.params['flights']['max_height'])

            # segments contains a list of connected points
            # this is used for path going over the threshold for angles at -180/180
            segments = []
            points = []

            for index, (coord, height) in enumerate(zip(path, heights)):
                current_point = None
                # checking if the point is visible or not
                for turn in [-1, 0, 1]:
                    point, unseen = self.project(coord, angle, turn, r=height)
                    if not unseen:
                        current_point = point

                # if the point is visible, add to the current list of points
                if current_point is not None:
                    points.append(current_point)

                # if the point is not visible, add the points to a new segment and restart the process
                else:
                    segments.append(points)
                    points = []

            # adding the last possible segment
            segments.append(points)

            # plotting the segments
            for points in segments:
                if points: # non-empty segment
                    x, y = zip(*points)
                    # plotting the border of the flights
                    self.ax.plot(x, y,
                        solid_joinstyle='round',
                        solid_capstyle='round',
                        linewidth=ratio*self.params['flights']['size'] + self.params['flights']['border'],
                        color=self.params['flights']['border_colour'],
                        zorder=self.params['zorder']['flights_border'],
                        alpha=ratio,
                    )
                    # plotting the flights
                    self.ax.plot(x, y,
                        solid_joinstyle='round',
                        solid_capstyle='round',
                        linewidth=ratio*self.params['flights']['size'],
                        color=self.params['flights']['colour'],
                        zorder=self.params['zorder']['flights'],
                        alpha=ratio,
                    )

    def plot_airplanes(self, angle, airplanes_index=9*2021):
        '''
        Plots the airplanes.
        '''
        angle = self.normalize_angle(angle)

        for flights_info in self.flights.values():
            ratio = flights_info['ratio']
            path = flights_info['path']
            heights = self.to_height(path, max_height=self.params['flights']['max_height'])

            # segments contains a list of connected points
            # this is used for path going over the threshold for angles at -180/180
            segments = []
            points = []
            n_indices = self.params['airplanes']['n_indices'] # the number of indices to represent the planes
            airplane_index = (airplanes_index % (len(path) + n_indices)) - n_indices

            for index, (coord, height) in enumerate(zip(path, heights)):
                if (index >= airplane_index) & (index < airplane_index + n_indices):
                    current_point = None
                    # checking if the point is visible or not
                    for turn in [-1, 0, 1]:
                        point, unseen = self.project(coord, angle, turn, r=height)
                        if not unseen:
                            current_point = point

                    # if the point is visible, add to the current list of points
                    if current_point is not None:
                        points.append(current_point)

                    # if the point is not visible, add the points to a new segment and restart the process
                    else:
                        segments.append(points)
                        points = []

            # adding the last possible segment
            segments.append(points)

            # plotting the airplanes
            for points in segments:
                if points: # non-empty segment
                    x, y = zip(*points)
                    # plotting the border of the airplanes
                    self.ax.plot(x, y,
                        solid_joinstyle='round',
                        solid_capstyle='round',
                        linewidth=ratio*self.params['airplanes']['size'] + self.params['airplanes']['border'],
                        color=self.params['airplanes']['border_colour'],
                        zorder=self.params['zorder']['airplanes'],
                        alpha=ratio,
                    )
                    # plotting the airplanes
                    self.ax.plot(x, y,
                        solid_joinstyle='round',
                        solid_capstyle='round',
                        linewidth=ratio*self.params['airplanes']['size'],
                        color=self.params['airplanes']['colour'],
                        zorder=self.params['zorder']['airplanes'],
                        alpha=ratio,
                    )

    def plot(self, name='map', folder='.', title='', angle=0):
        '''
        Plots the airports, flights, and airplanes on the globe.
        '''
        self.set_figure()
        self.plot_globe(angle)
        self.plot_airports(angle)
        self.plot_flights(angle)
        self.plot_airplanes(angle)
        self.savefig(name, folder, title)


if __name__ == '__main__':
    N = 10
    np.random.seed(0)
    airports = {
        str(a) : {
            'coord' : (x,y),
            'ratio' : 1
        }
        for (a,x,y) in zip(
            np.random.rand(N),
            360*np.random.rand(N) - 180,
            180*np.random.rand(N) - 90,
        )
    }

    flights = {}
    for _ in range(N):
        a1 = np.random.choice(list(airports))
        a2 = np.random.choice(list(airports))
        if a1 != a2:
            flights[a1, a2] = {'ratio' : 1}


    WF = WorldFlights(airports=airports, flights=flights)
    WF.plot()