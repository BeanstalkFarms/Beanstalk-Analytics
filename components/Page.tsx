import Head from "next/head";
import React from "react";
import Header from "./Header";

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
      <div className="page">
        {children}
      </div>
    </>
  )
}

export default Page;