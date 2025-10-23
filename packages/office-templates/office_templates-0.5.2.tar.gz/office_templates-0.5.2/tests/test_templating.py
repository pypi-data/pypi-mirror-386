import datetime
import re
import unittest
from unittest.mock import patch

from office_templates.templating.exceptions import (
    BadTemplateModeError,
    PermissionDeniedException,
    MissingDataException,
)
from office_templates.templating.core import process_text

from tests.utils import has_view_permission


# ----- Dummy Classes for Testing -----


class DummyUser:
    def __init__(self, name, email, is_active=True, friend_count=0):
        self.name = name
        self.email = email
        self.is_active = is_active
        self.friend_count = friend_count
        # Simulate a Django object by adding _meta
        self._meta = True

    def __str__(self):
        return self.name


class DummyDjangoUser(DummyUser):
    # This tricks our system into thinking this is a django model
    _meta = True


class DummyCohort:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


class DummyRequestUser:
    """A dummy request user that approves everything except objects with 'deny' in their name."""

    def has_perm(self, perm, obj):
        if hasattr(obj, "name") and "deny" in obj.name.lower():
            return False
        return True


# For testing, we'll use a normal Python list to simulate program.users.
# (Our parser code should work on lists as well.)


# ----- Test Case for Normal Mode -----
class TestTemplatingNormalMode(unittest.TestCase):
    def setUp(self):
        # Create a dummy cohort, users, and program context.
        self.cohort = DummyCohort("Cohort A")
        self.user1 = DummyUser(
            "Alice", "alice-three@example.com", is_active=True, friend_count=2
        )
        self.user2 = DummyUser("Bob", "bob@example.com", is_active=True, friend_count=0)
        self.django_user = DummyDjangoUser(
            "DenyUser", "deny@example.com", is_active=True, friend_count=1
        )
        # program.users as a list (simulate queryset already converted to a list)
        self.program = {
            "users": [self.user1, self.user2, self.django_user],
            "name": "Test Program",
        }
        self.now = datetime.datetime(2025, 2, 18, 12, 0, 0)
        self.context = {
            "user": self.user1,
            "program": self.program,
            "date": datetime.date(2020, 1, 15),
        }
        # Use a dummy request user that denies permission on any object whose name contains "deny".
        self.request_user = DummyRequestUser()

    @patch("office_templates.templating.resolve.datetime.datetime")
    def test_pure_now_formatting_normal(self, mock_dt):
        # Patch datetime.datetime.now in the parser module to always return self.now.
        mock_dt.now.return_value = self.now
        tpl = "{{ now | MMMM dd, YYYY }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        expected = self.now.strftime("%B %d, %Y")
        self.assertEqual(result, expected)

    def test_pure_list_normal(self):
        # Pure placeholder that resolves to a list in normal mode
        tpl = "{{ program.users.email }}"
        # Since self.program["users"] is a list of DummyUser, and email is an attribute
        # Expect joined emails, but note that self.user3 should be filtered out by permission check.
        # However, here check_permissions is False.
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        expected = ", ".join(u.email for u in self.program["users"])
        self.assertEqual(result, expected)

    def test_datetime_formatting(self):
        """Test that datetime formatting works correctly with the date filter."""
        # Add a datetime to the context
        self.context["meeting_time"] = datetime.datetime(2025, 2, 18, 12, 0, 0)
        tpl = "{{ meeting_time | MMMM dd, YYYY }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        expected = self.context["meeting_time"].strftime("%B %d, %Y")
        self.assertEqual(result, expected)

        # Test with now to ensure it works the same
        tpl2 = "{{ now | MMMM dd, YYYY }}"
        with patch("office_templates.templating.resolve.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = self.now
            result2 = process_text(
                tpl2,
                self.context,
                check_permissions=None,
                mode="normal",
            )
        expected2 = self.now.strftime("%B %d, %Y")
        self.assertEqual(result2, expected2)

    def test_mixed_text_multiple(self):
        # Mixed text with multiple placeholders.
        tpl = "The program is: {{ program.name }}. The user is: {{ user.name }}."
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        # Expected: "The program is: Test Program. Users: alice-three@example.com, bob@example.com, deny@example.com are active."
        expected = (
            f"The program is: {self.program['name']}. The user is: {self.user1.name}."
        )
        self.assertEqual(result, expected)

    def test_mixed_text_list(self):
        # Mixed text with a placeholder that resolves to a list should join the list.
        tpl = "All emails: {{ program.users.email }} are active."
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        # Expected: "All emails: alice-three@example.com, bob@example.com, deny@example.com are active."
        expected = (
            f"All emails: {', '.join(u.email for u in self.program['users'])} are active."
        )
        self.assertEqual(result, expected)

    def test_mixed_text_list_multiple(self):
        # Mixed text with a list placeholder AND another.
        tpl = "All emails: {{ program.users.email }}. User is: {{ user.name }}."
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        expected = f"All emails: {', '.join(u.email for u in self.program['users'])}. User is: {self.user1.name}."
        self.assertEqual(result, expected)

    def test_permission_denied_in_normal(self):
        # In pure mode with check_permissions True, the dummy request user denies objects with "deny".
        tpl = "{{ program.users.email }}"
        # Now, with permission checking enabled, self.user3 ("DenyUser") should be filtered out.
        with self.assertRaises(PermissionDeniedException):
            check_permissions = lambda obj: has_view_permission(obj, self.request_user)
            process_text(
                tpl,
                self.context,
                check_permissions=check_permissions,
                mode="normal",
            )

    def test_empty_placeholder(self):
        tpl = "Empty tag: {{   }}."
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        self.assertEqual(result, "Empty tag: .")

    def test_missing_key_in_context(self):
        tpl = "Missing: {{ non_existent }}."
        with self.assertRaises(MissingDataException):
            process_text(
                tpl,
                self.context,
                check_permissions=None,
                mode="normal",
            )

    def test_nested_lookup_with_function(self):
        # Dynamically add a callable attribute to user1.
        self.user1.get_display = lambda: self.user1.name.upper()
        self.context["user"] = self.user1
        tpl = "Display: {{ user.get_display() }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        self.assertEqual(result, "Display: ALICE")

    def test_filter_multiple_conditions(self):
        tpl = "{{ program.users[is_active=True, email=bob@example.com].email }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        # The filtered list will join a single email into a string.
        self.assertEqual(result, self.user2.email)

    def test_all_permissions_denied(self):
        # Create a request user that denies permission for all objects.
        class DenyAllUser:
            def has_perm(self, perm, obj):
                return False

        denier = DenyAllUser()
        tpl = "{{ program.users.email }}"
        with self.assertRaises(PermissionDeniedException):
            check_permissions = lambda obj: has_view_permission(obj, denier)
            process_text(
                tpl,
                self.context,
                check_permissions=check_permissions,
                mode="normal",
            )

    def test_table_mode_with_single_value(self):
        self.context["value"] = 100
        tpl = "{{ value }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="table",
        )
        self.assertEqual(result, "100")

    def test_table_mode_with_list_value(self):
        self.context["value"] = [100]
        tpl = "{{ value }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="table",
        )
        self.assertEqual(result, ["100"])

    def test_non_date_formatting(self):
        # Test if formatting fails gracefully.
        tpl = "{{ now | RANDOM WORDS }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        self.assertEqual(
            result, "RANDOM WORDS"
        )  # Should return empty string and record an error.

    def test_no_placeholder_mixed_text(self):
        tpl = "This text has no placeholders."
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        self.assertEqual(result, tpl)

    @patch("office_templates.templating.resolve.datetime.datetime")
    def test_now_in_mixed_text(self, mock_dt):
        mock_dt.now.return_value = self.now
        tpl = "Date is {{ now | MMMM dd, YYYY }} and time is set."
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        expected_date = self.now.strftime("%B %d, %Y")
        expected = re.sub(r"\{\{.*?\}\}", expected_date, tpl)
        self.assertEqual(result, expected)

    def test_integer_resolution(self):
        self.context["count"] = 42
        tpl = "The count is {{ count }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        self.assertEqual(result, "The count is 42")

    def test_float_resolution(self):
        self.context["price"] = 19.95
        tpl = "Price: {{ price }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        self.assertEqual(result, "Price: 19.95")

    def test_math_operator_multiplication(self):
        self.context["value"] = 7
        tpl = "{{ value * 2 }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        self.assertEqual(result, "14.0")

    def test_math_operator_subtraction(self):
        self.context["value"] = 10
        tpl = "{{ value - 4 }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        self.assertEqual(result, "6.0")

    def test_numerical_formatting(self):
        self.context["value"] = 3.14159
        tpl = "{{ value | .2f }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        self.assertEqual(result, "3.14")

    def test_math_and_formatting_combined(self):
        self.context["value"] = 2.71828
        tpl = "{{ value * 3 | .2f }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        self.assertEqual(result, "8.15")

    def test_string_upper_formatting(self):
        self.context["value"] = "hello world"
        tpl = "{{ value | upper }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        self.assertEqual(result, "HELLO WORLD")

    def test_length_formatting(self):
        self.context["value"] = "hello world"
        tpl = "{{ value | length }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        self.assertEqual(result, "11")

    def test_string_lower_formatting(self):
        self.context["value"] = "Hello World"
        tpl = "{{ value | lower }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        self.assertEqual(result, "hello world")

    def test_string_capitalize_formatting(self):
        self.context["value"] = "hello world"
        tpl = "{{ value | capitalize }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        self.assertEqual(result, "HELLO WORLD")

    def test_string_title_formatting(self):
        self.context["value"] = "hello world"
        tpl = "{{ value | title }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        self.assertEqual(result, "Hello World")

    def test_filter_and_math_operation(self):
        tpl = "{{ program.users[is_active=True, email=alice-three@example.com].friend_count * 2 }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="normal",
        )
        # The filtered list will join a single email into a string, and then multiply by 2 to give 4.
        self.assertEqual(result, "4.0")


