#!/usr/bin/env python3
"""
WebSum - Photon Results Summarizer

This script:
1. Traverses through /home/jarvis/photon_results and its subfolders
2. Extracts URLs from text files in these folders
3. Fetches and extracts content from these URLs using BeautifulSoup
4. Summarizes content using various methods:
   - Built-in TextRank summarizer (no API required)
   - Ollama models (local)
   - ChatGPT (OpenAI API)
   - Hugging Face models
5. Processes URLs in batches, showing individual summaries and an overall batch summary
6. Asks user if they want to continue after each batch
7. Saves the summaries to a summary.txt file in each subfolder
"""

import os
import re
import json
import time
import argparse
import requests
import sys
import logging
import math
import heapq
import string
import nltk
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

# Try to download nltk data if it's not already available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Downloading NLTK punkt tokenizer...")
    nltk.download('punkt', quiet=True)

__version__ = "1.1"

# Default configuration
PHOTON_ROOT = "/home/jarvis/photon_results"
BATCH_SIZE = 10
DEFAULT_OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_HF_API_URL = "https://api-inference.huggingface.co/models/"
DEFAULT_TIMEOUT = 90  # seconds
MAX_CONTENT_LENGTH = 8000  # characters

# Default API keys (can be overridden by environment variables or user input)
DEFAULT_OPENAI_API_KEY = ""
DEFAULT_HF_API_KEY = ""

# Regular expression for extracting URLs
URL_PATTERN = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[^)\s]*)?')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextRankSummarizer:
    """Implementation of TextRank algorithm for text summarization"""

    def __init__(self):
        self.stop_words = set([
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'were', 'will', 'with'
        ])

    def _clean_text(self, text):
        """Remove special characters and convert to lowercase"""
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        return text.lower()

    def _extract_sentences(self, text):
        """Extract sentences from text"""
        return nltk.sent_tokenize(text)

    def _compute_word_frequencies(self, text):
        """Compute word frequencies in the text"""
        word_freq = Counter()
        clean_text = self._clean_text(text)

        for word in clean_text.split():
            if word not in self.stop_words:
                word_freq[word] += 1

        # Normalize frequencies
        max_freq = max(word_freq.values()) if word_freq else 1
        for word in word_freq:
            word_freq[word] = word_freq[word] / max_freq

        return word_freq

    def _score_sentences(self, sentences, word_freq):
        """Score sentences based on word frequency"""
        sentence_scores = {}

        for i, sentence in enumerate(sentences):
            clean_sentence = self._clean_text(sentence)

            # Skip very short sentences (likely not meaningful content)
            if len(clean_sentence.split()) <= 3:
                continue

            for word in clean_sentence.split():
                if word in word_freq:
                    if i not in sentence_scores:
                        sentence_scores[i] = 0
                    sentence_scores[i] += word_freq[word]

        return sentence_scores

    def summarize(self, text, ratio=0.2):
        """Generate a summary using the TextRank algorithm"""
        if not text or len(text.strip()) == 0:
            return ""

        # Extract sentences
        sentences = self._extract_sentences(text)

        # Handle very short texts
        if len(sentences) <= 3:
            return text

        # Calculate word frequencies
        word_freq = self._compute_word_frequencies(text)

        # Score sentences
        sentence_scores = self._score_sentences(sentences, word_freq)

        # Calculate number of sentences for the summary
        num_sentences = max(1, math.ceil(len(sentences) * ratio))

        # Get top-scoring sentence indices
        top_sentence_indices = heapq.nlargest(num_sentences,
                                           sentence_scores,
                                           key=sentence_scores.get)

        # Sort indices to maintain original order
        top_sentence_indices = sorted(top_sentence_indices)

        # Construct summary
        summary = ' '.join([sentences[i] for i in top_sentence_indices])

        return summary

    def extract_keywords(self, text, ratio=0.1):
        """Extract keywords from the text"""
        word_freq = self._compute_word_frequencies(text)

        # Calculate number of keywords
        num_keywords = max(5, math.ceil(len(word_freq) * ratio))

        # Get top words
        keywords = heapq.nlargest(num_keywords, word_freq, key=word_freq.get)

        return ', '.join(keywords)

