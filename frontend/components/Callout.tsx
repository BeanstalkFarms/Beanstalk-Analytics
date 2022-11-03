import React from "react";
import { format as d3_format } from "d3-format";


const Callout : React.FC<{
    status: 'loading' | 'ready'
    type: 'quantity' | 'info'
    title?: string 
    value?: any 
    subtitle?: string 
}> = ({
  status, type, title, value, subtitle
}) => {
    let body = null; 
    if (status === 'ready') {
        if (type === "quantity") {
            if (!value) {
                throw Error('value must be specified.'); 
            }
            body = <React.Fragment>
                <div className="whitespace-nowrap">{title}</div>
                <div className="whitespace-nowrap">{value}</div>
            </React.Fragment>; 
        } else {
            body = <React.Fragment>
                <div className="whitespace-nowrap">{title}</div>
                <div className="whitespace-nowrap">{subtitle}</div>
            </React.Fragment>; 
        }
    }  

    return (
        <div>
            <div className="relative bg-[#45b955]/[.2] m-2 rounded-md overflow-hidden bg-clip-content">
                {/* Background Logo */}
                <div className="flex justify-center items-center h-24 w-12 m-auto">
                    <img alt="" src="/bean-logo-circled.svg" className="absolute w-12 inline opacity-20" />
                </div>
                {/* Content */}
                <div className="absolute inset-1/2">
                    <div className="absolute inset-1/2 flex flex-col justify-center items-center">
                        {body}
                    </div>
                </div>
            </div>
        </div>
  )
}

export default Callout;