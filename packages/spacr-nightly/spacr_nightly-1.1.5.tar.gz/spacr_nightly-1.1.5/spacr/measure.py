import os, cv2, time, sqlite3, traceback, shutil
import numpy as np
import pandas as pd
from collections import defaultdict
from scipy.stats import pearsonr, skew, kurtosis, mode
import multiprocessing as mp
from scipy.ndimage import distance_transform_edt, generate_binary_structure, binary_dilation, gaussian_filter, center_of_mass
from skimage.measure import regionprops, regionprops_table, shannon_entropy
from skimage.exposure import rescale_intensity
from skimage.segmentation import find_boundaries
from skimage.feature import graycomatrix, graycoprops
from mahotas.features import zernike_moments
from skimage import morphology, measure, filters
from skimage.util import img_as_bool
import matplotlib.pyplot as plt
from math import ceil, sqrt

def get_components(cell_mask, nucleus_mask, pathogen_mask):
    """
    Get the components (nucleus and pathogens) for each cell in the given masks.

    Args:
        cell_mask (ndarray): Binary mask of cell labels.
        nucleus_mask (ndarray): Binary mask of nucleus labels.
        pathogen_mask (ndarray): Binary mask of pathogen labels.

    Returns:
        tuple: A tuple containing two dataframes - nucleus_df and pathogen_df.
            nucleus_df (DataFrame): Dataframe with columns 'cell_id' and 'nucleus',
                representing the mapping of each cell to its nucleus.
            pathogen_df (DataFrame): Dataframe with columns 'cell_id' and 'pathogen',
                representing the mapping of each cell to its pathogens.
    """
    # Create mappings from each cell to its nucleus, pathogens, and cytoplasms
    cell_to_nucleus = defaultdict(list)
    cell_to_pathogen = defaultdict(list)
    # Get unique cell labels
    cell_labels = np.unique(cell_mask)
    # Iterate over each cell label
    for cell_id in cell_labels:
        if cell_id == 0:
            continue
        # Find corresponding component labels
        nucleus_ids = np.unique(nucleus_mask[cell_mask == cell_id])
        pathogen_ids = np.unique(pathogen_mask[cell_mask == cell_id])
        # Update dictionaries, ignoring 0 (background) labels
        cell_to_nucleus[cell_id] = nucleus_ids[nucleus_ids != 0].tolist()
        cell_to_pathogen[cell_id] = pathogen_ids[pathogen_ids != 0].tolist()
    # Convert dictionaries to dataframes
    nucleus_df = pd.DataFrame(list(cell_to_nucleus.items()), columns=['cell_id', 'nucleus'])
    pathogen_df = pd.DataFrame(list(cell_to_pathogen.items()), columns=['cell_id', 'pathogen'])
    # Explode lists
    nucleus_df = nucleus_df.explode('nucleus')
    pathogen_df = pathogen_df.explode('pathogen')
    return nucleus_df, pathogen_df

def _calculate_zernike(mask, df, degree=8):
    """
    Calculate Zernike moments for each region in the given mask image.

    Args:
        mask (ndarray): Binary mask image.
        df (DataFrame): Input DataFrame.
        degree (int, optional): Degree of Zernike moments. Defaults to 8.

    Returns:
        DataFrame: Updated DataFrame with Zernike features appended, if any regions are found in the mask.
                   Otherwise, returns the original DataFrame.
    Raises:
        ValueError: If the lengths of Zernike moments are not consistent.

    """
    zernike_features = []
    for region in regionprops(mask):
        zernike_moment = zernike_moments(region.image, degree)
        zernike_features.append(zernike_moment.tolist())

    if zernike_features:
        feature_length = len(zernike_features[0])
        for feature in zernike_features:
            if len(feature) != feature_length:
                raise ValueError("All Zernike moments must be of the same length")

        zernike_df = pd.DataFrame(zernike_features, columns=[f'zernike_{i}' for i in range(feature_length)])
        return pd.concat([df.reset_index(drop=True), zernike_df], axis=1)
    else:
        return df

def _analyze_cytoskeleton(array, mask, channel):
    """
    Analyzes and extracts skeleton properties from labeled objects in a masked image based on microtubule staining intensities.

    Parameters:
    image : numpy array
        Intensity image where the microtubules are stained.
    mask : numpy array
        Mask where objects are labeled for analysis. Each label corresponds to a unique object.

    Returns:
    DataFrame
        A pandas DataFrame containing the measured properties of each object's skeleton.
    """

    image = array[:, :, channel]

    properties_list = []

    # Process each object in the mask based on its label
    for label in np.unique(mask):
        if label == 0:
            continue  # Skip background

        # Isolate the object using the label
        object_region = mask == label
        region_intensity = np.where(object_region, image, 0)  # Use np.where for more efficient masking

        # Ensure there are non-zero values to process
        if np.any(region_intensity):
            # Calculate adaptive offset based on intensity percentiles within the object
            valid_pixels = region_intensity[region_intensity > 0]
            if len(valid_pixels) > 1:  # Ensure there are enough pixels to compute percentiles
                offset = np.percentile(valid_pixels, 90) - np.percentile(valid_pixels, 50)
                block_size = 35  # Adjust this based on your object sizes and detail needs
                local_thresh = filters.threshold_local(region_intensity, block_size=block_size, offset=offset)
                cytoskeleton = region_intensity > local_thresh

                # Skeletonize the thresholded cytoskeleton
                skeleton = morphology.skeletonize(img_as_bool(cytoskeleton))

                # Measure properties of the skeleton
                skeleton_props = measure.regionprops(measure.label(skeleton), intensity_image=image)
                skeleton_length = sum(prop.area for prop in skeleton_props)  # Sum of lengths of all skeleton segments
                branch_data = morphology.skeleton_branch_analysis(skeleton)

                # Store properties
                properties = {
                    "object_label": label,
                    "skeleton_length": skeleton_length,
                    "skeleton_branch_points": len(branch_data['branch_points'])
                }
                properties_list.append(properties)
            else:
                # Handle cases with insufficient pixels
                properties_list.append({
                    "object_label": label,
                    "skeleton_length": 0,
                    "skeleton_branch_points": 0
                })

    return pd.DataFrame(properties_list)

