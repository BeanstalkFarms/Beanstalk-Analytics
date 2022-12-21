import { NextPage } from "next";
import React from 'react';

import Page from "../components/Page";
import Chart from "../components/Chart"; 

const OverviewPage: NextPage = () => {
  return (
    <Page title="Overview">
      <Chart
        title="Credit Profile"
        name="credit_profile"
        description="An overview of Beanstalk's credit history, including total debt and credit from Pods and Fertilizer."
      />
    </Page>
  );
}

export default OverviewPage;