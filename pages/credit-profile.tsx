import { NextPage } from "next";
import React from 'react';

import Page from "../components/Page";
import Chart from "../components/Chart"; 

const CreditProfile: NextPage = () => {
  return (
    <Page title="Credit Profile">
      <div className="block md:grid md:grid-cols-6 gap-4 m-4">
        <div className="col-span-6">
            <Chart
              title="Credit Profile"
              name="credit_profile"
              description="An overview of Beanstalk's credit history, including total debt and credit from Pods and Fertilizer."
            />
        </div>
      </div>
    </Page>
  );
}

export default CreditProfile;