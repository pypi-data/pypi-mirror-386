"""
gnss_status.py

GNSS Status class.

Container for the latest readings from the GNSS receiver.

Created on 07 Apr 2022

:author: semuadmin (Steve Smith)
:copyright: 2020 semuadmin
:license: BSD 3-Clause
"""

from datetime import datetime, timezone


class GNSSStatus:
    """
    GNSS Status class.
    Container for the latest readings from the GNSS receiver.
    """

    def __init__(self):
        """
        Constructor.
        """

        self.utc = datetime.now(timezone.utc).time().replace(microsecond=0)  # UTC time
        self.lat = 0.0  # latitude as decimal
        self.lon = 0.0  # longitude as decimal
        self.alt = 0.0  # height above sea level m
        self.hae = 0.0  # height above ellipsoid m
        self.speed = 0.0  # speed m/s
        self.track = 0.0  # track degrees
        self.fix = "NO FIX"  # fix type e.g. "3D"
        self.siv = 0  # satellites in view
        self.sip = 0  # satellites in position solution
        self.pdop = 0.0  # dilution of precision DOP
        self.hdop = 0.0  # horizontal DOP
        self.vdop = 0.0  # vertical DOP
        self.hacc = 0.0  # horizontal accuracy m
        self.vacc = 0.0  # vertical accuracy m
        self.diff_corr = 0  # DGPS correction status True/False
        self.diff_age = 0  # DGPS correction age seconds
        self.diff_station = "N/A"  # DGPS station id
        self.base_ecefx = 0.0  # base station ECEF X
        self.base_ecefy = 0.0  # base station ECEF Y
        self.base_ecefz = 0.0  # base station ECEF Z
        self.rel_pos_heading = 0.0  # rover relative position heading
        self.rel_pos_length = 0.0  # rover relative position distance
        self.acc_heading = 0.0  # rover relative position heading accuracy
        self.acc_length = 0.0  # rover relative position distance accuracy
        self.rel_pos_flags = []  # rover relative position flags
        self.gsv_data = {}  # list of satellite tuples (gnssId, svid, elev, azim, cno)
        self.version_data = {}  # dict of hardware, firmware and software versions
        self.sysmon_data = {}  # dict of system monitor data (cpu and memory load, etc.)
        self.spectrum_data = []  # list of spectrum data (spec, spn, res, ctr, pga)
        self.comms_data = {}  # dict of comms port utilisation (tx and rx loads)
        self.imu_data = {}  # dict of imu data (roll, pitch, yaw, status)
