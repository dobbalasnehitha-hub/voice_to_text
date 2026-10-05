
"""
Voice to Text (Speech Recognition) App

Transcribes audio files or microphone recordings using
the faster-whisper model.

Features:
- 90+ languages
- Automatic language detection
- Translation to English
- TXT transcript download
- SRT subtitle download
- Local processing
- No API key required
"""

import os
import tempfile

import streamlit as st
from faster_whisper import WhisperModel


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Voice to Text",
    page_icon="🎙️",
    layout="centered"
)


# ============================================================
# SUPPORTED LANGUAGES
# ============================================================

LANGUAGES = {
    "Auto detect": None,
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Tamil": "ta",
    "Bengali": "bn",
    "Marathi": "mr",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Gujarati": "gu",
    "Urdu": "ur",
    "French": "fr",
    "Spanish": "es",
    "German": "de",
    "Japanese": "ja",
}


# ============================================================
# SESSION STATE
# ============================================================

if "widget_key" not in st.session_state:
    st.session_state.widget_key = 0

if "result" not in st.session_state:
    st.session_state.result = None


# ============================================================
# CLEAR AUDIO FUNCTION
# ============================================================

def clear_audio():
    """
    Clear the current audio and previous transcription.
    """

    st.session_state.widget_key += 1
    st.session_state.result = None


# ============================================================
# LOAD WHISPER MODEL
# ============================================================

@st.cache_resource(
    show_spinner="Loading Whisper model... First run may take some time."
)
def load_model(model_size):
    """
    Load and cache the faster-whisper model.

    CPU + int8 is used for compatibility with most computers.
    """

    return WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8"
    )


# ============================================================
# FORMAT TIME FOR SRT
# ============================================================

def format_srt_time(seconds):
    """
    Convert seconds into SRT timestamp format.

    Example:
    65.25 -> 00:01:05,250
    """

    milliseconds = int(round(seconds * 1000))

    hours = milliseconds // 3_600_000
    milliseconds %= 3_600_000

    minutes = milliseconds // 60_000
    milliseconds %= 60_000

    seconds_part = milliseconds // 1000
    milliseconds %= 1000

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds_part:02d},"
        f"{milliseconds:03d}"
    )


# ============================================================
# CREATE SRT FILE
# ============================================================

def to_srt(segments):
    """
    Convert transcription segments into SRT subtitle format.
    """

    lines = []

    for index, segment in enumerate(
        segments,
        start=1
    ):

        start = format_srt_time(
            segment["start"]
        )

        end = format_srt_time(
            segment["end"]
        )

        text = segment["text"]

        lines.append(
            f"{index}\n"
            f"{start} --> {end}\n"
            f"{text}\n"
        )

    return "\n".join(lines)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ Settings")


model_size = st.sidebar.selectbox(
    "🤖 Whisper Model",
    [
        "tiny",
        "base",
        "small",
        "medium"
    ],
    index=1,
    help=(
        "Larger models are generally more accurate "
        "but require more RAM and processing time."
    )
)


language_name = st.sidebar.selectbox(
    "🌐 Language",
    list(LANGUAGES.keys())
)


task = st.sidebar.radio(
    "📝 Task",
    [
        "Transcribe",
        "Translate to English"
    ]
)


st.sidebar.markdown("---")

st.sidebar.caption(
    "💡 Tip: 'base' is a good starting model. "
    "Use 'small' for better accuracy if your computer can handle it."
)


# ============================================================
# MAIN APPLICATION
# ============================================================

st.title("🎙️ Voice to Text")

st.write(
    "Upload an audio file or record your voice "
    "and convert speech into text."
)


# ============================================================
# AUDIO INPUT
# ============================================================

current_key = st.session_state.widget_key

tab_upload, tab_record = st.tabs(
    [
        "📁 Upload Audio",
        "🎤 Record Voice"
    ]
)

audio = None


# ============================================================
# UPLOAD AUDIO
# ============================================================

with tab_upload:

    uploaded_audio = st.file_uploader(
        "Choose an audio file",
        type=[
            "mp3",
            "wav",
            "m4a",
            "ogg",
            "flac",
            "webm",
            "mp4"
        ],
        key=f"upload_{current_key}"
    )

    if uploaded_audio is not None:
        audio = uploaded_audio


# ============================================================
# RECORD AUDIO
# ============================================================

with tab_record:

    recorded_audio = st.audio_input(
        "🎤 Click to record",
        key=f"record_{current_key}"
    )

    if recorded_audio is not None:
        audio = recorded_audio


# ============================================================
# PROCESS AUDIO
# ============================================================

