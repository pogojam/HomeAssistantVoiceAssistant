# OpenAI Realtime Assistant

{% if installed %}
## Changes in this version

- Initial release
- Real-time voice conversations with GPT-4o
- Home Assistant entity control via function calling
- Multiple voice options
- Automatic reconnection and error handling

{% endif %}

## Features

This integration replaces Home Assistant's default voice assistant with OpenAI's real-time API, providing:

- **Natural Conversations**: Talk to your home like you would to a person
- **Context Awareness**: The assistant remembers previous interactions
- **Smart Home Control**: Control devices through natural language
- **Low Latency**: Sub-second response times for fluid conversations
- **Interruption Support**: Interrupt the assistant mid-response

## Requirements

- OpenAI API key with Realtime API access
- Home Assistant 2024.1.0 or newer
- Voice satellite device

## Quick Start

1. Add your OpenAI API key to `configuration.yaml`
2. Restart Home Assistant
3. Configure your voice satellite to use this assistant
4. Start talking!

See the [full documentation](https://github.com/yourusername/openai-realtime-assistant) for detailed setup instructions.