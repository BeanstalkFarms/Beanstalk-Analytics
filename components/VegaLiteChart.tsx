import React, { useState } from 'react';
import useSize from '@react-hook/size';
import { useEffect, useReducer, useRef, useLayoutEffect } from "react";
import { VegaLite } from 'react-vega';
import { set, cloneDeep, omit } from "lodash";
import useInterval from '../hooks/useInterval';

export type WidthPaths = Array<{ path: Array<string | number>, factor: number, value: number }>; 

const apply_w_factor = (s: Object, wpaths: WidthPaths, wf: number) => {
  for (let { path, factor, value } of wpaths) {
    // Factor scales the magnitude of changes done by wf 
    // ex: Factor is 2, impact of wf is twice as small on size increase / decrease. 
    const multiplier = 1 + (wf - 1) / factor; 
    set(s, path, value * multiplier); 
  }
  return s; 
}; 

const w_tol = 10;
const w_factor_initial = 1; 
const w_factor_delta_initial = .5;

type ResizeState = {
  // The current target width for the resize attempt    
  w_target: number 
  // Multiplicative factor by which we multiply all vega-lite width path values.
  // We are attempting to find the value of wf that gives us a width close 
  // enough to w_target to be considered successful. 
  wf: number
  // Additive factor by which we change wf when resizing. 
  wf_delta: number 
  // The width of the chart on the previous resize iteration. 
  w_last: number 
  // Counter for num iterations spent resizing 
  counter: number 
  // epoch (milliseconds)
  epoch: number
};

type State = {
  // Vega-lite spec 
  vega_lite_spec: Object 
  // State related to chart resizing 
  resize: ResizeState
}; 

type Action =
    { type: "resize-set-width", width_paths: WidthPaths, w: number, w_target: number }
  | { type: "resize", width_paths: WidthPaths, w: number, };


const MAX_ITERATION_LIMIT = 50; 


function reducer(state: State, action: Action): State {

    const { vega_lite_spec, resize } = state; 
    const { w_target, wf, w_last, wf_delta, counter } = resize; 

    switch (action.type) {
      case "resize-set-width": 
        // Resetting of the resize object. Occurs when target width changes 
        console.log(`Resize reset. Current Width: ${action.w} Target width: ${action.w_target}`);
        return {
          vega_lite_spec: apply_w_factor(
            cloneDeep(vega_lite_spec), action.width_paths, w_factor_initial
          ),
          resize: {
            w_target: action.w_target,
            wf: w_factor_initial,  
            wf_delta: w_factor_delta_initial, 
            w_last: action.w, 
            counter: 0, 
            epoch: Date.now()
          }
        };
      case "resize":  
        // If we need to resize, compute new values for wf and wf_delta 
        const too_small = action.w < (w_target - w_tol); 
        const too_large = action.w > (w_target + w_tol);
        let new_wf_delta; 
        let new_wf; 
        // I just love how I literally have no idea what I'm doing but this just works 
        if (too_small) {
          let did_overshoot = counter > 0 && w_last > (w_target + w_tol);
          new_wf_delta = did_overshoot ? wf_delta / 2 : wf_delta; 
          new_wf = wf + new_wf_delta; 
        } 
        else if (too_large) {
          let did_overshoot = w_last < (w_target - w_tol);
          new_wf_delta = did_overshoot ? wf_delta / 2 : wf_delta; 
          while (wf - new_wf_delta <= 0) {
            new_wf_delta /= 2; 
          }
          new_wf = wf - new_wf_delta; 
        } else {
          return state; 
        }
        // Failure conditions 
        if (new_wf < 0) {
          throw new Error("wf cannot be negative."); 
        } else if (wf_delta < 0) {
          throw new Error("wf_delta cannot be negative."); 
        } else if (state.resize.counter > MAX_ITERATION_LIMIT) {
          throw new Error(
            `Resizing algorithm exceeded max iteration limit of ${MAX_ITERATION_LIMIT}.`
          );
        }
        // console.log(
        //   `Resize step start\n` +
        //   `Last Width: ${w_last} Current Width: ${action.w} Target Width: ${w_target}\n` + 
        //   `Current width ${wf < new_wf ? "too small" : "too large"}\n` + 
        //   `wf: ${wf} -> ${new_wf}\n` + 
        //   `wf_delta: ${wf_delta}` + (wf_delta !== new_wf_delta ? ` -> ${new_wf_delta}\n` : '\n') + 
        //   `iteration: ${state.resize.counter}`
        // );
        const new_spec = apply_w_factor(
            // TODO: @SiloChad the spec updates aren't working correctly unless I clone the 
            //      entire object. This probably is terrible for performance so any suggestions on 
            //      how to make this more efficient?
            cloneDeep(vega_lite_spec), 
            action.width_paths, 
            new_wf,
        ); 
        return {
          vega_lite_spec: new_spec, 
          resize: {
            w_target: state.resize.w_target, 
            wf: new_wf, 
            wf_delta: new_wf_delta,
            w_last: action.w, 
            counter: state.resize.counter + 1, 
            epoch: Date.now()
          }
        };
      default:
        throw new Error("Invalid action");
    }
}

const VegaLiteChart: React.FC<{ 
  name: string, 
  spec: Object, 
  width_paths: WidthPaths, 
  height: number, 
  target_width: number, 
}> = ({ name, spec, width_paths, height, target_width }) => {

  const spec_no_data = cloneDeep(omit(spec, 'datasets')); 
  // @ts-ignore
  const data = spec['datasets'];
  
  const ref_wrapper = useRef<HTMLDivElement>(null); 
  const [w, h] = useSize(ref_wrapper);
  const [resize_toggle, set_resize_toggle] = useState<boolean>(false); 
  const [state, dispatch] = useReducer(reducer, { 
    vega_lite_spec: spec_no_data,
    resize: { 
      w_target: 0, wf: 0, wf_delta: 0, counter: 0, w_last: 0, epoch: Date.now()
    }, 
  });
  const { vega_lite_spec, resize } = state; 
  const { w_target, epoch } = resize; 

  useEffect(() => {
    if (target_width !== w_target) {
      dispatch({ type: "resize-set-width", width_paths, w_target: target_width, w });  
    } 
  }, [w, width_paths, target_width, w_target])

  useLayoutEffect(() => {
    if (w !== 0) {
      dispatch({ type: "resize", width_paths, w });
    }
  }, [w, width_paths, w_target, resize_toggle]);

  useInterval(() => {
    const too_small = w < (w_target - w_tol); 
    const too_large = w > (w_target + w_tol);
    const ts = Date.now()
    // console.log(too_small, too_large, (ts - epoch) >= 500, ts, epoch, ts - epoch, )
    if ((ts - epoch) >= 500 && (too_small || too_large)) {
      set_resize_toggle(!resize_toggle);
    }
  }, 500); 

  const is_resizing = !(
    target_width === w_target && 
    w >= (w_target - w_tol) &&
    w <= (w_target + w_tol)
  );

  return <div ref={ref_wrapper} className="relative">
    <VegaLite spec={cloneDeep(vega_lite_spec)} data={data} height={height}></VegaLite>
    <div className={`absolute top-0 left-0 w-full h-full ${is_resizing ? 'bg-red-300' : 'bg-slate-300'} opacity-50`}></div>
  </div>;

}; 

export default VegaLiteChart; 
