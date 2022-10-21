import { NextPage } from "next";
import React from 'react';

import Page from "../components/Page";
import Chart from "../components/Chart"; 

const LiquidityPage: NextPage = () => {
  return (
    <Page title="Market">
      <div className="block md:grid md:grid-cols-6 gap-4 m-4">
        <div className="col-span-6">
          <Chart
            title="Liquidity Curve Bean:3CRV"
            name="liquidity_curve_bean_3crv"
            description="Data describing the state of the Curve Bean:3Crv Pool. Data shown is average daily data across all metrics."
          />
        </div>
      </div>
    </Page>
  );
}

export default LiquidityPage;