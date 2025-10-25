### Usage

```python
from pipecat.audio.vad.vad_analyzer import VADParams
from connexity.metrics.pipecat_twilio import ConnexityTwilioObserver
from twilio.rest import Client

# build your VADParams once
vad_params = VADParams(
    confidence=0.5,
    min_volume=0.6,
    start_secs=0.2,
    stop_secs=0.8,
)

# assume you’ve already created/started your TwilioClient somewhere:
#    twilio_client = Client(account_sid, auth_token)
#    twilio_client.calls(call_sid).recordings.create()
# and you want to inject that manager into the observer

observer = ConnexityTwilioObserver()
await observer.initialize(
    agent_id="YOUR_AGENT_ID",
    api_key="YOUR_CONNEXITY_API_KEY",
    sid=call_sid,
    phone_call_provider="twilio",    # OPTIONAL FIELD
    user_phone_number=from_number,   # OPTIONAL FIELD
    agent_phone_number=to_number,    # OPTIONAL FIELD

    # <<< now using DI of client instead of creds >>>
    twilio_client=twilio_client.client,  # OPTIONAL FIELD
    daily_api_key="DAILY_API_KEY",       # OPTIONAL FIELD

    voice_provider="11labs",
    llm_provider="openai",
    llm_model="gpt-4o",
    stt_model="deepgram-nova-2",      # STT model (dynamic, may change with provider updates)
    tts_model="eleven_turbo_v2",      # TTS model (dynamic, may change with provider updates)
    tts_voice="your-voice-id",        # TTS voice ID (dynamic, may change with provider updates)
    call_type="inbound",
    transcriber="deepgram",
    vad_params=vad_params,
    env="development",          # or "production"
    vad_analyzer="silero",      # your chosen VAD engine name
)

pipeline.register_observer(observer)
```

# CHANGELOG

v0.0.8.13 — 2025-10-24

### New Features

- **snapshot_error_frame.py**  
  add wrapper to capture error frames in Pipecat

# CHANGELOG

v0.0.8.12 — 2025-09-04

### CRITICAL FIX

- **get_daily_recording_url**  
  fixed issue with types

# CHANGELOG

v0.0.8.11 — 2025-09-02

### New Features

- **ConnexityDailyObserver support**  
  Added support for `ConnexityDailyObserver`, including retrieving Daily recording and call duration.  
  **Note:** You must pass `daily_api_key` to enable this feature.

### Breaking Changes

- **Observer logic refactor**

  - Introduced `pipecat_interface` with standardized `initialize(...)` and `on_push_frame(...)` methods for all current and future observer classes.
  - Created `ConnexityDailyObserver` and `ConnexityTwilioObserver`. These should now be used instead of previous observer implementations.

  - **STT and TTS Model Parameters**: Added support for configurable STT and TTS models and voices
  - `stt_model`: Specify the speech-to-text model to use (dynamic values from providers)
  - `tts_model`: Specify the text-to-speech model to use (dynamic values from providers)
  - `tts_voice`: Specify the voice ID for text-to-speech (dynamic values from providers)

- **ConnexityTwilioObserver Updates**: Updated to handle new STT/TTS parameters in initialization

v0.0.8.9 — 2025-06-24

### Minor Fixes

- **Get recording from region specific twilio account**

v0.0.8.8 — 2025-06-24

### Breaking Changes

- **Twilio DI instead of credentials**

Removed twilio_account_sid and twilio_auth_token parameters from initialize(...).

Now you must pass a twilio_client: TwilioClient instance via the twilio_client argument.
Action required: construct and start your own TwilioClient, then inject it into the observer.

v0.0.8.7 — 2025-06-20

### Breaking Changes

- **Removed built-in Twilio call recording**  
  Recording is no longer performed by this package.  
  **Action required:** start your Twilio recording on the app side as soon as the WebSocket connection is established.

v0.0.8.6 — 2025-06-13

## New Features

### VAD compensation

- Configurable via VADParams
- Pass vad_params into initialize(...)
- Environment & analyzer tags
- Added env and vad_analyzer metadata fields to register_call
