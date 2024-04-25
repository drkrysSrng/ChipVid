from seleniumwire import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import re
import ffmpeg
from time import sleep
import requests


def login(username, password, url_login):
    try:
        firefox_options = Options()
        firefox_options.add_argument("-headless")
        driver = webdriver.Firefox(options=firefox_options)
    except Exception as e:
        print(f"Problems creating selenium driver. Exception: {e}")
        return

    driver.get(url_login)
    sleep(5)

    try:
        # Put user/pass
        username_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Username']")
        password_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Password']")
        username_input.send_keys(username)
        sleep(1)
        password_input.send_keys(password)
        sleep(1)

    except NoSuchElementException:
        print("Website did not load, reloading page")

    # Press submit button
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    sleep(5)

    print("Logged in Moodle")

    # Check if it's logged again (search only logged class)
    try:
        driver.find_element(By.CSS_SELECTOR, "span[class='userbutton']")
    except NoSuchElementException:
        print("Logging unsuccessful, change credentials")

    sleep(2)

    return driver


def get_vimeo_video_by_title(driver, title, url_videos):
    found_links = []
    found_video = ""
    found_audio = ""
    download_video_url = ""
    download_audio_url = ""

    print("Getting vimeo videos")
    driver.get(url_videos)
    sleep(31
          )

    # Regex pattern to find URLs
    url_pattern = re.compile(r'https://120vod-adaptive\.akamaized\.net/.*?/master\.json')

    # Find all iframes on the page
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for index, iframe in enumerate(iframes):
        # Check if the iframe's title attribute contains the provided title
        iframe_title = iframe.get_attribute('title')
        print("title iframe", iframe_title.lower())
        print("fo tind", title.lower())
        if title.lower() in iframe_title.lower():
            print("title is", iframe_title.lower())
            print("******Found", iframe_title.lower())

            driver.switch_to.frame(index)

            scripts = driver.find_elements(By.TAG_NAME, "script")

            # Extract URLs from each script's content
            for script in scripts:
                script_content = script.get_attribute('innerHTML')
                matches = url_pattern.findall(script_content)
                print("script_content", script_content)
                found_links.extend(matches)

            # Switch back to the main document
            driver.switch_to.default_content()
            break

    for link in found_links:
        print("Link found=>", link)
        # Fetch the JSON data
        response = requests.get(link)
        if response.status_code == 200:
            json_data = response.json()

            # Traverse through the JSON looking for 'video' elements
            if 'video' in json_data:
                for video in json_data['video']:
                    if isinstance(video, dict) and 'base_url' in video:
                        if video['width'] == 1920:
                            # Regex to capture the required part of the URL
                            match = re.search(r'video/(.*?\.mp4)', video['base_url'])
                            if match:
                                found_video = match.group(0)

            # Traverse through the JSON looking for 'video' elements
            if 'audio' in json_data:
                for video in json_data['audio']:
                    if isinstance(video, dict) and 'base_url' in video:
                        if video['avg_bitrate'] == 194000:
                            # Regex to capture the required part of the URL
                            match = re.search(r'audio/(.*?\.mp4)', video['base_url'])
                            if match:
                                found_audio = match.group(0)

        download_video_url = re.sub(r'/sep/video.*', '/parcel/', link) + found_video
        print(f"Downloading video from: {download_video_url}")

        download_audio_url = re.sub(r'/sep/video.*', '/parcel/', link) + found_audio
        print(f"Downloading audio from: {download_audio_url}")
        break

    return download_video_url, download_audio_url


def download_video(url, title):
    response = requests.get(url)
    if response.status_code == 200:
        print("Downloading video from", url)
        print("Destination", title)
        with open(f"{title}", 'wb') as f:
            f.write(response.content)
        print("Download successful.")
    else:
        print("Failed to download the video.")


def combine_video_audio(video_path, audio_path, output_path):
    input_video = ffmpeg.input(video_path)
    input_audio = ffmpeg.input(audio_path)
    ffmpeg.concat(input_video, input_audio, v=1, a=1).output(output_path).run()


def main_menu():
    print("""
    
_________ .__    .__     ____   ____.__    .___
\_   ___ \|  |__ |__|____\   \ /   /|__| __| _/
/    \  \/|  |  \|  \____ \   Y   / |  |/ __ | 
\     \___|   Y  \  |  |_> >     /  |  / /_/ | 
 \______  /___|  /__|   __/ \___/   |__\____ | 
        \/     \/   |__|                    \/ 

    
                """)

    while True:

        print("\n")
        print("1. Video from title")
        print("0. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":

            title = input("Enter the title of the video[DD/MM/YYYY] : ")
            url_login = input("Enter the url of the login page: ")
            url_conferences = input("Enter the url where the conferences are: ")
            username = input("Enter the username: ")
            password = input("Enter the password: ")

            # Get user input for start and end dates
            driver = login(username, password, url_login)

            source_video, source_audio = get_vimeo_video_by_title(driver, title, url_conferences)

            filename = title.replace("/", "_")
            if len(source_video) > 0:
                download_video(source_video, f"{filename}_video.mp4")

            if len(source_audio) > 0:
                download_video(source_audio, f"{filename}_audio.mp4")

            sleep(3)
            try:
                combine_video_audio(f"{filename}_video.mp4", f"{filename}_audio.mp4", f"{filename}_final.mp4")
                print("The video and audio were combined successfully!")
            except ffmpeg.Error as e:
                print("An error occurred:", e)

            # Close the driver
            driver.quit()


if __name__ == "__main__":
    main_menu()