#@log_function_call
def _morphological_measurements(cell_mask, nucleus_mask, pathogen_mask, cytoplasm_mask, settings, zernike=True, degree=8):
    """
    Calculate morphological measurements for cells, nucleus, pathogens, and cytoplasms based on the given masks.

    Args:
        cell_mask (ndarray): Binary mask of cell labels.
        nucleus_mask (ndarray): Binary mask of nucleus labels.
        pathogen_mask (ndarray): Binary mask of pathogen labels.
        cytoplasm_mask (ndarray): Binary mask of cytoplasm labels.
        settings (dict): Dictionary containing settings for the measurements.
        zernike (bool, optional): Flag indicating whether to calculate Zernike moments. Defaults to True.
        degree (int, optional): Degree of Zernike moments. Defaults to 8.

    Returns:
        tuple: A tuple containing four dataframes - cell_df, nucleus_df, pathogen_df, and cytoplasm_df.
            cell_df (DataFrame): Dataframe with morphological measurements for cells.
            nucleus_df (DataFrame): Dataframe with morphological measurements for nucleus.
            pathogen_df (DataFrame): Dataframe with morphological measurements for pathogens.
            cytoplasm_df (DataFrame): Dataframe with morphological measurements for cytoplasms.
    """
    morphological_props = ['label', 'area', 'area_filled', 'area_bbox', 'convex_area', 'major_axis_length', 'minor_axis_length', 
                           'eccentricity', 'solidity', 'extent', 'perimeter', 'euler_number', 'equivalent_diameter_area', 'feret_diameter_max']
    
    prop_ls = []
    ls = []
    
    # Create mappings from each cell to its nucleus, pathogens, and cytoplasms
    if settings['cell_mask_dim'] is not None:
        cell_to_nucleus, cell_to_pathogen = get_components(cell_mask, nucleus_mask, pathogen_mask)
        cell_props = pd.DataFrame(regionprops_table(cell_mask, properties=morphological_props))
        cell_props = _calculate_zernike(cell_mask, cell_props, degree=degree)
        prop_ls = prop_ls + [cell_props]
        ls = ls + ['cell']
    else:
        prop_ls = prop_ls + [pd.DataFrame()]
        ls = ls + ['cell']

    if settings['nucleus_mask_dim'] is not None:
        nucleus_props = pd.DataFrame(regionprops_table(nucleus_mask, properties=morphological_props))
        nucleus_props = _calculate_zernike(nucleus_mask, nucleus_props, degree=degree)
        if settings['cell_mask_dim'] is not None:
            nucleus_props = pd.merge(nucleus_props, cell_to_nucleus, left_on='label', right_on='nucleus', how='left')
        prop_ls = prop_ls + [nucleus_props]
        ls = ls + ['nucleus']
    else:
        prop_ls = prop_ls + [pd.DataFrame()]
        ls = ls + ['nucleus']
    
    if settings['pathogen_mask_dim'] is not None:
        pathogen_props = pd.DataFrame(regionprops_table(pathogen_mask, properties=morphological_props))
        pathogen_props = _calculate_zernike(pathogen_mask, pathogen_props, degree=degree)
        if settings['cell_mask_dim'] is not None:
            pathogen_props = pd.merge(pathogen_props, cell_to_pathogen, left_on='label', right_on='pathogen', how='left')
        prop_ls = prop_ls + [pathogen_props]
        ls = ls + ['pathogen']
    else:
        prop_ls = prop_ls + [pd.DataFrame()]
        ls = ls + ['pathogen']

    if settings['cytoplasm']:
        cytoplasm_props = pd.DataFrame(regionprops_table(cytoplasm_mask, properties=morphological_props))
        prop_ls = prop_ls + [cytoplasm_props]
        ls = ls + ['cytoplasm']
    else:
        prop_ls = prop_ls + [pd.DataFrame()]
        ls = ls + ['cytoplasm']

    df_ls = []
    for i,df in enumerate(prop_ls):
        df.columns = [f'{ls[i]}_{col}' for col in df.columns]
        df = df.rename(columns={col: 'label' for col in df.columns if 'label' in col})
        df_ls.append(df)
 
    return df_ls[0], df_ls[1], df_ls[2], df_ls[3]
    
def _create_dataframe(radial_distributions, object_type):
        """
        Create a pandas DataFrame from the given radial distributions.

        Parameters:
        - radial_distributions (dict): A dictionary containing the radial distributions.
        - object_type (str): The type of object.

        Returns:
        - df (pandas.DataFrame): The created DataFrame.
        """
        df = pd.DataFrame()
        for key, value in radial_distributions.items():
            cell_label, object_label, channel_index = key
            for i in range(len(value)):
                col_name = f'{object_type}_rad_dist_channel_{channel_index}_bin_{i}'
                df.loc[object_label, col_name] = value[i]
            df.loc[object_label, 'cell_id'] = cell_label
        # Reset the index and rename the column that was previously the index
        df = df.reset_index().rename(columns={'index': 'label'})
        return df

def _extended_regionprops_table(labels, image, intensity_props):
    """
    Calculate extended region properties table, adding a suite of advanced quantitative features.
    """
    
    def _gini(array):
        # Compute Gini coefficient (nan safe)
        array = np.abs(array[~np.isnan(array)])
        n = array.size
        if n == 0:
            return np.nan
        array = np.sort(array)
        index = np.arange(1, n + 1)
        return (np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)) if np.sum(array) else np.nan
    
    props = regionprops_table(labels, image, properties=intensity_props)
    df = pd.DataFrame(props)

    regions = regionprops(labels, intensity_image=image)
    integrated_intensity = []
    std_intensity = []
    median_intensity = []
    skew_intensity = []
    kurtosis_intensity = []
    mode_intensity = []
    range_intensity = []
    iqr_intensity = []
    cv_intensity = []
    gini_intensity = []
    frac_high90 = []
    frac_low10 = []
    entropy_intensity = []

    for region in regions:
        intens = region.intensity_image[region.image]
        intens = intens[~np.isnan(intens)]
        if intens.size == 0:
            integrated_intensity.append(np.nan)
            std_intensity.append(np.nan)
            median_intensity.append(np.nan)
            skew_intensity.append(np.nan)
            kurtosis_intensity.append(np.nan)
            mode_intensity.append(np.nan)
            range_intensity.append(np.nan)
            iqr_intensity.append(np.nan)
            cv_intensity.append(np.nan)
            gini_intensity.append(np.nan)
            frac_high90.append(np.nan)
            frac_low10.append(np.nan)
            entropy_intensity.append(np.nan)
        else:
            integrated_intensity.append(np.sum(intens))
            std_intensity.append(np.std(intens))
            median_intensity.append(np.median(intens))
            skew_intensity.append(skew(intens) if intens.size > 2 else np.nan)
            kurtosis_intensity.append(kurtosis(intens) if intens.size > 3 else np.nan)
            # Mode (use first mode value if multimodal)
            try:
                mode_val = mode(intens, nan_policy='omit').mode
                mode_intensity.append(mode_val[0] if len(mode_val) > 0 else np.nan)
            except Exception:
                mode_intensity.append(np.nan)
            range_intensity.append(np.ptp(intens))
            iqr_intensity.append(np.percentile(intens, 75) - np.percentile(intens, 25))
            cv_intensity.append(np.std(intens) / np.mean(intens) if np.mean(intens) != 0 else np.nan)
            gini_intensity.append(_gini(intens))
            frac_high90.append(np.mean(intens > np.percentile(intens, 90)))
            frac_low10.append(np.mean(intens < np.percentile(intens, 10)))
            entropy_intensity.append(shannon_entropy(intens) if intens.size > 1 else 0.0)

    df['integrated_intensity'] = integrated_intensity
    df['std_intensity'] = std_intensity
    df['median_intensity'] = median_intensity
    df['skew_intensity'] = skew_intensity
    df['kurtosis_intensity'] = kurtosis_intensity
    df['mode_intensity'] = mode_intensity
    df['range_intensity'] = range_intensity
    df['iqr_intensity'] = iqr_intensity
    df['cv_intensity'] = cv_intensity
    df['gini_intensity'] = gini_intensity
    df['frac_high90'] = frac_high90
    df['frac_low10'] = frac_low10
    df['entropy_intensity'] = entropy_intensity

    percentiles = [5, 10, 25, 75, 85, 95]
    for p in percentiles:
        df[f'percentile_{p}'] = [
            np.percentile(region.intensity_image[region.image], p)
            for region in regions
        ]
    return df

