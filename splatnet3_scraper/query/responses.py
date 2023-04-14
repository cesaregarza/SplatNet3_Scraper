from datetime import datetime
from typing import (
    Any,
    Callable,
    Iterator,
    Literal,
    TypeAlias,
    TypedDict,
    TypeVar,
    cast,
    overload,
)

from splatnet3_scraper.query.json_parser import JSONParser
from splatnet3_scraper.utils import match_partial_path

T = TypeVar("T")

PathType: TypeAlias = str | int | tuple[str | int, ...]


class MetaData(TypedDict, total=False):
    query: str
    timestamp: float


class QueryResponse:
    """The QueryResponse class represents a response from the SplatNet 3 API.
    The class provides various convenience methods for interacting with the
    returned data and contains metadata about the response. The metadata
    contains the query that was used to get the data and the timestamp of the
    response. Additional metadata may be added in the future. Using the getitem
    method on the response will return another QueryResponse with the data from
    the key. If the data is a list, the getitem method will generate a
    QueryResponse for each item in the list. The QueryResponse class also
    provides a parse_json method that returns a JSONParser object for the
    response data. This is currently not used by the library, so it may be
    removed in the future.
    """

    def __init__(
        self,
        data: dict[str, Any] | list[dict[str, Any]],
        metadata: dict[str, Any] | MetaData | None = None,
    ) -> None:
        """Initializes a QueryResponse.

        Args:
            data (dict[str, Any]): The data from the response as a dictionary.
                If the data is a list, the data should be a list of
                dictionaries. The data should be some sort of JSON object of
                nested dictionaries and lists.
            metadata (dict[str, Any] | None): The metadata from the response.
                Possible keys are "query" and "timestamp". Defaults to None.
        """
        self._data = data

        self._metadata = self.__parse_metadata(metadata)

    def __parse_metadata(
        self, metadata: dict[str, Any] | MetaData | None
    ) -> MetaData | None:
        """Parses the metadata from the response.

        Args:
            metadata (dict[str, Any] | MetaData | None): The metadata from the
                response.

        Returns:
            MetaData | None: The parsed metadata.
        """
        if metadata is None:
            return None

        annotations = MetaData.__annotations__
        _metadata = {}
        for key, value in metadata.items():
            if key in annotations:
                _metadata[key] = value
        if len(_metadata) == 0:
            return None
        return MetaData(_metadata)  # type: ignore

    def __top_level_is_list(self) -> bool:
        """Returns whether the top level of the data is a list. Internal use
        only.

        Returns:
            bool: Whether the top level is a list.
        """
        return isinstance(self._data, list)

    @property
    def data(self) -> dict[str, Any] | list[dict[str, Any]]:
        """The raw data from the response. This is the data that was passed to
        the QueryResponse at initialization.

        This property, as opposed to the ``__getitem__`` method, will return the
        raw data from the response without any parsing.

        Returns:
            dict[str, Any] | list[dict[str, Any]]: The raw data.
        """
        return self._data

    @property
    def metadata(self) -> MetaData:
        """The metadata from the response.

        Raises:
            ValueError: If no metadata was provided at initialization.

        Returns:
            MetaData: The metadata.
        """
        if self._metadata is None:
            raise ValueError("No metadata was provided.")
        return self._metadata

    @property
    def query(self) -> str:
        """The query that was used to get the data.

        Raises:
            ValueError: If no metadata was provided at initialization.

        Returns:
            str: The query.
        """
        if self._metadata is None:
            raise ValueError("No metadata was provided.")
        try:
            return self._metadata["query"]
        except KeyError:
            raise ValueError("No query was provided.")

    @property
    def timestamp_raw(self) -> float:
        """The timestamp of the response, as a float.

        Raises:
            ValueError: If no metadata was provided at initialization.

        Returns:
            float: The timestamp.
        """
        if self._metadata is None:
            raise ValueError("No metadata was provided.")
        try:
            return self._metadata["timestamp"]
        except KeyError:
            raise ValueError("No timestamp was provided.")

    @property
    def timestamp(self) -> datetime:
        """The timestamp of the response, as a datetime object.

        Returns:
            datetime: The timestamp.
        """
        return datetime.fromtimestamp(self.timestamp_raw)

    def parse_json(self) -> JSONParser:
        """The JSONParser object containing the data.

        Returns:
            JSONParser: The data.
        """
        return JSONParser(self._data)

    def __repr__(self) -> str:
        """Returns a string representation of the QueryResponse.

        Representation includes the metadata, if it exists. If the metadata
        exists, the representation will include the query and the timestamp.
        This method also iterates over the MetaData dictionary and adds it to
        the representation. This method should not need updating if new
        metadata fields are added.

        Returns:
            str: The string representation of the QueryResponse.
        """
        out_str = "QueryResponse("
        if self._metadata is None:
            return out_str + ")"

        spacing = " " * len(out_str)
        for key, value in self._metadata.items():
            # Intercept if key is "timestamp" and convert to datetime
            if key == "timestamp":
                value = cast(float, value)
                out_value = datetime.fromtimestamp(value).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            elif isinstance(value, str):
                out_value = value if len(value) < 20 else value[:20] + "..."
            elif isinstance(value, float):
                out_value = f"{value:.2f}"
            else:
                out_value = str(value)

            out_str += spacing + f"{key}={out_value},\n"

        return out_str[:-2] + ")"

    def __eq__(self, other: object) -> bool:
        """Returns whether the QueryResponse is equal to another object.

        Explicitly, this method checks whether the other object is a
        QueryResponse and whether the data and metadata are the same as the ones
        found in the QueryResponse.

        Args:
            other (object): The object to compare to.

        Returns:
            bool: Whether the QueryResponse is equal to the other object.
        """
        if not isinstance(other, QueryResponse):
            return False
        return self._data == other._data and self._metadata == other._metadata

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, key: PathType) -> "QueryResponse":
        """Returns a QueryResponse object containing the data at the given
        key. If the key is a tuple, this method will treat it as taking multiple
        keys in order to get to the data. For example, the following two are
        equivalent:

        >>> query_response["key1"]["key2"] == query_response["key1", "key2"]

        This method will then return a QueryResponse object containing the data
        at the given key.

        Args:
            key (PathType): The key to get the data

        Returns:
            QueryResponse: The QueryResponse object containing the data.
        """
        if isinstance(key, tuple):
            for k in key:
                self = self[k]
            return self

        data = self._data[key]  # type: ignore
        if isinstance(data, (dict, list)):
            return QueryResponse(data, metadata=self._metadata)
        return data

    def keys(self) -> list[str | int]:
        """Returns a list of keys in the data. If the top level of the data is
        a list, this method will return a list of integers from ``0`` to the
        length of the list.

        Returns:
            list[str | int]: The keys in the data.
        """
        if self.__top_level_is_list():
            return list(range(len(self)))
        data = cast(dict[str, Any], self._data)
        return list(data.keys())

    def values(self) -> list[Any]:
        """Returns a list of values in the data.

        Returns:
            list[Any]: The values in the data.
        """
        return list(self)

    def items(self) -> list[tuple[str, Any]]:
        """Returns a list of items in the data. If the top level of the data is
        a list, this method will return a list of integers from ``0`` to the
        length as the keys.

        Done to match the behavior of ``dict.items()``, which returns a list of
        tuples of the form ``(key, value)``. This method will return a list of
        tuples of the form ``(key, value)`` where the key can be an integer if
        the top level of the data is a list, otherwise it works the same as
        ``dict.items()``.

        Returns:
            list[tuple[str, Any]]: The items in the data.
        """
        if self.__top_level_is_list():
            return list(enumerate(self))  # type: ignore
        data = cast(dict[str, Any], self._data)
        return list(data.items())

    def __iter__(self) -> Iterator[Any]:
        """Returns an iterator over the values in the data.

        This method simply calls ``self.keys()`` and iterates over over
        ``self[key]`` for each key in the list of keys. This method is used to
        implement ``self.values()``.

        Yields:
            Iterator[Any]: The values in the data.
        """
        keys = self.keys()
        for key in keys:
            yield self[key]

    @overload
    def show(self, return_value: Literal[False]) -> None:
        ...

    @overload
    def show(self, return_value: Literal[True]) -> dict[str, Any]:
        ...

    def show(
        self, return_value: bool = False
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Prints the data to the console. If ``return_value`` is True, returns
        the data as a dict instead.

        Args:
            return_value (bool): Whether to return the data as a dict. If True,
                the data will be returned instead of printed. Defaults to False.

        Returns:
            dict[str, Any] | list[dict[str, Any]] | None: The data. If
                return_value is False, this will be None.
        """
        if return_value:
            return self._data
        print(self._data)
        return None

    def apply(
        self,
        func: Callable[[Any], T],
        key: PathType | list[PathType],
        partial: bool = True,
    ) -> T | list[T]:
        """Applies a function to the data.

        Given a function and a key to apply the function to, this method will
        apply the function to the data at the given key. If the key is a tuple,
        this method will treat it as a path. For example, a ``key`` argument of
        ``(0, "key1")`` will be treated as ``data[0]["key1"]``. If the key is
        a string, this method will treat it as a key in a dictionary. Integers
        will be treated as indices in a list. If the ``partial`` argument is
        ``True``, this method will apply the function to all keys in the data
        that match the given key or path. For example, if the ``key`` argument
        is ``(0, "key1")`` and the ``partial`` argument is ``True``, this will
        apply the function to all values within the JSON object where the path
        is ``...[0]["key1"]``. If the ``partial`` argument is ``False``, this
        will only apply the function to the value at the absolute key or path in
        the data.

        Args:
            func (Callable[[Any], QueryResponse]): The function to apply to the
                data. The function must take a single argument and return a
                QueryResponse object. The argument that the function takes will
                be representative of the value at the given key or path.
            key (PathType | list[PathType]): The key or path to apply the
                function to. If the key is a tuple, this method will treat it
                as a path. For example, a ``key`` argument of ``(0, "key1")``
                will be treated as ``data[0]["key1"]``. If the key is a string,
                this method will treat it as a key in a dictionary. Integers
                will be treated as indices in a list. If the ``partial``
                argument is ``True``, this method will treat a ``key``
                argument of ``(0, "key1")`` as ``...[0]["key1"]`` rather than
                just ``data[0]["key1"]``.
            partial (bool): Whether to apply the function to all keys in the
                data that match the given key or path. For example, if the
                ``key`` argument is ``(0, "key1")`` and the ``partial``
                argument is ``True``, this will apply the function to all values
                within the JSON object where the path is ``...[0]["key1"]``. If
                the ``partial`` argument is ``False``, this will only apply
                the function to the value at the absolute key or path in the
                data. Defaults to True.

        Returns:
            QueryResponse: The QueryResponse object containing the transformed
                data.
        """
        if not partial:
            if not isinstance(key, list):
                return func(self[key])
            out: list[T] = []
            for path in key:
                out.append(func(self[path]))

        paths = self.match_partial_path(key)
        return [func(self[path]) for path in paths]

    def match_partial_path(
        self, partial_path: PathType | list[PathType]
    ) -> list[tuple[str | int, ...]]:
        """Returns a list of all paths that match the given partial path. For
        example, if partial_path is ``(0, "key1")``, this will return all paths
        in the data that match ``...[0]["key1"]``.

        Given a partial path, this method will return a list of all paths in
        the data that match the given partial path. For example, if
        ``partial_path`` is ``(0, "key1")``, this will return all paths in the
        data that match ``...[0]["key1"]``. If the partial path is a string,
        this method will treat it as a key in a dictionary. Integers will be
        treated as indices in a list. If the partial path is a tuple, this
        method will treat it as a path. For example, a ``partial_path`` argument
        of ``(0, "key1")`` will be treated as ``...[0]["key1"]``.


        Args:
            partial_path (str | int | tuple[str | int, ...]): The partial path
                to match. If the partial path is a tuple, this method will treat
                it as a path. For example, a ``partial_path`` argument of ``(0,
                "key1")`` will be treated as ``...[0]["key1"]``. If the partial
                path is a string, this method will treat it as a key in a
                dictionary. Integers will be treated as indices in a list.

        Returns:
            list[tuple[str | int, ...]]: A list of all paths that match the
                given partial path.
        """
        return match_partial_path(self._data, partial_path)

    def get(self, key: PathType, default: Any = None) -> Any:
        """Returns the value at the given key. If the key is not found, returns
        the default value.

        This method is similar to ``self[key]`` except that it will not raise
        an error if the key is not found. Instead, it will return the default
        value. This method will still raise a type error if a string key is
        given and the key's level data is a list.

        Args:
            key (PathType): The key to get the value at. If the key is a tuple,
                this method will treat it as taking multiple keys in order to
                get to the data.
            default (Any): The default value to return if the key is not found.
                Defaults to None.

        Returns:
            Any: The value at the given key or the default value if the key is
                not found.
        """
        try:
            return self[key]
        except (KeyError, IndexError):
            return default
