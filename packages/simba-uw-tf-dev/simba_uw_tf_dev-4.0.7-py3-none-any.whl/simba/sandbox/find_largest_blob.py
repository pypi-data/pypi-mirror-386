from typing import Dict, Optional, Union, List
from copy import copy
import pandas as pd

try:
    from typing import Literal
except:
    from typing_extensions import Literal

import numpy as np
from shapely.geometry import MultiPolygon, Polygon, Point
from shapely.affinity import scale
from simba.utils.checks import check_instance, check_valid_boolean, check_float, check_if_valid_img, check_str, is_img_bw, check_int
import cv2
from simba.utils.read_write import read_img_batch_from_video_gpu
from simba.utils.enums import GeometryEnum
from simba.mixins.geometry_mixin import GeometryMixin
from simba.mixins.image_mixin import ImageMixin
from simba.utils.errors import InvalidInputError



def find_largest_blob_location(imgs: Dict[int, np.ndarray],
                               verbose: bool = False,
                               video_name: Optional[str] = None,
                               inclusion_zones: Optional[Union[Polygon, MultiPolygon,]] = None,
                               window_size: Optional[int] = None) -> Dict[int, Dict[str, Union[int, np.ndarray]]]:
    """
    Helper to find the largest connected component in binary image. E.g., Use to find a "blob" (i.e., animal) within a background subtracted image.

    .. seealso::
       To create background subtracted videos, use e.g., :func:`simba.video_processors.video_processing.video_bg_subtraction_mp`, or :func:`~simba.video_processors.video_processing.video_bg_subtraction`.
       To get ``img`` dict, use :func:`~simba.utils.read_write.read_img_batch_from_video_gpu` or :func:`~simba.mixins.image_mixin.ImageMixin.read_img_batch_from_video`.
       For relevant notebook, see `BACKGROUND REMOVAL <https://simba-uw-tf-dev.readthedocs.io/en/latest/nb/bg_remove.html>`__.

    .. important::
       Pass black and white [0, 255] pixel values only, where the foreground is 255 and background is 0.

    :param Dict[int, np.ndarray] imgs: Dictionary of images where the key is the frame id and the value is an image in np.ndarray format.
    :param bool verbose: If True, prints progress. Default: False.
    :param video_name video_name: The name of the video being processed for interpretable progress msg if ``verbose``.
    :param Optional[Union[Polygon, MultiPolygon,]] inclusion_zones: If not None, a shapely Polygon or Multipolygon representing the part(s) of the image the blob center is allowed in. If The animal center is OUTSIDE the ``inclusion_zones``, then data is NaN.
    :return: Dictionary where the key is the frame id and the value is a 2D array with x and y coordinates.
    :rtype: Dict[int, np.ndarray]
    """

    check_valid_boolean(value=[verbose], source=f'{find_largest_blob_location.__name__} verbose', raise_error=True)
    if inclusion_zones is not None:
        check_instance(source=f'{find_largest_blob_location.__name__} inclusion_zone', instance=inclusion_zones, accepted_types=(MultiPolygon, Polygon,), raise_error=True)
    if window_size is not None:
        check_int(name='window_size', value=window_size, min_value=1, raise_error=True)
    results, prior_window = {}, None
    for frm_idx, img in imgs.items():
        if verbose:
            if video_name is None: print(f'Finding blob in image {frm_idx}...')
            else: print(f'Finding blob in image {frm_idx} (Video {video_name})...')
        is_img_bw(img=img, raise_error=True, source=f'{find_largest_blob_location.__name__} {frm_idx}')
        contours = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1]
        contours = [cnt.reshape(1, -1, 2) for cnt in contours if len(cnt) >= 3]
        geometries = GeometryMixin().contours_to_geometries(contours=contours, force_rectangles=False)
        if inclusion_zones is not None:
            geo_idx = [inclusion_zones.contains(x.centroid) for x in geometries]
            selected_polygons = [geometries[i] for i in geo_idx]
            geometries = copy(selected_polygons)
        if prior_window is not None:
            geo_idx = [prior_window.contains(x.centroid) for x in geometries]
            selected_polygons = [geometries[i] for i in geo_idx]
            geometries = copy(selected_polygons)
        geometry_stats = GeometryMixin().get_shape_statistics(shapes=geometries)
        geometry = geometries[np.argmax(np.array(geometry_stats['areas']))].convex_hull.simplify(tolerance=5)
        if window_size is not None:
            window_geometry = GeometryMixin.minimum_rotated_rectangle(shape=geometry)
            prior_window = scale(window_geometry, xfact=window_size, yfact=window_size, origin=window_geometry.centroid)
        center = np.array(geometry.centroid.coords)[0].astype(np.int32)
        vertices = np.array(geometry.exterior.coords).astype(np.int32)
        results[frm_idx] = {'x': center[0], 'y': center[1], 'vertices': vertices}
    return results








imgs = read_img_batch_from_video_gpu(video_path=r"C:\troubleshooting\mitra\test\temp\501_MA142_Gi_Saline_0515.mp4", start_frm=0, end_frm=0, black_and_white=True)
data = find_largest_blob_location(imgs=imgs, window_size=3)
data = pd.DataFrame.from_dict(data, orient='index')

#geos = GeometryMixin().contours_to_geometries(contours=contours, force_rectangles=False)