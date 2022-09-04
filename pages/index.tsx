import { NextPage } from "next";
import { useEffect, useState } from "react";
import { VegaLite } from 'react-vega';

if (!process.env.NEXT_PUBLIC_STORAGE_BUCKET_NAME) throw new Error('Environment: Missing bucket');
if (!process.env.NEXT_PUBLIC_CDN) throw new Error('Environment: Missing CDN address'); 

const bucketUrl = new URL(`${process.env.NEXT_PUBLIC_CDN}/${process.env.NEXT_PUBLIC_STORAGE_BUCKET_NAME}`);

const Chart : React.FC<{ name: string }> = ({ name }) => {
  const [spec, setSpec] = useState<null | object>(null);
  
  useEffect(() => {
    (async () => {
      const url = new URL(`${bucketUrl}/${name}.json`);
      console.log(`Fetching: ${url}`)
      try {
        setSpec(
          await fetch(url.toString()).then((r) => r.json())
        )
      } catch(e) {
        console.error(e);
      }
    })()
  }, [])

  if (!spec) {
    return <>Loading</>;
  }

  return (
    <VegaLite spec={spec} />
  )
}

const Home: NextPage = () => {
  return (
    <div>
      <Chart name="Fertilizer" />
    </div>
  );
}

export default Home;