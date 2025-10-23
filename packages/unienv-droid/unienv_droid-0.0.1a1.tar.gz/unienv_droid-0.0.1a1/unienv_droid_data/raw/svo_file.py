# There is some warning with converting the depth to uint16, but this is a valid thing to do (DROID does it).
import warnings
warnings.filterwarnings("ignore")
import time

import os
import pyzed.sl as sl

from .metadata import DroidDatasetEpisodicMetadata
import numpy as np
import cv2
from typing import Tuple, Optional, Any, Dict, List, Union

__all__ = [
    "read_camera_SVO"
]

def zed_camera_intrinsics(
    params
) -> np.ndarray:
    """
    Converts ZED camera intrinsics to a 3x3 numpy array.
    """
    return np.array([
        [params.fx, 0, params.cx],
        [0, params.fy, params.cy],
        [0, 0, 1]
    ], dtype=np.float32)

def rescale_intrinsics(
    intrinsics: np.ndarray,
    scale_x: float,
    scale_y: float
) -> np.ndarray:
    new_intrinsics = intrinsics.copy()
    new_intrinsics[0, 0] *= scale_x  # fx
    new_intrinsics[1, 1] *= scale_y  # fy
    new_intrinsics[0, 2] *= scale_x  # cx
    new_intrinsics[1, 2] *= scale_y  # cy
    return new_intrinsics

