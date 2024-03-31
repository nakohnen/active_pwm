from dataclasses import dataclass, field

import arrow
from arrow import Arrow
from rapidfuzz import fuzz
import toml


# Representing a "far future" date (conceptually "infinity")
_FAR_FUTURE = arrow.get('9999-12-31T23:59:59.999999')

# Representing a "far past" date (conceptually "-infinity")
_FAR_PAST = arrow.get('0001-01-01T00:00:00.000000')

@dataclass
class PasswordEntry:
    id: int = -1
    name: str = ""
    username: str = ""
    password: str = ""
    url: str = ""
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    created: Arrow = field(default_factory=Arrow.now)
    modified: Arrow = field(default_factory=Arrow.now)
    password_history: list[tuple[Arrow, str]] = field(default_factory=list)
    next_expiration: Arrow = _FAR_FUTURE
    expiration_interval: int = -1
    expiration_interval_unit: str = "days"
    reset_script: str = ""

    def __hash__(self):
        return self.id

    def set_password(self, password: str):
        now = Arrow.now()
        self.password_history.append((now, self.password))
        self.modified = now
        self.password = password
        self._set_next_expiration()

    def set_expiration_interval(self, interval: int, unit: str):
        if unit not in ['years', 'months', 'weeks', 'days']:
            raise ValueError("Invalid unit, must be one of 'years', 'months', 'weeks', 'days'")

        self.expiration_interval = interval
        self.expiration_interval_unit = unit
        self.modified = Arrow.now()
        self._set_next_expiration()

    def _set_next_expiration(self):
        if self.expiration_interval > 0:
            unit = self.expiration_interval_unit
            interval = self.expiration_interval
            self.next_expiration = self.modified.shift(**{unit: interval})
            self.next_expiration = self.next_expiration.floor('day')
        else:
            self.next_expiration = _FAR_FUTURE

class PWM:

    def __init__(self):
        self.entries = []
        self._next_id = 1
        self.trash = []
        self._FUZZY_MATCH_THRESHOLD = 0.8

    def get_fuzzy_match_threshold(self):
        return self._FUZZY_MATCH_THRESHOLD

    def set_fuzzy_match_threshold(self, threshold: float):
        if 0 < threshold < 1:
            self._FUZZY_MATCH_THRESHOLD = threshold
            return threshold
        else:
            raise ValueError("Threshold must be scrictly between 0 and 100")

    def add_entry(self, entry: PasswordEntry):
        self.entries.append(entry)
        entry.id = self._next_id
        self._next_id += 1
        entry.created = Arrow.now()
        entry.modified = Arrow.now()

        entry._set_next_expiration()
            

    def remove_entry(self, entry_id: int):
        to_remove = None
        for entry in self.entries:
            if entry.id == entry_id:
                to_remove = entry
                break
        if to_remove is not None:
            self.entries.remove(to_remove)
            self.trash.append(to_remove)
            to_remove.modified = Arrow.now()
        else:
            raise Exception(f"Entry with id {entry_id} not found")

    def get_entry(self, name: str) -> PasswordEntry:
        for entry in self.entries:
            if entry.name == name:
                return entry
        return None

    def get_entries(self, tag: str = None, page: int = 0, entries_per_page: int = -1) -> list[PasswordEntry]:
        if tag is None:
            if entries_per_page > 0:
                return self.entries[page * entries_per_page:(page + 1) * entries_per_page]
            return self.entries
        else:
            result = []
            if entries_per_page > 0:
                result = [entry for entry in self.entries if tag in entry.tags][page * entries_per_page:(page + 1) * entries_per_page]
            else:
                result = [entry for entry in self.entries if tag in entry.tags]
            return result


    def update_entry(self, entry: PasswordEntry):
        found = False
        for i, e in enumerate(self.entries):
            if e.id == entry.id:
                self.entries[i] = entry
                found = True
                break
        if found:
            entry.modified = Arrow.now()

        else:
            raise Exception(f"Entry with id {entry.id} not found")

    def save(self, filename: str):
        with open(filename, 'w') as f:
            to_be_saved = dict()
            to_be_saved['entries'] = [entry.__dict__ for entry in self.entries]
            to_be_saved['trash'] = [entry.__dict__ for entry in self.trash]
            toml.dump(to_be_saved, f)

    def load(self, filename: str):
        with open(filename, 'r') as f:
            loaded = toml.load(f)
            self.entries = loaded['entries']
            self.trash = loaded['trash']
        self._next_id = max([entry.id for entry in self.entries + self.trash]) + 1

    def get_expired_entries(self) -> list[PasswordEntry]:
        return [entry for entry in self.entries if entry.next_expiration < Arrow.now()]

    def get_trash(self) -> list[PasswordEntry]:
        return self.trash

    def restore_entry(self, entry_id: int):
        to_restore = None
        for entry in self.trash:
            if entry.id == entry_id:
                to_restore = entry
                break
        if to_restore is not None:
            self.trash.remove(to_restore)
            self.entries.append(to_restore)
            to_restore.modified = Arrow.now()
        else:
            raise Exception(f"Entry with id {entry_id} not found")

    def purge_entry(self, entry_id: int):
        to_purge = None
        for entry in self.trash:
            if entry.id == entry_id:
                to_purge = entry
                break
        if to_purge is not None:
            self.trash.remove(to_purge)
        else:
            raise Exception(f"Entry with id {entry_id} not found")


    def search(self, query: str) -> list[PasswordEntry]:
        results = set()
        fuzzy_match_threshold = self.get_fuzzy_match_threshold() * 100
        for entry in self.entries:
            if fuzz.ratio(query, entry.name) > fuzzy_match_threshold:
                results.add(entry)
                continue
            if fuzz.ratio(query, entry.username) > fuzzy_match_threshold:
                results.add(entry)
                continue
            if fuzz.ratio(query, entry.url) > fuzzy_match_threshold:
                results.add(entry)
                continue
            if fuzz.ratio(query, entry.notes) > fuzzy_match_threshold or query in entry.notes:
                results.add(entry)
                continue
            for tag in entry.tags:
                if fuzz.ratio(query, tag) > fuzzy_match_threshold:
                    results.add(entry)
                    break
            if fuzz.ratio(query, entry.reset_script) > fuzzy_match_threshold or \
                    query in entry.reset_script:
                results.add(entry)
                continue
            if any([fuzz.ratio(query, password) > fuzzy_match_threshold for _, password in entry.password_history]):
                results.add(entry)
                continue
        return list(results)


    def get_all_tags(self) -> list[str]:
        return list(set([tag for tag in entry.tags for entry in self.entries]))



