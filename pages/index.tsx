import { NextPage } from "next";
import React from 'react';
import { PropsWithChildren, useEffect, useState } from "react";
import { VegaLite } from 'react-vega';
import { Popover } from '@headlessui/react'
import Module from "../components/Module";
import Page from "../components/Page";
import useInterval from "../hooks/useInterval"; 
import { isNumber } from "lodash";


const RECOMPUTE_SCHEMA_AGE_SECONDS = 1; 


if (!process.env.NEXT_PUBLIC_STORAGE_BUCKET_NAME) throw new Error('Environment: Missing bucket');
if (!process.env.NEXT_PUBLIC_CDN) throw new Error('Environment: Missing storage url'); 
if (!process.env.NEXT_PUBLIC_API_URL) throw new Error('Environment: Missing api url'); 

const urlBucket = new URL(`${process.env.NEXT_PUBLIC_CDN}/${process.env.NEXT_PUBLIC_STORAGE_BUCKET_NAME}`);
const urlApi = new URL(`${process.env.NEXT_PUBLIC_API_URL}`); 

const urlBucketName = (name: string) => (
  new URL(`${urlBucket}/schemas/${name.toLowerCase()}.json?${Date.now()}`)
);
const urlApiName = (name: string) => (
  new URL(`${urlApi}schemas/refresh?data=${name.toLowerCase()}&${Date.now()}`)
);

type Schema = {
  // Name of the vega-lite schema. This is the identifier we use to request the schema from the server. 
  name: string 
  // Vega-lite schema object. null if we have not loaded in a schema from the server 
  schema: Object | null
  // The timestamp at which the schema was created in iso8061 datetime format. null if schema is null. 
  timestamp: string | null
  // The age of this schema in minutes, recomputed each RECOMPUTE_SCHEMA_AGE_SECONDS seconds via a hook. 
  age_minutes: number | null 
  // The amount of time in seconds that it took the server to internally generate this schema object 
  query_runtime_secs: number | null
}


// Represents the most recent status of an api call 
// "pending" if there is an ongoing request 
// "success" if the most recent request succeeded. 
// "failure" if the most recent request failed. 
// null if we have not yet made a request 
type EndpointStatus = "pending" | "success" | "failure" | null 


type ChartState = {
  // The schema object backing the chart. 
  schema: Schema | null 
  // Chart status 
  /*- "pre-loading": We are about to attempt to refresh and retrieve a new copy of schema. 
    - "loading": We are in the process of refresing and retrieving a new copy of schema. 
    - "stable": We are not actively preparing to make api calls or making api calls. 
  */
  status_chart: "pre-loading" | "loading" | "stable"
  // Status for most recent attempt to refresh schema.
  status_refresh_endpoint: EndpointStatus
  // Status for most recent attempt to load schema.
  status_storage_endpoint: EndpointStatus
  // Flag indicator for whether or not user can attempt to refresh schema. 
  user_can_refresh: boolean 
}; 

interface ChartInfoPopoverProps extends PropsWithChildren, ChartState {
  refreshChart: () => void 
}; 

const computeAgeMinutes = (iso_timestamp: string) => {
  const msecs_now = Date.now(); 
  const msecs_tstamp = new Date(iso_timestamp).valueOf(); 
  const age_minutes = (msecs_now - msecs_tstamp) / 1000 / 60; 
  if (age_minutes <= 0) {
    throw new Error("Age should never be negative"); 
  }
  return age_minutes; 
}

const canUserRefresh = (age_minutes: number) : boolean => {
  return age_minutes < 45
}

