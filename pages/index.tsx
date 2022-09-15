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

const Chart : React.FC<{ name: string; height?: number; }> = ({ name, height = 300 }) => {
  const [spec, setSpec] = useState<null | object>(null);
  const [status, setStatus] = useState<'loading' | 'error' | 'ready'>('loading');
  
  useEffect(() => {
    (async () => {
      const reqUrlApi = new URL(`${urlApi}schemas/refresh?data=${name.toLowerCase()}&${Date.now()}`);
      const reqUrlBucket = new URL(`${urlBucket}/schemas/${name.toLowerCase()}.json?${Date.now()}`);
      try {
        const apiResp = await fetch(reqUrlApi.toString()).then(r => r.json()); 
        // status: Either 'recomputed' or 'use_cached' 
        // run_time_seconds: The number of seconds it took to generate the chart on the server 
        const { status, run_time_seconds } = apiResp; 
        // timestamp: The timestamp at which the schema was created 
        const { schema, timestamp } = await fetch(reqUrlBucket.toString()).then(r => r.json()); 
        setSpec(schema); 
        setStatus('ready');
        // const preflight = await fetch(url.toString(), {
        //   "method": "OPTIONS", 
        //   // "mode": "cors", 
        //   "headers": {
        //     "Access-Control-Request-Method": "GET"
        //   }
        // });
        // console.log("Preflight response"); 
        // console.log(preflight); 
      } catch(e) {
        console.error(e);
        setStatus('error');
      }
    })()
  }, [])

  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        Loading...
      </div>
    );
  }

  if (status === 'error' || !spec) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        Something went wrong while loading chart {name}.
      </div>
    );
  }

  return (
    <div>
      <div className="p-2"><h4 className="font-bold">{name}</h4></div>
      <div className="flex items-center justify-center">
        <VegaLite spec={spec} height={height} />
      </div>
    </div>
  )
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