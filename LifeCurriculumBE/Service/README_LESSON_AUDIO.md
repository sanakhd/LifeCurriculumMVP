# Lesson Audio Generator

The Lesson Audio Generator is a comprehensive system that converts lesson conversations into high-quality TTS audio files using OpenAI's text-to-speech capabilities.

## Features

- **Multi-voice Support**: Automatically assigns different voices to different hosts (Host A, Host B, etc.)
- **UUID-based Organization**: Each audio file gets a unique identifier for easy tracking
- **Manifest Tracking**: JSON manifest files track all generated audio metadata
- **Idempotent Generation**: Re-running generation skips already existing files
- **Error Recovery**: Partial failures don't break the entire generation process
- **Multiple Endpoints**: Generate, check status, delete, and regenerate audio

## API Endpoints

### 1. Generate Lesson Audio
```
POST /programs/generate-lesson-audio
```

Generate TTS audio for all conversation chunks in a lesson.

**Request Body:**
```json
{
  "program_id": "program-uuid-here",
  "day_number": 1,
  "voice_mapping": {
    "Host A": "alloy",
    "Host B": "echo"
  }
}
```

**Response:**
```json
{
  "success": true,
  "lesson_id": "lesson-uuid-here",
  "audio_files": [
    {
      "chunk_index": 0,
      "audio_id": "audio-uuid-here",
      "speaker": "Host A",
      "voice": "alloy",
      "file_path": "program_audios/lesson-uuid/audio-uuid.wav",
      "duration_seconds": 15,
      "regenerated": true
    }
  ],
  "total_duration_seconds": 180,
  "files_generated": 8,
  "files_total": 8,
  "manifest_path": "program_audios/lesson-uuid/manifest.json"
}
```

### 2. Check Audio Status
```
GET /programs/lessons/{program_id}/{day_number}/audio-status
```

Check if audio has been generated for a lesson.

**Response:**
```json
{
  "exists": true,
  "lesson_id": "lesson-uuid-here",
  "manifest": {
    "lesson_id": "lesson-uuid-here",
    "program_id": "program-uuid-here",
    "day_number": 1,
    "generated_at": "2025-01-16T05:30:00Z",
    "voice_mapping": {
      "Host A": "alloy",
      "Host B": "echo"
    },
    "audio_files": [...]
  },
  "audio_directory": "program_audios/lesson-uuid-here"
}
```

### 3. Delete Lesson Audio
```
DELETE /programs/lessons/{program_id}/{day_number}/audio
```

Delete all generated audio files for a lesson.

**Response:**
```json
{
  "success": true,
  "lesson_id": "lesson-uuid-here",
  "deleted_files": [
    "program_audios/lesson-uuid/audio-uuid-1.wav",
    "program_audios/lesson-uuid/audio-uuid-2.wav",
    "program_audios/lesson-uuid/manifest.json"
  ],
  "files_deleted": 3
}
```

### 4. Regenerate Audio
```
POST /programs/regenerate-lesson-audio
```

Force regeneration of audio, even if files already exist.

### 5. Available Voices
```
GET /programs/available-voices
```

Get list of available OpenAI TTS voices and default mappings.

## File Organization

Audio files are organized in the following structure:

```
program_audios/
├── {lesson_uuid_1}/
│   ├── {audio_uuid_1}.wav          # Host A's first turn
│   ├── {audio_uuid_2}.wav          # Host B's response  
│   ├── {audio_uuid_3}.wav          # Host A's second turn
│   └── manifest.json               # Metadata and tracking
├── {lesson_uuid_2}/
│   └── ...
```

## Voice Mapping

### Default Voice Assignments
- **Host A**: `alloy` - Neutral, informative voice
- **Host B**: `echo` - Warm, conversational voice  
- **Host C**: `fable` - British accent, expressive
- **Host D**: `onyx` - Deep, authoritative voice
- **Host E**: `nova` - Friendly, approachable voice
- **Host F**: `shimmer` - Expressive, dynamic voice

### Custom Voice Mapping
You can override the default voice assignments:

```json
{
  "voice_mapping": {
    "Host A": "nova",
    "Host B": "shimmer",
    "Host C": "alloy"
  }
}
```

## Usage Examples

### Generate Audio for a Lesson
```bash
curl -X POST "http://localhost:8000/programs/generate-lesson-audio" \
  -H "Content-Type: application/json" \
  -d '{
    "program_id": "your-program-id",
    "day_number": 1,
    "voice_mapping": {
      "Host A": "alloy",
      "Host B": "echo"
    }
  }'
```

### Check Status
```bash
curl "http://localhost:8000/programs/lessons/your-program-id/1/audio-status"
```

### Delete Audio
```bash
curl -X DELETE "http://localhost:8000/programs/lessons/your-program-id/1/audio"
```

## Testing

Run the test script to validate the implementation:

```bash
cd Service
python test_audio_generation.py
```

This will:
1. Find an existing program with lessons
2. Check current audio status
3. Generate TTS audio for conversation chunks
4. Verify the generated files and manifest

## Implementation Details

### AudioGeneratorService
The core service (`app/services/audio_generator.py`) handles:
- Lesson data retrieval from program store
- TTS generation via OpenAI API
- File organization and UUID generation
- Metadata tracking and manifest creation
- Error handling and recovery

### Error Handling
- **Partial Failures**: If TTS fails for one chunk, others continue processing
- **Idempotent**: Re-running generation skips existing files
- **Validation**: Proper error messages for missing programs/lessons
- **API Limits**: Handles OpenAI API rate limits and errors

### Performance Considerations
- Files are generated sequentially to respect API limits
- Audio files are saved locally for fast access
- Manifest files enable quick status checks without file system scanning
- Duration estimation provides rough playback time calculations

## Future Enhancements

1. **Concatenated Audio**: Create single merged file for entire conversation
2. **Background Processing**: Use task queues for async generation
3. **Multiple Formats**: Support MP3, OGG formats
4. **MinIO Integration**: Store audio in object storage for distributed access
5. **SSML Support**: Add prosody control for better speech synthesis
6. **Batch Processing**: Generate audio for multiple lessons at once

## Configuration

The system uses existing OpenAI configuration from `app/config.py`:

```python
openai_tts_model: str = "tts-1"
openai_default_voice: str = "alloy" 
openai_default_audio_format: str = "wav"
```

Audio files are stored in the `program_audios/` directory relative to the Service root.