if audio is not None:

    st.audio(audio)

    # Create a unique ID for the current audio.
    audio_name = getattr(
        audio,
        "name",
        "recording"
    )

    audio_size = getattr(
        audio,
        "size",
        0
    )

    audio_id = (
        f"{audio_name}_{audio_size}"
    )

    st.markdown("---")

    # ========================================================
    # BUTTONS
    # ========================================================

    col1, col2 = st.columns(2)

    convert_button = col1.button(
        "📝 Convert to Text",
        type="primary",
        use_container_width=True
    )

    clear_button = col2.button(
        "🗑️ Clear / New Audio",
        use_container_width=True
    )

    if clear_button:
        clear_audio()
        st.rerun()


    # ========================================================
    # CONVERT AUDIO
    # ========================================================

    if convert_button:

        temp_path = None

        try:

            # Determine file extension.
            extension = os.path.splitext(
                audio_name
            )[1]

            if not extension:
                extension = ".wav"


            # Create temporary audio file.
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=extension
            ) as temp_file:

                temp_file.write(
                    audio.getvalue()
                )

                temp_path = temp_file.name


            # Load Whisper model.
            with st.spinner(
                "🤖 Loading Whisper model..."
            ):

                model = load_model(
                    model_size
                )


            # Determine task.
            whisper_task = (
                "translate"
                if task == "Translate to English"
                else "transcribe"
            )


            # Determine language.
            selected_language = LANGUAGES[
                language_name
            ]


            # Transcribe audio.
            with st.spinner(
                "🎙️ Transcribing audio..."
            ):

                segments_generator, info = (
                    model.transcribe(
                        temp_path,
                        language=selected_language,
                        task=whisper_task,
                        beam_size=5,
                        vad_filter=True
                    )
                )


                # Convert generator to list.
                segments = []

                for segment in segments_generator:

                    segments.append(
                        {
                            "start": segment.start,
                            "end": segment.end,
                            "text": segment.text.strip()
                        }
                    )


            # =================================================
            # SAVE RESULT
            # =================================================

            transcript_text = " ".join(
                segment["text"]
                for segment in segments
            ).strip()


            st.session_state.result = {
                "audio_id": audio_id,
                "text": transcript_text,
                "segments": segments,
                "language": info.language,
                "probability": info.language_probability,
                "duration": info.duration
            }


            st.success(
                "✅ Transcription completed successfully!"
            )


        except Exception as error:

            st.error(
                "❌ Failed to process the audio."
            )

            st.info(
                "Please make sure the audio file is valid "
                "and try again."
            )

            with st.expander(
                "Show technical error"
            ):
                st.code(
                    str(error)
                )


        finally:

            # Delete temporary file.
            if (
                temp_path is not None
                and os.path.exists(temp_path)
            ):

                try:
                    os.remove(temp_path)

                except Exception:
                    pass


    # ========================================================
    # DISPLAY RESULT
    # ========================================================

    result = st.session_state.result


    if (
        result is not None
        and result["audio_id"] == audio_id
    ):

        probability = (
            result["probability"] * 100
        )


        # ====================================================
        # INFORMATION
        # ====================================================

        st.success(
            f"🌐 Detected Language: "
            f"**{result['language']}** "
            f"({probability:.0f}% confidence)"
        )

        st.info(
            f"⏱️ Audio Duration: "
            f"{result['duration']:.1f} seconds"
        )


        # ====================================================
        # TRANSCRIPT
        # ====================================================

        st.subheader(
            "📝 Transcript"
        )

        st.text_area(
            "Recognized Text",
            result["text"],
            height=220
        )


        # ====================================================
        # TIMESTAMPS
        # ====================================================

        with st.expander(
            "⏱️ Show Timestamps"
        ):

            if result["segments"]:

                for segment in result["segments"]:

                    st.write(
                        f"`[{segment['start']:6.1f}s → "
                        f"{segment['end']:6.1f}s]` "
                        f"{segment['text']}"
                    )

            else:

                st.write(
                    "No timestamp segments available."
                )


        # ====================================================
        # DOWNLOADS
        # ====================================================

        st.subheader(
            "⬇️ Download"
        )

        col1, col2 = st.columns(2)


        # TXT download
        col1.download_button(
            "⬇️ Download TXT",
            data=result["text"],
            file_name="transcript.txt",
            mime="text/plain",
            use_container_width=True
        )


        # SRT download
        srt_content = to_srt(
            result["segments"]
        )

        col2.download_button(
            "⬇️ Download SRT",
            data=srt_content,
            file_name="transcript.srt",
            mime="text/plain",
            use_container_width=True
        )


else:

    st.info(
        "👆 Upload an audio file or record your voice "
        "to begin."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "🎙️ Voice to Text | "
    "Powered by faster-whisper and Streamlit"
)
