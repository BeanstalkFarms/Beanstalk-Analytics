import { NextPage } from "next";
import React from 'react';

import Page from "../components/Page";
import Chart from "../components/Chart"; 

const SiloPage: NextPage = () => {
  return (
    <Page title="Silo">
      <div className="grid grid-cols-6">
        <div className="col-span-2 p-2">
          <Chart
            title="Silo Emissions"
            name="silo_emissions"
            description="Seignorage distributed to silo members."
          />
        </div>
        <div className="col-span-4 p-2">
          <Chart
            title="Seeds, Stalk, Deposited Bdv"
            name="seeds_stalk"
            description="Seeds, stalk, deposited bdv, and some ratios between these quantities."
          />
        </div>
      </div>
      <Chart
        title="Silo Asset Breakdown"
        name="silo_asset_breakdown"
        description="Breakdown of all deposited Bdv into various asset types."
      />
    </Page>
  );
}

export default SiloPage;