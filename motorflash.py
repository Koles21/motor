import time
import pandas as pd
from pandas.core.arrays.categorical import contains
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import requests
import os

from bs4 import BeautifulSoup
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Function to download image and save it to the specified subfolder
def download_image(image_url, folder_name, image_name):
    try:
        # Make a GET request to the image URL
        img_data = requests.get(image_url).content

        # Create folder if it doesn't exist
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # Save the image
        with open(os.path.join(folder_name, image_name), 'wb') as file:
            file.write(img_data)
            time.sleep(2)

        print(f"Image saved as {image_name}")
    except Exception as e:
        print(f"Error downloading image from {image_url}: {e}")


def scrape_car_details(url, excel_filename='car_details.xlsx'):
    chrome_options = Options()
    # chrome_options.add_argument("--headless")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(url)

    time.sleep(5)

    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    # cookies accept
    element = driver.find_element(By.CLASS_NAME, 'accept')
    element.click()
    time.sleep(2)

    car_containers = driver.find_elements(By.CLASS_NAME, 'item-listado')

    cars = []
    sublink_list = []

    for container in car_containers:
        try:
            # get sublinks
            sublinks_class = container.find_element(By.CLASS_NAME, "swiper-slide-active")
            link = sublinks_class.find_element(By.TAG_NAME, "a")
            sublinks_subpage = link.get_attribute("href")
            sublink_list.append(sublinks_subpage)

            # get car Ref_id
            # li_element = container.find_element(By.XPATH, "//li[starts-with(normalize-space(text()), 'Ref:')]")

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
                'Year': year,
                'sublink_page': sublinks_subpage,
                # 'ref_id': li_element.text,
                'ref_id_test': sublinks_subpage.split('/')[-2]
            })
        except Exception as e:
            print(f"Error processing a car listing: {e}")

    driver.quit()

    df = pd.DataFrame(cars)
    print(f"Saved {len(df)} cars to car_details.csv")
    df.to_csv('car_details.csv')
    df.to_excel(excel_filename, index=False)
    print(f"Saved {len(cars)} cars to {excel_filename}")

    return cars, sublink_list


def save_images(list_links):
    i = 1
    chrome_options = Options()
    # chrome_options.add_argument("--headless")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    for link in list_links:
        driver.get(link)
        time.sleep(1)

        try:
            driver.refresh()
            time.sleep(2)
            # Wait for the lazyloaded image to be present on the page
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "lazyloaded"))
            )
            print("Page fully loaded with the lazyloaded image.")
            driver.refresh()
            time.sleep(6)
        except Exception as e:
            print('ovde sam za: ')
            driver.refresh()
            time.sleep(2)
            print(f"Error: {e}")

        if i >= 3:
            pass
        else:

            try:
                element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'accept'))
                )
                element.click()
                i += 1

            except Exception as e:
                print("No cookie banner found or other issue:", e)

        time.sleep(2)

        ref_id = link.split('/')[-2].split('-')[0]

        ancla = driver.find_element(By.ID, "ancla-galeria")
        element = ancla.find_element(by="xpath", value='//div[@class="swiper-wrapper" and @id="gallery"]')
        html_content = element.get_attribute("innerHTML")

        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        # Find all <source> elements
        source_elements = soup.find_all('source')
        image_urls = []
        for source in source_elements:
            data_srcset = source.get('data-srcset')
            if data_srcset:
                # Split the 'data-srcset' into individual URLs
                for item in data_srcset.split(','):
                    if "size=1400" in item and "2x" in item and 'format=webp' in item:
                        url = item.strip().split()[0]  # Extract the URL part
                        image_urls.append(url)

        folder_name = f"downloaded_images_{ref_id}"

        # Print the filtered image URLs
        for index, img in enumerate(image_urls):
            image_name = f"image_{ref_id}_{index + 1}.jpg"

            download_image(img, folder_name, image_name)


# Example usage
url = 'https://www.motorflash.com/coches-de-segunda_mano/audi/'
results, list_sublinks1 = scrape_car_details(url)

