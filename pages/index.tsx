import { NextPage } from "next";
import React from 'react';
import { PropsWithChildren, useEffect, useReducer, useState } from "react";
import { VegaLite } from 'react-vega';
import { Popover } from '@headlessui/react'
import Module from "../components/Module";
import Page from "../components/Page";
import useInterval from "../hooks/useInterval"; 
import { delay, isNumber } from "lodash";


const RECOMPUTE_SCHEMA_AGE_SECONDS = 1; 
const SCHEMA_MAX_AGE_MINUTES = .1; 
const ARTIFICIAL_DELAY = true; 


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
  schema: Object
  // The timestamp at which the schema was created. null if schema is null. 
  timestamp: SchemaTimestamp
  // The age of this schema in minutes, recomputed each RECOMPUTE_SCHEMA_AGE_SECONDS seconds via a hook. 
  age_minutes: number
  // The amount of time in seconds that it took the server to internally generate this schema object 
  query_runtime_secs: number
}

// Represents the most recent status of an api call 
// "pending" if there is an ongoing request 
// "success" if the most recent request succeeded. 
// "failure" if the most recent request failed. 
// null if we have not yet made a request 
type EndpointStatus = "pending" | "success" | "failure" | null; 

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
  // True when (chart stable && ((schema exists and is refreshable) || schema does not exist))
  // Always false when status_chart !== "stable"
  user_can_refresh: boolean 
}; 

interface ChartInfoPopoverProps extends PropsWithChildren, ChartState {
  refreshChart: () => void 
}; 

class SchemaTimestamp {

  iso_timestamp: string;
  date: Date; 

  constructor(iso_timestamp: string) {
    this.iso_timestamp = iso_timestamp; 
    this.date = new Date(iso_timestamp); 
  }

  get_age_minutes() {
    const msecs_now = Date.now(); 
    const msecs_tstamp = this.date.valueOf(); 
    const age_minutes = (msecs_now - msecs_tstamp) / 1000 / 60; 
    if (age_minutes <= 0) {
      throw new Error("Age should never be negative"); 
    }
    return age_minutes; 
  }

};

function is_past_age_threshold(timestamp: SchemaTimestamp) {
  return timestamp.get_age_minutes() > SCHEMA_MAX_AGE_MINUTES
}

const ChartInfoPopover: React.FC<ChartInfoPopoverProps> = ({
  children, schema, status_storage_endpoint, user_can_refresh, status_refresh_endpoint, refreshChart
}) => {
  // props.children are the elements we want to serve as the "button" that opens the model. 
  // This group of elements will have a click listener attached by this component. 
  const { age_minutes, query_runtime_secs } = schema || {}; 

  // Compute text values for populating tooltip body 
  const empty = "n/a"; 
  const strQueryRuntime: string = isNumber(query_runtime_secs) ? `${Math.round(query_runtime_secs).toString()} seconds` : empty; 
  const strRefreshEndpointHealth: string = status_refresh_endpoint || empty; 
  const strStorageEndpointHealth: string = status_storage_endpoint || empty; 
  let strLastRefreshed: string; 
  if (isNumber(age_minutes)) {
    const ageMins = Math.floor(age_minutes); 
    const ageSecs = Math.round((age_minutes - ageMins) * 60);  
    strLastRefreshed = ageMins === 0 ? `${ageSecs} seconds` : `${ageMins} minutes ${ageSecs} seconds`;
  } else {
    strLastRefreshed = empty; 
  }

  // Compute button visual state 
  const buttonText: string = (
    !user_can_refresh ? "Disabled" : 
    status_storage_endpoint === "success" ? "Refresh" : "Retry"
  ); 
  const buttonExtraClasses: string = user_can_refresh ? 
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
      <Popover.Panel className="absolute right-0 top-7 z-10 w-96" style={{"zIndex": 1001}}>
        <div className="block border border-solid border-sky-500 rounded-md p-3 bg-slate-50">
          {/* Chart metadata */}
          <div className="grid gap-2 grid-cols-2 grid-rows-4">
              <p>refresh endpoint health:</p><p>{strRefreshEndpointHealth}</p>
              <p>storage endpoint health:</p><p>{strStorageEndpointHealth}</p>
              <p>query runtime:</p><p>{strQueryRuntime}</p>
              <p>chart age:</p><p>{strLastRefreshed}</p>
          </div>
          {/* Refresh button */}
          <div className="flex items-center justify-center">
            <button
              type="button"
              className={`
              inline-flex justify-center 
              rounded-md border border-transparent px-4 py-2 text-sm font-medium
              ${buttonExtraClasses}`}
              onClick={refreshChart}
            >
              {buttonText}
            </button>
          </div>
        
      </div>
      </Popover.Panel>
    </Popover>
  )
}

