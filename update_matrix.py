#!/usr/bin/env python3
"""Extract SharpHound and AzureHound versions from BloodHound Docker images."""

import requests
import re
import json
import argparse
import time
from datetime import datetime, timezone
from packaging import version


def get_all_tags(repository: str, page_size: int = 100, max_retries: int = 3) -> list:
    """Get all available tags for a repository with pagination."""
    tags = []
    url = f"https://hub.docker.com/v2/repositories/{repository}/tags"
    params = {"page_size": page_size}

    while url:
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                tags.extend(t["name"] for t in data["results"])
                url = data.get("next")
                params = {}  # params already in next URL
                break
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                print(f"Error fetching tags (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

    return tags


def is_valid_semver(tag: str) -> bool:
    """Check if tag looks like a semantic version."""
    return bool(re.match(r"^\d+\.\d+\.\d+$", tag))


def get_collector_versions(repository: str, tag: str, max_retries: int = 3) -> dict:
    """Extract SHARPHOUND_VERSION and AZUREHOUND_VERSION from image layers."""
    url = f"https://hub.docker.com/v2/repositories/{repository}/tags/{tag}/images"

    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            for image in response.json():
                if image.get("architecture") == "amd64" and image.get("os") == "linux":
                    versions = {}
                    for layer in image.get("layers", []):
                        instruction = layer.get("instruction", "")
                        if match := re.match(r"ARG (SHARPHOUND_VERSION|AZUREHOUND_VERSION)=(.+)", instruction):
                            versions[match.group(1)] = match.group(2)
                    if versions:
                        return versions
            return None
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                print(f"Failed to get versions for {tag} after {max_retries} attempts: {e}")
                return None
            wait_time = 2 ** attempt
            time.sleep(wait_time)


def main():
    parser = argparse.ArgumentParser(description="Get BloodHound collector version matrix")
    parser.add_argument("--min-version", "-m", default="8.0.0", help="Minimum BloodHound tag version (e.g., 8.4.0)")
    args = parser.parse_args()

    min_ver = version.parse(args.min_version)
    repository = "specterops/bloodhound"
    
    print(f"Fetching tags for {repository}...")
    tags = get_all_tags(repository)
    print(f"Found {len(tags)} total tags")
    
    # Filter to valid semver tags >= min_version
    valid_tags = [t for t in tags if is_valid_semver(t) and version.parse(t) >= min_ver]
    valid_tags.sort(key=version.parse, reverse=True)
    
    print(f"Processing {len(valid_tags)} tags >= {args.min_version}...\n")
    
    matrix = []
    for tag in valid_tags:
        versions = get_collector_versions(repository, tag)
        if versions:
            matrix.append({
                "bloodhound": tag,
                "sharphound": versions.get("SHARPHOUND_VERSION", "N/A"),
                "azurehound": versions.get("AZUREHOUND_VERSION", "N/A")
            })
            print(f"{tag}: SharpHound={versions.get('SHARPHOUND_VERSION', 'N/A')}, AzureHound={versions.get('AZUREHOUND_VERSION', 'N/A')}")

    output = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "versions": matrix
    }

    try:
        with open("bloodhound_versions.json", "w") as f:
            json.dump(output, f, indent=2)
        print(f"\nFound {len(matrix)} versions. Matrix saved to bloodhound_versions.json")
    except IOError as e:
        print(f"Error writing output file: {e}")
        raise


if __name__ == "__main__":
    main()
