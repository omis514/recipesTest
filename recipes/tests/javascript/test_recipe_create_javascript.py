"""Tests for JavaScript functionality on the recipe create page using Selenium."""

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from recipes.models import User
from recipes.tests.helpers import LogInTester


class RecipeCreateJavaScriptTestCase(StaticLiveServerTestCase, LogInTester):
    """Tests for JavaScript functionality on recipe create page."""

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    @classmethod
    def setUpClass(cls):
        """Set up ChromeDriver for tests."""
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
        """Set up test data and login."""
        self.user = User.objects.get(username="@johndoe")
        self.url = self.live_server_url + reverse("recipe_create")

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

    def scroll_to_element(self, element):
        """Scroll element into view."""
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        WebDriverWait(self.driver, 2).until(lambda d: element.is_displayed())

    def click_element(self, element):
        """Click element, scrolling into view first and using JS click if needed."""
        self.scroll_to_element(element)
        try:
            element.click()
        except Exception:
            # Fallback to JavaScript click if regular click fails
            self.driver.execute_script("arguments[0].click();", element)

    def test_add_ingredient_button_creates_new_form(self):
        """Test that clicking 'Add Ingredient' button creates a new ingredient form."""
        self.driver.get(self.url)

        # Wait for page to load and JavaScript to initialize
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "add-ingredient"))
        )
        # Wait for DOM to be ready
        WebDriverWait(self.driver, 5).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Count initial forms (should have at least 1)
        initial_forms = len(
            self.driver.find_elements(By.CLASS_NAME, "ingredient-form-row")
        )
        self.assertGreaterEqual(initial_forms, 1)

        # Get total forms input value
        total_forms_input = self.driver.find_element(
            By.CSS_SELECTOR, "#id_ingredients-TOTAL_FORMS"
        )
        initial_total = int(total_forms_input.get_attribute("value"))

        # Click add ingredient button
        add_button = self.driver.find_element(By.ID, "add-ingredient")
        self.click_element(add_button)

        # Wait for new form to appear
        WebDriverWait(self.driver, 5).until(
            lambda d: len(d.find_elements(By.CLASS_NAME, "ingredient-form-row"))
            > initial_forms
        )

        # Check that new form was added
        new_forms = len(self.driver.find_elements(By.CLASS_NAME, "ingredient-form-row"))
        self.assertEqual(new_forms, initial_forms + 1)

        # Check that TOTAL_FORMS was updated
        new_total = int(total_forms_input.get_attribute("value"))
        self.assertEqual(new_total, initial_total + 1)

    def test_remove_ingredient_button_hides_form(self):
        """Test that clicking remove ingredient button hides the form."""
        self.driver.get(self.url)

        # Wait for page to load and JavaScript to initialize
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "add-ingredient"))
        )
        WebDriverWait(self.driver, 5).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Add an ingredient first
        add_button = self.driver.find_element(By.ID, "add-ingredient")
        self.click_element(add_button)

        # Wait for form to be added
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".ingredient-form-row:last-child .remove-ingredient")
            )
        )

        forms = self.driver.find_elements(By.CLASS_NAME, "ingredient-form-row")
        self.assertGreater(len(forms), 1, "Should have at least 2 forms")

        # Get the last form
        last_form = forms[-1]
        remove_button = last_form.find_element(By.CSS_SELECTOR, ".remove-ingredient")

        # Click remove button
        self.click_element(remove_button)

        # Wait for form to be hidden
        WebDriverWait(self.driver, 5).until(
            EC.invisibility_of_element_located(last_form)
        )

        # Check that form is hidden
        self.assertEqual(last_form.value_of_css_property("display"), "none")

    def test_add_instruction_button_creates_new_form(self):
        """Test that clicking 'Add instruction' button creates a new instruction form."""
        self.driver.get(self.url)

        # Wait for page to load and JavaScript to initialize
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "add-instruction"))
        )
        WebDriverWait(self.driver, 5).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Count initial forms
        initial_forms = len(
            self.driver.find_elements(By.CLASS_NAME, "instruction-form-row")
        )

        # Get total forms input value
        total_forms_input = self.driver.find_element(
            By.CSS_SELECTOR, "#id_instructions-TOTAL_FORMS"
        )
        initial_total = int(total_forms_input.get_attribute("value"))

        # Click add instruction button
        add_button = self.driver.find_element(By.ID, "add-instruction")
        self.click_element(add_button)

        # Wait for new form to appear
        WebDriverWait(self.driver, 5).until(
            lambda d: len(d.find_elements(By.CLASS_NAME, "instruction-form-row"))
            > initial_forms
        )

        # Check that new form was added
        new_forms = len(
            self.driver.find_elements(By.CLASS_NAME, "instruction-form-row")
        )
        self.assertEqual(new_forms, initial_forms + 1)

        # Check that TOTAL_FORMS was updated
        new_total = int(total_forms_input.get_attribute("value"))
        self.assertEqual(new_total, initial_total + 1)

    def test_remove_instruction_button_hides_form(self):
        """Test that clicking remove instruction button hides the form."""
        self.driver.get(self.url)

        # Wait for page to load and JavaScript to initialize
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "add-instruction"))
        )
        WebDriverWait(self.driver, 5).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Add an instruction first
        add_button = self.driver.find_element(By.ID, "add-instruction")
        self.click_element(add_button)

        # Wait for form to be added
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    ".instruction-form-row:last-child .remove-instruction",
                )
            )
        )

        forms = self.driver.find_elements(By.CLASS_NAME, "instruction-form-row")
        self.assertGreater(len(forms), 1, "Should have at least 2 forms")

        # Get the last form
        last_form = forms[-1]
        remove_button = last_form.find_element(By.CSS_SELECTOR, ".remove-instruction")

        # Click remove button
        self.click_element(remove_button)

        # Wait for form to be hidden
        WebDriverWait(self.driver, 5).until(
            EC.invisibility_of_element_located(last_form)
        )

        # Check that form is hidden
        self.assertEqual(last_form.value_of_css_property("display"), "none")

    def test_instruction_step_numbers_renumbered(self):
        """Test that instruction step numbers are correctly renumbered when forms are removed."""
        self.driver.get(self.url)

        # Wait for page to load and JavaScript to initialize
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "add-instruction"))
        )
        WebDriverWait(self.driver, 5).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Add multiple instructions
        add_button = self.driver.find_element(By.ID, "add-instruction")
        for _ in range(3):
            self.click_element(add_button)
            WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".instruction-form-row:last-child")
                )
            )

        # Get all visible forms
        all_forms = self.driver.find_elements(By.CLASS_NAME, "instruction-form-row")
        visible_forms = [
            f for f in all_forms if f.value_of_css_property("display") != "none"
        ]

        # Verify initial numbering
        for i, form in enumerate(visible_forms, 1):
            step_number = form.find_element(By.CSS_SELECTOR, ".instruction-step-number")
            self.assertEqual(int(step_number.text), i)

        # Remove the second form
        if len(visible_forms) > 1:
            second_form = visible_forms[1]
            remove_button = second_form.find_element(
                By.CSS_SELECTOR, ".remove-instruction"
            )
            self.click_element(remove_button)

            # Wait for form to be hidden
            WebDriverWait(self.driver, 5).until(
                EC.invisibility_of_element_located(second_form)
            )

            # Wait a bit for renumbering
            WebDriverWait(self.driver, 2).until(
                lambda d: int(
                    d.find_elements(By.CLASS_NAME, "instruction-form-row")[0]
                    .find_element(By.CSS_SELECTOR, ".instruction-step-number")
                    .text
                )
                == 1
            )

            # Verify renumbering
            remaining_forms = [
                f
                for f in self.driver.find_elements(
                    By.CLASS_NAME, "instruction-form-row"
                )
                if f.value_of_css_property("display") != "none"
            ]
            expected_step = 1
            for form in remaining_forms:
                step_number = form.find_element(
                    By.CSS_SELECTOR, ".instruction-step-number"
                )
                self.assertEqual(
                    int(step_number.text),
                    expected_step,
                    f"Step should be {expected_step} but was {step_number.text}",
                )
                expected_step += 1

    def test_form_validation_prevents_empty_submission(self):
        """Test that form validation prevents submission with empty fields."""
        self.driver.get(self.url)

        # Wait for page to load and JavaScript to initialize
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[type="submit"]'))
        )
        WebDriverWait(self.driver, 5).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Try to submit empty form
        submit_button = self.driver.find_element(
            By.CSS_SELECTOR, 'button[type="submit"]'
        )
        self.click_element(submit_button)

        # Wait for alert
        try:
            WebDriverWait(self.driver, 5).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            alert.accept()

            # Should show validation error
            self.assertIn("title", alert_text.lower())
            self.assertIn("ingredient", alert_text.lower())
            self.assertIn("instruction", alert_text.lower())
        except TimeoutException:
            self.fail("Expected alert dialog for empty form submission")

    def test_clicking_spiciness_button_updates_hidden_input(self):
        """Test that clicking a spiciness button updates the hidden input value."""
        self.driver.get(self.url)

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".spiciness-btn"))
        )
        WebDriverWait(self.driver, 5).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Wait for hidden input to be present
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, "id_spiciness"))
        )

        # Find hidden input and button
        hidden_input = self.driver.find_element(By.ID, "id_spiciness")
        mild_button = self.driver.find_element(
            By.CSS_SELECTOR, ".spiciness-btn[data-level='1']"
        )

        # Verify initial value is empty
        initial_value = hidden_input.get_attribute("value") or ""
        self.assertEqual(initial_value, "", "Initial spiciness value should be empty")

        # Click the mild button
        self.click_element(mild_button)

        # Wait for value to update
        WebDriverWait(self.driver, 5).until(
            lambda d: d.find_element(By.ID, "id_spiciness").get_attribute("value")
            == "1"
        )

        # Verify hidden input was updated
        new_value = hidden_input.get_attribute("value")
        self.assertEqual(new_value, "1", "Hidden input should be updated to level 1")

    def test_cuisine_dropdown_is_selectable(self):
        """Test that the cuisine dropdown field can be selected and changed."""
        self.driver.get(self.url)

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "id_cuisine"))
        )
        WebDriverWait(self.driver, 5).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Find cuisine dropdown
        cuisine_select = self.driver.find_element(By.ID, "id_cuisine")
        self.assertIsNotNone(cuisine_select)

        # Verify it's a select element
        self.assertEqual(cuisine_select.tag_name, "select")

        # Get all options
        select = Select(cuisine_select)
        options = select.options
        self.assertGreater(len(options), 0, "Cuisine dropdown should have options")

        # Test selecting a different cuisine option
        if len(options) > 1:
            # Select the second option (index 1)
            select.select_by_index(1)

            # Verify selection was updated
            selected_value = select.first_selected_option.get_attribute("value")
            self.assertIsNotNone(selected_value)
            self.assertNotEqual(selected_value, "")

    def test_vegetarian_toggle_switch_works(self):
        """Test that the vegetarian toggle switch works correctly."""
        self.driver.get(self.url)

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "id_vegetarian"))
        )
        WebDriverWait(self.driver, 5).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Find the vegetarian toggle switch and label
        vegetarian_toggle = self.driver.find_element(By.ID, "id_vegetarian")
        vegetarian_label = self.driver.find_element(By.ID, "vegetarian-label")

        # Verify initial state (should be unchecked, showing "No")
        self.assertFalse(
            vegetarian_toggle.is_selected(),
            "Vegetarian toggle should be unchecked initially",
        )
        self.assertEqual(
            vegetarian_label.text, "No", "Vegetarian label should show 'No' initially"
        )

        # Click the toggle to turn it on
        self.click_element(vegetarian_toggle)

        # Wait for the label to update
        WebDriverWait(self.driver, 5).until(
            lambda d: d.find_element(By.ID, "vegetarian-label").text == "Yes"
        )

        # Verify it's now checked and label shows "Yes"
        self.assertTrue(
            vegetarian_toggle.is_selected(),
            "Vegetarian toggle should be checked after clicking",
        )
        self.assertEqual(
            vegetarian_label.text,
            "Yes",
            "Vegetarian label should show 'Yes' when checked",
        )

        # Click the toggle again to turn it off
        self.click_element(vegetarian_toggle)

        # Wait for the label to update
        WebDriverWait(self.driver, 5).until(
            lambda d: d.find_element(By.ID, "vegetarian-label").text == "No"
        )

        # Verify it's now unchecked and label shows "No"
        self.assertFalse(
            vegetarian_toggle.is_selected(),
            "Vegetarian toggle should be unchecked after second click",
        )
        self.assertEqual(
            vegetarian_label.text,
            "No",
            "Vegetarian label should show 'No' when unchecked",
        )
