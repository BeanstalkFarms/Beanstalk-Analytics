import { NextPage } from "next";
import React from 'react';

import Page from "../components/Page";
import Chart from "../components/Chart"; 

const CreditProfile: NextPage = () => {
  return (
    <Page title="Credit Profile">
      <Chart
        title="Credit Profile"
        name="credit_profile"
        description="An overview of Beanstalk's credit history, including total debt and credit from Pods and Fertilizer."
      />
    </Page>
  );
}

export default CreditProfile;