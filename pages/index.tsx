import { NextPage } from "next";
import { useEffect, useState } from "react";
import { VegaLite } from 'react-vega';
import Module from "../components/Module";
import Page from "../components/Page";

if (!process.env.NEXT_PUBLIC_STORAGE_BUCKET_NAME) throw new Error('Environment: Missing bucket');
if (!process.env.NEXT_PUBLIC_CDN) throw new Error('Environment: Missing CDN address'); 

// const apiUrl = new URL(`${process.env.}`)
const bucketUrl = new URL(`${process.env.NEXT_PUBLIC_CDN}/${process.env.NEXT_PUBLIC_STORAGE_BUCKET_NAME}`);

const Chart : React.FC<{ name: string; height?: number; }> = ({ name, height = 300 }) => {
  const [spec, setSpec] = useState<null | object>(null);
  const [status, setStatus] = useState<'loading' | 'error' | 'ready'>('loading');
  
  useEffect(() => {
    (async () => {
      const url = new URL(`${bucketUrl}/schemas/${name.toLowerCase()}.json?${Date.now()}`);
      try {
        setSpec(
          await fetch(url.toString())
            .then((r) => r.json())
        )
        setStatus('ready');
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