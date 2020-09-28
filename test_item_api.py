from unittest import TestCase
from item_api import ItemAPI
from item_model import Item
from flask import request

from app import app, db

app.testing = True


class ItemAPITests(TestCase):

    def setUp(self):
        # Create the Item table for each test
        db.create_all()

        # I needed an item to exist for each test.
        # An interesting note here: before I had a tearDown method,
        # this would create an item for each test, meaning the unique=True
        # for item_id wasn't properly working.
        with app.test_client() as test_client:
            test_client.post(
                '/',
                json={
                    "item_id": "1",
                    "item_name": "Clock",
                    "item_description": "Tells time."
                })

            self.item = ItemAPI()
            self.test_item = self.item.post()

        # I was having an issue with the context missing from a lot of tests
        # and rather using with statements in each test, pushing the context
        # like this makes it so the with statements aren't always necessary.
        app_context = app.app_context()
        app_context.push()

    def tearDown(self):
        # Tear down after we're done executing test.
        db.session.remove()
        db.drop_all()

    ##################################################################

    # ItemAPI.get tests

    ##################################################################

    def test_get_handles_invalid_item_id(self):
        # Given an invalid item_id, make sure we get the expected result.
        # This will fail every time because query_item will have none for each of its values.

        expected = {"status": "failed", "error_message": "The item id is not valid."}

        item = ItemAPI()

        # Testing int because the Item model expects a string.
        # This might fail if the db model doesn't stringify ints.
        self.assertEqual(item.get(12), expected)
        # Testing an item_id greater than 8 characters
        # This will fail, likely due to an empty queryset being returned.
        self.assertEqual(item.get("102945030"), expected)
        # Testing not a number
        # This will fail because an empty queryset will return. Test might not be valid.
        self.assertEqual(item.get("twelve"), expected)

    ##################################################################

    # ItemAPI.put tests

    ##################################################################

    def test_put_updates_item_with_expected_info(self):
        # Given a valid name from a form, verify the response json is accurate.

        # Mock the form request data
        with app.test_request_context('/'):
            request.form = {
                "item_name": "Watch",
                "item_description": "Tells time in a different way."
            }

            item = ItemAPI()
            actual = item.put(1)

            expected = {"id": 1,
                        "item_id": "1",
                        "item_name": "Watch",
                        "item_description": "Tells time in a different way."
                        }

            # Test that the json results are what's expected
            self.assertEqual(actual.json['result'], expected)

            # Make a database query for the item
            query_item = Item.query.filter(Item.item_id == 1).first()

            # Do we get the correct item name?
            self.assertEqual(query_item.item_name, "Watch")
            # Do we get the correct description?
            self.assertEqual(query_item.item_description, "Tells time in a different way.")

    def test_put_handles_None_value(self):
        # If we get None for item_name, does the method handle it gracefully?

        with app.test_request_context('/'):
            request.form = {
                "item_name": None,
                "item_description": "Tells time in a different way."
            }

            item = ItemAPI()
            actual = item.put(1)

        # We would expect a different status and an error message for a DB failure
        expected = {"status": "failed", "error_message": "Updates were not committed."}

        self.assertEqual(actual.json, expected)

    ##################################################################

    # ItemAPI.post tests

    ##################################################################

    def test_post_returns_expected_results(self):
        # Given a valid data, check if we get success.

        self.assertEqual(self.test_item.status, "200 OK")

    def test_post_item_was_added_to_db(self):
        # Given updates to an item, check the database if the item contains
        # the new data.

        query_item = Item.query.filter(Item.item_id == 1).first()

        self.assertEqual(query_item.item_id, "1")
        self.assertEqual(query_item.item_name, "Clock")
        self.assertEqual(query_item.item_description, "Tells time.")

    def test_post_handles_db_exception(self):
        # I ran out of time before I could properly figure out how to mock
        # the database to return an exception. I know it would fail because
        # there's no logic to handle exceptions.

        expected = {"status": "failed", "error_message": "Updates were not committed."}

        self.assertEqual(self.test_item.status, expected)

    ##################################################################

    # ItemAPI.delete tests

    ##################################################################

    def test_delete_returns_success_for_valid_item(self):
        # Given a valid item_id for deletion, test the expected status returned

        actual = self.item.delete(1)

        self.assertEqual(actual.status, "200 OK")

    def test_delete_deleted_valid_item(self):
        # Delete the item, then query for the item_id that was deleted.

        self.item.delete(1)

        query_item = Item.query.filter(Item.item_id == 1).first()

        self.assertEqual(query_item, None)

    def test_delete_returns_expected_status_when_invalid_item(self):
        # Did we get the correct status when a delete fails?
        # This will pass because the delete method doesn't care whether it
        # actually deleted something.

        actual = self.item.delete("100")

        self.assertEqual(actual.status, "200 OK")

    def test_delete_handles_db_exception(self):
        # Another test for db exceptions that I wasn't able to get to.
        # If we did get an exception from the db, this would fail.

        item = ItemAPI()
        actual = item.delete("26")

        expected = {"status": "failed", "error_message": "Couldn't connect to the database."}

        self.assertEqual(actual.json, expected)
