import os
import os.path as osp
import cv2
from shutil import rmtree

from flights import WorldFlights


class WorldAnimation(WorldFlights):

    def __init__(self, **kwargs):
        '''
        The 'WorldAnimation' class builds on the 'WorldFlights' class
        and animates the globe and the airplanes.
        '''
        super().__init__(**kwargs)

    def make_frames(self,
                    frames_dir='frames',
                    title='',
                    n_angles=9,
                    n_rotations=1,
                    plot_airports=True,
                    plot_flights=True,
                    plot_airplanes=True):
        '''
        Creates the frames for the animation.
        '''
        if osp.exists(frames_dir):
            rmtree(frames_dir)
        os.makedirs(frames_dir)

        index = 0
        shift = 9*2021 # to skew the starting point of the airplanes
        for index_rotation in range(n_rotations):
            for index_angle in range(n_angles):
                angle = index_angle*360/n_angles

                self.set_figure()
                self.plot_globe(angle)

                if plot_airports:
                    self.plot_airports(angle)
                if plot_flights:
                    self.plot_flights(angle)
                if plot_airplanes:
                    self.plot_airplanes(angle, airplanes_index=index + shift)

                self.savefig(f'{index:04d}', frames_dir, title)
                index += 1

    def frames_to_video(self, name='world', folder='.', frames_dir='frames', fps=20):
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
            fps,
            (w, h)
        )

        for frame in frames:
            image = cv2.imread(frame)
            video.write(image)

        video.release()
        cv2.destroyAllWindows()

        return video_file

    def make(self,
             name='world',
             folder='.',
             frames_dir='frames',
             fps=20,
             title='',
             n_angles=9,
             n_rotations=1,
             plot_airports=True,
             plot_flights=True,
             plot_airplanes=True):
        '''
        Makes the animation of the world.
        '''
        if n_angles*n_rotations > 10000:
            raise Exception('Too many frames for the video! You really want to see that earth spin, don\'t ya?')

        print(f'Number of frames to be made: {n_angles*n_rotations}')
        print(f'* check-out the folder \'{frames_dir}/\' to see the frames being made *')

        self.make_frames(frames_dir, title, n_angles, n_rotations, plot_airports, plot_flights, plot_airplanes)
        print('Frames done, combining them...')

        video_file = self.frames_to_video(name, folder, frames_dir, fps)
        print(f'Video ready at \'{video_file}\'')