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
    <div className="flex flex-row px-4 py-2 border-b border-gray-200">
      <div className="flex-1 flex items-center justify-start md:space-x-5 space-x-2">
        <NavLink href="/" className="md:inline-block hidden">
          <img alt="" src="/beanstalk.svg" className="h-5" /> 
        </NavLink>
        <NavLink href="/credit-profile">
          Credit Profile
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
      <div className="flex items-center justify-end">
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