"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app, talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"

HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)
        talisman.force_https = False

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_read_an_account(self):
        """It should read an acccount"""
        account = AccountFactory()
        response = self.client.post(BASE_URL, json=account.serialize())
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            "Could not create test Account",
        )
        new_account = response.get_json()
        account.id = new_account["id"]
        response = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        r_account = response.get_json()
        self.assertEqual(r_account["name"], account.name)
        self.assertEqual(r_account["email"], account.email)
        self.assertEqual(r_account["address"], account.address)
        self.assertEqual(r_account["phone_number"], account.phone_number)
        self.assertEqual(r_account["date_joined"], str(account.date_joined))

    def test_account_not_found(self):
        """IT should return not found"""
        account_id = 0
        response = self.client.get(f"{BASE_URL}/{account_id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_account(self):
        """it should return a list of all accounts"""
        accounts = self._create_accounts(10)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        r_accounts = response.get_json()
        self.assertEqual(len(accounts), len(r_accounts))

    def test_empty_list_account(self):
        """it should return a list of all accounts"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        r_accounts = response.get_json()
        self.assertEqual(len(r_accounts), 0)

    def test_update_account(self):
        """It should Update a new account"""
        account = self._create_accounts(1)[0]
        account.name = "SIMOHAMMED ALAOUI"
        response = self.client.put(
            f"{BASE_URL}/{account.id}",
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check the data is correct
        updated_account = response.get_json()
        self.assertEqual(updated_account["name"], account.name)

    def test_update_account_not_found(self):
        """It should return account not found"""
        account = AccountFactory()
        account.id = 1
        response = self.client.put(
            f"{BASE_URL}/{account.id}",
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account(self):
        """It should delete an account"""
        accounts = self._create_accounts(10)
        account_to_delete = accounts[0]
        response = self.client.delete(f"{BASE_URL}/{account_to_delete.id}")
        new_list_accounts = Account.all()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(new_list_accounts), len(accounts) - 1)

    def test_method_not_allowed(self):
        """It should not allow an illegal method call"""
        resp = self.client.delete(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_security_headers(self):
        """It should check the security headers"""
        response = self.client.get(BASE_URL,environ_overrides=HTTPS_ENVIRON)
        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': 'default-src \'self\'; object-src \'none\'',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key,value in headers.items():
            self.assertEqual(response.headers.get(key),value)
