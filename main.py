from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import mido
import os
from typing import Optional
import requests
import json
import logging
import re
import struct
import zlib
from tempfile import NamedTemporaryFile

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextRequest(BaseModel):
    text: str
    output_type: Optional[str] = None  # For legacy endpoints

def clean_json_response(response: str) -> str:
    # Remove markdown code block syntax
    response = re.sub(r'```json\n?', '', response)
    response = re.sub(r'\n?```$', '', response)
    # Remove any leading/trailing whitespace
    response = response.strip()
    return response

def strip_json_comments(s: str) -> str:
    # Remove // comments
    return re.sub(r'//.*', '', s)

def generate_midi_prompt(text: str) -> str:
    return f"""Generate a MIDI pattern in JSON format based on: {text}
Only output valid JSON. Do not include comments or explanations.
If the pattern is long, only include the first 8 bars.

Format:
{{
    "tempo": 120,
    "time_signature": [4, 4],
    "notes": [
        {{"pitch": 60, "velocity": 100, "duration": 1.0, "start": 0.0}}
    ]
}}
"""

def generate_serum_prompt(text: str) -> str:
    return f"""Generate a Serum preset in JSON format based on: {text}

Format:
{{
    "preset_name": "name",
    "oscillators": {{
        "osc1": {{
            "waveform": "Basic Shapes",
            "wavetable_pos": 0,
            "level": 1.0,
            "pan": 0,
            "octave": 0,
            "semitones": 0,
            "detune": 0,
            "phase": 0,
            "unison": {{
                "voices": 1,
                "detune": 0
            }}
        }},
        "osc2": {{
            "waveform": "Basic Shapes",
            "wavetable_pos": 0,
            "level": 1.0,
            "pan": 0,
            "octave": 0,
            "semitones": 0,
            "detune": 0,
            "phase": 0,
            "unison": {{
                "voices": 1,
                "detune": 0
            }}
        }}
    }},
    "filters": {{
        "filter1": {{
            "type": "LP 24",
            "cutoff": 1.0,
            "resonance": 0,
            "drive": 0,
            "mix": 1.0
        }},
        "filter2": {{
            "type": "LP 24",
            "cutoff": 1.0,
            "resonance": 0,
            "drive": 0,
            "mix": 1.0
        }}
    }},
    "envelopes": {{
        "env1": {{
            "attack": 0.01,
            "decay": 0.1,
            "sustain": 1.0,
            "release": 0.1
        }},
        "env2": {{
            "attack": 0.01,
            "decay": 0.1,
            "sustain": 1.0,
            "release": 0.1
        }}
    }},
    "lfos": {{
        "lfo1": {{
            "rate": 1.0,
            "shape": "Sine",
            "trigger_mode": "Free"
        }}
    }},
    "effects": {{
        "reverb": {{
            "mix": 0.2,
            "size": 0.5,
            "decay": 0.5,
            "predelay": 0
        }},
        "delay": {{
            "mix": 0.2,
            "time": 0.5,
            "feedback": 0.5
        }}
    }}
}}"""

def create_fxp_file(preset_data: dict, output_path: str) -> bool:
    try:
        # Convert the preset data to a binary format that Serum expects
        # This is a simplified version - we'll need to map our parameters to Serum's format
        preset_name = preset_data.get("preset_name", "Untitled")[:28].ljust(28, '\0')
        
        # Create the FXP header
        header = struct.pack('>4si4si4sii28s',
            b'CcnK',  # Magic number
            0xfc6,    # Header length
            b'FPCh',  # Format identifier
            1,        # Version
            b'XfsX',  # Serum identifier
            1,        # Format version
            1,        # Number of programs
            preset_name.encode()  # Preset name
        )
        
        # Convert preset data to binary format
        # This is where we need to map our parameters to Serum's binary format
        # For now, we'll just JSON encode and compress it
        preset_bytes = json.dumps(preset_data).encode()
        compressed_data = zlib.compress(preset_bytes)
        
        # Write the file
        with open(output_path, 'wb') as f:
            f.write(header)
            f.write(struct.pack('>i', len(compressed_data)))  # Data length
            f.write(compressed_data)
        
        return True
    except Exception as e:
        logger.error(f"Failed to create FXP file: {str(e)}")
        return False

