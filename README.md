# FL Studio AI MCP

A simple application that generates MIDI patterns and Serum presets based on text input using AI.

## Setup

1. Install Python 3.8 or higher
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the server:
   ```bash
   python main.py
   ```

2. Start the client:
   ```bash
   python client.py
   ```

3. Enter your text request in the client window and select the desired output type (MIDI or Serum preset).

## Features

- Text-to-MIDI pattern generation
- Text-to-Serum preset generation
- Simple GUI interface
- REST API for integration with other applications

## TODO

- [ ] Implement AI integration (using Ollama or similar)
- [ ] Add MIDI file generation
- [ ] Add Serum FXP file generation
- [ ] Add FL Studio OSC integration
- [ ] Add preset preview functionality

## Development

This project uses:
- FastAPI for the server
- Tkinter for the client GUI
- Mido for MIDI handling
- Python-OSC for FL Studio communication 