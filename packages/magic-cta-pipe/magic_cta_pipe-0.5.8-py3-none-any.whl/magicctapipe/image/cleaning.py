"""
Module for cleaning utilities
"""
import copy
import itertools

import numpy as np
from scipy.sparse.csgraph import connected_components

__all__ = [
    "MAGICClean",
    "PixelTreatment",
    "get_num_islands_MAGIC",
]


class MAGICClean:
    """Implement the cleaning used by MAGIC.

    Parameters
    ----------
    camera : ctapipe.instrument.CameraGeometry
        Camera geometry.
    configuration : dict
        Dictionary for the configuration.
    """

    def __init__(self, camera, configuration):
        """Initiate cleaning class.

        Parameters
        ----------
        camera : ctapipe.instrument.CameraGeometry
            Camera geometry.
        configuration : dict
            Dictionary for the configuration.
        """
        self.configuration = configuration
        self.camera = camera

        if configuration["use_sum"]:
            self.NN2 = self.GetListOfNN(NN_size=2)
            self.NN3 = self.GetListOfNN(NN_size=3)
            self.NN4 = self.GetListOfNN(NN_size=4)

        # Set the XNN thresholds and windows if they have not already been defined.
        # The defaults are from the expert values values in the star_MX_OSA.rc file.

        if "SumThresh2NNPerPixel" in configuration:
            self.SumThresh2NNPerPixel = configuration["SumThresh2NNPerPixel"]
        else:
            self.SumThresh2NNPerPixel = 1.8

        if "SumThresh3NNPerPixel" in configuration:
            self.SumThresh3NNPerPixel = configuration["SumThresh3NNPerPixel"]
        else:
            self.SumThresh3NNPerPixel = 1.3

        if "SumThresh4NNPerPixel" in configuration:
            self.SumThresh4NNPerPixel = configuration["SumThresh4NNPerPixel"]
        else:
            self.SumThresh4NNPerPixel = 1.0

        # default WindowXNN values are converted from time slices to ns
        if "Window2NN" in configuration:
            self.Window2NN = configuration["Window2NN"]
        else:
            self.Window2NN = 0.82 / 1.639

        if "Window3NN" in configuration:
            self.Window3NN = configuration["Window3NN"]
        else:
            self.Window3NN = 1.15 / 1.639

        if "Window4NN" in configuration:
            self.Window4NN = configuration["Window4NN"]
        else:
            self.Window4NN = 1.80 / 1.639

        if "clipping" in configuration:
            self.clipping = configuration["clipping"]
        else:
            self.clipping = 750.0

        if "find_hotpixels" in configuration:
            self.find_hotpixels = configuration["find_hotpixels"]
        else:
            self.find_hotpixels = False

        if self.find_hotpixels:
            if "use_interpolation" in configuration:
                use_interpolation = configuration["use_interpolation"]
            else:
                use_interpolation = True

            if "use_process_pedestal_evt" in configuration:
                use_process_pedestal_evt = configuration["use_process_pedestal_evt"]
            else:
                use_process_pedestal_evt = True

            if "use_process_times" in configuration:
                use_process_times = configuration["use_process_times"]
            else:
                use_process_times = True

            if "minimum_number_of_neighbors" in configuration:
                minimum_number_of_neighbors = configuration[
                    "minimum_number_of_neighbors"
                ]
            else:
                minimum_number_of_neighbors = 3

            if "fast" in configuration:
                fast = configuration["fast"]
            else:
                fast = False

            treatment_config = dict(
                use_interpolation=use_interpolation,
                use_process_pedestal_evt=use_process_pedestal_evt,
                use_process_times=use_process_times,
                minimum_number_of_neighbors=minimum_number_of_neighbors,
                fast=fast,
            )

            self.pixel_treatment = PixelTreatment(self.camera, treatment_config)

    def GetListOfNN(self, NN_size=2, bad_pixels=None):
        """Get the list of next neighbor pixels.

        Parameters
        ----------
        NN_size : int, optional
            Order of next neighbors to find, by default 2.
        bad_pixels : np.ndarray, optional
            Array of bad pixels, by default None.

        Returns
        -------
        np.ndarray
            Array of neighbor pixels.
        """
        NN = []
        pixels = list(range(self.camera.n_pixels))

        if bad_pixels is not None:
            pixels = np.setdiff1d(pixels, bad_pixels)

        for pixel in pixels:
            neighbors = np.where(self.camera.neighbor_matrix[pixel])[0]

            if bad_pixels is not None:
                neighbors = np.setdiff1d(neighbors, bad_pixels)

            if len(neighbors) < NN_size:
                continue

            combos = list(itertools.combinations(neighbors, NN_size - 1))
            for combo in combos:
                arr = list(combo)
                arr.append(pixel)

                if NN_size == 2:
                    NN.append(sorted(arr))

                if NN_size == 3:
                    neigh0 = np.where(self.camera.neighbor_matrix[arr[0]])[0]
                    neigh1 = np.where(self.camera.neighbor_matrix[arr[1]])[0]

                    if bad_pixels is not None:
                        neigh0 = np.setdiff1d(neigh0, bad_pixels)
                        neigh1 = np.setdiff1d(neigh1, bad_pixels)

                    neigh_set = np.asarray(list(set(neigh0) & set(neigh1)))
                    if len(neigh_set) != 2:
                        continue
                    shared_pixel = neigh_set[neigh_set != pixel]
                    if shared_pixel in neighbors:
                        continue

                    NN.append(sorted(arr))

                if NN_size == 4:
                    neigh0 = np.where(self.camera.neighbor_matrix[arr[0]])[0]
                    neigh1 = np.where(self.camera.neighbor_matrix[arr[1]])[0]
                    neigh2 = np.where(self.camera.neighbor_matrix[arr[2]])[0]

                    if bad_pixels is not None:
                        neigh0 = np.setdiff1d(neigh0, bad_pixels)
                        neigh1 = np.setdiff1d(neigh1, bad_pixels)
                        neigh2 = np.setdiff1d(neigh2, bad_pixels)

                    if (
                        ((arr[0] in neigh1) or (arr[0] in neigh2))
                        and ((arr[1] in neigh0) or (arr[1] in neigh2))
                        and ((arr[2] in neigh0) or (arr[2] in neigh1))
                    ):
                        pass
                    else:
                        continue

                    NN.append(sorted(arr))

        return np.unique(NN, axis=0)

    def clean_image(self, event_image, event_pulse_time, unsuitable_mask=None):
        """Clean the input image.

        Parameters
        ----------
        event_image : np.ndarray
            Input array with event image (charge per each pixel).
        event_pulse_time : np.ndarray
            Input array with event times (time per each pixel).
        unsuitable_mask : np.ndarray, optional
            Array of unsuitable pixels, by default None.

        Returns
        -------
        clean_mask : np.ndarray
            Mask with pixels surviving the cleaning.
        self.event_image : np.ndarray
            Image (charges) with only surviving pixels.
        self.event_pulse_time : np.ndarray
            Image (times) with only surviving pixels.

        Raises
        ------
        ValueError
            Raised if no unsuitable mask is provided but `find_hotpixles` is True.
        """
        if unsuitable_mask is None and self.find_hotpixels:
            raise ValueError(
                "find_hotpixels set to %s but not unsuitable_mask provided."
                % self.find_hotpixels
            )

        if self.find_hotpixels:
            self.event_image = copy.copy(event_image)
            (
                self.event_image,
                self.event_pulse_time,
                self.unsuitable_mask,
                self.unmapped_mask,
            ) = self.pixel_treatment.treat(
                self.event_image, event_pulse_time, unsuitable_mask
            )
            self.event_image[self.unmapped_mask] = 0.0

        else:
            self.event_image = copy.copy(event_image)
            self.event_pulse_time = copy.copy(event_pulse_time)
            self.unmapped_mask = []
            self.unsuitable_mask = []

        # try:
        clean_mask = np.asarray([False] * self.camera.n_pixels)

        if self.configuration["use_sum"]:
            clean_mask = self.magic_clean_step1Sum()
        else:
            clean_mask = self.magic_clean_step1()

        self.mask_step1 = copy.copy(clean_mask)

        # # clean_mask = self.magic_clean_step2(clean_mask)
        clean_mask = self.magic_clean_step2b(clean_mask)

        self.mask_step2 = copy.copy(clean_mask)
        self.core_pix = np.sum(clean_mask)

        clean_mask = self.magic_clean_step3b(clean_mask)
        self.mask_step3 = copy.copy(clean_mask)

        self.used_pix = np.sum(clean_mask)

        # clipping
        self.event_image[np.where(self.event_image > self.clipping)] = self.clipping

        return clean_mask, self.event_image, self.event_pulse_time

    def group_calculation(self, mask, NN, clipNN, windowNN, thresholdNN):
        """Calculate pixel groups.

        Parameters
        ----------
        mask : np.ndarray
            Mask aray.
        NN : np.ndarray
            Neighbor pixels array.
        clipNN : float
            Charge clipping value.
        windowNN : float
            Time window cut.
        thresholdNN : float
            Group charge threshold.

        Returns
        -------
        np.ndarray
            Updated mask array.
        """
        meantime = 0.0
        totcharge = 0.0

        charge = copy.copy(self.event_image[NN])
        charge[charge > clipNN] = clipNN

        totcharge = np.sum(charge, axis=1)
        meantime = np.sum(charge * self.event_pulse_time[NN], axis=1) / totcharge

        meantime_proper = np.tile(meantime, (len(NN[0]), 1)).transpose()

        timeok = np.all(
            np.fabs(meantime_proper - self.event_pulse_time[NN]) < windowNN, axis=1
        )

        selection = (timeok) * (totcharge > thresholdNN)
        mask[NN[selection]] = True

        return mask, NN[selection]

    def magic_clean_step1Sum(self):
        """Perform the 1st step of the Sum cleaning.

        Returns
        -------
        np.ndarray
            Mask array with excluded pixels.
        """
        sumthresh2NN = (
            self.SumThresh2NNPerPixel * 2 * self.configuration["picture_thresh"]
        )
        sumthresh3NN = (
            self.SumThresh3NNPerPixel * 3 * self.configuration["picture_thresh"]
        )
        sumthresh4NN = (
            self.SumThresh4NNPerPixel * 4 * self.configuration["picture_thresh"]
        )

        clip2NN = 2.2 * sumthresh2NN / 2.0
        clip3NN = 1.05 * sumthresh3NN / 3.0
        clip4NN = 1.05 * sumthresh4NN / 4.0

        mask = np.asarray([False] * len(self.event_image))

        if self.find_hotpixels:
            bad_pixels = np.where(self.unmapped_mask)[0]

            NN2_mask = np.any(np.isin(self.NN2, bad_pixels), axis=1)
            NN2 = self.NN2[~NN2_mask]

            NN3_mask = np.any(np.isin(self.NN3, bad_pixels), axis=1)
            NN3 = self.NN3[~NN3_mask]

            NN4_mask = np.any(np.isin(self.NN4, bad_pixels), axis=1)
            NN4 = self.NN4[~NN4_mask]

            # NN2 = copy.copy(self.NN2)
            # NN3 = copy.copy(self.NN3)
            # NN4 = copy.copy(self.NN4)

        else:
            NN2 = copy.copy(self.NN2)
            NN3 = copy.copy(self.NN3)
            NN4 = copy.copy(self.NN4)

        mask, self.fuck2NN = self.group_calculation(
            mask, NN2, clip2NN, self.Window2NN, sumthresh2NN
        )
        mask, self.fuck3NN = self.group_calculation(
            mask, NN3, clip3NN, self.Window3NN, sumthresh3NN
        )
        mask, self.fuck4NN = self.group_calculation(
            mask, NN4, clip4NN, self.Window4NN, sumthresh4NN
        )

        # print("4NN",self.fuck4NN)

        return np.asarray(mask)

    def magic_clean_step1(self):
        """Perform the 1st step of the cleaning.

        Returns
        -------
        np.ndarray
            Mask array with excluded pixels.
        """
        mask = self.event_image <= self.configuration["picture_thresh"]
        return ~mask

    def magic_clean_step2(self, mask):
        """Perform the 2nd step of the cleaning.

        Parameters
        ----------
        mask : np.ndarray
            Input mask.

        Returns
        -------
        np.ndarray
            Mask array with excluded pixels.
        """
        if np.sum(mask) == 0:
            return mask

        else:
            n = 0
            size = 0

            if self.configuration["use_time"]:
                neighbors = copy.copy(self.camera.neighbor_matrix)
                neighbors[self.unmapped_mask][:, self.unmapped_mask] = False
                clean_neighbors = neighbors[mask][:, mask]

                num_islands, labels = connected_components(
                    clean_neighbors, directed=False
                )

                island_ids = np.zeros(self.camera.n_pixels)
                island_ids[mask] = labels + 1

                island_sizes = np.zeros(num_islands)
                for i in range(num_islands):
                    island_sizes[i] = self.event_image[mask][labels == i].sum()

                brightest_id = island_sizes.argmax() + 1

                nphot = self.event_image[island_ids == brightest_id]
                meantime = np.sum(
                    self.event_pulse_time[island_ids == brightest_id] * nphot * nphot
                ) / np.sum(nphot * nphot)

                for ipixel in range(self.camera.n_pixels):
                    if ipixel in self.unmapped_mask:
                        continue

                    if (
                        self.event_image[ipixel]
                        > 2 * self.configuration["picture_thresh"]
                    ):
                        if (
                            np.fabs(self.event_pulse_time[ipixel] - meantime)
                            > 2 * self.configuration["max_time_off"]
                        ):
                            mask[ipixel] = False

                    if (
                        self.event_image[ipixel]
                        < 2 * self.configuration["picture_thresh"]
                    ):
                        if (
                            np.fabs(self.event_pulse_time[ipixel] - meantime)
                            > self.configuration["max_time_off"]
                        ):
                            mask[ipixel] = False

            neighbors = copy.copy(self.camera.neighbor_matrix)

            for ipixel in range(self.camera.n_pixels):
                if ipixel in self.unmapped_mask:
                    continue

                hasNeighbor = False
                for neigh in np.where(neighbors[ipixel])[0]:
                    if neigh in np.where(mask)[0]:
                        hasNeighbor = True
                        break

                if hasNeighbor == False:
                    size += self.event_image[ipixel]
                    n += 1

            return mask

    def magic_clean_step2b(self, mask):
        """Perform the 2nd step of the cleaning (b version).

        Parameters
        ----------
        mask : np.ndarray
            Input mask.

        Returns
        -------
        np.ndarray
            Mask array with excluded pixels.
        """
        if np.sum(mask) == 0:
            return mask

        else:
            pixels_to_remove = []

            neighbors = copy.copy(self.camera.neighbor_matrix)
            neighbors[self.unmapped_mask] = False
            clean_neighbors = neighbors[mask][:, mask]

            num_islands, labels = connected_components(clean_neighbors, directed=False)

            island_ids = np.zeros(self.camera.n_pixels)
            island_ids[mask] = labels + 1

            # Finding the islands "sizes" (total charges)
            island_sizes = np.zeros(num_islands)
            for i in range(num_islands):
                island_sizes[i] = self.event_image[mask][labels == i].sum()

            # Disabling pixels for all islands save the brightest one
            brightest_id = island_sizes.argmax() + 1

            if self.configuration["use_time"]:
                brightest_pixel_times = self.event_pulse_time[
                    mask & (island_ids == brightest_id)
                ]
                brightest_pixel_charges = self.event_image[
                    mask & (island_ids == brightest_id)
                ]

                brightest_time = np.sum(
                    brightest_pixel_times * brightest_pixel_charges**2
                ) / np.sum(brightest_pixel_charges**2)

                time_diff = np.abs(self.event_pulse_time - brightest_time)

                mask[
                    (self.event_image > 2 * self.configuration["picture_thresh"])
                    & (time_diff > 2 * self.configuration["max_time_off"])
                ] = False
                mask[
                    (self.event_image < 2 * self.configuration["picture_thresh"])
                    & (time_diff > self.configuration["max_time_off"])
                ] = False

            for pix_id in np.where(mask)[0]:
                if len(set(np.where(neighbors[pix_id] & mask)[0])) == 0:
                    pixels_to_remove.append(pix_id)

            mask[pixels_to_remove] = False

        return mask

    def magic_clean_step3(self, mask):
        """Perform the 3rd step of the cleaning.

        Parameters
        ----------
        mask : np.ndarray
            Input mask.

        Returns
        -------
        np.ndarray
            Mask array with excluded pixels.
        """
        selection = []
        core_mask = mask.copy()

        pixels_with_picture_neighbors_matrix = copy.copy(self.camera.neighbor_matrix)

        for pixel in np.where(self.event_image)[0]:
            if pixel in np.where(core_mask)[0]:
                continue

            if self.event_image[pixel] <= self.configuration["boundary_thresh"]:
                continue

            hasNeighbor = False
            if self.configuration["use_time"]:
                neighbors = np.where(pixels_with_picture_neighbors_matrix[pixel])[0]

                for neighbor in neighbors:
                    if neighbor not in np.where(core_mask)[0]:
                        continue

                    time_diff = np.abs(
                        self.event_pulse_time[neighbor] - self.event_pulse_time[pixel]
                    )

                    if time_diff < self.configuration["max_time_diff"]:
                        hasNeighbor = True
                        break

                    # print(pixel, neighbor, time_diff, self.configuration['max_time_diff'], hasNeighbor)

                if not hasNeighbor:
                    continue

            if not pixels_with_picture_neighbors_matrix.dot(core_mask)[pixel]:
                continue

            selection.append(pixel)

        mask[selection] = True
        return mask

    def magic_clean_step3b(self, mask):
        """Perform the 3rd step of the cleaning (b version).

        Parameters
        ----------
        mask : np.ndarray
            Input mask.

        Returns
        -------
        np.ndarray
            Mask array with excluded pixels.
        """
        selection = []
        core_mask = mask.copy()
        boundary_mask = ~mask
        pixels_with_picture_neighbors_matrix = copy.copy(self.camera.neighbor_matrix)

        boundary_threshold_selection = (
            self.event_image > self.configuration["boundary_thresh"]
        )
        boundary_threshold_selection = boundary_threshold_selection * boundary_mask

        pixels = np.where(boundary_threshold_selection)[0]

        if self.configuration["use_time"]:
            boundary_pixels = copy.copy(pixels)
            neighbors = pixels_with_picture_neighbors_matrix[boundary_pixels]
            neighbors[:, ~core_mask] = False

            time_broadcast = np.tile(self.event_pulse_time, (len(self.event_image), 1))
            boundary_times = np.transpose(time_broadcast)[boundary_pixels]
            neighbor_times = time_broadcast[boundary_pixels]

            time_diff = np.abs(neighbor_times - boundary_times)
            time_selection = time_diff < self.configuration["max_time_diff"]

            hasNeighbor = np.minimum(
                np.sum(time_selection * neighbors, axis=1), 1
            ).astype(bool)
            pixels = boundary_pixels[hasNeighbor]

        selection = pixels[pixels_with_picture_neighbors_matrix.dot(core_mask)[pixels]]
        mask[selection] = True
        return mask

    def single_island(self, neighbors, mask):
        """Find single islands in the image.

        Parameters
        ----------
        neighbors : np.ndarray
            Array with neighbor pixels.
        mask : np.ndarray
            Input mask array.

        Returns
        -------
        np.ndarray
            Mask of pixels with single islands.
        """
        pixels_to_remove = []
        for pix_id in np.where(mask)[0]:
            if len(set(np.where(neighbors[pix_id] & mask)[0])) == 0:
                pixels_to_remove.append(pix_id)
        mask[pixels_to_remove] = False
        return mask


