
class Hurdat2Aliases:

    @property
    def tc(self):
        return self._tc

    @property
    def season(self):
        return self._season

    @property
    def filesappended(self):
        return self._filesappended

class SeasonAliases:

    @property
    def year(self):
        return self._year

    @property
    def tc(self):
        return self._tc

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


class TCEntryAliases:
    __slots__ = []

    @property
    def index(self):
        return self._tc.entry.index(self)

    # Datetime stuff
    @property
    def entrytime(self):
        return self._entrytime

    @property
    def time(self):
        return self.entrytime

    @property
    def date(self):
        return self.entrytime

    @property
    def hour(self):
        return self.entrytime.hour

    @property
    def minute(self):
        return self.entrytime.minute

    @property
    def month_day_tuple(self):
        return (self.date.month, self.date.day)

    # Stats

    @property
    def record_identifier(self):
        return self._record_identifier

    @property
    def status(self):
        return self._status

    @property
    def lat_str(self):
        return self._lat_str

    @property
    def lon_str(self):
        return self._lon_str

    @property
    def location(self):
        return self._location

    @property
    def location_reversed(self):
        return tuple(reversed(self.location))

    @property
    def location_rev(self):
        return self.location_reversed

    @property
    def lat(self):
        return self._lat

    @property
    def latitude(self):
        return self.lat

    @property
    def lon(self):
        return self._lon

    @property
    def longitude(self):
        return self.lon

    @property
    def wind(self):
        return self._wind

    @property
    def status_desc(self):
        return self._status_desc

    @property
    def saffir_equiv(self):
        return self.saffir_simpson

    @property
    def mslp(self):
        return self._mslp

    @property
    def extent_TS(self):
        return [self.tsNE, self.tsSE, self.tsSW, self.tsNW]

    @property
    def tsNE(self):
        return self._tsNE

    @property
    def tsSE(self):
        return self._tsSE

    @property
    def tsSW(self):
        return self._tsSW

    @property
    def tsNW(self):
        return self._tsNW

    @property
    def extent_TS50(self):
        return [self.ts50NE, self.ts50SE, self.ts50SW, self.ts50NW]

    @property
    def ts50NE(self):
        return self._ts50NE

    @property
    def ts50SE(self):
        return self._ts50SE

    @property
    def ts50SW(self):
        return self._ts50SW

    @property
    def ts50NW(self):
        return self._ts50NW

    @property
    def extent_HU(self):
        return [self.huNE, self.huSE, self.huSW, self.huNW]

    @property
    def huNE(self):
        return self._huNE

    @property
    def huSE(self):
        return self._huSE

    @property
    def huSW(self):
        return self._huSW

    @property
    def huNW(self):
        return self._huNW

    @property
    def wind_radii(self):
        return self._wind_radii

















