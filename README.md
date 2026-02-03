# BloodHound Compatibility Matrix

An automated compatibility matrix showing which versions of SharpHound and AzureHound are bundled with each BloodHound Community Edition release.

## Overview

This project automatically tracks the compatibility between BloodHound Community Edition and its data collection tools (SharpHound and AzureHound) by:

1. Querying the Docker Hub API for BloodHound images
2. Extracting collector versions from Docker image build arguments
3. Generating a fresh compatibility matrix on each run
4. Publishing the results as a static GitHub Pages site
5. Updating daily via GitHub Actions (without committing the JSON to the repository)

## Live Site

View the compatibility matrix at: https://philomath213.github.io/bloodhound-ce-versions/

## How It Works

### Python Script ([update_matrix.py](update_matrix.py))

The Python script:
- Fetches all tags from the `specterops/bloodhound` Docker repository
- Filters to semantic version tags (e.g., `8.5.2`, `8.4.0`)
- Extracts `SHARPHOUND_VERSION` and `AZUREHOUND_VERSION` from Docker image layers
- Generates a JSON file with the compatibility matrix

**Features:**
- Automatic retry with exponential backoff for API failures
- Configurable minimum version filter
- Pagination support for large tag lists
- Error handling and logging

### Static Site ([index.html](index.html))

A lightweight, client-side HTML page that:
- Loads the JSON data
- Displays the matrix in a clean, responsive table
- Links to Docker Hub and GitHub releases
- Uses a dark theme matching GitHub's aesthetic

### GitHub Actions ([.github/workflows/update-matrix.yml](.github/workflows/update-matrix.yml))

The workflow:
- Runs daily at 00:00 UTC (configurable via cron)
- Can be triggered manually via workflow dispatch
- Generates fresh compatibility data on each run
- Deploys only `index.html` and `bloodhound_versions.json` to GitHub Pages
- Does not commit the JSON file to the repository (keeps git history clean)

## Local Development

### Prerequisites

- Python 3.11+
- pip

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/philomath213/bloodhound-ce-versions.git
   cd bloodhound-compatibility-matrix
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the script:
   ```bash
   python update_matrix.py
   ```

   Or with a custom minimum version:
   ```bash
   python update_matrix.py --min-version 8.4.0
   ```

4. Open `index.html` in a browser to view the results locally

## Configuration

### Script Options

```bash
python update_matrix.py --help
```

Options:
- `--min-version`, `-m`: Minimum BloodHound version to include (default: `8.0.0`)

### Workflow Schedule

To change the update frequency, edit the cron expression in [.github/workflows/update-matrix.yml](.github/workflows/update-matrix.yml#L5):

```yaml
schedule:
  - cron: '0 0 * * *'  # Daily at midnight UTC
```

Examples:
- `0 */12 * * *` - Every 12 hours
- `0 0 * * 0` - Weekly on Sunday
- `0 0 1 * *` - Monthly on the 1st

## Output Format

The generated `bloodhound_versions.json` has this structure:

```json
{
  "updated": "2026-02-03T12:00:00.000000+00:00",
  "versions": [
    {
      "bloodhound": "8.5.2",
      "sharphound": "v2.9.0",
      "azurehound": "v2.8.3"
    }
  ]
}
```

## GitHub Pages Setup

1. Go to repository Settings > Pages
2. Set Source to "GitHub Actions"
3. The workflow will automatically deploy after each update

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── update-matrix.yml    # GitHub Actions workflow
├── update_matrix.py             # Python script to fetch versions
├── index.html                   # Static site
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
└── README.md                    # This file

Note: `bloodhound_versions.json` is generated during workflow runs but not committed to the repository.
```

## Dependencies

- [requests](https://requests.readthedocs.io/) - HTTP library for API calls
- [packaging](https://packaging.pypa.io/) - Version parsing and comparison

## License

This project is provided as-is for community use.

## Contributing

Contributions welcome! Please open an issue or pull request.

## Related Projects

- [BloodHound](https://github.com/SpecterOps/BloodHound) - Six Degrees of Domain Admin
- [SharpHound](https://github.com/SpecterOps/SharpHound) - C# Data Collector for BloodHound
- [AzureHound](https://github.com/SpecterOps/AzureHound) - Azure Data Exporter for BloodHound
