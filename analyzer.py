import loader

import matplotlib.pyplot as plt

import tracks


def analyze(file):

	flap = loader.load_file(file)

	track = tracks.get_track("monza")

	plt.plot(flap['dist_lap'], flap['speedkmh'])
	plt.plot(flap['dist_lap'], flap['brake'])
	plt.plot(flap['dist_lap'], flap['throttle'])

	plt.show()

	track.analyze(flap)
