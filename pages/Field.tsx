import { NextPage } from "next";
import React from 'react';

import Page from "../components/Page";
import Chart from "../components/Chart"; 

const FieldPage: NextPage = () => {
  return (
    <Page title="Field">
      <div className="block md:grid md:grid-cols-6 gap-4 m-4">
        <div className="col-span-6">
          <Chart
            name="pod_line_breakdown"
            title="Pod Line Breakdown"
            description="Historical view of Pods minted in the Field."
          />
        </div>
      </div>
    </Page>
  );
}

export default FieldPage;