const ChartInfoPopover: React.FC<ChartInfoPopoverProps> = ({
  children, status_storage_endpoint, user_can_refresh, query_runtime_secs, age_minutes, status_refresh_endpoint, refreshChart
}) => {
  // props.children are the elements we want to serve as the "button" that opens the model. 
  // This group of elements will have a click listener attached by this component. 
  const isButtonActive = () => (
    status_storage_endpoint === 'failed' || (status_storage_endpoint === 'loaded' && user_can_refresh === 'refreshable')
  )
  const buttonActive = isButtonActive(); 

  // Compute text values for populating tooltip body 
  const strQueryRuntime = isNumber(query_runtime_secs) ? `${Math.round(query_runtime_secs).toString()} seconds` : 'n/a'; 
  const strEndpointHealth = status_refresh_endpoint; 
  let strLastRefreshed = null; 
  if (isNumber(age_minutes)) {
    const ageMins = Math.floor(age_minutes); 
    const ageSecs = Math.round((age_minutes - ageMins) * 60);  
    strLastRefreshed = ageMins === 0 ? `${ageSecs} seconds ago` : `${ageMins} minutes ${ageSecs} seconds ago`;
  } else {
    strLastRefreshed = 'n/a'; 
  }

  // Compute button visual state 
  const buttonText = status_storage_endpoint === "failed" || status_storage_endpoint === "loading" ? "Retry" : "Refresh"; 
  const buttonExtraClasses = buttonActive ? 
    `bg-blue-100 text-blue-900 
    hover:bg-blue-200 
    focus:outline-none 
    focus-visible:ring-2 
    focus-visible:ring-blue-500 
    focus-visible:ring-offset-2` 
    : 
    `bg-gray-100 text-gray-900 
    disabled`;

  return (
    <Popover className="relative">
      <Popover.Button>{children}</Popover.Button>
      {/* Vega lite action button has zIndex of 1000 so this ensures that popup overlays it */}
      <Popover.Panel className="absolute right-0 top-7 z-10 w-72" style={{"zIndex": 1001}}>
        <div className="block border border-solid border-sky-500 rounded-md p-3 bg-slate-50">
          {/* Chart metadata */}
          <div className="grid gap-2 grid-cols-2 grid-rows-3">
              <p>endpoint health:</p><p>{strEndpointHealth}</p>
              <p>query runtime:</p><p>{strQueryRuntime}</p>
              <p>last refreshed:</p><p>{strLastRefreshed}</p>
          </div>
          {/* Refresh button */}
          <div className="flex items-center justify-center">
            <button
              type="button"
              className={`
              inline-flex justify-center 
              rounded-md border border-transparent px-4 py-2 text-sm font-medium
              ${buttonExtraClasses}`}
              onClick={() => isButtonActive() && refreshChart()}
            >
              {buttonText}
            </button>
          </div>
        
      </div>
      </Popover.Panel>
    </Popover>
  )
}

