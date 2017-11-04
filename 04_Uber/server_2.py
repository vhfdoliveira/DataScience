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
		print('Distance: ', distance)
	except:
		distance = float('inf')
	
	return distance



# return one point inside the polygon
def generate_random(polygon):
    minx, miny, maxx, maxy = polygon.bounds
    counter = 0
    while counter < 1:
        x = random.uniform(minx, maxx)
        y = random.uniform(miny, maxy)
        pnt = Point(x, y)
        if polygon.contains(pnt):
            counter += 1
    return pnt


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
initial_time = dt.datetime.now() - dt.timedelta(minutes=INTERVAL)
while True:
	if dt.datetime.now() >= initial_time + dt.timedelta(minutes=INTERVAL):
		k = k+1
		print('\n\nCollecting the data.')
		print('Iteration number: ', k )
		print('\n\n')
		
		file = open('db_server2.csv','a')
		writer = csv.writer(file)
		
		# search all features
		for feature in geo_json_natal['features']:
			# get the name of neighborhood
			neighborhood = feature['properties']['name']
			# take the coordinates (lat,log) of neighborhood
			geom = feature['geometry']['coordinates']
			# create a polygon using all coordinates
			polygon = Polygon(geom[0])
			
			number_of_points = 2
			counter = 0
			while counter < number_of_points:
				point = generate_random(polygon)
				log = point.x
				lat = point.y
				
				max_distance = 400
				if nearest_road_distance(log, lat) < max_distance:
					counter = counter + 1
					
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
	
	
