import React from "react";

interface ChatHeaderProps {
  companyName: string;
  onClose: () => void;
  onMouseDown: (e: React.MouseEvent) => void;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
  companyName,
  onClose,
  onMouseDown,
}) => {
  return (
    <div className="chat-header" onMouseDown={onMouseDown}>
      <span>{companyName}</span>
      <button onClick={onClose} className="close-chat">
        ×
      </button>
    </div>
  );
};

export default ChatHeader;