def setup_argparse():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract, fetch, and summarize URLs from Photon results",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--root-dir", type=str, default=PHOTON_ROOT,
                        help="Root directory containing Photon results")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE,
                        help="Number of URLs to process in each batch")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help="Timeout for HTTP requests and API calls (seconds)")
    parser.add_argument("--ollama-url", type=str, default=DEFAULT_OLLAMA_API_URL,
                        help="Ollama API endpoint URL")
    parser.add_argument("--max-content", type=int, default=MAX_CONTENT_LENGTH,
                        help="Maximum content length to send for summarization")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug mode with additional information")
    parser.add_argument("--auto", action="store_true",
                        help="Start in automatic mode (no prompts between batches)")

    return parser.parse_args()

def configure_logging(verbose, debug):
    """Configure logging level based on command line arguments."""
    if debug:
        logger.setLevel(logging.DEBUG)
    elif verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

def print_header(text):
    """Print a formatted header."""
    try:
        width = min(os.get_terminal_size().columns, 80)
    except OSError:
        width = 80
    print(f"\n\033[1;36m{'=' * width}\n{text.center(width)}\n{'=' * width}\033[0m\n")

def extract_urls_from_file(file_path):
    """Extract URLs from a file using regex."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Find all URLs in the content
        urls = URL_PATTERN.findall(content)

        # Remove duplicates while preserving order
        clean_urls = []
        seen = set()
        for url in urls:
            # Clean up the URL to remove trailing punctuation
            url = url.rstrip('.,;:\'\"!?)')

            # Skip duplicates
            if url not in seen:
                seen.add(url)
                clean_urls.append(url)

        return clean_urls
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []

def get_domain(url):
    """Extract domain from URL."""
    parsed = urlparse(url)
    domain = parsed.netloc
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def fetch_webpage_content(url, timeout=DEFAULT_TIMEOUT):
    """Fetch and extract text content from a webpage."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # Make the request but don't raise for status yet
        response = requests.get(url, timeout=timeout, headers=headers)

        # Check specifically for 404 status
        if response.status_code == 404:
            logger.warning(f"404 Not Found: {url}")
            return {
                "title": "404 Not Found",
                "text": "",
                "url": url,
                "status_code": 404,
                "error": True
            }

        # Check for other error status codes
        if response.status_code >= 400:
            logger.warning(f"HTTP Error {response.status_code}: {url}")
            return {
                "title": f"HTTP Error {response.status_code}",
                "text": "",
                "url": url,
                "status_code": response.status_code,
                "error": True
            }

        # If we got here, status code is good, raise for other errors
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type and 'application/json' not in content_type:
            return {
                "title": f"Unsupported content type: {content_type}",
                "text": "",
                "url": url,
                "status_code": response.status_code,
                "error": True
            }

        soup = BeautifulSoup(response.content, "html.parser")

        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else "No title found"

        # Remove script, style, nav, etc.
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.extract()

        # Extract text from paragraph tags first
        paragraphs = soup.find_all("p")
        if paragraphs:
            page_text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        else:
            # If no paragraphs, try other common content containers
            content_containers = soup.select("article, .content, .main, #content, #main")
            if content_containers:
                page_text = "\n\n".join([el.get_text(strip=True) for el in content_containers])
            else:
                # Fallback to all text
                page_text = soup.get_text(separator="\n\n", strip=True)

        # Clean up text
        page_text = re.sub(r'\n{3,}', '\n\n', page_text)
        page_text = re.sub(r'\s{2,}', ' ', page_text)

        # Return content with success status
        return {
            "title": title,
            "text": page_text,
            "url": url,
            "status_code": response.status_code,
            "error": False
        }
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return {
            "title": f"Error: {str(e)[:100]}",
            "text": "",
            "url": url,
            "status_code": 0,  # Use 0 to indicate a connection/non-HTTP error
            "error": True
        }

