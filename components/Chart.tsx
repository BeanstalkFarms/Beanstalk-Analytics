import React from 'react';
import { PropsWithChildren, useEffect, useReducer, useRef } from "react";
import { Popover } from '@headlessui/react' 
import { isNumber } from "lodash";

import useInterval from "../hooks/useInterval";
import VegaLiteChart, { WidthPaths } from "./VegaLiteChart"; 
import useSize from '@react-hook/size';


const RECOMPUTE_SPEC_AGE_SECONDS = 1; 
const SPEC_MAX_AGE_MINUTES = 15; 
const ARTIFICIAL_DELAY = false; 

const urlBucket = new URL(`${process.env.NEXT_PUBLIC_CDN}/${process.env.NEXT_PUBLIC_STORAGE_BUCKET_NAME}`);
const urlApi = new URL(`${process.env.NEXT_PUBLIC_API_URL}`); 

const urlBucketName = (name: string) => (
  // TODO: change this path to spec 
  new URL(`${urlBucket}/schemas/${name.toLowerCase()}.json?${Date.now()}`)
);
const urlApiName = (name: string) => (
  // TODO: change this path to spec 
  new URL(`${urlApi}schemas/refresh?data=${name.toLowerCase()}&${Date.now()}`)
);

type Spec = {
  // Name of the vega-lite spec. This is the identifier we use to request the spec from the server. 
  name: string 
  // Vega-lite spec object. null if we have not loaded in a spec from the server 
  spec: Object
  // The timestamp at which the spec was created. null if spec is null. 
  timestamp: SpecTimestamp
  // The age of this spec in minutes, recomputed each RECOMPUTE_SPEC_AGE_SECONDS seconds via a hook. 
  age_minutes: number
  // The amount of time in seconds that it took the server to internally generate this spec object 
  query_runtime_secs: number
  // The paths into the spec that must be modified for changing width dynamically 
  width_paths: WidthPaths
  // Custom stylesheet for rendered spec 
  css: string | null 
}

// Represents the most recent status of an api call 
// "pending" if there is an ongoing request 
// "success" if the most recent request succeeded. 
// "failure" if the most recent request failed. 
// null if we have not yet made a request 
type EndpointStatus = "pending" | "success" | "failure" | null; 

type ChartState = {
  // The spec object backing the chart. 
  spec: Spec | null 
  // Chart status 
  /*- "pre-loading": We are about to attempt to refresh and retrieve a new copy of spec. 
    - "loading": We are in the process of refresing and retrieving a new copy of spec. 
    - "stable": We are not actively preparing to make api calls or making api calls. 
  */
  status_chart: "pre-loading" | "loading" | "stable"
  // Status for most recent attempt to refresh spec.
  status_refresh_endpoint: EndpointStatus
  // Status for most recent attempt to load spec.
  status_storage_endpoint: EndpointStatus
  // Flag indicator for whether or not user can attempt to refresh spec. 
  // True when (chart stable && ((spec exists and is refreshable) || spec does not exist))
  // Always false when status_chart !== "stable"
  user_can_refresh: boolean 
  // Whether or not the vega-lite chart is actively resizing 
  is_resizing: boolean 
}; 

interface ChartInfoPopoverProps extends PropsWithChildren, ChartState {
  refreshChart: () => void 
}; 

interface ChartStatusBoxProps extends ChartState {}; 

