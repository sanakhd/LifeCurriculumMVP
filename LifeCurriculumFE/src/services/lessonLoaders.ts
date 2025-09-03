// src/services/lessonLoaders.ts
import { lifeCurriculumApi } from '../services/api';
import type { LessonData, AudioSegment } from '../types/lesson';
import { getDisplayName } from '../utils/voices';

// Simple cache to avoid re-fetching the same lesson data
const lessonCache = new Map<string, { lesson: LessonData; segments: AudioSegment[]; timestamp: number }>();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

/** Convert API lesson → LessonData the page expects (kept 1:1 with current shape) */
export function mapApiLessonToLessonData(lesson: any, day: number): LessonData {
  return {
    id: lesson.id || lesson.lesson_uuid,
    title: lesson.title || `Day ${day}`,
    content: lesson.content || '',
    transcript: lesson.transcript || lesson.content || '',
    conversationChunks: lesson.conversation_chunks || [],
    primary_interaction: lesson.primary_interaction,
    learning_objectives: lesson.learning_objectives || lesson.objectives || [],
    description: lesson.description || lesson.summary || '',
  };
}

/** Split transcript into text-only segments as a fallback when audio isn’t available */
export function createTranscriptSegments(data: LessonData): AudioSegment[] {
  const transcriptText = data.transcript || data.content || '';
  const paragraphs = transcriptText.split('\n\n').filter((p) => p.trim().length > 0);

  if (!paragraphs.length) {
    const sentences = transcriptText.split(/[.!?]+/).filter((s) => s.trim().length > 0);
    const out: AudioSegment[] = [];
    for (let i = 0; i < sentences.length; i += 2) {
      const text = sentences.slice(i, i + 2).join('. ').trim() + '.';
      if (text.length > 1) {
        out.push({
          audio_id: `text-${i}`,
          speaker: 'Narrator',
          voice: getDisplayName('narrator'),
          duration_seconds: 0,
          chunk_index: i,
          stream_url: '',
          text,
        });
      }
    }
    return out;
  }

  return paragraphs.map((paragraph, index) => ({
    audio_id: `text-${index}`,
    speaker: 'Narrator',
    voice: getDisplayName('narrator'),
    duration_seconds: 0,
    chunk_index: index,
    stream_url: '',
    text: paragraph,
  }));
}

/** Try to fetch an existing playlist; return segments or null if none/failed */
export async function tryLoadAudioPlaylist(
  lessonUuid: string,
  data: LessonData
): Promise<AudioSegment[] | null> {
  const playlist = await lifeCurriculumApi.getLessonAudioPlaylist(lessonUuid);
  if (!playlist?.playlist?.length) return null;

  const segments: AudioSegment[] = playlist.playlist.map((item: any, index: number) => {
    const chunkText =
      data.conversationChunks[index]?.text ||
      data.conversationChunks[index]?.content ||
      `${item.speaker}: [Audio ${index + 1}]`;

    let streamUrl = item.stream_url;
    if (!streamUrl || !streamUrl.startsWith('http')) {
      streamUrl = lifeCurriculumApi.getAudioStreamUrl(lessonUuid, item.audio_id);
    }
    return { ...item, stream_url: streamUrl, text: chunkText };
  });

  return segments;
}

/** Ask backend to generate audio, then reload playlist. Fall back to transcript if still not available. */
export async function ensureAudioOrTranscript(
  lessonUuid: string,
  data: LessonData
): Promise<AudioSegment[]> {
  // voice ids come from your utils (no inline mapping here)
  const voice_mapping: Record<string, string> = {
    'Host A': getDisplayName('Host A'),
    'Host B': getDisplayName('Host B'),
    narrator: getDisplayName('narrator'),
  };

  // request generation
  const resp = await lifeCurriculumApi.generateLessonAudio({ lesson_uuid: lessonUuid, voice_mapping });

  // whether generation succeeds or not, try playlist once more
  if (resp?.success) {
    const segments = await tryLoadAudioPlaylist(lessonUuid, data);
    if (segments?.length) return segments;
  }

  // final fallback
  return createTranscriptSegments(data);
}

/**
 * Load lesson + audio segments with simple progress callbacks.
 * Keeps the page dumb; all side effects live here.
 */
export async function loadLessonBundle(
  programId: string,
  day: number,
  onProgress?: (pct: number) => void
): Promise<{ lesson: LessonData; segments: AudioSegment[] }> {
  const cacheKey = `${programId}-${day}`;
  const now = Date.now();
  
  // Check cache first
  const cached = lessonCache.get(cacheKey);
  if (cached && (now - cached.timestamp) < CACHE_DURATION) {
    onProgress?.(100);
    return { lesson: cached.lesson, segments: cached.segments };
  }

  onProgress?.(10);
  const raw = await lifeCurriculumApi.getSingleLesson(programId, day);
  if (!raw) throw new Error('Lesson not found');

  onProgress?.(30);
  const lesson = mapApiLessonToLessonData(raw, day);

  onProgress?.(50);
  const uuid = raw.lesson_uuid || raw.id;

  // try playlist first
  onProgress?.(60);
  let segments = null;
  try {
    segments = await tryLoadAudioPlaylist(uuid, lesson);
  } catch {
    // swallow; fallback below
  }

  if (!segments || segments.length === 0) {
    onProgress?.(70);
    try {
      segments = await ensureAudioOrTranscript(uuid, lesson);
      onProgress?.(100);
    } catch {
      segments = createTranscriptSegments(lesson);
      onProgress?.(100);
    }
  } else {
    onProgress?.(100);
  }

  const result = { lesson, segments: segments! };
  
  // Cache the result
  lessonCache.set(cacheKey, { ...result, timestamp: now });
  
  // Clean up old cache entries (keep cache size reasonable)
  if (lessonCache.size > 20) {
    const oldestEntries = Array.from(lessonCache.entries())
      .sort(([, a], [, b]) => a.timestamp - b.timestamp)
      .slice(0, 10);
    oldestEntries.forEach(([key]) => lessonCache.delete(key));
  }

  return result;
}
