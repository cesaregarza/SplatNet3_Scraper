import json
import os
from dataclasses import is_dataclass
from pathlib import Path
from typing import Any, Callable, Type
from warnings import warn


class SecondaryException(Exception):
    pass


class JSONDataClass:
    """Base class for all dataclasses. This class provides the following
    functionality:
    - Recursively initialize dataclasses from dictionaries.
    - Print the object tree in a human readable format.
    - Enable numpy style indexing, e.g. obj["key1", "key2"].
    - Index all the ids in the object tree.
    - Get the top level keys of the object tree.
    - Provide a method to apply a function to all the objects in the object.
    """

    def __post_init__(self) -> None:
        """After initializing the dataclass, check if any of the fields are
        dictionaries. If so, initialize the corresponding annotation with the
        dictionary as the argument.

        Raises:
            SecondaryException: If the key of the dictionary is not found in the
                result of the get_annotations() method.
            Exception: SecondaryExceptions get passed up the chain.
        """
        # This class should be used as a base class for all dataclasses
        for key, value in self.__dict__.items():

            try:
                if isinstance(value, dict):
                    annotations = self.get_annotations()
                    cls = annotations[key]
                    # This is a hack to get around the fact that there is a key
                    # in the JSON that has a double underscore prefix. Since
                    # double underscore triggers name mangling,
                    # we circumvent that by using a single underscore prefix in
                    # dataclass definition instead, and then replacing the
                    # double underscore with a single underscore here.
                    value = {k.replace("__", "_"): v for k, v in value.items()}
                    setattr(self, key, cls(**value))
                elif (
                    isinstance(value, list)
                    and (len(value) > 0)
                    and isinstance(value[0], dict)
                ):
                    annotations = self.get_annotations()
                    super_cls = annotations[key]
                    # Try/except block to catch the case where the list is
                    # empty.
                    try:
                        cls = super_cls.__args__[0]
                    except AttributeError:
                        setattr(self, key, [])
                        continue
                    # Replace double underscores with single underscores for
                    # the same reason as above.
                    attrset = [
                        cls(
                            **{k.replace("__", "_"): v for k, v in item.items()}
                        )
                        for item in value
                    ]
                    setattr(self, key, attrset)
            except Exception as e:
                if not isinstance(e, SecondaryException):
                    raise SecondaryException from e
                else:
                    raise e

    @classmethod
    def get_annotations(cls) -> dict[str, Type[Any]]:
        """Get the annotations of the class, but also include the annotations
        of any ancestor classes.

        Returns:
            dict[str, type]: A dictionary of the annotations of the class and
                the annotations of any ancestor classes.
        """
        annotations: dict[str, Any] = {}
        for c in cls.mro():
            try:
                annotations.update(**c.__annotations__)
            except AttributeError:
                pass
        return annotations

    def __repr__(self, level=1) -> str:
        """Print the object tree in a human readable format.

        Args:
            level (int, optional): The level of the object tree. Defaults to 1.

        Returns:
            str: The object tree in a human readable format.
        """
        out = self.__class__.__name__ + ":\n" if level == 1 else ""
        tabs = " " * level

        for key, value in self.__dict__.items():
            if isinstance(value, JSONDataClass):
                out += f"{tabs}{key}:\n" + value.__repr__(level + 1)
            elif isinstance(value, list):
                if len(value) == 0:
                    out += f"{tabs}{key}: list[]\n"
                    continue
                idx = 1 if len(value) > 1 else 0
                out += (
                    tabs
                    + f"{key}: "
                    + f"list[{value[idx].__class__.__name__}]\n"
                )
                # Assume all items in the list are of the same type
                try:
                    out += value[idx].__repr__(level + 1)
                except TypeError:
                    # If list contains None, then the above will fail.
                    out += tabs + "  " + value[idx].__repr__() + "\n"
            else:
                out += tabs + f"{key}: {type(value).__name__}\n"
        return out

    def __getitem__(
        self, key: str | int | slice | tuple[str | int, ...]
    ) -> Any:
        """Get the value of the given key. If the key is a tuple, then enable
        numpy style indexing.

        Args:
            key (str | tuple[str  |  int]): The key to get the value of.

        Raises:
            IndexError: If the key is an integer or slice and there is more than
                one item in the object tree.

        Returns:
            Any: The value of the given key.
        """
        if isinstance(key, str):
            return getattr(self, key)
        elif isinstance(key, (int, slice)):
            top_level_keys = self.top_level_keys()
            if len(top_level_keys) > 1:
                raise IndexError(
                    "Cannot index with an integer or slice if there are "
                    "multiple top level keys."
                )
            return getattr(self, top_level_keys[0])[key]

        # If the key is a tuple, recursively call __getitem__ on the
        # corresponding attribute.
        curent_level = self
        for k in key:
            curent_level = curent_level[k]

        return curent_level

    def __index_ids(self) -> dict[str, Any]:
        """Index all the ids in the object tree. This is used to get the
        corresponding object from the id.

        Returns:
            dict[str, Any]: A dictionary of all the ids in the object tree.
        """
        id_index: dict[str, Any] = {}
        for key, value in self.__dict__.items():
            if isinstance(value, JSONDataClass):
                id_index.update(**value.__index_ids())
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, JSONDataClass):
                        id_index.update(**item.__index_ids())
            elif key == "id":
                id_index[str(value)] = self
        return id_index

    def search_by_id(self, id: int | str) -> Any:
        """Search the object tree for the object with the given id. Indexing is
        done on the first call to this method, and then the generated index is
        used for subsequent calls.

        Args:
            id (str): The id of the object to search for. If fed an integer,
                it will be converted to a string.

        Returns:
            Any: The object with the given id.
        """
        if getattr(self, "__id_index", None) is None:
            self.__id_index = self.__index_ids()
        return self.__id_index[str(id)]

    def traverse_tree(
        self, func: Callable[[Any, str], Any], prune_none: bool = False
    ) -> dict:
        """Traverse the object tree and apply the given function to each object.

        Args:
            func (Callable[[Any], Any]): The function to apply to each object.
                First attempts to call the function with the object and the key
                as arguments. If this fails, then it will call the function on
                just the object.
            prune_none (bool): If True, then prune the branches where the
                function returns None. Defaults to False.

        Returns:
            dict: A dictionary of the results of the function applied to each
                object.
        """
        out = {}
        for key, value in self.__dict__.items():
            if isinstance(value, JSONDataClass):
                out[key] = value.traverse_tree(func, prune_none)
            elif isinstance(value, list):
                li = []
                for item in value:
                    if isinstance(item, JSONDataClass):
                        li.append(item.traverse_tree(func, prune_none))
                    else:
                        try:
                            val = func(item, key)
                        except TypeError:
                            val = func(item)
                        li.append(val)
                out[key.replace("_", "__")] = li
            else:
                try:
                    val = func(value, key)
                except TypeError:
                    val = func(value)
                if not prune_none or val is not None:
                    out[key.replace("_", "__")] = val
        return out

    def top_level_keys(self) -> list[str]:
        """Get the top level keys of the object tree.

        Returns:
            list[str]: The top level keys of the object tree.
        """
        return list(self.__dict__.keys())

    def to_dict(self, drop_nones: bool = True) -> dict[str, Any]:
        """Convert the object tree to a dictionary. Syntactic sugar for the
        traverse_tree method with the function set to return the object.

        Args:
            drop_nones (bool): If True, then any keys with a value of None will
                be dropped. Defaults to True.

        Returns:
            dict[str, Any]: The object tree as a dictionary.
        """
        return self.traverse_tree(lambda x: x, drop_nones)

    @classmethod
    def load(cls, filename: str) -> "JSONDataClass":
        """Load the object tree from a JSON file.

        Args:
            filename (str): The path to the JSON file.

        Returns:
            Self: The object tree.
        """
        with open(filename, "r") as f:
            data = json.load(f)
        return cls(**data)

    def save(self, filename: str) -> None:
        """Save the object tree to a JSON file.

        Args:
            filename (str): The path to the JSON file.
        """
        with open(filename, "w") as f:
            json.dump(self.to_dict(), f, indent=4)


