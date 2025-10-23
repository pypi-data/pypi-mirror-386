import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from office_templates.office_renderer import render_xlsx

from tests.utils import has_view_permission


class TestXlsxUnit(unittest.TestCase):
    def setUp(self):
        # Create temporary files for input and output
        self.temp_input = tempfile.mktemp(suffix=".xlsx")
        self.temp_output = tempfile.mktemp(suffix=".xlsx")

        # Create a minimal context
        self.context = {
            "user": {"name": "Alice", "email": "alice@example.com"},
            "company": "Example Corp",
        }

        # Request user for permission checks
        self.request_user = MagicMock()
        self.request_user.has_perm.return_value = True

    def tearDown(self):
        # Clean up temporary files
        for temp_file in [self.temp_input, self.temp_output]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    @patch("office_templates.office_renderer.xlsx.render.get_load_workbook")
    @patch("office_templates.office_renderer.xlsx.render.process_worksheet")
    def test_render_xlsx_with_file_path(
        self, mock_process_worksheet, mock_get_load_workbook
    ):
        """Test rendering an XLSX file from a file path."""
        # Set up mock workbook
        mock_workbook = MagicMock()
        mock_worksheet = MagicMock()
        mock_workbook.__getitem__.return_value = mock_worksheet
        mock_workbook.sheetnames = ["Sheet1", "Sheet2"]

        # Set up mock load_workbook function
        mock_load_func = MagicMock(return_value=mock_workbook)
        mock_get_load_workbook.return_value = mock_load_func

        # Call render_xlsx with file path
        result, errors = render_xlsx(
            template=self.temp_input,
            context=self.context,
            output=self.temp_output,
            check_permissions=lambda obj: has_view_permission(obj, self.request_user),
        )

        # Verify load_workbook was called with the file path
        mock_load_func.assert_called_once_with(self.temp_input)

        # Verify the calls made to process_worksheet
        # Check that it was called twice
        self.assertEqual(mock_process_worksheet.call_count, 2)

        # Check the first call (Sheet1)
        first_call_args, first_call_kwargs = mock_process_worksheet.call_args_list[0]
        self.assertEqual(first_call_kwargs["worksheet"], mock_worksheet)
        self.assertEqual(first_call_kwargs["context"]["sheet_name"], "Sheet1")
        self.assertEqual(first_call_kwargs["context"]["user"]["name"], "Alice")
        self.assertIsNotNone(
            first_call_kwargs["check_permissions"]
        )  # Lambda function present

        # Check the second call (Sheet2)
        second_call_args, second_call_kwargs = mock_process_worksheet.call_args_list[1]
        self.assertEqual(second_call_kwargs["worksheet"], mock_worksheet)
        self.assertEqual(second_call_kwargs["context"]["sheet_name"], "Sheet2")
        self.assertEqual(second_call_kwargs["context"]["user"]["name"], "Alice")
        self.assertIsNotNone(
            second_call_kwargs["check_permissions"]
        )  # Lambda function present

        # Verify workbook.save was called with the output path
        mock_workbook.save.assert_called_once_with(self.temp_output)

        # Verify result and errors
        self.assertEqual(result, self.temp_output)
        self.assertIsNone(errors)

    @patch("office_templates.office_renderer.xlsx.render.get_load_workbook")
    @patch("office_templates.office_renderer.xlsx.render.process_worksheet")
    def test_render_xlsx_with_file_object(
        self, mock_process_worksheet, mock_get_load_workbook
    ):
        """Test rendering an XLSX file from a file-like object."""
        # Set up mock workbook and worksheet
        mock_workbook = MagicMock()
        mock_worksheet = MagicMock()
        mock_workbook.__getitem__.return_value = mock_worksheet
        mock_workbook.sheetnames = ["Sheet1"]

        # Set up mock load_workbook function
        mock_load_func = MagicMock(return_value=mock_workbook)
        mock_get_load_workbook.return_value = mock_load_func

        # Mock file objects
        mock_input_file = MagicMock()
        mock_output_file = MagicMock()

        # Call render_xlsx with file objects
        result, errors = render_xlsx(
            template=mock_input_file,
            context=self.context,
            output=mock_output_file,
            check_permissions=lambda obj: has_view_permission(obj, self.request_user),
        )

        # Verify file handling
        mock_input_file.seek.assert_called_once_with(0)
        mock_load_func.assert_called_once_with(mock_input_file)

        # Verify process_worksheet was called
        mock_process_worksheet.assert_called_once()

        # Verify workbook.save was called with the output file object
        mock_workbook.save.assert_called_once_with(mock_output_file)

        # Verify output file was rewound
        mock_output_file.seek.assert_called_once_with(0)

        # Verify result and errors
        self.assertEqual(result, mock_output_file)
        self.assertIsNone(errors)

    @patch("office_templates.office_renderer.xlsx.render.get_load_workbook")
    @patch("office_templates.office_renderer.xlsx.render.process_worksheet")
    def test_render_xlsx_with_error(self, mock_process_worksheet, mock_get_load_workbook):
        """Test handling of errors during rendering."""
        # Set up mock workbook
        mock_workbook = MagicMock()
        mock_worksheet = MagicMock()
        mock_workbook.__getitem__.return_value = mock_worksheet
        mock_workbook.sheetnames = ["Sheet1"]

        # Set up mock load_workbook function
        mock_load_func = MagicMock(return_value=mock_workbook)
        mock_get_load_workbook.return_value = mock_load_func

        # Make process_worksheet raise an exception
        mock_process_worksheet.side_effect = ValueError("Test error")

        # Call render_xlsx
        with patch("builtins.print") as mock_print:
            result, errors = render_xlsx(
                template=self.temp_input,
                context=self.context,
                output=self.temp_output,
                check_permissions=lambda obj: has_view_permission(obj, self.request_user),
            )

        # Verify error handling
        self.assertIsNone(result)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], "Error in sheet 'Sheet1': Test error")

        # Verify error messages were printed
        mock_print.assert_any_call("Rendering aborted due to the following errors:")
        mock_print.assert_any_call(" - Error in sheet 'Sheet1': Test error")
        mock_print.assert_any_call("Output file not saved.")

        # Verify workbook.save was not called
        mock_workbook.save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
