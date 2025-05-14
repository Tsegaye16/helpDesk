import React, { useState, useRef, useEffect, useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  getCompanyName,
  chat,
  getChatHistory,
  initSession,
} from "./store/action/action";
import CustomFloatButton from "./components/FloatButton/FloatButton";
import ChatInterface from "./components/ChatInterface/ChatInterface";
import useVoiceRecognition from "./components/VoiceRecognition/VoiceRecognition";

const App: React.FC = () => {
  // State and refs
  const [position, setPosition] = useState({
    x: window.innerWidth - 80,
    y: window.innerHeight - 80,
  });
  const [isDragging, setIsDragging] = useState(false);
  const [initialPosition, setInitialPosition] = useState({ x: 0, y: 0 });
  const [tooltipPosition, setTooltipPosition] = useState<"left" | "right">(
    "left"
  );
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [chatSize, setChatSize] = useState({ width: 300, height: 400 });
  const [isResizing, setIsResizing] = useState(false);
  const [resizeStart, setResizeStart] = useState({ x: 0, y: 0 });
  const [activeHandle, setActiveHandle] = useState<string | null>(null);
  const [isChatDragging, setIsChatDragging] = useState(false);
  const [chatDragStart, setChatDragStart] = useState({ x: 0, y: 0 });

  const floatButtonRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  //const chatBodyRef = useRef<HTMLDivElement>(null);

  // Constants
  const minWidth = 200;
  const minHeight = 250;
  //const maxWidth = window.innerWidth - 20;
  //const maxHeight = window.innerHeight - 80;
  const buttonSize = 60;

  // Derived values
  const chatPosition = {
    left: position.x - chatSize.width + buttonSize / 2,
    top: position.y - chatSize.height + buttonSize / 2,
  };

  // Redux state and dispatch
  const dispatch = useDispatch();
  const {
    company,
    loading: companyLoading,
    error: companyError,
  } = useSelector((state: any) => state.companyName);
  const {
    messages,
    session_id,
    loading: chatLoading,
    error: chatError,
  } = useSelector((state: any) => state.chat);

  // Voice recognition
  const {
    isListening,
    error: voiceError,
    toggleListening,
    isSupported: isSpeechSupported,
  } = useVoiceRecognition({
    onTranscript: (transcript: any) => {
      setInputValue((prev) => prev + transcript);
    },
    onError: (error: any) => {
      console.error("Voice recognition error:", error);
    },
    onListeningChange: (listening: any) => {
      if (!listening && inputRef.current) {
        inputRef.current.focus();
      }
    },
  });

  // Welcome message
  const welcomeMessage = company?.result?.company_name
    ? `Welcome to ${company.result.company_name}'s chat support! How can we assist you today?`
    : "Welcome to our chat support! How can we assist you today?";

  // Effects
  useEffect(() => {
    const storedSessionId = localStorage.getItem("chatSessionId");
    if (storedSessionId) {
      dispatch(getChatHistory(storedSessionId) as any);
    } else if (isChatOpen && !session_id) {
      dispatch(initSession() as any);
    }
  }, [dispatch, isChatOpen, session_id]);

  useEffect(() => {
    if (session_id) {
      localStorage.setItem("chatSessionId", session_id);
    }
  }, [session_id]);

  useEffect(() => {
    dispatch(getCompanyName() as any);
  }, [dispatch]);

  // Event handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setInitialPosition({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    });
  };

  const handleChatMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).classList.contains("close-chat")) return;
    if ((e.target as HTMLElement).closest(".resize-handle")) return;
    setIsChatDragging(true);
    setChatDragStart({
      x: e.clientX - chatPosition.left,
      y: e.clientY - chatPosition.top,
    });
    e.preventDefault();
  };

  const updateTooltipDisplaySide = useCallback(
    (currentPos: { x: number; y: number }) => {
      if (floatButtonRef.current) {
        const buttonWidth = floatButtonRef.current.offsetWidth;
        const estimatedTooltipWidth = 100;
        const spaceRight = window.innerWidth - (currentPos.x + buttonWidth / 2);
        const spaceLeft = currentPos.x - buttonWidth / 2;

        if (
          spaceRight < estimatedTooltipWidth &&
          spaceLeft > estimatedTooltipWidth
        ) {
          setTooltipPosition("left");
        } else {
          setTooltipPosition("right");
        }
      }
    },
    []
  );

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      const newPosition = {
        x: e.clientX - initialPosition.x,
        y: e.clientY - initialPosition.y,
      };
      const boundedX = Math.max(
        buttonSize / 2,
        Math.min(newPosition.x, window.innerWidth - buttonSize / 2)
      );
      const boundedY = Math.max(
        buttonSize / 2,
        Math.min(newPosition.y, window.innerHeight - buttonSize / 2)
      );
      setPosition({ x: boundedX, y: boundedY });
      updateTooltipDisplaySide({ x: boundedX, y: boundedY });
    }
    if (isChatDragging) {
      let newLeft = e.clientX - chatDragStart.x;
      let newTop = e.clientY - chatDragStart.y;

      newLeft = Math.max(
        0,
        Math.min(newLeft, window.innerWidth - chatSize.width)
      );
      newTop = Math.max(
        0,
        Math.min(newTop, window.innerHeight - chatSize.height)
      );

      const newIconX = newLeft + chatSize.width - buttonSize / 2;
      const newIconY = newTop + chatSize.height - buttonSize / 2;
      setPosition({ x: newIconX, y: newIconY });
      updateTooltipDisplaySide({ x: newIconX, y: newIconY });
    }
    if (isResizing && activeHandle) {
      let newWidth = chatSize.width;
      let newHeight = chatSize.height;
      let currentChatLeft = chatPosition.left;
      let currentChatTop = chatPosition.top;

      const deltaX = e.clientX - resizeStart.x;
      const deltaY = e.clientY - resizeStart.y;

      if (activeHandle.includes("right")) {
        newWidth = Math.min(
          Math.max(chatSize.width + deltaX, minWidth),
          window.innerWidth - currentChatLeft
        );
      }
      if (activeHandle.includes("left")) {
        const potentialWidth = chatSize.width - deltaX;
        if (currentChatLeft + deltaX < 0) {
          newWidth = currentChatLeft + chatSize.width;
          currentChatLeft = 0;
        } else if (potentialWidth < minWidth) {
          currentChatLeft += potentialWidth - minWidth;
          newWidth = minWidth;
        } else {
          newWidth = potentialWidth;
          currentChatLeft += deltaX;
        }
      }
      if (activeHandle.includes("bottom")) {
        newHeight = Math.min(
          Math.max(chatSize.height + deltaY, minHeight),
          window.innerHeight - currentChatTop
        );
      }
      if (activeHandle.includes("top")) {
        const potentialHeight = chatSize.height - deltaY;
        if (currentChatTop + deltaY < 0) {
          newHeight = currentChatTop + chatSize.height;
          currentChatTop = 0;
        } else if (potentialHeight < minHeight) {
          currentChatTop += potentialHeight - minHeight;
          newHeight = minHeight;
        } else {
          newHeight = potentialHeight;
          currentChatTop += deltaY;
        }
      }

      setChatSize({ width: newWidth, height: newHeight });
      const newIconX = currentChatLeft + newWidth - buttonSize / 2;
      const newIconY = currentChatTop + newHeight - buttonSize / 2;
      setPosition({ x: newIconX, y: newIconY });
      updateTooltipDisplaySide({ x: newIconX, y: newIconY });
      setResizeStart({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setIsChatDragging(false);
    setIsResizing(false);
    setActiveHandle(null);
  };

  const handleResizeMouseDown = (handle: string) => (e: React.MouseEvent) => {
    setIsResizing(true);
    setActiveHandle(handle);
    setResizeStart({ x: e.clientX, y: e.clientY });
    e.preventDefault();
    e.stopPropagation();
  };

  const toggleChat = () => {
    if (isChatOpen) {
      const newIconX = chatPosition.left + chatSize.width - buttonSize / 2;
      const newIconY = chatPosition.top + chatSize.height - buttonSize / 2;
      setPosition({ x: newIconX, y: newIconY });
      updateTooltipDisplaySide({ x: newIconX, y: newIconY });
    } else {
      let newChatLeft = position.x - chatSize.width + buttonSize / 2;
      let newChatTop = position.y - chatSize.height + buttonSize / 2;

      newChatLeft = Math.max(
        0,
        Math.min(newChatLeft, window.innerWidth - chatSize.width)
      );
      newChatTop = Math.max(
        0,
        Math.min(newChatTop, window.innerHeight - chatSize.height)
      );

      const newIconX = newChatLeft + chatSize.width - buttonSize / 2;
      const newIconY = newChatTop + chatSize.height - buttonSize / 2;
      setPosition({ x: newIconX, y: newIconY });
      updateTooltipDisplaySide({ x: newIconX, y: newIconY });
    }
    setIsChatOpen(!isChatOpen);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && inputValue.trim()) {
      handleSendMessage();
    }
  };

  const handleSendMessage = () => {
    if (inputValue.trim()) {
      const userMessage = inputValue.trim();
      setInputValue("");
      dispatch(chat({ message: userMessage, session_id: session_id }) as any);
      if (isListening) {
        toggleListening();
      }
    }
  };

  if (companyLoading) {
    return <div>Loading company name...</div>;
  }

  if (companyError) {
    return <div>Error loading company name: {companyError}</div>;
  }

  return (
    <div
      className="app-container"
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      <div className="page-header">
        <h1>{company?.company_name}</h1>
      </div>
      {!isChatOpen && (
        <CustomFloatButton
          position={position}
          isDragging={isDragging}
          tooltipPosition={tooltipPosition}
          buttonSize={buttonSize}
          onMouseDown={handleMouseDown}
          onClick={toggleChat}
        />
      )}

      {isChatOpen && (
        <ChatInterface
          companyName={company?.company_name || "Chat Support"}
          messages={messages}
          isLoading={chatLoading}
          error={chatError}
          welcomeMessage={welcomeMessage}
          inputValue={inputValue}
          isListening={isListening}
          voiceError={voiceError}
          isSpeechSupported={isSpeechSupported}
          chatSize={chatSize}
          chatPosition={chatPosition}
          onClose={toggleChat}
          onChatMouseDown={handleChatMouseDown}
          onResizeMouseDown={handleResizeMouseDown}
          onInputChange={(e: any) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          onSendMessage={handleSendMessage}
          onToggleVoiceRecognition={toggleListening}
        />
      )}
    </div>
  );
};

export default App;
