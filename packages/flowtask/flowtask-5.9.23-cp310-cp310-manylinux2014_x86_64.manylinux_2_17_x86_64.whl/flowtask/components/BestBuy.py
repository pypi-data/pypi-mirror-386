import asyncio
import aiohttp
from typing import Any, Dict, Optional
from collections.abc import Callable
import random
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import httpx
import pandas as pd
import backoff
import ssl
import json
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from navconfig.logging import logging
import os
from pathlib import Path
from datetime import datetime
import time

# Internals
from ..exceptions import (
    ComponentError,
    DataNotFound,
    NotSupported,
    ConfigError
)
from .flow import FlowComponent
from ..interfaces import HTTPService, SeleniumService
from ..interfaces.http import ua


logging.getLogger(name='selenium.webdriver').setLevel(logging.WARNING)
logging.getLogger(name='WDM').setLevel(logging.WARNING)
logging.getLogger(name='hpack').setLevel(logging.WARNING)

ProductPayload = {
    "locationId": None,
    "zipCode": None,
    "showOnShelf": True,
    "lookupInStoreQuantity": True,
    "xboxAllAccess": False,
    "consolidated": True,
    "showOnlyOnShelf": False,
    "showInStore": True,
    "pickupTypes": [
        "UPS_ACCESS_POINT",
        "FEDEX_HAL"
    ],
    "onlyBestBuyLocations": True,
    "items": [
        {
            "sku": None,
            "condition": None,
            "quantity": 1,
            "itemSeqNumber": "1",
            "reservationToken": None,
            "selectedServices": [],
            "requiredAccessories": [],
            "isTradeIn": False,
            "isLeased": False
        }
    ]
}


def bad_gateway_exception(exc):
    """Check if the exception is a 502 Bad Gateway error."""
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 502


# Desktop-only User-Agents for product scraping
desktop_user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


