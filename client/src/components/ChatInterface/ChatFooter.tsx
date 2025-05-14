import React from "react";
import {
  AudioOutlined,
  AudioMutedOutlined,
  ArrowUpOutlined,
} from "@ant-design/icons";

interface ChatFooterProps {
  inputValue: string;
  isLoading: boolean;
  isListening: boolean;
  voiceError: string | null;
  isSpeechSupported: boolean;
  onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onKeyPress: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  onSendMessage: () => void;
  onToggleVoiceRecognition: () => void;
}

const ChatFooter: React.FC<ChatFooterProps> = ({
  inputValue,
  isLoading,
  isListening,
  voiceError,
  isSpeechSupported,
  onInputChange,
  onKeyPress,
  onSendMessage,
  onToggleVoiceRecognition,
}) => {
  return (
    <div className="chat-footer">
      <div className="input-wrapper">
        <input
          type="text"
          placeholder="Type a message..."
          className="chat-input"
          value={inputValue}
          onChange={onInputChange}
          onKeyPress={onKeyPress}
          disabled={isLoading || isListening}
        />
        <div className="chat-controls">
          <button
            className={`voice-button ${isListening ? "active" : ""}`}
            onClick={onToggleVoiceRecognition}
            disabled={isLoading || !isSpeechSupported}
            aria-label={isListening ? "Stop listening" : "Start voice input"}
          >
            {isListening ? (
              <AudioMutedOutlined style={{ color: "#ff4d4f" }} />
            ) : (
              <AudioOutlined />
            )}
          </button>

          <ArrowUpOutlined
            className={`chat-input-icon ${
              inputValue.trim() && !isLoading ? "" : "disabled"
            }`}
            onClick={
              inputValue.trim() && !isLoading ? onSendMessage : undefined
            }
            disabled={!inputValue.trim() || isLoading}
            aria-label="Send message"
          />
        </div>
      </div>
      {isListening && (
        <div className="voice-status">
          <div className="pulse-animation"></div>
          <span>Listening... Speak now</span>
        </div>
      )}
      {voiceError && (
        <div className="voice-error-message">
          <span>{voiceError}</span>
        </div>
      )}
    </div>
  );
};

export default ChatFooter;
