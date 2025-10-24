from __future__ import annotations

# third-pary
import zarr
from zarr.storage import LocalStore, ZipStore
from zarr.codecs import BloscCodec, BloscShuffle, BloscCname
import numpy as np
# built-in
import re
import logging
from collections.abc import Sequence
from math import ceil
from datetime import datetime, date
import multiprocessing as mp
from concurrent.futures import as_completed, ThreadPoolExecutor, ProcessPoolExecutor
from typing import Callable, Iterable, Iterator, Any
import os, psutil, tempfile
from contextlib import contextmanager
from pathlib import Path
import warnings

# *----------------------------------------------------*
#                        GLOBALS
# *----------------------------------------------------*

_logger = logging.getLogger(__name__)

# *----------------------------------------------------*
#                        CLASSES
# *----------------------------------------------------*

class ArrayStorage:
    """A single-root-group Zarr v3 container with multiple arrays and metadata.

    This wraps a root Zarr **group** (backed by a LocalStore `<name>.zarr`
    or a read-only ZipStore `<name>.zip`). Each logical "block" is a Zarr
    array with shape ``(N, *item_shape)`` where axis 0 is append-only.
    Per-block metadata (chunk length, item shape, dtype) is kept in group attrs.
    """
    def __init__(self, pth: Path | str, mode: str) -> None:
        """Initialize the storage and ensure a root group exists.

        Args:
          pth: Base path. If it ends with ``.zip`` a read-only ZipStore is used;
            otherwise a LocalStore at ``<pth>.zarr`` is used.
          mode: Zarr open mode. For ZipStore this must be ``"r"``.
            For LocalStore, an existing store is opened with this mode; if
            missing, a new root group is created.

        Raises:
          ValueError: If `pth` type is invalid or ZipStore mode is not ``"r"``.
          FileNotFoundError: If a ZipStore was requested but the file is missing.
          TypeError: If the root object is an array instead of a group.
        """
        _logger.info("ArrayStorage init: pth=%s mode=%s", pth, mode)

        if not isinstance(pth, (str, Path)):
            _logger.error("Invalid 'pth' type: %s", type(pth))
            raise ValueError(f"Expected 'str' or 'Path' for 'pth'; got: {type(pth)}")

        p = Path(pth)
        self.mode = mode

        # store backend
        if p.suffix == ".zip":
            # ZipStore is read-only for safety (no overwrite semantics)
            self.store_path = p.resolve()
            _logger.info("Using ZipStore backend at %s", self.store_path)
            if mode != "r":
                _logger.error("Attempted to open ZipStore with non-read mode: %s", mode)
                raise ValueError("ZipStore must be opened read-only (mode='r').")
            if not self.store_path.exists():
                _logger.error("ZipStore path does not exist: %s", self.store_path)
                raise FileNotFoundError(f"No ZipStore at: {self.store_path}")
            self.store = ZipStore(self.store_path, mode="r")
        else:
            # local directory store at <pth>.zarr
            self.store_path = p.with_suffix(".zarr").resolve()
            _logger.info("Using LocalStore backend at %s", self.store_path)
            self.store = LocalStore(self.store_path)

        # open existing or create new root group
        try:
            # try to open the store
            _logger.info("Opening store at %s with mode=%s", self.store_path, mode)
            self.root = zarr.open(self.store, mode=mode)
            # the root must be a group. if it's not -- schema error then
            if not isinstance(self.root, zarr.Group):
                _logger.error("Root is not a group at %s", self.store_path)
                raise TypeError(f"Root at {self.store_path} must be a group.")
        except Exception:
            # if we can't open:
            # for ZipStore or read-only modes, we must not create, so re-raise
            if isinstance(self.store, ZipStore) or mode == "r":
                _logger.exception("Failed to open store in read-only context; re-raising")
                raise
            # otherwise, create a new group
            _logger.info("Creating new root group at %s", self.store_path)
            self.root = zarr.group(store=self.store, mode="a")

        # metadata attrs (JSON-safe)
        self._attrs = self.root.attrs
        self._attrs.setdefault("array_chunk_size_in_block", {})
        self._attrs.setdefault("array_shape_in_block", {})
        self._attrs.setdefault("array_dtype_in_block", {})
        _logger.debug("Metadata attrs initialized: keys=%s", list(self._attrs.keys()))

    def close(self) -> None:
        """Close the underlying store if it supports closing."""
        try:
            if hasattr(self, "store") and hasattr(self.store, "close"):
                self.store.close()
        except Exception as e:
            _logger.warning("Ignoring error while closing store: %s", e)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    # --------- PRIVATE ----------
        
    def _array_chunk_size_in_block(self, named: str, *, given: int | None) -> int:
        """Resolve per-block chunk length along axis 0; set default if unset."""
        apc = self._attrs["array_chunk_size_in_block"]
        cached = apc.get(named)
        if cached is None:
            if given is None:
                apc[named] = 10
                _logger.warning(
                    "array_chunk_size_in_block not provided for '%s'; defaulting to 10", named
                )
                warnings.warn(
                    f"You never set 'array_chunk_size_in_block' for block '{named}'. "
                    f"Defaulting to 10 — may be suboptimal for your RAM and array size.",
                    RuntimeWarning,
                    stacklevel=2,
                )
            else:
                if given <= 0:
                    _logger.error("Non-positive arrays_per_chunk for block '%s': %s", named, given)
                    raise ValueError("'array_chunk_size_in_block' must be positive")
                apc[named] = int(given)
            self._attrs["array_chunk_size_in_block"] = apc
            _logger.debug("Set arrays_per_chunk for '%s' to %s", named, apc[named])
            return apc[named]

        if given is None:
            return int(cached)

        if int(cached) != int(given):
            _logger.error(
                "array_chunk_size_in_block mismatch for '%s': cached=%s, given=%s",
                named, cached, given
            )
            raise RuntimeError(
                "The specified 'array_chunk_size_in_block' does not match the value used "
                f"when the block was initialized: {named}.array_chunk_size_in_block is {cached}, "
                f"but {given} was provided."
            )
        return int(cached)

    def _array_shape_in_block(self, named: str, *, given: tuple[int, ...]) -> tuple[int, ...]:
        """Resolve per-item shape for a block; enforce consistency if already set."""
        shp = self._attrs["array_shape_in_block"]
        cached = shp.get(named)
        if cached is None:
            shp[named] = list(map(int, given))
            self._attrs["array_shape_in_block"] = shp
            _logger.debug("Set shape for '%s' to %s", named, shp[named])
            return tuple(given)

        cached_t = tuple(int(x) for x in cached)
        if cached_t != tuple(given):
            _logger.error(
                "Shape mismatch for '%s': cached=%s, given=%s", named, cached_t, given
            )
            raise RuntimeError(
                "The specified 'array_shape_in_block' does not match the value used "
                f"when the block was initialized: {named}.array_shape_in_block is {cached_t}, "
                f"but {given} was provided."
            )
        return cached_t

    def _array_dtype_in_block(self, named: str, *, given: np.dtype) -> np.dtype:
        """Resolve dtype for a block; store/recover via dtype.str."""
        dty = self._attrs["array_dtype_in_block"]
        given = np.dtype(given)
        cached = dty.get(named)
        if cached is None:
            dty[named] = given.str
            self._attrs["array_dtype_in_block"] = dty
            _logger.debug("Set dtype for '%s' to %s", named, dty[named])
            return given

        cached_dt = np.dtype(cached)
        if cached_dt != given:
            _logger.error(
                "Dtype mismatch for '%s': cached=%s, given=%s", named, cached_dt, given
            )
            raise RuntimeError(
                "The specified 'array_dtype_in_block' does not match the value used "
                f"when the block was initialized: {named}.array_dtype_in_block is {cached_dt}, "
                f"but {given} was provided."
            )
        return cached_dt

    def _setdefault(
            self,
            named: str,
            shape: tuple[int, ...],
            dtype: np.dtype,
            arrays_per_chunk: int | None = None,
        ) -> zarr.Array:
        """Create or open the block array with the resolved metadata."""
        shape = self._array_shape_in_block(named, given=shape)
        dtype = self._array_dtype_in_block(named, given=dtype)
        apc   = self._array_chunk_size_in_block(named, given=arrays_per_chunk)

        # if it already exists, validate and return it
        if named in self.root:
            block = self.root[named]
            if not isinstance(block, zarr.Array):
                raise TypeError(f"Member '{named}' is not a Zarr array")
            if block.shape[1:] != shape:
                raise TypeError(f"Incompatible existing shape {block.shape} vs (0,{shape})")
            if np.dtype(block.dtype) != np.dtype(dtype):
                raise TypeError(f"Incompatible dtype {block.dtype} vs {dtype}")
            return block

        # otherwise, create the appendable array (length 0 along axis 0)
        _logger.debug("Creating array '%s' with shape=(0,%s), chunks=(%s,%s), dtype=%s",
                    named, shape, apc, shape, dtype)
        return self.root.create_array(
            name=named,
            shape=(0,) + shape,
            chunks=(int(apc),) + shape,
            dtype=dtype,
        )

    # --------- PUBLIC ----------

    def write(
        self,
        these_arrays: Sequence[np.ndarray] | np.ndarray,
        to_block_named: str,
        *,
        arrays_per_chunk: int | None = None,
    ) -> None:
        """Append arrays to a block.

        Appends a batch of arrays (all the same shape and dtype) to the Zarr array
        named `to_block_named`. The array grows along axis 0; chunk length is
        resolved per-block and stored in group attrs.

        Args:
        these_arrays: A sequence of NumPy arrays **or** a stacked ndarray with
            shape `(k, *item_shape)`. If a generic iterable is provided, it will be
            consumed into a list. All items must share the same shape and dtype.
        to_block_named: Name of the target block (array) inside the root group.
        arrays_per_chunk: Optional chunk length along axis 0. If unset and the
            block is new, defaults to 10 with a warning.

        Raises:
        RuntimeError: If the storage is opened read-only.
        ValueError: If any array's shape or dtype differs from the first element.
        """
        if self.mode == "r":
            _logger.error("Write attempted in read-only mode")
            raise RuntimeError("Cannot write to a read-only ArrayStorage")

        # Normalize to something indexable (list/tuple/ndarray)
        if not isinstance(these_arrays, (list, tuple, np.ndarray)):
            these_arrays = list(these_arrays)

        if len(these_arrays) == 0:
            _logger.info("write() called with empty input for block '%s'; no-op", to_block_named)
            return

        arr0 = np.asarray(these_arrays[0])
        _logger.info("Appending %d arrays to block '%s' (item_shape=%s, dtype=%s)",
                    len(these_arrays), to_block_named, arr0.shape, arr0.dtype)
        block = self._setdefault(
            to_block_named, tuple(arr0.shape), arr0.dtype, arrays_per_chunk
        )

        # quick validation
        for i, a in enumerate(these_arrays[1:], start=1):
            a = np.asarray(a)
            if a.shape != arr0.shape:
                _logger.error("Shape mismatch at index %d: %s != %s", i, a.shape, arr0.shape)
                raise ValueError(f"these_arrays[{i}] shape {a.shape} != {arr0.shape}")
            if np.dtype(a.dtype) != np.dtype(arr0.dtype):
                _logger.error("Dtype mismatch at index %d: %s != %s", i, a.dtype, arr0.dtype)
                raise ValueError(f"these_arrays[{i}] dtype {a.dtype} != {arr0.dtype}")

        data = np.asarray(these_arrays, dtype=block.dtype)
        k = data.shape[0]
        start = block.shape[0]
        block.resize((start + k,) + arr0.shape)
        block[start:start + k, ...] = data
        _logger.info("Appended %d rows to '%s'; new length=%d", k, to_block_named, block.shape[0])

    def read(
        self,
        from_block_named: str,
        ids: int | slice | tuple[int] = None):
        """Read rows from a block and return a NumPy array.

        Args:
          from_block_named: Name of the block (array) to read from.
          ids: Row indices to select along axis 0. May be one of:
            - ``None``: read the entire array;
            - ``int``: a single row;
            - ``slice``: a range of rows;
            - ``tuple[int]``: explicit row indices (order preserved).

        Returns:
          A NumPy array containing the selected data (a copy).

        Raises:
          KeyError: If the named block does not exist.
          TypeError: If the named member is not a Zarr array.
        """
        if from_block_named not in self.root:
            _logger.error("read(): block '%s' does not exist", from_block_named)
            raise KeyError(f"Block '{from_block_named}' does not exist")

        block = self.root[from_block_named]
        if not isinstance(block, zarr.Array):
            _logger.error("read(): member '%s' is not a Zarr array", from_block_named)
            raise TypeError(f"Member '{from_block_named}' is not a Zarr array")

        # log selection summary (type only to avoid huge logs)
        sel_type = type(ids).__name__ if ids is not None else "all"
        _logger.debug("Reading from '%s' with selection=%s", from_block_named, sel_type)

        if ids is None:
            out = block[:]
        elif isinstance(ids, (int, slice)):
            out = block[ids, ...]
        else:
            idx = np.asarray(ids, dtype=np.intp)
            out = block.get_orthogonal_selection((idx,) + (slice(None),) * (block.ndim - 1))

        return np.asarray(out, copy=True)

    def block_iter(
        self,
        from_block_named: str,
        *,
        step: int = 1) -> Iterator:
        """Iterate over a block in chunks along axis 0.

        Args:
          from_block_named: Name of the block (array) to iterate over.
          step: Number of rows per yielded chunk along axis 0.

        Yields:
          NumPy arrays of shape ``(m, *item_shape)`` where ``m <= step`` for the
          last chunk.

        Raises:
          KeyError: If the named block does not exist.
          TypeError: If the named member is not a Zarr array.
        """
        if from_block_named not in self.root:
            _logger.error("block_iter(): block '%s' does not exist", from_block_named)
            raise KeyError(f"Block '{from_block_named}' does not exist")

        block = self.root[from_block_named]
        if not isinstance(block, zarr.Array):
            _logger.error("block_iter(): member '%s' is not a Zarr array", from_block_named)
            raise TypeError(f"Member '{from_block_named}' is not a Zarr array")

        _logger.info("Iterating block '%s' with step=%d", from_block_named, step)

        if block.ndim == 0:
            # scalar array
            yield np.asarray(block[...], copy=True)
            return

        for i in range(0, block.shape[0], step):
            j = min(i + step, block.shape[0])
            out = block[i:j, ...]
            yield np.asarray(out, copy=True)

    def delete_block(self, named: str) -> None:
        """Delete a block and remove its metadata entries.

        Args:
          named: Block (array) name to delete.

        Raises:
          RuntimeError: If the storage is opened read-only.
          KeyError: If the block does not exist.
        """
        if self.mode == "r":
            _logger.error("delete_block() attempted in read-only mode")
            raise RuntimeError("Cannot delete blocks from a read-only ArrayStorage")

        if named not in self.root:
            _logger.error("delete_block(): block '%s' does not exist", named)
            raise KeyError(f"Block '{named}' does not exist")

        _logger.info("Deleting block '%s'", named)
        del self.root[named]
        
        for key in ("array_chunk_size_in_block", "array_shape_in_block", "array_dtype_in_block"):
            d = dict(self._attrs.get(key, {}))
            d.pop(named, None)
            self._attrs[key] = d
        _logger.debug("Removed metadata entries for '%s'", named)

    def add_attr(self, key: str, val: Any) -> None:
        """
        Attach JSON-serializable metadata to the root group's attributes.

        Coerces common non-JSON types into JSON-safe forms before writing to
        ``self.root.attrs``:
        * NumPy scalars → native Python scalars via ``.item()``
        * NumPy arrays → Python lists via ``.tolist()``
        * ``set``/``tuple`` → lists
        * ``datetime.datetime``/``datetime.date`` → ISO 8601 strings via ``.isoformat()``

        Args:
        key (str): Attribute name to set on the root group.
        val (Any): Value to store. If not JSON-serializable as provided, it will be
            coerced using the rules above. Large blobs should not be stored as attrs.

        Raises:
        RuntimeError: If the storage was opened in read-only mode (``mode == "r"``).
        TypeError: If the coerced value is still not JSON-serializable by Zarr.

        Examples:
        >>> store = ArrayStorage("/tmp/demo", mode="w")
        >>> store.add_attr("experiment", "run_3")
        >>> store.add_attr("created_at", datetime.utcnow())
        >>> store.add_attr("means", np.arange(3, dtype=np.float32))
        >>> store.get_attr["experiment"]
        'run_3'

        Note:
        If you distribute consolidated metadata, re-consolidate after changing attrs
        so external readers can see the updates.
        """
        if self.mode == "r":
            _logger.error("Write attempted in read-only mode")
            raise RuntimeError("Cannot write to a read-only ArrayStorage")

        # coerce to JSON-safe types Zarr accepts for attrs
        def _to_json_safe(x):
            if isinstance(x, np.generic):
                return x.item()
            if isinstance(x, np.ndarray):
                return x.tolist()
            if isinstance(x, (set, tuple)):
                return list(x)
            if isinstance(x, (datetime, date)):
                return x.isoformat()
            return x

        js_val = _to_json_safe(val)
        try:
            self.root.attrs[key] = js_val
            _logger.debug("Set root attr %r=%r", key, js_val)
        except TypeError as e:
            _logger.error("Value for attr %r is not JSON-serializable: %s", key, e)
            raise

    def get_attr(self, key: str):
        """Return a root attribute by key.

        Args:
            key: Attribute name.

        Returns:
            The stored value as-is (JSON-safe form, e.g., lists/ISO strings).

        Raises:
            KeyError: If the attribute does not exist.
        """
        try:
            val = self.root.attrs[key]
        except KeyError:
            _logger.error("get_attr: attribute %r not found", key)
            raise
        _logger.debug("get_attr: %r=%r", key, val)
        return val

    def compress(
        self,
        into: str | Path | None = None,
        *,
        compression_level: int,
    ) -> str:
        """Write a read-only ZipStore clone of the current store.

        Copies the single root group (its attrs and all child arrays with their
        attrs) into a new ``.zip`` file.

        Args:
        into: Optional destination. If a path ending with ``.zip``, that exact
            file is created/overwritten. If a directory, the zip is created there
            with ``<store>.zip``. If ``None``, uses ``<store>.zip`` next to the
            local store.
        compression_level: Blosc compression level to use for data chunks
            (integer, 0-9). ``0`` disables compression (still writes with a Blosc
            container); higher = more compression, slower writes.

        Returns:
        Path to the created ZipStore as a string.

        Notes:
        * If the backend is already a ZipStore, this is a no-op (path returned).
        * For Zarr v3, compressors are part of the *codecs pipeline*. Here we set
            a single compressor (Blosc with Zstd) and rely on defaults for the
            serializer; that's valid and interoperable. 
        """
        if isinstance(self.store, ZipStore):
            _logger.info("compress(): already a ZipStore; returning current path")
            return str(self.store_path)

        # --- destination path resolution ---
        if into is None:
            zip_path = self.store_path.with_suffix(".zip")
        else:
            into = Path(into)
            if into.suffix.lower() == ".zip":
                zip_path = into.resolve()
            else:
                zip_path = (into / self.store_path.with_suffix(".zip").name).resolve()
            zip_path.parent.mkdir(parents=True, exist_ok=True)

        # --- compression level checks & logs ---
        try:
            clevel = int(compression_level)
        except Exception as e:
            _logger.error("Invalid compression_level=%r (%s)", compression_level, e)
            raise

        if not (0 <= clevel <= 9):
            _logger.error("compression_level out of range: %r (expected 0..9)", clevel)
            raise ValueError("compression_level must be in the range [0, 9]")

        if clevel == 0:
            _logger.warning("Compression disabled: compression_level=0")

        _logger.info("Compressing store to ZipStore at %s with Blosc(zstd, clevel=%d, shuffle=shuffle)",
                    zip_path, clevel)

        def _attrs_dict(attrs):
            try:
                return attrs.asdict()
            except Exception:
                return dict(attrs)

        with ZipStore(zip_path, mode="w") as z:
            dst_root = zarr.group(store=z)

            dst_root.attrs.update(_attrs_dict(self.root.attrs))

            copied = 0
            for key, src in self.root.arrays():

                dst = dst_root.create_array(
                    name=key,
                    shape=src.shape,
                    chunks=src.chunks,
                    dtype=src.dtype,
                    compressors=BloscCodec(
                        cname=BloscCname.zstd,
                        clevel=clevel,
                        shuffle=BloscShuffle.shuffle,
                    )
                )

                dst.attrs.update(_attrs_dict(src.attrs))
                dst[...] = src[...]
                copied += 1
                _logger.debug("Compressed array '%s' shape=%s dtype=%s", key, src.shape, src.dtype)

        _logger.info("Compression complete: %d arrays -> %s", copied, zip_path)
        return str(zip_path)
    
    @classmethod
    @contextmanager
    def compress_and_cleanup(cls, output_pth: str | Path, compression_level: int) -> Iterator[ArrayStorage]:
        """
        Create a temporary ArrayStorage, yield it for writes, then compress it into `output_pth`.
        The temporary local store is deleted after compression.

        Args:
            output_pth: Destination .zip file or directory (delegated to `compress(into=...)`).
            compression_level: Blosc compression level to use for data chunks
                (integer, 0-9). ``0`` disables compression (still writes with a Blosc
                container); higher = more compression, slower writes.
        """
        output_pth = Path(output_pth)
        _logger.info("compress_and_cleanup: creating temp store (suffix .zarr)")
        with tempfile.TemporaryDirectory(suffix=".zarr") as tmp_dir:
            arr_storage = cls(tmp_dir, mode="w")
            try:
                yield arr_storage
            finally:
                _logger.info("compress_and_cleanup: compressing to %s (compression level of %d)", output_pth, compression_level)
                arr_storage.compress(output_pth, compression_level=compression_level)
                arr_storage.close()
        _logger.info("compress_and_cleanup: temp store cleaned up")

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= #
#  PARALLEL PROCESSING AND EFFICIENT MEMORY USAGE RELATED FUNCTIONS
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= #