def check_ollama_connection(url, timeout=5):
    """Check if Ollama server is running and reachable."""
    try:
        base_url = url
        if "/api/generate" in url:
            base_url = url.split("/api/generate")[0]

        response = requests.get(f"{base_url}/api/tags", timeout=timeout)
        response.raise_for_status()

        # Check if we got a valid response with models
        data = response.json()
        if "models" in data and len(data["models"]) > 0:
            logger.debug(f"Available Ollama models: {[m['name'] for m in data['models']]}")
            return True
        else:
            logger.warning("No models found in Ollama")
            return False
    except Exception as e:
        logger.error(f"Ollama connection failed: {e}")
        return False

def create_spinner():
    """Create a simple spinner to indicate progress during API calls."""
    import itertools
    import threading

    spinner_active = [True]
    spinner_thread = None

    def spin():
        for c in itertools.cycle('|/-\\'):
            if not spinner_active[0]:
                break
            sys.stdout.write(f"\r{c} ")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\r')
        sys.stdout.flush()

    spinner_thread = threading.Thread(target=spin)
    spinner_thread.daemon = True
    spinner_thread.start()

    def stop_spinner():
        spinner_active[0] = False
        if spinner_thread:
            spinner_thread.join(0.5)

    return stop_spinner

def summarize_with_textrank(content, depth, timeout=DEFAULT_TIMEOUT):
    """Summarize content using TextRank algorithm."""
    text = content["text"]
    if not text:
        return "No content to summarize."

    print("Generating summary with TextRank...", end="", flush=True)
    stop_spinner = create_spinner()

    try:
        # Create TextRank summarizer instance
        summarizer = TextRankSummarizer()

        # Adjust ratio based on depth parameter
        if depth == "short":
            ratio = 0.05  # Very short summary
        elif depth == "medium":
            ratio = 0.1   # Medium summary
        else:  # detailed
            ratio = 0.3   # Detailed summary

        # Apply summarization
        summary = summarizer.summarize(text, ratio=ratio)

        # If summary is empty (happens with short texts), return the original text
        if not summary:
            if len(text) > 200:
                summary = text[:200] + "..."
            else:
                summary = text

        # Add keywords if the depth is medium or detailed
        if depth in ["medium", "detailed"]:
            try:
                key_terms = summarizer.extract_keywords(text, ratio=0.01)
                if key_terms:
                    summary += f"\n\nKey terms: {key_terms}"
            except Exception as e:
                logger.warning(f"Error extracting keywords: {e}")

        stop_spinner()
        print(" Done!")
        return summary
    except Exception as e:
        stop_spinner()
        print(f" Error: {str(e)[:100]}")
        logger.error(f"TextRank summarization error: {e}")
        return f"Error generating summary: {str(e)[:100]}"

def summarize_batch_with_textrank(summaries):
    """Generate an overall summary of a batch using TextRank summarization."""
    # Combine all the individual summaries into one text
    combined_text = "\n\n".join([f"Title: {s['title']}\nSummary: {s['summary']}"
                                for s in summaries
                                if s["summary"] and not s["summary"].startswith("Error")])

    if not combined_text:
        return "No valid summaries to create an overall summary."

    try:
        # Use the TextRank algorithm to extract the key points
        summarizer = TextRankSummarizer()
        overall_summary = summarizer.summarize(combined_text, ratio=0.3)

        # If summary is empty, use a default message
        if not overall_summary:
            overall_summary = "The batch contains varied content without clear unifying themes."

        # Add keywords to provide additional context
        try:
            key_terms = summarizer.extract_keywords(combined_text, ratio=0.02)
            if key_terms:
                overall_summary += f"\n\nCommon themes across this batch: {key_terms}"
        except Exception:
            pass  # Ignore keyword errors in batch summary

        return overall_summary
    except Exception as e:
        logger.error(f"Error generating batch summary with TextRank: {e}")
        return "Could not generate an overall batch summary."

