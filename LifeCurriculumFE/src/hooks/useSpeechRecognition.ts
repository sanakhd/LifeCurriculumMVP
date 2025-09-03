import { useState, useEffect, useRef, useCallback } from 'react';

export const useSpeechRecognition = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const SpeechRecognition = 
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return;
    }

    setSpeechSupported(true);
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onerror = () => setIsRecording(false);
    recognition.onend = () => setIsRecording(false);

    recognitionRef.current = recognition;
  }, []);

  const startRecording = useCallback((onResult: (transcript: string) => void) => {
    if (!speechSupported || !recognitionRef.current) return;

    recognitionRef.current.onresult = (event: any) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        }
      }
      if (finalTranscript) {
        onResult(finalTranscript);
      }
    };

    try {
      recognitionRef.current.start();
      setIsRecording(true);
    } catch {
      setIsRecording(false);
    }
  }, [speechSupported]);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  const toggleRecording = useCallback((onResult: (transcript: string) => void) => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording(onResult);
    }
  }, [isRecording, startRecording, stopRecording]);

  return {
    isRecording,
    speechSupported,
    startRecording,
    stopRecording,
    toggleRecording
  };
};