def _calculate_homogeneity(label, channel, distances=[2,4,8,16,32,64]):
        """
        Calculate the homogeneity values for each region in the label mask.

        Parameters:
        - label (ndarray): The label mask containing the regions.
        - channel (ndarray): The image channel corresponding to the label mask.
        - distances (list): The distances to calculate the homogeneity for.

        Returns:
        - homogeneity_df (DataFrame): A DataFrame containing the homogeneity values for each region and distance.
        """
        homogeneity_values = []
        # Iterate through the regions in label_mask
        for region in regionprops(label):
            region_image = (region.image * channel[region.slice]).astype(int)
            homogeneity_per_distance = []
            for d in distances:
                rescaled_image = rescale_intensity(region_image, out_range=(0, 255)).astype('uint8')
                glcm = graycomatrix(rescaled_image, [d], [0], symmetric=True, normed=True)
                homogeneity_per_distance.append(graycoprops(glcm, 'homogeneity')[0, 0])
            homogeneity_values.append(homogeneity_per_distance)
        columns = [f'homogeneity_distance_{d}' for d in distances]
        homogeneity_df = pd.DataFrame(homogeneity_values, columns=columns)

        return homogeneity_df

def _periphery_intensity(label_mask, image):
    """
    Calculate intensity statistics for the periphery regions in the label mask.

    Args:
        label_mask (ndarray): Binary mask indicating the regions of interest.
        image (ndarray): Input image.

    Returns:
        list: List of tuples containing periphery intensity statistics for each region.
              Each tuple contains the region label and the following statistics:
              - Mean intensity
              - 5th percentile intensity
              - 10th percentile intensity
              - 25th percentile intensity
              - 50th percentile intensity (median)
              - 75th percentile intensity
              - 85th percentile intensity
              - 95th percentile intensity
    """
    periphery_intensity_stats = []
    boundary = find_boundaries(label_mask)
    for region in np.unique(label_mask)[1:]:  # skip the background label
        region_boundary = boundary & (label_mask == region)
        intensities = image[region_boundary]
        if intensities.size == 0:
            periphery_intensity_stats.append((region, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan))
        else:
            periphery_intensity_stats.append((region, np.mean(intensities), np.percentile(intensities,5), np.percentile(intensities,10),
                                              np.percentile(intensities,25), np.percentile(intensities,50),
                                              np.percentile(intensities,75), np.percentile(intensities,85), 
                                              np.percentile(intensities,95)))
    return periphery_intensity_stats

def _outside_intensity(label_mask, image, distance=5):
    """
    Calculate the statistics of intensities outside each labeled region in the image.

    Args:
        label_mask (ndarray): Binary mask indicating the labeled regions.
        image (ndarray): Input image.
        distance (int): Distance for dilation operation (default: 5).

    Returns:
        list: List of tuples containing the statistics for each labeled region.
              Each tuple contains the region label and the following statistics:
              - Mean intensity
              - 5th percentile intensity
              - 10th percentile intensity
              - 25th percentile intensity
              - 50th percentile intensity (median)
              - 75th percentile intensity
              - 85th percentile intensity
              - 95th percentile intensity
    """
    outside_intensity_stats = []
    for region in np.unique(label_mask)[1:]:  # skip the background label
        region_mask = label_mask == region
        dilated_mask = binary_dilation(region_mask, iterations=distance)
        outside_mask = dilated_mask & ~region_mask
        intensities = image[outside_mask]
        if intensities.size == 0:
            outside_intensity_stats.append((region, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan))
        else:
            outside_intensity_stats.append((region, np.mean(intensities), np.percentile(intensities,5), np.percentile(intensities,10),
                                              np.percentile(intensities,25), np.percentile(intensities,50),
                                              np.percentile(intensities,75), np.percentile(intensities,85), 
                                              np.percentile(intensities,95)))
    return outside_intensity_stats

def _calculate_radial_distribution(cell_mask, object_mask, channel_arrays, num_bins=6):
    """
    Calculate the radial distribution of average intensities for each object in each cell.

    Args:
        cell_mask (numpy.ndarray): The mask representing the cells.
        object_mask (numpy.ndarray): The mask representing the objects.
        channel_arrays (numpy.ndarray): The array of channel images.
        num_bins (int, optional): The number of bins for the radial distribution. Defaults to 6.

    Returns:
        dict: A dictionary containing the radial distributions of average intensities for each object in each cell.
            The keys are tuples of (cell_label, object_label, channel_index), and the values are numpy arrays
            representing the radial distributions.

    """
    def _calculate_average_intensity(distance_map, single_channel_image, num_bins):
        """
        Calculate the average intensity of a single-channel image based on the distance map.

        Args:
            distance_map (numpy.ndarray): The distance map.
            single_channel_image (numpy.ndarray): The single-channel image.
            num_bins (int): The number of bins for the radial distribution.

        Returns:
            numpy.ndarray: The radial distribution of average intensities.

        """
        radial_distribution = np.zeros(num_bins)
        for i in range(num_bins):
            min_distance = i * (distance_map.max() / num_bins)
            max_distance = (i + 1) * (distance_map.max() / num_bins)
            bin_mask = (distance_map >= min_distance) & (distance_map < max_distance)
            radial_distribution[i] = single_channel_image[bin_mask].mean()
        return radial_distribution


    object_radial_distributions = {}

    # get unique cell labels
    cell_labels = np.unique(cell_mask)
    cell_labels = cell_labels[cell_labels != 0]

    for cell_label in cell_labels:
        cell_region = cell_mask == cell_label

        object_labels = np.unique(object_mask[cell_region])
        object_labels = object_labels[object_labels != 0]

        for object_label in object_labels:
            objecyt_region = object_mask == object_label
            object_boundary = find_boundaries(objecyt_region, mode='outer')
            distance_map = distance_transform_edt(~object_boundary) * cell_region
            for channel_index in range(channel_arrays.shape[2]):
                radial_distribution = _calculate_average_intensity(distance_map, channel_arrays[:, :, channel_index], num_bins)
                object_radial_distributions[(cell_label, object_label, channel_index)] = radial_distribution

    return object_radial_distributions

