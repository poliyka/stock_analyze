from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("-standard", "cal")
class TestCalculateNetProfitAndLossCase(TransactionCase):

    def setUp(self, *args, **kwargs):
        """setUp"""
        super().setUp(*args, **kwargs)
        print("Run setUp")

    def test_hello_world(self):
        """test_hello_world"""
        self.assertEqual(0, 0, "test hello world")

    def test_datetime_validation(self):
        """test_datetime_validation"""
        values = {
            'name': 'hello',
            'start_datetime': '2020-02-01',
            'stop_datetime': '2020-01-01',
        }
        with self.assertRaises(ValidationError):
            print("Validation Error")
            print(values)
