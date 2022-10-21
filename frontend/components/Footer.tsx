import React from "react";

const Footer: React.FC<{
  children?: React.ReactNode;
}> = (props) => {
  return (
    <div className="flex flex-row justify-center gap-10 pt-2 pb-7">
      <a href="https://docs.bean.money/" target="_blank" rel="noreferrer">
        Docs
      </a>
      <a href="https://discord.gg/beanstalk" target="_blank" rel="noreferrer">
        Discord
      </a>
      <a href="https://twitter.com/beanstalkfarms" target="_blank" rel="noreferrer">
        Twitter
      </a>
      <a href="https://immunefi.com/bounty/beanstalk" target="_blank" rel="noreferrer">
        Bug Bounty
      </a>
      <a href="https://github.com/beanstalkfarms" target="_blank" rel="noreferrer" className="md:inline-block hidden">
        GitHub
      </a>
      <a href="https://docs.bean.money/disclosures" target="_blank" rel="noreferrer" className="md:inline-block hidden">
        Disclosures
      </a>
    </div>
  )
}

export default Footer;
