import React from "react";

const Module : React.FC<{
  children?: React.ReactNode;
}> = ({
  children
}) => {
  return (
    <div className="border-gray-200 border">
      {children}
    </div>
  )
}

export default Module;