import { NextPage } from "next";
import React from 'react';

import Page from "../components/Page";
import Chart from "../components/Chart"; 

const PodHoldersPage: NextPage = () => {
  return (
    <Page title="Pod Holders">
      <Chart
        title="Pod Holders Breakdown"
        name="pod_holder_breakdown"
        description="We bin active pod holders by the number of pods held, and show the count of unique addresses and aggregate pods for each bin."
      />
      <Chart
        title="Pod Holders Table"
        name="pod_holder_table"
        description="Cumulative pods held by each pod holder. Shift-click on a row to see the address on etherscan."
      />
    </Page>
  );
}

export default PodHoldersPage;