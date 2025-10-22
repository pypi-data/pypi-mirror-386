import os
import zlib
import pickle
import hashlib
import pandas as pd
import numpy as np

class byteBars:
    """
    A disk-backed, compressed, lazy-loading DataFrame-like storage system.
    Supports row-wise and column-wise access, vectorized operations, 
    appending new data, and SHA-256 integrity verification.
    """

    HASH_SIZE = 64  # SHA-256 hex string length

    def __init__(self, data_file, index_file, block_size=100, load_existing=True):
        """
        Initialize the LazyCompressedDataFrame.

        Parameters:
        -----------
        data_file : str
            Path to the binary data file.
        index_file : str
            Path to the index file storing block metadata.
        block_size : int
            Number of rows per block (for compression).
        load_existing : bool
            Whether to load existing files if present.
        """
        self.data_file = data_file
        self.index_file = index_file
        self.block_size = block_size
        self.index = []
        self.pending_block = []
        self._last_block_idx = None
        self._last_block_data = None
        self.columns = None

        # Initialize files if they do not exist
        if not os.path.exists(self.data_file):
            with open(self.data_file, "wb") as f:
                f.write(b"0"*self.HASH_SIZE)
        if not os.path.exists(self.index_file):
            with open(self.index_file, "wb") as f:
                f.write(b"0"*self.HASH_SIZE)

        if load_existing:
            self.load_existing_files()

    # ------------------------------
    # Hash utilities
    # ------------------------------
    def _compute_hash(self, file_path):
        """
        Compute SHA-256 hash of the file, skipping the header.

        Parameters:
        -----------
        file_path : str
            Path to the file.

        Returns:
        --------
        str : SHA-256 hex digest.
        """
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            f.seek(self.HASH_SIZE)
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _write_header(self, file_path, hash_str):
        """
        Write a hash string to the header of a file.

        Parameters:
        -----------
        file_path : str
            Path to the file.
        hash_str : str
            SHA-256 hash string to write.
        """
        with open(file_path, "r+b") as f:
            f.seek(0)
            f.write(hash_str.encode("utf-8"))

    def _read_header(self, file_path):
        """
        Read the SHA-256 hash from the header of a file.

        Parameters:
        -----------
        file_path : str
            Path to the file.

        Returns:
        --------
        str : Hash string stored in header.
        """
        with open(file_path, "rb") as f:
            f.seek(0)
            return f.read(self.HASH_SIZE).decode("utf-8")

    def validate_files(self):
        """
        Validate that data and index files match each other using hashes.
        Raises ValueError if inconsistency is detected.
        """
        data_hash_in_header = self._read_header(self.data_file)
        index_hash_in_header = self._read_header(self.index_file)
        current_data_hash = self._compute_hash(self.data_file)
        current_index_hash = self._compute_hash(self.index_file)
        if data_hash_in_header != current_index_hash:
            raise ValueError("Data file header does not match current index file!")
        if index_hash_in_header != current_data_hash:
            raise ValueError("Index file header does not match current data file!")

    # ------------------------------
    # Load existing files
    # ------------------------------
    def load_existing_files(self):
        """
        Load index and column information from existing files if present.
        Validates files first.
        """
        if os.path.getsize(self.data_file) > self.HASH_SIZE and os.path.getsize(self.index_file) > self.HASH_SIZE:
            self.validate_files()
            with open(self.index_file, "rb") as f:
                f.seek(self.HASH_SIZE)
                self.index = pickle.load(f)
            if self.index:
                self.columns = self._load_block(0)[0].keys()

    # ------------------------------
    # Core methods
    # ------------------------------
    def add_row(self, row):
        """
        Add a single row to the pending block.

        Parameters:
        -----------
        row : dict or pd.Series
            Row data to append. Columns are inferred from the first row.
        """
        if isinstance(row, pd.Series):
            row = row.to_dict()
        elif not isinstance(row, dict):
            raise TypeError("Row must be dict or pd.Series")
        if self.columns is None:
            self.columns = list(row.keys())
        self.pending_block.append(row)
        if len(self.pending_block) >= self.block_size:
            self._flush_block()

    def add_dataframe(self, df):
        """
        Add a Pandas DataFrame to the store.

        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame to append.
        """
        if self.columns is None:
            self.columns = df.columns.tolist()
        for _, row in df.iterrows():
            self.add_row(row)

    def _flush_block(self):
        """
        Compress and write the pending block to disk, update index and headers.
        """
        if not self.pending_block:
            return
        serialized = pickle.dumps(self.pending_block)
        compressed = zlib.compress(serialized, level=9)
        with open(self.data_file, "ab") as f:
            offset = f.tell()
            f.write(compressed)
            length = len(compressed)
            self.index.append((offset, length, len(self.pending_block)))
        self.pending_block = []
        self._save_index()
        self._update_headers()
        self._last_block_idx = None
        self._last_block_data = None

    def _save_index(self):
        """Serialize and save the index to the index file."""
        with open(self.index_file, "r+b") as f:
            f.seek(self.HASH_SIZE)
            pickle.dump(self.index, f)

    def _update_headers(self):
        """Update the SHA-256 headers for integrity check."""
        data_hash = self._compute_hash(self.index_file)
        index_hash = self._compute_hash(self.data_file)
        self._write_header(self.data_file, data_hash)
        self._write_header(self.index_file, index_hash)

    def _load_block(self, block_idx):
        """
        Load a block from disk (decompress) or return cached.

        Parameters:
        -----------
        block_idx : int
            Index of block to load.

        Returns:
        --------
        list : List of row dictionaries in the block.
        """
        if self._last_block_idx == block_idx:
            return self._last_block_data
        block_offset, block_length, _ = self.index[block_idx]
        with open(self.data_file, "rb") as f:
            f.seek(block_offset)
            compressed = f.read(block_length)
            block_data = pickle.loads(zlib.decompress(compressed))
        self._last_block_idx = block_idx
        self._last_block_data = block_data
        return block_data

    # ------------------------------
    # Retrieval
    # ------------------------------
    def retrieve_row(self, idx):
        """
        Retrieve a single row by global index.

        Parameters:
        -----------
        idx : int
            Row index.

        Returns:
        --------
        dict : Row data as a dictionary.
        """
        running_total = 0
        for block_idx, (_, _, num_entries) in enumerate(self.index):
            if running_total + num_entries > idx:
                return self._load_block(block_idx)[idx - running_total]
            running_total += num_entries
        pending_idx = idx - running_total
        if 0 <= pending_idx < len(self.pending_block):
            return self.pending_block[pending_idx]
        raise IndexError("Index out of range")

    def retrieve_block(self, block_idx, as_dataframe=True):
        """
        Retrieve an entire block.

        Parameters:
        -----------
        block_idx : int
            Block index.
        as_dataframe : bool
            Return as pd.DataFrame if True, else list of dicts.

        Returns:
        --------
        pd.DataFrame or list of dict
        """
        block = self._load_block(block_idx)
        if as_dataframe:
            return pd.DataFrame(block, columns=self.columns)
        return block

    def retrieve_rows(self, start, end):
        """
        Retrieve rows from start to end.

        Parameters:
        -----------
        start : int
        end : int

        Returns:
        --------
        pd.DataFrame : Rows in range [start, end)
        """
        rows = [self.retrieve_row(i) for i in range(start, end)]
        return pd.DataFrame(rows, columns=self.columns)

    # ------------------------------
    # Lazy DataFrame-like interface
    # ------------------------------
    @property
    def df(self):
        """Provides a lazy Pandas-like view of the dataset."""
        return self.LazyView(self)

    class LazyColumn:
        """Represents a lazy-access column for vectorized operations."""

        def __init__(self, store, column):
            self.store = store
            self.column = column

        def to_numpy(self, row_slice=None):
            """
            Return column data as NumPy array for specified row slice.

            Parameters:
            -----------
            row_slice : int, slice, or list/array, optional

            Returns:
            --------
            np.ndarray
            """
            if row_slice is None:
                row_slice = slice(0, len(self.store))
            if isinstance(row_slice, int):
                return np.array([self.store.retrieve_row(row_slice)[self.column]])
            elif isinstance(row_slice, slice):
                start, stop, step = row_slice.indices(len(self.store))
                data = [self.store.retrieve_row(i)[self.column] for i in range(start, stop, step)]
                return np.array(data)
            elif isinstance(row_slice, list) or isinstance(row_slice, np.ndarray):
                data = [self.store.retrieve_row(i)[self.column] for i in row_slice]
                return np.array(data)
            else:
                raise TypeError("Unsupported index type")

    class LazyView:
        """Provides lazy DataFrame-like access."""

        def __init__(self, store):
            self.store = store

        def __getitem__(self, col):
            """Return LazyColumn for a column."""
            if col not in self.store.columns:
                raise KeyError(f"Column {col} does not exist")
            return byteBars.LazyColumn(self.store, col)

        def iloc(self, row_slice):
            """Return rows according to integer-location-based slicing."""
            if isinstance(row_slice, int):
                return pd.DataFrame([self.store.retrieve_row(row_slice)], columns=self.store.columns)
            elif isinstance(row_slice, slice):
                start, stop, step = row_slice.indices(len(self.store))
                return self.store.retrieve_rows(start, stop).iloc[::step]
            elif isinstance(row_slice, list) or isinstance(row_slice, np.ndarray):
                rows = [self.store.retrieve_row(i) for i in row_slice]
                return pd.DataFrame(rows, columns=self.store.columns)
            else:
                raise TypeError("Unsupported index type for iloc")

        def head(self, n=5):
            """Return first n rows."""
            return self.iloc(slice(0, n))

        def tail(self, n=5):
            """Return last n rows."""
            return self.iloc(slice(len(self.store)-n, len(self.store)))

        def to_numpy(self, row_slice=None):
            """Return entire view as NumPy array."""
            df = self.iloc(row_slice if row_slice else slice(0, len(self.store)))
            return df.to_numpy()

    # ------------------------------
    # Utilities
    # ------------------------------
    def flush(self):
        """Flush pending rows to disk."""
        self._flush_block()

    def __len__(self):
        """Return total number of rows (including pending rows)."""
        total = sum(num for _, _, num in self.index)
        total += len(self.pending_block)
        return total