def json_to_midi(midi_data, output_path):
    try:
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)

        # Set tempo
        tempo = mido.bpm2tempo(midi_data.get('tempo', 120))
        track.append(mido.MetaMessage('set_tempo', tempo=tempo))

        # Set time signature
        ts = midi_data.get('time_signature', [4, 4])
        track.append(mido.MetaMessage('time_signature', numerator=ts[0], denominator=ts[1]))

        # Add notes
        ticks_per_beat = mid.ticks_per_beat
        last_tick = 0
        for note in sorted(midi_data['notes'], key=lambda n: n.get('start', 0)):
            start_tick = int(note.get('start', 0) * ticks_per_beat)
            duration_tick = int(note.get('duration', 1) * ticks_per_beat)
            pitch = note['pitch']
            velocity = note['velocity']
            # Calculate delta time
            delta = max(0, start_tick - last_tick)
            track.append(mido.Message('note_on', note=pitch, velocity=velocity, time=delta))
            track.append(mido.Message('note_off', note=pitch, velocity=0, time=duration_tick))
            last_tick = start_tick + duration_tick
        mid.save(output_path)
        return True
    except Exception as e:
        logger.error(f"Failed to create MIDI file: {str(e)}")
        return False

async def call_lm_studio(prompt: str) -> str:
    try:
        logger.debug(f"Sending prompt to LM Studio: {prompt}")
        response = requests.post(
            "http://localhost:1234/v1/chat/completions",
            json={
                "model": "gemma-3-27b-it-qat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 2048
            }
        )
        logger.debug(f"LM Studio response status: {response.status_code}")
        logger.debug(f"LM Studio response: {response.text}")
        
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Failed to connect to LM Studio: {str(e)}")
        raise HTTPException(status_code=503, detail="LM Studio is not running or not accessible. Please make sure it's running on port 1234.")
    except Exception as e:
        logger.error(f"Error calling LM Studio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calling LM Studio: {str(e)}")

@app.post("/generate/midi")
async def generate_midi(request: TextRequest):
    prompt = generate_midi_prompt(request.text)
    logger.debug(f"Generated MIDI prompt: {prompt}")
    ai_response = await call_lm_studio(prompt)
    logger.debug(f"AI response: {ai_response}")
    try:
        cleaned_response = clean_json_response(ai_response)
        cleaned_response = strip_json_comments(cleaned_response)
        logger.debug(f"Cleaned response (no comments): {cleaned_response}")
        midi_data = json.loads(cleaned_response)
        logger.debug(f"Parsed MIDI data: {midi_data}")
        with NamedTemporaryFile(delete=False, suffix='.mid') as tmpfile:
            if json_to_midi(midi_data, tmpfile.name):
                tmpfile.flush()
                return FileResponse(
                    tmpfile.name,
                    media_type="audio/midi",
                    filename="generated_ai_midi.mid"
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to create MIDI file")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Invalid JSON response from AI: {str(e)}")

# (Legacy endpoint for backward compatibility)
@app.post("/generate")
async def generate_content(request: TextRequest):
    try:
        logger.debug(f"Received request: {request}")
        
        if request.output_type == "midi":
            prompt = generate_midi_prompt(request.text)
            logger.debug(f"Generated MIDI prompt: {prompt}")
            ai_response = await call_lm_studio(prompt)
            logger.debug(f"AI response: {ai_response}")
            
            try:
                cleaned_response = clean_json_response(ai_response)
                cleaned_response = strip_json_comments(cleaned_response)
                logger.debug(f"Cleaned response (no comments): {cleaned_response}")
                midi_data = json.loads(cleaned_response)
                logger.debug(f"Parsed MIDI data: {midi_data}")
                output_path = os.path.expanduser("~/Documents/generated_ai_midi.mid")
                if json_to_midi(midi_data, output_path):
                    return {"status": "success", "type": "midi", "data": midi_data, "file_path": output_path}
                else:
                    raise HTTPException(status_code=500, detail="Failed to create MIDI file")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Invalid JSON response from AI: {str(e)}")
                
        elif request.output_type == "serum":
            prompt = generate_serum_prompt(request.text)
            logger.debug(f"Generated Serum prompt: {prompt}")
            ai_response = await call_lm_studio(prompt)
            logger.debug(f"AI response: {ai_response}")
            
            try:
                cleaned_response = clean_json_response(ai_response)
                logger.debug(f"Cleaned response: {cleaned_response}")
                serum_data = json.loads(cleaned_response)
                logger.debug(f"Parsed Serum data: {serum_data}")
                
                # Generate FXP file
                output_path = os.path.expanduser("~/Documents/serum_preset.fxp")
                if create_fxp_file(serum_data, output_path):
                    return {
                        "status": "success",
                        "type": "serum",
                        "data": serum_data,
                        "file_path": output_path
                    }
                else:
                    raise HTTPException(status_code=500, detail="Failed to create FXP file")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Invalid JSON response from AI: {str(e)}")
        else:
            logger.error(f"Invalid output type: {request.output_type}")
            raise HTTPException(status_code=400, detail="Invalid output type")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 