import random
from typing import Any, Optional, Iterable, Generic, TypeVar, Self
from collections import defaultdict
from collections.abc import Callable, Hashable


def rejection_sample(population: Iterable, excluded: Iterable, max_attempts: int = 100):
    population = list(population)
    if not population:
        raise ValueError("Sequence is empty")
    excluded_ids = set(id(x) for x in excluded)

    # Fast rejection sampling (O(1) average case for small exclusion sets)
    for _ in range(max_attempts):
        choice = random.choice(population)
        if id(choice) not in excluded_ids:
            return choice

    # Fallback to O(n) scan only if necessary (rare for small exclusion sets)
    valid_choices = [item for item in population if id(item) not in excluded_ids]
    if not valid_choices:
        raise ValueError("No valid elements to choose from")
    return random.choice(valid_choices)


class OrderedSet[T]:
    def __init__(self, items: Optional[Iterable[T]] = None):
        self.dict = dict() if items is None else dict.fromkeys(items)

    def __iter__(self):
        yield from self.dict

    def __len__(self):
        return len(self.dict)

    def add(self, item: Any) -> None:
        self.dict[item] = None

    def remove(self, item: Any) -> None:
        del self.dict[item]


class Counted:
    counter = 0

    def __init__(self):
        self.id = Counted.counter
        Counted.counter += 1

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return hash(self) == hash(other)


# --- Indexed sets ---

T = TypeVar("T")  # Member type of `IndexedSet`


class SetProperty:
    """
    This class should be initialized with a function or lambda which
    takes a set member as input, and returns a collection or iterable of
    values associated with that member that you want to index by.

    Example initialization:
    ```
    @dataclass
    class SportsTeam:
        name: str
        members: list[str]

    members_alt = SetProperty(lambda team: team.members) # If someone can belong to multiple teams (default)
    ```
    """

    def __init__(self, fn: Callable[[T], Iterable[Hashable]], is_unique=False):
        self.fn = fn
        self.is_unique = is_unique

    def __call__(self, item: T) -> Iterable[Hashable]:
        return self.fn(item)


class Property(SetProperty):
    """
    This class should be initialized with a function or lambda which
    takes a set member as input, and returns a single object which is
    the corresponding property value of a set member.

    An example of initializing a `Property`
    ```
    @dataclass
    class Fruit:
        color: str

    my_property = Property(lambda fruit: fruit.color) # Equivalent using a lambda function
    ```
    """

    def __call__(self, item: T) -> Iterable[Hashable]:
        return [self.fn(item)]


class IndexedSet(set[T], Generic[T]):
    """
    A subclass of the built-in `set`, with support for indexing
    by arbitrary properties of set members, as well as integer
    indexing to allow for random sampling.

    Credit https://stackoverflow.com/a/15993515 for the integer indexing logic.

    If you know for some property that you should only get a single
    set member back when using `lookup`, mark that property as unique
    when you create it.

    NOTE: although this class is indexable due to the implementation
    of `__getitem__`, member ordering is not stable across insertions
    and deletions.

    Example usage:
    ```
    @dataclass
    class SportsTeam:
        name: str
        jersey_color: str
        members: list[str]

    teams: IndexedSet[SportsTeam] = IndexedSet()
    teams.create_index("name", Property(lambda team: team.name, is_unique=True))
    teams.create_index("color", Property(lambda team: team.jersey_color))

    [...] # populate the set with teams

    teams.lookup("name", "Manchester") # Returns the team whose name is "Manchester"
    teams.lookup("color", "blue")    # Returns all teams with blue jerseys
    ```
    """

    properties: dict[str, SetProperty]
    indices: dict[str, defaultdict[Hashable, Self]]

    _item_to_pos: dict[T, int]
    _item_list: list[T]

    def __init__(self, iterable: Iterable[T] = []):
        iterable = list(iterable)
        super().__init__(iterable)
        self._item_list = iterable
        self._item_to_pos = {item: i for (i, item) in enumerate(iterable)}

        self.properties = {}
        self.indices = {}

    def add(self, item: T):
        if item in self:
            return
        super().add(item)

        # Update integer index
        self._item_list.append(item)
        self._item_to_pos[item] = len(self._item_list) - 1

        # Update property indices
        for prop_name in self.properties:
            prop = self.properties[prop_name]
            for val in prop(item):
                if prop.is_unique:
                    assert not self.indices[prop_name][val]
                self.indices[prop_name][val].add(item)

    def remove(self, item: T):
        assert item in self
        super().remove(item)

        # Update integer index
        pos = self._item_to_pos.pop(item)
        last_item = self._item_list.pop()
        if pos != len(self._item_list):
            self._item_list[pos] = last_item
            self._item_to_pos[last_item] = pos

        # Update property indices
        for prop_name in self.properties:
            prop = self.properties[prop_name]
            for val in prop(item):
                self.indices[prop_name][val].remove(item)
                # If the index entry is now empty, delete it
                if not self.indices[prop_name][val]:
                    del self.indices[prop_name][val]

    def lookup(self, name: str, value: Any) -> T | Iterable[T]:
        prop = self.properties[name]
        matches = self.indices[name][value]

        if prop.is_unique:
            assert len(matches) == 1
            return next(iter(matches))
        else:
            return matches

    def remove_by(self, prop_name: str, value: Any):
        """
        Remove all set members whose property `prop_name` matches or contains `value`.
        """
        if value not in self.indices[prop_name]:
            return
        matches = list(self.indices[prop_name][value])
        for match in matches:
            assert match in self
            self.remove(match)

    def create_index(self, name: str, prop: SetProperty):
        """
        Given a function which maps a set member to an `Any`-typed value, create
        a reverse-index mapping a property value to the set of the members of `self`
        with that property. This index is updated when adding new members or removing
        existing ones, but please note that if you mutate the internal state of an
        existing set member, this object will not reflect those updates unless you
        take the care to update the indices manually.

        NOTE: mutating set members outside of interface calls can invalidate indices.
        """
        assert name not in self.properties
        self.properties[name] = prop
        self.indices[name] = defaultdict(IndexedSet)

        for el in self:
            for val in prop(el):
                if prop.is_unique:
                    assert not self.indices[name][val]
                self.indices[name][val].add(el)

    def __getitem__(self, i):
        assert 0 <= i < len(self)
        return self._item_list[i]
