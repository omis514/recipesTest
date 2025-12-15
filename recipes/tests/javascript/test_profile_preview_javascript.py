"""
Selenium Tests for Profile Preview Functionality.

Tests that the profile preview card updates in real-time via JavaScript
as the user types into the form fields.
"""

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from recipes.models import User


class ProfilePreviewJavaScriptTestCase(StaticLiveServerTestCase):
    """Tests for JavaScript live preview on the edit profile page."""

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    @classmethod
    def setUpClass(cls):
        """Set up ChromeDriver for headless testing."""
        super().setUpClass()
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(10)
        cls.driver.set_window_size(1920, 1080)

    @classmethod
    def tearDownClass(cls):
        """Close browser after tests."""
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        """Log in and navigate to the edit profile page."""
        self.user = User.objects.get(username="@johndoe")
        self.url = self.live_server_url + reverse("edit_profile")

        # Login via Django test client to set session cookie
        self.client.force_login(self.user)
        cookie = self.client.cookies["sessionid"]
        self.driver.get(self.live_server_url)
        self.driver.add_cookie(
            {
                "name": "sessionid",
                "value": cookie.value,
                "path": "/",
            }
        )

        # Navigate to edit profile page and wait for it to load
        self.driver.get(self.url)
        WebDriverWait(self.driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def test_preview_loads_initial_data(self):
        """Test that the preview card loads with the user's current data."""
        # Wait for preview elements to be visible
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, "preview-name"))
        )

        preview_name = self.driver.find_element(By.ID, "preview-name").text
        preview_username = self.driver.find_element(By.ID, "preview-username").text

        # Verify initial state matches database
        self.assertIn(self.user.first_name, preview_name)
        self.assertIn(self.user.last_name, preview_name)
        self.assertEqual(preview_username, self.user.username)

    def test_name_input_updates_preview_realtime(self):
        """Test that typing in First/Last name inputs updates the Full Name."""
        first_name_input = self.driver.find_element(By.ID, "id_first_name")
        last_name_input = self.driver.find_element(By.ID, "id_last_name")
        preview_name = self.driver.find_element(By.ID, "preview-name")

        # 1. Clear and Type new First Name
        first_name_input.clear()
        first_name_input.send_keys("Test123")

        # Verify JS updated the text immediately
        WebDriverWait(self.driver, 2).until(lambda d: "Test123" in preview_name.text)

        # 2. Clear and Type new Last Name
        last_name_input.clear()
        last_name_input.send_keys("TestUser")

        # Verify combined result
        WebDriverWait(self.driver, 2).until(
            lambda d: preview_name.text == "Test123 TestUser"
        )

    def test_username_input_updates_preview_realtime(self):
        """Test that typing in Username input updates the preview username."""
        username_input = self.driver.find_element(By.ID, "id_username")
        preview_username = self.driver.find_element(By.ID, "preview-username")

        username_input.clear()
        username_input.send_keys("@test_testing")

        # Wait for JS update
        WebDriverWait(self.driver, 2).until(
            lambda d: preview_username.text == "@test_testing"
        )

    def test_bio_input_updates_preview_realtime(self):
        """Test that typing in Bio textarea updates the preview bio."""
        bio_input = self.driver.find_element(By.ID, "id_bio")
        preview_bio = self.driver.find_element(By.ID, "preview-bio")

        new_bio = "This is a bio typed by an automated browser."
        bio_input.clear()
        bio_input.send_keys(new_bio)

        WebDriverWait(self.driver, 2).until(lambda d: preview_bio.text == new_bio)