def summarize_with_ollama(content, model, depth, api_url=DEFAULT_OLLAMA_API_URL, timeout=DEFAULT_TIMEOUT):
    """Summarize content using Ollama API."""
    # Truncate content if too long
    text = content["text"]
    if len(text) > MAX_CONTENT_LENGTH:
        text = text[:MAX_CONTENT_LENGTH] + "... [truncated]"

    # Build prompt based on depth
    if depth == "short":
        prompt = f"Summarize the following content in 1-2 concise sentences. Provide any additional context or knowledge you have that's relevant to the topic:\n\n{text}"
    elif depth == "medium":
        prompt = f"Summarize the following content in one paragraph (3-5 sentences). Include important details and provide any additional context or knowledge you have that's relevant to the topic:\n\n{text}"
    else:  # detailed
        prompt = f"Provide a detailed summary of the following content, including important details, relevant facts, and any additional context or knowledge you have that's relevant to the topic:\n\n{text}"

    print("Generating summary with Ollama...", end="", flush=True)
    stop_spinner = create_spinner()

    try:
        response = requests.post(
            api_url,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout
        )
        response.raise_for_status()
        result = response.json()
        summary = result.get("response", "No summary generated.")

        stop_spinner()
        print(" Done!")
        return summary.strip()
    except Exception as e:
        stop_spinner()
        print(f" Error: {str(e)[:100]}")
        logger.error(f"Ollama API error: {e}")
        return f"Error generating summary: {str(e)[:100]}"

def summarize_with_openai(content, api_key, depth, timeout=DEFAULT_TIMEOUT):
    """Summarize content using OpenAI API."""
    text = content["text"]
    if len(text) > MAX_CONTENT_LENGTH:
        text = text[:MAX_CONTENT_LENGTH] + "... [truncated]"

    if depth == "short":
        system_prompt = "You are a skilled summarizer. Create a 1-2 sentence summary capturing the key points. Include any additional context or knowledge you have that's relevant to the topic."
    elif depth == "medium":
        system_prompt = "You are a skilled summarizer. Create a single paragraph summary (3-5 sentences) capturing the main ideas. Include any additional context or knowledge you have that's relevant to the topic."
    else:  # detailed
        system_prompt = "You are a skilled summarizer. Create a detailed summary capturing important details and relevant facts. Include any additional context or knowledge you have that's relevant to the topic."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
    }

    print("Generating summary with ChatGPT...", end="", flush=True)
    stop_spinner = create_spinner()

    try:
        response = requests.post(
            DEFAULT_OPENAI_API_URL,
            headers=headers,
            json=data,
            timeout=timeout
        )
        response.raise_for_status()
        result = response.json()
        summary = result["choices"][0]["message"]["content"]

        stop_spinner()
        print(" Done!")
        return summary.strip()
    except Exception as e:
        stop_spinner()
        print(f" Error: {str(e)[:100]}")
        logger.error(f"OpenAI API error: {e}")
        return f"Error generating summary: {str(e)[:100]}"

