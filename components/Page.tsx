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
      <div className="border-t border-gray-200 p-4">
        <div className="grid grid-cols-3">
          <div>
            <a href="https://bean.money">bean.money</a>
          </div>
        </div>
      </div>
    </>
  )
}

export default Page;