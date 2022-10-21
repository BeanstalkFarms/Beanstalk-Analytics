import React from "react";

const Footer: React.FC<{
  children?: React.ReactNode;
}> = (props) => {
  return (
    <div className="flex flex-col md:flex-row justify-center gap-2 md:gap-10 md:py-6 py-4 md:px-4 px-2 border-t border-gray-50">
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
