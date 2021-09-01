import argparse

from data import MapLoader
from animate import WorldAnimation
from config import PARAMS


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--name', type=str, default='world',
        help='the name of the saved animation')
    parser.add_argument('--save_folder', type=str, default='.',
        help='where to save the animation')
    parser.add_argument('--frames_dir', type=str, default='frames',
        help='where to save the frames of the animation')
    parser.add_argument('--fps', type=int, default=20,
        help='the frames per second of the animation')
    parser.add_argument('--title', type=str, default='',
        help='the title to put on the animation')
    parser.add_argument('--n_angles', type=int, default=9,
        help='the number of angles for the earth to rotate around itself')
    parser.add_argument('--n_rotations', type=int, default=1,
        help='the number of rotations of the earth')
    parser.add_argument('--plot_airports', type=int, default=1,
        help='if the airports should be plotted on the animation (0 = not plotted; 1 = plotter)')
    parser.add_argument('--plot_flights', type=int, default=1,
        help='if the flights should be plotted on the animation (0 = not plotted; 1 = plotter)')
    parser.add_argument('--plot_airplanes', type=int, default=1,
        help='if the airplanes should be plotted on the animation (0 = not plotted; 1 = plotter)')

    kwargs = vars(parser.parse_args())

    loader = MapLoader()
    Anim = WorldAnimation(
        shapes=loader.to_shapes(),
        airports=loader.to_airports(),
        flights=loader.to_flights(),
        params=PARAMS
    )
    Anim.make(**kwargs)
