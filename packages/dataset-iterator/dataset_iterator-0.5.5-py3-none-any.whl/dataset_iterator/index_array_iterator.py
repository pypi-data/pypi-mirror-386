from math import ceil, isclose
import numpy as np
from .utils import ensure_size

INCOMPLETE_LAST_BATCH_MODE = ["KEEP", "CONSTANT_SIZE", "REMOVE"]
class IndexArrayIterator():
    def __init__(self, n, batch_size, shuffle, seed, incomplete_last_batch_mode=INCOMPLETE_LAST_BATCH_MODE[1], step_number:int=0):
        self.n = n
        self.batch_size = batch_size
        self.seed = seed
        self.shuffle = shuffle
        self.batch_index = 0
        self.total_batches_seen = 0
        self.index_array = None
        self.allowed_indexes=np.arange(self.n)
        if isinstance(incomplete_last_batch_mode, str):
            self.incomplete_last_batch_mode = INCOMPLETE_LAST_BATCH_MODE.index(incomplete_last_batch_mode)
        else:
            assert incomplete_last_batch_mode in [0, 1, 2], "Invalid incomplete_last_batch_mode"
            self.incomplete_last_batch_mode = incomplete_last_batch_mode
        self.step_number = step_number
        self.index_probability = None

    def set_allowed_indexes(self, indexes):
        if isinstance(indexes, int):
            self._n = indexes
            self.allowed_indexes=np.arange(self.n)
        else:
            self.allowed_indexes=indexes
            self._n=len(indexes)
        self.index_array=None
        if self.index_probability is not None and len(self.index_probability) != len(self.allowed_indexes):
            self.index_probability = None

    def _get_index_array(self, choice:bool = True):
        array = self.allowed_indexes
        if choice and self.index_probability is not None:
            tiling = len(self.index_probability.shape)==2
            index_probability = np.sum(self.index_probability, axis=1) if tiling else self.index_probability # sum proba per tile
            array = np.random.choice(array, size=array.shape[0], replace=True, p=index_probability)
            #print(f"set index array with proba factor: [{np.min(index_probability) * index_probability.shape[0]}; {np.max(index_probability) * index_probability.shape[0]}] tiling: {tiling}")
        else:
            array = np.copy(array)
        return array

    def get_sample_number(self):
        return len(self.allowed_indexes)

    def get_batch_size(self):
        return self.batch_size

    def set_index_probability(self, value, n_tiles = 1):
        if value is not None:
            if isinstance(n_tiles, (list, tuple)):
                assert len(n_tiles)==1, f"set_index_probability: invalid n_tiles len={len(n_tiles)} expected = 1"
                n_tiles=n_tiles[0]
            if n_tiles is not None and n_tiles > 1:
                value = np.reshape(value, (-1, n_tiles))
            assert value.shape[0] == self.get_sample_number(), f"invalid probability number expected: {self.get_sample_number()} got {value.shape[0]}"
        self.index_probability = value

    def open(self):
        pass

    def close(self, force:bool=False):
        pass

    def enqueuer_init(self):
        return None

    def enqueuer_end(self, params):
        pass

    def __len__(self):
        if self.step_number > 0:
            return self.step_number
        if self.incomplete_last_batch_mode == 2:
            return max(1, self.n // self.batch_size)
        else:
            return (self.n + self.batch_size - 1) // self.batch_size  # round up

    def __getitem__(self, idx):
        length = len(self)
        if idx >= length:
            raise ValueError('Asked to retrieve element {idx}, but the Sequence has length {length}'.format(idx=idx,length=len(self)))
        if self.seed is not None:
            np.random.seed(self.seed + self.total_batches_seen)
        self.total_batches_seen += 1
        if self.index_array is None:
            self._set_index_array()
        if idx == length-1 and self.incomplete_last_batch_mode == 1:
            index_array = self.index_array[-self.batch_size:]
        else:
            index_array = self.index_array[self.batch_size * idx:self.batch_size * (idx + 1)]
        return self._get_batches_of_transformed_samples(index_array)

    def _get_batches_of_transformed_samples(self, index_array):
        raise NotImplementedError("Not implemented")

    def _set_index_array(self):
        self.index_array = np.copy(self._get_index_array())
        self._ensure_step_number() # also sets n

    def _ensure_step_number(self):
        if self.index_array is None:
            return
        step_number = self.step_number
        if self.step_number <= 0:
            if self.incomplete_last_batch_mode == 1 and len(self.index_array) < self.batch_size:
                step_number = 1
            else:
                return
        self.index_array = ensure_size(self.index_array, step_number * self.batch_size, shuffle=self.shuffle)
        self._n = len(self.index_array)

    def disable_random_transforms(self, data_augmentation:bool=True, channels_postprocessing:bool=False):
        return {}

    def enable_random_transforms(self, parameters):
        pass

    def on_epoch_end(self):
        self._set_index_array()

    def reset(self):
        self.batch_index = 0

    @property
    def batch_size(self):
        return self._batch_size

    @batch_size.setter
    def batch_size(self, value):
        if value <= 0:
            raise AttributeError("batch_size must be >0")
        self._batch_size = value
        if hasattr(self, "step_number") and hasattr(self, "index_array"):
            self._ensure_step_number()

    @property
    def step_number(self):
        return self._step_number

    @step_number.setter
    def step_number(self, value):
        self._step_number = value
        if hasattr(self, "batch_size") and hasattr(self, "index_array"):
            self._ensure_step_number()

    @property
    def n(self):
        return self._n

    @n.setter
    def n(self, value):
        if hasattr(self, "allowed_indexes"):
            raise AttributeError("Cannot set n after initialization")
        self._n = value

    @property
    def index_probability(self):
        return self._index_probability

    @index_probability.setter
    def index_probability(self, value):
        if value is not None:
            size = self.get_sample_number()
            assert size == len(value), f"invalid index_probability length: expected: {size} actual {len(value)}"
            assert isclose(np.sum(value), 1.), "probabilities do not sum to 1"
        self._index_probability = value