class JSONDataClassListTopLevel(JSONDataClass):
    """A subclass of JSONDataClass that has a specific override for the __init__
    method to allow for the top level of the object tree to be a list. This is
    an abstract base class and should not be instantiated directly.
    """

    next_level_type: Type[JSONDataClass] = JSONDataClass

    def __new__(cls, *args, **kwargs) -> "JSONDataClassListTopLevel":
        """Override the __new__ method to ensure that making the class into a
        dataclass is not allowed.

        Args:
            *args: The arguments to pass to the __new__ method.
            **kwargs: The keyword arguments to pass to the __new__ method.

        Raises:
            TypeError: If the class is being made into a dataclass.

        Returns:
            Self: The new instance of the class.
        """
        if is_dataclass(cls):
            raise TypeError(
                "JSONDataClassListTopLevel should not be used as a dataclass."
            )
        return super().__new__(cls)

    def __init__(self, json: list[dict] | list[Type[next_level_type]]) -> None:
        """Override the __init__ method to allow for the top level of the object
        tree to be a list.

        Args:
            json (list[dict] | list[Type[next_level_type]]): The json to
                convert to an object tree. Should be a list of dictionaries, or
                a list of objects of the next level type.

        Raises:
            TypeError: If the types of the items in the list are not all that of
                the defined next level type.
        """
        if len(json) > 0 and all(isinstance(result, dict) for result in json):
            self.data = [self.next_level_type(**result) for result in json]
        elif not all(
            isinstance(result, self.next_level_type) for result in json
        ):
            raise TypeError(
                "All items in the list must be of type "
                f"{self.next_level_type.__name__}"
            )
        else:
            self.data = json

    def __getitem__(
        self, key: str | int | slice | tuple[str | int, ...]
    ) -> Any:
        """Get the value of the given key. If the key is a tuple, then enable
        numpy style indexing. To maintain liskov substitution, this method
        will return an error if the first or only key are strings.

        Args:
            key (str | int | slice | tuple[str  |  int, ...]): The key to get
                the value of.

        Raises:
            TypeError: If the key is a string.
            TypeError: If the key is a tuple and the first key is a string.

        Returns:
            Any: The value of the given key.
        """
        if isinstance(key, tuple):
            first_index = key[0]
            other_index = key[1:]
            if isinstance(first_index, str):
                raise TypeError("Cannot index top level by string")
            return self.data[first_index][other_index]
        elif isinstance(key, slice):
            return JSONDataClassListTopLevel(self.data[key])
        elif isinstance(key, str):
            raise TypeError("Cannot index top level by string")
        return self.data[key]

    def __getattr__(self, key: str) -> Any:
        """If the attribute exists, act normally. Otherwise, assume the
        attribute exists in the top level child, data, and return a function
        that returns that attribute for each node.

        Args:
            key (str): Attribute name

        Returns:
            Any: If the attribute exists, return the attribute. Otherwise,
            return a function that returns the attribute for each node.
        """
        try:
            return super().__getattr__(key)
        except AttributeError:
            pass

        if key == "__id_index":
            if key in self.__dict__:
                return self.__dict__[key]
            else:
                return None

        def attr_func(*args, **kwargs) -> list[Any]:
            return [getattr(node, key)(*args, **kwargs) for node in self.data]

        return attr_func

    def __len__(self) -> int:
        return len(self.data)

    def traverse_tree(
        self, func: Callable[[Any], Any], prune_none: bool = False
    ) -> None:
        pre_return = super().traverse_tree(func, prune_none)
        return pre_return["data"]

    def to_dict(self, drop_nones: bool = True) -> list[dict]:
        """Convert the object tree to a dictionary. Syntactic sugar for the
        traverse_tree method with the function set to return the object.

        Args:
            drop_nones (bool): If True, then any keys with a value of None will
                be dropped. Defaults to True.

        Returns:
            dict[str, Any]: The object tree as a dictionary.
        """
        return self.traverse_tree(lambda x: x, drop_nones)

    @classmethod
    def load(
        cls, filename: str | list[str] | Path | list[Path]
    ) -> "JSONDataClassListTopLevel":
        """Load the object tree from a JSON file. If a list of filenames is
        provided, then load each file and return a list of the objects.

        Args:
            filename (str | list[str] | Path | list[Path]): The path to the JSON
                file, or a list of paths to the JSON files.

        Returns:
            JSONDataClassListTopLevel: The object tree.
        """
        if isinstance(filename, (str, Path)):
            return cls.__load_one(filename)
        jsons = []
        for file in filename:
            if isinstance(file, Path):
                file = str(file)
            jsons.append(cls.__load_one(file))
        return cls.concatenate(*jsons)

    @classmethod
    def __load_one(cls, filename: str) -> "JSONDataClassListTopLevel":
        """Load the object tree from a single JSON file.

        Args:
            filename (str): The path to the JSON file.

        Returns:
            JSONDataClassListTopLevel: The loaded object tree, as an instance of the class.
        """
        with open(filename, "r") as f:
            data = json.load(f)
        return cls(data)

    @classmethod
    def load_all_from_dir(
        cls, directory: str, recursive: bool = False
    ) -> "JSONDataClassListTopLevel":
        """Load all the JSON files from a directory into a single object tree.
        If recursive is True, then all subdirectories will be searched as well.
        Any improperly formatted JSON files will be skipped.

        Args:
            directory (str): The path to the directory.
            recursive (bool): If True, then all subdirectories will be searched
                as well. Defaults to False.

        Returns:
            JSONDataClassListTopLevel: The object tree.
        """
        data = []
        for filename in os.listdir(directory):
            if recursive:
                full_path = os.path.join(directory, filename)
                if os.path.isdir(full_path):
                    data.append(cls.load_all_from_dir(full_path, recursive))
                    continue
            if filename.endswith(".json"):
                try:
                    obj = cls.load(os.path.join(directory, filename))
                    data.append(obj)
                except Exception:
                    continue
        return cls.concatenate(*data)

    @classmethod
    def are_same_type(cls, other: Any) -> bool:
        """Check if the other object is of the same type as this one.

        Args:
            other (Any): The other object to check.

        Returns:
            bool: If the other object is of the same type as this one.
        """
        return isinstance(other, cls) and (
            cls.next_level_type == other.next_level_type
        )

    @classmethod
    def concatenate(
        cls, *args: list["JSONDataClassListTopLevel"]
    ) -> "JSONDataClassListTopLevel":
        """Concatenate the given objects into a single object.

        Args:
            *args: The objects to concatenate.

        Raises:
            ValueError: If no objects are given.
            TypeError: If the objects are not of the same type.

        Returns:
            JSONDataClassListTopLevel: The concatenated object.
        """
        if len(args) == 0:
            raise ValueError("No objects to concatenate")
        if len(args) == 1 and isinstance(args[0], list):
            warn(
                "Only one object to concatenate and it is a list. Unpacking"
                " the list for you, but this may not be what you want. Do not"
                " pass a list of objects to concatenate, instead pass each "
                "object as a separate argument."
            )
            args = args[0]
        if not all(cls.are_same_type(arg) for arg in args):
            raise TypeError("All objects must be of the same type")

        data = [data for c in args for data in c.data]

        return cls(data)
