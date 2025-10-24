#!/usr/bin/env python3
"""
Example demonstrating the ScrapeGraphAI Crawler with sitemap functionality.

This example shows how to use the crawler with sitemap enabled for better page discovery:
- Sitemap helps discover more pages efficiently
- Better coverage of website content
- More comprehensive crawling results

Requirements:
- Python 3.7+
- scrapegraph-py
- python-dotenv
- A valid API key (set in .env file as SGAI_API_KEY=your_key or environment variable)

Usage:
    python crawl_sitemap_example.py
"""

import json
import os
import time
from typing import Any, Dict

from dotenv import load_dotenv

from scrapegraph_py import Client


def poll_for_result(
    client: Client, crawl_id: str, max_attempts: int = 20
) -> Dict[str, Any]:
    """
    Poll for crawl results with intelligent backoff to avoid rate limits.

    Args:
        client: The ScrapeGraph client
        crawl_id: The crawl ID to poll for
        max_attempts: Maximum number of polling attempts

    Returns:
        The final result or raises an exception on timeout/failure
    """
    print("⏳ Starting to poll for results with rate-limit protection...")

    # Initial wait to give the job time to start processing
    time.sleep(15)

    for attempt in range(max_attempts):
        try:
            result = client.get_crawl(crawl_id)
            status = result.get("status")

            if status == "success":
                return result
            elif status == "failed":
                raise Exception(f"Crawl failed: {result.get('error', 'Unknown error')}")
            else:
                # Calculate progressive wait time: start at 15s, increase gradually
                base_wait = 15
                progressive_wait = min(60, base_wait + (attempt * 3))  # Cap at 60s

                print(
                    f"⏳ Status: {status} (attempt {attempt + 1}/{max_attempts}) - waiting {progressive_wait}s..."
                )
                time.sleep(progressive_wait)

        except Exception as e:
            if "rate" in str(e).lower() or "429" in str(e):
                wait_time = min(90, 45 + (attempt * 10))
                print(f"⚠️ Rate limit detected in error, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ Error polling for results: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(20)  # Wait before retry
                    continue
                raise

    raise Exception(f"⏰ Timeout: Job did not complete after {max_attempts} attempts")


def sitemap_crawling_example():
    """
    Sitemap-enabled Crawling Example

    This example demonstrates how to use sitemap for better page discovery.
    Sitemap helps the crawler find more pages efficiently by using the website's sitemap.xml.
    """
    print("=" * 60)
    print("SITEMAP-ENABLED CRAWLING EXAMPLE")
    print("=" * 60)
    print("Use case: Comprehensive website crawling with sitemap discovery")
    print("Benefits: Better page coverage, more efficient crawling")
    print("Features: Sitemap-based page discovery, structured data extraction")
    print()

    # Initialize the client
    client = Client.from_env()

    # Target URL - using a website that likely has a sitemap
    url = "https://www.giemmeagordo.com/risultati-ricerca-annunci/?sort=newest&search_city=&search_lat=null&search_lng=null&search_category=0&search_type=0&search_min_price=&search_max_price=&bagni=&bagni_comparison=equal&camere=&camere_comparison=equal"

    # Schema for real estate listings
    schema = {
        "type": "object",
        "properties": {
            "listings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "price": {"type": "string"},
                        "location": {"type": "string"},
                        "description": {"type": "string"},
                        "features": {"type": "array", "items": {"type": "string"}},
                        "url": {"type": "string"},
                    },
                },
            }
        },
    }

    prompt = "Extract all real estate listings with their details including title, price, location, description, and features"

    print(f"🌐 Target URL: {url}")
    print("🤖 AI Prompt: Extract real estate listings")
    print("📊 Crawl Depth: 1")
    print("📄 Max Pages: 10")
    print("🗺️ Use Sitemap: True (enabled for better page discovery)")
    print("🏠 Same Domain Only: True")
    print("💾 Cache Website: True")
    print("💡 Mode: AI extraction with sitemap discovery")
    print()

    # Start the sitemap-enabled crawl job
    print("🚀 Starting sitemap-enabled crawl job...")

    # Call crawl with sitemap=True for better page discovery
    response = client.crawl(
        url=url,
        prompt=prompt,
        data_schema=schema,
        extraction_mode=True,  # AI extraction mode
        depth=1,
        max_pages=10,
        same_domain_only=True,
        cache_website=True,
        sitemap=True,  # Enable sitemap for better page discovery
    )

    crawl_id = response.get("crawl_id") or response.get("task_id")

    if not crawl_id:
        print("❌ Failed to start sitemap-enabled crawl job")
        return

    print(f"📋 Crawl ID: {crawl_id}")
    print("⏳ Polling for results...")
    print()

    # Poll for results with rate-limit protection
    try:
        result = poll_for_result(client, crawl_id, max_attempts=20)

        print("✅ Sitemap-enabled crawl completed successfully!")
        print()

        result_data = result.get("result", {})
        llm_result = result_data.get("llm_result", {})
        crawled_urls = result_data.get("crawled_urls", [])
        credits_used = result_data.get("credits_used", 0)
        pages_processed = result_data.get("pages_processed", 0)

        # Prepare JSON output
        json_output = {
            "crawl_results": {
                "pages_processed": pages_processed,
                "credits_used": credits_used,
                "cost_per_page": (
                    credits_used / pages_processed if pages_processed > 0 else 0
                ),
                "crawled_urls": crawled_urls,
                "sitemap_enabled": True,
            },
            "extracted_data": llm_result,
        }

        # Print JSON output
        print("📊 RESULTS IN JSON FORMAT:")
        print("-" * 40)
        print(json.dumps(json_output, indent=2, ensure_ascii=False))

        # Print summary
        print("\n" + "=" * 60)
        print("📈 CRAWL SUMMARY:")
        print("=" * 60)
        print(f"✅ Pages processed: {pages_processed}")
        print(f"💰 Credits used: {credits_used}")
        print(f"🔗 URLs crawled: {len(crawled_urls)}")
        print(f"🗺️ Sitemap enabled: Yes")
        print(f"📊 Data extracted: {len(llm_result.get('listings', []))} listings found")

    except Exception as e:
        print(f"❌ Sitemap-enabled crawl failed: {str(e)}")


def main():
    """Run the sitemap crawling example."""
    print("🌐 ScrapeGraphAI Crawler - Sitemap Example")
    print("Comprehensive website crawling with sitemap discovery")
    print("=" * 60)

    # Load environment variables from .env file
    load_dotenv()

    # Check if API key is set
    api_key = os.getenv("SGAI_API_KEY")
    if not api_key:
        print("⚠️ Please set your API key in the environment variable SGAI_API_KEY")
        print("   Option 1: Create a .env file with: SGAI_API_KEY=your_api_key_here")
        print(
            "   Option 2: Set environment variable: export SGAI_API_KEY=your_api_key_here"
        )
        print()
        print("   You can get your API key from: https://dashboard.scrapegraphai.com")
        return

    print(f"🔑 Using API key: {api_key[:10]}...")
    print()

    # Run the sitemap crawling example
    sitemap_crawling_example()

    print("\n" + "=" * 60)
    print("🎉 Example completed!")
    print("💡 This demonstrates sitemap-enabled crawling:")
    print("   • Better page discovery using sitemap.xml")
    print("   • More comprehensive website coverage")
    print("   • Efficient crawling of structured websites")
    print("   • Perfect for e-commerce, news sites, and content-heavy websites")


if __name__ == "__main__":
    main()
