import pandas as pd
from logger import logger_app as logger
import os
from logic import ldparser as ldp
from logic import telemetry
import numpy as np

MIN_TIMES = {
	"monza": 100,
	"nurburgring": 110,
	"spa": 130,
	"Zolder": 80,
	# unsure
	"Imola": 90,
	"brands_hatch": 78,
	"Zandvoort": 80,
	"mount_panorama": 110
}
ABS_MIN_TIME = 60

FREQ = 100
TIMESTEP = 1 / FREQ


def minpass(l, thres):
	try:
		min_time = min(x for x in l if x >= thres)
	except:
		min_time = 0
	return min_time


def get_threshold(track_name):
	if track_name in MIN_TIMES:
		return MIN_TIMES[track_name]
	return ABS_MIN_TIME


def load_file(file_path):
	parquet_path = os.path.splitext(file_path)[0] + ".parquet"
	try:
		flap = pd.read_parquet(parquet_path)
	except:
		flap = create_parquet(file_path, parquet_path)
	return flap


def create_parquet(file_path, parquet_path):
	logger.info(f" --------- processing file {file_path}")
	head, chans = ldp.read_ldfile(file_path)

	if head.event == "AC_LIVE":
		logger.error("Detected wrong ld file, aborting")
		return

	# print(type(head))
	# print(head.venue)  # track
	# print(head.event)  # car

	# read laps from xml files
	laps = np.array(telemetry.laps(file_path))
	logger.info("Read laps")
	# create DataStore that is used later to get pandas DataFrame
	ds = telemetry.LDDataStore(chans, laps, freq=FREQ, acc=head.event != 'AC_LIVE')

	# print(ds.laps_times)
	fastest_lap_time = minpass(ds.laps_times, get_threshold(head.venue))
	if fastest_lap_time == 0:
		logger.error("Fastest lap time is way too short, maybe the file way just empty! Aborting.")
		return

	# print(f"fastest lap was {fastest_lap_time}")
	fastest_lap_ix = ds.laps_times.index(fastest_lap_time)
	# print(fastest_lap_ix)
	fastest_lap = ds.get_data_frame(lap=fastest_lap_ix)
	# print(fastest_lap.keys())

	logger.info("Got fastest lap from data.")

	# print(fastest_lap[["speedkmh", "dist_lap", "time_lap"]])

	# create parquet file
	fastest_lap_filtered = fastest_lap[["speedkmh", "throttle", "brake", "dist_lap", "time_lap"]]

	fastest_lap_filtered.to_parquet(path=parquet_path, index=True)

	logger.info(f" --------- finished processing file {file_path}")

	return fastest_lap_filtered
