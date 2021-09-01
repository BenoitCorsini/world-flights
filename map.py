import os
import os.path as osp
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle
from shapefile import Reader

from config import PARAMS


class WorldMap(object):

    def __init__(self, shapes=[], params=PARAMS):
        '''
        The 'WorldMap' class is useful in constructing a 3D figure of the world map
        and contains basic function to normalize and project map coordinates.  
        '''
        self.shapes = shapes
        self.params = params

        self.globe = None # a globe useful to clip the figures

    @staticmethod
    def normalize_angle(angle):
        '''
        Normalizes any angle to be in [-180,180).
        '''
        while angle >= 180:
            angle -= 360

        while angle < -180:
            angle += 360

        assert (angle >= -180) & (angle < 180) # checking that 'angle' is well-normalized

        return angle

    @staticmethod
    def project(coord, angle=0, turn=0, flip=False, r=1, away=10):
        '''
        Projects the coordinates on the 3D map.
        'turn' is useful for coordinates partly at the left/right end of the other side of the globe.
        'away' is useful to avoid having non-desired lines on the map.
        '''
        x, y = coord
        y = y*np.pi/180
        x = x - angle + turn*360
        unseen = False # if the coordinates are on the other side of the globe

        pos_x = r*np.sin(x*np.pi/180)*np.cos(y)
        pos_y = r*np.sin(y)
        d = pos_x**2 + pos_y**2

        if (x > 90) & (d <= 1):
            pos_x = away*r*np.cos(y)
            pos_y *= away
            unseen = True
        elif (x < -90) & (d <= 1):
            pos_x = - away*r*np.cos(y)
            pos_y *= away
            unseen = True

        if flip:
            pos_x = - pos_x

        return (pos_x, pos_y), unseen

    def set_figure(self):
        '''
        Resets the figure.
        '''
        if hasattr(self, 'fig'):
            plt.close('all')

        # creating the general figure
        self.fig, self.ax = plt.subplots(figsize=[self.params['figure']['size']]*2)
        self.fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        self.ax.set_axis_off()
        extra = 1 + self.params['figure']['extra_space']
        self.ax.set_xlim(-extra, extra)
        self.ax.set_ylim(-extra, extra)

        if self.params['figure']['background'] is not None:
            self.ax.add_patch(Rectangle(
                xy=(-2*extra, -2*extra),
                width=4*extra,
                height=4*extra,
                color=self.params['figure']['background'],
                zorder=self.params['zorder']['background']
            ))

    def plot_globe(self, angle=0):
        '''
        Plots the globe and its shade as viewed from 'angle'.
        '''
        angle = self.normalize_angle(angle)

        self.globe = Circle(
            xy=(0, 0),
            radius=1,
            color=self.params['globe']['water_colour'],
            zorder=self.params['zorder']['water'],
            lw=0,
        )
        self.ax.add_patch(self.globe)

        for shape in self.shapes:
            for turn in [-1, 0, 1]: # to cover for the boundary problems
                points, unseen = zip(*[self.project(point, angle, turn) for point in shape])
                if not all(unseen):
                    # the border of the land
                    self.ax.add_patch(Polygon(
                        xy=points,
                        color=self.params['globe']['border_colour'],
                        zorder=self.params['zorder']['land_border'],
                        lw=self.params['globe']['border'],
                        clip_path=self.globe,
                        joinstyle='round',
                    ))
                    # the main land
                    self.ax.add_patch(Polygon(
                        xy=points,
                        color=self.params['globe']['land_colour'],
                        zorder=self.params['zorder']['land'],
                        lw=0,
                        clip_path=self.globe,
                    ))

        # plotting the shade
        self.plot_shade(angle)

    def plot_shade(self, angle=0):
        '''
        Plots the shaded version of the globe.
        '''
        angle = self.normalize_angle(angle + self.params['shade']['angle'])

        # general transformation applied on the shade
        transform = self.ax.transData.get_affine()
        x_shift = transform.get_matrix()[0,2]
        y_shift = transform.get_matrix()[1,2]
        x_scale = transform.get_matrix()[0,0]
        y_scale = transform.get_matrix()[1,1]

        transform.set_matrix(np.diag(np.diag(transform.get_matrix()))) # only keep the diagonal
        transform.scale(
            self.params['shade']['ratio']*self.params['shade']['scale'],
            self.params['shade']['scale']
        )
        transform.rotate_deg(self.params['shade']['rotation'])
        transform.translate(
            x_shift + x_scale*self.params['shade']['x_pos'],
            y_shift - y_scale + y_scale*self.params['shade']['y_pos']
        )

        # plotting the shaded world sphere
        self.ax.add_patch(Circle(
            xy=(0, 0),
            radius=1,
            color=self.params['shade']['water_colour'],
            zorder=self.params['zorder']['shade_water'],
            alpha=self.params['shade']['alpha'],
            transform=transform,
            lw=0,
        ))
        for shape in self.shapes:
            for turn in [-1, 0, 1]: # to cover for the boundary problems
                points, unseen = zip(*[self.project(point, angle, turn, flip=True, away=1) for point in shape])
                if not all(unseen):
                    self.ax.add_patch(Polygon(
                        xy=points,
                        color=self.params['shade']['land_colour'],
                        zorder=self.params['zorder']['shade_land'],
                        alpha=self.params['shade']['alpha'],
                        transform=transform,
                        lw=0,
                    ))

    def savefig(self, name='map', folder='.', title=''):
        '''
        Saves the current state of the figure.
        '''
        assert hasattr(self, 'fig')

        if not osp.exists(folder):
            os.makedirs(folder)

        # adds a title when available
        if title:
            bbox = {
                'boxstyle' : 'round',
                'edgecolor' : self.params['text']['colour'],
                'facecolor' : self.params['text']['background'],
                'linewidth' : self.params['text']['border'],
            }
            self.ax.text(
                - 1 - self.params['figure']['extra_space'] + self.params['text']['x'],
                - 1 - self.params['figure']['extra_space'] + self.params['text']['y'],
                title,
                fontsize=self.params['text']['fontsize'],
                color=self.params['text']['colour'],
                #fontweight='demibold',
                bbox=bbox,
            )

        self.fig.savefig(osp.join(folder, name + '.png'), transparent=True)

    def plot(self, name='map', folder='.', title='', angle=0):
        '''
        Plots the world globe.
        '''
        self.set_figure()
        self.plot_globe(angle)
        self.savefig(name, folder, title)