class SpecTimestamp {

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

function is_past_age_threshold(timestamp: SpecTimestamp) {
  return timestamp.get_age_minutes() > SPEC_MAX_AGE_MINUTES
}

const ChartInfoPopover: React.FC<ChartInfoPopoverProps> = ({
  children, spec, status_storage_endpoint, user_can_refresh, status_refresh_endpoint, refreshChart
}) => {
  // props.children are the elements we want to serve as the "button" that opens the model. 
  // This group of elements will have a click listener attached by this component. 
  const { age_minutes, query_runtime_secs } = spec || {}; 

  // Compute text values for populating tooltip body 
  const empty = "n/a"; 
  const strQueryRuntime: string = isNumber(query_runtime_secs) ? `${Math.round(query_runtime_secs).toString()} seconds` : empty; 
  const strRefreshEndpointHealth: string = status_refresh_endpoint || empty; 
  const strStorageEndpointHealth: string = status_storage_endpoint || empty; 
  let strLastRefreshed: string; 
  if (isNumber(age_minutes)) {
    const ageMins = Math.floor(age_minutes); 
    const ageSecs = Math.round((age_minutes - ageMins) * 60);  
    strLastRefreshed = ageMins === 0 ? `${ageSecs} seconds` : `${ageMins} min ${ageSecs} secs`;
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
    `bg-gray-300 text-gray-900 
    disabled`;

  const fieldClassName = "col-span-2 font-medium text-slate-900"; 
  const valueClassName = "text-slate-700"; 
  // TODO: The popover button focus state is behaving really strangely. 
  //        Not super high priorty but would be nice to fix. @SiloChad any recs here? 
  return (
    <Popover className="relative">
      {({ open }) => (
        <>
          {/* ui-not-open:!outline-0 ui-open:!border-slate-200 */}
          <Popover.Button className={`mt-1 mr-2`}>
            {children}
          </Popover.Button>
          {/* Vega lite action button has zIndex of 1000 so this ensures that popup overlays it */}
          <Popover.Panel className="absolute right-2 top-12 z-10 w-96 z-[1005]">
          {({ close }) => (
            <div className="block border border-solid border-sky-500 rounded-md p-3 bg-slate-50">
              {/* Chart metadata */}
              <div className="grid gap-2 grid-cols-3 grid-rows-4">
                  <p className={fieldClassName}>refresh endpoint health:</p>
                  <p className={valueClassName}>{strRefreshEndpointHealth}</p>
                  <p className={fieldClassName}>storage endpoint health:</p>
                  <p className={valueClassName}>{strStorageEndpointHealth}</p>
                  <p className={fieldClassName}>query runtime:</p>
                  <p className={valueClassName}>{strQueryRuntime}</p>
                  <p className={fieldClassName}>chart age:</p>
                  <p className={valueClassName}>{strLastRefreshed}</p>
              </div>
              {/* Refresh button */}
              <div className="flex items-center justify-center">
                <button
                  type="button"
                  className={`
                  inline-flex justify-center 
                  rounded-md border border-transparent px-4 py-2 text-sm font-medium
                  ${buttonExtraClasses}`}
                  onClick={() => {
                    if (user_can_refresh) {
                      close(); 
                      refreshChart();
                    }
                  }}
                >
                  {buttonText}
                </button>
              </div>
            </div> 
          )}       
          </Popover.Panel>
        </>
      )}
    </Popover>
  )
}

const ChartStatusBox: React.FC<ChartStatusBoxProps> = ({
  spec, status_storage_endpoint, user_can_refresh, status_chart, is_resizing
}) => {

  let pingAnimation = false; 
  let pingAnimationClass = "animate-ping opacity-75"
  let statusString; 
  let statusIndicatorColorClass; 
  if (status_chart !== "stable") {
    // We are loading a new spec 
    pingAnimation = true; 
    statusString = "loading"; 
    statusIndicatorColorClass = "bg-blue-500"; 
  } else if (status_storage_endpoint === "failure" && spec) {
    // Chart is stable. Couldn't load new spec but old spec exists.
    statusString = "failed to refresh"; 
    statusIndicatorColorClass = "bg-orange-500"; 
  } else if (status_storage_endpoint === "failure" && !spec) {
    // Chart is stable. Couldn't load new spec and no old spec exists. 
    statusString = "failed"; 
    statusIndicatorColorClass = "bg-red-500"; 
  } else if (spec) {
    if (is_resizing) {
      pingAnimation = true; 
      statusString = "resizing"; 
      statusIndicatorColorClass = "bg-emerald-400";
    } else if (!user_can_refresh) {
      // Chart is stable. Spec is present and non-refreshable
      statusString = "up to date"; 
      statusIndicatorColorClass = "bg-green-500"; 
    } else { 
      // Chart is stable. Spec is present and refreshable
      statusString = "refreshable"; 
      statusIndicatorColorClass = "bg-yellow-500"; 
    }
  } else {
    throw new Error(`Invalid state. 
    spec: ${spec ? 'exists' : 'null'}
    user_can_refresh: ${user_can_refresh}
    status_storage_endpoint: ${status_storage_endpoint}
    status_chart: ${status_chart}`); 
  }

  return <div className="flex justify-center pl-2 pr-2 pt-1 pb-1">
    <p className="inline ml-1 mr-2 text-neutral-700">{statusString}</p>
    <div className="inline-flex items-center">
        {pingAnimation ? 
          <span className={`absolute rounded-full w-3.5 h-3.5 ${statusIndicatorColorClass} ${pingAnimationClass}`}></span>
          : null 
        }
        <span className={`relative rounded-full w-3.5 h-3.5 ${statusIndicatorColorClass}`}></span>
    </div>
  </div>;

}

function reducerAfterware(state: ChartState) {
  // Run after all reducer actions. 
  // If spec exists, we update it's age. 
  // Update user_can_refresh. 
  if (state.spec) {
    state.spec.age_minutes = state.spec.timestamp.get_age_minutes(); 
    state.user_can_refresh = (
      state.status_chart === "stable" && is_past_age_threshold(state.spec.timestamp)
    ); 
  } else {
    state.user_can_refresh = state.status_chart === "stable"; 
  }
  return state
}

const initialState: ChartState = {
  spec: null, 
  status_chart: "pre-loading", 
  status_refresh_endpoint: null, 
  status_storage_endpoint: null, 
  user_can_refresh: false, 
  is_resizing: false,
};


type Action =
 | { type: "start-loading" }
 | { type: "set-resizing", is_resizing: boolean }
 | { type: "replace-state", chart_state: ChartState }
 | { type: "toggle-user-can-refresh" }
 | { type: "update-spec-age" };


function reducer(state: ChartState, action: Action): ChartState {
  switch (action.type) {
    case "set-resizing": 
      return {...state, is_resizing: action.is_resizing}; 
    case "start-loading": 
      return reducerAfterware({
        spec: state.spec,
        status_chart: "loading", 
        status_refresh_endpoint: "pending", 
        status_storage_endpoint: "pending", 
        user_can_refresh: false, 
        is_resizing: state.is_resizing, 
      })
    case "replace-state":
      return reducerAfterware(action.chart_state);
    case "update-spec-age": 
      if (!state.spec) {
        throw new Error("Spec must exist for action update-spec-age");
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
  const ref_header = useRef(null); 
  const [header_width, header_height] = useSize(ref_header); 
  const { spec, status_chart, user_can_refresh, is_resizing } = state; 

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
        let new_spec: Spec | null; 
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
          const spec_timestamp = new SpecTimestamp(res.timestamp); 
          new_spec = {
            name, 
            spec: res.spec, 
            timestamp: spec_timestamp, 
            query_runtime_secs: parseFloat(res.run_time_seconds),
            age_minutes: spec_timestamp.get_age_minutes(), 
            width_paths: res.width_paths, 
            css: res.css, 
          }
        } catch (e) {
          console.error(e);
          new_status_storage_endpoint = "failure"; 
          new_spec = spec;
        }
        // Update state 
        dispatch({ 
          type: "replace-state",  
          chart_state: { 
            spec: new_spec, 
            status_chart: "stable", 
            status_refresh_endpoint: new_status_refresh_endpoint, 
            status_storage_endpoint: new_status_storage_endpoint, 
            user_can_refresh: false,
            // is_resizing: false, 
          }
        })
      })();
    }
  }, [spec, status_chart, name]);

  useInterval(() => {
    // Update spec age every RECOMPUTE_SPEC_AGE_SECONDS seconds when spec exists 
    // TODO: @Silo Chad, right now, I'm updating the chart age and refreshability every second 
    //      for all charts do you see any potential performance concerns here? 
    if (spec) dispatch({type: "update-spec-age"}); 
  }, RECOMPUTE_SPEC_AGE_SECONDS * 1000);

  const setResizing = (new_is_resizing: boolean) => {
    if (is_resizing !== new_is_resizing) dispatch({type: "set-resizing", is_resizing: new_is_resizing});
  }

  // Determine the chart body 
  let chartBody; 
  if (!spec) {
    const bodyText = ["pre-loading", "loading"].includes(status_chart) ? "Loading..." : "Error"; 
    chartBody = <div className="flex items-center justify-center" style={{ height }}>
      <p>{bodyText}</p>
    </div>;
  } else {
    // Regardless of chart state, if the spec exists, we show the chart.
    chartBody = <div className="flex items-center justify-center">
      <VegaLiteChart 
      className={undefined}
      name={name} 
      spec={spec.spec as Object} 
      css={spec.css}
      height={height}
      setResizing={setResizing}
      width_paths={spec.width_paths}
      target_width={header_width * .9}/>
    </div>;
  }

  const refreshChart = () => {
    if (user_can_refresh) dispatch({type: "start-loading"});
  }; 

  return <div className="overflow-hidden">
    {/* Chart Header */}
    <div ref={ref_header} className="grid gap-4 grid-cols-2 grid-rows-1">
      <div className="p-2"><h4 className="font-bold">{name}</h4></div>
      <div className="flex justify-end">
        <ChartInfoPopover {...state} refreshChart={refreshChart}>
          <ChartStatusBox {...state}/>
        </ChartInfoPopover>
      </div>
    </div>
    {/* Chart body */}
    {chartBody}
  </div>;

}

export default Chart;