import React, { useRef, useEffect } from "react";
import "../../App.css";

interface Message {
  sender: string;
  text: string;
  isPending?: boolean; // Add this new property
}

interface ChatBodyProps {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  welcomeMessage: string;
  pendingUserMessage?: string; // Add this prop for immediate display
}

const ChatBody: React.FC<ChatBodyProps> = ({
  messages,
  isLoading,
  error,
  welcomeMessage,
  pendingUserMessage,
}) => {
  const chatBodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
    }
  }, [messages, pendingUserMessage]); // Add pendingUserMessage to dependencies

  // Combine regular messages with pending message if it exists
  const allMessages = [
    ...messages,
    ...(pendingUserMessage
      ? [{ sender: "user", text: pendingUserMessage, isPending: true }]
      : []),
  ];

  return (
    <div className="chat-body" ref={chatBodyRef}>
      {isLoading && messages.length === 0 && (
        <div className="message bot-message">
          <span className="bot-icon">🤖</span>
          <div className="bot-bubble">Thinking...</div>
        </div>
      )}
      {error && <div className="message error">{error}</div>}
      {messages.length === 0 && !isLoading && !error && !pendingUserMessage && (
        <div className="message bot-message">
          <span className="bot-icon">🤖</span>
          <div className="bot-bubble">{welcomeMessage}</div>
        </div>
      )}
      {allMessages.map((msg, index) => (
        <div
          key={index}
          className={`message ${
            msg.sender === "user" ? "user" : "bot"
          }-message ${msg.isPending ? "pending" : ""}`}
        >
          {msg.sender === "user" ? (
            <>
              <div className="user-bubble">{msg.text}</div>
              <span className="user-icon">👤</span>
            </>
          ) : (
            <>
              <span className="bot-icon">🤖</span>
              <div className="bot-bubble">{msg.text}</div>
            </>
          )}
        </div>
      ))}
      {isLoading && messages.length > 0 && (
        <div className="message bot-message">
          <span className="bot-icon">🤖</span>
          <div className="bot-bubble">Thinking...</div>
        </div>
      )}
    </div>
  );
};

export default ChatBody;