def summarize_with_huggingface(content, api_key, model=None, depth="medium", timeout=DEFAULT_TIMEOUT):
    """Summarize content using Hugging Face API."""
    if not model:
        model = "facebook/bart-large-cnn"

    text = content["text"]
    if len(text) > MAX_CONTENT_LENGTH:
        text = text[:MAX_CONTENT_LENGTH] + "... [truncated]"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Adjust parameters based on depth
    parameters = {}
    if depth == "short":
        parameters = {"max_length": 50, "min_length": 20}
    elif depth == "medium":
        parameters = {"max_length": 100, "min_length": 50}
    else:  # detailed
        parameters = {"max_length": 200, "min_length": 100}

    payload = {
        "inputs": text,
        "parameters": parameters
    }

    print(f"Generating summary with Hugging Face ({model})...", end="", flush=True)
    stop_spinner = create_spinner()

    try:
        response = requests.post(
            f"{DEFAULT_HF_API_URL}{model}",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
        result = response.json()

        stop_spinner()
        print(" Done!")

        if isinstance(result, list) and len(result) > 0:
            return result[0].get("summary_text", "No summary generated.").strip()
        else:
            return "No summary generated."
    except Exception as e:
        stop_spinner()
        print(f" Error: {str(e)[:100]}")
        logger.error(f"Hugging Face API error: {e}")
        return f"Error generating summary: {str(e)[:100]}"

def summarize_content(content, provider, model, depth, api_keys, api_urls, timeout=DEFAULT_TIMEOUT):
    """Summarize content using the selected provider."""
    if not content["text"]:
        return f"No content available for {content['url']}"

    if provider == "textrank":
        return summarize_with_textrank(content, depth, timeout)
    elif provider == "ollama":
        return summarize_with_ollama(content, model, depth, api_urls["ollama"], timeout)
    elif provider == "openai":
        if not api_keys["openai"]:
            return "Error: OpenAI API key not provided."
        return summarize_with_openai(content, api_keys["openai"], depth, timeout)
    elif provider == "huggingface":
        if not api_keys["huggingface"]:
            return "Error: Hugging Face API key not provided."
        return summarize_with_huggingface(content, api_keys["huggingface"], model, depth, timeout)
    else:
        return f"Error: Unknown provider '{provider}'."

def process_batch(urls, provider, model, depth, api_keys, api_urls, timeout=DEFAULT_TIMEOUT, automatic_mode=False):
    """Process a batch of URLs: fetch, summarize, and display results."""
    valid_contents = []
    invalid_urls = []
    summaries = []
    all_404 = True  # Flag to track if all URLs result in 404 errors

    print(f"\nProcessing {len(urls)} URLs...")

    # Fetch content from URLs
    contents = []
    with ThreadPoolExecutor(max_workers=min(len(urls), 5)) as executor:
        future_to_url = {executor.submit(fetch_webpage_content, url, timeout): url for url in urls}
        for i, future in enumerate(as_completed(future_to_url), 1):
            url = future_to_url[future]
            try:
                content = future.result()
                # Print appropriate message based on content status
                if content["error"]:
                    if content["status_code"] == 404:
                        # In automatic mode, don't show 404 messages
                        if not automatic_mode:
                            print(f"[{i}/{len(urls)}] Skipping 404 Not Found: {url}")
                        invalid_urls.append(url)
                    else:
                        print(f"[{i}/{len(urls)}] Error: {content['title']} for {url}")
                        contents.append(content)
                        all_404 = False  # Found an error that's not a 404
                else:
                    print(f"[{i}/{len(urls)}] Fetched: {url} ({len(content['text'])} chars)")
                    contents.append(content)
                    valid_contents.append(content)
                    all_404 = False  # Found at least one valid URL
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                print(f"[{i}/{len(urls)}] Error fetching {url}: {str(e)[:100]}")
                contents.append({
                    "title": f"Error fetching {url}",
                    "text": "",
                    "url": url,
                    "status_code": 0,
                    "error": True
                })

    # Log the number of URLs being skipped due to 404
    if invalid_urls:
        logger.info(f"Skipping {len(invalid_urls)} URLs due to 404 errors")
        if not automatic_mode:  # Only show in non-automatic mode
            print(f"\n\033[1;33mSkipping {len(invalid_urls)} URLs due to 404 errors\033[0m")

    # Summarize content (excluding 404 pages)
    for i, content in enumerate([c for c in contents if not (c.get("status_code") == 404)], 1):
        if not content["text"]:
            print(f"\n\033[1;33m[{i}/{len(contents) - len(invalid_urls)}] Error: Could not extract content from {content['url']}\033[0m")
            summaries.append({
                "title": content["title"],
                "url": content["url"],
                "summary": "No content could be extracted from this URL."
            })
            continue

        print(f"\n\033[1;33m[{i}/{len(contents) - len(invalid_urls)}] Summarizing: {content['title']}\033[0m")
        summary = summarize_content(content, provider, model, depth, api_keys, api_urls, timeout)

        domain = get_domain(content["url"])
        print(f"\n\033[1;32m[{i}/{len(contents) - len(invalid_urls)}] Summary for {content['title']}\033[0m")
        print(f"\033[0;36m{content['url']}\033[0m \033[0;90m({domain})\033[0m")
        print(f"{summary}")
        print("-" * 60)

        summaries.append({
            "title": content["title"],
            "url": content["url"],
            "summary": summary
        })

    # Generate overall summary for the batch (only for valid contents)
    if valid_contents and summaries and any(s["summary"] and not s["summary"].startswith("Error") for s in summaries):
        print("\nGenerating overall summary for this batch...")

        # Use TextRank's specialized batch summarization if provider is textrank
        if provider == "textrank":
            overall_summary = summarize_batch_with_textrank(summaries)
        else:
            # Create a prompt with all individual summaries for other providers
            overall_prompt = {
                "title": f"Overall summary for batch of {len(summaries)} websites",
                "text": "Based on the following summaries, provide an overall summary that highlights common themes and important points:\n\n" +
                       "\n\n".join([f"Title: {s['title']}\nSummary: {s['summary']}" for s in summaries if s["summary"] and not s["summary"].startswith("Error")])
            }

            overall_summary = summarize_content(overall_prompt, provider, model, depth, api_keys, api_urls, timeout)

        print("\n\033[1;32mOVERALL BATCH SUMMARY:\033[0m")
        print(overall_summary)
        print("=" * 60)

        return summaries, overall_summary, all_404

    return summaries, "No valid summaries generated for this batch.", all_404

def collect_urls_from_folders(root_dir):
    """Collect URLs from all subfolders in the root directory."""
    folder_urls = {}

    if not os.path.isdir(root_dir):
        logger.error(f"Root directory {root_dir} does not exist.")
        return folder_urls

    # List all subfolders
    subfolders = [f for f in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, f))]
    if not subfolders:
        logger.warning(f"No subfolders found in {root_dir}.")
        return folder_urls

    # Process each subfolder
    for subfolder in subfolders:
        subfolder_path = os.path.join(root_dir, subfolder)
        urls = []

        # Get all text files in the subfolder
        text_files = [f for f in os.listdir(subfolder_path)
                      if f.endswith('.txt') and f != 'summary.txt' and os.path.isfile(os.path.join(subfolder_path, f))]

        # Extract URLs from each text file
        for text_file in text_files:
            file_path = os.path.join(subfolder_path, text_file)
            file_urls = extract_urls_from_file(file_path)
            urls.extend(file_urls)

        # Remove duplicates while preserving order
        unique_urls = []
        seen = set()
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        if unique_urls:
            folder_urls[subfolder] = unique_urls

    return folder_urls

