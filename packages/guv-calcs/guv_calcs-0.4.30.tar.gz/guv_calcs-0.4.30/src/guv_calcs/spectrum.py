import csv
import warnings
from importlib import resources
import numpy as np
import matplotlib.pyplot as plt
from .io import load_csv, rows_to_bytes


class Spectrum:
    """
    Attributes:
        wavelengths: 1d arraylike
            wavelength values in nanometers
        intensities: 1d arraylike
            relative intensity values in arbitrary units
        weights: dict
            Dictionary containing spectral weights. Keys are labels for the weighting
            table and values are a tuple of two lists, (wavelengths, intensities).
            Generally loaded from within the package but you can pass your own if you
            really want to.
    """

    def __init__(self, wavelengths, intensities, weights=None):
        self.raw_wavelengths = np.array(wavelengths)
        self.raw_intensities = np.array(intensities)

        # sort values in case they are out of order
        sortidx = np.argsort(self.raw_wavelengths)
        self.raw_wavelengths = self.raw_wavelengths[sortidx]
        self.raw_intensities = self.raw_intensities[sortidx]

        if len(self.raw_wavelengths) != len(self.raw_intensities):
            raise ValueError("Number of wavelengths and intensities do not match.")

        # store copy for later retrieval
        self.wavelengths = self.raw_wavelengths
        self.intensities = self.raw_intensities

        self.weights = self._load_spectral_weightings() if weights is None else weights
        self.weighted_intensities = (
            None if self.weights is None else self._weight_spectra()
        )

    @classmethod
    def from_file(cls, filepath):
        """
        initialize spectrum object from file
        Be careful initializing from file, as the class assumes the file's
        first column correponds to 'Wavelengths' and the second column
        corresponds to 'Intensities'. 'Wavelengths' should be in units of
        nanometers, 'Intensities' should be in units of relative intensity.
        """
        csv_data = load_csv(filepath)
        reader = csv.reader(csv_data)
        # read each line
        spectra = []
        for i, row in enumerate(reader):
            try:
                vals = list(map(float, row))
                spectra.append((vals[0], vals[1]))
            except ValueError:
                if i == 0:  # probably a header
                    continue
                # else:
                # warnings.warn(f"Skipping invalid datarow: {row}")
        if len(spectra) == 0:
            raise ValueError("File contains no valid data.")

        wavelengths = np.array(spectra).T[0]
        intensities = np.array(spectra).T[1]
        return cls(wavelengths, intensities)

    @classmethod
    def from_dict(cls, dct):
        """
        initialize spectrum object from a dictionary where
        the first key contains wavelength values, and the second
        key contains intensity values
        """
        keys = list(dct.keys())
        wavelengths = np.array(dct[keys[0]])
        intensities = np.array(dct[keys[1]])
        return cls(wavelengths, intensities)

    def to_dict(self, as_string=False):
        spec = {}
        spec["Wavelength"] = self.wavelengths
        spec["Unweighted Relative Intensity"] = self.intensities
        if self.weighted_intensities is not None:
            for key, val in self.weighted_intensities.items():
                spec[key] = val
        if as_string:
            for key, val in spec.items():
                spec[key] = ", ".join(map(str, spec[key]))
        return spec

    def to_csv(self, fname=None):
        rows = [list(self.to_dict().keys())]
        vals = [self.wavelengths, self.intensities]
        vals += list(self.weighted_intensities.values())
        rows += list(np.array(vals).T)
        csv_bytes = rows_to_bytes(rows)
        if fname is not None:
            with open(fname, "wb") as csvfile:
                csvfile.write(csv_bytes)
        else:
            return csv_bytes

    def _log_interp(self, wvs, weight_wvs, weight_values):
        """log10 interpolation for the tlv weights"""
        logterp = np.interp(wvs, weight_wvs, np.log10(weight_values))
        return np.power(10, logterp)

    def _load_spectral_weightings(self):
        """load spectral weightings from within package"""

        fname = "UV Spectral Weighting Curves.csv"
        path = resources.files("guv_calcs.data").joinpath(fname)
        with path.open("rb") as file:
            weights = file.read()

        csv_data = load_csv(weights)
        reader = csv.reader(csv_data, delimiter=",")
        headers = next(reader, None)  # get headers

        data = {}
        for header in headers:
            data[header] = []
        for row in reader:
            for header, value in zip(headers, row):
                data[header].append(float(value))

        spectral_weightings = {}
        for i, (key, val) in enumerate(data.items()):
            if i == 0:
                wavelengths = np.array(val)
            else:
                spectral_weightings[key] = (wavelengths, np.array(val))
        return spectral_weightings

    def weight(self, standard):
        """weight by spectral effectiveness"""
        if standard in self.weights.keys():
            weight_wavelengths, weights_orig = self.weights[standard]
            weights = log_interp(self.wavelengths, weight_wavelengths, weights_orig)
            weighted_intensity = self.intensities * weights
        else:
            warnings.warn(f"{standard} not in available weightings.")
        return weighted_intensity

    def _weight_spectra(self):
        """calculate the weighted spectra"""
        weighted_intensities = {}
        maxval = max(self.intensities)
        for key, val in self.weights.items():
            weighted_intensity = self.weight(key)
            ratio = maxval / max(weighted_intensity)
            weighted_intensities[key] = weighted_intensity * ratio
        return weighted_intensities

    def _scale(self, value):
        """scale both the base and weighted intensities by a value"""
        self.intensities *= value
        if self.weighted_intensities is not None:
            for key, val in self.weighted_intensities.items():
                self.weighted_intensities[key] *= value

    def _filter(self, wavelength, intensity, minval=None, maxval=None):
        """internal method for filtering. Returns tuple (wavelength,intensity)"""
        if minval is None:
            minval = min(self.wavelengths)
        if maxval is None:
            maxval = max(self.wavelengths)
        idx1 = np.argwhere(wavelength >= minval)
        idx2 = np.argwhere(wavelength <= maxval)
        idx = np.intersect1d(idx1, idx2)
        return wavelength[idx], intensity[idx]

    def revert(self):
        """restore wavelength and intensity values to original values"""
        self.wavelengths = self.raw_wavelengths
        self.intensities = self.raw_intensities
        return self

    def filter(self, minval=None, maxval=None):
        """
        filter the spectra and weighted spectra over a wavelength range
        """
        for key, val in self.weighted_intensities.items():
            w2, i2 = self._filter(self.wavelengths, val, minval, maxval)
            self.weighted_intensities[key] = i2
        w, i = self._filter(self.wavelengths, self.intensities, minval, maxval)
        self.wavelengths = w
        self.intensities = i
        return self

    def sum(self, minval=None, maxval=None, weight=None):
        if weight in self.weighted_intensities.keys():
            intensities = self.weighted_intensities[weight]
            wavelengths, intensities = self._filter(
                self.wavelengths, intensities, minval, maxval
            )
        else:
            wavelengths, intensities = self._filter(
                self.wavelengths, self.intensities, minval, maxval
            )
        return sum_spectrum(wavelengths, intensities)

    def scale(self, power, minval=None, maxval=None):
        """
        scale the spectra to a power value, such that the total spectral
        power is equal to the value.
        optionally, consider only the power output over a range of wavelengths
        """
        spectral_power = self.sum(minval=minval, maxval=maxval)
        self._scale(power / spectral_power)
        return self

    def normalize(self, normval=1):
        """normalize the maximum intensity to a value"""
        self._scale(normval / max(self.intensities))
        return self

    def get_tlv(self, standard):
        """return the total uv dose over 8 hours for this specific lamp,
        per a particular spectral effectiveness standard. units: mJ/cm2"""
        weights = log_interp(self.wavelengths, *self.weights[standard])  # get weights
        i_new = self.intensities / self.sum()  # scale
        s_lambda = sum_spectrum(self.wavelengths, weights * i_new)
        return 3 / s_lambda

    def get_max_irradiance(self, standard):
        """return max irradiance for this specific spectra, per a particular
        spectral effectiveness standard. units: uW/cm2"""
        return self.get_tlv(standard) / 60 / 60 / 8 * 1000

    def get_seconds_to_tlv(self, irradiance, standard):
        """
        determine the number of seconds before a TLV is reached
        provided an irradiance value in uW/cm2
        and a spectral effectiveness standard
        """
        weights = log_interp(self.wavelengths, *self.weights[standard])  # get weights
        i_new = self.intensities * irradiance / self.sum()  # scale
        weighted_irradiance = sum_spectrum(self.wavelengths, weights * i_new)
        return 3000 / weighted_irradiance

    def plot(
        self,
        title="",
        fig=None,
        ax=None,
        figsize=(6.4, 4.8),
        yscale="linear",
        label=None,
        weights=False,
    ):
        """
        plot the spectra and any weighted spectra.
        `yscale` is generally either "linear" or "log", but any matplotlib
        scale is permitted
        label: str or bool or None
            if str, the spectrum will be labeled with that str. If True,
            default label is `Unweighted Relative Intensity`. If False, label
            will not be used. if
        weights: bool or str
            If not False or None,
        """

        if fig is None:
            if ax is None:
                fig, ax = plt.subplots()
            else:
                fig = plt.gcf()
        else:
            if ax is None:
                ax = fig.axes[0]

        default_label = "Unweighted Relative Intensity"
        if label:
            if isinstance(label, str):
                ax.plot(self.wavelengths, self.intensities, label=label)
            else:
                ax.plot(self.wavelengths, self.intensities, label=default_label)
        else:
            ax.plot(self.wavelengths, self.intensities)

        if weights:
            if isinstance(weights, str):
                if weights in self.weighted_intensities.keys():
                    val = self.weighted_intensities[weights]
                    ax.plot(
                        self.wavelengths,
                        self.weighted_intensities[weights],
                        label=weights,
                        alpha=0.7,
                        linestyle="--",
                    )
            elif isinstance(weights, bool):
                for key, val in self.weighted_intensities.items():
                    ax.plot(self.wavelengths, val, label=key, alpha=0.7, linestyle="--")

        if label or weights:
            ax.legend()
        ax.grid(True, which="both", ls="--", c="gray", alpha=0.3)
        ax.set_xlabel("Wavelength [nm]")
        ax.set_ylabel("Relative intensity [%]")
        ax.set_yscale(yscale)
        ax.set_title(title)
        return fig, ax


def sum_spectrum(wavelength, intensity):
    """
    sum across a spectrum.
    ALWAYS use this when summing across a spectra!!!
    """
    weighted_intensity = [
        intensity[i] * (wavelength[i] - wavelength[i - 1])
        for i in range(1, len(wavelength))
    ]
    return sum(weighted_intensity)


def log_interp(wvs, weight_wvs, weight_values):
    """log10 interpolation for the tlv weights"""
    logterp = np.interp(wvs, weight_wvs, np.log10(weight_values))
    return np.power(10, logterp)