function reducerAfterware(state: ChartState) {
  // Run after all reducer actions. 
  // If schema exists, we update it's age. 
  // Update user_can_refresh. 
  if (state.schema) {
    state.schema.age_minutes = state.schema.timestamp.get_age_minutes(); 
    state.user_can_refresh = (
      state.status_chart === "stable" && is_past_age_threshold(state.schema.timestamp)
    ); 
  } else {
    state.user_can_refresh = state.status_chart === "stable"; 
  }
  return state
}

const initialState: ChartState = {
  schema: null, 
  status_chart: "pre-loading", 
  status_refresh_endpoint: null, 
  status_storage_endpoint: null, 
  user_can_refresh: false, 
};


type Action =
 | { type: "start-loading" }
 | { type: "replace-state", chart_state: ChartState }
 | { type: "toggle-user-can-refresh" }
 | { type: "update-schema-age" };


function reducer(state: ChartState, action: Action): ChartState {
  switch (action.type) {
    case "start-loading": 
      return reducerAfterware({
        schema: state.schema,
        status_chart: "loading", 
        status_refresh_endpoint: "pending", 
        status_storage_endpoint: "pending", 
        user_can_refresh: false, 
      })
    case "replace-state":
      return reducerAfterware(action.chart_state);
    case "update-schema-age": 
      if (!state.schema) {
        throw new Error("Schema must exist for action update-schema-age");
      }
      return reducerAfterware({...state}); 
    case "toggle-user-can-refresh": 
      return reducerAfterware({...state, user_can_refresh: !state.user_can_refresh});
    default:
      throw new Error("Invalid action");
  }
}

