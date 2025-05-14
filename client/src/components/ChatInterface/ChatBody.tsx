import React, { useRef, useEffect } from "react";

import "../../App.css"; // Adjust the path as necessary
interface Message {
  sender: string;
  text: string;
}

interface ChatBodyProps {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  welcomeMessage: string;
}

const ChatBody: React.FC<ChatBodyProps> = ({
  messages,
  isLoading,
  error,
  welcomeMessage,
}) => {
  const chatBodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="chat-body" ref={chatBodyRef}>
      {isLoading && messages.length === 0 && (
        <div className="message bot-message">
          <span className="bot-icon">🤖</span>
          <div className="bot-bubble">Thinking...</div>
        </div>
      )}
      {error && <div className="message error">{error}</div>}
      {messages.length === 0 && !isLoading && !error && (
        <div className="message bot-message">
          <span className="bot-icon">🤖</span>
          <div className="bot-bubble">{welcomeMessage}</div>
        </div>
      )}
      {messages.map((msg, index) => (
        <div
          key={index}
          className={`message ${
            msg.sender === "user" ? "user" : "bot"
          }-message`}
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