class BestBuy(FlowComponent, SeleniumService, HTTPService):
    """BestBuy.

    Combining API Key and Web Scrapping, this component will be able to extract
    Best Buy Information (stores, products, Product Availability, etc).


        Example:

        ```yaml
        BestBuy:
          type: availability
          product_info: false
          brand: Bose
        ```

    """
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        job: Callable = None,
        stat: Callable = None,
        **kwargs,
    ):
        self._fn = kwargs.pop('type', None)
        self.chunk_size: int = kwargs.get('chunk_size', 100)
        self.task_parts: int = kwargs.get('task_parts', 10)
        self.product_info: bool = kwargs.get('product_info', False)
        # Storage parameters
        self.use_storage: bool = kwargs.get('use_storage', False)
        self.storage_path: str = kwargs.get('storage_path')
        if self.use_storage and not self.storage_path:
            raise ConfigError(
                "BestBuy: storage_path is required when use_storage is True"
            )
        if not self._fn:
            raise ConfigError(
                "BestBuy: require a `type` Function to be called, ex: availability"
            )
        super(BestBuy, self).__init__(
            loop=loop,
            job=job,
            stat=stat,
            **kwargs
        )
        # Log storage information after logger is initialized
        if self.use_storage:
            self._logger.info(
                f"Storage enabled. Data will be saved in: {self.storage_path}"
            )
        # Always use proxies:
        self.use_proxy: bool = True
        self._free_proxy: bool = False
        ctt_list: list = [
            "f809c975d614934754e4f615db22447f"
        ]
        sid_list: list = [
            "ceeff26f-9a8a-4182-aba8-1effafc9b33f"
        ]
        self.cookies = {
            # "CTT": ,
            "CTT": random.choice(ctt_list),
            "SID": random.choice(sid_list),
            "bby_rdp": "l",
            "bm_sz": "9F5ED0110AF18594E2347A89BB4AB998~YAAQxm1lX6EqYHGSAQAAw+apmhkhXIeGYEc4KnzUMsjeac3xEoQmTNz5+of62i3RXQL6fUI+0FvCb/jgSjiVQOcfaSF+LdLkOXP1F4urgeIcqp/dBAhu5MvZXaCQsT06bwr7j21ozhFfTTWhjz1HmZN8wecsE6WGbK6wXp/33ODKlLaGWkTutqHbkzvMiiHXBCs9hT8jVny0REfita4AfqTK85Y6/M6Uq4IaDLPBLnTtJ0cTlPHk1HmkG5EsnI46llghcx1KZnCGnvZfHdb2ME9YZJ2GmC2b7dNmAgyL/gSVpoNdCJOj5Jk6z/MCVhZ81OZfX4S01E2F1mBGq4uV5/1oK2KR4YgZP4dsTN8izEEPybUKGY3CyM1gOUc=~3556420~4277810",  # noqa
            "bby_cbc_lb": "p-browse-e",
            "intl_splash": "false"
        }
        self.headers: dict = {
            "authority": "www.bestbuy.com",
            "Host": "www.bestbuy.com",
            "Referer": "https://www.bestbuy.com/",
            "X-Requested-With": "XMLHttpRequest",
            "TE": "trailers",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",  # noqa
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": random.choice(ua),
            **self.headers
        }
        self.semaphore = asyncio.Semaphore(10)

    async def close(self, **kwargs) -> bool:
        self.close_driver()
        return True

    async def start(self, **kwargs) -> bool:
        await super(BestBuy, self).start(**kwargs)
        if self.previous:
            self.data = self.input
            if not isinstance(self.data, pd.DataFrame):
                raise ComponentError(
                    "Incompatible Pandas Dataframe"
                )
        #else:
        #    raise DataNotFound(
        #        "Data Not Found",
        #        status=404
        #    )
        self.api_token = self.get_env_value(self.api_token) if hasattr(self, 'api_token') else self.get_env_value('BEST_BUY_API_KEY')
        # if self._fn == 'availability':
            # if not hasattr(self, 'brand'):
            #     raise ConfigError(
            #         "BestBuy: A Brand is required for using Product Availability"
            #     )
        if not hasattr(self, self._fn):
            raise ConfigError(
                f"BestBuy: Unable to found Function {self._fn} in BBY Component."
            )

    def _get_search_url(self, brand: str, sku: str) -> str:
        front_url = "https://www.bestbuy.com/site/searchpage.jsp?cp="
        middle_url = "&searchType=search&st="
        page_count = 1
        # TODO: Get the Brand and Model from the Component.
        search_term = f'{sku}'
        end_url = "&_dyncharset=UTF-8&id=pcat17071&type=page&sc=Global&nrp=&sp=&qp=&list=n&af=true&iht=y&usc=All%20Categories&ks=960&keys=keys"  # noqa
        url = front_url + str(page_count) + middle_url + search_term + end_url
        print('SEARCH URL: ', url)
        return url

    def _extract_rating_and_reviews(self):
        """Returns (avg_rating: Optional[float], num_reviews: Optional[int]) from JSON-LD.
        Fallback: tries in visible HTML if JSON-LD is not found.
        """
        avg_rating = None
        num_reviews = None

        try:
            soup = BeautifulSoup(self._driver.page_source, 'html.parser')

            # 1) Prefer JSON-LD (@type Product -> aggregateRating)
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    raw = script.string or script.get_text(strip=True)
                    if not raw:
                        continue
                    data = json.loads(raw)
                except Exception:
                    continue

                stack = [data]
                while stack:
                    node = stack.pop()
                    if isinstance(node, list):
                        stack.extend(node)
                        continue
                    if not isinstance(node, dict):
                        continue

                    if node.get('@type') == 'Product' and isinstance(node.get('aggregateRating'), dict):
                        ag = node['aggregateRating']
                        rv = ag.get('ratingValue') or ag.get('rating') or ag.get('ratingValue')
                        rc = ag.get('reviewCount') or ag.get('ratingCount')

                        try:
                            if rv is not None:
                                avg_rating = float(str(rv).replace(',', '.'))
                        except Exception:
                            pass
                        try:
                            if rc is not None:
                                num_reviews = int(str(rc).replace(',', ''))
                        except Exception:
                            pass

                        if avg_rating is not None or num_reviews is not None:
                            self._logger.info(f"Extracted from JSON-LD -> avg_rating: {avg_rating}, num_reviews: {num_reviews}")
                            return avg_rating, num_reviews

                    # push children
                    for v in node.values():
                        if isinstance(v, (list, dict)):
                            stack.append(v)

            # 2) Short fallback to already rendered DOM (in case BestBuy leaves something visible)
            #    a) span.c-reviews -> "71 Reviews"
            reviews_span = soup.select_one('span.c-reviews')
            if reviews_span:
                m = re.search(r'(\d[\d,]*)', reviews_span.get_text(strip=True))
                if m:
                    try:
                        num_reviews = int(m.group(1).replace(',', ''))
                    except Exception:
                        pass

            #    b) rating in aria-label like "4.7 out of 5 stars"
            rating_node = soup.select_one('[aria-label*="out of 5"]')
            if rating_node and avg_rating is None:
                m = re.search(r'(\d+(\.\d+)?)\s*out of 5', rating_node.get('aria-label',''), flags=re.I)
                if m:
                    try:
                        avg_rating = float(m.group(1))
                    except Exception:
                        pass

            #    c) legacy (what we had before)
            if avg_rating is None:
                rating_span = soup.select_one('span.font-weight-medium.font-weight-bold')
                if rating_span:
                    try:
                        avg_rating = float(rating_span.get_text(strip=True))
                    except Exception:
                        pass

            if avg_rating is not None or num_reviews is not None:
                self._logger.info(f"Extracted from DOM -> avg_rating: {avg_rating}, num_reviews: {num_reviews}")

        except Exception as e:
            self._logger.debug(f"_extract_rating_and_reviews error: {e}")

        return avg_rating, num_reviews


    def _extract_product_description(self) -> str:
        """Opens 'Features' and extracts the description from the modal."""
        desc = ""
        wait = WebDriverWait(self._driver, 20)

        try:
            # 1) Close any previous sheet
            for sel in (
                'button[data-testid="brix-sheet-closeButton"]',
                'button[aria-label="Close"]',
                'button[aria-busy="false"][aria-label="Close"]',
                'button.border-solid.justify-center.items-center',
            ):
                try:
                    btn = self._driver.find_element(By.CSS_SELECTOR, sel)
                    if btn.is_displayed():
                        self._driver.execute_script("arguments[0].click();", btn)
                        time.sleep(0.6)
                        break
                except Exception:
                    pass

            # 2) Extra optional ESC
            try:
                self._driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(0.3)
            except Exception:
                pass

            # 3) Wait for backdrop to disappear if present
            try:
                wait.until_not(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[data-testid="brix-sheet-backdrop"]')
                ))
            except Exception:
                pass

            # 4) Click on Features (robust locator)
            features_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//h3[normalize-space()="Features"]/ancestor::button[1]'))
            )
            self._driver.execute_script("arguments[0].scrollIntoView({block:'center'});", features_btn)
            time.sleep(0.4)
            self._driver.execute_script("arguments[0].click();", features_btn)

            # 5) Wait for sheet content
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-testid="brix-sheet-content"]')))
            time.sleep(0.2)  # dar tiempo al DOM para pintar el texto

            # 6) If there is "See more...", open it to get the full paragraph
            try:
                see_more = self._driver.find_element(
                    By.XPATH,
                    '//div[@data-testid="brix-sheet-content"]//button[contains(@class,"c-button-link")][contains(.,"See more")]'
                )
                self._driver.execute_script("arguments[0].click();", see_more)
                time.sleep(0.2)
            except Exception:
                pass

            # 7) Parse and take the first valid <p>
            soup = BeautifulSoup(self._driver.page_source, 'html.parser')
            content = soup.find('div', attrs={'data-testid': 'brix-sheet-content'})
            if content:
                for p in content.find_all('p'):
                    txt = p.get_text(strip=True)
                    if txt and not re.search(r'out of 5|review', txt.lower()):
                        desc = txt
                        break

        except (TimeoutException, StaleElementReferenceException) as e:
            self._logger.warning(f"Error extracting product description: {e}")
        except Exception as e:
            self._logger.warning(f"Error extracting product description: {e}")

        return desc
    
    def _parse_price(self, text):
        """Returns the first numeric price found as float (without $ or commas)."""
        if not text:
            return None
        s = str(text).replace('\xa0', ' ')
        m = re.search(r'(\d[\d,]*\.?\d*)', s)  # primer número tipo 1,234.56
        if not m:
            return None
        try:
            return float(m.group(1).replace(',', ''))
        except ValueError:
            return None

    def _extract_price(self) -> Optional[float]:
        """Reads the price from the DOM (headless-safe) and returns it as float."""
        selectors = (
            'div[data-testid="price-block-customer-price"] span, '
            'div[data-testid="customer-price"] span, '
            'div.priceView-customer-price span'
        )
        try:
            wait = WebDriverWait(self._driver, 20)
            # Espera a que exista al menos un candidato
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selectors)))

            # Toma el primero visible con texto
            for el in self._driver.find_elements(By.CSS_SELECTOR, selectors):
                try:
                    if el.is_displayed():
                        txt = el.get_attribute("textContent") or el.text
                        val = self._parse_price(txt)
                        if val is not None:
                            return val
                except StaleElementReferenceException:
                    continue
        except TimeoutException:
            self._logger.debug("Price element not found before timeout")

        # Fallback corto: parsear el HTML actual con los mismos selectores
        try:
            soup = BeautifulSoup(self._driver.page_source, 'html.parser')
            el = (soup.select_one('div[data-testid="price-block-customer-price"] span')
                or soup.select_one('div[data-testid="customer-price"] span')
                or soup.select_one('div.priceView-customer-price span'))
            return self._parse_price(el.get_text(strip=True)) if el else None
        except Exception:
            return None


    def _clean_image_url(self, url: Optional[str]) -> Optional[str]:
        """Returns the base image URL without Best Buy suffixes.
        - Takes the first candidate if it comes from a srcset (comma/space).
        - Cuts everything after the first ';'.
        """
        if not url:
            return None
        s = str(url).strip()
        # si viene como srcset: "url1 1x, url2 2x"
        s = s.split(',')[0].strip().split(' ')[0]
        # quitar parámetros añadidos por BestBuy
        s = s.split(';', 1)[0]
        return s or None



    async def _extract_product_info(self, product_element):
        """Extract product information from a specific product element and its specification sheet"""
        try:
            sku_id = product_element.get("data-testid")
            if not sku_id:
                sku_element = product_element.select_one('div.attribute:-soup-contains("SKU") span.value')
                if sku_element:
                    sku_id = sku_element.text.strip()

            title_element = product_element.select_one(
                '.product-list-item-title a, h4.sku-title a, a.product-list-item-link'
            ) or product_element.select_one('a.product-list-item-link')

            # Don't fail if no title found - we already matched by SKU
            title = title_element.text.strip() if title_element else f"Product SKU {sku_id}"
            # Create soup from product element
            soup = BeautifulSoup(str(product_element), "html.parser")
            # Extract price (helper)
            price = self._extract_price()
            image_element = product_element.select_one('img.product-image, img')
            image = None
            if image_element:
                raw_img = (
                    image_element.get('src') or
                    image_element.get('data-src') or
                    image_element.get('data-lazy')
                )
                image = self._clean_image_url(raw_img)

            url = title_element.get('href', None)
            self._logger.notice(f':: Product URL: {url}')

            model_element = product_element.select_one('div.attribute:-soup-contains("Model") span.value')
            model_value = model_element.text.strip() if model_element else self.model

            specifications = {}
            product_description = ""
            try:
                if url and self._driver:
                    self._driver.get(url)
                    await asyncio.sleep(1)

                    # Extract specifications
                    try:
                        wait = WebDriverWait(self._driver, 10)
                        # Try multiple selectors in order of preference
                        selectors_to_try = [
                            # New structure (2025): by text "See All Specifications"
                            ('xpath', '//button[contains(@class, "show-full-specs-btn")]//span[contains(text(), "See All Specifications")]'),
                            # Alternative: by h5 text "Specifications"
                            ('xpath', '//button[.//h5[text()="Specifications"]]'),
                            # Legacy: by h3 text
                            ('xpath', '//button[.//h3[text()="Specifications"]]'),
                            # Old fallback
                            ('css', 'button.c-button.show-full-specs-btn[data-testid="brixbutton"]')
                        ]

                        spec_btn = None
                        for selector_type, selector in selectors_to_try:
                            try:
                                if selector_type == 'xpath':
                                    spec_btn = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                                else:
                                    spec_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                                self._logger.debug(f"Found specifications button using: {selector}")
                                break
                            except TimeoutException:
                                continue

                        if not spec_btn:
                            raise TimeoutException("Could not find specifications button with any selector")

                        self._driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", spec_btn)
                        await asyncio.sleep(1)
                        spec_btn.click()
                        await asyncio.sleep(2)
                    except Exception as e:
                        self._logger.warning(f"Could not click the specifications button: {e}")

                    soup = BeautifulSoup(self._driver.page_source, 'html.parser')
                    content_div = soup.find('div', attrs={'data-testid': 'brix-sheet-content'})
                    if content_div:
                        ul = content_div.find('ul')
                        if ul:
                            for li in ul.find_all('li', recursive=False):
                                section_title_elem = li.find('h4')
                                section_title = section_title_elem.get_text(strip=True) if section_title_elem else 'Specifications'
                                for attr_row in li.find_all('div', class_='inline-flex'):
                                    label_div = attr_row.find('div', class_='font-weight-medium')
                                    value_div = attr_row.find('div', class_='pl-300')
                                    if label_div and value_div:
                                        key = label_div.get_text(strip=True)
                                        value = value_div.get_text(strip=True)
                                        if section_title not in specifications:
                                            specifications[section_title] = {}
                                        specifications[section_title][key] = value


            except Exception as e:
                self._logger.warning(f"Error extracting specifications: {e}")
            try:
                product_description = self._extract_product_description()
            except Exception as e:
                self._logger.warning(f"Error extracting description: {e}")

            # Extract reviews and rating from current page (homologado con helper)
            try:
                avg_rating, num_reviews = self._extract_rating_and_reviews()
            except Exception as e:
                self._logger.warning(f"Could not extract reviews/rating: {e}")

            return {
                "sku": sku_id,
                "brand": self.brand,
                "product_name": title,
                "image_url": image,
                "price": price,
                "url": url,
                "specifications": specifications if specifications else {},
                "product_description": product_description,
                "num_reviews": num_reviews,
                "avg_rating": avg_rating
            }

        except Exception as e:
            self._logger.error(f"Error extracting product info: {e}")
            return None

    async def _product_info(self, idx, row):
        async with self.semaphore:
            model = row.get('model')
            brand = row.get('brand') or getattr(self, 'brand', None)
            sku = row.get('sku')
            product_url = row.get('url')  # Check for URL in DataFrame

            self.brand = brand
            self.sku = sku
            self.model = model
            
            self._logger.info(f"Processing product - Brand: {brand}, Model: {model}, SKU: {sku}, URL: {product_url}")

            if not self._driver:
                await self.get_driver()

            try:
                # If we have a direct product URL, use it instead of searching
                if product_url:
                    self._logger.info(f"Using direct product URL: {product_url}")
                    await self.get_page(product_url)
                    await asyncio.sleep(3)
                    
                    # Extract product info directly from the page
                    soup = BeautifulSoup(self._driver.page_source, 'html.parser')
                    
                    # Extract title
                    title_element = (
                        soup.select_one('h1.heading-5.v-fw-regular') or
                        soup.select_one('h1[data-testid="product-title"]') or
                        soup.select_one('h1.product-title') or
                        soup.select_one('h1')
                    )
                    title = title_element.text.strip() if title_element else f"Product SKU {sku}"
                    # Extract price
                    price = self._extract_price()
                    # Extract image
                    image_element = (
                        soup.select_one('img.primary-image') or
                        soup.select_one('img[data-testid="product-image"]') or
                        soup.select_one('img.product-image') or
                        soup.select_one('img')
                    )
                    image = None
                    if image_element:
                        raw_img = (
                            image_element.get('src') or
                            image_element.get('data-src') or
                            image_element.get('data-lazy')
                        )
                        image = self._clean_image_url(raw_img)
                    
                    # ✅ Extract reviews and rating (usando helper)
                    avg_rating, num_reviews = self._extract_rating_and_reviews()
                    
                    # Extract specifications
                    specifications = {}
                    product_description = ""
                    try:
                        # Try to click specifications button
                        # Try multiple selectors in order of preference
                        selectors_to_try = [
                            # New structure (2025): by text "See All Specifications"
                            ('xpath', '//button[contains(@class, "show-full-specs-btn")]//span[contains(text(), "See All Specifications")]'),
                            # Alternative: by h5 text "Specifications"
                            ('xpath', '//button[.//h5[text()="Specifications"]]'),
                            # Legacy: by h3 text
                            ('xpath', '//button[.//h3[text()="Specifications"]]'),
                            # Old fallback
                            ('css', 'button.c-button.show-full-specs-btn[data-testid="brixbutton"]')
                        ]

                        spec_btn = None
                        for selector_type, selector in selectors_to_try:
                            try:
                                if selector_type == 'xpath':
                                    spec_btn = self._driver.find_element(By.XPATH, selector)
                                else:
                                    spec_btn = self._driver.find_element(By.CSS_SELECTOR, selector)
                                self._logger.debug(f"Found specifications button using: {selector}")
                                break
                            except:
                                continue

                        if spec_btn:
                            self._driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", spec_btn)
                            await asyncio.sleep(1)
                            spec_btn.click()
                            await asyncio.sleep(2)
                            
                            # Re-parse after clicking
                            soup = BeautifulSoup(self._driver.page_source, 'html.parser')
                            content_div = soup.find('div', attrs={'data-testid': 'brix-sheet-content'})
                            if content_div:
                                ul = content_div.find('ul')
                                if ul:
                                    for li in ul.find_all('li', recursive=False):
                                        section_title_elem = li.find('h4')
                                        section_title = section_title_elem.get_text(strip=True) if section_title_elem else 'Specifications'
                                        for attr_row in li.find_all('div', class_='inline-flex'):
                                            label_div = attr_row.find('div', class_='font-weight-medium')
                                            value_div = attr_row.find('div', class_='pl-300')
                                            if label_div and value_div:
                                                key = label_div.get_text(strip=True)
                                                value = value_div.get_text(strip=True)
                                                if section_title not in specifications:
                                                    specifications[section_title] = {}
                                                specifications[section_title][key] = value
                    except Exception as e:
                        self._logger.debug(f"Could not extract specifications: {e}")
                    try:
                        product_description = self._extract_product_description()
                    except Exception as e:
                        self._logger.warning(f"Error extracting description: {e}")

                    
                    product_info = {
                        "sku": sku,
                        "brand": brand,
                        "product_name": title,
                        "image_url": image,
                        "price": price,
                        "url": product_url,
                        "specifications": specifications if specifications else {},
                        "product_description": product_description,
                        "num_reviews": num_reviews,
                        "avg_rating": avg_rating
                    }
                    
                    if product_info:
                        # Override the SKU and URL with our known values
                        product_info['sku'] = sku
                        product_info['url'] = product_url
                        
                        for key, value in product_info.items():
                            if key == "specifications":
                                self.data.at[idx, "specifications"] = json.dumps(value, ensure_ascii=False)
                            elif key in self.data.columns:
                                self.data.loc[idx, key] = value
                            else:
                                self.data.at[idx, key] = value
                        self.data.loc[idx, 'enabled'] = True
                        return row
                    else:
                        self._logger.warning(f"Could not extract product info from direct URL: {product_url}")
                
                # Fallback to search method if no URL or direct extraction failed
                url = self._get_search_url(brand, model)
                await self.get_page(url)
                self.data.loc[idx, 'enabled'] = False

                self._execute_scroll(scroll_pause_time=4.0, max_scrolls=10)
                await asyncio.sleep(3)

                soup = BeautifulSoup(self._driver.page_source, 'html.parser')
                # Try multiple selectors to find product items
                product_items = (
                    soup.find_all('li', {'data-testid': True}) or  # New structure with data-testid
                    soup.find_all('li', {'class': ['product-list-item']}) or  # Legacy structure
                    soup.find_all('li', {'class': ['sku-item']})  # Alternative legacy structure
                )

                self._logger.info(f"Found {len(product_items)} product items to analyze")
                
                for item in product_items:
                    try:
                        sku_id = item.get("data-testid")
                        model_element = item.select_one('div.attribute:-soup-contains("Model") span.value')
                        model_value = model_element.text.strip() if model_element else None

                        self._logger.debug(f"Analyzing product - SKU ID: {sku_id}, Model: {model_value}, Target SKU: {sku}, Target Model: {model}")

                        # Improved SKU matching with type conversion
                        sku_match = False
                        if sku and sku_id:
                            sku_match = (str(sku_id) == str(sku))
                        
                        # Improved model matching
                        model_match = False
                        if model_value and model:
                            model_clean = model.strip().lower()
                            model_value_clean = model_value.strip().lower()
                            model_match = (
                                model_value_clean == model_clean or
                                model_value.replace(" ", "").lower() == model.replace(" ", "").lower() or
                                model_clean in model_value_clean or
                                model_value_clean in model_clean
                            )

                        self._logger.debug(f"Match results - SKU match: {sku_match}, Model match: {model_match}")
                        
                        if sku_match or model_match:
                            self._logger.info(f"Found matching product - SKU: {sku_id}, Model: {model_value}")
                            product_info = await self._extract_product_info(item)

                            if product_info:
                                for key, value in product_info.items():
                                    if key == "specifications":
                                        self.data.at[idx, "specifications"] = json.dumps(value, ensure_ascii=False)
                                    elif key in self.data.columns:
                                        self.data.loc[idx, key] = value
                                    else:
                                        self.data.at[idx, key] = value
                                self.data.loc[idx, 'enabled'] = True
                                return row
                    except Exception as e:
                        self._logger.warning(f"Error processing product: {e}")

                self._logger.warning(f"No matching product found for {brand} {model} / {sku}")
                return row

            except Exception as exc:
                self._logger.error(f"Error during product search for {brand} {model}: {exc}")
                return row

    def chunkify(self, lst, n):
        """Split list lst into chunks of size n."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    @backoff.on_exception(
        backoff.expo,
        (httpx.ConnectTimeout, httpx.HTTPStatusError),
        max_tries=2,
        giveup=lambda e: not bad_gateway_exception(e) and not isinstance(e, httpx.ConnectTimeout)
    )
    async def _check_store_availability(self, idx, row, cookies):
        async with self.semaphore:
            # Prepare payload for the API request
            zipcode = row['zipcode']
            location_code = str(row['location_code'])
            sku = row['sku']
            brand = row['brand']
            payload = ProductPayload.copy()
            payload["locationId"] = location_code
            payload["zipCode"] = zipcode
            for item in payload["items"]:
                item["sku"] = sku

            # checking if this current store is already marked as checked:
            matching_store = self.data[
                (self.data['location_code'] == location_code) & (self.data['sku'] == sku)
            ]
            if not matching_store.empty and matching_store.iloc[0]['checked'] is True:
                # exit without making any HTTP call.
                return row
            try:
                result = await self.api_post(
                    url="https://www.bestbuy.com/productfulfillment/c/api/2.0/storeAvailability",
                    cookies=cookies,
                    payload=payload
                )
                self._num_iterations += 1
            except (httpx.TimeoutException, httpx.HTTPError) as ex:
                self._logger.warning(f"Request failed: {ex}")
                return row
            except Exception as ex:
                self._logger.error(f"An error occurred: {ex}")
                return row

            if not result:
                self._logger.warning(
                    f"No availability data found for {sku} at zipcode {zipcode}"
                )
                return row

            # Extract the availability data from the API response
            items = result.get('ispu', {}).get('items', [])
            for item in items:
                # Extract boolean fields from item level
                in_store_available = item.get('inStoreAvailable', False)
                pickup_eligible = item.get('pickupEligible', False)
                
                locations = item.get('locations', [])
                for location in locations:
                    self.data.loc[idx, 'enabled'] = False if result.get('consolidatedButtonState', {}).get('buttonState', '') == 'NOT_AVAILABLE' else True
                    lid = location.get('locationId')
                    # Find matching store and SKU in DataFrame
                    matching_store = self.data[
                        (self.data['location_code'] == lid) & (self.data['sku'] == sku)
                    ]
                    if not matching_store.empty:
                        idx = matching_store.index[0]
                        if self.data.loc[idx, 'checked'] is True:
                            print('Already checked, continue ...')
                            continue  # Skip this row if it's already marked as checked
                        if 'availability' not in location:
                            self.data.loc[idx, 'locationId'] = lid
                            self.data.loc[idx, 'checked'] = True
                            continue  # This store doesn't have availability
                        print(f'Found matching store {lid} for sku {sku}')

                        # Update the DataFrame row with new availability data
                        self.data.loc[idx, ['brand', 'location_data']] = [brand, location]
                        
                        # Set the boolean fields from item level
                        self.data.loc[idx, 'inStoreAvailable'] = in_store_available
                        self.data.loc[idx, 'pickupEligible'] = pickup_eligible
                        
                        for key, val in location.items():
                            if key in self.data.columns:
                                self.data.at[idx, key] = val
                            else:
                                self.data.at[idx, key] = None
                            if key == 'inStoreAvailability':
                                try:
                                    self.data.loc[idx, 'availableInStoreQuantity'] = val.get(
                                        'availableInStoreQuantity', 0
                                    )
                                except KeyError:
                                    self.data.loc[idx, 'availableInStoreQuantity'] = None
                            if key == 'availability':
                                try:
                                    self.data.loc[idx, 'availablePickupQuantity'] = val.get(
                                        'availablePickupQuantity', 0
                                    )
                                except KeyError:
                                    self.data.loc[idx, 'availablePickupQuantity'] = None
                        # Mark the row as checked
                        self.data.loc[idx, 'checked'] = True
            return row

    def column_exists(self, column: str, default_val: Any = None):
        if column not in self.data.columns:
            self._logger.warning(
                f"Column {column} does not exist in the Dataframe"
            )
            self.data[column] = default_val
            return False
        return True

    async def availability(self):
        """availability.

        Best Buy Product Availability.
        """
        httpx_cookies = httpx.Cookies()
        for key, value in self.cookies.items():
            httpx_cookies.set(
                key, value,
                domain='.bestbuy.com',
                path='/'
            )

        # define the columns returned:
        self.column_exists('brand')
        self.column_exists('location_data')
        self.column_exists('locationId')
        self.column_exists('availability')
        self.column_exists('inStoreAvailability')
        self.column_exists('onShelfDisplay', False)
        self.column_exists('availableInStoreQuantity', 0)
        self.column_exists('inStoreAvailable', False)
        self.column_exists('pickupEligible', False)
        self.column_exists('availablePickupQuantity', 0)
        self.column_exists('enabled', False)

        # With available cookies, iterate over dataframe for stores:
        self.data['checked'] = False  # Add 'checked' flag column

        # Iterate over each row in the DataFrame
        print('starting ...')

        tasks = [
            self._check_store_availability(
                idx,
                row,
                httpx_cookies
            ) for idx, row in self.data.iterrows()
        ]

        self._num_iterations = 0
        await self._processing_tasks(tasks)

        self.add_metric('NUM_HTTP_CALLS', self._num_iterations)

        # show the num of rows in final dataframe:
        self._logger.notice(
            "Ending Checking Availability."
        )

        # return existing data
        return self.data

    async def products(self):
        """
            Fetch all products from the Best Buy API by paginating through all pages.

            Returns:
                list: A combined list of all products from all pages.
        """
        all_products = []
        current_page = 1
        total_pages = None
        show = 'sku,upc,modelNumber,name,manufacturer,type,salePrice,url,productTemplate,classId,class,subclassId,subclass,department,image,longDescription,customerReviewCount,customerReviewAverage'
        self._num_iterations = 0
        try:
            while True:
                url = f"https://api.bestbuy.com/v1/products?page={current_page}&pageSize=100&apiKey={self.api_token}&show={show}&format=json"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as result:
                        response = await result.json()
                        #response = await self.api_get(url, httpx_cookies)
                        self._num_iterations += 1

                        # Extract products from the response
                        products = response.get("products", [])
                        if len(products) == 0:
                            continue
                        all_products.extend(products)
                        #all_products += products

                        # Pagination control
                        current_page = response.get("currentPage", current_page)
                        total_pages = response.get("totalPages", current_page) if total_pages is None else total_pages
                        self._logger.debug(f"{url}\n    Current Page: {current_page}, Total Pages: {total_pages}, Products: {len(all_products)}")

                        # Break if we've processed all pages
                        if current_page >= total_pages:  # or current_page == 3:
                            break

                        # Increment page for the next request
                        current_page += 1

            self.add_metric('NUM_HTTP_CALLS', self._num_iterations)
            return pd.DataFrame(all_products)

        except Exception as exc:
            self._logger.error(f"Error while fetching products: {exc}")
            return []

    async def stores(self):
        """
            Fetch all stores from the Best Buy API by paginating through all pages.

            Returns:
                list: A combined list of all stores from all pages.
        """
        all_stores = []
        current_page = 1
        total_pages = None
        self._num_iterations = 0
        try:
            while True:
                url = f"https://api.bestbuy.com/v1/stores?page={current_page}&pageSize=100&apiKey={self.api_token}&format=json"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as result:
                        response = await result.json()
                        self._num_iterations += 1

                        # Extract stores from the response
                        stores = response.get("stores", [])
                        if len(stores) == 0:
                            continue
                        all_stores.extend(stores)
                        # Pagination control
                        current_page = response.get("currentPage", current_page)
                        total_pages = response.get("totalPages", current_page) if total_pages is None else total_pages
                        self._logger.debug(f"{url}\n    Current Page: {current_page}, Total Pages: {total_pages}, Stores: {len(all_stores)}")

                        # Break if we've processed all pages
                        if current_page >= total_pages:
                            break

                        # Increment page for the next request
                        current_page += 1

            self.add_metric('NUM_HTTP_CALLS', self._num_iterations)
            return pd.DataFrame(all_stores)

        except Exception as exc:
            self._logger.error(f"Error while fetching stores: {exc}")
            return []

    @backoff.on_exception(
        backoff.expo,
        (httpx.TimeoutException, httpx.ConnectTimeout, httpx.HTTPStatusError),
        max_tries=3,
        jitter=backoff.full_jitter,
        giveup=lambda e: not bad_gateway_exception(e) and not isinstance(e, httpx.ConnectTimeout)
    )
    async def _product_reviews(self, idx, row, cookies):
        async with self.semaphore:
            # Prepare payload for the API request
            sku = row['sku']
            pagesize = 20
            max_pages = 20    # Maximum number of pages to fetch
            current_page = 1
            all_reviews = []
            total_reviews = 0
            try:
                while current_page <= max_pages:
                    payload = {
                        "page": current_page,
                        "pageSize": pagesize,
                        "sort": "MOST_RECENT",
                        # "variant": "A",
                        # "verifiedPurchaseOnly": "true",
                        "sku": sku
                    }
                    print('PAYLOAD > ', payload)
                    headers = {
                        'authority': 'www.bestbuy.com',
                        'x-client-id': 'ratings-and-reviews-user-generated-content-ratings-and-reviews-v1',
                        'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': '"macOS"',
                        'sec-fetch-dest': 'empty',
                        'sec-fetch-mode': 'cors',
                        'sec-fetch-site': 'same-origin',
                        **self.headers
                    }
                    url = f"https://www.bestbuy.com/ugc/v2/reviews?page={current_page}&pageSize={pagesize}&sku={sku}&sort=MOST_RECENT&variant=A"
                    print('URL > ', url)
                    result = await self.api_get(
                        # url="https://www.bestbuy.com/ugc/v2/reviews",
                        url=url,
                        cookies=cookies,
                        # params=payload,
                        headers=headers,
                        use_proxy=True,
                        free_proxy=False
                    )
                    await asyncio.sleep(0.1)
                    total_reviews = result.get('totalResults', 0)
                    if not result:
                        self._logger.warning(
                            f"No Product Reviews found for {sku}."
                        )
                        break
                    # Extract the reviews data from the API response
                    items = result.get('topics', [])
                    if len(items) == 0:
                        break

                    all_reviews.extend(items)

                    # Determine if we've reached the last page
                    total_pages = result.get('totalPages', max_pages)
                    if current_page >= total_pages:
                        break
                    current_page += 1  # Move to the next page
            except (httpx.TimeoutException, httpx.HTTPError) as ex:
                self._logger.warning(f"Request failed: {ex}")
                return []
            except Exception as ex:
                self._logger.error(f"An error occurred: {ex}")
                return []

            # Extract the reviews data from the API response
            reviews = []
            for item in all_reviews:
                # Exclude certain keys
                filtered_item = {k: v for k, v in item.items() if k not in ('brandResponses', 'badges', 'photos', 'secondaryRatings')}
                # Combine with original row data
                review_data = row.to_dict()
                review_data['total_reviews'] = total_reviews
                review_data.update(filtered_item)
                reviews.append(review_data)
            self._logger.info(
                f"Fetched {len(reviews)} reviews for SKU {sku}."
            )
            await asyncio.sleep(random.randint(1, 3))
            return reviews

    async def reviews(self):
        """reviews.

        Best Buy Product Reviews.
        """
        httpx_cookies = httpx.Cookies()
        for key, value in self.cookies.items():
            httpx_cookies.set(
                key, value,
                domain='.bestbuy.com',
                path='/'
            )

        # With available cookies, iterate over dataframe for stores:
        self.data['checked'] = False  # Add 'checked' flag column

        # Iterate over each row in the DataFrame
        print('starting ...')

        tasks = [
            self._product_reviews(
                idx,
                row,
                httpx_cookies
            ) for idx, row in self.data.iterrows()
        ]
        # Gather results concurrently
        all_reviews_nested = await self._processing_tasks(tasks)

        # Flatten the list of lists
        all_reviews = [review for reviews in all_reviews_nested for review in reviews]

        # Convert to DataFrame
        reviews_df = pd.DataFrame(all_reviews)

        # Remove duplicates based on the review 'id' column
        if 'id' in reviews_df.columns:
            reviews_df = reviews_df.drop_duplicates(subset=['id'])

        # rename the "text" column as "review" and the "id" column as "reviewid"
        reviews_df.rename(columns={'text': 'review', 'id': 'reviewid'}, inplace=True)

        # at the end, adding a column for origin of reviews:
        reviews_df['origin'] = 'bestbuy'

        # show the num of rows in final dataframe:
        self._logger.notice(
            f"Ending Product Reviews: {len(reviews_df)}"
        )

        # Override previous dataframe:
        self.data = reviews_df

        # return existing data
        return self.data

    async def product(self):
        """product.

        Best Buy Product Information.
        """
        # Ensure required columns exist in the DataFrame
        self.column_exists('model')
        self.column_exists('brand')
        self.column_exists('sku')
        self.column_exists('product_name')
        self.column_exists('image_url')
        self.column_exists('price')
        self.column_exists('url')
        self.column_exists('product_description')
        self.column_exists('num_reviews')
        self.column_exists('avg_rating')
        self.column_exists('enabled', False)

        # Set headless to True for production
        self.headless = True

        # Always set as_mobile to False to ensure desktop mode
        self.as_mobile = False

        # Initialize Selenium driver
        if not self._driver:
            await self.get_driver()
            
        # Override User-Agent with desktop version for product scraping
        desktop_ua = random.choice(desktop_user_agents)
        self._driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            'userAgent': desktop_ua
        })
        self._logger.info(f"Product scraping: Set desktop User-Agent: {desktop_ua[:50]}...")

        # Create tasks to process each row in the DataFrame
        tasks = [
            self._product_info(
                idx,
                row
            ) for idx, row in self.data.iterrows()
        ]

        # Process tasks concurrently
        await self._processing_tasks(tasks)

        # Add origin column
        self.data['origin'] = 'bestbuy'

        # Close Selenium driver after completing all tasks
        self.close_driver()

        # Return the updated DataFrame
        return self.data

    def _get_storage_file(self) -> str:
        """Get the storage file path for the current execution."""
        today = datetime.now().strftime('%Y%m%d')
        filename = f"bestbuy_{self._fn}_{self._program}_{today}.csv"
        storage_dir = Path(self.storage_path)
        storage_dir.mkdir(parents=True, exist_ok=True)
        return str(storage_dir / filename)

    async def run(self):
        # Try to load from storage first
        if self.use_storage:
            storage_file = self._get_storage_file()
            if os.path.exists(storage_file):
                self._logger.info(
                    f"Found existing data file: {storage_file}. Using stored data."
                )
                try:
                    self._result = pd.read_csv(storage_file)
                    return self._result
                except Exception as e:
                    self._logger.error(f"Error loading storage file: {e}")
            else:
                self._logger.info(
                    f"No existing data file found. Will generate new file: {storage_file}"
                )

        # If no storage or error, proceed with normal execution
        fn = getattr(self, self._fn)
        result = None
        if not callable(fn):
            raise ComponentError(
                f"Best Buy: Function {self._fn} doesn't exists."
            )
        try:
            result = await fn()
            # Save to storage after successful execution
            if self.use_storage and result is not None and isinstance(result, pd.DataFrame):
                try:
                    storage_file = self._get_storage_file()
                    result.to_csv(storage_file, index=False)
                    self._logger.info(
                        f"Successfully saved data to: {storage_file}"
                    )
                except Exception as e:
                    self._logger.error(f"Error saving to storage: {e}")
        except (ComponentError, TimeoutError, NotSupported):
            raise
        except Exception as exc:
            raise ComponentError(
                f"BestBuy: Unknown Error: {exc}"
            ) from exc
        # Print results
        print(result)
        print("::: Printing Column Information === ")
        for column, t in result.dtypes.items():
            print(column, "->", t, "->", result[column].iloc[0])
        self._result = result
        return self._result
