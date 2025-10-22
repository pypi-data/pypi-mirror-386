import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from .config import BASE, AJAX_URL, OUTPUT_DIR


# Fetch Page

async def fetch_page(session, page_num, year_id):
    """
    Fetch a single page of PDF links from the CBSL website.
    Returns a list of (date_object, pdf_url) tuples.
    """
    payload = {
        "view_name": "price_report",
        "view_display_id": "block_1",
        "view_path": "node/144",
        "view_base_path": "publications/price",
        "pager_element": 0,
        "page": page_num,
        "field_year_tid": year_id,
        "field_month_tid": "All",
    }

    async with session.post(AJAX_URL, data=payload) as response:
        if response.status != 200:
            print(f"Failed to fetch page {page_num}: HTTP {response.status}")
            return []

        json_data = await response.json()

        html_content = next(
            (item.get("data") for item in json_data if item.get("command") == "insert"),
            None,
        )
        if not html_content:
            print(f"No HTML content found on page {page_num}")
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        pdf_links = []

        for link in soup.select("a[href$='.pdf']"):
            pdf_url = urljoin(BASE, link["href"])
            link_text = link.get_text(strip=True)

            date_object = None
            try:
                date_object = datetime.strptime(
                    link_text.split("-")[-1].strip(), "%d %B %Y"
                )
            except Exception:
                pass

            pdf_links.append((date_object, pdf_url))

        return pdf_links


# Download pdf file

async def download_pdf(session, date_obj, url, output_dir):
    """Download and save a single PDF file."""
    os.makedirs(output_dir, exist_ok=True)

    filename = (
        f"{date_obj.strftime('%Y-%m-%d')}.pdf" if date_obj else "unknown_date.pdf"
    )
    output_path = os.path.join(output_dir, filename)

    if os.path.exists(output_path):
        print(f"Skipping {filename} (already exists)")
        return

    try:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"Failed {url}: HTTP {response.status}")
                return
            pdf_content = await response.read()
            with open(output_path, "wb") as f:
                f.write(pdf_content)
            print(f"Saved {output_path}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")


# Main function

async def main(years=None, outputdir=None):
    """
    Download PDFs for given list of years.

    Args:
        years (list[str] or list[int]): Years to download (e.g., ["2025", "2024"])
    """
    async with aiohttp.ClientSession() as session:
        # CBSL year ID mapping
        year_map = {
            "88": 2025,
            "87": 2024,
            "86": 2023,
            "85": 2022,
            "84": 2021,
            "83": 2020,
        }

        # Determine which years to process
        if not years:
            years = [str(v) for v in year_map.values()]
        years = [str(y) for y in years]

        # Reverse lookup: find CBSL ID for each year number
        reverse_map = {str(v): k for k, v in year_map.items()}

        for year in years:
            if year not in reverse_map:
                print(f"Unknown year {year} (skipped)")
                continue

            year_id = reverse_map[year]
            print(f"\nFetching reports for {year} (year_id={year_id})...")
            year_output_dir = OUTPUT_DIR / str(year)
            year_output_dir.mkdir(parents=True, exist_ok=True)

            all_links = []
            page = 0

            while True:
                reports = await fetch_page(session, page, year_id)
                if not reports:
                    print(f"No more reports at page {page} for {year}.")
                    break
                print(f"Found {len(reports)} reports on page {page} ({year})")
                all_links.extend(reports)
                page += 1
                await asyncio.sleep(1)

            print(f"Total PDFs found for {year}: {len(all_links)}")

            # Deduplicate by URL
            unique_links = {}
            for date_obj, url in all_links:
                if url not in unique_links:
                    unique_links[url] = date_obj

            download_limit = asyncio.Semaphore(5)

            async def download_with_limit(date_obj, url):
                async with download_limit:
                    await download_pdf(session, date_obj, url, year_output_dir)

            tasks = [
                download_with_limit(date_obj, url)
                for url, date_obj in unique_links.items()
            ]
            import os
            await asyncio.gather(*tasks)
            print(f"Completed downloads for {year} → {year_output_dir}")

# New async function to download PDFs to a specified output directory
async def download_pdfs_to(years, outputdir):
    """
    Download PDFs for the given list of years to the specified output directory.
    Args:
        years (list[str] or list[int]): Years to download (e.g., [2025, 2024])
        outputdir (str or Path): Output directory to save PDFs
    """
    from pathlib import Path
    output_base = Path(outputdir)
    async with aiohttp.ClientSession() as session:
        # CBSL year ID mapping
        year_map = {
            "88": 2025,
            "87": 2024,
            "86": 2023,
            "85": 2022,
            "84": 2021,
            "83": 2020,
        }

        # Determine which years to process
        if not years:
            years = [str(v) for v in year_map.values()]
        years = [str(y) for y in years]

        # Reverse lookup: find CBSL ID for each year number
        reverse_map = {str(v): k for k, v in year_map.items()}

        for year in years:
            if year not in reverse_map:
                print(f"Unknown year {year} (skipped)")
                continue

            year_id = reverse_map[year]
            print(f"\nFetching reports for {year} (year_id={year_id})...")
            year_output_dir = output_base / str(year)
            year_output_dir.mkdir(parents=True, exist_ok=True)

            all_links = []
            page = 0

            while True:
                reports = await fetch_page(session, page, year_id)
                if not reports:
                    print(f"No more reports at page {page} for {year}.")
                    break
                print(f"Found {len(reports)} reports on page {page} ({year})")
                all_links.extend(reports)
                page += 1
                await asyncio.sleep(1)

            print(f"Total PDFs found for {year}: {len(all_links)}")

            # Deduplicate by URL
            unique_links = {}
            for date_obj, url in all_links:
                if url not in unique_links:
                    unique_links[url] = date_obj

            download_limit = asyncio.Semaphore(5)

            async def download_with_limit(date_obj, url):
                async with download_limit:
                    await download_pdf(session, date_obj, url, year_output_dir)

            tasks = [
                download_with_limit(date_obj, url)
                for url, date_obj in unique_links.items()
            ]
            await asyncio.gather(*tasks)
            print(f"Completed downloads for {year} → {year_output_dir}")