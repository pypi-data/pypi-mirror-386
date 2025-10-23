from .datasetIO import DatasetIO
import threading
import os
from os import listdir
from os.path import isfile, join, basename
from tensorflow.keras.utils import img_to_array
from math import log10
import numpy as np
try:
    from PIL import Image as pil_image
except ImportError:
    pil_image = None
try:
    from tifffile import imwrite as tiff_write
except ImportError:
    tiff_write = None
try:
    import imageio as imio
except ImportError:
    imio = None

if pil_image is not None:
    _PIL_INTERPOLATION_METHODS = {
        'nearest': pil_image.NEAREST,
        'bilinear': pil_image.BILINEAR,
        'bicubic': pil_image.BICUBIC,
    }
    if hasattr(pil_image, 'HAMMING'):
        _PIL_INTERPOLATION_METHODS['hamming'] = pil_image.HAMMING
    if hasattr(pil_image, 'BOX'):
        _PIL_INTERPOLATION_METHODS['box'] = pil_image.BOX
    if hasattr(pil_image, 'LANCZOS'):
        _PIL_INTERPOLATION_METHODS['lanczos'] = pil_image.LANCZOS

SUPPORTED_IMAGE_FORMATS = ('.png', '.tif', '.tiff')
SUPPORTED_IMAGEIO_FORMATS = ('.mov',)

