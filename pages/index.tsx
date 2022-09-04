import { NextPage } from "next";
import { useEffect, useState } from "react";
import { VegaLite } from 'react-vega';

const url = `/barn_breakdown.json`;

const Chart : React.FC = () => {
  const [spec, setSpec] = useState<null | object>(null);
  useEffect(() => {
    (async () => {
      setSpec(
        await fetch(url).then((r) => r.json())
      )
    })()
  })

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
      <Chart />
    </div>
  );
}

export default Home;