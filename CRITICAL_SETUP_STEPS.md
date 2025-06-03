# CRITICAL: How to Make OpenAI Realtime Assistant Appear in Voice Assistants

## The integration must be added via UI, not just YAML!

### Step 1: Remove YAML Configuration (Temporarily)
Comment out or remove from configuration.yaml:
```yaml
# openai_realtime_assistant:
#   api_key: "sk-..."
```

### Step 2: Restart Home Assistant
```bash
ha core restart
```

### Step 3: Add Integration via UI
1. Go to **Settings → Devices & Services**
2. Click **"+ ADD INTEGRATION"** button (bottom right)
3. Search for **"OpenAI"** or **"Realtime"**
4. Select **"OpenAI Realtime Assistant"**
5. Enter your API key when prompted
6. Click Submit

### Step 4: Create Voice Assistant Pipeline
1. Go to **Settings → Voice assistants**
2. Click **"+ ADD ASSISTANT"**
3. Give it a name (e.g., "OpenAI Assistant")
4. Configure:
   - **Language**: Choose your language
   - **Conversation agent**: Select "OpenAI Realtime Assistant"
   - **Speech-to-text**: Select "OpenAI Realtime Assistant"
   - **Text-to-speech**: Select "OpenAI Realtime Assistant"
   - **Wake word**: Configure if desired

### Step 5: Assign to Voice Satellite
1. Go to your voice satellite device
2. Select the new "OpenAI Assistant" pipeline

## Why YAML-only doesn't work for Voice Assistants:

Home Assistant's Voice Assistant system requires:
1. A properly registered integration (via UI)
2. All three components (STT, TTS, Conversation) available
3. A configured pipeline

YAML configuration alone doesn't register the integration properly for voice assistant selection.

## If "OpenAI Realtime Assistant" doesn't appear in Add Integration:

1. **Check HACS status** - make sure it's downloaded (not just added)
2. **Clear browser cache** - Ctrl+F5 or Cmd+Shift+R
3. **Check custom_components folder**:
   ```bash
   ls -la /config/custom_components/openai_realtime_assistant/
   ```
4. **Restart again and check logs**:
   ```bash
   ha core restart
   grep -i "setup.*openai" /config/home-assistant.log
   ```

## Alternative if UI setup fails:

Try forcing discovery:
```yaml
# In configuration.yaml
default_config:
discovery:
```

Then restart and check Settings → Devices & Services → Discovered