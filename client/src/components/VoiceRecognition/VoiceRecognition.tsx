import { useState, useEffect, useRef } from "react";

const SpeechRecognitionAPI =
  window.SpeechRecognition || (window as any).webkitSpeechRecognition;

interface VoiceRecognitionProps {
  onTranscript: (transcript: string) => void;
  onError: (error: string) => void;
  onListeningChange?: (isListening: boolean) => void;
}

const useVoiceRecognition = ({
  onTranscript,
  onError,
  onListeningChange,
}: VoiceRecognitionProps) => {
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (!SpeechRecognitionAPI) {
      const errorMsg = "Speech recognition is not supported in this browser.";
      setError(errorMsg);
      onError(errorMsg);
      return;
    }

    recognitionRef.current = new SpeechRecognitionAPI();
    const recognition = recognitionRef.current;

    recognition.interimResults = false; // We only want final results
    recognition.continuous = false; // Stop after each utterance
    recognition.lang = "en-US";

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0])
        .map((result) => result.transcript)
        .join("");
      onTranscript(transcript);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      let errorMsg = "";
      switch (event.error) {
        case "no-speech":
          errorMsg = "No speech detected.";
          break;
        case "audio-capture":
          errorMsg = "No microphone found.";
          break;
        case "not-allowed":
          errorMsg = "Microphone access denied.";
          break;
        default:
          errorMsg = `Error: ${event.error}`;
      }
      setError(errorMsg);
      onError(errorMsg);
      setIsListening(false);
      if (onListeningChange) onListeningChange(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      if (onListeningChange) onListeningChange(false);
    };

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
    };
  }, [onTranscript, onError, onListeningChange]);

  const toggleListening = async () => {
    if (!recognitionRef.current) {
      const errorMsg = "Recognition not initialized";
      setError(errorMsg);
      onError(errorMsg);
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      return;
    }

    try {
      // Check microphone permissions
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());

      setError(null);
      recognitionRef.current.start();
      setIsListening(true);
      if (onListeningChange) onListeningChange(true);
    } catch (err: any) {
      let errorMsg = "Microphone access denied.";
      if (err.name === "NotFoundError") {
        errorMsg = "No microphone found.";
      }
      setError(errorMsg);
      onError(errorMsg);
      setIsListening(false);
      if (onListeningChange) onListeningChange(false);
    }
  };

  return {
    isListening,
    error,
    toggleListening,
    isSupported: !!SpeechRecognitionAPI,
  };
};

export default useVoiceRecognition;