def choose_provider():
    """Let user choose the summarization provider."""
    print("\nChoose a summarization provider:")
    print("1) TextRank (built-in, no API required)")
    print("2) Ollama (local)")
    print("3) OpenAI (ChatGPT)")
    print("4) Hugging Face")

    while True:
        choice = input("Enter your choice (1-4): ").strip()
        if choice == "1":
            return "textrank"
        elif choice == "2":
            return "ollama"
        elif choice == "3":
            return "openai"
        elif choice == "4":
            return "huggingface"
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

def choose_model(provider):
    """Let user choose the model for the selected provider."""
    if provider == "textrank":
        # TextRank has no model options in this implementation
        return "textrank"

    elif provider == "ollama":
        print("\nChoose an Ollama model:")
        print("1) gemma3:12b")
        print("2) llama3:latest")
        print("3) deepseek-r1:8b")
        print("4) Other (enter name)")

        choice = input("Enter your choice (1-4): ").strip()
        if choice == "1":
            return "gemma3:12b"
        elif choice == "2":
            return "llama3:latest"
        elif choice == "3":
            return "deepseek-r1:8b"
        elif choice == "4":
            return input("Enter the model name: ").strip()
        else:
            print("Invalid choice. Using gemma3:12b.")
            return "gemma3:12b"

    elif provider == "openai":
        print("\nChoose an OpenAI model:")
        print("1) gpt-3.5-turbo")
        print("2) gpt-4 (if available)")

        choice = input("Enter your choice (1-2): ").strip()
        if choice == "1":
            return "gpt-3.5-turbo"
        elif choice == "2":
            return "gpt-4"
        else:
            print("Invalid choice. Using gpt-3.5-turbo.")
            return "gpt-3.5-turbo"

    elif provider == "huggingface":
        print("\nChoose a Hugging Face model:")
        print("1) facebook/bart-large-cnn (summarization)")
        print("2) sshleifer/distilbart-cnn-12-6 (faster summarization)")
        print("3) Other (enter name)")

        choice = input("Enter your choice (1-3): ").strip()
        if choice == "1":
            return "facebook/bart-large-cnn"
        elif choice == "2":
            return "sshleifer/distilbart-cnn-12-6"
        elif choice == "3":
            return input("Enter the model name: ").strip()
        else:
            print("Invalid choice. Using facebook/bart-large-cnn.")
            return "facebook/bart-large-cnn"

    return None

