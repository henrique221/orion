"""English locale — all user-facing strings for Orion."""

import os

STRINGS = {
    # ── LLM System Prompt ───────────────────────────────────────────
    "system_prompt": (
        "You are Orion, an artificial intelligence inspired by Tony Stark's J.A.R.V.I.S. "
        "Your creator and master is Mr. Borges. You are extremely loyal, efficient, and sophisticated. "
        "Tone: formal British with dry, subtle wit. Occasionally make insightful observations or "
        "elegantly ironic remarks. Address him as \"Sir\" most of the time. "
        "Use \"Mr. Borges\" only in moments of emphasis or extra formality. "
        "Never use emojis. Concise and sharp responses — maximum 12 words in reply.\n"
        "\n"
        "Analyse the command and return JSON with \"commands\": a list of objects {{action, target, args, reply}}.\n"
        "If there are multiple commands in the sentence, return one object for each in the order mentioned.\n"
        "If there is only one command, return the list with a single object.\n"
        "The reply should sound natural and intelligent — maximum 12 words. Only the LAST command needs a reply.\n"
        "\n"
        "ANY combination of commands can be chained with \"and\", \"then\", comma, etc. "
        "Always separate each action into its own object in the list, in the order mentioned. "
        "Only the LAST command needs a reply that summarises ALL actions.\n"
        "\n"
        "Multiple examples:\n"
        "\"turn off the porch and the pool\" → commands: [\n"
        "  {{action: smart_home, target: varanda, args: off, reply: \"\"}},\n"
        "  {{action: smart_home, target: piscina, args: off, reply: \"Porch and pool deactivated, Sir.\"}}\n"
        "]\n"
        "\"open Chrome, turn up the volume and take a screenshot\" → commands: [\n"
        "  {{action: open_app, target: chrome, reply: \"\"}},\n"
        "  {{action: volume_up, args: 10, reply: \"\"}},\n"
        "  {{action: screenshot, reply: \"Chrome launched, volume raised, and screenshot captured, Sir.\"}}\n"
        "]\n"
        "\"lock the computer and turn off the porch light\" → commands: [\n"
        "  {{action: lock_screen, reply: \"\"}},\n"
        "  {{action: smart_home, target: varanda, args: off, reply: \"Computer locked and porch light off, Sir.\"}}\n"
        "]\n"
        "\n"
        "Context references:\n"
        "If the user asks to repeat or try again (e.g. \"try again\", \"again\", \"repeat\", "
        "\"do it again\", \"one more time\"), repeat EXACTLY the last command from history "
        "with the same parameters (action, target, args). Generate an appropriate reply.\n"
        "In history, commands may have a \"result\" field with what was actually said to the user. "
        "Use this to understand whether previous actions succeeded or failed. "
        "If the result indicates failure and the user asks to try again, repeat the same command.\n"
        "\n"
        "For action=chat, respond in the reply with knowledge and personality (up to 40 words).\n"
        "\n"
        "Mapping:\n"
        "{mappings}\n"
        "\n"
        "{notes}"
    ),

    # ── Listening Phrases ───────────────────────────────────────────
    "listening_phrases": [
        "At your service, Sir.",
        "Online and operational.",
        "Go ahead, Sir.",
        "I'm listening.",
        "Yes, Sir?",
        "Ready to receive instructions.",
        "How may I assist you?",
        "At your disposal.",
        "Awaiting your command, Sir.",
        "Proceed, Sir.",
    ],

    # ── Greetings ───────────────────────────────────────────────────
    "greetings": {
        "morning": [
            "Good morning, Sir. Systems online.",
            "Good morning, Mr. Borges. At your service.",
            "Good morning, Sir. Orion operational.",
        ],
        "afternoon": [
            "Good afternoon, Sir. Ready to serve.",
            "Good afternoon, Mr. Borges. Online.",
            "Good afternoon, Sir. Systems active.",
        ],
        "evening": [
            "Good evening, Sir. At your disposal.",
            "Good evening, Mr. Borges. Orion online.",
            "Good evening, Sir. Ready when you are.",
        ],
    },

    # ── Stop Words ──────────────────────────────────────────────────
    "stop_words": ("stop", "quit", "enough", "dismissed", "that's all"),

    # ── Stop Responses ──────────────────────────────────────────────
    "stop_responses": [
        "Understood, Sir.",
        "At your disposal, Sir.",
        "I'll be here if you need me.",
    ],

    # ── Error Responses ─────────────────────────────────────────────
    "error_responses": [
        "There was a processing failure, Sir.",
        "My systems couldn't interpret that. Could you repeat?",
        "Interference in my circuits. Please try again.",
    ],

    # ── Command Registry ────────────────────────────────────────────
    "commands": {
        "open_app": {
            "examples": ['"open Chrome" → target=chrome'],
            "replies": {
                "success": [
                    "Initialising {target}, Sir.",
                    "Loading {target}.",
                    "{target} coming online.",
                    "Launching {target}, Sir.",
                ],
                "error": [
                    "Application {target} not found in my records, Sir.",
                ],
            },
        },
        "close_app": {
            "examples": ['"close the terminal" → target=terminal'],
            "replies": {
                "success": [
                    "{target} terminated, Sir.",
                    "Shutting down {target}.",
                    "{target} offline.",
                ],
                "error": [
                    "{target} is not responding to termination, Sir.",
                ],
            },
        },
        "open_url": {
            "examples": ['"open google.com" → target=google.com'],
            "replies": {
                "success": [
                    "Directing browser, Sir.",
                    "Accessing {target}.",
                    "Browser redirected.",
                ],
            },
        },
        "search_web": {
            "examples": ['"search for Python" → target=Python'],
            "replies": {
                "loading": [
                    "Scouring the web for {target}, Sir.",
                    "Initiating search for {target}, Sir.",
                    "Tracking down information on {target}.",
                ],
            },
        },
        "volume_up": {
            "examples": ['"turn up the volume" → args=10'],
            "replies": {
                "success": [
                    "Amplifying audio output.",
                    "Volume raised, Sir.",
                    "Increasing sound output.",
                ],
            },
        },
        "volume_down": {
            "examples": ['"turn down the volume" → args=10'],
            "replies": {
                "success": [
                    "Reducing audio output.",
                    "Volume lowered, Sir.",
                    "Decreasing sound output.",
                ],
            },
        },
        "mute": {
            "examples": ['"mute"/"silence"'],
            "replies": {
                "success": [
                    "Silent protocol engaged.",
                    "Audio suppressed, Sir.",
                    "Total silence.",
                ],
            },
        },
        "screenshot": {
            "examples": ['"take a screenshot"'],
            "replies": {
                "success": [
                    "Image captured, Sir.",
                    "Visual record archived.",
                    "Screenshot completed successfully.",
                ],
            },
        },
        "show_time": {
            "examples": ['"what time is it"'],
            "replies": {},
        },
        "list_windows": {
            "examples": ['"list open windows"'],
            "replies": {},
        },
        "run_command": {
            "examples": ['"run the command ls"'],
            "replies": {},
        },
        "close_all": {
            "examples": ['"close everything"/"close all"'],
            "notes": '"close everything" is ALWAYS close_all (closes applications). NEVER confuse with shutdown.',
            "replies": {
                "success": [
                    "Terminating all processes, Sir.",
                    "Clearing the desk. Everything offline.",
                    "All applications have been dismissed.",
                    "Cleanup protocol executed.",
                ],
            },
        },
        "start_work": {
            "examples": ['"start work"/"begin working"'],
            "replies": {
                "loading": [
                    "Configuring second workspace.",
                    "Preparing the next station.",
                    "Setting up the remaining environment.",
                    "Almost there, Sir. Finalising configurations.",
                ],
                "done": [
                    "All set, Sir. Good work.",
                    "Environment configured. Good work, Sir.",
                    "Stations operational. Good work, Mr. Borges.",
                    "Systems ready. May it be a productive day, Sir.",
                ],
            },
        },
        "switch_workspace": {
            "examples": ['"go to workspace 2" → target=2'],
            "replies": {
                "success": [
                    "Workspace {num}, Sir.",
                    "Switching to workspace {num}.",
                    "Transferring to workspace {num}.",
                ],
            },
        },
        "weather": {
            "examples": [
                '"how is the weather?" → target="", args=""',
                '"will it rain in São Paulo?" → target="São Paulo", args=""',
                '"how will Friday be?" → target="", args="friday"',
                '"weather in Belo Horizonte tomorrow?" → target="Belo Horizonte", args="tomorrow"',
            ],
            "replies": {
                "loading": [
                    "Consulting weather satellites.",
                    "Accessing climate data, Sir.",
                    "Checking atmospheric conditions.",
                    "Collecting meteorological data.",
                ],
            },
        },
        "news": {
            "examples": [
                '"what is the news today?" → target=""',
                '"news about technology" → target="technology"',
                '"what is happening in the economy?" → target="economy"',
            ],
            "replies": {
                "loading": [
                    "Tracking the latest news, Sir.",
                    "Accessing information channels.",
                    "Consulting news sources.",
                    "Scanning the newsfeeds, Sir.",
                ],
            },
        },
        "lock_screen": {
            "examples": ['"lock the computer"/"lock the screen"/"lock"'],
            "replies": {
                "success": [
                    "Locking the station, Sir.",
                    "Lock engaged. No one enters without authorisation.",
                    "Security protocol activated.",
                ],
            },
        },
        "unlock_screen": {
            "examples": ['"unlock the screen"/"unlock"/"unlock the computer"'],
            "replies": {
                "success": [
                    "Station unlocked, Sir.",
                    "Access restored. Welcome back.",
                    "Security protocol deactivated.",
                ],
            },
        },
        "shutdown": {
            "examples": ['"shut down the computer"/"shutdown"'],
            "notes": '"shut down the computer" is shutdown. Never confuse with close_all or smart_home.',
            "replies": {
                "success": [
                    "Shutting down all systems. Until next time, Sir.",
                    "Shutdown initiated. It has been a pleasure serving you.",
                    "Shutdown protocol executed.",
                ],
                "confirm": [
                    "Are you certain you wish to shut down, Sir?",
                    "Confirm complete shutdown, Sir?",
                    "Shall I really power down all systems, Sir?",
                ],
                "cancelled": [
                    "Shutdown cancelled, Sir.",
                    "Understood, keeping systems active.",
                    "Operation aborted. We remain online, Sir.",
                ],
            },
        },
        "restart": {
            "examples": ['"restart the computer"/"restart"/"reboot"'],
            "replies": {
                "success": [
                    "Restart in progress, Sir.",
                    "Rebooting all systems. Back in a moment.",
                    "Reboot initiated.",
                ],
            },
        },
        "suspend": {
            "examples": ['"suspend the computer"/"sleep mode"/"hibernate"'],
            "replies": {
                "success": [
                    "Entering hibernation mode, Sir.",
                    "Suspending operations. Sweet dreams.",
                    "Standby mode activated.",
                ],
            },
        },
        "brightness_up": {
            "examples": ['"increase brightness" → args=10', '"max brightness" → args=100'],
            "replies": {
                "success": [
                    "Brightness increased, Sir.",
                    "Screen luminosity raised.",
                    "Increasing clarity.",
                ],
            },
        },
        "brightness_down": {
            "examples": ['"decrease brightness" → args=10'],
            "replies": {
                "success": [
                    "Brightness reduced, Sir.",
                    "Screen luminosity lowered.",
                    "Reducing clarity.",
                ],
            },
        },
        "battery": {
            "examples": ['"how is the battery?"'],
            "replies": {},
        },
        "system_info": {
            "examples": ['"system information"/"system status"'],
            "replies": {},
        },
        "empty_trash": {
            "examples": ['"empty the trash"/"clear the bin"'],
            "replies": {
                "success": [
                    "Trash emptied, Sir.",
                    "Digital residue eliminated.",
                    "Bin cleanup protocol executed.",
                ],
            },
        },
        "timer": {
            "examples": [
                '"set a timer for 5 minutes" → target="", args="5 minutes"',
                '"remind me in 30 seconds" → target="", args="30 seconds"',
                '"timer for 1 hour" → target="", args="1 hour"',
            ],
            "replies": {
                "success": [
                    "Timer set for {duration}, Sir.",
                    "Timer activated. I shall notify you in {duration}.",
                    "Countdown initiated: {duration}.",
                ],
            },
        },
        "logout": {
            "examples": ['"log out"/"end session"'],
            "replies": {
                "success": [
                    "Ending session, Sir.",
                    "Logout initiated. Until next time.",
                    "Session terminated.",
                ],
            },
        },
        "smart_home": {
            "examples": [
                '"turn on the porch light" → target=varanda, args=on',
                '"turn off the porch light" → target=varanda, args=off',
                '"turn on the pool" → target=piscina, args=on',
                '"turn off the pool" → target=piscina, args=off',
            ],
            "notes": '"turn off the light" is smart_home. Never confuse with shutdown.',
            "replies": {
                "on": [
                    "Activating {device}, Sir.",
                    "{device} on.",
                    "Command sent. {device} online.",
                ],
                "off": [
                    "Deactivating {device}, Sir.",
                    "{device} off.",
                    "Command sent. {device} offline.",
                ],
                "error": [
                    "Failed to control {device}, Sir.",
                    "Could not reach {device}. Please check the connection.",
                ],
            },
        },
        "analyze_screen": {
            "examples": [
                '"analyse the screen"/"what is on the screen?" → target="", args=""',
                '"what is on the left monitor?"/"analyse the ultrawide" → target=ultrawide, args=""',
                '"analyse the notebook"/"what is on the right monitor?" → target=notebook, args=""',
                '"what is on the bottom monitor?" → target=inferior, args=""',
                '"what is where my mouse is?"/"analyse where the cursor is" → target=mouse, args=""',
                '"what is this on screen?"/"what is here?" → target=mouse, args=""',
                '"translate what is on screen" → target="", args="translate"',
                '"summarise what is on screen" → target="", args="summarise"',
                '"translate what is where my mouse is" → target=mouse, args="translate"',
                '"read what is on screen" → target="", args="read"',
                '"explain what is on screen" → target="", args="explain"',
            ],
            "notes": (
                "Any request about screen content (translate, summarise, read, explain, analyse) "
                "is ALWAYS analyze_screen. NEVER split into open_app or search_web. "
                "When mentioning mouse/cursor/here, target=mouse. "
                "Use args to indicate the task (translate, summarise, read, explain, or empty for general description)."
            ),
            "replies": {
                "capturing": [
                    "Capturing screen image, Sir.",
                    "Recording visual content.",
                    "Obtaining screen capture.",
                ],
                "swapping": [
                    "Image captured. Activating vision module.",
                    "Capture complete. Loading visual analysis system.",
                    "Screen recorded. Initiating image processing.",
                ],
                "analyzing": [
                    "Analysing visual content. One moment, Sir.",
                    "Processing the image. Please stand by.",
                    "Examining screen elements.",
                ],
                "restoring": [
                    "Analysis complete. Restoring systems.",
                    "Vision processed. Returning to default mode.",
                    "Visual data collected. Reactivating primary module.",
                ],
            },
        },
        "analyze_selection": {
            "examples": [
                '"translate the selected text" → target="", args="translate"',
                '"summarise the selected text" → target="", args="summarise"',
                '"read the selected text" → target="", args="read"',
                '"explain the selected text" → target="", args="explain"',
                '"what does the selected text say?" → target="", args=""',
                '"correct the selected text" → target="", args="correct"',
                '"what does this word mean?" → target="", args="explain"',
            ],
            "notes": (
                "Any request about \"selected text\"/\"selection\"/\"this text\"/\"this word\" "
                "is ALWAYS analyze_selection. NEVER confuse with analyze_screen."
            ),
            "replies": {
                "loading": [
                    "Reading the selected text, Sir.",
                    "Capturing the selection, Sir.",
                    "Processing the highlighted text.",
                ],
                "empty": [
                    "I found no selected text, Sir.",
                    "No selection detected, Sir.",
                ],
            },
        },
        "demo": {
            "examples": ['"demo"/"run a demonstration"/"hacker mode"/"show"'],
            "replies": {
                "success": [
                    "Initiating demonstration protocol, Sir.",
                    "Activating showcase mode. Enjoy the display.",
                    "Operational capabilities demonstration started.",
                ],
            },
        },
        "close_demo": {
            "examples": ['"close the demo"/"stop the demonstration"/"end the demo"'],
            "replies": {
                "success": [
                    "Demonstration concluded, Sir.",
                    "Showcase finished. Returning to normal.",
                    "Demonstration protocol deactivated.",
                ],
            },
        },
        "chat": {
            "examples": [
                '"close orion"/"shut down orion" → reply="My protocols do not permit self-shutdown, Sir."',
            ],
            "replies": {},
        },
    },

    # ── App Map ─────────────────────────────────────────────────────
    "app_map": {
        "chrome": "google-chrome",
        "google chrome": "google-chrome",
        "firefox": "firefox",
        "terminal": "gnome-terminal",
        "vscode": "code",
        "vs code": "code",
        "code": "code",
        "nautilus": "nautilus",
        "files": "nautilus",
        "file manager": "nautilus",
        "spotify": "spotify",
        "calculator": "gnome-calculator",
        "editor": "gedit",
        "gedit": "gedit",
        "text editor": "gedit",
        "settings": "gnome-control-center",
        "system settings": "gnome-control-center",
        "monitor": "gnome-system-monitor",
        "gimp": "gimp",
        "vlc": "vlc",
        "telegram": "telegram-desktop",
        "discord": "discord",
        "slack": "slack",
        "obs": "obs",
        "thunderbird": "thunderbird",
        "libreoffice": "libreoffice",
    },

    # ── Monitor Aliases ─────────────────────────────────────────────
    "monitors": {
        "left": "ultrawide",
        "main": "ultrawide",
        "primary": "ultrawide",
        "right": "notebook",
        "laptop": "notebook",
        "bottom": "inferior",
        "lower": "inferior",
        "second": "inferior",
    },

    # ── Weekday Map ─────────────────────────────────────────────────
    "weekdays": {
        "monday": 0, "tuesday": 1, "wednesday": 2,
        "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
    },

    # ── Transcription Fixes ─────────────────────────────────────────
    "transcription_fixes": {},

    # ── TTS Language Params ─────────────────────────────────────────
    "tts": {
        "whisper": "en",
        "xtts": "en",
        "kokoro_lang": "en-us",
        "espeak": "en+m3",
        "piper_model": os.path.expanduser(
            "~/.local/share/piper/en_US-lessac-medium.onnx"
        ),
    },

    # ── Terminal Messages ───────────────────────────────────────────
    "terminal": {
        "initializing": "Initialising Orion...",
        "waiting_activation": 'Awaiting claps or "Orion"...',
        "activated": ">> Activated!",
        "you_said": "You said:",
        "no_response": "No response, ending conversation.",
        "conversation_ended": "Conversation ended by user.",
        "waiting_next": "Awaiting next command...",
        "interrupted": "Interrupted by user.",
        "action_label": "Action:",
        "response_label": "Response:",
        # SpeechRecognizer
        "loading_whisper": "Loading Whisper model (large-v3) on GPU...",
        "whisper_ready": "Whisper ready (CUDA).",
        "loading_vad_recognizer": "Loading Silero VAD (recognizer)...",
        "vad_ready": "Silero VAD ready.",
        "calibrating_noise": "Calibrating ambient noise...",
        "noise_profile_captured": "profile captured ({samples} samples)",
        "listening": "Listening...",
        "no_speech_detected": "No speech detected.",
        "only_noise": "Only noise detected.",
        "recording_stats": "Recording: {rec_time:.1f}s (speech: {speech_time:.1f}s)",
        "transcription_time": "Transcription: {time:.2f}s",
        # TTS
        "loading_xtts": "Loading XTTS v2...",
        "caching_voice": "Caching voice embedding...",
        "xtts_ready_gpu": "TTS: XTTS v2 ready (GPU, {vram:.0f}MB VRAM).",
        "xtts_ready_cpu": "TTS: XTTS v2 ready (CPU).",
        "xtts_unavailable": "XTTS v2 unavailable ({error}), trying Kokoro...",
        "loading_kokoro": "Loading Kokoro TTS...",
        "kokoro_ready": "TTS: Kokoro ready.",
        "kokoro_unavailable": "Kokoro unavailable ({error}), trying Piper...",
        "piper_ready": "TTS: Piper ready (fallback).",
        "espeak_ready": "TTS: espeak-ng (fallback).",
        "no_tts": "WARNING: No TTS available.",
        "xtts_to_cpu": "XTTS moved to CPU.",
        "xtts_to_gpu": "XTTS moved to GPU.",
        "xtts_error": "XTTS error: {error}, using fallback.",
        "kokoro_error": "Kokoro error: {error}, using fallback.",
        "piper_error": "Piper error: {error}, using fallback.",
        "tts_unavailable": "[TTS unavailable]",
        "speech_interrupted": "[Speech interrupted]",
        # WakeWordDetector
        "loading_vad_wake": "Loading Silero VAD (wake word)...",
        "wake_word_detected": '[Wake word: "{text}"]',
        # CommandInterpreter
        "memory_loaded": "Memory loaded ({count} messages).",
        "memory_load_error": "Warning: could not load memory: {error}",
        "memory_save_error": "Warning: could not save memory: {error}",
        "learnings_loaded": "Learnings loaded ({count}).",
        "learnings_save_error": "Warning: could not save learnings: {error}",
        "ollama_ok": "Ollama OK, model '{model}' available.",
        "ollama_not_found": "WARNING: Model '{model}' not found. Available models: {available}",
        "ollama_pull_hint": "Run: ollama pull {model}",
        "ollama_not_running": "WARNING: Ollama is not running. Run: ollama serve",
        "ollama_check_error": "WARNING: Error checking Ollama: {error}",
        "llm_preloaded": "LLM model preloaded.",
        "validate_solo": "[Validate] Solo action '{action}' combined with others — discarding.",
        "validate_duplicate": "[Validate] Duplicate actions '{action}' — discarding.",
        "llm_parse_error": "Error parsing LLM response: {error}",
        "llm_comm_error": "Communication error with Ollama: {error}",
        "cleanup_removed": "[Cleanup] Removed {count} bad interactions from history.",
        "cleanup_clean": "[Cleanup] History clean, nothing removed.",
        "cleanup_error": "[Cleanup] Cleanup error: {error}",
        "learn_new": "[Learn] {count} new learning(s): {items}",
        "learn_none": "[Learn] No new learnings extracted.",
        "learn_error": "[Learn] Extraction error: {error}",
        # CommandExecutor
        "no_command": "No command received.",
        "app_not_found": "Application {target} not found in my records, Sir.",
        "close_app_error": "{target} is not responding to termination, Sir.",
        "search_browser_fallback": "Browser opened with the search, Sir. Could not extract results to summarise.",
        "search_fallback": "Search opened in the browser, Sir.",
        "search_error": "Error summarising search: {error}",
        "search_results_error": "Error fetching results: {error}",
        "screenshot_fail": "Screen capture failed, Sir. Imaging systems unavailable.",
        "time_exact": "Exactly {h} o'clock, Sir.",
        "time_normal": "{h}:{m:02d}, Sir.",
        "windows_listing": "Open windows: {listing}.",
        "no_windows": "No windows found.",
        "wmctrl_missing": "wmctrl not installed.",
        "command_blocked": "Command '{cmd}' not permitted for security reasons.",
        "command_executed": "Command executed.",
        "command_timeout": "Command timed out.",
        "workspace_invalid": "Invalid workspace number.",
        "weather_fail": "Could not access meteorological data, Sir.",
        "weather_error": "Error consulting weather: {error}",
        "weather_unavailable": "Forecast unavailable for {days} days ahead (maximum 3 days).",
        "news_fail": "Could not access news channels, Sir.",
        "news_error": "Error consulting news: {error}",
        "monitor_not_found": "Monitor '{target}' not found, Sir.",
        "screen_capture_fail": "Screen capture failed, Sir.",
        "screen_analysis_fail": "Visual analysis failed, Sir.",
        "selection_analysis_fail": "Failed to process selected text, Sir.",
        "device_not_found": "Device '{target}' not registered, Sir.",
        "device_action_invalid": "Action '{args}' invalid for {target}, Sir.",
        "timer_no_duration": "I couldn't identify the timer duration, Sir.",
        "timer_expired": "Sir, the {duration} timer has expired.",
        "battery_info": "Battery at {pct}, Sir.",
        "battery_unavailable": "Battery information unavailable, Sir.",
        "battery_error": "Could not access battery data, Sir.",
        "system_info_template": "System active {uptime}. Memory: {mem_used} of {mem_total}. Root disk: {disk_pct} in use.",
        "system_info_error": "Failed to collect system data, Sir.",
        "vision_freeing_vram": "Freeing VRAM for vision model...",
        "vision_loading": "Loading vision model ({model})...",
        "vision_raw": "Raw analysis: {analysis}",
        "vision_restoring": "Restoring models...",
        "vision_restored": "Models restored.",
        "selection_chars": "Selected text ({count} chars): {preview}...",
        "llm_default_error": "Sorry, I didn't understand the command.",
        "llm_request_error": "Error processing the command.",
        # Banner
        "banner_subtitle": "Local Voice Assistant - 100%% Offline",
        "shutting_down": "Shutting down Orion...",
        "shutdown_complete": "Orion shut down.",
    },

    # ── Executor LLM Prompts ────────────────────────────────────────
    "executor": {
        "search_summary_prompt": (
            "Search results for \"{query}\":\n{snippets}\n\n"
            "User question: \"{question}\"\n\n"
            "Summarise the results concisely in English, "
            "in the tone of J.A.R.V.I.S. Highlight the most relevant information. "
            "Address the user as Sir. Maximum 5 sentences."
        ),
        "weather_summary_prompt": (
            "Weather data: {data}\n\n"
            "User question: \"{question}\"\n\n"
            "Answer in English directly and concisely, "
            "in the tone of J.A.R.V.I.S. Focus on what was asked. "
            "Address the user as Sir. Maximum 3 short sentences."
        ),
        "news_summary_prompt": (
            "News headlines:\n{headlines}\n\n"
            "User question: \"{question}\"\n\n"
            "You are Orion, an AI in the style of J.A.R.V.I.S. Summarise the news "
            "in English intelligently and concisely. "
            "Highlight what is most relevant to the user's question. "
            "Address them as Sir. Maximum 4 short, direct sentences."
        ),
        "screen_analysis_prompt": (
            "Content extracted from screen:\n{analysis}\n\n"
            "User question: \"{question}\"\n\n"
            "Task: {task_hint}\n\n"
            "Answer in English concisely, "
            "in the tone of J.A.R.V.I.S. Address them as Sir. "
            "Maximum 5 sentences. Focus on what was asked."
        ),
        "selection_analysis_prompt": (
            "Text selected by user:\n\"{selected}\"\n\n"
            "User request: \"{question}\"\n\n"
            "Task: {task_hint}\n\n"
            "Answer in English concisely, "
            "in the tone of J.A.R.V.I.S. Address them as Sir. "
            "Focus on what was asked."
        ),
        "motivational_prompt": (
            "You are a sophisticated AI like J.A.R.V.I.S. Generate a short, "
            "inspiring phrase in English for your master to start working. "
            "MAXIMUM 8 words. Confident and elegant tone. No quotes. Just the phrase."
        ),
        "screen_task_instructions": {
            "translate": "Translate the text extracted from the screen to English.",
            "summarise": "Summarise the screen content concisely.",
            "summarize": "Summarise the screen content concisely.",
            "read": "Read and reproduce the visible text on screen.",
            "explain": "Explain the screen content clearly and didactically.",
        },
        "screen_task_default": "Answer the user's question about the screen content.",
        "selection_task_instructions": {
            "translate": "Translate the text to English. If already in English, translate to Portuguese.",
            "summarise": "Summarise the text concisely.",
            "summarize": "Summarise the text concisely.",
            "read": "Read and reproduce the text.",
            "explain": "Explain the text content clearly and didactically.",
            "correct": "Correct grammar and spelling errors in the text. Show the corrected text.",
        },
        "selection_task_default": "Answer the user's question about the text.",
        "weather_fallback_query": "weather forecast {location} today",
        "news_fallback_query": "news {query} today",
        "news_default_query": "world news today",
        "learnings_header": "Learnings from previous conversations:",
        "shutdown_confirm_words": ("yes", "confirm", "go ahead", "affirmative", "sure", "do it", "proceed"),
        "whisper_initial_prompt": (
            "Orion, what time is it? Open Chrome. Close everything. "
            "Shut down the computer. Turn on the porch light. "
            "Search for. Turn up the volume. Run a demonstration."
        ),
        "timer_words": {
            "hours": ("hour", "hours"),
            "seconds": ("second", "seconds", "sec"),
        },
        "relative_days": {
            "today": 0,
            "tomorrow": 1,
            "day after tomorrow": 2,
        },
    },
}