class MultipleFileIO(DatasetIO):
    """Allows to iterate an image dataset that contains several image files compatible with PILLOW

    Parameters
    ----------
    directory : string
        Each subdirectory in this directory will be considered to contain images from one channel with the name of the channel corresponding to the name of the subdirectory
    one_image_per_file : boolean
        whether each file contains a single frame or not.
        if n_image_per_file == 1 the following structure is expected :
            path
            ├── ...
            ├── dataset_name0
            │   ├── channel0
            │   │   ├──frame0 (= single frame image)
            │   │   ├──frame1
            │   │   └── ...
            │   └── channel1
            │   │   ├──frame0
            │   │   ├──frame1
            │   │   └── ...
            │   └── ...
            ├── dataset_name1
            │   ├── channel0
            │   └── channel1
            │   └── ...
            └── ...
        otherwise:
            set zero if each file contains several images but this number is unknown
            the following structure is expected:
            path
            ├── ...
            ├── dataset_name0
            │   ├── channel0 (= multiple frame image)
            │   ├── channel1
            │   └── ...
            ├── dataset_name1
            │   ├── channel0
            │   ├── channel1
            │   └── ...
            └── ...
    target_shape : tuple
        tuple of integers, dimensions to resize input images to. if None all image must have same dimension. no check is done at initialization
    channel_map_interpolation : dict
        interpolation scheme for each channel. Key is the channel directory
        value is the interpolation method used to resample the image if the
          target size is different from that of the loaded image.
          Supported methods are "nearest", "bilinear", and "bicubic".
          If PIL version 1.1.3 or newer is installed, "lanczos" is also
          supported. If PIL version 3.4.0 or newer is installed, "box" and
          "hamming" are also supported.
          if None: crop to target_shape is performed. If not none, an iterpolation for each channel that will be used must be provided
    data_format : type
        one of `channels_first`, `channels_last`.
    data_type : string
        type to use for generated arrays.
    supported_image_fun : type
        function that takes a file name as argument and return whether the file is a supported image type

    Attributes
    ----------
    image_shape : tuple
        target image shape
    one_image_per_file
    supported_image_fun
    channel_map_interpolation : interpolation function for each channel, or None
    data_format
    data_type

    """
    def __init__(self, directory, one_image_per_file, target_shape=None, channel_map_interpolation=None, data_format='channels_last', data_type='float32', supported_image_fun = lambda f : f.lower().endswith(SUPPORTED_IMAGE_FORMATS), supported_imageio_fun = lambda f : f.lower().endswith(SUPPORTED_IMAGEIO_FORMATS), write_format='tif'):
        super().__init__()
        self.path = directory
        if pil_image is None:
            raise ImportError('Could not import PIL.Image. The use of `MultipleFilesIO` requires PIL.')
        if channel_map_interpolation is not None:
            assert target_shape is not None, "target_shape must be provided if channel_map_interpolation is provided"
        self.one_image_per_file = one_image_per_file
        self.image_shape = target_shape
        self.supported_image_fun = supported_image_fun
        self.supported_imageio_fun=supported_imageio_fun
        self.channel_map_interpolation = {c:get_interpolation_function(target_shape, i) for c,i in channel_map_interpolation.items()} if channel_map_interpolation is not None else None
        self.channel_map_nn_interpolation = {c:i=='nearest' for c,i in channel_map_interpolation.items() } if channel_map_interpolation is not None else None # flag channels that have nearest neighbor interpolation to avoid converting them to float
        self.data_format = data_format
        self.dtype = data_type
        self.crop_function = get_crop_function(target_shape) if target_shape is not None else None
        self.write_format = write_format.lower().replace('.', '')

    def close(self):
        pass

    def get_dataset_paths(self, channel_keyword, group_keyword=None):
        channel_keyword = fix_keyword(channel_keyword)
        all_dirs = scandir(self.path)
        if self.one_image_per_file:
            return [d for d in all_dirs if os.path.basename(d) == channel_keyword and (group_keyword is None or group_keyword in d) ]
        else:
            if len(all_dirs)==0:
                all_dirs = [self.path]
            filtered_dirs = all_dirs if group_keyword is None else [d for d in all_dirs if group_keyword in d]
            all_imgs = []
            for d in filtered_dirs:
                all_imgs.extend(self.get_images(d, name = channel_keyword))
                all_imgs.extend(self.get_images(d, name = channel_keyword, npy=True))
                all_imgs.extend(self.get_images(d, name=channel_keyword, imageio=True))
            return all_imgs

    def __getitem__(self, path):
        return self.get_dataset(path)

    def get_dataset(self, path):
        if self.one_image_per_file:
            channel_keyword = os.path.basename(os.path.normpath(path))
            return ImageListWrapper(path, self, channel_keyword)
        else:
            channel_keyword = os.path.splitext(os.path.basename(path))[0]
            return ImageWrapper(path, self, channel_keyword)

    def get_attribute(self, path, attribute_name):
        return None

    def create_dataset(self, path, **create_dataset_kwargs):
        pass

    def __contains__(self, key):
        if self.one_image_per_file: # datasets are channel folders
            for root, dirs, files in os.walk(self.path):
                if key in dirs:
                    return True
            return False
        else: # datasets are channel files
            for root, dirs, files in os.walk(self.path):
                if key in files:
                    return True
            return False

    def write_direct(self, path, data, source_sel=None, dest_sel=None):
        if (source_sel is not None or dest_sel is not None) and not self.one_image_per_file:
            assert (source_sel is None or source_sel == np.s_[0:data.shape[0]]) and (dest_sel is None or dest_sel == np.s_[0:data.shape[0]]), "index selection is only supported if one_image_per_file is True"
        if not os.path.isabs(path):
            path = os.path.join(self.path, path)
        if self.one_image_per_file:
            if not os.path.isdir(path):
                os.makedirs(path)
            n_zeros = int(log10( len(data) )) + 1
            if dest_sel is None:
                dest_sel = source_sel
            for i, j in zip(source_sel, dest_sel):
                self.write(os.path.join(path, str(j).zfill(n_zeros)), data[i])
        else:
            if not os.path.isdir(get_parent_path(path)):
                os.makedirs(get_parent_path(path))
            self.write(path, data)

    def write(self, path, data):
        if self.write_format == 'tif' or self.write_format == 'tiff' or self.write_format == "ome.tif" or self.write_format == "ome.tiff" and tiff_write is not None:
            if len(data.shape) == 2:
                dimorder = "YX"
            elif len(data.shape) == 3:
                if self.data_format=='channels_last':
                    data = np.transpose(data, axes=[2, 0, 1])
                dimorder = "CYX"
            elif len(data.shape) == 4:
                if self.one_image_per_file:
                    if self.data_format == 'channels_last':
                        data = np.transpose(data, axes=[3, 0, 1, 2])
                    dimorder = "CZYX"
                else:
                    if self.data_format == 'channels_last':
                        data = np.transpose(data, axes=[0, 3, 1, 2])
                    dimorder = "TCYX"
            elif len(data.shape) == 5:
                if self.data_format == 'channels_last':
                    data = np.transpose(data, axes=[0, 4, 1, 2, 3])
                dimorder = "TCZYX"
            else :
                raise ValueError("Rank >5 not supported")
            format = "ome.tif" if len(data.shape)>3 else self.write_format # force OME-TIFF
            tiff_write(f"{path}.{format}", data=data, ome=True, metadata={'axes': dimorder})
        else: # fallback to numpy
            np.save(path, data, allow_pickle=True)

    def get_images(self, path, name = None, npy=False, imageio=False):
        if npy:
            return sorted([join(path, f) for f in listdir(path) if f.lower().endswith('.npy') and (name is None or name in f)])
        elif imageio:
            return sorted([join(path, f) for f in listdir(path) if self.supported_imageio_fun(f.lower()) and (name is None or name in f)])
        else:
            return sorted([join(path, f) for f in listdir(path) if self.supported_image_fun(f.lower()) and (name is None or name in f)])

