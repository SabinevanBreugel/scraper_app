import re
import time
import logging
from datetime import datetime 
from functions.database import Database
from functions.base_scraper import BaseScraper
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


class VacancyScraper(BaseScraper):
    def __init__(self, env="dev", headless=False):
        self.db = Database()
        self.env = env
        self.headless = headless
        self.max_retries = 10
        self.url_count=0
        self.table_name = "nationalevacaturebank"
        self.run_date = datetime.today().date()
        self.base_url = "https://www.nationalevacaturebank.nl/vacatures/functie/"
        print(f"Running on env: {env}")
    
    def start(self):
        self.create_db_table()
        logging.info("Started scraping")
        self.create_driver()
        logging.info("Driver created")
        
        #FOr loop hier bouwen
        search_title = "softwareontwikkelaar"
        self.search_for_function_title(search_title)

        #Voor alle nieuwe vacatures, zoek tekst op en haal zoekwoorden eruit 
        # Daarna wegschrijven 
        self.driver.quit()
    
    def create_db_table(self):
        logging.info("Creating table if not exists")
        vacancy_table_query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            vacancy_id VARCHAR(255) PRIMARY KEY,
            placing_date VARCHAR(55),
            search_title VARCHAR(155) NOT NULL,
            url VARCHAR(255) NOT NULL,
            function_title VARCHAR(100) NOT NULL,
            company VARCHAR(100) NOT NULL,
            city VARCHAR(55) NOT NULL,
            salary VARCHAR(55),
            hours VARCHAR(55),
            education_level VARCHAR(55),
            salary_estimated BOOL,
            run_date DATE,
            PRIMARY KEY (vacancy_id, placing_date)
        );
        """
        self.db.insert_data(vacancy_table_query)
        logging.info("Database base table created")

        vacancy_details_query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            vacancy_id VARCHAR(255) PRIMARY KEY,
            url VARCHAR(255) NOT NULL,
            function_title VARCHAR(100) NOT NULL,
            function_text VARCHAR()
            PRIMARY KEY (vacancy_id)
        );
        """
        #TO DO: beslissen welke velden & restricties

    def create_driver(self):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        if self.headless == True:
            options.add_argument("--headless")

        # We want to use the remote Webdriver if we run in production/docker container
        if self.env == "prod":
            for i in range(self.max_retries):
                try: 
                    self.driver = webdriver.Remote(
                        command_executor="http://selenium:4444/wd/hub",
                        options=options
                    )
                    break
                except WebDriverException as e:
                    print(f"Selenium is not yet available, trying again. {i+1}/{self.max_retries}")
            else:
                raise RuntimeError("Selenium did not start on time")
        
        # We use our local Chrome Webdriver when running in dev
        else:
            self.driver = webdriver.Chrome(options=options)

        self.driver.delete_all_cookies()
        self.wait = WebDriverWait(self.driver, 5) 

    def search_for_function_title(self, search_title):
        self.open_first_page(search_title)
        if self.number_of_pages>1:
            for page in range(2, self.number_of_pages+1):
                page_url = self.base_url + "softwareontwikkelaar" + '?page=' + str(page)
                print(page_url)
                self.driver.get(page_url) 
                self.find_vacancies()
        print(f"Number of urls found: {self.url_count}, out of {self.number_of_vacancies} vacancies")
       
    def open_first_page(self, search_title):
        function_url = self.base_url + search_title
        print(f"Navigating to page: {function_url}")
        self.driver.get(function_url) 

        print("Page title:", self.driver.title)
        self.accept_privacy_statement()
        self.get_base_info()
        self.find_vacancies(search_title)

    def accept_privacy_statement(self):
        try:
            shadow_host = self.driver.find_element(By.CSS_SELECTOR, "#pg-host-shadow-root")
            shadow_root = self.driver.execute_script("return arguments[0].shadowRoot", shadow_host)
        except:
            print("shadow root not found")

        try:
            accept_button = shadow_root.find_element(By.CSS_SELECTOR, "#pg-accept-btn")
            accept_button.click()
            print("Button clicked")
            time.sleep(3)
        except:
            print("No accept button found")

    def get_base_info(self):
        try:
            self.number_of_vacancies = self.driver.find_element(By.CLASS_NAME, "nvb_totalNumberOfJobs__JHP_X").text
            print(f"Number of vacancies: {self.number_of_vacancies}")
        except NoSuchElementException:
            print("Element for number of vacancies not found")

        try:
            all_pages = self.driver.find_elements(By.CLASS_NAME, "nvb_page__ftOlF")
            page_numbers = [int(el.text) for el in all_pages if el.text and el.text.isdigit()]
            if not page_numbers:
                raise ValueError("Number of pages not found")
            self.number_of_pages = max(page_numbers) 
            print(f"Number of pages: {self.number_of_pages}")
        except ValueError:
            print("Error when looking up the number of pages")

    def classify_attributes(self, attributes):
        attributes_dict = {
            'salary': None,
            'hours': None,
            'education': None
        }

        for attribute in attributes:
            if re.search(r'[\€$]', attribute):
                attributes_dict['salary'] = attribute.strip()
            elif 'uur' in attribute:
                attributes_dict['hours'] = attribute.strip()
            else:
                attributes_dict['education'] = attribute.strip()

        return attributes_dict

    def find_vacancies(self, search_title):
        results = []
        try:
            loaded_results = self.driver.find_element(By.CSS_SELECTOR, ".nvb_searchResults__3hm4V.nvb_searchResults__ADMc2")
            li_elements = loaded_results.find_elements(By.TAG_NAME, "li")
            for result in li_elements:
                try:
                    result_element = result.find_element(By.TAG_NAME, "a")
                    url = result_element.get_attribute("href")
                    if not url:
                        print("element does not contain a url")
                        continue
                    self.url_count+=1
                    vacancy_id = url.split('/')[4]
                    function_title = result.text.splitlines()[0]
                    company = result.text.splitlines()[1]
                    city = result.text.splitlines()[2]
                    print(f"Vacancy: {function_title}, {company}, {city}")
                    try:
                        all_attributes = result.find_element(By.CLASS_NAME, "nvb_attributes__IP60d")
                    except NoSuchElementException:
                        print("Could not find the element for all attributes")
                    try:
                        all_attributes.find_element(By.CLASS_NAME, "nvb_info__c_6p4")
                        salary_est = True
                    except:
                        salary_est = False
                    attributes_dict = self.classify_attributes(all_attributes.text.splitlines())

                    vacancy_data = {
                        "vacancy_id": vacancy_id,
                        "placing_date": result.text.splitlines()[-1],
                        "search_title": search_title,
                        "url": url,
                        "function_title": function_title,
                        "company": company,
                        "city": city,
                        "salary": attributes_dict.get("salary"),
                        "hours": attributes_dict.get("hours"),
                        "education_level": attributes_dict.get("education"),
                        "salary_estimated": salary_est
                    }
                    results.append(vacancy_data)
                except Exception as e:
                    print(f"Error: {e}")
                    continue
        except NoSuchElementException:
            print("Could not find the results element")
        except:
            print("Could not load results")
        
        df = pd.DataFrame(results)
        df['run_date'] = self.run_date 
        
        self.db.write_df(df, self.table_name)
