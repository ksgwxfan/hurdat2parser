
class Hurdat2Aliases:

    @property
    def tc(self):
        return self._tc

    @property
    def season(self):
        return self._season

class SeasonAliases:

    @property
    def year(self):
        return self._year

    @property
    def tc(self):
        return self._tc

    # Energy Indices lower-case shortcuts 
    @property
    def ace(self):
        return self.ACE

    @property
    def hdp(self):
        return self.HDP

    @property
    def mhdp(self):
        return self.MHDP

class TropicalCycloneAliases:

    @property
    def atcfid(self):
        return self._atcfid

    @property
    def atcf_num(self):
        return self._atcf_num

    @property
    def storm_number(self):
        return self.atcf_num

    @property
    def year(self):
        return self._year

    @property
    def name(self):
        return self._name

    @property
    def entry(self):
        return self._entry

    # Energy Indices lower-case shortcuts
    @property
    def ace(self):
        return self.ACE

    @property
    def hdp(self):
        return self.HDP

    @property
    def mhdp(self):
        return self.MHDP

class TCEntryAliases:
    __slots__ = []

    @property
    def index(self):
        """
        Returns the index that this object appears in the parent
        <TropicalCyclone>.entry list.
        """
        return self._tc.entry.index(self)

    # Datetime stuff
    @property
    def entrytime(self):
        """Returns the datetime.datetime for this entry."""
        return self._entrytime

    @property
    def time(self):
        """Returns the datetime.datetime for this entry."""
        return self.entrytime

    @property
    def date(self):
        """Returns the datetime.datetime for this entry."""
        return self.entrytime

    @property
    def hour(self):
        """Returns the recorded hour of this entry."""
        return self.entrytime.hour

    @property
    def minute(self):
        """Returns the recorded minute of this entry."""
        return self.entrytime.minute

    @property
    def month_day_tuple(self):
        """Returns a tuple of the month and day of the month for this entry."""
        return (self.date.month, self.date.day)

    # Stats

    @property
    def record_identifier(self):
        """
        Returns the record identifier (think Landfall indicator) for this
        entry.
        """
        return self._record_identifier

    @property
    def status(self):
        """
        Returns the designated storm status acquired at the time of this entry.
        """
        return self._status

    @property
    def lat_str(self):
        """Returns the Hurdat2-formatted latitude string for this entry."""
        return self._lat_str

    @property
    def lon_str(self):
        """Returns the Hurdat2-formatted longitude string for this entry."""
        return self._lon_str


    @property
    def lat(self):
        """Returns the latitude coordinate in decimal degrees for this entry."""
        return self._lat

    @property
    def latitude(self):
        """Returns the latitude coordinate in decimal degrees for this entry."""
        return self.lat

    @property
    def lon(self):
        """Returns the longitude coordinate in decimal degrees for this entry."""
        return self._lon

    @property
    def longitude(self):
        """Returns the longitude coordinate in decimal degrees for this entry."""
        return self.lon

    @property
    def location_rev(self):
        return self.location_reversed

    @property
    def wind(self):
        """
        Returns the recorded maximum sustained winds in knots for this entry.
        """
        return self._wind

    @property
    def status_desc(self):
        """
        Returns a readable description of the designated status of the storm at
        the time of this entry.
        """
        return self._status_desc

    @property
    def mslp(self):
        """Returns the Mean Sea Level Pressure in hPa (same as mb)."""
        return self._mslp

    # extent_TS
    @property
    def tsNE(self):
        """
        Returns the tropical storm-strength (>= 34kts) wind extent experienced
        in the cyclone's northeast quadrant.
        """
        return self._tsNE

    @property
    def tsSE(self):
        """
        Returns the tropical storm-strength (>= 34kts) wind extent experienced
        in the cyclone's southeast quadrant.
        """
        return self._tsSE

    @property
    def tsSW(self):
        """
        Returns the tropical storm-strength (>= 34kts) wind extent experienced
        in the cyclone's southwest quadrant.
        """
        return self._tsSW

    @property
    def tsNW(self):
        """
        Returns the tropical storm-strength (>= 34kts) wind extent experienced
        in the cyclone's northwest quadrant.
        """
        return self._tsNW

    # extent_TS50
    @property
    def ts50NE(self):
        """
        Returns the gale-force (>= 50kts) wind extent experienced in the
        cyclone's northeast quadrant.
        """
        return self._ts50NE

    @property
    def ts50SE(self):
        """
        Returns the gale-force (>= 50kts) wind extent experienced in the
        cyclone's southeast quadrant.
        """
        return self._ts50SE

    @property
    def ts50SW(self):
        """
        Returns the gale-force (>= 50kts) wind extent experienced in the
        cyclone's southwest quadrant.
        """
        return self._ts50SW

    @property
    def ts50NW(self):
        """
        Returns the gale-force (>= 50kts) wind extent experienced in the
        cyclone's northwest quadrant.
        """
        return self._ts50NW

    # extent_HU
    @property
    def huNE(self):
        """
        Returns the hurricane-force (>= 64kts) wind extent experienced in the
        cyclone's northeast quadrant.
        """
        return self._huNE

    @property
    def huSE(self):
        """
        Returns the hurricane-force (>= 64kts) wind extent experienced in the
        cyclone's southeast quadrant.
        """
        return self._huSE

    @property
    def huSW(self):
        """
        Returns the hurricane-force (>= 64kts) wind extent experienced in the
        cyclone's southwest quadrant.
        """
        return self._huSW

    @property
    def huNW(self):
        """
        Returns the hurricane-force (>= 64kts) wind extent experienced in the
        cyclone's northwest quadrant.
        """
        return self._huNW

    @property
    def maxwind_radius(self):
        """
        Returns the radius from the center where the maximum winds are being
        experienced in nautical miles.
        """
        return self._maxwind_radius

















