import numpy as np
import pandas as pd
import os
import xml.etree.ElementTree as ET

from pandas.errors import InvalidIndexError

from logger import logger_worker as logger

class DataStore(object):
    @staticmethod
    def create_track(df, laps_times=None):
        # dx = (2*r*np.tan(alpha/2)) * np.cos(heading)
        # dy = (2*r*np.tan(alpha/2)) * np.sin(heading)
        # dx = df.ds * np.cos(df.heading)
        # dy = df.ds * np.sin(df.heading)

        # calculate correction to close the track
        # use best lap
        if laps_times is None:
            df_ = df
        else:
            fastest = np.argmin([999999 if x == 0 else x for x in laps_times])
            df_ = df[(df.lap == fastest)]
        fac = 1.
        dist = None
        n = 0
        while n < 1000:
            dx = df_.ds * np.cos(df_.heading * fac)
            dy = df_.ds * np.sin(df_.heading * fac)
            end = (dx.cumsum()).values[-1], (dy.cumsum()).values[-1]
            # print(end, dist, fac)

            newdist = np.sqrt(end[0] ** 2 + end[1] ** 2)
            if dist is not None and newdist > dist: break
            dist = newdist
            fac -= 0.0001
            n += 1

        if n == 1000:
            fac = 1.

        # recalculate with correction
        df.alpha = df.alpha * fac
        df.heading = df.alpha.cumsum()
        dx = df.ds * np.cos(df.heading * fac)
        dy = df.ds * np.sin(df.heading * fac)
        x = dx.cumsum()
        y = dy.cumsum()

        df = pd.concat([df, pd.DataFrame(
            {'x': x, 'y': y,
             'dx': dx, 'dy': dy,
             })], axis=1)

        return df

    @staticmethod
    def calc_over_understeer(df):
        # calculate oversteer, based on math in ACC MoTec workspace
        wheelbase = 2.645
        df['neutral_steering'] = (wheelbase * df.alpha * 180 / np.pi).rolling(10).mean()
        df['steering_corr'] = df.steerangle / 11
        df['oversteer'] = np.sign(df.g_lat) * (df['neutral_steering'] - df['steering_corr'])
        df['understeer'] = df['oversteer']
        df.at[df['understeer'] > 0, 'understeer'] = 0
        return df

    @staticmethod
    def add_cols(df, laps_limits=None, lap=None):
        if 'speedkmh' not in df.columns:
            df['speedkmh'] = df.speed * 3.6
        if 'speed' not in df.columns:
            df['speed'] = df.speedkmh / 3.6

        # create list with the distance
        dv = df['speed'] - df['speed'].shift(1, fill_value=df['speed'][0])
        df['ds'] = (df.speed + dv) * df.dt
        # division by zero ...
        df.at[0, 'ds'] = 0
        # create list with total time
        t = df.dt.cumsum()

        # create list with the lap number, distance in lap, time in lap
        s = df.ds.cumsum().values
        if laps_limits is None:
            l, sl, tl = [lap] * len(s), s, t
        else:
            l, sl, tl = [], [], []
            for n, (n1, n2) in enumerate(laps_limits):
                l.extend([n] * (n2 - n1))
                sl.extend(list(s[n1:n2] - s[n1]))
                tl.extend(list(t[n1:n2] - t[n1]))

        # for calculate of x/y position on track from speed and g_lat
        if 'heading' not in df.columns:
            gN = 9.81
            r = 1 / (gN * df.g_lat / df.speed.pow(2))
            alpha = df.ds / r
            df['heading'] = alpha.cumsum()
        else:
            alpha = []
            for a, b in zip(df['heading'], df['heading'].shift(1, fill_value=df['heading'][0])):
                if a - b > np.pi:
                    alpha.append(a - abs(b))
                elif b - a > np.pi:
                    alpha.append(abs(a) - b)
                else:
                    alpha.append(a - b)

        # add the lists to the dataframe
        df = pd.concat([df, pd.DataFrame(
            {'lap': l,
             'g_sum': df.g_lon.abs() + df.g_lat.abs(),
             'alpha': alpha,
             'dist': s, 'dist_lap': sl,
             'time': t, 'time_lap': tl})], axis=1)

        return df

    def get_data_frame(self, lap=None):
        pass


class LDDataStore(DataStore):
    def __init__(self, channs, laps, freq=20, acc=True):
        self.channs = channs
        self.acc = acc
        self.freq = freq
        self.n = self.freq * len(self.channs[0].data) // self.channs[0].freq
        self.columns = {}
        self._df = None
        self.laps_limits = laps_limits(laps, self.freq, self.n)
        self.laps_times = laps_times(laps)
        # print('Scaling to %i Hz' % self.freq)

    def chan_name(self, x):
        if self.acc: return x.name.lower()
        return ac_chan_map[x.name] \
            if x.name in ac_chan_map \
            else x.name.lower()

    def __getitem__(self, item):
        if item not in self.columns:
            # print("Creating column %s"%(item))

            col = [n for n, x in enumerate(self.channs) if self.chan_name(x) == item]
            if len(col) != 1:
                raise Exception("Could not reliably get column", col)
            col = col[0]

            n = len(self.channs[col].data)
            x = np.linspace(0, n, self.n)
            data = np.interp(x, np.arange(0, n), self.channs[col].data)

            # convert some of the data from ld file to integer
            if (self.acc and col in [7, 11, 12]) or (not self.acc and col in [62]):
                data = data.astype(int)
            # downsample channels to the one with lowest frequency (this takes way tooo long)
            # if len(data) != self.n:
            #     data = signal.resample(data, self.n)

            self.columns[item] = data
        return self.columns[item]

    def get_data_frame(self, lap=None):
        for x in self.channs:
            _ = self[self.chan_name(x)]

        df = pd.DataFrame(self.columns)
        logger.info("Available columns in data frame for get_frame_data:")
        logger.info(df.keys())
        df['dt'] = 1 / self.freq
        df = DataStore.add_cols(df, self.laps_limits)
        df = DataStore.create_track(df)
        try:
            df = DataStore.calc_over_understeer(df)
        except InvalidIndexError as e:
            # columns couldnt be found for understeer calculation, just skipping.
            logger.warning("Dataframe hadn't the correct indices for calculating over and understeer!")

        if lap is not None:
            df = df[df.lap == lap]
        return df


