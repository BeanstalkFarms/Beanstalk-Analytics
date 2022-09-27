import React from 'react';
import useSize from '@react-hook/size';
import { useEffect, useReducer, useRef } from "react";
import { VegaLite } from 'react-vega';
import { get, set, cloneDeep } from "lodash";

export type WidthPaths = Array<{ path: Array<string | number>, factor: number, value: number }>; 

const apply_w_factor = (s: Object, wpaths: WidthPaths, wf: number) => {
  for (let { path, factor, value } of wpaths) {
    /* 2 examples illustrating how we use factor, value, and wf to determine current width: 
    ------------------------------------------------------------------------
    wpaths = [
      {path: ["width"], factor: 1, value: 100},
      {path: ["radius"], factor: 2, value: 100},
    ]
    schema = {
      "width": 100,   
      "radius": 100, 
    }

    Logically, factor decreases the impact of wf by a multiplicative factor  
    Both factor and wf are inputs to multiplier 
    - multiplier = 1 + (wf - 1) / factor 

    ------------------------------------------------------------------------
    example 1: wf = .9 
    
    - width goes from 100 -> 90
    - radius goes from 100 -> 95 
      - applying full wf (as is done to "width") decreases width by 10. 
      - factor tells us to reduce the amount of decrease (10) by a factor of 2 yielding 10 / 2 = 5. 

    compute multiplier for "width"
    1 + (.9 - 1) / 1 = 1 + -.1 = .9

    compute multiplier for "radius"
    1 + (.9 - 1) / 2 = 1 + -.1 / 2 = .95

    ------------------------------------------------------------------------
    example 2: wf = 1.2
   
    - width goes from 100 -> 120
    - radius goes from 100 -> 110 
      - applying full wf (as is done to "width") increases width by 20. 
      - factor tells us to reduce the amount of increase (20) by a factor of 2 yielding 20 / 2 = 10. 

    compute multiplier for "width"
    1 + (1.2 - 1) / 1 = 1 + .2 = 1.2

    compute multiplier for "radius"
    1 + (1.2 - 1) / 2 = 1 + .2 / 2 = 1.1 
    */ 
    const multiplier = 1 + (wf - 1) / factor; 
    set(s, path, value * multiplier); 
  }
  return s; 
}; 

type State = {
  // vega-lite spec 
  vega_lite_spec: Object 
  // The target width of the chart 
  w_target: number 
  // The tolerance threshold for getting near w_target 
  w_tol: number 
  // multiplicative factor by which we multiply all vega-lite width path values 
  w_factor: number 
  // additive factor by which we change w_factor when resizing. 
  w_factor_delta: number 
  // the last value of w 
  w_last: number 
  // counter variable for number of iterations spent resizing 
  resize_counter: number 
}; 

const getInitialState = (spec: Object) => ({ 
    vega_lite_spec: cloneDeep(spec),
    w_target: 600, // 500 is problematic 
    w_tol: 10,
    w_factor: 1, 
    w_factor_delta: .15, 
    w_last: -1, 
    resize_counter: 0, 
})

type Action =
  | { 
      type: "resize", 
      width_paths: WidthPaths, 
      w_factor: number, 
      w_factor_delta?: number, 
      w: number, 
    }
  | { type: "update-width", w: number };


const MAX_ITERATION_LIMIT = 100; 


