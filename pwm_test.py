import unittest
from pwm import PWM, PasswordEntry
from pwm import _FAR_FUTURE as pwm_FAR_FUTURE

class TestPWM(unittest.TestCase):
    def setUp(self):
        self.pwm = PWM()
        entry = PasswordEntry(name="test", 
                              password="password",
                              username="username",
                              url="url",
                              notes="notes",
                              tags=["tag1", "tag2"],
                              reset_script="reset_script")
        self.pwm.add_entry(entry)

    def test_get_fuzzy_match_treshold(self):
        fuzzy_match_treshold = self.pwm.get_fuzzy_match_threshold()
        self.assertEqual(fuzzy_match_treshold, 0.8)

    def test_set_fuzzy_match_treshold(self):
        self.pwm.set_fuzzy_match_threshold(0.9)
        self.assertEqual(self.pwm.get_fuzzy_match_threshold(), 0.9)

        with self.assertRaises(ValueError):
            self.pwm.set_fuzzy_match_threshold(1.1)

        with self.assertRaises(ValueError):
            self.pwm.set_fuzzy_match_threshold(-0.1)

    def test_create_entry(self):
        entry = PasswordEntry(name="test2", 
                              password="password2",
                              username="username2",
                              url="url",
                              notes="notes",
                              tags=["tag1", "tag2"],
                              reset_script="reset_script")
        before = entry.id
        self.pwm.add_entry(entry)
        after = entry.id
        self.assertNotEqual(before, after)

    def test_set_password(self):
        entry = self.pwm.get_entry("test")
        entry.set_password("password2")
        self.assertEqual(entry.password, "password2")
        self.assertEqual(len(entry.password_history), 1)
        self.assertEqual(entry.password_history[0][1], "password")

    def test_get_entry(self):
        entry = self.pwm.get_entry("test")
        self.assertEqual(entry.name, "test")

    def test_get_trash(self):
        self.assertEqual(len(self.pwm.get_trash()), 0)

    def test_transfer_to_trash(self):
        entry = self.pwm.get_entry("test")
        self.pwm.remove_entry(entry.id)
        self.assertEqual(len(self.pwm.get_trash()), 1)

    def test_restore_entry(self):
        entry = self.pwm.get_entry("test")
        self.pwm.remove_entry(entry.id)
        self.pwm.restore_entry(entry.id)
        self.assertEqual(len(self.pwm.get_trash()), 0)
        self.assertEqual(len(self.pwm.entries), 1)

    def test_purge_entry(self):
        entry = self.pwm.get_entry("test")
        self.pwm.remove_entry(entry.id)
        self.pwm.purge_entry(entry.id)
        self.assertEqual(len(self.pwm.get_trash()), 0)
        self.assertEqual(len(self.pwm.entries), 0)
        self.assertEqual(self.pwm._next_id, 2)

    def test_get_entries(self):
        self.assertEqual(len(self.pwm.get_entries()), 1)

    def test_get_entires_by_page(self):
        for id in range(100):
            entry = PasswordEntry(name=f"test{id}", 
                                  password="password",
                                  username="username",
                                  url="url",
                                  notes="notes",
                                  tags=["tag1", "tag2"],
                                  reset_script="reset_script")
            self.pwm.add_entry(entry)
        self.assertEqual(len(self.pwm.get_entries(page=1, entries_per_page=10)), 10)
        self.assertEqual(len(self.pwm.get_entries(page=1, entries_per_page=50)), 50)
        self.assertEqual(len(self.pwm.get_entries(page=0, entries_per_page=1000)), 101)
        self.assertEqual(len(self.pwm.get_entries(page=2, entries_per_page=100)), 0)

    def test_get_entires_by_tag(self):
        entry = PasswordEntry(name="test2", 
                              password="password2",
                              username="username2",
                              url="url",
                              notes="notes",
                              tags=["tag1", "tag3"],
                              reset_script="reset_script")
        self.pwm.add_entry(entry)
        self.assertEqual(len(self.pwm.get_entries(tag="tag1")), 2)
        self.assertEqual(len(self.pwm.get_entries(tag="tag3")), 1)
        self.assertEqual(len(self.pwm.get_entries(tag="tag2")), 1)

    def test_update_entry(self):
        entry = self.pwm.get_entry("test")
        entry.name = "test2"
        modified_date = entry.modified
        self.pwm.update_entry(entry)
        self.assertEqual(self.pwm.get_entry("test2").name, "test2")
        self.assertNotEqual(modified_date, self.pwm.get_entry("test2").modified)

    def test_update_entry_error(self):
        entry = PasswordEntry(name="test2", 
                              password="password2",
                              username="username2",
                              url="url",
                              notes="notes",
                              tags=["tag1", "tag2"],
                              reset_script="reset_script")
        self.assertNotEqual(entry.id, self.pwm.get_entry("test").id)
        with self.assertRaises(Exception):
            self.pwm.update_entry(entry)

    def test_set_expiration_interval(self):
        entry = self.pwm.get_entry("test")
        self.assertEqual(entry.expiration_interval, -1)
        self.assertEqual(entry.expiration_interval_unit, "days")
        self.assertEqual(entry.next_expiration, pwm_FAR_FUTURE)
        for interval in ["days", "weeks", "months", "years"]:
            entry.set_expiration_interval(interval=10, unit=interval)
            self.assertEqual(entry.expiration_interval, 10)
            self.assertEqual(entry.expiration_interval_unit, interval)
            self.assertEqual(len(self.pwm.get_expired_entries()), 0)

        with self.assertRaises(ValueError):
            entry.set_expiration_interval(interval=10, unit="invalid")

    def test_get_expired_entries(self):
        self.assertEqual(len(self.pwm.get_expired_entries()), 0)
        entry = self.pwm.get_entry("test")
        entry.set_expiration_interval(10, unit="days")
        self.pwm.update_entry(entry)
        self.assertEqual(len(self.pwm.get_expired_entries()), 0)
        entry.next_expiration = entry.next_expiration.shift(days=-100)
        self.pwm.update_entry(entry)
        self.assertEqual(len(self.pwm.get_expired_entries()), 1)


    def test_search(self):
        self.assertEqual(len(self.pwm.search("test")), 1)

        self.assertEqual(len(self.pwm.search("invalid")), 0)

        self.pwm.set_fuzzy_match_threshold(0.999999)
        self.assertEqual(len(self.pwm.search("test123")), 0)

        self.pwm.set_fuzzy_match_threshold(0.5)
        self.assertEqual(len(self.pwm.search("test123")), 1)


if __name__ == '__main__':
    unittest.main()
