import { NextPage } from "next";
import React from 'react';

import Page from "../components/Page";
import Chart from "../components/Chart"; 

const BarnPage: NextPage = () => {
  return (
    <Page title="Barn">
      <Chart
        title="Fertilizer Breakdown"
        name="fertilizer_breakdown"
        description="Outstanding Sprouts and Rinsable Sprouts over time; breakdown of Fertilizer by available (unpurchased), active (purchased + earning Bean mints), and used (purchased + fully repaid)."
      />
    </Page>
  );
}

export default BarnPage;