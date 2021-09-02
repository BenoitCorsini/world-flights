# Flights of the World

This project represents flights on a world globe and animates it.
It originated during the [11th Montreal Industrial Problem Workshop](http://crm.umontreal.ca/probindustrielsEn2021/) when I was working on the problem given by [IATA](https://www.iata.org/).

## Getting started

### Running the code

The library requirements for this code can be found in `requirements.txt`. To install them, run the following command line in the terminal:
```sh
pip install -r requirements.txt
```
In its current form, this project also uses data with restricted access.
In order for the code to properly run, download [this file](https://data.world/garyhoov/us-airline-route-segments-2015/workspace/file?filename=1000+Largest+City+Pairs+by+Number+of+Passengers.xlsx) into the `data/` folder.
Once the required libraries are installed and the previous file is downloaded, run the following:
```sh
python main.py
```

### Organization of the code

`map.py` contains the class `WorldMap` which is able to represent the world globe from any given angle.

`flights.py` builds on the class `WorldMap` to define the class `WorldFlights`, able to represent airports and flights on the globe.
It also has a feature to represent _airplanes_ as moving points on the routes defined by the flights.

`animate.py` builds on the class `WorldFlights` to define the class `WorldAnimation`, able to animate the previously defined images by building multiple frames and combining them into a video.

`main.py` wraps evverything together and is used to run the algorithms.

`config.py` is an extra file containing all the configuration parameters of this model and `data.py` is used to load the datasets and output them in the desired format.

### The data

To construct the world map and to represent the flights, two dataset sources were used.

- The website [Natural Earth](https://www.naturalearthdata.com/) was used to access the shapes of the continents and the locations of the airports.
- The website [data.world](https://data.world/) was used to access the data on the flights. More precisely, the flights data come from the [US Airline Route Segments 2015](https://data.world/garyhoov/us-airline-route-segments-2015) dataset by [Gary Hoover](https://data.world/garyhoov).

The code implemented in this project is meant to be adaptable.
The three datasets used here can easily be modified and the code in `data.py` can be adapted to other inputs.
As long as the `MapLoader` class contains the functions `to_shapes()`, `to_airports()`, and `to_flights()`, launching `main.py` will work and output the desired result.

## Results

This code can produce map images but is mainly intended for its animation purpose. Typical results look like the following.

<p align="center"><img width="50%" src="figures/animation.gif"/></p>.

## Contact and information

If you have any questions regarding the code, feel free to contact me at <benoitcorsini@gmail.com>.
