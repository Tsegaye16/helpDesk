import React from "react";
import { FloatButton } from "antd";
import { MessageOutlined } from "@ant-design/icons";

interface FloatButtonProps {
  position: { x: number; y: number };
  isDragging: boolean;
  tooltipPosition: "left" | "right";
  buttonSize: number;
  onMouseDown: (e: React.MouseEvent) => void;
  onClick: () => void;
}

const CustomFloatButton: React.FC<FloatButtonProps> = ({
  position,
  isDragging,
  tooltipPosition,
  buttonSize,
  onMouseDown,
  onClick,
}) => {
  return (
    <FloatButton
      icon={<MessageOutlined />}
      type="primary"
      tooltip={{ title: "Open Chat", placement: tooltipPosition }}
      style={{
        position: "absolute",
        left: `${position.x}px`,
        top: `${position.y}px`,
        width: `${buttonSize}px`,
        height: `${buttonSize}px`,
        cursor: isDragging ? "grabbing" : "grab",
      }}
      onMouseDown={onMouseDown}
      onClick={onClick}
    />
  );
};

export default CustomFloatButton;
