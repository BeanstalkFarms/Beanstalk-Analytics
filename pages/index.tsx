import { NextPage } from "next";
import { useEffect, useState } from "react";
import { VegaLite } from 'react-vega';
import Module from "../components/Module";
import Page from "../components/Page";

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

type ChartState = {
  "schema": Object | null, 
  "chartLoaded": "loading" | "loaded" | "failed", 
  "apiStatus": 'healthy' | 'unhealthy' | null, 
  "chartStatus": "updated" | "refreshable" | null, 
  "queryRuntimeSeconds": number | null, 
}

const computeAgeMinutes = (iso_timestamp: string) => {
  const msecs_now = Date.now(); 
  const msecs_tstamp = new Date(iso_timestamp).valueOf(); 
  const age_minutes = (msecs_now - msecs_tstamp) / 1000 / 60; 
  if (age_minutes <= 0) {
    throw new Error("Age should never be negative"); 
  }
  return age_minutes; 
}

const getChartStatusFromAge = (iso_timestamp: string) => {
  const age_minutes = computeAgeMinutes(iso_timestamp); 
  return age_minutes < 15 ? "updated" : "refreshable"
}

const Chart : React.FC<{ name: string; height?: number; }> = ({ name, height = 300 }) => {
  const [chartState, setChartState] = useState<ChartState>({
    "schema": null, 
    "chartLoaded": "loading", 
    "apiStatus": null, 
    "chartStatus": null, 
    "queryRuntimeSeconds": null
  }); 

  useEffect(() => {
    (async () => {
      // Including the Authorization header forces the requests to do CORS preflight 
      const headers = {"Authorization": "Bearer dummy_force_cors_preflight"}
      const newChartState: ChartState = {
        "schema": null, 
        "chartLoaded": "loading", 
        "apiStatus": null, 
        "chartStatus": null, 
        "queryRuntimeSeconds": null
      }; 
      try {
        const res = await fetch(urlApiName(name).toString(), {"headers": headers })
          .then(r => r.json());
        const { status } = res[name.toLowerCase()]; 
        if (status !== 'recomputed' && status !== 'use_cached') {
          throw new Error(`Unrecognized status returned from cloud function: ${status}`)
        }
        newChartState.apiStatus = "healthy"; 
      } catch (e) {
        console.error(e);
        newChartState.apiStatus = "unhealthy"; 
      }
      try {
        const { schema, timestamp, run_time_seconds } = await fetch(urlBucketName(name).toString(), {"headers": headers })
          .then(r => r.json()); 
        newChartState.chartLoaded = "loaded";  
        newChartState.schema = schema; 
        newChartState.queryRuntimeSeconds = parseFloat(run_time_seconds); 
        newChartState.chartStatus = getChartStatusFromAge(timestamp);
      } catch (e) {
        console.error(e);
        newChartState.chartLoaded = "failed";  
        newChartState.schema = null; 
        newChartState.queryRuntimeSeconds = null; 
        newChartState.chartStatus = null; 
      }
      setChartState(newChartState);
    })()
  }, [])

  const statusColor = (
      chartState.chartStatus === "updated" ? "green" : 
      chartState.chartStatus === "refreshable" ? "yellow" : 
      "red"
  );

  // Chart body content 
  const chartContent = (
    chartState.chartLoaded === "loading" ? (
      <div className="flex items-center justify-center" style={{ height }}>
        Loading...
      </div>
    ) : 
    chartState.chartLoaded === "loaded" ? (
      <div>
        <div className="grid gap-4 grid-cols-2 grid-rows-1">
          <div className="p-2"><h4 className="font-bold">{name}</h4></div>
          <div className="flex justify-end p-2">
            <h6 className="font-bold inline">status:</h6>
            <p className="inline ml-1 mr-2">{chartState.chartStatus}</p>
            <div className="inline flex items-center">
              <div className={`rounded-full bg-${statusColor}-500 w-3.5 h-3.5`}></div>
            </div>
          </div>
        </div>
        <div className="flex items-center justify-center">
          <VegaLite spec={chartState.schema as Object} height={height} />
        </div>
      </div>
    ) : (
      <div className="flex items-center justify-center" style={{ height }}>
        Something went wrong while loading chart {name}.
      </div>
    )
  ); 

  return chartContent; 

}

const Home: NextPage = () => {
  return (
    <Page>
      <div className="block md:grid md:grid-cols-6 gap-4 m-4">
        <div className="col-span-6">
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
        </div>
        <div className="col-span-6">
          <Module>
            <Chart name="FieldOverview" />
          </Module>
        </div>
        {/* <div className="col-span-6">
          <Module>
            <Chart name="Creditworthiness" />
          </Module>
        </div> */}
      </div>
    </Page>
  );
}

export default Home;