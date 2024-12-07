import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def scrape_car_details(url, excel_filename='car_details.xlsx'):
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(url)

    time.sleep(5)

    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    car_containers = driver.find_elements(By.CLASS_NAME, 'item-listado')

    cars = []
    for container in car_containers:
        try:
            title_elem = container.find_element(By.XPATH, './/p[@class="h2-style"]//a[contains(@title, "Oferta")]')
            full_title = title_elem.get_attribute('title')
            clean_title = full_title.replace("Oferta de ", "").replace(" - Vehículo usado", "")

            price_elem = container.find_element(By.XPATH, './/span[contains(@class, "precio")]')
            price = price_elem.text.strip()

            # Extract details from the "general" list
            details_list = container.find_element(By.CLASS_NAME, 'general')
            details = [item.text for item in details_list.find_elements(By.TAG_NAME, 'li')]

            fuel = details[0]
            location = details[1]
            mileage = details[2]
            year = details[3]

            cars.append({
                'Title': clean_title,
                'Price': price,
                'Fuel': fuel,
                'Location': location,
                'Mileage': mileage,
                'Year': year
            })
        except Exception as e:
            print(f"Error processing a car listing: {e}")

    driver.quit()

    df = pd.DataFrame(cars)
    df.to_excel(excel_filename, index=False)
    print(f"Saved {len(cars)} cars to {excel_filename}")

    return cars


# Example usage
url = 'https://www.motorflash.com/coches-de-segunda_mano/audi/'
results = scrape_car_details(url)