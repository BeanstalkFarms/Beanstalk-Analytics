import React from 'react';
import useSize from '@react-hook/size';
import { useEffect, useReducer, useRef } from "react";
import { VegaLite } from 'react-vega';
import { get, set, cloneDeep } from "lodash";

export type WidthPaths = Array<{ path: Array<string | number>, factor: number }>; 

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
}; 

const getInitialState = (spec: Object) => ({ 
    vega_lite_spec: cloneDeep(spec),
    w_target: 600,
    w_tol: 10,
    w_factor: 1, 
    w_factor_delta: .15, 
    w_last: -1 
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


function reducer(state: State, action: Action): State {

    // const apply_w_factor = (s: Object, wpaths: WidthPaths, wf_old: number, wf_new: number) => {
    //   for (let { path, factor } of wpaths) {
    //     // Invert the previous multiplier calculation 
    //     const m1 = (1 + Math.abs(wf_new - 1) / factor); 
    //     let w_curr = get(s, path, undefined); 
    //     let w_base = w_curr / (1 + Math.abs(wf_old - 1) / factor); 
    //     set(s, path,  * m0 * m1); 
    //   }
    //   return s; 
    // }; 

    switch (action.type) {
      case "update-width": 
        return {...state, w_last: action.w}; 
      case "resize": 
        let msg = `Width of ${action.w} is ${state.w_factor < action.w_factor ? "too small" : "too large"}`; 
        msg += ` / w_factor: ${state.w_factor} -> ${action.w_factor}`; 
        if (action.w_factor_delta) {
          msg += ` / w_factor_delta: ${state.w_factor_delta} -> ${action.w_factor_delta}`; 
        }
        console.log(msg); 
        return {
          ...state, 
          vega_lite_spec: apply_w_factor(
              // TODO: @SiloChad the spec updates aren't working correctly unless I clone the 
              //      entire object. This probably is terrible for performance so any suggestions on 
              //      how to make this more efficient. 
              cloneDeep({...state.vega_lite_spec}), 
              action.width_paths, 
              state.w_factor, 
              action.w_factor
          ),
          w_factor: action.w_factor, 
          w_factor_delta: get(action, "w_factor_delta", state.w_factor_delta), 
          w_last: action.w, 
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
    if (w_factor < 0) {
      // Failed to resize chart to the desired width. Should show an error to the user. 
      throw new Error("uggggghhhhhh")
    }
    if (spec && rendered) {
      if (too_small) {
        // Need to increase size of chart 
        if ((w_last > w_target + w_tol) && w_last > w) {
          // On last iteration, chart was too large, then we overshot optimal range.
          // w_factor_delta is too large 
          // w_factor is too small 
          let new_w_factor_delta = w_factor_delta / 2; 
          let new_w_factor = w_factor + new_w_factor_delta; 
          dispatch({ 
            type: "resize", 
            width_paths,
            w_factor: new_w_factor, 
            w_factor_delta: new_w_factor_delta, 
            w
          }); 
        } else {
          // We did not overshoot the optimal range, and are still below it 
          // w_factor_delta is fine 
          // w_factor is too small 
          let new_w_factor = w_factor + w_factor_delta
          dispatch({ 
            type: "resize", 
            width_paths,
            w_factor: new_w_factor, 
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
          let new_w_factor = w_factor - new_w_factor_delta; 
          dispatch({ 
            type: "resize", 
            width_paths,
            w_factor: new_w_factor, 
            w_factor_delta: new_w_factor_delta, 
            w
          }); 
        } else {
          // We did not overshoot the optimal range, and are still above it 
          // w_factor_delta is fine 
          // w_factor is too large 
          let new_w_factor = w_factor - w_factor_delta; 
          dispatch({ 
            type: "resize", 
            width_paths,
            w_factor: new_w_factor, 
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