# ----- Test Case for Table Mode -----
class TestTemplatingTableMode(unittest.TestCase):
    def setUp(self):
        # Create a dummy cohort, users, and program context.
        self.cohort = DummyCohort("Cohort A")
        self.user1 = DummyUser("Alice", "alice-three@example.com", is_active=True)
        self.user2 = DummyUser("Bob", "bob@example.com", is_active=True)
        self.django_user = DummyDjangoUser("DenyUser", "deny@example.com", is_active=True)
        # program.users as a list (simulate queryset already converted to a list)
        self.program = {
            "users": [self.user1, self.user2, self.django_user],
            "name": "Test Program",
        }
        self.now = datetime.datetime(2025, 2, 18, 12, 0, 0)
        self.context = {
            "user": self.user1,
            "program": self.program,
            "date": datetime.date(2020, 1, 15),
        }
        # Use a dummy request user that denies permission on any object whose name contains "deny".
        self.request_user = DummyRequestUser()

    # Table mode tests.
    @patch("office_templates.templating.resolve.datetime.datetime")
    def test_pure_now_formatting_table(self, mock_dt):
        # Patch datetime.datetime.now in the parser module to always return self.now.
        mock_dt.now.return_value = self.now
        # Pure placeholder in table mode returns a string (if not list).
        tpl = "{{ now | MMMM dd, YYYY }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="table",
        )
        expected = self.now.strftime("%B %d, %Y")
        self.assertEqual(result, expected)

    def test_pure_list_table(self):
        # Pure placeholder in table mode returns a list of strings.
        tpl = "{{ program.users.email }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="table",
        )
        expected = [str(u.email) for u in self.program["users"]]
        self.assertEqual(result, expected)

    def test_mixed_text_table(self):
        # Mixed text in table mode: only one placeholder allowed. If it resolves to a list, should return a list.
        tpl = "User email: {{ program.users.email }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="table",
        )
        # Expect a list with one entry per user.
        expected = [f"User email: {u.email}" for u in self.program["users"]]
        self.assertEqual(result, expected)

    def test_mixed_text_multiple_placeholders_table(self):
        tpl = "User: {{ user.name }} and Email: {{ user.email }}"
        with self.assertRaises(BadTemplateModeError):
            process_text(
                tpl,
                self.context,
                check_permissions=None,
                mode="table",
            )

    def test_table_mode_with_single_value(self):
        self.context["value"] = 100
        tpl = "{{ value }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="table",
        )
        self.assertEqual(result, "100")

    def test_table_mode_with_list_value(self):
        self.context["value"] = [100]
        tpl = "{{ value }}"
        result = process_text(
            tpl,
            self.context,
            check_permissions=None,
            mode="table",
        )
        self.assertEqual(result, ["100"])

    def test_all_permissions_denied(self):
        # Create a request user that denies permission for all objects.
        class DenyAllUser:
            _meta: True

            def has_perm(self, perm, obj):
                return False

        denier = DenyAllUser()
        tpl = "{{ program.users.email }}"
        with self.assertRaises(PermissionDeniedException):
            check_permissions = lambda obj: has_view_permission(obj, denier)
            process_text(
                tpl,
                self.context,
                check_permissions=check_permissions,
                mode="table",
            )


if __name__ == "__main__":
    unittest.main()
