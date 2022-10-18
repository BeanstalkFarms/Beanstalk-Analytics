import React from "react";

const Module : React.FC<{
  children?: React.ReactNode;
}> = ({
  children
}) => {
  return (
    <div className="border-slate-400 border">
      {children}
    </div>
  )
}

export default Module;