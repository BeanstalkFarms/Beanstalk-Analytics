import { NextPage } from "next";
import React from 'react';

import Module from "../components/Module";
import Page from "../components/Page";
import Chart from "../components/Chart"; 

const Home: NextPage = () => {
  return (
    <Page>
      <div className="block md:grid md:grid-cols-6 gap-4">
        <div className="col-span-6 p-4">
          <div className="md:p-12">
            <h1 className="text-4xl font text-center">
              Explore Beanstalk protocol analytics
            </h1>
          </div>

        </div>
      </div>
    </Page>
  );
}

export default Home;