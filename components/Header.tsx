import React from "react";
import Navigation from "./Navigation";

const Header : React.FC<{
  children?: React.ReactNode;
}> = ({
  children
}) => {
  return (
    <div className="grid grid-cols-6 px-4 py-4 border-b border-slate-500 bg-[#daebf7]">
      <div className="col-span-2 flex items-center justify-start">
        <Navigation/>
      </div>
      <div className="col-span-2 flex items-center justify-center">
        <img src="/beanstalk.svg" className="h-6" /> 
      </div>
      <div className="col-span-2 flex items-center justify-end">
        ???
      </div>
    </div>
  )
};

export default Header;