def laps_limits(laps, freq, n):
    """find the start/end indizes of the data for each lap
    """
    laps_limits = []
    if laps[0] != 0:
        laps_limits = [0]
    laps_limits.extend((np.array(laps) * freq).astype(int))
    laps_limits.extend([n])
    return list(zip(laps_limits[:-1], laps_limits[1:]))


def laps_times(laps):
    """calculate the laptime for each lap"""
    laps_times = []
    if len(laps) == 0:
        return laps_times
    if laps[0] != 0:
        laps_times = [laps[0]]
    laps_times.extend(list(laps[1:] - laps[:-1]))
    return laps_times


def laps(f):
    laps = []
    tree = ET.parse(os.path.splitext(f)[0] + ".ldx")
    root = tree.getroot()

    # read lap times
    for lap in root[0][0][0][0]:
        laps.append(float(lap.attrib['Time']) * 1e-6)
    return laps


# map from acti names to ACC names
ac_chan_map = {
    'ABS Active': 'abs',
    'Brake Pos': 'brake',
    'Brake Temp FL': 'brake_temp_lf',
    'Brake Temp FR': 'brake_temp_rf',
    'Brake Temp RL': 'brake_temp_lr',
    'Brake Temp RR': 'brake_temp_rr',
    'CG Accel Lateral': 'g_lat',
    'CG Accel Longitudinal': 'g_lon',
    'Engine RPM': 'rpms',
    'Gear': 'gear',
    'Ground Speed': 'speedkmh',
    'Steering Angle': 'steerangle',
    'Suspension Travel FL': 'sus_travel_lf',
    'Suspension Travel FR': 'sus_travel_rf',
    'Suspension Travel RL': 'sus_travel_lr',
    'Suspension Travel RR': 'sus_travel_rr',
    'TC Active': 'tc',
    'Throttle Pos': 'throttle',
    'Wheel Angular Speed FL': 'wheel_speed_lf',
    'Wheel Angular Speed FR': 'wheel_speed_rf',
    'Wheel Angular Speed RL': 'wheel_speed_lr',
    'Wheel Angular Speed RR': 'wheel_speed_rr',
    'Tire Pressure FL': 'tyre_press_lf',
    'Tire Pressure FR': 'tyre_press_rf',
    'Tire Pressure RL': 'tyre_press_lr',
    'Tire Pressure RR': 'tyre_press_rr',
    'Tire Temp Core FL': 'tyre_tair_lf',
    'Tire Temp Core FR': 'tyre_tair_rf',
    'Tire Temp Core RL': 'tyre_tair_lr',
    'Tire Temp Core RR': 'tyre_tair_rr',
}

# map from pyacc shm names to ACC names
acc_shmem_map = {
    'packetId': 'packetId',
    'abs': 'abs',
    'brake': 'brake',
    'brakeTemp': ['brake_temp_lf',
                  'brake_temp_rf',
                  'brake_temp_lr',
                  'brake_temp_rr'],
    'accG': ['g_lat', 'accG', 'g_lon'],
    'rpms': 'rpms',
    'gear': 'gear',
    'roll': 'roll',
    'speedKmh': 'speedkmh',
    'steerAngle': 'steerangle',
    'heading': 'heading',
    'suspensionTravel': ['sus_travel_lf',
                         'sus_travel_rf',
                         'sus_travel_lr',
                         'sus_travel_rr'],
    'tc': 'tc',
    'gas': 'throttle',
    'wheelSlip': ['wheel_slip_lf',
                  'wheel_slip_rf',
                  'wheel_slip_lr',
                  'wheel_slip_rr'],
    'wheelAngularSpeed': ['wheel_speed_lf',
                          'wheel_speed_rf',
                          'wheel_speed_lr',
                          'wheel_speed_rr'],
    'wheelsPressure': ['tyre_press_lf',
                       'tyre_press_rf',
                       'tyre_press_lr',
                       'tyre_press_rr'],
    'tyreContactPoint': ['tyre_contact_point_lf',
                         'tyre_contact_point_rf',
                         'tyre_contact_point_lr',
                         'tyre_contact_point_rr'],
    'tyreCoreTemperature': ['tyre_tair_lf',
                            'tyre_tair_rf',
                            'tyre_tair_lr',
                            'tyre_tair_rr'],
    'carDamage': ['damage_front',
                  'damage_rear',
                  'damage_left',
                  'damage_right',
                  'damage_centre']
}