def is_main_process() -> bool:
    p = mp.current_process()
    return mp.parent_process() is None and p.name == "MainProcess"

def _apply(f: Callable, x: Any, extra_args: tuple, extra_kwargs: dict) -> Any:
    return f(x, *extra_args, **extra_kwargs)

def elementwise_processor(
    in_parallel: bool = False,
    Executor: type[ThreadPoolExecutor] | type[ProcessPoolExecutor] | None = None,
    max_workers: int | None = None,
    capture_output: bool = True,
) -> Callable[[Iterable[Any], Callable[..., Any], Any], list[Any] | None]:
    """Factory that returns a function to process an iterable elementwise.

    The returned callable executes a provided `function` over each element of an
    `iterable`, either sequentially or in parallel using the specified
    `Executor`. Results are optionally captured and returned as a list.

    Args:
        in_parallel: If True, process with a concurrent executor; otherwise run sequentially.
        Executor: Executor class to use when `in_parallel` is True
            (e.g., `ThreadPoolExecutor` or `ProcessPoolExecutor`). Ignored if `in_parallel` is False.
        max_workers: Maximum parallel workers. Defaults to `os.cpu_count()` when None.
        capture_output: If True, collect and return results; if False, execute for side effects and return None.

    Returns:
        A callable with signature:
            `(iterable, function, *extra_args, **extra_kwargs) -> list | None`
        When `capture_output` is True, the list preserves the input order.

    Raises:
        ValueError: If `in_parallel` is True and `Executor` is None.
        Exception: Any exception raised by `function` for a given element is propagated.

    Notes:
        - In parallel mode, task results are re-ordered to match input order.
        - In non-capturing modes, tasks are still awaited so exceptions surface.

    Example:
        >>> runner = elementwise_processor(in_parallel=True, Executor=ThreadPoolExecutor, max_workers=4)
        >>> out = runner(range(5), lambda x: x * 2)
        >>> out
        [0, 2, 4, 6, 8]
    """
    def inner(iterable: Iterable[Any], function: Callable, *extra_args: Any, **extra_kwargs: Any) -> list[Any] | None:
        """Execute `function` over `iterable` per the configuration of the factory.

        Args:
            iterable: Collection of input elements to process.
            function: Callable applied to each element of `iterable`.
            *extra_args: Extra positional arguments forwarded to `function`.
            **extra_kwargs: Extra keyword arguments forwarded to `function`.

        Returns:
            List of results when `capture_output` is True; otherwise None.

        Raises:
            ValueError: If `Executor` is missing while `in_parallel` is True.
            Exception: Any exception raised by `function` is propagated.
        """
        _logger.debug(
            "elementwise_processor: in_parallel=%s, Executor=%s, max_workers=%s, capture_output=%s, func=%s",
            in_parallel, getattr(Executor, "__name__", None), max_workers, capture_output, getattr(function, "__name__", repr(function))
        )

        if not in_parallel:
            _logger.info("elementwise_processor: running sequentially")
            if capture_output:
                result = [function(x, *extra_args, **extra_kwargs) for x in iterable]
                _logger.info("elementwise_processor: sequential completed with %d results", len(result))
                return result
            else:
                for x in iterable:
                    function(x, *extra_args, **extra_kwargs)
                _logger.info("elementwise_processor: sequential completed (no capture)")
                return None

        if Executor is None:
            _logger.error("elementwise_processor: Executor is required when in_parallel=True")
            raise ValueError("An 'Executor' argument must be provided if 'in_parallel' is True.")

        local_max_workers = max_workers or (os.cpu_count() or 1)
        _logger.info("elementwise_processor: starting parallel with %d workers via %s", local_max_workers, Executor.__name__)
        with Executor(max_workers=local_max_workers) as executor:
            futures = {executor.submit(_apply, function, x, extra_args, extra_kwargs): i
                       for i, x in enumerate(iterable)}
            _logger.info("elementwise_processor: submitted %d tasks", len(futures))
            if capture_output:
                results: list[Any] = [None] * len(futures)
                for fut in as_completed(futures):
                    idx = futures[fut]
                    try:
                        results[idx] = fut.result()
                    except Exception:
                        _logger.exception("elementwise_processor: task %d raised", idx)
                        raise
                _logger.info("elementwise_processor: parallel completed with %d results", len(results))
                return results
            else:
                for fut in as_completed(futures):
                    try:
                        fut.result()
                    except Exception:
                        _logger.exception("elementwise_processor: task %d raised", futures[fut])
                        raise
                _logger.info("elementwise_processor: parallel completed (no capture)")
                return None

    return inner

