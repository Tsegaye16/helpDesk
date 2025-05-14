import React from "react";
import ChatHeader from "./ChatHeader";
import ChatBody from "./ChatBody";
import ChatFooter from "./ChatFooter";
import ResizeHandles from "./ResizeHandles";

interface Message {
  sender: string;
  text: string;
}

interface ChatInterfaceProps {
  companyName: string;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  welcomeMessage: string;
  inputValue: string;
  isListening: boolean;
  voiceError: string | null;
  isSpeechSupported: boolean;
  chatSize: { width: number; height: number };
  chatPosition: { left: number; top: number };
  onClose: () => void;
  onChatMouseDown: (e: React.MouseEvent) => void;
  onResizeMouseDown: (handle: string) => (e: React.MouseEvent) => void;
  onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onKeyPress: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  onSendMessage: () => void;
  onToggleVoiceRecognition: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  companyName,
  messages,
  isLoading,
  error,
  welcomeMessage,
  inputValue,
  isListening,
  voiceError,
  isSpeechSupported,
  chatSize,
  chatPosition,
  onClose,
  onChatMouseDown,
  onResizeMouseDown,
  onInputChange,
  onKeyPress,
  onSendMessage,
  onToggleVoiceRecognition,
}) => {
  return (
    <div
      className="chat-interface"
      style={{
        width: `${chatSize.width}px`,
        height: `${chatSize.height}px`,
        left: `${chatPosition.left}px`,
        top: `${chatPosition.top}px`,
      }}
    >
      <ChatHeader
        companyName={companyName}
        onClose={onClose}
        onMouseDown={onChatMouseDown}
      />
      <ChatBody
        messages={messages}
        isLoading={isLoading}
        error={error}
        welcomeMessage={welcomeMessage}
      />
      <ChatFooter
        inputValue={inputValue}
        isLoading={isLoading}
        isListening={isListening}
        voiceError={voiceError}
        isSpeechSupported={isSpeechSupported}
        onInputChange={onInputChange}
        onKeyPress={onKeyPress}
        onSendMessage={onSendMessage}
        onToggleVoiceRecognition={onToggleVoiceRecognition}
      />
      <ResizeHandles onResizeMouseDown={onResizeMouseDown} />
    </div>
  );
};

export default ChatInterface;
