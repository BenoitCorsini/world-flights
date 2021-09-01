import os
import os.path as osp
import cv2
import shutil
import matplotlib.pyplot as plt

import numpy as np
import itertools
from config import PARAMS

from flights import WorldFlights


class WorldAnimation(WorldFlights):

    def __init__(self, fps=20, **kwargs):
        super().__init__(**kwargs)
        self.fps = fps

    def make_frames(self, frames_dir='frames', title='', n_angles=360, n_rotations=1, plot_airports=True, plot_flights=True, plot_airplanes=True):
        if osp.exists(frames_dir):
            shutil.rmtree(frames_dir)
        os.makedirs(frames_dir)

        index = 0
        skew = np.random.randint(12345)
        for _ in range(n_rotations):
            for i_angle in range(n_angles):
                angle = i_angle*360/n_angles

                self.set_figure()
                self.plot_globe(angle)
                if plot_airports:
                    self.plot_airports(angle)
                if plot_flights:
                    if plot_airplanes:
                        self.plot_flights(angle, general_index=skew + index)
                    else:
                        self.plot_flights(angle)
                self.savefig(f'{index:04d}', frames_dir, title)
                index += 1

    def frames_to_video(self, name='world', folder='.', frames_dir='frames'):
        '''
        Transforms a directory of frames into a video.
        '''
        if not osp.exists(folder):
            os.makedirs(folder)

        frames = [osp.join(frames_dir, file) for file in sorted(os.listdir(frames_dir))]

        h, w, _ = cv2.imread(frames[0]).shape

        video_file = osp.join(folder, name + '.avi')
        video = cv2.VideoWriter(
            video_file,
            cv2.VideoWriter_fourcc(*'XVID'),
            self.fps,
            (w, h)
        )

        for frame in frames:
            image = cv2.imread(frame)
            video.write(image)

        video.release()
        cv2.destroyAllWindows()

    def make(self, name='world', folder='.', frames_dir='frames', title='', n_angles=360, n_rotations=1, plot_airports=True, plot_flights=True, plot_airplanes=True):
        if n_angles*n_rotations > 10000:
            raise Exception('Too many frames for the video! You really want to see that earth spin don\'t ya?')

        print(f'Number of frames to be made: {n_angles*n_rotations}')

        self.make_frames(frames_dir, title, n_angles, n_rotations, plot_airports, plot_flights, plot_airplanes)
        self.frames_to_video(name, folder, frames_dir)

    def combine(self, name='world', folder='.', frames_dir='frames', folder_1='frames_1', folder_2='frames_2', overlap=100):
        if osp.exists(frames_dir):
            shutil.rmtree(frames_dir)
        os.makedirs(frames_dir)

        files_1 = sorted(os.listdir(folder_1))
        files_2 = sorted(os.listdir(folder_2))
        assert len(files_1) == len(files_2)

        for file_1, file_2 in zip(files_1, files_2):
            image_1 = plt.imread(osp.join(folder_1, file_1))
            image_2 = plt.imread(osp.join(folder_2, file_2))
            assert np.size(image_1) == np.size(image_2)

            image = np.concatenate([image_1[:,:-overlap,:], image_2[:,overlap:,:]], axis=1)
            #image = np.concatenate([image_1, image_2[2*overlap:,:,:]], axis=0)
            r = np.size(image, axis=1)/np.size(image, axis=0)

            plt.figure(figsize=(r*self.params['figure']['size'], self.params['figure']['size']))
            plt.imshow(image)
            plt.subplots_adjust(left=0, right=1, bottom=0, top=1)
            plt.axis('off')
            plt.savefig(osp.join(frames_dir, file_1))
            plt.close('all')

        self.frames_to_video(name, folder, frames_dir)

if __name__ == '__main__':
    N = 10
    np.random.seed(27)
    airports = {f'airport {i}': {'coord':(x,y)} for i, (x,y) in enumerate(zip(np.random.rand(N)*360 - 180,np.random.rand(N)*180 - 90))}
    flights = {(x,y): {'size':1} for x,y in itertools.product(airports, airports) if (x != y) & (np.random.rand() < 2/N)}

    WA = WorldAnimation(airports=airports, flights=flights, params=PARAMS)
    WA.make(n_rotations=2, n_angles=180, title='Test')