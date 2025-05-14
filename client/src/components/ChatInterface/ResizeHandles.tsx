import React from "react";

interface ResizeHandlesProps {
  onResizeMouseDown: (handle: string) => (e: React.MouseEvent) => void;
}

const ResizeHandles: React.FC<ResizeHandlesProps> = ({ onResizeMouseDown }) => {
  return (
    <>
      <div
        className="resize-handle left"
        onMouseDown={onResizeMouseDown("left")}
      />
      <div
        className="resize-handle right"
        onMouseDown={onResizeMouseDown("right")}
      />
      <div
        className="resize-handle top"
        onMouseDown={onResizeMouseDown("top")}
      />
      <div
        className="resize-handle bottom"
        onMouseDown={onResizeMouseDown("bottom")}
      />
      <div
        className="resize-handle top-left"
        onMouseDown={onResizeMouseDown("top-left")}
      />
      <div
        className="resize-handle top-right"
        onMouseDown={onResizeMouseDown("top-right")}
      />
      <div
        className="resize-handle bottom-left"
        onMouseDown={onResizeMouseDown("bottom-left")}
      />
      <div
        className="resize-handle bottom-right"
        onMouseDown={onResizeMouseDown("bottom-right")}
      />
    </>
  );
};

export default ResizeHandles;