def choose_depth():
    """Let user choose the summarization depth."""
    print("\nChoose summarization depth:")
    print("1) Short (1-2 sentences)")
    print("2) Medium (one paragraph)")
    print("3) Detailed (comprehensive)")

    while True:
        choice = input("Enter your choice (1-3): ").strip()
        if choice == "1":
            return "short"
        elif choice == "2":
            return "medium"
        elif choice == "3":
            return "detailed"
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def get_api_keys(provider):
    """Get API keys for the selected provider."""
    api_keys = {
        "openai": DEFAULT_OPENAI_API_KEY,
        "huggingface": DEFAULT_HF_API_KEY
    }

    # No API keys needed for textrank
    if provider == "textrank":
        return api_keys

    if provider == "openai":
        key_input = input(f"\nEnter your OpenAI API key (or press Enter to use default/env var): ").strip()
        if key_input:
            api_keys["openai"] = key_input
        elif os.environ.get("OPENAI_API_KEY"):
            api_keys["openai"] = os.environ.get("OPENAI_API_KEY")

    elif provider == "huggingface":
        key_input = input(f"\nEnter your Hugging Face API key (or press Enter to use default/env var): ").strip()
        if key_input:
            api_keys["huggingface"] = key_input
        elif os.environ.get("HF_API_KEY"):
            api_keys["huggingface"] = os.environ.get("HF_API_KEY")

    return api_keys

def save_summary_to_file(folder_path, batch_summaries, batch_overall_summaries):
    """Save summaries to a file in the folder."""
    summary_path = os.path.join(folder_path, "summary.txt")

    try:
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("# WEBSITE SUMMARIES\n\n")

            for batch_idx, (summaries, overall) in enumerate(zip(batch_summaries, batch_overall_summaries), 1):
                f.write(f"## Batch {batch_idx}\n\n")

                for i, summary in enumerate(summaries, 1):
                    f.write(f"### {i}. {summary['title']}\n")
                    f.write(f"URL: {summary['url']}\n\n")
                    f.write(f"{summary['summary']}\n\n")

                f.write("### Overall Batch Summary\n\n")
                f.write(f"{overall}\n\n")
                f.write("-" * 40 + "\n\n")

            f.write("# COMPLETE FOLDER SUMMARY\n\n")

            # Create a summary of all batch overall summaries
            if batch_overall_summaries:
                f.write("Based on all batches processed, the websites in this folder cover:\n\n")
                for batch_idx, overall in enumerate(batch_overall_summaries, 1):
                    f.write(f"Batch {batch_idx}: {overall}\n\n")

        print(f"\nSummary saved to: {summary_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving summary to {summary_path}: {e}")
        print(f"Error saving summary: {str(e)}")
        return False

def check_for_key_press():
    """Check if a key has been pressed without blocking execution."""
    try:
        # Check if there's any input ready (non-blocking)
        import select
        ready, _, _ = select.select([sys.stdin], [], [], 0)
        if ready:
            # There's input ready, read it
            key = sys.stdin.readline().strip().lower()
            return key
        return None
    except Exception:
        return None

