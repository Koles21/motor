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


def windows_scroll(driver):
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.refresh()

def cookies_popup_accept(driver):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'accept'))
        )
        element.click()


    except Exception as e:
        print("No cookie banner found or other issue:", e)


def wait_image_appearance(driver):
    try:
        # Wait for the lazyloaded image to be present on the page
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "lazyloaded"))
        )
        print("Page fully loaded with the lazyloaded image.")

    except Exception as e:
        print('ovde sam za: ')
        driver.refresh()
        time.sleep(2)
        print(f"Error: {e}")

def image_extractor(soup, source_elements):
    """
    Since there are, till now , two types of images that appears on the site.


    :param soup:
    :param source_elements:
    :return:
    """
    image_urls= []
    if len(source_elements) == 0:
        img_tags = soup.select("div.swiper-slide img")
        for img in img_tags:
            if img.get("data-src"):
                image_urls.append(img.get("data-src"))


    else:
        for source in source_elements:
            data_srcset = source.get('data-srcset')
            if data_srcset:
                # Split the 'data-srcset' into individual URLs
                for item in data_srcset.split(','):
                    if "size=1400" in item and "2x" in item and 'format=webp' in item:
                        url = item.strip().split()[0]  # Extract the URL part
                        image_urls.append(url)

    return image_urls


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

    windows_scroll(driver)
    cookies_popup_accept(driver)



    car_containers = driver.find_elements(By.CLASS_NAME, 'item-listado')

    cars = []
    sublink_list = []

    for container in car_containers:
        try:
            # get sub-links for each car
            sublinks_class = container.find_element(By.CLASS_NAME, "swiper-slide-active")
            link = sublinks_class.find_element(By.TAG_NAME, "a")
            sublinks_subpage = link.get_attribute("href")
            sublink_list.append(sublinks_subpage)

            # extract important info elements
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


def image_download_from_links(list_links):
    i = 1
    chrome_options = Options()
    # chrome_options.add_argument("--headless")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    for link in list_links:
        driver.get(link)
        time.sleep(1)
        print(f'Currently active link: {link}')

        windows_scroll(driver)
        wait_image_appearance(driver)

        if i >= 3:
            pass
        else:
            cookies_popup_accept(driver)
            i=+1

        time.sleep(1)
        # get ref-id of car to be able to map images
        ref_id = link.split('/')[-2].split('-')[0]


        # parsing sub-link page to get the main img container
        try:
            ancla = driver.find_element(By.ID, "ancla-galeria")
            element = ancla.find_element(by="xpath", value='//div[@class="swiper-wrapper" and @id="gallery"]')
        except Exception as e:
            print(f'ovde sam za {ref_id}: ')
            driver.refresh()
        html_content = element.get_attribute("innerHTML")
        soup = BeautifulSoup(html_content, 'html.parser')
        source_elements = soup.find_all('source')


        image_urls = image_extractor(soup,source_elements)

        # download each images from sub-link in given folder
        folder_name = f"downloaded_images_{ref_id}"
        for index, img in enumerate(image_urls):
            image_name = f"image_{ref_id}_{index + 1}.jpg"

            download_image(img, folder_name, image_name)


# Example usage
url = 'https://www.motorflash.com/coches-de-segunda_mano/audi/'
results, list_sublinks1 = scrape_car_details(url)

image_download_from_links(list_sublinks1)

# todo
# napraviti while loop za .nxtpage dugme da bi izlistao sve stranice i poskidao elemente