def _calculate_correlation_object_level(channel_image1, channel_image2, mask, settings):
        """
        Calculate correlation at the object level between two channel images based on a mask.

        Args:
            channel_image1 (numpy.ndarray): The first channel image.
            channel_image2 (numpy.ndarray): The second channel image.
            mask (numpy.ndarray): The mask indicating the objects.
            settings (dict): Additional settings for correlation calculation.

        Returns:
            pandas.DataFrame: A DataFrame containing the correlation data at the object level.
        """
        thresholds = settings['manders_thresholds']

        corr_data = {}
        for i in np.unique(mask)[1:]:
            object_mask = (mask == i)
            object_channel_image1 = channel_image1[object_mask]
            object_channel_image2 = channel_image2[object_mask]
            total_intensity1 = np.sum(object_channel_image1)
            total_intensity2 = np.sum(object_channel_image2)

            if len(object_channel_image1) < 2 or len(object_channel_image2) < 2:
                pearson_corr = np.nan
            else:
                pearson_corr, _ = pearsonr(object_channel_image1, object_channel_image2)

            corr_data[i] = {f'label_correlation': i,
                            f'Pearson_correlation': pearson_corr}

            for thresh in thresholds:
                chan1_thresh = np.percentile(object_channel_image1, thresh)
                chan2_thresh = np.percentile(object_channel_image2, thresh)

                # boolean mask where both signals are present
                overlap_mask = (object_channel_image1 > chan1_thresh) & (object_channel_image2 > chan2_thresh)
                M1 = np.sum(object_channel_image1[overlap_mask]) / total_intensity1 if total_intensity1 > 0 else 0
                M2 = np.sum(object_channel_image2[overlap_mask]) / total_intensity2 if total_intensity2 > 0 else 0

                corr_data[i].update({f'M1_correlation_{thresh}': M1,
                                     f'M2_correlation_{thresh}': M2})

        return pd.DataFrame(corr_data.values())

def _estimate_blur(image):
    """
    Estimates the blur of an image by computing the variance of its Laplacian.

    Parameters:
    image (numpy.ndarray): The input image.

    Returns:
    float: The variance of the Laplacian of the image.
    """
    # Check if the image is not already in a floating-point format
    if image.dtype != np.float32 and image.dtype != np.float64:
        # Convert the image to float64 for processing
        image_float = image.astype(np.float64)
    else:
        # If it's already a floating-point image, use it as is
        image_float = image
    # Compute the Laplacian of the image
    lap = cv2.Laplacian(image_float, cv2.CV_64F)
    # Compute and return the variance of the Laplacian
    return lap.var()

def _measure_intensity_distance(cell_mask, nucleus_mask, pathogen_mask, channel_arrays, settings):
    """
    Compute Gaussian-smoothed intensity-weighted centroid distances for each cell object.
    """

    sigma = settings.get('distance_gaussian_sigma', 1.0)
    cell_labels = np.unique(cell_mask)
    cell_labels = cell_labels[cell_labels > 0]

    dfs = []
    nucleus_dt = distance_transform_edt(nucleus_mask == 0)
    pathogen_dt = distance_transform_edt(pathogen_mask == 0)

    for ch in range(channel_arrays.shape[-1]):
        channel_img = channel_arrays[:, :, ch]
        blurred_img = gaussian_filter(channel_img, sigma=sigma)

        data = []
        for label in cell_labels:
            cell_coords = np.argwhere(cell_mask == label)
            if cell_coords.size == 0:
                data.append([label, np.nan, np.nan])
                continue

            minr, minc = np.min(cell_coords, axis=0)
            maxr, maxc = np.max(cell_coords, axis=0) + 1

            cell_submask = (cell_mask[minr:maxr, minc:maxc] == label)
            blurred_subimg = blurred_img[minr:maxr, minc:maxc]

            if np.sum(cell_submask) == 0:
                data.append([label, np.nan, np.nan])
                continue

            masked_intensity = blurred_subimg * cell_submask
            com_local = center_of_mass(masked_intensity)
            if np.isnan(com_local[0]):
                data.append([label, np.nan, np.nan])
                continue

            com_global = (com_local[0] + minr, com_local[1] + minc)
            com_global_int = tuple(np.round(com_global).astype(int))

            x, y = com_global_int
            if not (0 <= x < cell_mask.shape[0] and 0 <= y < cell_mask.shape[1]):
                data.append([label, np.nan, np.nan])
                continue

            nucleus_dist = nucleus_dt[x, y]
            pathogen_dist = pathogen_dt[x, y]

            data.append([label, nucleus_dist, pathogen_dist])

        df = pd.DataFrame(data, columns=['label',
                                         f'cell_channel_{ch}_distance_to_nucleus',
                                         f'cell_channel_{ch}_distance_to_pathogen'])
        dfs.append(df)

    # Merge all channel dataframes on label
    merged_df = dfs[0]
    for df in dfs[1:]:
        merged_df = merged_df.merge(df, on='label', how='outer')

    return merged_df


