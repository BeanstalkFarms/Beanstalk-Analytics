import { NextPage } from "next";
import React, { useState } from 'react';
import { ethers } from 'ethers';

import Page from "../components/Page";
import Chart from "../components/Chart"; 
import Callout from "../components/Callout"; 
import { useContractData, ModuleSlot, CallsModule, parseSlot } from "../components/v1/CallsModule";

export const localeNumber = (decimals: number, maxFractionDigits?: number) => 
  (v: ethers.BigNumber) => (
    parseFloat(ethers.utils.formatUnits(v, decimals))
    .toLocaleString('en-us', { maximumFractionDigits: maxFractionDigits || 3 }
  ));
export const percentNumber = (decimals: number) =>
  (v: ethers.BigNumber) => `${(parseFloat(ethers.utils.formatUnits(v, decimals))*100).toFixed(4)}%`

const FieldPage: NextPage = () => {

  const slots: ModuleSlot[] = [
    ["Pods", "totalPods", localeNumber(6, 0)],
    // ["Soil", "totalSoil", localeNumber(6)],
    // ["Temperature", "yield", percentNumber(2)],
    // ["Harvested Pods", "totalHarvested", localeNumber(6)],
    // ["Harvestable Index", "harvestableIndex", localeNumber(6)]
  ]; 
  const raw = false; 
  const { data, status } = useContractData(slots, raw);   
  const pods = parseSlot(slots[0], data, 0); 


  return (
    <Page title="Field">
      <CallsModule
        title="Field"
        slots={slots}
        raw={false}
      />
      <div className="grid grid-cols-3">
        <Callout 
        title="Pods" 
        status={status} 
        type="quantity" 
        value={pods && pods.split(".")[0]} />
        <Callout 
        status={status} 
        type="info" 
        title="Two" 
        subtitle="SubTwo"/>
      </div>
      
      <Chart
        name="pod_line_breakdown"
        title="Pod Line Breakdown"
        description="Historical view of Pods minted in the Field."
      />
    </Page>
  );
}

export default FieldPage;