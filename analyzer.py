import loader

import matplotlib.pyplot as plt
import pandas as pd

import tracks


def analyze(file):

	flap = loader.load_file(file)

	track = tracks.get_track("monza")

	plt.plot(flap['dist_lap'], flap['speedkmh'])
	plt.plot(flap['dist_lap'], flap['brake'])
	plt.plot(flap['dist_lap'], flap['throttle'])

	plt.show()

	analyze_brakezones(flap, track)


def analyze_brakezones(flap, track):

	for zone in track.brakingzones:

		df = flap[(flap["dist_lap"] > zone.begin) & (flap["dist_lap"] < zone.end)]

		braking_full_begin = df.loc[(df['brake'] >= 95).idxmax(), "dist_lap"]
		braking_full_end = df.loc[
			df.loc[df['brake'] >= 95].last_valid_index(),
		"dist_lap"]

		print(braking_full_begin, braking_full_end)

		plt.plot(df['dist_lap'], df['speedkmh'])
		plt.plot(df['dist_lap'], df['brake'])
		plt.plot(df['dist_lap'], df['throttle'])

		plt.show()

		speed_dropoff_begin = df.loc[df['speedkmh'].idxmax(), 'dist_lap']

		print(speed_dropoff_begin)

