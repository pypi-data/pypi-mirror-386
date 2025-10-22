import numpy as np
from scipy.special import jv, voigt_profile


# We use this implementation so that the shape is not always the same at the cost of some accuracy on fwhm
def voigt_fwhm(x, fwhm, seed=0):
    """
    Generate a pseudo-voigt profile. Usually, the fwhm is defined by sigma and gamma.
    Here we use random values of sigma and gamma that respect the relationship found in https://doi.org/10.1364/JOSA.63.000987, to preserve the desired fwhm.
    We use this method to generate pseudo-voigt with a different shape each time. The seed is required to control the randomness of the shape.

    Args:
    - x (np.ndarray): The energy values
    - fwhm (float): The desired full width at half maximum of the pseudo-voigt profile. The actual fwhm will be slightly different (10% accuracy).
    - seed (int): The seed to control the randomness of the shape of the pseudo-voigt profile. If 0, a random seed will be generated.
    """
    if seed == 0:
        seed = np.random.randint(100000)
    np.random.seed(seed)
    ratio = 3.0 * np.random.rand(1)
    gamma = fwhm / (0.5346 + np.sqrt(
        0.2166 + ratio ** 2))  # inverting the approximation of https://doi.org/10.1364/JOSA.63.000987
    # it leads to roughly 10% error in the fwhm
    sigma = gamma * ratio
    profile = voigt_profile(x, sigma, gamma)
    return profile / np.max(profile)


def my_gaussian(x, mu, sig):
    """
    Generate a gaussian profile.

    Args:
    - x (np.ndarray): The energy values
    - mu (float): The mean of the gaussian profile
    - sig (float): The standard deviation of the gaussian profile
    """
    gauss = np.exp(-np.power(x - mu, 2.0) / (2 * np.power(sig, 2.0))) * (
                1 / (sig * np.sqrt(2 * np.pi)))
    return gauss


def g_distrib_temp_averaged(g, g0, ratio):
    """
    Function to take into account g-averaging in the calculation of PINEM spectra.
    It assumes that the electron pulse very broad compared to the photon pulse in the temporal domain.
    A high ratio (above 1.0) will lead to almost no g-averaging, while a low ratio (below 1.0) will lead to a strong g-averaging.

    Args:
    - g (np.ndarray): The range of g values. It is assumed to be normalized between 0 and g0.
    - g0 (float): The maximum value of g
    - ratio (float): The ratio of the temporal width of the electron pulse to the photon pulse (To be checked)
    """
    return ((1. / np.sqrt(np.pi) * ratio) * (g / g0) ** (ratio * ratio)) * 1. / (
                g * np.sqrt(np.log(g0 / g)))


# TODO : externalise the simulation to another package so that it is more flexible.

