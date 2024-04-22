
from seleniumwire import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
import pickle, os
from os import path, remove
from time import sleep
import requests

MOODLE_WEB_LOGIN = "https://escuela-idiomas-militar.com/login/index.php"
MOODLE_WEB_BASE = "https://escuela-idiomas-militar.com"
MOODLE_CONFERENCES_2 = "https://escuela-idiomas-militar.com/mod/folder/view.php?id=1358"
MOODLE_CONFERENCES_1 = "https://escuela-idiomas-militar.com/course/view.php?id=27"
FOLDER_PATH = "./media_files"
FOLDER_SESSIONS = "./sessions"

def login(username, password):
    cookie_name = f"{username}_firefox_cookie.pkl"
    is_logged = False

    # Create a Selenium Firefox driver with authenticated proxy
    try:
        driver = webdriver.Firefox()
    except Exception as e:
        print(f"Problems creating selenium driver. Exception: {e}")

    # Login in hushed loop
    while not is_logged:
        driver.get(MOODLE_WEB_LOGIN)
        sleep(5)

        if path.exists(cookie_name):
            # Load cookie and put in the driver
            cookies = pickle.load(open(cookie_name, "rb"))
            for cookie in cookies:
                driver.add_cookie(cookie)

            driver.get(MOODLE_WEB_BASE)
            sleep(5)

        try:
            driver.find_element(By.CSS_SELECTOR, "span[class='userbutton']")
            print("Already logged in Moodle")
            is_logged = True
        except NoSuchElementException:

            driver.get(MOODLE_WEB_LOGIN)
            sleep(5)
            # If there's not an exception, there is a login form. We need to remove the old cookie and log in.
            if path.exists(cookie_name):
                print("Session expired. Removing cookie file and Logging again...")
                remove(cookie_name)

            sleep(3)
            try:
                # Put user/pass
                username_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Username']")
                password_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Password']")
                username_input.send_keys(username)
                sleep(1)
                password_input.send_keys(password)
                sleep(5)

            except NoSuchElementException:
                print("Website did not load, reloading page")
                continue

            # Press submit button
            sleep(5)
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            sleep(5)

            # Store the cookie for the next login and consider login done
            pickle.dump(driver.get_cookies(), open(cookie_name, "wb"))
            is_logged = True
            print("Logged in Moodle")

        # Check if it's logged again (search only logged class)
        try:
            driver.find_element(By.CSS_SELECTOR, "span[class='userbutton']")
        except NoSuchElementException:
            print("Logging unsuccessful, banned. Try again in 5 minutes")

    return driver

def get_vimeo_video_by_title(driver, title):
    driver.get(MOODLE_CONFERENCES_2)
    # Find all iframes on the page
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for iframe in iframes:
        # Check if the iframe's title attribute contains the provided title
        iframe_title = iframe.get_attribute('title')
        print("title is", iframe_title.lower())
        print("fo tind", title.lower())
        if title.lower() in iframe_title.lower():
            print("Found")
            src = iframe.get_attribute('src')
            if 'vimeo' in src:
                print("Source is", src)
                return src
    return None
def download_video(url, cookies):
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])

    response = requests.get(url)
    if response.status_code == 200:
        with open('downloaded_video.mp4', 'wb') as f:
            f.write(response.content)
        print("Download successful.")
    else:
        print("Failed to download the video.")

def main_menu():
    print("""
                          .___.__                     __                .__                
  _____   ____   ____   __| _/|  |   ____     _______/  |_  ____ _____  |  |   ___________ 
 /     \ /  _ \ /  _ \ / __ | |  | _/ __ \   /  ___/\   __\/ __ \\__  \ |  | _/ __ \_  __ \
|  Y Y  (  <_> |  <_> ) /_/ | |  |_\  ___/   \___ \  |  | \  ___/ / __ \|  |_\  ___/|  | \/
|__|_|  /\____/ \____/\____ | |____/\___  > /____  > |__|  \___  >____  /____/\___  >__|   
      \/                   \/           \/       \/            \/     \/          \/    
      
      
                """)

    while True:

        print("\n")
        print("1. Video from date")
        print("0. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            # Get user input for start and end dates
            username = input("Enter the username: ")
            password = input("Enter the password: ")
            date_input = input("Enter the date (DD/MM/YYY): ")
            driver = login(username, password)
            source = get_vimeo_video_by_title(driver, date_input)
            if source is not None:
                download_video(source, driver.get_cookies())



if __name__ == "__main__":
    if not os.path.exists(FOLDER_PATH):
        # Create the directory
        os.makedirs(FOLDER_PATH)
    main_menu()