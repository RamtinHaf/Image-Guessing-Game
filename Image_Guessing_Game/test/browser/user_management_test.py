import unittest
from app import app, query_db
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# import testhelper as helper

URL = "localhost:5000"

class UserManagement(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome()
    
    def test_can_create_user_and_log_in(self):
        driver = self.driver
        driver.get(URL)
        driver.implicitly_wait(1)
    
        username = "testmctest"
        password = "A1.aaaaa"

        # Register
        username_input = driver.find_element_by_id("register-username")
        username_input.send_keys(username)
        password_input = driver.find_element_by_id("register-password")
        password_input.send_keys(password)
        password_confirm_input = driver.find_element_by_id("register-confirm_password")
        password_confirm_input.send_keys(password)

        register_submit = driver.find_element_by_id("register-submit")
        register_submit.click()

        # Log in
        login_username_input = driver.find_element_by_id("login-username")
        login_username_input.send_keys(username)
        login_password_input = driver.find_element_by_id("login-password")
        login_password_input.send_keys(password)
        
        login_submit = driver.find_element_by_id("login-submit")
        login_submit.click()

        # TODO: Something less broad.
        assert username in driver.page_source

        # Delte created user
        with app.app_context():
            query_db("delete FROM Users WHERE Users.username = 'testmctest'")

    def tearDown(self):
        self.driver.close()

if __name__== "__main__":
    unittest.main()