class Pinem:
    """
    PINEM spectrum simulation class. Currently the simulation takes into account one interaction only, with g averaging.

    Args:
    - x: 1D array of energy values in eV
    - kernel (np.ndarray or str): 
        np.ndarray : 1D array of the zero-loss peak in the same energy units as x and same length as x. The kernel is assumed to be centered at x=0.
        str : The type of kernel to use. Currently, only 'Voigt' and 'Gaussian' are supported.
    - amplitude: float to scale the intensity of the peaks
    - pump: float describing the energy of the subbands in eV
    - n_cutoff: int describing the number of subbands to consider
    """

    def __init__(self, x, amplitude, n_cutoff, kernel=None, plasmon=True):
        self.x = x
        # delta g is used to produce a linear distribution of g values between 0.0001*g0 and 0.9999*g0
        self.delta_g = np.linspace(0.0001, 1.0 - 0.0001, 1000)
        # number of possible g values taking into account the g averaging effect
        self.num_g = self.delta_g.shape[0]
        self.amplitude = amplitude
        self.kernel = kernel
        self.n_cutoff = n_cutoff
        self.scale = self.x[1] - self.x[0]
        self.ns, self.fns = self.gen_indices()
        self.plasmon = plasmon

    def gen_indices(self):
        """
        Generate all the reachable subband indices inside the pre-determined cutoff.

        Returns:
        - tns (np.ndarray): The subband indices inside cutoff, both positive and negative
        - ns (np.ndarray): expanded indices for all g values. It has shape (2*self.n_cutoff+1, self.num_g)
        """
        tns = np.arange(-self.n_cutoff, self.n_cutoff + 1)
        ns = tns[:, np.newaxis] * np.ones((self.num_g,))
        return ns, tns

    def gen_kernel_mattrix(self, omega, offset=0.0, fwhm=0.3, seed=0):
        """
        Generate a matrix of 'kernels' (e.g. gaussians), each 'kernel' being shifted by a different amount of energy (i.e. omega). 
        There is one 'kernel' for each allowed subband index.

        Args:
        - omega (float): The energy of the laser pulse in eV
        - offset (float): The offset of the energy scale in eV (To simulate energy shift during the experiment)
        - fwhm (float): The full width at half maximum of the kernel (gaussian or pseudo-voigt). Ignore for other kernel types.
        - seed (int): The seed to control the randomness of the shape of the pseudo-voigt profile. If 0, a random seed will be generated. Not applicable to other kernel types.

        Returns:
        - t (np.ndarray): The matrix of shifted 'kernels' (e.g. gaussians) for each subband index
        - mask_mus (np.ndarray): A mask to keep only the indices that are within the energy range of the x values
        """
        # Scaling to get the indices that are in the range of the x values (while taking into account the offset)
        fmus = self.fns * omega / self.scale + offset / self.scale
        mus = np.round(fmus).astype(int)
        # Masking out the indices that are outside the range of the x values
        mask_mus = np.abs(mus) < self.x.shape[0] / 2
        len_mask = np.sum(mask_mus)
        # Build or set the kernel
        if self.kernel == 'Voigt':
            kernel1D = voigt_fwhm(self.x, fwhm, seed=seed)
        elif self.kernel == 'Gaussian':
            kernel1D = my_gaussian(self.x, 0, fwhm / 2.355)
        else:
            kernel1D = np.roll(self.kernel)
        # Generata a matrix of kernels. One kernel for each subband index that is in the range of the x values (i.e. kept in by the mask)
        kernels = np.repeat(kernel1D[:, np.newaxis], len_mask, axis=1)
        # Shift the kernels to the right position thus building the matrix of shifted kernels
        t = np.array([np.roll(kernels[:, i], mus[mask_mus][i]) for i in range(len(mus[mask_mus]))])
        return t, mask_mus

    def calc(self, omega, g, offset=0.0, fwhm=0.3, rt=0.7, seed=0):
        """
        Calculate the complex valued PINEM spectrum. 

        Args:
        - omega (float): The energy of the laser pulse in eV
        - g (float): The g factor
        - offset (float): The offset of the energy scale in eV (To simulate energy shift during the experiment)
        - fwhm (float): The full width at half maximum of the kernel (gaussian or pseudo-voigt)
        - rt (float): The ratio of the temporal width of the electron pulse to the photon pulse (To be checked)
        - seed (int): The seed to control the randomness of the shape of the pseudo-voigt profile. If 0, a random seed will be generated. Not applicable to other kernel types.

        Returns:
        - wave (np.ndarray): The complex valued PINEM spectrum
        """
        # TODO : Check the calculation speed. It seems a bit slow.

        # Generate the g distribution, i.e. g values between 0.0001*g and 0.9999*g
        vg1 = np.tile((g * self.delta_g)[:, np.newaxis], self.ns.shape[0]).T
        g_dist = g_distrib_temp_averaged(vg1, g, rt)
        # Check if the g values are out of bounds
        assert np.isnan(g_dist).sum() == 0, 'Il y a un souci vg1 max {}, vg1 min {}, g {}'.format(
            np.max(vg1), np.min(vg1), g)
        # Generate the shifted kernels and the accessible subband indices
        kern_mat, mask_n = self.gen_kernel_mattrix(omega, offset=offset, fwhm=fwhm, seed=seed)
        # Generation of all the weights for each subband and g value
        j = jv(self.ns, 2 * vg1)
        # Summing the contribution of all the g values for each accessible subband
        js = np.sum((g_dist * j ** 2)[mask_n, :], axis=1)[:, np.newaxis]
        # Apply the weights to the shifted kernels and sum the contributions of all the accessible subbands to create the PINEM spectrum
        wave = np.sum(kern_mat * js, axis=0)

        self.kernel_matrix = kern_mat

        return wave

    def calc_sq_modulus(self, omega, g, offset=0.0, fwhm=0.3, rt=0.7, seed=0):
        """
        Function to be called to get real PINEM spectra. It returns the squared modulus of the complex PINEM simulation.
        It is first normalized to the range [0,1] and then scaled to the desired amplitude. We do it that way for a better control of the intensity of the peaks.

        Args:
        - omega (float): The energy of the laser pulse in eV
        - g (float): The g factor
        - offset (float): The offset of the energy scale in eV (To simulate energy shift during the experiment)
        - fwhm (float): The full width at half maximum of the kernel (gaussian or pseudo-voigt)
        - rt (float): The ratio of the temporal width of the electron pulse to the photon pulse (To be checked)
        - seed (int): The seed to control the randomness of the shape of the pseudo-voigt profile. If 0, a random seed will be generated. Not applicable to other kernel types.
        """
        wave = self.calc(omega, g, offset=offset, fwhm=fwhm, rt=rt, seed=seed)
        mod_wave = np.real(wave) ** 2 + np.imag(wave) ** 2
        Mwave, mwave = np.max(mod_wave), np.min(mod_wave)
        nwave = (mod_wave - mwave) / (Mwave - mwave)
        fwave = self.amplitude * nwave
        if self.plasmon:
            fwave += self.add_plasmon(self.amplitude, fwhm)
        return fwave

    def add_plasmon(self, amplitude, fwhm):
        """
        Add a plasmon peak to the PINEM spectrum. The plasmon peak is a gaussian profile.

        Args:
        - center (float): The energy of the plasmon peak in eV
        - sigma (float): The standard deviation of the gaussian profile
        - amplitude (float): The amplitude of the plasmon peak
        """
        peak_num = np.random.randint(1, 4)
        plasmon = np.zeros(self.x.shape[0])
        for i in range(peak_num):
            center = np.random.uniform(1.5, 15.0)
            sigma = fwhm * 2 * np.random.uniform(1.0, 5.0)
            amp = amplitude * np.random.uniform(0.01, 0.2)
            plasmon += amp * my_gaussian(self.x, center, sigma)

        return plasmon


