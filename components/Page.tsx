import React from "react";
import Header from "./Header";
import Footer from "./Footer";

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
      <Footer />
    </div>
  )
}

export default Page;