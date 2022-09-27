import { NextPage } from "next";
import React from 'react';

import Module from "../components/Module";
import Page from "../components/Page";
import Chart from "../components/Chart"; 

if (!process.env.NEXT_PUBLIC_STORAGE_BUCKET_NAME) throw new Error('Environment: Missing bucket');
if (!process.env.NEXT_PUBLIC_CDN) throw new Error('Environment: Missing storage url'); 
if (!process.env.NEXT_PUBLIC_API_URL) throw new Error('Environment: Missing api url'); 

const Home: NextPage = () => {
  return (
    <Page>
      <div className="block md:grid md:grid-cols-6 gap-4 m-4">
        {/* <div className="col-span-6">
          <Module>
            <Chart name="BeanstalkCreditworthiness" />
          </Module>
        </div> */}
        {/* <div className="col-span-6">
          <Module>
            <Chart name="FarmersMarketHistory" />
          </Module>
        </div> */}
        <div className="col-span-6">
          <Module>
            <Chart name="FertilizerBreakdown" />
          </Module>
        </div>
        {/* <div className="col-span-6">
          <Module>
            <Chart name="FieldOverview" />
          </Module>
        </div> */}
        {/* <div className="col-span-6">
          <Module>
            <Chart name="noexist" />
          </Module>
        </div> */}
      </div>
    </Page>
  );
}

export default Home;