const Chart : React.FC<{ name: string; height?: number; }> = ({ name, height = 300 }) => {

  const [chartState, setChartState] = useState<ChartState>({
    schema: {
      name: name, 
      schema: null,
      timestamp: null,
      age_minutes: null, 
      query_runtime_secs: null
    }, 
    status_chart: "pre-loading", 
    status_refresh_endpoint: null, 
    status_storage_endpoint: null, 
    user_can_refresh: false, // user can't refresh because we always refresh during initialization 
  }); 

  useEffect(() => {
    if (chartState.status_chart === 'pre-loading') {
      setChartState({
        ...chartState, 
        status_chart: "loading", 
        status_refresh_endpoint: "pending", 
        status_storage_endpoint: "pending", 
      }); 
    } else if (chartState.status_storage_endpoint === 'loading') {
      (async () => {
        // Including the Authorization header forces the requests to do CORS preflight 
        const headers = {"Authorization": "Bearer dummy_force_cors_preflight"}
        let newChartState: ChartState = {...chartState}; 
        try {
          const res = await fetch(urlApiName(name).toString(), {"headers": headers })
            .then(r => r.json());
          const { status } = res[name.toLowerCase()]; 
          if (status !== 'recomputed' && status !== 'use_cached') {
            throw new Error(`Unrecognized status returned from cloud function: ${status}`)
          }
          newChartState.status_refresh_endpoint = "healthy"; 
        } catch (e) {
          console.error(e);
          newChartState.status_refresh_endpoint = "unhealthy"; 
        }
        try {
          const { schema, timestamp, run_time_seconds } = await fetch(urlBucketName(name).toString(), {"headers": headers })
            .then(r => r.json()); 
          const age_minutes = computeAgeMinutes(timestamp); 
          newChartState = {
            ...newChartState, 
            schema: {
              name, 
              schema, 
              timestamp, 
              query_runtime_secs: parseFloat(run_time_seconds),
              age_minutes
            }, 
            status_storage_endpoint: "loaded",
            user_can_refresh: canUserRefresh(age_minutes), 
          };
        } catch (e) {
          console.error(e);
          newChartState.status_storage_endpoint = "failed";
          if (newChartState.schema && newChartState.schema.timestamp) {
            // If we failed to load a new schema, and an old schema exists, we update its age. 
            const age_minutes = computeAgeMinutes(newChartState.schema.timestamp)
            newChartState = {
              ...newChartState, 
              schema: {...newChartState.schema, age_minutes}, 
              user_can_refresh: canUserRefresh(age_minutes),
            };
          } else {
            // If we failed to load a new schema, and no schema exists, user can refresh. 
            newChartState.user_can_refresh = true;
          }
        }
        setChartState(newChartState);
      })()
    }
  }, [chartState.status_chart]);

  useInterval(() => {
    // Updates schema age and chart refreshability status on a time interval 
    // Only performs these updates when a schema is present, so note that 
    // user_can_refresh will only be updated when there is a backing schema. 
    if (chartState.schema && chartState.schema.timestamp) {
      // TODO: @Silo Chad, right now, I'm updating the chart age every second for all charts 
      //      do you see any potential performance concerns here? I have no idea what i'm doing tbh. 
      const age_minutes = computeAgeMinutes(chartState.schema.timestamp); 
      setChartState({
        ...chartState, 
        schema: {...chartState.schema, age_minutes}, 
        user_can_refresh: canUserRefresh(age_minutes)
      });
    }
  }, RECOMPUTE_SCHEMA_AGE_SECONDS * 1000);

  // Passed to tooltip so it can trigger chart updates 
  const handleRefreshChart = () => setDoUpdate(true); 

  // Chart body content 
  const chartContent = (
    chartState.status_storage_endpoint === "loading" ? (
      <div className="flex items-center justify-center" style={{ height }}>
        Loading...
      </div>
    ) : (
      <div>
        <div className="grid gap-4 grid-cols-2 grid-rows-1">
          <div className="p-2"><h4 className="font-bold">{name}</h4></div>
          <div className="flex justify-end p-2">
            <ChartInfoPopover {...chartState} refreshChart={handleRefreshChart}>
              <h6 className="font-bold inline">status:</h6>
              <p className="inline ml-1 mr-2">{chartState.user_can_refresh ? chartState.user_can_refresh : "failed"}</p>
              <div className="inline-flex items-center">
                <div className={`rounded-full w-3.5 h-3.5
                ${chartState.user_can_refresh === "updated" ? "bg-green-500" : 
                  chartState.user_can_refresh === "refreshable" ? "bg-yellow-500" : 
                  chartState.user_can_refresh === null ? "bg-red-500" : ''}`
                }></div>
              </div>
            </ChartInfoPopover>
          </div>
        </div>
        {chartState.status_storage_endpoint === "failed" ? null : (
          <div className="flex items-center justify-center">
            <VegaLite spec={chartState.schema as Object} height={height} />
          </div>
        )}
      </div>
    )
  ); 

  // const chartContent = (
  //   chartState.status_storage_endpoint === "loading" ? (
  //     <div className="flex items-center justify-center" style={{ height }}>
  //       Loading...
  //     </div>
  //   ) : 
  //   chartState.status_storage_endpoint === "loaded" ? (
  //     <div>
  //       <div className="grid gap-4 grid-cols-2 grid-rows-1">
  //         <div className="p-2"><h4 className="font-bold">{name}</h4></div>
  //         <div className="flex justify-end p-2">
  //           <ChartInfoPopover {...chartState}>
  //             <h6 className="font-bold inline">status:</h6>
  //             <p className="inline ml-1 mr-2">{chartState.user_can_refresh}</p>
  //             <div className="inline-flex items-center">
  //               <div className={`rounded-full w-3.5 h-3.5
  //               ${chartState.user_can_refresh === "updated" ? "bg-green-500" : 
  //                 chartState.user_can_refresh === "refreshable" ? "bg-yellow-500" : 
  //                 chartState.user_can_refresh === "failed" ? "bg-red-500" : ''}`
  //               }></div>
  //             </div>
  //           </ChartInfoPopover>
  //         </div>
  //       </div>
  //       <div className="flex items-center justify-center">
  //         <VegaLite spec={chartState.schema as Object} height={height} />
  //       </div>
  //     </div>
  //   ) : (
  //     <div className="flex items-center justify-center" style={{ height }}>
  //       Something went wrong while loading chart {name}.
  //     </div>
  //   )
  // );

  return chartContent; 

}

const Home: NextPage = () => {
  return (
    <Page>
      <div className="block md:grid md:grid-cols-6 gap-4 m-4">
        {/* <div className="col-span-6">
          <Module>
            <Chart name="BeanstalkCreditworthiness" />
          </Module>
        </div>
        <div className="col-span-6">
          <Module>
            <Chart name="FarmersMarketHistory" />
          </Module>
        </div>
        <div className="col-span-6">
          <Module>
            <Chart name="FertilizerBreakdown" />
          </Module>
        </div> */}
        <div className="col-span-6">
          <Module>
            <Chart name="FieldOverview" />
          </Module>
        </div>
        <div className="col-span-6">
          <Module>
            <Chart name="noexist" />
          </Module>
        </div>
      </div>
    </Page>
  );
}

export default Home;