const Chart : React.FC<{ name: string; height?: number; }> = ({ name, height = 300 }) => {

  const [state, dispatch] = useReducer(reducer, initialState); 
  const { schema, status_chart, status_storage_endpoint, user_can_refresh } = state; 

  useEffect(() => {
    if (status_chart === 'pre-loading') {
      dispatch({type: "start-loading"});
    } else if (status_chart === 'loading') {
      (async () => {
        if (ARTIFICIAL_DELAY) {
          // for debugging purposes 
          const delay = (secs: number) => new Promise(res => setTimeout(res, secs * 1000));
          await delay(3); 
        }
        // Including the Authorization header forces the requests to do CORS preflight 
        const headers = {"Authorization": "Bearer dummy_force_cors_preflight"}
        let new_schema: Schema | null; 
        let new_status_refresh_endpoint: EndpointStatus;
        let new_status_storage_endpoint: EndpointStatus; 
        // 1. Make a call to the refresh endpoint 
        try {
          const res = await fetch(urlApiName(name).toString(), {"headers": headers })
            .then(r => r.json());
          const { status } = res[name.toLowerCase()]; 
          if (status !== 'recomputed' && status !== 'use_cached') {
            throw new Error(`Unrecognized status returned from cloud function: ${status}`)
          }
          new_status_refresh_endpoint = "success"; 
        } catch (e) {
          console.error(e);
          new_status_refresh_endpoint = "failure"; 
        }
        // 2. Make a call to the storage endpoint 
        try {
          const res = await fetch(urlBucketName(name).toString(), {"headers": headers })
            .then(r => r.json()); 
          new_status_storage_endpoint = "success"; 
          const schema_timestamp = new SchemaTimestamp(res.timestamp); 
          new_schema = {
            name, 
            schema: res.schema, 
            timestamp: schema_timestamp, 
            query_runtime_secs: parseFloat(res.run_time_seconds),
            age_minutes: schema_timestamp.get_age_minutes(), 
          }
        } catch (e) {
          console.error(e);
          new_status_storage_endpoint = "failure"; 
          new_schema = schema;
        }
        // Update state 
        dispatch({ 
          type: "replace-state",  
          chart_state: { 
            schema: new_schema, 
            status_chart: "stable", 
            status_refresh_endpoint: new_status_refresh_endpoint, 
            status_storage_endpoint: new_status_storage_endpoint, 
            user_can_refresh: false,
          }
        })
      })();
    }
  }, [schema, status_chart, name]);

  useInterval(() => {
    // Update schema age every RECOMPUTE_SCHEMA_AGE_SECONDS seconds when schema exists 
    // TODO: @Silo Chad, right now, I'm updating the chart age and refreshability every second 
    //      for all charts do you see any potential performance concerns here? 
    if (schema) dispatch({type: "update-schema-age"}); 
  }, RECOMPUTE_SCHEMA_AGE_SECONDS * 1000);

  let chartBody; 
  if (status_chart !== "stable") {
    chartBody = <div className="flex items-center justify-center" style={{ height }}>
      Loading...
    </div>;
  } else {
    chartBody = !schema ? null : (
      <div className="flex items-center justify-center">
        <VegaLite spec={schema.schema as Object} height={height} />
      </div>
    ); 
  }

  // Passed to tooltip so it can trigger chart updates 
  const handleRefreshChart = () => {
    if (user_can_refresh) dispatch({type: "start-loading"});
  }; 

  let pingAnimation = false; 
  let pingAnimationClass = "animate-ping opacity-75"
  let statusString; 
  let statusIndicatorColorClass; 
  if (status_chart !== "stable") {
    // If chart is not stable (i.e. loading), we show blue pinging indicator
    pingAnimation = true; 
    statusString = "loading"; 
    statusIndicatorColorClass = "bg-blue-500"; 
  } else if (status_storage_endpoint === "failure" || !schema) {
    /* If chart is stable but 
    1. Last storage request failed 
    2. Schema is null 
    We show red. Note that this does not necessarily mean that schema 
    is null. If the  storage call succeeded previously but failed on our 
    last attempt then the chart will show data but the indicator will be red. */
    statusString = !schema ? "failure" : "failure to reload"; 
    statusIndicatorColorClass = "bg-red-500"; 
  } else if (!user_can_refresh) {
    // Schema is present and non-refreshable, we show green
    statusString = "up to date"; 
    statusIndicatorColorClass = "bg-green-500"; 
  } else {
    // Schema is present and refreshable, we show yellow
    statusString = "refreshable"; 
    statusIndicatorColorClass = "bg-yellow-500"; 
  }

  return <div>
    {/* Chart Header */}
    <div className="grid gap-4 grid-cols-2 grid-rows-1">
      <div className="p-2"><h4 className="font-bold">{name}</h4></div>
      <div className="flex justify-end p-2">
        <ChartInfoPopover {...state} refreshChart={handleRefreshChart}>
          <div className="flex justify-center">
            <h6 className="font-bold inline">status:</h6>
            <p className="inline ml-1 mr-2">{statusString}</p>
            <div className="inline-flex items-center">
                {pingAnimation ? 
                  <span className={`absolute rounded-full w-3.5 h-3.5 ${statusIndicatorColorClass} ${pingAnimationClass}`}></span>
                  : null 
                }
                <span className={`relative rounded-full w-3.5 h-3.5 ${statusIndicatorColorClass}`}></span>
            </div>
          </div>
        </ChartInfoPopover>
      </div>
    </div>
    {chartBody}
  </div>;

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