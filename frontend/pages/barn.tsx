import { NextPage } from "next";
import React from 'react';

import Page from "../components/Page";
import Chart from "../components/Chart"; 

const Barn: NextPage = () => {
  return (
    <Page title="Barn">
      <div className="block md:grid md:grid-cols-6 gap-4 m-4">
        <div className="col-span-6 space-y-4">
          <Chart
            title="Fertilizer Breakdown"
            name="fertilizer_breakdown"
            description="Outstanding Sprouts and Rinsable Sprouts over time; breakdown of Fertilizer by available (unpurchased), active (purchased + earning Bean mints), and used (purchased + fully repaid)."
          />
        </div>
      </div>
    </Page>
  );
}

export default Barn;