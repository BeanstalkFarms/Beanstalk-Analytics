import React from 'react';
import useSize from '@react-hook/size';
import { useEffect, useReducer, useRef } from "react";
import { VegaLite } from 'react-vega';
import { get, set, cloneDeep } from "lodash";

export type WidthPaths = Array<{ path: Array<string | number>, factor: number, value: number }>; 

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
    w_target: 300,
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
              action.w_factor,
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
      throw new Error("need to do something here lmao.")
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