def fix_keyword(keyword):
    if keyword is None:
        return None
    if keyword[0]=='/':
        keyword = keyword[1:]
    return keyword

def get_parent_path(path):
    return os.path.dirname(os.path.normpath(path))

def get_crop_function(target_shape):
    target_size = target_shape[::-1]
    width, height = target_size
    def fun(img):
        if img.size != target_size:
            return img.crop((0, 0, width, height))
        else:
            return img
    return fun

def scandir(dirname):
    subfolders= [f.path for f in os.scandir(dirname) if f.is_dir()]
    for dirname in list(subfolders):
        subfolders.extend(scandir(dirname))
    return subfolders

# adapted from keras_preprocessing
def get_interpolation_function(target_shape, interpolation):
    target_size = target_shape[::-1]
    if interpolation not in _PIL_INTERPOLATION_METHODS:
        raise ValueError('Invalid interpolation method {} specified. Supported methods are {}'.format(interpolation, ", ".join(_PIL_INTERPOLATION_METHODS.keys())))
    resample = _PIL_INTERPOLATION_METHODS[interpolation]
    def fun(img):
        if img.size != target_size:
            return img.resize(target_size, resample)
        else:
            return img
    return fun

# one file with multiple images
class ImageWrapper():
    def __init__(self, path, mfileIO, channel_keyword):
        self.path = path
        self.mfileIO=mfileIO
        self.npy = path.endswith('.npy')
        self.imageio = not self.npy and mfileIO.supported_imageio_fun(basename(path).lower())
        if not mfileIO.one_image_per_file or mfileIO.image_shape is None: # get shape from image file
            if self.npy:
                img = np.load(self.path, mmap_mode='r')
                self.shape = img.shape
                self.dtype= img.dtype
            elif self.imageio:
                self.imageio_reader = imio.get_reader(path, 'ffmpeg')
                first_frame = self.imageio_reader.get_data(0)
                meta_data = self.imageio_reader.get_meta_data()
                num_frames = meta_data['nframes']
                if np.isinf(num_frames) or np.isnan(num_frames):
                    num_frames = meta_data['duration'] * meta_data['fps']
                    if np.isinf(num_frames) or np.isnan(num_frames):
                        num_frames = get_number_of_frames(path)
                    else:
                        num_frames = int(num_frames)
                else:
                    num_frames = int(num_frames)
                self.shape = (num_frames,) + tuple(first_frame.shape)
                self.dtype = first_frame.dtype
            else:
                self.image = pil_image.open(self.path)
                self.shape = (self.image.n_frames,) + (mfileIO.image_shape if mfileIO.image_shape is not None else self.image.size[::-1])
                self.dtype = get_pil_image_dtype(self.image) # not tested
        else:
            self.shape = (1,) + mfileIO.image_shape
        self.image = None
        self.interpolator = self.mfileIO.channel_map_interpolation[channel_keyword] if self.mfileIO.channel_map_interpolation is not None else None
        if self.interpolator is None and self.mfileIO.crop_function is not None:
            self.interpolator = self.mfileIO.crop_function
        self.convert = not self.mfileIO.channel_map_nn_interpolation[channel_keyword] if self.mfileIO.channel_map_nn_interpolation is not None else False
        if self.npy or self.imageio:
            assert self.interpolator is None, "interpolation not supported (yet) with npy files"
        self.__lock__ = None if self.npy else threading.Lock()

    def __getitem__(self, idx):
        if self.npy:
            return np.load(self.path, mmap_mode='r')[idx]
        elif self.imageio:
            if isinstance(idx, slice):
                return np.stack([self.imageio_reader.get_data(i) for i in self._slice_to_indices(idx)], 0)
            else:
                return self.imageio_reader.get_data(idx)
        else:
            with self.__lock__:
                if self.image is None:
                    self.image = pil_image.open(self.path)
                if isinstance(idx, slice):
                    return np.stack([self._open_pil_image(i) for i in self._slice_to_indices(idx)], 0)
                else:
                    assert idx<self.shape[0] and idx>=0, "invalid index"
                    return self._open_pil_image(idx)

    def _slice_to_indices(self, s:slice):
        start = s.start or 0
        stop = s.stop or self.shape[0]
        step = s.step or 1
        return list(range(start, stop, step))

    def _open_pil_image(self, idx:int):
        self.image.seek(idx)
        if self.interpolator is not None:
            pil_img = self.image.convert("F") if self.convert else self.image
            pil_img = self.interpolator(pil_img)
        else:
            pil_img = self.image
        return img_to_array(pil_img, data_format=self.mfileIO.data_format, dtype=self.mfileIO.dtype)

    def __len__(self):
        return self.shape[0]