class PixelTreatment:
    """Interpolation for unsuitable pixels.

    Parameters
    ----------
    camera : ctapipe.instrument.CameraGeometry
        Camera geometry.
    configuration : dict
        Dictionary for the configuration.
    """

    def __init__(self, camera, configuration):
        """_summary_

        Parameters
        ----------
        camera : ctapipe.instrument.CameraGeometry
            Camera geometry.
        configuration : dict
            Dictionary for the configuration.
        """
        self.configuration = configuration
        self.camera = camera

        if "use_interpolation" in configuration:
            self.use_interpolation = configuration["use_interpolation"]
        else:
            self.use_interpolation = True

        if "use_process_pedestal_evt" in configuration:
            self.use_process_pedestal_evt = configuration["use_process_pedestal_evt"]
        else:
            self.use_process_pedestal_evt = True

        if "use_process_times" in configuration:
            self.use_process_times = configuration["use_process_times"]
        else:
            self.use_process_times = True

        if "minimum_number_of_neighbors" in configuration:
            self.minimum_number_of_neighbors = configuration[
                "minimum_number_of_neighbors"
            ]
        else:
            self.minimum_number_of_neighbors = 3

        if "fast" in configuration:
            self.fast = configuration["fast"]
        else:
            self.fast = False

        self.neighbors_array = self.camera.neighbor_matrix
        self.npix = self.camera.n_pixels

    def treat(self, event_image, event_pulse_time, unsuitable_mask):
        """Interpolate unsuitable pixels (charge and time).

        Parameters
        ----------
        event_image : np.ndarray
            Event image (charge).
        event_pulse_time : np.ndarray
            Event image (time).
        unsuitable_mask : np.ndarray
            Mask array with unsuitable pixels.

        Returns
        -------
        tuple
            Tuple with interpolated values for pixels' charge and time.
        """
        self.event_image = event_image
        self.event_pulse_time = event_pulse_time
        self.unsuitable_mask = unsuitable_mask
        self.unmapped_mask = []

        self.unsuitable_neighbors = self.neighbors_array[self.unsuitable_mask]
        self.unsuitable_pixels = np.where(self.unsuitable_mask)[0]

        if self.use_interpolation:
            self.interpolate_signals()
            if self.use_process_pedestal_evt:
                self.interpolate_pedestals()
            if self.use_process_times:
                self.interpolate_times_slow()

        return (
            self.event_image,
            self.event_pulse_time,
            self.unsuitable_mask,
            self.unmapped_mask,
        )

    def interpolate_signals(self):
        """Interpolate charge values."""
        neighbors_unsuitable = copy.copy(self.unsuitable_neighbors)
        neighbors_unsuitable[:, self.unsuitable_mask] = False

        number_of_neighbors = np.sum(neighbors_unsuitable, axis=1)
        number_of_neighbors_selection = (
            number_of_neighbors > self.minimum_number_of_neighbors - 1
        )

        unsuitable_mask = np.asarray([False] * self.npix)
        unsuitable_mask[self.unsuitable_pixels[number_of_neighbors_selection]] = True

        unmapped_mask = np.asarray([False] * self.npix)
        unmapped_mask[self.unsuitable_pixels[~number_of_neighbors_selection]] = True

        image_broadcast = np.repeat(
            self.event_image[np.newaxis, ...], neighbors_unsuitable.shape[0], axis=0
        )
        image_broadcast[~neighbors_unsuitable] = np.nan

        self.event_image[self.unsuitable_mask] = np.nanmean(image_broadcast, axis=1)

        self.unmapped_mask = copy.copy(unmapped_mask)

        self.unsuitable_mask_new = unsuitable_mask
        self.unsuitable_pixels_new = np.where(self.unsuitable_mask_new)[0]

    def find_two_closest_times(self, times_arr):
        """Find two closest times to the one of the current pixel.

        Parameters
        ----------
        times_arr : np.ndarray
            Time array.

        Returns
        -------
        tuple
            Two closest times.
        """
        n0 = len(times_arr)
        minval = 1e10
        p0 = -1
        p1 = -1

        for j in range(n0):
            for k in range(j):
                diff = np.fabs(times_arr[j] - times_arr[k])

                if diff >= minval and diff < 250:
                    continue

                p0 = j
                p1 = k
                minval = diff

        return p0, p1

    def interpolate_times_slow(self):
        """Interpolate times (slow version)."""
        pixel_and_times = zip(
            self.unsuitable_pixels_new, self.event_pulse_time[self.unsuitable_mask_new]
        )
        for ipixel, event_time in pixel_and_times:
            times = self.event_pulse_time[
                np.logical_and(self.neighbors_array[ipixel][:], ~self.unsuitable_mask)
            ]
            p0, p1 = self.find_two_closest_times(times)

            if p0 >= 0 and p1 >= 0 and np.fabs(times[p0] - times[p1]) < 250:
                self.event_pulse_time[ipixel] = (times[p0] + times[p1]) / 2.0

    def interpolate_times_fast(self):
        """Interpolate times (fast version)."""
        neighbors_unsuitable = self.neighbors_array[self.unsuitable_mask_new]
        neighbors_unsuitable[:, self.unsuitable_mask] = False

        times_broadcast = np.repeat(
            self.event_pulse_time[np.newaxis, ...],
            neighbors_unsuitable.shape[0],
            axis=0,
        )
        times_broadcast[~neighbors_unsuitable] = np.nan

        times_broadcast.sort(axis=1)
        idx = np.nanargmin(np.fabs(np.diff(times_broadcast, axis=1)), axis=1)

        for ix, ipixel in enumerate(self.unsuitable_pixels_new):
            time1 = times_broadcast[ix][idx[ix]]
            time2 = times_broadcast[ix][idx[ix] + 1]
            self.event_pulse_time[ipixel] = (time1 + time2) / 2.0

    def interpolate_pedestals(self):
        """Interpolate pedestals (not implemented)."""
        pass


def get_num_islands_MAGIC(camera, clean_mask):
    """Evaluate the number of islands as in MARS.

    Parameters
    ----------
    camera : ctapipe.instrument.camera.geometry.CameraGeometry
        Camera geometry.
    clean_mask : numpy.ndarray
        Clean mask.

    Returns
    -------
    int
        Number of islands in the image.
    """
    # Identifying connected islands
    neighbors = camera.neighbor_matrix_sparse
    clean_neighbors = neighbors[clean_mask][:, clean_mask]
    num_islands, labels = connected_components(clean_neighbors, directed=False)
    return num_islands
