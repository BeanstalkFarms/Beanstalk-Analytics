import React from "react";
import Header from "./Header";

const Page : React.FC<{
  children: React.ReactNode;
  rightHeader?: React.ReactNode;
}> = ({
  children,
  rightHeader
}) => {
  return (
    <div>
      <Header />
      {children}
    </div>
  )
}

export default Page;