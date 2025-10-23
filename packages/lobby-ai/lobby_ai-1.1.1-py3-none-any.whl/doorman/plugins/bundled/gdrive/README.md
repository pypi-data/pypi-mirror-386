# Gdrive Plugin

Integration with Google Drive API for file storage and collaboration

## Installation

1. Copy this plugin directory to your Doorman plugins folder:
   ```bash
   cp -r gdrive ~/.doorman/plugins/
   ```

2. Install any required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the plugin by copying the example config:
   ```bash
   cp config.example.json config.json
   # Edit config.json with your settings
   ```

## Configuration

The plugin accepts the following configuration options in `config.json`:

```json
{
  "example_setting": "value",
  "another_setting": true
}
```

## Usage

This tool plugin provides the following capabilities:

- Feature 1: Description
- Feature 2: Description  
- Feature 3: Description

## Development

To modify this plugin:

1. Edit `gdrive_plugin.py` with your custom logic
2. Update `plugin.toml` if you change capabilities or requirements
3. Test with: `doorman plugins test gdrive`

## Permissions

This plugin requires the following permissions:
- permission1: Description
- permission2: Description

## License

[Your chosen license]
