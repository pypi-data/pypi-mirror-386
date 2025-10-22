import asyncio
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from typing import List
from urllib.parse import urljoin, urlparse

from pyba.utils.common import url_entropy


class DOMExtraction:
    """
    Given the DOM from the URL, this class provides functions to extract it properly
    
    1. Extract all the hyperlinks from it
    2. Extract all input_fields from it (basically all fillable boxes)
    3. Extract all the clickables from it
    4. Extract all the actual text from it (we don't have to do any OCR for this!)

    Note that extracing all clickable elements might get messy so we'll use that only when
    the total length is lower than a certain threshold.
    """

    def __init__(self, html: str, body_text: str, elements: str, base_url: str = None, clickable_fields_flag: bool = False) -> None:
        """
        We'll take the entire dom, the text_body and the elements for sure 
        """

        self.html = html
        self.body_text = body_text
        self.elements = elements
        self.base_url = base_url

        self.clickable_fields_flag = clickable_fields_flag
        # For testing fields
        self.test_value = "PyBA"

    def _extract_clickables(self) -> List[dict]:
        soup = BeautifulSoup(self.html, "html.parser")
        candidates = []

        for tag in soup.find_all(["a", "button", "area", "summary"]):
            if tag.name == "a":
                href = tag.get("href", "").strip().lower()
                if (
                    not href
                    or href in {"#", "#!", "/", "javascript:void(0)", "javascript:void(0);", "javascript: void(0)"}
                    or href.startswith("javascript:")
                    or href.startswith("#")
                ):
                    continue
            candidates.append(tag)

        for tag in soup.find_all("input"):
            t = tag.get("type", "").lower()
            if t in ("button", "submit", "reset"):
                candidates.append(tag)

        candidates += soup.find_all(attrs={"onclick": True})
        candidates += soup.find_all(attrs={"role": lambda v: v and v.lower() in ("button", "link")})
        candidates += soup.find_all(attrs={"tabindex": True})

        seen = set()
        results = []
        for el in candidates:
            key = (el.name, str(el))
            if key in seen:
                continue
            seen.add(key)

            href = el.get("href")
            onclick = el.get("onclick")
            role = el.get("role")
            tabindex = el.get("tabindex")
            text = el.get_text(strip=True)

            if not (text or href or onclick):
                continue

            if href and self.base_url:
                href = urljoin(self.base_url, href)

            # Not sure how junk these are but dropping them for now to avoid explosion of context
            junk_keywords = [
                "previous", "next", "slide", "carousel", "arrow", "goto", "nav", "scroll"
            ]
            if any(k in text.lower() for k in junk_keywords):
                continue

            results.append(
                {
                    "tag": el.name,
                    "text": text,
                    "href": href,
                    "onclick": onclick,
                    "role": role,
                    "tabindex": tabindex,
                    "outer_html": str(el)[:1000],
                }
            )

        return results

    def _extract_href(self) -> List[str]:
        soup = BeautifulSoup(str(self.html), "html.parser")
        hrefs = [a["href"].strip() for a in soup.find_all("a", href=True)]

        clean_hrefs = []
        for href in hrefs:
            href_lower = href.lower()

            # If we do a raw extraction, all this junk will make it through
            if (
                not href_lower
                or href_lower in {"#", "#!", "/", "javascript:void(0)", "javascript:void(0);", "javascript: void(0)"}
                or href_lower.startswith("javascript:")
                or href_lower.startswith("#")
            ):
                continue

            # Have to figure out a bettery way to handle these
            # In the case where we do have relative URLs, we just make it absolute
            if any(x in href_lower for x in [
                "ref_=", "track", "redirect", "sessionid", "signin", "register"
            ]):
                continue
            full_url = urljoin(self.base_url, href)

            # Skipping any other type of URL. Will have to make this a confugrable parameter
            parsed = urlparse(full_url)
            if parsed.scheme not in {"http", "https", "mailto", "ftp", "tel"}:
                continue

            clean_hrefs.append(full_url)

        # Before moving forward, we can filter them based on entropy
        """
        From what I noticed, big sites like amazon or facebook, have lots and lots of URLs and most of them
        contain a bunch of random strings for IDs and whatnot. We don't want that because that gives no
        additional context to the model regarding what the href is actually for!

        So, we'll strip those based on entropy. I noticed from multiple scans that the shannon entropy for
        such URLs are almost always greater than 5. Its interesting...
        """

        output = [href for href in clean_hrefs if url_entropy(href) < 5.0]
        return output


    async def _extract_all_text(self) -> List:
        lines = self.body_text.split("\n")
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        return non_empty_lines


    async def _extract_input_fields(
        self,
        known_fields: List = None,
    ) -> List[dict]:
        """
        Extracts and verifies fillable input fields. We're passing to it all the valid fields we already know
        of so that it caches it and doesn't mess with the actual DOM during execution. 

        Args:
            known_fields : List[Dict], optional
            Previously detected valid fields (to avoid duplicate fills).

        Returns:
            List[Dict]
                List of valid fillable fields with tag/type/id/name/selector info.
        """

        valid_fields = [] if known_fields is None else known_fields.copy()
        seen_selectors = {f["selector"] for f in valid_fields if f.get("selector")}

        for el in self.elements:
            try:
                is_visible = await el.is_visible()
                is_enabled = await el.is_enabled()
                if not (is_visible and is_enabled):
                    continue

                tag = (await el.evaluate("e => e.tagName.toLowerCase()")).strip()
                input_type = await el.get_attribute("type")
                input_type = (input_type or "text").lower().strip()
                existing_value = await el.input_value() if tag in ["input", "textarea"] else ""

                if tag not in {"input", "textarea", "select"}:
                    continue
                if input_type in {"hidden", "submit", "button", "checkbox", "radio", "file"}:
                    continue

                field_info = {
                    "tag": tag,
                    "type": input_type,
                    "id": await el.get_attribute("id"),
                    "name": await el.get_attribute("name"),
                    "placeholder": await el.get_attribute("placeholder"),
                    "aria_label": await el.get_attribute("aria-label"),
                    "selector": None,
                }

                if field_info["id"]:
                    selector = f"#{field_info['id']}"
                elif field_info["name"]:
                    selector = f"{field_info['tag']}[name='{field_info['name']}']"
                elif field_info["placeholder"]:
                    selector = f"{field_info['tag']}[placeholder='{field_info['placeholder']}']"
                elif field_info["aria_label"]:
                    selector = f"{field_info['tag']}[aria-label='{field_info['aria_label']}']"
                else:
                    selector = f"{field_info['tag']}:nth-of-type(unknown)"

                field_info["selector"] = selector


                # If the field is already filled or we've seen it before,
                # Then we can skip it
                if selector in seen_selectors:
                    continue

                if existing_value and existing_value.strip():
                    valid_fields.append(field_info)
                    seen_selectors.add(selector)
                    continue

                # Filling it and seein
                await el.fill(self.test_value, timeout=1500)
                await asyncio.sleep(0.05)
                new_value = await el.input_value()

                if self.test_value in new_value:
                    valid_fields.append(field_info)
                    seen_selectors.add(selector)
                    await el.fill("")  # clearing the field after testing it
                else:
                    pass  # ignore false positives

            except PlaywrightTimeoutError:
                continue
            except Exception:
                continue

        return valid_fields

    async def extract(self) -> dict:
        """
        Runs all extraction functions and returns a unified cleaned_dom dictionary.

        Returns:
            dict: A dictionary containing hyperlinks, input fields, clickable fields, and text content.
        """
        cleaned_dom = {
            "hyperlinks": None,
            "input_fields": None,
            "clickable_fields": None,
            "actual_text": None,
        }

        try:
            cleaned_dom["hyperlinks"] = self._extract_href()
        except Exception as e:
            cleaned_dom["hyperlinks"] = []
            print(f"Failed to extract hyperlinks: {e}")

        try:
            if self.clickable_fields_flag:
                cleaned_dom["clickable_fields"] = self._extract_clickables()
            else:
                cleaned_dom["clickable_fields"] = self._extract_clickables()[:10]
                # This is taking way too many tokens so restricting the total number.
                # There has to be a better way to do this!
        except Exception as e:
            cleaned_dom["clickable_fields"] = []
            print(f"Failed to extract clickables: {e}")

        try:
            cleaned_dom["actual_text"] = await self._extract_all_text()
        except Exception as e:
            cleaned_dom["actual_text"] = []
            print(f"Failed to extract text: {e}")

        try:
            cleaned_dom["input_fields"] = await self._extract_input_fields()
        except Exception as e:
            cleaned_dom["input_fields"] = []
            print(f"Failed to extract input fields: {e}")



        return cleaned_dom