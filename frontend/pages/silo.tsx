import { NextPage } from "next";
import React from 'react';

import Page from "../components/Page";
import Chart from "../components/Chart"; 

const SiloPage: NextPage = () => {
  return (
    <Page title="Field">
      <div className="block md:grid md:grid-cols-6 gap-4 m-4">
        <div className="col-span-6">
          Silo analytics are under development - come back soon.
        </div>
      </div>
    </Page>
  );
}

export default SiloPage;