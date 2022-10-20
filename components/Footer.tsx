import React from "react";

const Footer: React.FC<{
  children?: React.ReactNode;
}> = (props) => {
  return (
    <div className="flex flex-row justify-center gap-10 pt-2 pb-7">
      <a href="https://docs.bean.money/">Docs</a>
      <a href="https://discord.gg/beanstalk">Discord</a>
      <a href="https://twitter.com/beanstalkfarms">Twitter</a>
      <a href="https://immunefi.com/bounty/beanstalk">Bug Bounty</a>
      <a href="https://github.com/beanstalkfarms">GitHub</a>
      <a href="https://docs.bean.money/disclosures">Disclosures</a>
    </div>
  )
}

export default Footer;