#@log_function_call
def _intensity_measurements(cell_mask, nucleus_mask, pathogen_mask, cytoplasm_mask, channel_arrays, settings, sizes=[3, 6, 12, 24], periphery=True, outside=True):
    
    """
    Calculate various intensity measurements for different regions in the image.

    Args:
        cell_mask (ndarray): Binary mask indicating the cell regions.
        nucleus_mask (ndarray): Binary mask indicating the nucleus regions.
        pathogen_mask (ndarray): Binary mask indicating the pathogen regions.
        cytoplasm_mask (ndarray): Binary mask indicating the cytoplasm regions.
        channel_arrays (ndarray): Array of channel images.
        settings (dict): Additional settings for the intensity measurements.
        sizes (list, optional): List of sizes for the measurements. Defaults to [3, 6, 12, 24].
        periphery (bool, optional): Flag indicating whether to calculate periphery intensity measurements. Defaults to True.
        outside (bool, optional): Flag indicating whether to calculate outside intensity measurements. Defaults to True.

    Returns:
        dict: A dictionary containing the calculated intensity measurements.

    """
    radial_dist = settings['radial_dist']
    calculate_correlation = settings['calculate_correlation']
    homogeneity = settings['homogeneity']
    distances = settings['homogeneity_distances']
    
    intensity_props = ["label", "centroid_weighted", "centroid_weighted_local", "max_intensity", "mean_intensity", "min_intensity"]
    col_lables = ['region_label', 'mean', '5_percentile', '10_percentile', '25_percentile', '50_percentile', '75_percentile', '85_percentile', '95_percentile']
    cell_dfs, nucleus_dfs, pathogen_dfs, cytoplasm_dfs = [], [], [], []
    ls = ['cell','nucleus','pathogen','cytoplasm']
    labels = [cell_mask, nucleus_mask, pathogen_mask, cytoplasm_mask]
    dfs = [cell_dfs, nucleus_dfs, pathogen_dfs, cytoplasm_dfs]
    
    for i in range(0,channel_arrays.shape[-1]):
        channel = channel_arrays[:, :, i]
        for j, (label, df) in enumerate(zip(labels, dfs)):
            
            if np.max(label) == 0:
                empty_df = pd.DataFrame()
                df.append(empty_df)
                continue
                
            mask_intensity_df = _extended_regionprops_table(label, channel, intensity_props)
            #mask_intensity_df['shannon_entropy'] = shannon_entropy(channel, base=2)

            if homogeneity:
                homogeneity_df = _calculate_homogeneity(label, channel, distances)
                mask_intensity_df = pd.concat([mask_intensity_df.reset_index(drop=True), homogeneity_df], axis=1)

            if periphery:
                if ls[j] == 'nucleus' or ls[j] == 'pathogen':
                    periphery_intensity_stats = _periphery_intensity(label, channel)
                    mask_intensity_df = pd.concat([mask_intensity_df, pd.DataFrame(periphery_intensity_stats, columns=[f'periphery_{stat}' for stat in col_lables])],axis=1)

            if outside:
                if ls[j] == 'nucleus' or ls[j] == 'pathogen':
                    outside_intensity_stats = _outside_intensity(label, channel)
                    mask_intensity_df = pd.concat([mask_intensity_df, pd.DataFrame(outside_intensity_stats, columns=[f'outside_{stat}' for stat in col_lables])], axis=1)

            blur_col = [_estimate_blur(channel[label == region_label]) for region_label in mask_intensity_df['label']]
            mask_intensity_df[f'{ls[j]}_channel_{i}_blur'] = blur_col

            mask_intensity_df.columns = [f'{ls[j]}_channel_{i}_{col}' if col != 'label' else col for col in mask_intensity_df.columns]
            df.append(mask_intensity_df)
            
    if isinstance(settings['distance_gaussian_sigma'], int):
        if settings['distance_gaussian_sigma'] != 0:
            if settings['cell_mask_dim'] != None:
                if settings['nucleus_mask_dim'] != None or settings['pathogen_mask_dim'] != None:
                    intensity_distance_df = _measure_intensity_distance(cell_mask, nucleus_mask, pathogen_mask, channel_arrays, settings)
                    cell_dfs.append(intensity_distance_df)
    
    if radial_dist:
        if np.max(nucleus_mask) != 0:
            nucleus_radial_distributions = _calculate_radial_distribution(cell_mask, nucleus_mask, channel_arrays, num_bins=6)
            nucleus_df = _create_dataframe(nucleus_radial_distributions, 'nucleus')
            dfs[1].append(nucleus_df)
            
        if np.max(pathogen_mask) != 0:
            pathogen_radial_distributions = _calculate_radial_distribution(cell_mask, pathogen_mask, channel_arrays, num_bins=6)
            pathogen_df = _create_dataframe(pathogen_radial_distributions, 'pathogen')
            dfs[2].append(pathogen_df)
        
    if calculate_correlation:
        if channel_arrays.shape[-1] >= 2:
            for i in range(channel_arrays.shape[-1]):
                for j in range(i+1, channel_arrays.shape[-1]):
                    chan_i = channel_arrays[:, :, i]
                    chan_j = channel_arrays[:, :, j]
                    for m, mask in enumerate(labels):
                        coloc_df = _calculate_correlation_object_level(chan_i, chan_j, mask, settings)
                        coloc_df.columns = [f'{ls[m]}_channel_{i}_channel_{j}_{col}' for col in coloc_df.columns]
                        dfs[m].append(coloc_df)
    
    return pd.concat(cell_dfs, axis=1), pd.concat(nucleus_dfs, axis=1), pd.concat(pathogen_dfs, axis=1), pd.concat(cytoplasm_dfs, axis=1)

def save_and_add_image_to_grid(png_channels, img_path, grid, plot=False):
    """
    Add an image to a grid and save it as PNG.

    Args:
        png_channels (ndarray): The array representing the image channels.
        img_path (str): The path to save the image as PNG.
        grid (list): The grid of images to be plotted later.

    Returns:
        grid (list): Updated grid with the new image added.
    """

    # Save the image as a PNG
    cv2.imwrite(img_path, png_channels)

    if plot:

        # Ensure the image is in uint8 format for cv2 functions
        if png_channels.dtype == np.uint16:
            png_channels = (png_channels / 256).astype(np.uint8)
        
        # Get the filename without the extension
        filename = os.path.splitext(os.path.basename(img_path))[0]
        
        # Add the label to the image
        #labeled_image = cv2.putText(png_channels.copy(), filename, (10, 30), 
        #                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Add the labeled image to the grid
        grid.append(png_channels)
    
    return grid

def img_list_to_grid(grid, titles=None):
    """
    Plot a grid of images with optional titles.

    Args:
        grid (list): List of images to be plotted.
        titles (list): List of titles for the images.

    Returns:
        fig (Figure): The matplotlib figure object containing the image grid.
    """
    n_images = len(grid)
    grid_size = ceil(sqrt(n_images))
    
    fig, axs = plt.subplots(grid_size, grid_size, figsize=(15, 15), facecolor='black')
    
    for i, ax in enumerate(axs.flat):
        if i < n_images:
            image = grid[i]
            ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            ax.axis('off')
            ax.set_facecolor('black')
            
            if titles:
                # Determine text size
                img_height, img_width = image.shape[:2]
                text_size = max(min(img_width / (len(titles[i]) * 1.5), img_height / 10), 4)
                ax.text(5, 5, titles[i], color='white', fontsize=text_size, ha='left', va='top', fontweight='bold')
        else:
            fig.delaxes(ax)
    
    # Adjust spacing
    plt.subplots_adjust(wspace=0.05, hspace=0.05)
    plt.tight_layout(pad=0.1)
    return fig

