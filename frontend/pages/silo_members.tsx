import { NextPage } from "next";
import React from 'react';

import Page from "../components/Page";
import Chart from "../components/Chart"; 

const SiloMembersPage: NextPage = () => {
  return (
    <Page title="Pod Holders">
      <Chart
        title="Silo Members Breakdown"
        name="silo_member_breakdown"
        description="We bin active silo members by the deposited Bdv, and show the count of unique addresses and aggregate Bdv for each bin."
      />
      <Chart
        title="Silo Members Table"
        name="silo_member_table"
        description="Cumulative Bdv held by each silo member. Shift-click on a row to see the address on etherscan."
      />
    </Page>
  );
}

export default SiloMembersPage;