class PinemGenerator():
    """
    Object managing the PINEM interfacing for live modifications of parameters in the GUI.

    Args : 
    - n (int): The number of energy values in the x axis
    - scale (float): The scale of the x axis
    - kernel (np.ndarray or str): 
        np.ndarray : 1D array of the zero-loss peak in the same energy units as x and same length as x. The kernel is assumed to be centered at x=0.
        str : The type of kernel to use. Currently, only 'Voigt' and 'Gaussian' are supported.
    - n_cutoff (int): The number of subbands to consider
    - amplitude (int): The amplitude of the PINEM spectra
    """

    def __init__(
            self,
            n: int,
            scale: float,
            kernel,
            n_cutoff: int = 20,
            k_cutoff: int = 100,
            amplitude: int = 50
    ):
        self.n = n
        self.pinem: Pinem = None
        self._rt = None
        self.x = np.linspace(-n / 2 * scale, n / 2 * scale, n)
        self.kernel = kernel
        self.n_cutoff = n_cutoff
        self._amplitude = amplitude

        self._omg = 1.5
        self._g = None
        self._fwhm = 0.7
        self._offset = None
        self.scale = scale
        self._noise = False
        self._background = 0.1
        self._remove_background = True
        self._counter = 0
        self._angles = np.linspace(0, 2 * np.pi, 360)


    ## Getters and setters ##

    # We use properties to control the values of the parameters from the GUI
    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = value
        # Changing the scale requires a change in the x values of the PINEM object
        self.x = np.linspace(-self.n / 2 * self._scale, self.n / 2 * self._scale, self.n)
        self.pinem = Pinem(x=self.x, amplitude=self._amplitude, kernel=self.kernel,
                           n_cutoff=self.n_cutoff)

    @property
    def rt(self):
        if self._rt is None:
            return 0.7
        else:
            return self._rt

    @rt.setter
    def rt(self, value):
        self._rt = value

    @property
    def amplitude(self):
        return self._amplitude

    @amplitude.setter
    def amplitude(self, value):
        self._amplitude = value
        #  It is the same as for the scale setter
        self.pinem = Pinem(x=self.x, amplitude=self._amplitude, kernel=self.kernel,
                           n_cutoff=self.n_cutoff)

    @property
    def omg(self):
        return self._omg

    @omg.setter
    def omg(self, value):
        self._omg = value

    @property
    def g(self):
        #  Currently, the g value is randomly generated if not set
        self._counter += 1
        if self._g is None:
            return 3 * (np.sin(self._angles[self._counter % 360]) ** 2)
        else:
            return self._g

    @g.setter
    def g(self, value):
        self._g = value

    @property
    def offset(self):
        # Currently, the offset is randomly generated if not set
        if self._offset is None:
            return np.random.uniform(-0.5, 0.5)
        else:
            return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = value

    @property
    def fwhm(self):
        return self._fwhm

    @fwhm.setter
    def fwhm(self, value):
        self._fwhm = value

    @property
    def noise(self):
        return self._noise

    @noise.setter
    def noise(self, value):
        self._noise = value

    @property
    def background(self):
        return self._background

    @background.setter
    def background(self, value):
        self._background = value

    @property
    def remove_background(self):
        return self._remove_background

    @remove_background.setter
    def remove_background(self, value):
        self._remove_background = value

    ## Data generation ##

    def gen_data(self):
        spectre = self.pinem.calc_sq_modulus(omega=self.omg, g=self.g, offset=self.offset,
                                             fwhm=self.fwhm, rt=self.rt)
        # The spectra are already scaled to [0, self.amplitude] in the PINEM class
        # Then we add the background and the noise if required. The background is expected to be expressed in percentage of the amplitude.
        if not (self.noise):
            noiseless_spectre = spectre + self.amplitude * self.background
            return noiseless_spectre
        else:
            noisy_spectre = np.random.poisson(spectre + self.background * self.amplitude)
            return noisy_spectre

    def get_value(self, prop: str):
        if hasattr(self, prop):
            return getattr(self, prop)

    def set_value(self, prop: str, value: float):
        if hasattr(self, prop):
            setattr(self, prop, value)