#@log_function_call
def _measure_crop_core(index, time_ls, file, settings):

    """
    Measure and crop the images based on specified settings.

    Parameters:
    - index: int
        The index of the image.
    - time_ls: list
        The list of time points.
    - file: str
        The file path of the image.
    - settings: dict
        The dictionary containing the settings for measurement and cropping.

    Returns:
    - cropped_images: list
        A list of cropped images.
    """
    
    from .plot import _plot_cropped_arrays
    from .utils import _merge_overlapping_objects, _filter_object, _relabel_parent_with_child_labels, _exclude_objects, normalize_to_dtype, filepaths_to_database
    from .utils import _merge_and_save_to_database, _crop_center, _find_bounding_box, _generate_names, _get_percentiles

    figs = {}
    grid = []
    start = time.time() 
    try:
        source_folder = os.path.dirname(settings['src'])

        file_name = os.path.splitext(file)[0]
        data = np.load(os.path.join(settings['src'], file))
        data_type = data.dtype
        if data_type not in ['uint8','uint16']:
            data_type_before = data_type
            data = data.astype(np.uint16)
            data_type = data.dtype
            if settings['verbose']:
                print(f'Converted data from {data_type_before} to {data_type}')

        if settings['plot']:
            if len(data.shape) == 3:
                figuresize = data.shape[2]*10
            else:
                figuresize = 10
            fig = _plot_cropped_arrays(data, file, figuresize)
            figs[f'{file_name}__before_filtration'] = fig
        
        channel_arrays = data[:, :, settings['channels']].astype(data_type)        
        if settings['cell_mask_dim'] is not None:
            cell_mask = data[:, :, settings['cell_mask_dim']].astype(data_type)
            
            if settings['cell_min_size'] is not None and settings['cell_min_size'] != 0:
                cell_mask = _filter_object(cell_mask, settings['cell_min_size'])
        else:
            cell_mask = np.zeros_like(data[:, :, 0])
            settings['cytoplasm'] = False
            settings['uninfected'] = True

        if settings['nucleus_mask_dim'] is not None:
            nucleus_mask = data[:, :, settings['nucleus_mask_dim']].astype(data_type)
            if settings['cell_mask_dim'] is not None:
                nucleus_mask, cell_mask = _merge_overlapping_objects(mask1=nucleus_mask, mask2=cell_mask)
            if settings['nucleus_min_size'] is not None and settings['nucleus_min_size'] != 0:
                nucleus_mask = _filter_object(nucleus_mask, settings['nucleus_min_size'])
            if settings['timelapse_objects'] == 'nucleus':
                if settings['cell_mask_dim'] is not None:
                    cell_mask, nucleus_mask = _relabel_parent_with_child_labels(cell_mask, nucleus_mask)
                    data[:, :, settings['cell_mask_dim']] = cell_mask
                    data[:, :, settings['nucleus_mask_dim']] = nucleus_mask
                    save_folder = settings['src']
                    np.save(os.path.join(save_folder, file), data)
        else:
            nucleus_mask = np.zeros_like(data[:, :, 0])

        if settings['pathogen_mask_dim'] is not None:
            pathogen_mask = data[:, :, settings['pathogen_mask_dim']].astype(data_type)
            if settings['merge_edge_pathogen_cells']:
                if settings['cell_mask_dim'] is not None:
                    pathogen_mask, cell_mask = _merge_overlapping_objects(mask1=pathogen_mask, mask2=cell_mask)
            if settings['pathogen_min_size'] is not None and settings['pathogen_min_size'] != 0:
                pathogen_mask = _filter_object(pathogen_mask, settings['pathogen_min_size'])
        else:
            pathogen_mask = np.zeros_like(data[:, :, 0])

        # Create cytoplasm mask
        if settings['cytoplasm']:
            if settings['cell_mask_dim'] is not None:
                if settings['nucleus_mask_dim'] is not None and settings['pathogen_mask_dim'] is not None:
                    cytoplasm_mask = np.where(np.logical_or(nucleus_mask != 0, pathogen_mask != 0), 0, cell_mask)
                elif settings['nucleus_mask_dim'] is not None:
                    cytoplasm_mask = np.where(nucleus_mask != 0, 0, cell_mask)
                elif settings['pathogen_mask_dim'] is not None:
                    cytoplasm_mask = np.where(pathogen_mask != 0, 0, cell_mask)
                else:
                    cytoplasm_mask = np.zeros_like(cell_mask)
        else:
            cytoplasm_mask = np.zeros_like(cell_mask)

        if settings['cell_min_size'] is not None and settings['cell_min_size'] != 0:
            cell_mask = _filter_object(cell_mask, settings['cell_min_size'])
        if settings['nucleus_min_size'] is not None and settings['nucleus_min_size'] != 0:
            nucleus_mask = _filter_object(nucleus_mask, settings['nucleus_min_size'])
        if settings['pathogen_min_size'] is not None and settings['pathogen_min_size'] != 0:
            pathogen_mask = _filter_object(pathogen_mask, settings['pathogen_min_size'])
        if settings['cytoplasm_min_size'] is not None and settings['cytoplasm_min_size'] != 0:
            cytoplasm_mask = _filter_object(cytoplasm_mask, settings['cytoplasm_min_size'])

        if settings['cell_mask_dim'] is not None and settings['nucleus_mask_dim'] is not None and settings['pathogen_mask_dim'] is not None:
            cell_mask, nucleus_mask, pathogen_mask, cytoplasm_mask = _exclude_objects(cell_mask, nucleus_mask, pathogen_mask, cytoplasm_mask, uninfected=settings['uninfected'])
            data[:, :, settings['cell_mask_dim']] = cell_mask.astype(data_type)

        if settings['nucleus_mask_dim'] is not None:
            data[:, :, settings['nucleus_mask_dim']] = nucleus_mask.astype(data_type)
        if settings['pathogen_mask_dim'] is not None:
            data[:, :, settings['pathogen_mask_dim']] = pathogen_mask.astype(data_type)
        if settings['cytoplasm']:
            data = np.concatenate((data, cytoplasm_mask[:, :, np.newaxis]), axis=2)

        if settings['plot']:
            fig = _plot_cropped_arrays(data, file, figuresize)
            figs[f'{file_name}__after_filtration'] = fig

        if settings['save_measurements']:
            cell_df, nucleus_df, pathogen_df, cytoplasm_df = _morphological_measurements(cell_mask, nucleus_mask, pathogen_mask, cytoplasm_mask, settings)

            #if settings['skeleton']:
                #skeleton_df = _analyze_cytoskeleton(image=channel_arrays, mask=cell_mask, channel=1)
                #merge skeleton_df with cell_df here

            cell_intensity_df, nucleus_intensity_df, pathogen_intensity_df, cytoplasm_intensity_df = _intensity_measurements(cell_mask, nucleus_mask, pathogen_mask, cytoplasm_mask, channel_arrays, settings, sizes=[1, 2, 3, 4, 5], periphery=True, outside=True)
                        
            if settings['cell_mask_dim'] is not None:
                cell_merged_df = _merge_and_save_to_database(cell_df, cell_intensity_df, 'cell', source_folder, file_name, settings['experiment'], settings['timelapse'])
            if settings['nucleus_mask_dim'] is not None:
                nucleus_merged_df = _merge_and_save_to_database(nucleus_df, nucleus_intensity_df, 'nucleus', source_folder, file_name, settings['experiment'], settings['timelapse'])

            if settings['pathogen_mask_dim'] is not None:
                pathogen_merged_df = _merge_and_save_to_database(pathogen_df, pathogen_intensity_df, 'pathogen', source_folder, file_name, settings['experiment'], settings['timelapse'])

            if settings['cytoplasm']:
                cytoplasm_merged_df = _merge_and_save_to_database(cytoplasm_df, cytoplasm_intensity_df, 'cytoplasm', source_folder, file_name, settings['experiment'], settings['timelapse'])

        if settings['save_png'] or settings['save_arrays'] or settings['plot']:
            if isinstance(settings['dialate_pngs'], bool):
                dialate_pngs = [settings['dialate_pngs'], settings['dialate_pngs'], settings['dialate_pngs']]
            if isinstance(settings['dialate_pngs'], list):
                dialate_pngs = settings['dialate_pngs']

            if isinstance(settings['dialate_png_ratios'], float):
                dialate_png_ratios = [settings['dialate_png_ratios'], settings['dialate_png_ratios'], settings['dialate_png_ratios']]

            if isinstance(settings['dialate_png_ratios'], list):
                dialate_png_ratios = settings['dialate_png_ratios']

            if isinstance(settings['crop_mode'], str):
                crop_mode = [settings['crop_mode']]
            if isinstance(settings['crop_mode'], list):
                crop_ls = settings['crop_mode']
                size_ls = settings['png_size']
                
                if isinstance(size_ls[0], int):
                    size_ls = [size_ls]
                if len(crop_ls) > 1 and len(size_ls) == 1:
                    size_ls = size_ls * len(crop_ls)
                    
                if len(crop_ls) != len(size_ls):
                    print(f"Setting: size_ls: {settings['png_size']} should be a list of integers, or a list of lists of integers if crop_ls: {settings['crop_mode']} has multiple elements")
                
                for crop_idx, crop_mode in enumerate(crop_ls):
                    width, height = size_ls[crop_idx]

                    if crop_mode == 'cell':
                        crop_mask = cell_mask.copy()
                        dialate_png = dialate_pngs[crop_idx]
                        dialate_png_ratio = dialate_png_ratios[crop_idx]

                    elif crop_mode == 'nucleus':
                        crop_mask = nucleus_mask.copy()
                        dialate_png = dialate_pngs[crop_idx]
                        dialate_png_ratio = dialate_png_ratios[crop_idx]
                    elif crop_mode == 'pathogen':
                        crop_mask = pathogen_mask.copy()
                        dialate_png = dialate_pngs[crop_idx]
                        dialate_png_ratio = dialate_png_ratios[crop_idx]
                    elif crop_mode == 'cytoplasm':
                        crop_mask = cytoplasm_mask.copy()
                        dialate_png = False
                    else:
                        print(f'Value error: Posseble values for crop_mode are: cell, nucleus, pathogen, cytoplasm')

                    objects_in_image = np.unique(crop_mask)
                    objects_in_image = objects_in_image[objects_in_image != 0]
                    img_paths = []
                    
                    for _id in objects_in_image:
                        
                        region = (crop_mask == _id)

                        # Use the boolean mask to filter the cell_mask and then find unique IDs
                        region_cell_ids = np.atleast_1d(np.unique(cell_mask[region]))
                        region_nucleus_ids = np.atleast_1d(np.unique(nucleus_mask[region]))
                        region_pathogen_ids = np.atleast_1d(np.unique(pathogen_mask[region]))

                        if settings['use_bounding_box']:
                            region = _find_bounding_box(crop_mask, _id, buffer=10)

                        img_name, fldr, table_name = _generate_names(file_name=file_name, cell_id = region_cell_ids, cell_nucleus_ids=region_nucleus_ids, cell_pathogen_ids=region_pathogen_ids, source_folder=source_folder, crop_mode=crop_mode)

                        if dialate_png:
                            region_area = np.sum(region)
                            approximate_diameter = np.sqrt(region_area)
                            dialate_png_px = int(approximate_diameter * dialate_png_ratio) 
                            struct = generate_binary_structure(2, 2)
                            region = binary_dilation(region, structure=struct, iterations=dialate_png_px)

                        if settings['save_png']:
                            fldr_type = f"{crop_mode}_png/"
                            png_folder = os.path.join(fldr,fldr_type)
                            img_path = os.path.join(png_folder, img_name)
                            img_paths.append(img_path)

                            png_channels = data[:, :, settings['png_dims']].astype(data_type)

                            if settings['normalize_by'] == 'fov':
                                if not settings['normalize'] is False:
                                    percentile_list = _get_percentiles(png_channels, settings['normalize'][0], settings['normalize'][1])

                            png_channels = _crop_center(png_channels, region, new_width=width, new_height=height)
                            if isinstance(settings['normalize'], list):
                                if settings['normalize_by'] == 'png':
                                    png_channels = normalize_to_dtype(png_channels, settings['normalize'][0], settings['normalize'][1])

                                if settings['normalize_by'] == 'fov':
                                    png_channels = normalize_to_dtype(png_channels, settings['normalize'][0], settings['normalize'][1], percentile_list=percentile_list)
                            else:
                                png_channels = normalize_to_dtype(png_channels, 0, 100)
                            os.makedirs(png_folder, exist_ok=True)

                            if png_channels.shape[2] == 2:
                                dummy_channel = np.zeros_like(png_channels[:,:,0])  # Create a 2D zero array with same shape as one channel
                                png_channels = np.dstack((png_channels, dummy_channel))
                                grid = save_and_add_image_to_grid(png_channels, img_path, grid, settings['plot'])
                            else:
                                grid = save_and_add_image_to_grid(png_channels, img_path, grid, settings['plot'])

                            if len(img_paths) == len(objects_in_image):
                                filepaths_to_database(img_paths, settings, source_folder, crop_mode)

                        if settings['save_arrays']:
                            row_idx, col_idx = np.where(region)
                            region_array = data[row_idx.min():row_idx.max()+1, col_idx.min():col_idx.max()+1, :]
                            array_folder = f"{fldr}/region_array/"            
                            os.makedirs(array_folder, exist_ok=True)
                            np.save(os.path.join(array_folder, img_name), region_array)

                            grid = save_and_add_image_to_grid(png_channels, img_path, grid, settings['plot'])

                            img_paths.append(img_path)
                            if len(img_paths) == len(objects_in_image):
                                filepaths_to_database(img_paths, settings, source_folder, crop_mode)

        cells = np.unique(cell_mask)
    except Exception as e:
        print('main',e)
        cells = 0
        traceback.print_exc()

    end = time.time()
    duration = end-start
    time_ls.append(duration)
    average_time = np.mean(time_ls) if len(time_ls) > 0 else 0
    if settings['plot']:
        fig = img_list_to_grid(grid)
        figs[f'{file_name}__pngs'] = fig
    return index, average_time, cells, figs

