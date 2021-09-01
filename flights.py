import os
import os.path as osp
from matplotlib.patches import Ellipse
import numpy as np

from map import WorldMap


class WorldFlights(WorldMap):

    def __init__(self, airports, flights, **kwargs):
        super().__init__(**kwargs)
        self.airports = airports
        self.flights = flights
        self.__path__()
        '''
        self.frames_dir = frames_dir
        if not osp.exists(osp.join(self.main_dir, self.frames_dir)):
            os.makedirs(osp.join(self.main_dir, self.frames_dir))
        '''

    def __path__(self):
        for a1, a2 in self.flights:
            pair = self.airports[a1]['coord'], self.airports[a2]['coord']
            self.flights[a1, a2]['path'] = self.to_path(pair)

    def to_path(self, pair):
        '''
        Finds the path between any pair of points
        '''
        start, end = pair
        xyz = self.coord_to_xyz(np.stack([start, end]))

        n_steps = int(np.ceil((np.sum((xyz[0,:] - xyz[1,:])**2)**.5)/self.params['flights']['delta_step']))
        path = np.arange(n_steps + 1)/n_steps
        path = np.reshape(path, (-1, 1))
        
        path = xyz[0,:] + path*(xyz[1,:] - xyz[0,:])
        path /= np.reshape((path[:,0]**2 + path[:,1]**2 + path[:,2]**2)**.5, (-1,1))
        path = self.xyz_to_coord(path)

        return path
        
    @staticmethod
    def coord_to_xyz(coord):
        '''
        Transforms coordinates into a 3D point
        '''
        longitude, latitude = coord[:,0]*np.pi/180, coord[:,1]*np.pi/180
        x, y, z = np.cos(longitude)*np.cos(latitude), np.sin(longitude)*np.cos(latitude), np.sin(latitude)

        return np.stack([x,y,z], axis=1)

    @staticmethod
    def xyz_to_coord(xyz):
        '''
        Transforms a 3D point into coordinates
        '''
        latitude = np.arcsin(xyz[:,2])*180/np.pi

        x = xyz[:,0]
        zero_x = (x == 0).astype(float)
        sign_x = (x > 0).astype(float) - (x < 0).astype(float)
        y = xyz[:,1]
        zero_y = (y == 0).astype(float)
        sign_y = (y > 0).astype(float) - (y < 0).astype(float)

        alpha = (x != 0)*np.arctan(y/(x + (x==0)))*180/np.pi

        longitude = zero_x*90*sign_y + zero_y*(90*sign_x - 90) + (1 - zero_x)*(1 - zero_y)*(alpha + sign_y*(90 - 90*sign_x))

        assert np.all((latitude >= -90)*(latitude <= 90))
        assert np.all((longitude >= -180)*(longitude < 180))

        return np.stack([longitude, latitude], axis=1)

    def to_height(self, path):
        '''
        Define the heights from a set of 
        '''
        heights = np.arange(np.size(path, axis=0))/(np.size(path, axis=0) - 1)
        heights = heights*(1 - heights)
        heights = heights/np.max(heights)
        heights = 1 + heights*(self.params['flights']['max_height'] - 1)

        return heights

    def plot_airports(self, angle):
        '''
        Plots the airports
        '''
        angle = self.normalize_angle(angle)

        for airport_info in self.airports.values():
            r = airport_info['r']
            for turn in [-1, 0, 1]:
                point, unseen = self.project(airport_info['coord'], angle, turn)
                if not unseen:
                    dist = np.arccos((point[0]**2 + point[1]**2)**.5)*2/np.pi
                    if point[0] == 0:
                        if point[1] > 0:
                            a = 90
                        else:
                            a = -90
                    else:
                        a = np.arctan(point[1]/point[0])*180/np.pi

                    self.ax.add_patch(Ellipse(
                        xy=point,
                        width=r*self.params['airports']['size']*dist,
                        height=r*self.params['airports']['size'],
                        angle=a,
                        facecolor=self.params['airports']['colour'],
                        edgecolor=self.params['airports']['border_colour'],
                        lw=self.params['airports']['border'],
                        zorder=self.params['zorder']['airports'],
                        clip_path=self.globe,
                        alpha=r,
                    ))

    def plot_flights(self, angle, general_index=None):
        '''
        Plots the flights
        '''
        angle = self.normalize_angle(angle)

        for flights_info in self.flights.values():
            r = flights_info['r']
            path = flights_info['path']
            heights = self.to_height(path)

            segments = []
            points = []
            if general_index is not None:
                n_indices = self.params['airplanes']['n_indices']
                airplane_index = (general_index % (len(path) + n_indices)) - n_indices
                airplane_segments = []
                airplane_points = []

            for index, (coord, height) in enumerate(zip(path, heights)):
                current_point = None
                for turn in [-1, 0, 1]:
                    point, unseen = self.project(coord, angle, turn, r=height)
                    if not unseen:
                        current_point = point

                if current_point is not None:
                    points.append(current_point)

                    if general_index is not None:
                        if (index >= airplane_index) & (index < airplane_index + self.params['airplanes']['n_indices']):
                            airplane_points.append(current_point)

                else:
                    segments.append(points)
                    points = []

                    if general_index is not None:
                        if (index >= airplane_index) & (index < airplane_index + self.params['airplanes']['n_indices']):
                            airplane_segments.append(airplane_points)
                            airplane_points = []

            segments.append(points)
            if general_index is not None:
                airplane_segments.append(airplane_points)

            for points in segments:
                if points:
                    x, y = zip(*points)
                    self.ax.plot(x, y,
                        solid_joinstyle='round',
                        solid_capstyle='round',
                        linewidth=r*self.params['flights']['size'] + self.params['flights']['border'],
                        color=self.params['flights']['border_colour'],
                        zorder=self.params['zorder']['flights_border'],
                        alpha=r,
                    )
                    self.ax.plot(x, y,
                        solid_joinstyle='round',
                        solid_capstyle='round',
                        linewidth=r*self.params['flights']['size'],
                        color=self.params['flights']['colour'],
                        zorder=self.params['zorder']['flights'],
                        alpha=r,
                    )

            if general_index is not None:
                for points in airplane_segments:
                    if points:
                        x, y = zip(*points)
                        self.ax.plot(x, y,
                            solid_joinstyle='round',
                            solid_capstyle='round',
                            linewidth=r*self.params['airplanes']['size'] + self.params['airplanes']['border'],
                            color=self.params['airplanes']['border_colour'],
                            zorder=self.params['zorder']['airplanes'],
                            alpha=r,
                        )
                        self.ax.plot(x, y,
                            solid_joinstyle='round',
                            solid_capstyle='round',
                            linewidth=r*self.params['airplanes']['size'],
                            color=self.params['airplanes']['colour'],
                            zorder=self.params['zorder']['airplanes'],
                            alpha=r,
                        )

    def plot(self, name='map', folder='.', title='', angle=0):
        '''
        Plots the airports and flights on the globe
        '''
        self.set_figure()
        self.plot_globe(angle)
        self.plot_airports(angle)
        self.plot_flights(angle)
        self.savefig(name, folder, title)