def files_from(dir_path: str, pattern: re.Pattern = None) -> list[str]:
    """List files in a directory matching a regex pattern.

    Args:
        dir_path: Path to the directory to scan.
        pattern: Compiled regex pattern to match file names. If None, matches all files.

    Returns:
        A sorted list of absolute (string) file paths present in `dir_path` that match `pattern`.

    Notes:
        - Only regular files are returned; directories are ignored.
        - Raises `FileNotFoundError`/`PermissionError` if `dir_path` is invalid/inaccessible.
    """
    pat = pattern or re.compile(r".*")
    dp = Path(dir_path)
    _logger.debug("files_from: scanning %s with pattern=%r", dp, pat.pattern if hasattr(pat, "pattern") else pat)
    files = list()
    for file_name in sorted(os.listdir(dir_path)):
        pth = dp / file_name
        if pat.match(file_name) and pth.is_file():
            files.append(str(pth))
    _logger.debug("files_from: matched %d files in %s", len(files), dp)
    return files

def file_chunks_generator(file_path: str, chunk_size: int, skip_header: bool = True) -> Iterable[list[str]]:
    """Yield lists of text lines from a file using a size-hint per chunk.

    Uses `io.TextIOBase.readlines(sizehint)` to read approximately `chunk_size`
    bytes per iteration, always ending on a line boundary.

    Args:
        file_path: UTF-8 encoded text file to read.
        chunk_size: Approximate number of bytes to read per chunk (size hint).
        skip_header: If True, skip the first line before yielding content.

    Yields:
        Lists of strings, each list containing complete lines.

    Notes:
        - The `sizehint` is approximate; chunks may be larger or smaller.
        - If `skip_header` is True and the file is empty, the generator returns immediately.
    """
    _logger.info("file_chunks_generator: file=%s chunk_size=%d skip_header=%s", file_path, chunk_size, skip_header)
    with open(file_path, "r", encoding="utf-8") as file:
        if skip_header:
            try:
                next(file)
                _logger.debug("file_chunks_generator: skipped header line")
            except StopIteration:
                _logger.info("file_chunks_generator: file empty after header skip")
                return
        while True:
            chunk = file.readlines(chunk_size)
            if not chunk:
                break
            yield chunk
    _logger.debug("file_chunks_generator: completed for %s", file_path)

