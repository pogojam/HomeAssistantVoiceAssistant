# OpenAI Realtime Assistant for Home Assistant

A custom Home Assistant integration that replaces the default voice assistant pipeline with OpenAI's real-time API, enabling GPT-4o-powered voice conversations through Home Assistant voice satellites.

## Features

- **Real-time Voice Interaction**: Bidirectional audio streaming with OpenAI's GPT-4o
- **Natural Conversation**: Maintains context across interactions
- **Home Control**: Control lights, switches, scenes, and climate through natural language
- **Multiple Voice Options**: Choose from alloy, echo, fable, onyx, nova, or shimmer voices
- **Interrupt Handling**: Users can interrupt the assistant mid-response
- **Auto-reconnection**: Robust WebSocket connection with automatic reconnection

## Installation

### HACS Installation (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the "+" button
4. Search for "OpenAI Realtime Assistant"
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/openai_realtime_assistant` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

Add the following to your `configuration.yaml`:

```yaml
openai_realtime_assistant:
  api_key: "sk-..."  # Your OpenAI API key
  model: "gpt-4o-realtime-preview"  # Optional, default: gpt-4o-realtime-preview
  voice: "alloy"  # Optional, options: alloy, echo, fable, onyx, nova, shimmer
  temperature: 0.7  # Optional, default: 0.7
  system_prompt: "You are a helpful home assistant..."  # Optional
  enable_home_control: true  # Optional, default: true
  conversation_timeout: 30  # Optional, default: 30 seconds
```

## Usage

### Voice Satellite Configuration

Configure your voice satellite to use the OpenAI Realtime Assistant:

1. Go to Settings → Voice assistants
2. Select your voice satellite device
3. Choose "OpenAI Realtime Assistant" as the assistant
4. Configure wake word detection as usual

### Available Services

The integration exposes the following services:

- `openai_realtime_assistant.start_conversation`: Start a new conversation session
- `openai_realtime_assistant.stop_conversation`: Stop the current session
- `openai_realtime_assistant.clear_context`: Clear conversation history
- `openai_realtime_assistant.set_system_prompt`: Update the system prompt

### Supported Commands

When `enable_home_control` is true, you can use natural language to:

- Turn devices on/off: "Turn on the living room lights"
- Adjust brightness: "Dim the bedroom lights to 50%"
- Change colors: "Make the kitchen lights blue"
- Activate scenes: "Activate movie time"
- Control climate: "Set the thermostat to 72 degrees"
- Query states: "Is the garage door open?"

## Requirements

- Home Assistant 2024.1.0 or newer
- OpenAI API key with access to the Realtime API
- Voice satellite device (ESPHome, Atom Echo, etc.)

## Troubleshooting

### Connection Issues

If the integration fails to connect:

1. Verify your API key is correct
2. Check Home Assistant logs for detailed error messages
3. Ensure your OpenAI account has access to the Realtime API

### Audio Issues

- Ensure your voice satellite is configured for 16kHz, 16-bit PCM mono audio
- Check that the satellite's microphone and speaker are working properly
- Verify network bandwidth is sufficient for real-time audio streaming

### Response Delays

- The integration targets <500ms round-trip latency
- High network latency or API load can increase response times
- Consider adjusting the `conversation_timeout` if needed

## Development

### File Structure

```
custom_components/openai_realtime_assistant/
├── __init__.py          # Integration setup
├── const.py             # Constants and configuration
├── manifest.json        # Integration metadata
├── services.yaml        # Service definitions
├── websocket_client.py  # OpenAI WebSocket client
├── stt.py              # Speech-to-text platform
├── tts.py              # Text-to-speech platform
├── conversation.py      # Conversation agent
└── home_assistant_tools.py  # Function calling tools
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Credits

Built with ❤️ for the Home Assistant community.

Uses OpenAI's Realtime API for natural voice interactions.