import { NextPage } from "next";
import React from 'react';

import Module from "../components/Module";
import Page from "../components/Page";
import Chart from "../components/Chart"; 

const FarmersMarketPage: NextPage = () => {
  return (
    <Page title="Market">
      <div className="space-y-6">
        <div>
          <Chart
            title="Pod Market History"
            name="farmers_market_history"
            description="Interactive view of fills over time on the Pod Market. Use the brush at the bottom of the chart to select a time window of interest."
          />
        </div>
        <div>
          <Chart
            title="Pod Market Volume"
            name="farmers_market_volume"
            description="Total volume of the Pod Market, denominated in both Beans and Pods."
          />
        </div>
      </div>
    </Page>
  );
}

export default FarmersMarketPage;