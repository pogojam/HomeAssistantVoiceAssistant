# OpenAI Realtime Assistant for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A custom Home Assistant integration that replaces the default voice assistant pipeline with OpenAI's real-time API, enabling GPT-4o-powered voice conversations through Home Assistant voice satellites.

## Installation

### HACS Installation (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL: `https://github.com/pogojam/HomeAssistantVoiceAssistant`
5. Select "Integration" as the category
6. Click "Add"
7. Find "OpenAI Realtime Assistant" in the integration list
8. Click "Download"
9. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/openai_realtime_assistant` folder
2. Copy it to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

Add to your `configuration.yaml`:

```yaml
openai_realtime_assistant:
  api_key: "sk-..."  # Your OpenAI API key
```

See [configuration.yaml.example](configuration.yaml.example) for all available options.

## Features

- 🎙️ Real-time voice conversations with GPT-4o
- 🏠 Natural language home control
- 🔊 Multiple voice options
- ⚡ Sub-second response times
- 🔄 Automatic reconnection
- 🛡️ Robust error handling

## Documentation

See the [component README](custom_components/openai_realtime_assistant/README.md) for detailed documentation.

## License

MIT License