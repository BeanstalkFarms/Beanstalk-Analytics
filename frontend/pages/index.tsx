import { NextPage } from "next";
import React from 'react';

import Module from "../components/Module";
import Page from "../components/Page";
import Chart from "../components/Chart"; 
import Link from "next/link";

const WideLink : React.FC<React.PropsWithChildren<{ href: string }>> = ({ href, children }) => {
  return (
    <Link href={href}>
      <a className="flex flex-row justify-between max-w-full w-[400px] hover:no-underline hover:bg-gray-50 rounded-md px-4 py-2">
        <span>{children}</span>
        <span>&rarr;</span>
      </a>
    </Link>
  )
}

const Home: NextPage = () => {
  return (
    <Page>
      <div className="md:px-6 py-6">
        <h1 className="text-4xl font text-center">
          Explore Beanstalk protocol analytics
        </h1>
      </div>
      <div className="flex flex-col items-center justify-center">
        <div>
          <WideLink href="/credit-profile#credit-profile">
            Credit Profile
          </WideLink>
          <WideLink href="/liquidity#liquidity-curve-bean-3-crv">
            BEAN:3CRV Liquidity
          </WideLink>
          <WideLink href="/field#pod-line-breakdown">
            Pod Line Breakdown
          </WideLink>
          <WideLink href="/barn#fertilizer-breakdown">
            Fertilizer Breakdown
          </WideLink>
          <WideLink href="/market#pod-market-history">
            Pod Market History
          </WideLink>
          <WideLink href="/market#pod-market-volume">
            Pod Market Volume
          </WideLink>
        </div>
      </div>
    </Page>
  );
}

export default Home;