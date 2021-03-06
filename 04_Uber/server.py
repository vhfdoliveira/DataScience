import os
import folium
import json
import pandas as pd
from branca.colormap import linear
import numpy as np
from shapely.geometry import Polygon
from shapely.geometry import Point
from numpy import random

from uber_rides.session import Session
from uber_rides.client import UberRidesClient
import csv
import datetime as dt
from time import sleep

import requests


def nearest_road_distance(log, lat):
	#server = 'localhost:5000'
	server = 'router.project-osrm.org'
	service = 'nearest'
	version = 'v1'
	profile = 'car'
	
	#url = 'http://localhost:5000/nearest/v1/car/-35.155470,-5.787052'
	url = ('http://' + server + '/' + service + '/' + version +
		   '/' + profile + '/' + str(log) + ',' + str(lat) )
	
	try:
		response = requests.get(url)
		response_json = json.loads(response.text)
	
		distance = response_json.get('waypoints')[0]['distance']
	except:
		distance = float('inf')
	
	return distance



# return a number of points inside the polygon
def generate_random(number, polygon, neighborhood, max_distance):
    list_of_points = []
    minx, miny, maxx, maxy = polygon.bounds
    counter = 0
    while counter < number:
        x = random.uniform(minx, maxx)
        y = random.uniform(miny, maxy)
        pnt = Point(x, y)
        if polygon.contains(pnt) and nearest_road_distance(x, y) <= max_distance:
            list_of_points.append([x,y,neighborhood])
            counter += 1
    return list_of_points



INTERVAL = 7

print('Initializing server...')

try:
	session = Session(server_token='tph9nxWtIXGsrN1X_sBqs2LY10C88FaJpxYK_U6v')
	client = UberRidesClient(session)
	
	print('Uber client initialized')

except:
	print('Unable to stablish client connection with Uber.')


# import geojson file about natal neighborhood
natal_neigh = os.path.join('geojson', 'natal.geojson')

# load the data and use 'UTF-8'encoding
geo_json_natal = json.load(open(natal_neigh,encoding='UTF-8'))


k = 0
#initial_time = dt.datetime.now() - dt.timedelta(minutes=INTERVAL)
initial_time = dt.datetime.now()
while True:
	if dt.datetime.now() >= initial_time:
		k = k+1
		print('\n\nCollecting the data.')
		print('Iteration number: ', k )
		print('\n\n')
		
		number_of_points = 2

		file = open('db.csv','a')
		writer = csv.writer(file)
		
		# search all features
		for feature in geo_json_natal['features']:
			# get the name of neighborhood
			neighborhood = feature['properties']['name']
			# take the coordinates (lat,log) of neighborhood
			geom = feature['geometry']['coordinates']
			# create a polygon using all coordinates
			polygon = Polygon(geom[0])
			
			max_distance = 400
			# return number_of_points by neighborhood as a list [[log,lat],....]
			points = generate_random(number_of_points,polygon, neighborhood, max_distance)
			# iterate over all points and print in the map
			for i,value in enumerate(points):
				log, lat, name = value

				try:
					response = client.get_products(lat,log)

					# API - get/products
					products = response.json.get('products')
					for product in products:
						now = dt.datetime.now()

						try:
							wait_time = client.get_pickup_time_estimates(lat,log,
												product['product_id'])

							row = [wait_time.json.get('times')[0]['localized_display_name'],
								   lat,
								   log,
								   neighborhood,
								   now,
								   wait_time.json.get('times')[0]['estimate']]

							writer.writerow(row)
							print(row)

						except:
							pass
				except:
					pass        

		file.close()
		
		initial_time = initial_time + dt.timedelta(minutes=INTERVAL)
	
	#wait 10 seconds
	sleep(10)
	
	