def main():
    """Main function."""
    args = setup_argparse()
    configure_logging(args.verbose, args.debug)

    print_header("WEBSUMMARIZER - PHOTON RESULTS SUMMARIZER")
    print(f"Version: {__version__}")

    # Choose summarization provider, model, and depth
    provider = choose_provider()
    model = choose_model(provider)
    depth = choose_depth()
    api_keys = get_api_keys(provider)

    api_urls = {
        "ollama": args.ollama_url,
        "openai": DEFAULT_OPENAI_API_URL,
        "huggingface": DEFAULT_HF_API_URL
    }

    # Check Ollama connection if needed
    if provider == "ollama" and not check_ollama_connection(args.ollama_url):
        print("\nError: Cannot connect to Ollama. Make sure Ollama is running.")
        print("You can start Ollama with: ollama serve")
        print(f"And pull the model with: ollama pull {model}")
        return 1

    # Collect URLs from folders
    print(f"\nCollecting URLs from subfolders in {args.root_dir}...")
    folder_urls = collect_urls_from_folders(args.root_dir)

    if not folder_urls:
        print("No URLs found in any subfolder.")
        return 1

    print(f"\nFound {len(folder_urls)} subfolders with URLs:")
    for folder, urls in folder_urls.items():
        print(f"- {folder}: {len(urls)} URLs")

    # Track automatic mode state
    automatic_mode = args.auto
    if automatic_mode:
        print("\nAutomatic mode enabled. Processing will continue until complete or interrupted.")
        print(f"Using batch size of 20 for automatic mode (overrides default of {args.batch_size}).")
        print("Press 'n' then Enter at any time to exit automatic mode.")
        print("Or press Ctrl+C at any time to stop processing and save results.")

    # Process each subfolder
    for folder, urls in folder_urls.items():
        folder_path = os.path.join(args.root_dir, folder)
        print_header(f"Processing folder: {folder}")
        print(f"Found {len(urls)} URLs to process")

        # Process URLs in batches
        batch_summaries = []
        batch_overall_summaries = []

        i = 0
        while i < len(urls):
            # Use batch size of 20 when in automatic mode, otherwise use the specified batch size
            current_batch_size = 20 if automatic_mode else args.batch_size
            batch = urls[i:i + current_batch_size]

            batch_number = i // current_batch_size + 1
            print_header(f"Processing batch {batch_number} ({len(batch)} URLs)")

            summaries, overall_summary, all_404 = process_batch(
                batch, provider, model, depth, api_keys, api_urls, args.timeout, automatic_mode
            )

            batch_summaries.append(summaries)
            batch_overall_summaries.append(overall_summary)

            # Move to next batch
            i += current_batch_size

            # Check if we should continue to the next batch
            if i < len(urls):
                if all_404:
                    # Automatically continue to next batch if all URLs were 404s
                    if not automatic_mode:  # Only show in non-automatic mode
                        print("\nAll URLs in this batch resulted in 404 errors. Automatically continuing to next batch...")
                    continue
                elif automatic_mode:
                    # In fully automatic mode, just continue without prompting
                    # Just print a brief status message
                    print("\nAutomatic mode active - continuing to next batch automatically.")
                    print("(Press 'n' then Enter to exit automatic mode)")
                    # Brief pause to allow for reading messages
                    time.sleep(1.0)

                    # Non-blocking check if 'n' was pressed to exit automatic mode
                    key = check_for_key_press()
                    if key == 'n':
                        automatic_mode = False
                        print("Automatic mode disabled. Will prompt before each batch.")
                        # FIX: Make sure to clearly ask about continuing and enforce input validation
                        while True:
                            choice = input("Continue with next batch? (y/n): ").strip().lower()
                            if choice == 'y':
                                break
                            elif choice == 'n':
                                print("Stopping at user request.")
                                i = len(urls)  # This will exit the outer while loop
                                break
                            else:
                                print("Please enter 'y' or 'n'.")
                else:
                    # FIX: Implement better input validation to ensure only valid inputs are accepted
                    valid_response = False
                    while not valid_response:
                        choice = input("\nContinue with next batch? (y/n/a for automatic mode): ").strip().lower()
                        if choice == 'a':
                            automatic_mode = True
                            print("Automatic mode enabled. Processing will continue until complete or interrupted.")
                            print("Using batch size of 20 for remaining batches.")
                            print("Press 'n' then Enter at any time to exit automatic mode.")
                            valid_response = True
                        elif choice == 'y':
                            valid_response = True
                        elif choice == 'n':
                            print("Stopping at user request.")
                            i = len(urls)  # This will exit the outer while loop
                            valid_response = True
                        else:
                            print("Invalid input. Please enter 'y', 'n', or 'a'.")

        # Save summaries to file
        save_summary_to_file(folder_path, batch_summaries, batch_overall_summaries)

    print_header("SUMMARIZATION COMPLETE")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user.")
        print("Saving any completed summaries...")
        # Note: The summaries for the completed batches are already saved by the main loop
        print("Summary files have been saved for completed batches.")
        sys.exit(1)