def svo_convert(
    filepath: Union[str, os.PathLike],
    target_resolution : sl.Resolution,
    frame_range: Optional[Union[slice, List[int], np.ndarray]] = None,
    depth_mode = sl.DEPTH_MODE.NEURAL,
    read_right = False
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Converts a .svo file to cropped and resized RGB and depth numpy arrays, with scaled intrinsics.
    Extracts only the frames within the given slice.
    
    Parameters:
        filepath: Path to the .svo file.
        output_height: Desired output height of the images.
        output_width: Desired output width of the images.
        frame_range: An optional slice specifying the range of frames to extract (e.g., slice(0, 10)).
                     If None, all frames are extracted.
    
    Returns:
        A tuple of (RGB, Depth, Intrinsics):
            RGB: Array of shape (nframes, output_height, output_width, 3), dtype uint8.
            Depth: Array of shape (nframes, output_height, output_width), dtype uint16.
            Intrinsics: Array of shape (3, 3), dtype float.
    """

    # Note: We'll use left camera images and intrinsics for the DROID dataset (this is how we are getting extrinsics)
    # so we want to keep this consistent.
    initial_parameters = sl.InitParameters()
    initial_parameters.set_from_svo_file(filepath)
    initial_parameters.svo_real_time_mode = False
    initial_parameters.coordinate_units = sl.UNIT.METER
    initial_parameters.camera_image_flip = sl.FLIP_MODE.OFF
    initial_parameters.depth_minimum_distance = 0
    initial_parameters.depth_maximum_distance = 3
    initial_parameters.depth_mode = depth_mode
    initial_parameters.sdk_verbose = 0

    zed = sl.Camera()
    err = zed.open(initial_parameters)
    if err != sl.ERROR_CODE.SUCCESS:
        zed.close()
        raise RuntimeError("Failed to open SVO file.")

    cam_config = zed.get_camera_information().camera_configuration
    calib_params = cam_config.calibration_parameters
    left_intrinsics = zed_camera_intrinsics(calib_params.left_cam)
    right_intrinsics = zed_camera_intrinsics(calib_params.right_cam)

    original_width = cam_config.resolution.width
    original_height = cam_config.resolution.height
    output_width = target_resolution.width
    output_height = target_resolution.height
    total_frames = zed.get_svo_number_of_frames()

    # Determine the range of frames to process
    if frame_range is None:
        frame_indices = None
    elif isinstance(frame_range, slice):
        frame_indices = range(*frame_range.indices(total_frames))
    else:
        frame_indices = frame_range

    # Adjust intrinsics for cropping and scaling
    scale_x = output_width / original_width
    scale_y = output_height / original_height
    scaled_left_intrinsics = rescale_intrinsics(left_intrinsics, scale_x, scale_y)
    scaled_right_intrinsics = rescale_intrinsics(right_intrinsics, scale_x, scale_y)

    nframes = len(frame_indices) if frame_indices is not None else total_frames
    svo_rgb_left = np.empty((nframes, output_height, output_width, 3), dtype=np.uint8)
    svo_depth_left = np.empty((nframes, output_height, output_width), dtype=np.float32)
    rgb_image_left = sl.Mat()
    depth_image_left = sl.Mat()

    if read_right:
        svo_rgb_right = np.empty((nframes, output_height, output_width, 3), dtype=np.uint8)
        svo_depth_right = np.empty((nframes, output_height, output_width), dtype=np.float32)
        rgb_image_right = sl.Mat()
        depth_image_right = sl.Mat()
    else:
        svo_rgb_right = None
        svo_depth_right = None
        rgb_image_right = None
        depth_image_right = None

    rt_param = sl.RuntimeParameters()

    frame_index = 0
    for i in (frame_indices if frame_indices is not None else range(total_frames)):
        i = min(i, total_frames - 1)

        # Seek to the frame
        if frame_indices is not None:
            zed.set_svo_position(i)
        
        # Grab the frame
        err = zed.grab(rt_param)
        if err == sl.ERROR_CODE.END_OF_SVOFILE_REACHED:
            break
        assert err == sl.ERROR_CODE.SUCCESS, f"Failed to grab frame {i}."

        # Retrieve SVO images, LEFT
        zed.retrieve_image(rgb_image_left, sl.VIEW.LEFT, resolution=target_resolution)
        zed.retrieve_measure(depth_image_left, sl.MEASURE.DEPTH, resolution=target_resolution)
        svo_rgb_left[frame_index] = cv2.cvtColor(rgb_image_left.get_data(), cv2.COLOR_RGBA2RGB)
        svo_depth_left[frame_index] = depth_image_left.get_data()

        if read_right:
            zed.retrieve_image(rgb_image_right, sl.VIEW.RIGHT, resolution=target_resolution)
            zed.retrieve_measure(depth_image_right, sl.MEASURE.DEPTH_RIGHT, resolution=target_resolution)
            svo_rgb_right[frame_index] = cv2.cvtColor(rgb_image_right.get_data(), cv2.COLOR_RGBA2RGB)
            svo_depth_right[frame_index] = depth_image_right.get_data()
        
        frame_index += 1

    zed.close()
    svo_depth_left = np.nan_to_num(svo_depth_left, nan=0.0, copy=False)
    svo_depth_right = np.nan_to_num(svo_depth_right, nan=0.0, copy=False) if svo_depth_right is not None else None
    return svo_rgb_left, svo_depth_left, scaled_left_intrinsics, svo_rgb_right, svo_depth_right, scaled_right_intrinsics

def read_camera_SVO(
    episode_dir : Union[str, os.PathLike], 
    metadata : DroidDatasetEpisodicMetadata,
    frame_range: Optional[Union[slice, List[int], np.ndarray]] = None,
    target_resolution : sl.Resolution = sl.Resolution(672, 376),
    depth_mode = sl.DEPTH_MODE.NEURAL,
    read_right = False
) -> Dict[str, Dict[str, np.ndarray]]:
    SVO_folder = os.path.join(episode_dir, 'recordings', 'SVO')
    
    # Returns the ext1, ext2, wrist depth + RGB data (in that order).
    ext1_SVO = os.path.join(SVO_folder, metadata.ext1_cam_serial + '.svo')
    ext2_SVO = os.path.join(SVO_folder, metadata.ext2_cam_serial + '.svo')
    wrist_SVO = os.path.join(SVO_folder, metadata.wrist_cam_serial + '.svo')

    ext_1_rgb_left, ext_1_depth_left, ext_1_intrinsics_left, ext_1_rgb_right, ext_1_depth_right, ext_1_intrinsics_right = svo_convert(ext1_SVO, target_resolution, frame_range, depth_mode=depth_mode, read_right=read_right)
    ext_2_rgb_left, ext_2_depth_left, ext_2_intrinsics_left, ext_2_rgb_right, ext_2_depth_right, ext_2_intrinsics_right = svo_convert(ext2_SVO, target_resolution, frame_range, depth_mode=depth_mode, read_right=read_right)
    wrist_rgb_left, wrist_depth_left, wrist_intrinsics_left, wrist_rgb_right, wrist_depth_right, wrist_intrinsics_right = svo_convert(wrist_SVO, target_resolution, frame_range, depth_mode=depth_mode, read_right=read_right)

    ret = {
        "exterior_image_1_left": ext_1_rgb_left,
        "exterior_depth_1_left": ext_1_depth_left,
        "exterior_image_2_left": ext_2_rgb_left,
        "exterior_depth_2_left": ext_2_depth_left,
        "wrist_image_left": wrist_rgb_left,
        "wrist_depth_left": wrist_depth_left,
        "camera_intrinsics": {
            "exterior_camera_1_left": ext_1_intrinsics_left,
            "exterior_camera_2_left": ext_2_intrinsics_left,
            "wrist_camera_left": wrist_intrinsics_left
        }
    }
    if read_right:
        ret.update({
            "exterior_image_1_right": ext_1_rgb_right,
            "exterior_depth_1_right": ext_1_depth_right,
            "exterior_image_2_right": ext_2_rgb_right,
            "exterior_depth_2_right": ext_2_depth_right,
            "wrist_image_right": wrist_rgb_right,
            "wrist_depth_right": wrist_depth_right,
        })
        ret["camera_intrinsics"].update({
            "exterior_camera_1_right": ext_1_intrinsics_right,
            "exterior_camera_2_right": ext_2_intrinsics_right,
            "wrist_camera_right": wrist_intrinsics_right
        })

    return ret