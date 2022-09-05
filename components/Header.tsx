import React from "react";

const Header : React.FC<{
  children?: React.ReactNode;
}> = ({
  children
}) => {
  return (
    <div className="grid grid-flow-col px-4 py-4 border-b border-gray-200">
      <div className="col-span-2 flex items-center justify-start">
        Links
      </div>
      <div className="col-span-2 flex items-center justify-center">
        <img src="/beanstalk.svg" className="h-6" /> 
      </div>
      <div className="col-span-2 flex items-center justify-end">
        More links
      </div>
    </div>
  )
}

export default Header;