list_sublinks = [
    'https://exclusive.motorflash.com/aspexclusive/coche-de-segunda_mano/audi-q2-sport_35_tfsi_110_kw_150_cv_s_tronic/ocasion/56272341-es/',
    'https://exclusive.motorflash.com/coche-de-segunda_mano/audi-q2-s_line_30_tfsi_81_kw_110_cv/ocasion/61679406-es/',
    'https://exclusive.motorflash.com/coche-de-segunda_mano/audi-q3-black_line_35_tfsi_110_kw_150_cv_s_tronic/ocasion/61679199-es/',
    'https://exclusive.motorflash.com/coche-de-segunda_mano/audi-sq5_sportback-tdi_quattro_251_kw_341_cv/ocasion/61679187-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-q5_sportback_tfsie-black_line_55_tfsi_e_quattro_ultra_270_kw_367_cv/ocasion/61679151-es/',
    'https://exclusive.motorflash.com/aspexclusive/coche-de-segunda_mano/audi-q5-s_line_40_tdi_quattro_ultra_150_kw_204_cv_s_tronic/ocasion/57255789-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-q4_sportback_e_tron-black_line_edition_40_e_tron_82kwh_150_kw_204_cv/ocasion/61679109-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-a1_sportback-adrenalin_edition_30_tfsi_81_kw_110_cv_s_tronic/ocasion/61678071-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-a1_sportback-adrenalin_25_tfsi_70_kw_95_cv/ocasion/61678047-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-a4-black_line_35_tdi_120_kw_163_cv_s_tronic/ocasion/61678029-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-q5_sportback-advanced_40_tdi_quattro_ultra_150_kw_204_cv_s_tronic/ocasion/61488105-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-a3_sportback-genuine_edition_35_tdi_110_kw_150_cv_s_tronic/ocasion/61488060-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-q5-attraction_2_0_tdi_clean_diesel_quattro_140_kw_190_cv_s_tronic/ocasion/61487973-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-a3_sportback-genuine_edition_35_tdi_110_kw_150_cv/ocasion/61487838-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-a3_sportback-s_line_35_tdi_110_kw_150_cv_s_tronic/ocasion/61487835-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-a1_sportback-adrenalin_black_edition_30_tfsi_81_kw_110_cv_s_tronic/ocasion/61487772-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-q3_tfsie-advanced_45_tfsi_e_180_kw_245_cv_s_tronic/ocasion/61487733-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-q3_tfsie-advanced_45_tfsi_e_180_kw_245_cv_s_tronic/ocasion/61487700-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-q2-adrenalin_30_tdi_85_kw_116_cv_s_tronic/ocasion/61487697-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-q2-design_30_tdi_85_kw_116_cv_s_tronic/ocasion/61487676-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-q2-s_line_30_tdi_85_kw_116_cv/ocasion/61487556-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-q2-adrenalin_35_tfsi_110_kw_150_cv_s_tronic/ocasion/61487478-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-q2-s_line_30_tdi_85_kw_116_cv/ocasion/61486344-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-q2-s_line_30_tdi_85_kw_116_cv/ocasion/61486263-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-q2-advanced_30_tdi_85_kw_116_cv_s_tronic/ocasion/61481676-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-q2-s_line_35_tfsi_110_kw_150_cv_s_tronic/ocasion/61481496-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-q2-s_line_30_tdi_85_kw_116_cv_s_tronic/ocasion/61481376-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-a3_sportback_tfsie-s_line_40_tfsi_e_150_kw_204_cv_s_tronic/ocasion/61481349-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-a3_sportback_tfsie-s_line_40_tfsi_e_150_kw_204_cv_s_tronic/ocasion/61481346-es/',
    'https://www.motorflash.com/coche-de-segunda_mano/audi-a3_sportback_tfsie-genuine_edition_40_tfsi_e_150_kw_204_cv_s_tronic/ocasion/61481340-es/']

save_images(list_sublinks1)

# todo
# napraviti while loop za .nxtpage dugme da bi izlistao sve stranice i poskidao elemente
