import { NextPage } from "next";
import React from 'react';

import Page from "../components/Page";
import Chart from "../components/Chart"; 

const SiloPage: NextPage = () => {
  return (
    <Page title="Silo">
      <Chart
        title="Silo Emissions"
        name="silo_emissions"
        description="Seignorage distributed to silo members."
      />
    </Page>
  );
}

export default SiloPage;