def chunked_file(file_path: str, allowed_memory_percentage_hint: float, num_workers: int) -> Iterable[list[str]]:
    """Split a file into line chunks sized by per-worker memory allowance.

    Heuristically plans chunk sizes from available system memory and the
    declared number of workers, then yields line lists produced by
    `file_chunks_generator`.

    Args:
        file_path: Path to a UTF-8 text file.
        allowed_memory_percentage_hint: Fraction in (0, 1] of *available* RAM to budget in total,
            divided across workers.
        num_workers: Number of workers the chunks are intended for.

    Yields:
        Lists of strings representing line chunks of the file.

    Raises:
        ValueError: If `allowed_memory_percentage_hint` not in (0, 1] or `num_workers` < 1.

    Notes:
        - This is a heuristic: Python string overhead and decoding expand beyond raw bytes.
        - If the whole file fits within `memory_per_worker`, a single chunk is yielded.
    """
    if not (0 < allowed_memory_percentage_hint <= 1.0):
        _logger.error("chunked_file: invalid allowed_memory_percentage_hint=%s", allowed_memory_percentage_hint)
        raise ValueError(f"Invalid allowed_memory_percentage_hint parameter: expected a value between 0 and 1, instead got: {allowed_memory_percentage_hint}")
    
    if num_workers < 1:
        _logger.error("chunked_file: num_workers must be >= 1 (got %s)", num_workers)
        raise ValueError("num_workers must be at least 1")

    memory_per_worker = max(1, int((allowed_memory_percentage_hint * psutil.virtual_memory().available) / num_workers))
    file_size = os.path.getsize(file_path)
    _logger.info("chunked_file: file_size=%d bytes, memory_per_worker=%d bytes", file_size, memory_per_worker)

    if file_size <= memory_per_worker:
        _logger.info("chunked_file: file fits in memory per worker; yielding all lines")
        yield read_lines(file_path)
        return

    num_chunks = max(1, ceil(file_size / memory_per_worker))
    chunk_size = max(1, file_size // num_chunks)
    _logger.info("chunked_file: planning %d chunks (~%d bytes each)", num_chunks, chunk_size)

    yield from file_chunks_generator(file_path, chunk_size)

def dir_chunks_generator(file_paths: list[str], files_per_chunk: int, residual_files: int):
    """Yield lists of file paths partitioned by a base chunk size and residuals.

    Distributes `residual_files` by giving the first `residual_files` chunks one
    extra file each.

    Args:
        file_paths: Full list of file paths to chunk.
        files_per_chunk: Base number of files to include in each chunk (>= 0).
        residual_files: Number of initial chunks that should receive one additional file.

    Yields:
        Slices (lists) of `file_paths` representing each chunk.

    Notes:
        - If `files_per_chunk <= 0`, all files are yielded as a single chunk.
        - The final tail (if any) is yielded after full chunks.
    """
    total_files = len(file_paths)
    _logger.debug("dir_chunks_generator: total_files=%d, files_per_chunk=%d, residual_files=%d",
                  total_files, files_per_chunk, residual_files)
    
    if files_per_chunk <= 0:
        _logger.info("dir_chunks_generator: files_per_chunk<=0 → yielding all %d files at once", total_files)
        yield file_paths
        return
    
    num_chunks = (total_files - residual_files) // files_per_chunk
    _logger.debug("dir_chunks_generator: full_chunks=%d", num_chunks)
    
    start = 0
    for i in range(num_chunks):
        chunk_size = files_per_chunk + 1 if i < residual_files else files_per_chunk
        yield file_paths[start:start + chunk_size]
        start += chunk_size

    if start < total_files:
        _logger.debug("dir_chunks_generator: yielding tail chunk of %d files", total_files - start)
        yield file_paths[start:]

def chunked_dir(dir_path: str, allowed_memory_percentage_hint: float, num_workers: int):
    """Plan directory file chunks to fit a per-worker memory hint.

    Assumes files in `dir_path` are of similar size (uses the first file as a
    representative) to estimate how many files can be processed per worker.
    Yields lists of file paths sized accordingly.

    Args:
        dir_path: Directory containing the files to chunk.
        allowed_memory_percentage_hint: Fraction in (0, 1] of available RAM to allocate across workers.
        num_workers: Number of workers that will process the chunks.

    Yields:
        Lists of file paths sized for concurrent processing.

    Raises:
        ValueError: If inputs are invalid or the directory is empty.
        MemoryError: If a single file is too large for the per-worker memory allowance.

    Notes:
        - If the first file is empty, a 1-byte surrogate is used to avoid division by zero.
        - Actual memory usage depends on file content and processing overhead.
    """
    if not (0 < allowed_memory_percentage_hint <= 1.0):
        _logger.error("chunked_dir: invalid allowed_memory_percentage_hint=%s", allowed_memory_percentage_hint)
        raise ValueError(f"Invalid allowed_memory_percentage_hint parameter: expected a value between 0 and 1, instead got: {allowed_memory_percentage_hint}")
    if num_workers < 1:
        _logger.error("chunked_dir: num_workers must be >= 1 (got %s)", num_workers)
        raise ValueError("num_workers must be at least 1")
    
    memory_per_worker = max(1, int((psutil.virtual_memory().available * allowed_memory_percentage_hint) / num_workers))
    _logger.info("chunked_dir: memory_per_worker=%d bytes (hint=%s, workers=%d)", memory_per_worker, allowed_memory_percentage_hint, num_workers)

    file_paths = files_from(dir_path)
    if not file_paths:
        _logger.error("chunked_dir: no files found in directory %s", dir_path)
        raise ValueError(f"No files found in directory: {dir_path}")

    file_size = os.path.getsize(file_paths[0])
    if file_size == 0:
        _logger.warning("chunked_dir: first file is zero bytes; falling back to 1 byte for sizing")
        file_size = 1

    files_per_worker = int(memory_per_worker // file_size)
    _logger.info("chunked_dir: representative_file_size=%d bytes -> files_per_worker=%d", file_size, files_per_worker)

    if files_per_worker < 1:
        _logger.error("chunked_dir: files too large for current memory hint per worker")
        raise MemoryError(
            f"The files contained in {dir_path} are too large. Cannot distribute the files across the workers. "
            "Solution: increase 'allowed_memory_percentage_hint', if possible, or decrease 'num_workers'"
        )

    num_files = len(file_paths)
    files_per_chunk = files_per_worker
    residual_files = num_files % files_per_chunk
    _logger.info("chunked_dir: num_files=%d -> files_per_chunk=%d, residual_files=%d", num_files, files_per_chunk, residual_files)

    yield from dir_chunks_generator(file_paths, files_per_chunk, residual_files)

def read_lines(file_path: str, skip_header: bool = True) -> list[str]:
    """Read all lines from a UTF-8 text file, optionally skipping the header.

    Args:
        file_path: Path to the input file.
        skip_header: If True, omit the first line from the returned list.

    Returns:
        A list of lines (strings). If `skip_header` is True and the file is
        non-empty, the first line is excluded.

    Notes:
        - Uses `readlines()`; for gigantic files prefer streaming approaches.
    """
    _logger.debug("read_lines: reading %s (skip_header=%s)", file_path, skip_header)
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
        _logger.debug("read_lines: read %d lines from %s", len(lines), file_path)
        return lines[1:] if (skip_header and lines) else lines

def temporary_file(prefix: str, suffix: str) -> Path:
    """Create a named temporary file and return its path.

    This helper creates a `NamedTemporaryFile`, closes it immediately, and
    returns its filesystem path so other processes can open/write it later.
    The caller is responsible for deleting the file when finished.

    Args:
      prefix: Filename prefix used when creating the temporary file.
      suffix: Filename suffix (e.g., extension) used when creating the file.

    Returns:
      Path: Filesystem path to the created temporary file.

    Notes:
      The file is created on the default temporary directory for the system.
      The file handle is closed before returning, so only the path is kept.
    """
    ntf = tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix, delete=False)
    ntf.close()
    return Path(ntf.name)

def batches_of(iterable: Iterable,
               batch_size: int = -1,
               *,
               out_as: type = list,
               ranges: bool = False,
               inclusive_end: bool = False):
    """Yield elements of `iterable` in fixed-size batches or index ranges.

    Works with any iterable (lists, ranges, generators, file objects, etc.).
    For sliceable sequences, a fast path uses len()+slicing; for general
    iterables, items are accumulated into chunks.

    When `ranges=True`, yields 0-based index ranges based on consumption
    order: `(start, end_exclusive)` (or `(start, end_inclusive)` if
    `inclusive_end=True`) without materializing the data.

    Args:
      iterable: Any iterable to batch (sequence or generator).
      batch_size: Number of items per batch. If <= 0, the entire iterable is
        yielded as a single batch. Defaults to -1.
      out_as: Constructor to wrap each yielded batch (e.g., `list`, `tuple`)
        or to wrap the index pair when `ranges=True`. Defaults to `list`.
      ranges: If True, yield index ranges instead of data batches. Defaults to False.
      inclusive_end: If `ranges=True`, return an inclusive end index instead of
        exclusive. Ignored when `ranges=False`. Defaults to False.

    Yields:
      For `ranges=False`: a batch containing up to `batch_size` elements,
        wrapped with `out_as`.
      For `ranges=True`: an index pair `(start, end_exclusive)` (or inclusive)
        wrapped with `out_as`.

    Examples:
      >>> list(batches_of([1,2,3,4,5], batch_size=2))
      [[1, 2], [3, 4], [5]]

      >>> list(batches_of(range(10), batch_size=4, ranges=True))
      [(0, 4), (4, 8), (8, 10)]

      >>> gen = (i*i for i in range(7))
      >>> list(batches_of(gen, batch_size=3, out_as=tuple))
      [(0, 1, 4), (9, 16, 25), (36,)]
    """
    # try fast path for sliceable sequences (len + slicing)
    try:
        n = len(iterable)  # may raise TypeError for generators
        _ = iterable[0:0]  # cheap probe for slicing support
        is_sliceable = True
    except Exception:
        n = None
        is_sliceable = False

    if is_sliceable:
        if batch_size <= 0:
            batch_size = n
        for start in range(0, n, batch_size):
            end_excl = min(start + batch_size, n)
            if ranges:
                yield out_as((start, end_excl - 1)) if inclusive_end else out_as((start, end_excl))
            else:
                yield out_as(iterable[start:end_excl])
        return

    # generic-iterable path (generators, iterators, file objects, etc.)
    it = iter(iterable)

    if batch_size <= 0:
        # consume everything into a single batch
        chunk = list(it)
        if ranges:
            end_excl = len(chunk)
            yield out_as((0, end_excl - 1)) if inclusive_end else out_as((0, end_excl))
        else:
            yield out_as(chunk)
        return

    start_idx = 0
    while True:
        chunk = []
        try:
            for _ in range(batch_size):
                chunk.append(next(it))
        except StopIteration:
            pass

        if not chunk:
            break

        if ranges:
            end_excl = start_idx + len(chunk)
            yield out_as((start_idx, end_excl - 1)) if inclusive_end else out_as((start_idx, end_excl))
        else:
            yield out_as(chunk)

        start_idx += len(chunk)

def create_updated_subprocess_env(**var_vals: Any) -> dict[str, str]:
    """Return a copy of the current environment with specified overrides.

    Convenience helper for preparing an `env` dict to pass to `subprocess.run`.
    Values are converted to strings; booleans map to ``"TRUE"``/``"FALSE"``.
    If a value is `None`, the variable is removed from the child environment.
    Path-like values are converted via `os.fspath`.

    Args:
      **var_vals: Mapping of environment variable names to desired values.
        - `None`: remove the variable from the environment.
        - `bool`: stored as `"TRUE"` or `"FALSE"`.
        - `int`, `str`, path-like: converted to `str` (path-like via `os.fspath`).

    Returns:
      dict[str, str]: A new environment dictionary suitable for `subprocess.run`.

    Examples:
      >>> env = create_updated_subprocess_env(OMP_NUM_THREADS=1, MKL_DYNAMIC=False)
      >>> env["OMP_NUM_THREADS"]
      '1'
      >>> env["MKL_DYNAMIC"]
      'FALSE'
    """
    env: dict[str, str] = os.environ.copy()
    for var, val in var_vals.items():
        if val is None:
            env.pop(var, None)
        elif isinstance(val, bool):
            env[var] = "TRUE" if val else "FALSE"
        else:
            env[var] = os.fspath(val) if hasattr(val, "__fspath__") else str(val)
    return env

def current_time() -> str:
    """Returns the current time in the Y-%m-%d_%H%M%S format"""
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")

def compose_steps(
    *steps: tuple[
            Callable[..., Any], dict[str, Any] | None
        ]
) -> Callable[[Any], Any]:
    """Compose a pipeline from an ordered sequence of (function, kwargs) pairs.

    This helper returns a unary function that feeds an input value through each
    step you provide, in the exact order the steps appear in the argument list.
    Each step is a 2-tuple ``(func, kwargs)``; the composed function will call
    ``func(current, **(kwargs or {}))``, where *current* is the running value,
    and use the return value as the next *current*.

    Args:
        *steps: Variable-length sequence of pairs ``(callable, kwargs_dict_or_None)``.
            - Each callable must accept at least one positional argument
              (the current value) plus any keyword arguments supplied.
            - ``kwargs`` may be ``None`` to indicate no keyword arguments.
            - The order of steps determines execution order.

    Returns:
        Callable[[Any], Any]: A function ``g(x)`` that applies all steps to ``x``
        and returns the final result.

    Raises:
        TypeError: If any element of ``steps`` is not a 2-tuple of
            ``(callable, dict_or_None)``.
        Any exception raised by an individual step is propagated unchanged.

    Notes:
        - If a step mutates its input and returns ``None``, the next step will
          receive ``None``. Ensure each step returns the value you want to pass on.
        - ``kwargs`` is shallow-copied (via ``dict(kwargs)``) before each call so a
          callee cannot mutate the original mapping.

    Examples:
        >>> def scale(a, *, c): return a * c
        >>> def shift(a, *, b): return a + b
        >>> pipeline = compose_steps((scale, {'c': 2}), (shift, {'b': 3}))
        >>> pipeline(10)
        23
    """
    # validation
    for i, pair in enumerate(steps):
        if not (isinstance(pair, tuple) and len(pair) == 2 and callable(pair[0])):
            raise TypeError(
                f"steps[{i}] must be a (callable, kwargs_dict_or_None) pair; got: {pair!r}"
            )

    def inner(x: Any) -> Any:
        for func, kwargs in steps:
            x = func(x, **({} if kwargs is None else dict(kwargs)))
        return x

    return inner


__all__ = [
    "ArrayStorage",
    "elementwise_processor",
    "files_from",
    "chunked_file", # <-- legacy
    "chunked_dir",  # <-- legacy
    "batches_of",
    "compose_steps"
]

if __name__ == "__main__":
    pass
