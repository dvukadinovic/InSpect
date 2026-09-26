def load_spectrum(path):
    cube = IntensityCube()
    cube.read_from_file(path)
    return cube

from dataclasses import dataclass
from .array_types import FloatArray3D, FloatArray2D, FloatArray1D
import numpy as np
import netCDF4 as nc

_WAVELENGTH_AXIS: int = 0

@dataclass
class LineParameters:
    cog: float
    cog_err: float
    eqwd: float
    eqwd_err: float
    
class CubeIsNotProcessedException(Exception):
    pass 

@dataclass
class MeanLineProfile:
    wavelengths: FloatArray1D
    flux: FloatArray1D
    flux_err: FloatArray1D

class IntensityCube:
    """
    Parameters:
    -----------
    wavelengths: FloatArray1D
        1D array of wavelengths
    intensities : FloatArray3D
        intensity cube 3D (Nwavelengths, Nx, Ny)
    continuums: FloatArray2D
        level of continuum in each pixel, 2D float array (Nx, Ny), Optional 
    """
    def __init__(self, wavelengths=None, intensities=None, continuums=None, center_of_gravity=None,equivalent_widths=None, weights=None, is_cube_processed=None, outliers=None, cog_grad=None):
        self.wavelengths = wavelengths
        self.intensities = intensities
        self.continuums = continuums
        self.center_of_gravity = center_of_gravity
        self.equivalent_widths = equivalent_widths
        self.weights = weights
        self.is_cube_processed = is_cube_processed
        self.outliers = outliers
        self.cog_grad = cog_grad

    def read_from_file(self, filename):
        """
        Reads the data from an HDF5 file and initializes the cube parameters.

        Parameters:
        -----------
        filename : str
            Path to the file containing the data.
        """
        with nc.Dataset(filename) as dataset:
            # Read intensity and wavelength data
            self.intensities = dataset["Intensity"][:].data
            self.wavelengths = dataset["wave"][:].data
        # Set the cube as not processed initially
        self.is_cube_processed = False
        # print(f"Data loaded from {filename} successfully.")

    def average_in_subdomains(self, block_dim_x: int = 16, block_dim_y: int = 16):
        Nz, Nx, Ny = self.intensities.shape
        self.intensities = self.intensities.reshape(Nz, Nx // block_dim_x, block_dim_x, Ny // block_dim_y, block_dim_y).mean(axis=(2, 4))
        #return self

    def process_cube(self) -> "IntensityCube":
        continuums = self._compute_continuums()
        normalized_intencities = self._normalize_intensities(
            intensities=self.intensities,
            continuums=continuums
        )
        mask_outliers = np.ones(np.shape(normalized_intencities), dtype=bool)
        mask_outliers[np.abs(normalized_intencities)>2] = 0

        cog = self._compute_center_of_gravity(
            normalized_intencities=normalized_intencities*mask_outliers
        )
        eqwd = self.compute_equivalent_widths(
            normalized_intencities=normalized_intencities*mask_outliers,
            wavelengths=self.wavelengths
        )
        weights = self._compute_weights_for_averaging(
            continuums=continuums
        )

        #gradient = self._compute_intensity_gradient()
        #gradient[gradient>0] = 0

        #cog_grad = self._compute_grad_max(
        #    gradient*mask_outliers
        #)

        return IntensityCube(
            wavelengths=self.wavelengths,
            intensities=normalized_intencities,
            continuums=continuums,
            center_of_gravity=cog,
            equivalent_widths=eqwd,
            weights=weights, 
            is_cube_processed=True,
            outliers=mask_outliers,
            #cog_grad=cog_grad
        )

    def _compute_intensity_gradient(self) -> FloatArray3D:
        return np.gradient(self.intensities, self.wavelengths, axis=0)

    def _compute_grad_max(self, gradient: FloatArray3D) -> FloatArray2D:
        from numpy.polynomial import Polynomial
        ind_max = np.argmax(np.abs(gradient), axis=0)
        nw, nx, ny = self.intensities.shape
        for idx in range(nx):
            for idy in range(ny):
                _ind = ind_max[idx,idy]
                out = Polynomial.fit(self.wavelengths[_ind-3:_ind+3], self.intensities[_ind-3:_ind+3,idx,idy], deg=2).convert().coef 
        print(-out[1]/2/out[2])

        return self.intensities[0]

    def _compute_continuums(self) -> FloatArray2D:
        continuums = self.intensities[10, :, :]#np.max(self.intensities, axis=_WAVELENGTH_AXIS)
        return continuums
    
    def _normalize_intensities(
        self, 
        intensities: FloatArray3D,
        continuums: FloatArray2D
    ) -> FloatArray3D: 
        return intensities/continuums[np.newaxis, :, :]

    def _compute_center_of_gravity(
        self,
        normalized_intencities: FloatArray3D
    ) -> FloatArray2D:
        numerator = np.sum(
            self.wavelengths[:, np.newaxis, np.newaxis] * \
                (1. - normalized_intencities), axis=_WAVELENGTH_AXIS
        )
        denominator = np.sum(1. - normalized_intencities, axis=_WAVELENGTH_AXIS)
        return numerator / denominator

    def compute_equivalent_widths(
        self,
        normalized_intencities: FloatArray3D,
        wavelengths: FloatArray1D
    ) -> FloatArray2D:
        intens_norm = 1. - normalized_intencities
        equivalent_widths = np.trapz(intens_norm, wavelengths, axis=_WAVELENGTH_AXIS)
        self.equivalent_widths = equivalent_widths
        return equivalent_widths
    
    def _compute_weights_for_averaging(
        self,
        continuums: FloatArray2D
    ) -> FloatArray2D:
        return continuums/np.mean(continuums)

    def _compute_weighted_mean_cog_and_standard_deviation(
        self,
        data_array: FloatArray2D,
        weights: FloatArray2D
    ):
        weighted_mean = self._compute_weighted_mean(
            data_array=data_array,
            weights=weights
        )
        nominator = self._compute_nominator(
            data_array=data_array,
            weights=weights,
            weighted_mean=weighted_mean
        )    
        denominator = self._compute_denominator(
            weights=weights
        )
        weighted_rms = np.sqrt(nominator / denominator)
        return weighted_mean, weighted_rms
    
    def _compute_weighted_mean(
        self,
        data_array: FloatArray2D,
        weights: FloatArray2D
    ):
        return np.sum(data_array * weights) / np.sum(weights)
    
    def _compute_nominator(
        self,
        data_array: FloatArray2D,
        weights: FloatArray2D,
        weighted_mean: float
    ) -> float:
        return np.sum(weights * (data_array - weighted_mean) ** 2)

    def _compute_denominator(
        self,
        weights: FloatArray2D
    ) -> float:
        np_elements = np.count_nonzero(weights)
        return np.sum(weights) * (np_elements - 1) / np_elements

    def compute_line_parameters(self) -> LineParameters:
        if self.is_cube_processed:
            cog_weighted_mean, cog_weighted_rms = self._compute_weighted_mean_cog_and_standard_deviation(
                data_array=self.center_of_gravity,
                weights=self.weights
            )
            eqwd_weighted_mean, eqwd_weighted_rms = self._compute_weighted_mean_cog_and_standard_deviation(
                data_array=self.equivalent_widths,
                weights=self.weights
            )
            return LineParameters(
                cog=cog_weighted_mean,
                cog_err=cog_weighted_rms,
                eqwd=eqwd_weighted_mean,
                eqwd_err=eqwd_weighted_rms
            )
        else:
            raise CubeIsNotProcessedException

    def compute_mean_profile_and_scatter(
        self
    ) -> MeanLineProfile:
        if self.is_cube_processed:
           profiles = np.reshape(self.intensities, (self.intensities.shape[0], self.intensities.shape[1]*self.intensities.shape[2]))
           mean_profile = np.mean(profiles, axis=1)
           scatter = np.std(profiles, axis=1)
           return MeanLineProfile(
             wavelengths=self.wavelengths,
             flux=mean_profile,
             flux_err=scatter
           )
        else:
            raise CubeIsNotProcessedException
