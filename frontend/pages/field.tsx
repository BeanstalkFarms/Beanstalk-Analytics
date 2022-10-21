import { NextPage } from "next";
import React from 'react';

import Page from "../components/Page";
import Chart from "../components/Chart"; 

const FieldPage: NextPage = () => {
  return (
    <Page title="Field">
      <Chart
        name="pod_line_breakdown"
        title="Pod Line Breakdown"
        description="Historical view of Pods minted in the Field."
      />
    </Page>
  );
}

export default FieldPage;