#@log_function_call
def measure_crop(settings):
    
    """
    Measure the crop of an image based on the provided settings.

    Args:
        settings (dict): The settings for measuring the crop.

    Returns:
        None
    """

    from .io import _save_settings_to_db
    from .timelapse import _timelapse_masks_to_gif
    from .utils import measure_test_mode, print_progress, delete_intermedeate_files, save_settings, format_path_for_system, normalize_src_path
    from .settings import get_measure_crop_settings

    if not isinstance(settings['src'], (str, list)):
        ValueError(f'src must be a string or a list of strings')
        return
    
    settings['src'] = normalize_src_path(settings['src'])
    
    if isinstance(settings['src'], str):
        settings['src'] = [settings['src']]

    if isinstance(settings['src'], list):
        source_folders = settings['src']
        
        for source_folder in source_folders:
            print(f'Processing folder: {source_folder}')
            
            source_folder = format_path_for_system(source_folder)
            settings['src'] = source_folder
            src = source_folder

            settings = get_measure_crop_settings(settings)
            settings = measure_test_mode(settings)

            src_fldr = settings['src']
            
            if not os.path.basename(src_fldr).endswith('merged'):
                print(f"WARNING: Source folder, settings: src: {src_fldr} should end with '/merged'")
                src_fldr = os.path.join(src_fldr, 'merged')
                settings['src'] = src_fldr
                print(f"Changed source folder to: {src_fldr}")
            
            if settings['cell_mask_dim'] is None:
                settings['uninfected'] = True
            if settings['pathogen_mask_dim'] is None:
                settings['uninfected'] = True
            if settings['cell_mask_dim'] is not None and settings['pathogen_min_size'] is not None:
                settings['cytoplasm'] = True
            elif settings['cell_mask_dim'] is not None and settings['nucleus_min_size'] is not None:
                settings['cytoplasm'] = True
            else:
                settings['cytoplasm'] = False

            spacr_cores = int(mp.cpu_count() - 6)
            if spacr_cores <= 2:
                spacr_cores = 1

            if settings['n_jobs'] > spacr_cores:
                print(f'Warning reserving 6 CPU cores for other processes, setting n_jobs to {spacr_cores}')
                settings['n_jobs'] = spacr_cores

            settings_save = settings.copy()
            settings_save['src'] = os.path.dirname(settings['src'])
            save_settings(settings_save, name='measure_crop_settings', show=True)

            if settings['timelapse_objects'] == 'nucleus':
                if not settings['cell_mask_dim'] is None:
                    tlo = settings['timelapse_objects']
                    print(f'timelapse object:{tlo}, cells will be relabeled to nucleus labels to track cells.')

            int_setting_keys = ['cell_mask_dim', 'nucleus_mask_dim', 'pathogen_mask_dim', 'cell_min_size', 'nucleus_min_size', 'pathogen_min_size', 'cytoplasm_min_size']
            
            if isinstance(settings['normalize'], bool) and settings['normalize']:
                print(f'WARNING: to notmalize single object pngs set normalize to a list of 2 integers, e.g. [1,99] (lower and upper percentiles)')
                return
            
            if isinstance(settings['normalize'], list) or isinstance(settings['normalize'], bool) and settings['normalize']:
                if settings['normalize_by'] not in ['png', 'fov']:
                    print("Warning: normalize_by should be either 'png' to notmalize each png to its own percentiles or 'fov' to normalize each png to the fov percentiles ")
                    return

            if not all(isinstance(settings[key], int) or settings[key] is None for key in int_setting_keys):
                print(f"WARNING: {int_setting_keys} must all be integers")
                return

            if not isinstance(settings['channels'], list):
                print(f"WARNING: channels should be a list of integers representing channels e.g. [0,1,2,3]")
                return

            if not isinstance(settings['crop_mode'], list):
                print(f"WARNING: crop_mode should be a list with at least one element e.g. ['cell'] or ['cell','nucleus'] or [None] got: {settings['crop_mode']}")
                settings['crop_mode'] = [settings['crop_mode']]
                settings['crop_mode'] = [str(crop_mode) for crop_mode in settings['crop_mode']]
                print(f"Converted crop_mode to list: {settings['crop_mode']}")
            
            _save_settings_to_db(settings)
            #save_settings(settings, name='measure_crop', show=True)

            files = [f for f in os.listdir(settings['src']) if f.endswith('.npy')]
            n_jobs = settings['n_jobs']
            print(f'using {n_jobs} cpu cores')
            print_progress(files_processed=0, files_to_process=len(files), n_jobs=n_jobs, time_ls=[], operation_type='Measure and Crop')

            def job_callback(result):
                completed_jobs.add(result[0])
                process_meassure_crop_results([result], settings)
                files_processed = len(completed_jobs)
                files_to_process = len(files)
                print_progress(files_processed, files_to_process, n_jobs, time_ls=time_ls, operation_type='Measure and Crop')
                if files_processed >= files_to_process:
                    pool.terminate()

            with mp.Manager() as manager:
                time_ls = manager.list()
                completed_jobs = set()  # Set to keep track of completed jobs
                
                with mp.Pool(n_jobs) as pool:
                    for index, file in enumerate(files):
                        pool.apply_async(_measure_crop_core, args=(index, time_ls, file, settings), callback=job_callback)
                    
                    pool.close()
                    pool.join()

            if settings['timelapse']:
                if settings['timelapse_objects'] == 'nucleus':
                    folder_path = settings['src']
                    mask_channels = [settings['nucleus_mask_dim'], settings['pathogen_mask_dim'], settings['cell_mask_dim']]
                    object_types = ['nucleus', 'pathogen', 'cell']
                    _timelapse_masks_to_gif(folder_path, mask_channels, object_types)
                    
            if settings['delete_intermediate']:
                delete_intermedeate_files(settings)

            print("Successfully completed run")

