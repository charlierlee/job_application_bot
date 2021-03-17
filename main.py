from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import time
import sqlite3
import pandas as pd

def main():
    con = sqlite3.connect('./example.db')

    cur = con.cursor()

    # Create table
    cur.execute('''CREATE TABLE IF NOT EXISTS bookmarks(
        jobid string,
        linktext string,
        UNIQUE(jobid)
    )
    ''')
    

    # Save (commit) the changes
    con.commit()

    


    ACCOUNT_EMAIL = ""
    ACCOUNT_PASSWORD = ""
    

    chrome_driver_path = "/home/alice/git3/job_application_bot/chromedriver"
    options = webdriver.ChromeOptions()
    options.add_argument("--user-data-dir=/home/alice/.config/google-chrome")

    driver = webdriver.Chrome(options=options,
                                executable_path=chrome_driver_path)

    driver.get("https://www.linkedin.com/jobs/search/?f_JT=P&f_WRA=true&geoId=104145663&keywords=machine%20learning&location=Redmond%2C%20Washington%2C%20United%20States")

    try:
        sign_in_button = driver.find_element_by_link_text("Sign in")
        sign_in_button.click()

        time.sleep(2)

        # sign in
        username_input = driver.find_element_by_id("username")
        username_input.send_keys(ACCOUNT_EMAIL)
        password_input = driver.find_element_by_id("password")
        password_input.send_keys(ACCOUNT_PASSWORD)
        password_input.send_keys(Keys.ENTER)

        time.sleep(20)
    except NoSuchElementException:
        print("Already logged in")
        
    all_listings = driver.find_elements_by_css_selector(
        ".job-card-container--clickable")
    loop(con,cur,driver, all_listings)
    
    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    con.close()

    time.sleep(5)
def loop(con,cur, driver, all_listings):
    df = pd.read_sql_query("SELECT * FROM bookmarks ORDER BY jobid", con)

    # Verify that result of SQL query is stored in the dataframe
    print(df.head())
    for listing in all_listings:
        if not df['jobid'].astype(str).str.contains(str(listing.get_attribute("data-job-id"))).any():
            cur.execute('INSERT OR IGNORE INTO bookmarks(jobid,linktext) VALUES(\'' + str(listing.get_attribute("data-job-id")) + '\',\'' + listing.text + '\')')
            con.commit()
            print('writing value')
            listing.click()
            time.sleep(2)

            # Try to locate the apply button, if can't locate then skip the job.
            try:
                apply_button = driver.find_element_by_css_selector(
                    ".jobs-s-apply button")
                apply_button.click()
                time.sleep(5)

                # If phone field is empty, then fill your phone number.
                phone = driver.find_element_by_class_name("fb-single-line-text__input")
                PHONE = ""
                if phone.text == "":
                    phone.send_keys(PHONE)

                submit_button = driver.find_element_by_css_selector("footer button")

                # If the submit_button is a "Next" button, then this is a multi-step application, so skip.
                if submit_button.get_attribute("data-control-name") == "continue_unify":
                    close_button = driver.find_element_by_class_name(
                        "artdeco-modal__dismiss")
                    close_button.click()
                    time.sleep(2)
                    discard_button = driver.find_elements_by_class_name(
                        "artdeco-modal__confirm-dialog-btn")[1]
                    discard_button.click()
                    print("Complex application, skipped.")
                    continue
                else:
                    submit_button.click()

                # Once application completed, close the pop-up window.
                time.sleep(2)
                close_button = driver.find_element_by_class_name(
                    "artdeco-modal__dismiss")
                close_button.click()

            # If already applied to job or job is no longer accepting applications, then skip.
            except NoSuchElementException:
                print("No application button, skipped.")
                continue
    time.sleep(300)
    # caution. Will stack overflow eventually
    loop(con,cur,driver, all_listings)
main()