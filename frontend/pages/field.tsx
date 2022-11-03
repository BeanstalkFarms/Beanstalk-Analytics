import { NextPage } from "next";
import React from 'react';
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

  const i_pods = 0; 
  const i_soil = 1; 
  const i_temp = 2; 
  const i_pods_harvested = 3; 
  const i_harvestable_index = 4; 
  const slots: ModuleSlot[] = [
    ["Pods", "totalPods", localeNumber(6)],
    ["Soil", "totalSoil", localeNumber(6)],
    ["Temperature", "yield", percentNumber(2)],
    ["Harvested Pods", "totalHarvested", localeNumber(6)],
    ["Harvestable Index", "harvestableIndex", localeNumber(6)]
  ]; 
  const raw = false; 
  const { data, status } = useContractData(slots, raw);   

  const pods_harvestable = (
    data && data[i_pods_harvested] !== undefined && data[i_harvestable_index] !== undefined &&
    localeNumber(6)(data[i_harvestable_index].sub(data[i_pods_harvested])) 
  )
  const pods_unharvestable = (
    data && data[i_pods] !== undefined && data[i_harvestable_index] !== undefined &&
    localeNumber(6)(data[i_pods].sub(data[i_harvestable_index]))
  );
  const pods_harvested = (
    data && data[i_pods_harvested] !== undefined && 
    localeNumber(6)(data[i_pods_harvested])
  ); 

  return (
    <Page title="Field">
      {/* For debugging */}
      {/* <CallsModule
        title="Field"
        slots={slots}
        raw={false}
      /> */}
      <div className="grid grid-cols-3">
        <Callout 
        title="Pods Unharvestable" 
        status={status} 
        type="quantity" 
        value={pods_unharvestable && pods_unharvestable.split(".")[0]} />
        <Callout 
        title="Pods Harvested" 
        status={status} 
        type="quantity" 
        value={pods_harvested && pods_harvested.split(".")[0]} />
        <Callout 
        title="Pods Harvestable" 
        status={status} 
        type="quantity" 
        value={pods_harvestable && pods_harvestable.split(".")[0]} />
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