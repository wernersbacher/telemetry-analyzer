import matplotlib.pyplot as plt

SILENT = True


class Brakezone:
    def __init__(self, begin, end):
        self.begin = begin
        self.end = end

        # to be set
        self.speed_dropoff_begin = 0
        self.braking_full_begin = 0
        self.braking_full_end = 0

    def load(self, flap):
        self.braking_full_begin, self.braking_full_end, self.speed_dropoff_begin = self.calc(flap)

    def analyze(self, flap):
        braking_full_begin, braking_full_end, speed_dropoff_begin = self.calc(flap)

        if braking_full_begin > self.braking_full_begin + 5:
            print("You are braking too late!")
        if braking_full_begin < self.braking_full_begin - 5:
            print("You are braking too early!")

    def calc(self, flap):
        df = flap[(flap["dist_lap"] > self.begin) & (flap["dist_lap"] < self.end)]

        braking_full_begin = df.loc[(df['brake'] >= 95).idxmax(), "dist_lap"]
        braking_full_end = df.loc[
            df.loc[df['brake'] >= 95].last_valid_index(),
            "dist_lap"]

        speed_dropoff_begin = df.loc[df['speedkmh'].idxmax(), 'dist_lap']

        if not SILENT:
            ## debugging
            print(f"braking_full_begin={braking_full_begin}, braking_full_end={braking_full_end}")

            print(f"speed_dropoff_begin={speed_dropoff_begin}")

            plt.plot(df['dist_lap'], df['speedkmh'])
            plt.plot(df['dist_lap'], df['brake'])
            plt.plot(df['dist_lap'], df['throttle'])

            plt.show()

        return braking_full_begin, braking_full_end, speed_dropoff_begin


class Track:

    def __init__(self):
        self.zones = []
        self.loaded = False

    def add_zone(self, zone):
        self.zones.append(zone)

    def load(self, flap):
        for z in self.zones:
            z.load(flap)
        self.loaded = True

    def analyze(self, flap):
        if not self.loaded:
            print("Not loaded yet, so loading files")
            self.load(flap)
            return

        print("Analyzing flap...")
        for z in self.zones:
            z.analyze(flap)


monza = Track()

monza.add_zone(Brakezone(500, 1000))
monza.add_zone(Brakezone(1900, 2150))

TRACKS = {"monza": monza}


def get_track(name):
    if name in TRACKS:
        return TRACKS[name]
    else:
        raise Exception("Track no implemented yet")