function reducer(state: State, action: Action): State {

    switch (action.type) {
      case "update-width": 
        return {...state, resize_counter: 0, w_last: action.w}; 
      case "resize": 
        let msg = `Width of ${action.w} is ${state.w_factor < action.w_factor ? "too small" : "too large"}`; 
        msg += ` / w_factor: ${state.w_factor} -> ${action.w_factor}`; 
        if (action.w_factor_delta) {
          msg += ` / w_factor_delta: ${state.w_factor_delta} -> ${action.w_factor_delta}`; 
        }
        console.log(msg); 
        if (action.w_factor < 0) {
          throw new Error("w_factor cannot be negative."); 
        } else if (state.resize_counter > MAX_ITERATION_LIMIT) {
          throw new Error(
            `Resizing algorithm exceeded max iteration limit of ${MAX_ITERATION_LIMIT}.`
          );
        }
        return {
          ...state, 
          vega_lite_spec: apply_w_factor(
              // TODO: @SiloChad the spec updates aren't working correctly unless I clone the 
              //      entire object. This probably is terrible for performance so any suggestions on 
              //      how to make this more efficient. 
              cloneDeep({...state.vega_lite_spec}), 
              action.width_paths, 
              action.w_factor,
          ),
          w_factor: action.w_factor, 
          w_factor_delta: get(action, "w_factor_delta", state.w_factor_delta), 
          w_last: action.w, 
          resize_counter: state.resize_counter + 1 
        };
      default:
        throw new Error("Invalid action");
    }
}

const VegaLiteChart: React.FC<{ 
  name: string, spec: Object, width_paths: WidthPaths, height: number 
}> = ({ name, spec, width_paths, height }) => {

  const ref_wrapper = useRef<HTMLDivElement>(null); 
  const [state, dispatch] = useReducer(reducer, getInitialState(spec)); 
  const [w, h] = useSize(ref_wrapper);
  const { vega_lite_spec, w_factor, w_factor_delta, w_last, w_target, w_tol } = state; 

  useEffect(() => {
    const rendered = w !== 0; 
    const too_small = rendered && w < w_target - w_tol; 
    const too_large = rendered && w > w_target + w_tol;
    if (spec && rendered) {
      if (too_small) {
        // Need to increase size of chart 
        if ((w_last > w_target + w_tol) && w_last > w) {
          // On last iteration, chart was too large, then we overshot optimal range.
          // w_factor_delta is too large 
          // w_factor is too small 
          let new_w_factor_delta = w_factor_delta / 2; 
          dispatch({ 
            type: "resize", 
            width_paths,
            w_factor: w_factor + new_w_factor_delta, 
            w_factor_delta: new_w_factor_delta, 
            w
          }); 
        } else {
          // We did not overshoot the optimal range, and are still below it 
          // w_factor_delta is fine 
          // w_factor is too small 
          dispatch({ 
            type: "resize", 
            width_paths,
            w_factor: w_factor + w_factor_delta, 
            w
          }); 
        }
      } else if (too_large) {
        // Need to decrease size of chart 
        if ((w_last < w_target - w_tol) && w_last < w) {
          // On last iteration, chart was too small, then we overshot optimal range.
          // w_factor_delta is too large 
          // w_factor is too large 
          let new_w_factor_delta = w_factor_delta / 2; 
          while (w_factor - new_w_factor_delta < 0) {
            new_w_factor_delta /= 2; 
          }
          dispatch({ 
            type: "resize", 
            width_paths,
            w_factor: w_factor - new_w_factor_delta, 
            w_factor_delta: new_w_factor_delta, 
            w
          }); 
        } else {
          // We did not overshoot the optimal range, and are still above it 
          // w_factor_delta is fine (unless we go negative)
          // w_factor is too large 
          let new_w_factor_delta = w_factor_delta; 
          while (w_factor - new_w_factor_delta < 0) {
            new_w_factor_delta /= 2; 
          }
          dispatch({ 
            type: "resize", 
            width_paths,
            w_factor: w_factor - new_w_factor_delta, 
            w_factor_delta: new_w_factor_delta,
            w
          }); 
        }
      } else {
        if (w_last !== w) {
          dispatch({ type: "update-width", w });
        }
      }
    } else {
      if (w_last !== w) {
        dispatch({ type: "update-width", w });
      }
    }
  });

  return <div ref={ref_wrapper}>
    <VegaLite spec={vega_lite_spec} height={height}></VegaLite>
  </div>
}; 

export default VegaLiteChart; 
