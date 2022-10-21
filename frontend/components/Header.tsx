import cn from 'classnames';
import Link, { LinkProps } from "next/link";
import { useRouter } from "next/router";
import React from "react";
import Button from './Button';
import Navigation from "./Navigation";

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

const Header : React.FC<{
  children?: React.ReactNode;
}> = ({
  children
}) => {
  return (
    <div className="flex flex-row md:px-4 px-2 py-2 border-b border-gray-50">
      <div className="flex-1 flex items-center justify-start md:space-x-6 space-x-4">
        <NavLink href="/">
          <img alt="" src="/beanstalk.svg" className="h-5 hidden md:inline -mt-1" /> 
          <img alt="" src="/bean-logo-circled.svg" className="h-8 md:hidden inline" /> 
        </NavLink>
        <NavLink href="/credit-profile">
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