from math import isclose
import numpy as np
from .index_array_iterator import IndexArrayIterator, INCOMPLETE_LAST_BATCH_MODE
from .utils import ensure_multiplicity, ensure_size

class ConcatIterator(IndexArrayIterator):
    def __init__(self,
                 iterators:list,
                 batch_size:int,
                 proportion:list=None,
                 shuffle:bool=True,
                 seed = None,
                 incomplete_last_batch_mode:str=INCOMPLETE_LAST_BATCH_MODE[1],
                 step_number:int=0):
        assert isinstance(iterators, (list, tuple)), "iterators must be either list or tuple"
        self.iterators = []

        def append_it(iterator): # unroll concat iterators
            if isinstance(iterator, (list, tuple)):
                for subit in iterator:
                    append_it(subit)
            elif isinstance(iterator, ConcatIterator):
                for subit in iterator.iterators:
                    append_it(subit)
            else:
                self.iterators.append(iterator)

        append_it(iterators)
        bs = [it.get_batch_size() for it in self.iterators]
        if np.all(np.array(bs) == bs[0]):
            self.sub_iterator_batch_size = bs[0]
        else:
            self.sub_iterator_batch_size = None

        for it in self.iterators:
            it.incomplete_last_batch_mode = incomplete_last_batch_mode
        if proportion is None:
            proportion = [1.]
        self.proportion = ensure_multiplicity(len(iterators), proportion)
        it_len = np.array([len(it) for it in self.iterators])
        for i in range(1, len(it_len)):
            it_len[i]=it_len[i-1]+it_len[i]
        self.it_cumlen=it_len
        self.it_off=np.insert(self.it_cumlen[:-1], 0, 0)
        super().__init__(-1, batch_size, shuffle, seed, incomplete_last_batch_mode, step_number=step_number)

    def _get_index_array(self, choice:bool = True): # return concatenated indices for all iterators. not used by _set_index_array
        N = self.get_sample_number()
        if choice and self.index_probability is not None:
            tiling = len(self.index_probability.shape) == 2
            index_probability = np.sum(self.index_probability, axis=1) if tiling else self.index_probability  # sum proba per tile
            return np.random.choice(N, size=N, replace=True, p=index_probability)
        else:
            return np.arange(N)

    def get_sample_number(self):
        return self.it_cumlen[-1]

    def get_batch_size(self):
        assert self.sub_iterator_batch_size is not None, "some subiterator have batch size that differ"
        return self.batch_size * self.sub_iterator_batch_size

    def _set_index_array(self):
        indices_per_iterator = []
        for i, it in enumerate(self.iterators):
            if self.proportion[i] > 0:
                index_array = np.arange(self.it_off[i], self.it_cumlen[i])
                size = max(1, int((self.it_cumlen[i] - self.it_off[i]) * self.proportion[i] + 0.5))
                if self.index_probability is not None:
                    proba = self.index_probability[self.it_off[i]:self.it_cumlen[i]]
                    if len(proba.shape) == 2: # tiles probability
                        proba = np.sum(proba, axis=1)
                    proba = proba / np.sum(proba)
                    index_array = np.random.choice(index_array, size=size, replace=True, p=proba)
                    #print( f"concat it: set index array for it {i} with proba factor: [{np.min(self.index_probability[self.it_off[i]:self.it_cumlen[i]]) * (self.it_cumlen[i] - self.it_off[i] + 1) }; {np.max(self.index_probability[self.it_off[i]:self.it_cumlen[i]]) * (self.it_cumlen[i] - self.it_off[i] + 1)}] ")
                else:
                    index_array = ensure_size(index_array, size, shuffle=self.shuffle)
                indices_per_iterator.append(index_array)
        index_a = np.concatenate(indices_per_iterator)
        if self.shuffle:
            self.index_array = np.random.permutation(index_a)
        else:
            self.index_array = index_a
        self._ensure_step_number()
        self._n = len(self.index_array)

    def __len__(self):
        if self.n<0:
            self._set_index_array() # also set self.n
        return super().__len__()

    def _get_batches_of_transformed_samples(self, index_array):
        index_array = np.copy(index_array) # so that main index array is not modified
        index_it = self._get_it_idx(index_array) # modifies index_array so that indices are relative to each iterator
        #batches = [self.iterators[it_idx]._get_batches_of_transformed_samples(index_array[index_it==it_idx]) for it_idx in np.unique(index_it)]
        batches = [self.iterators[it][i] for i, it in zip(index_array, index_it)]
        for i in range(1, len(batches)):
            assert len(batches[i])==len(batches[0]), f"Iterators have different outputs: batch from iterator {index_it[0]} has length {len(batches[0])} whereas batch from iterator {index_it[i]} has length {batches[i]}"
        # concatenate batches
        if len(batches[0]) == 2:
            inputs = [b[0] for b in batches]
            outputs = [b[1] for b in batches]
            return concat_numpy_arrays(inputs), concat_numpy_arrays(outputs)
        else:
            batches = [b[0] for b in batches] # single output is a 1-tuple
            return concat_numpy_arrays(batches),

    def _get_it_idx(self, index_array): # !! modifies index_array
        it_idx = np.searchsorted(self.it_cumlen, index_array, side='right')
        index_array -= self.it_off[it_idx] # remove ds offset to each index
        return it_idx

    def set_allowed_indexes(self, indexes):
        raise NotImplementedError("Not supported yet")

    def enqueuer_init(self):
        return [it.enqueuer_init() for it in self.iterators]

    def enqueuer_end(self, params):
        for i, p in enumerate(params):
            self.iterators[i].enqueuer_end(p)

    def close(self, force:bool=False):
        for it in self.iterators:
            it.close(force)

    def _close_datasetIO(self):
        for it in self.iterators:
            it._close_datasetIO()

    def _open_datasetIO(self):
        for it in self.iterators:
            it._open_datasetIO()

    def open(self):
        for it in self.iterators:
            it.open()

    def disable_random_transforms(self, data_augmentation:bool=True, channels_postprocessing:bool=False):
        return [it.disable_random_transforms(data_augmentation, channels_postprocessing) for it in self.iterators]

    def enable_random_transforms(self, parameters):
        for it, params in zip(self.iterators, parameters):
            it.enable_random_transforms(params)

    def set_index_probability(self, value, n_tiles = 1): # set to sub_iterators/ expects a concatenated vector in the order of sub iterators
        if value is not None:
            cur_idx = 0
            n_tiles = ensure_multiplicity(len(self.iterators), n_tiles)
            for it, n_t in zip(self.iterators, n_tiles):
                size = it.get_sample_number() * n_t
                proba = value[cur_idx:cur_idx+size]
                sum_p = np.sum(proba)
                if sum_p == 0:
                    proba = np.ones_like(proba) / float(size)
                else:
                    proba = proba / sum_p
                it.set_index_probability(proba, n_tiles=n_t)
                cur_idx+=size
            assert cur_idx == value.shape[0], f"Concat iterator: invalid index_probability length expected: {cur_idx} actual {value.shape[0]}"
        else:
            for it in self.iterators:
                it.set_index_probability(None, 1)

def concat_numpy_arrays(arrays):
    if isinstance(arrays[0], (list, tuple)):
        n = len(arrays[0])
        for i in range(1, len(arrays)):
            assert len(arrays[i])==n, "Iterators have different outputs"
        return [np.concatenate([ a[i] for a in arrays], 0) for i in range(n)]
    else:
        return np.concatenate(arrays, 0)
