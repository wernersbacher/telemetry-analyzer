class Brakezone:
	def __init__(self, begin, end):
		self.begin = begin
		self.end = end

		# to be set
		self.brake_full_begin = 0
		self.brake_end_begin = 0


class Track:

	def __init__(self):
		self.brakingzones = []

	def add_brakezone(self, brakezone: Brakezone):
		self.brakingzones.append(brakezone)


monza = Track()
monza.add_brakezone(Brakezone(500, 1000))
monza.add_brakezone(Brakezone(1900, 2150))

TRACKS = {"monza": monza}


def get_track(name):

	if name in TRACKS:
		return TRACKS[name]
	else:
		raise Exception("Track no implemented yet")
