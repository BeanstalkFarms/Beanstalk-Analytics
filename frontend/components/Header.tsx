import cn from 'classnames';
import Link, { LinkProps } from "next/link";
import { useRouter } from "next/router";
import React from "react";
import Button from './Button';

const NavLink : React.FC<React.PropsWithChildren<LinkProps & { className?: string; }>> = ({ className, children, ...props }) => {
  const router = useRouter();
  return (
    <Link {...props} className={className}>
      <a className={cn(
        className, 
        router.pathname.toLowerCase() === props.href.toString().toLowerCase() ? 'underline' : 'text-gray-600',
        'text-lg hover:text-gray-900'
      )}>
        {children}
      </a>
    </Link>
  )
}

const Header : React.FC<{}> = () => {
  return (
    <div className="flex flex-row md:px-4 px-2 py-2 border-b border-gray-50">
      <div className="flex-1 flex items-center justify-start md:space-x-6 space-x-4">
        <Link href="/">
          <a className="inline-flex items-center space-x-2">
            <img alt="" src="/beanstalk.svg" className="h-5 hidden md:inline" /> 
            <img alt="" src="/bean-logo-circled.svg" className="h-8 md:hidden inline" />
            <span className="no-underline bg-slate-200 color-white px-2 py-0.5 rounded-md text-[10px]">BETA</span>
          </a>
        </Link>
        <NavLink href="/overview">
          Credit Profile
        </NavLink>
        <NavLink href="/liquidity">
          Liquidity
        </NavLink>
        <NavLink href="/silo">
          Silo
        </NavLink>
        <NavLink href="/field">
          Field
        </NavLink>
        <NavLink href="/barn">
          Barn
        </NavLink>
        <NavLink href="/market">
          Market
        </NavLink>
      </div>
      <div className="hidden md:flex items-center justify-end">
        <a href="https://app.bean.money" target="_blank" rel="noreferrer">
          <Button>
            Launch App
          </Button>
        </a>
      </div>
    </div>
  )
};

export default Header;