def process_meassure_crop_results(partial_results, settings):
    """
    Process the results, display, and optionally save the figures.

    Args:
        partial_results (list): List of partial results.
        settings (dict): Settings dictionary.
        save_figures (bool): Flag to save figures or not.
    """
    for result in partial_results:
        if result is None:
            continue
        index, avg_time, cells, figs = result
        if figs is not None:
            for key, fig in figs.items():
                part_1, part_2 = key.split('__')
                save_dir = os.path.join(os.path.dirname(settings['src']), 'results', f"{part_1}")
                os.makedirs(save_dir, exist_ok=True)
                fig_path = os.path.join(save_dir, f"{part_2}.pdf")
                fig.savefig(fig_path)
                plt.figure(fig.number)
                plt.show()
                plt.close(fig)
            result = (index, None, None, None)
            
def generate_cellpose_train_set(folders, dst, min_objects=5):
    os.makedirs(dst, exist_ok=True)
    os.makedirs(os.path.join(dst,'masks'), exist_ok=True)
    os.makedirs(os.path.join(dst,'imgs'), exist_ok=True)
    
    for folder in folders:
        mask_folder = os.path.join(folder, 'masks')
        experiment_id = os.path.basename(folder)
        for filename in os.listdir(mask_folder):  # List the contents of the directory
            path = os.path.join(mask_folder, filename)
            img_path = os.path.join(folder, filename)
            newname = experiment_id + '_' + filename
            new_mask = os.path.join(dst, 'masks', newname)
            new_img = os.path.join(dst, 'imgs', newname)

            mask = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if mask is None:
                print(f"Error reading {path}, skipping.")
                continue

            nr_of_objects = len(np.unique(mask)) - 1  # Assuming 0 is background
            if nr_of_objects >= min_objects:  # Use >= to include min_objects
                try:
                    shutil.copy(path, new_mask)
                    shutil.copy(img_path, new_img)
                except Exception as e:
                    print(f"Error copying {path} to {new_mask}: {e}")

def get_object_counts(src):
    database_path = os.path.join(src, 'measurements/measurements.db')
    # Connect to the SQLite database
    conn = sqlite3.connect(database_path)
    # Read the table into a pandas DataFrame
    df = pd.read_sql_query("SELECT * FROM object_counts", conn)
    # Group by 'count_type' and calculate the sum of 'object_count' and the average 'object_count' per 'file_name'
    grouped_df = df.groupby('count_type').agg(
        total_object_count=('object_count', 'sum'),
        avg_object_count_per_file_name=('object_count', 'mean')
    ).reset_index()
    # Close the database connection
    conn.close()
    return grouped_df


