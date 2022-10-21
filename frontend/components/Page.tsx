import Head from "next/head";
import React from "react";
import Header from "./Header";
import Footer from "./Footer";

const Page : React.FC<{
  children: React.ReactNode;
  title?: string
}> = ({
  children,
  title
}) => {
  return (
    <>
      <Head>
        <title>{title ? `${title} | ` : ''}Beanstalk Analytics</title>
      </Head>
      <Header />
      <div className="page md:p-4 p-2">
        {children}
      </div>
      <Footer />
    </>
  )
}

export default Page;