# several files with one single image
class ImageListWrapper():
    def __init__(self, directory, mfileIO, channel_keyword):
        self.path = directory
        self.mfileIO=mfileIO
        self.image_paths = mfileIO.get_images(directory)
        if len(self.image_paths)==0: # try with npy images
            self.image_paths = mfileIO.get_images(directory, npy=True)
            self.npy = True
            if len(self.image_paths)==0:
                raise ValueError("No supported image found in dir: {}".format(directory))
        else:
            self.npy = False
        self.interpolator = self.mfileIO.channel_map_interpolation[
            channel_keyword] if self.mfileIO.channel_map_interpolation is not None else None
        if self.interpolator is None and self.mfileIO.crop_function is not None:
            self.interpolator = self.mfileIO.crop_function
        self.convert = not self.mfileIO.channel_map_nn_interpolation[
            channel_keyword] if self.mfileIO.channel_map_nn_interpolation is not None else False

        if mfileIO.image_shape is None:
            if self.npy:
                img = np.load(self.image_paths[0], mmap_mode='r')
                self.shape = (len(self.image_paths),) + img.shape
                self.dtype = img.dtype
            else:
                pil_img = pil_image.open(self.image_paths[0])
                nchan = get_pil_image_nchan(pil_img)
                self.dtype = self.mfileIO.dtype
                if nchan is None:
                    x = np.asarray(pil_img, dtype=self.mfileIO.dtype)
                    nchan = x.shape[-1]
                self.shape = (len(self.image_paths),) + pil_img.size[::-1] + (nchan,)
        else:
            self.shape = (len(self.image_paths),) + mfileIO.image_shape

        if self.npy:
            assert self.interpolator is None, "interpolation not supported (yet) with npy files"

    def _slice_to_indices(self, s:slice):
        start = s.start or 0
        stop = s.stop or self.shape[0]
        step = s.step or 1
        return list(range(start, stop, step))

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            idxs = self._slice_to_indices(idx)
            return np.stack([self[i] for i in idxs], 0)
        if self.npy:
            return np.load(self.image_paths[idx], mmap_mode='r')
        else:
            pil_img = pil_image.open(self.image_paths[idx])
            if self.interpolator is not None:
                if self.convert:
                    pil_img = pil_img.convert("F")
                pil_img = self.interpolator(pil_img)
            return img_to_array(pil_img, data_format=self.mfileIO.data_format, dtype=self.mfileIO.dtype)

    def __len__(self):
        return len(self.image_paths)

def get_number_of_frames(video_path):
    import subprocess
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-count_packets',
        '-show_entries', 'stream=nb_read_packets',
        '-of', 'csv=p=0',
        video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return int(result.stdout.strip())

def get_pil_image_dtype(image:pil_image.Image):
    mode = image.mode
    if mode in ['1', 'L', 'P', 'RGB', 'RGBA', 'CMYK']:
        return 'uint8'
    elif mode == 'I':
        return 'int32'
    elif mode == 'F':
        return 'float32'
    else:
        return None

def get_pil_image_nchan(image:pil_image.Image):
    mode = image.mode
    if mode == '1' or mode == 'L' or mode == 'P' or mode == 'I' or mode == 'F':
        return 1
    elif mode == 'RGB':
        return 3
    elif mode == 'RGBA' or mode == 'CMYK':
        return 4
    else:
        return None