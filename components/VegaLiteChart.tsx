import React from 'react';
import useSize from '@react-hook/size';
import { useEffect, useReducer, useRef } from "react";
import { VegaLite } from 'react-vega';
import { get, set, cloneDeep, omit } from "lodash";

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
  // We are attempting to find the value of w_factor that gives us a width close 
  // enough to w_target to be considered successful. 
  w_factor: number 
  // Additive factor by which we change w_factor when resizing. 
  w_factor_delta: number 
  // Counter variable for number of iterations spent resizing 
  counter: number 
  // The width of the chart on the previous resize iteration. 
  w_last: number 
};

type State = {
  // Vega-lite spec 
  vega_lite_spec: Object 
  // State related to chart resizing 
  resize: ResizeState
}; 

const getInitialState = (
  spec: Object, 
  width_paths: WidthPaths, 
  w_target: number,
): State => ({ 
    vega_lite_spec: apply_w_factor(
      cloneDeep(spec), width_paths, w_factor_initial
    ),
    resize: {
      w_target,
      w_factor: w_factor_initial, 
      w_factor_delta: w_factor_delta_initial, 
      w_last: -1, 
      counter: 0, 
    }
}); 

type Action =
  | { 
      type: "resize", 
      width_paths: WidthPaths, 
      w_factor: number, 
      w_factor_delta: number, 
      w: number, 
    }
  | { 
      type: "trigger-resize", 
      width_paths: WidthPaths, 
      w_target: number 
    };


const MAX_ITERATION_LIMIT = 50; 


function reducer(state: State, action: Action): State {

    switch (action.type) {
      case "trigger-resize": 
        console.log(`Triggering a rezise to ${action.w_target}`);
        return getInitialState(
          state.vega_lite_spec, 
          action.width_paths, 
          action.w_target, 
        );
      case "resize":  
        const w_factor = action.w_factor; 
        const w_factor_delta = get(action, "w_factor_delta", state.resize.w_factor_delta); 
        if (w_factor < 0) {
          throw new Error("w_factor cannot be negative."); 
        } else if (w_factor_delta < 0) {
          throw new Error("w_factor_delta cannot be negative."); 
        } else if (state.resize.counter > MAX_ITERATION_LIMIT) {
          throw new Error(
            `Resizing algorithm exceeded max iteration limit of ${MAX_ITERATION_LIMIT}.`
          );
        }
        console.log(
          `Last Width: ${state.resize.w_last} Current Width: ${action.w} Target Width: ${state.resize.w_target}\n` + 
          `Current width ${state.resize.w_factor < w_factor ? "too small" : "too large"}\n` + 
          `w_factor: ${state.resize.w_factor} -> ${w_factor}\n` + 
          `w_factor_delta: ${state.resize.w_factor_delta}` + (
            state.resize.w_factor_delta !== w_factor_delta ? ` -> ${w_factor_delta}\n` : '\n'
          ) + 
          `iteration: ${state.resize.counter}`
        );
        const new_spec = apply_w_factor(
            // TODO: @SiloChad the spec updates aren't working correctly unless I clone the 
            //      entire object. This probably is terrible for performance so any suggestions on 
            //      how to make this more efficient. 
            cloneDeep(state.vega_lite_spec), 
            action.width_paths, 
            w_factor,
        ); 
        // for (let { path, value } of action.width_paths) {
        //   console.log(`reducer ${path} ${get(new_spec, path)} ${value}`); 
        // }
        return {
          vega_lite_spec: new_spec, 
          resize: {
            w_target: state.resize.w_target, 
            w_factor, 
            w_factor_delta, 
            counter: state.resize.counter + 1, 
            w_last: action.w, 
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
  const [state, dispatch] = useReducer(reducer, getInitialState(spec_no_data, width_paths, target_width)); 
  const { vega_lite_spec, resize } = state; 
  const { w_target, w_factor, w_factor_delta, w_last } = resize; 

  useEffect(() => {
    // for (let { path, value } of width_paths) {
    //   console.log(`effect ${path} ${get(vega_lite_spec, path)} ${value}`); 
    // }
    // console.log(vega_lite_spec)
    const is_parent_rendered = w_target > 0; 
    const is_self_rendered = w > 0; 
    const width_stable = w_last == w; // don't resize when this is true 
    const ready = spec && is_parent_rendered && is_self_rendered; 
    const too_small = ready && w < (w_target - w_tol); 
    const too_large = ready && w > (w_target + w_tol);
    console.log(ready, too_small, too_large, width_stable);
    if (ready && target_width !== w_target) {
      dispatch({type: "trigger-resize", width_paths, w_target: target_width});  
    } 
    else if ((too_small || too_large) && (!width_stable)) {
      let sign; 
      let new_w_factor_delta
      if (too_small) {
        // Need to increase size of chart 
        let did_overshoot = w_last > (w_target + w_tol);
        // If we are too small on current iteration but were too large on prior iteration, 
        // then we overshot the optimal width range. Thus, we decrease w_factor_delta to 
        // minimize the chances of overshooting the optimal range again. 
        new_w_factor_delta = did_overshoot ? w_factor_delta / 2 : w_factor_delta; 
        sign = 1; 
      } else {
        // Need to decrease size of chart 
        let did_overshoot = w_last < (w_target - w_tol);
        // If we are too large on current iteration but were too small on prior iteration, 
        // then we overshot the optimal width range. Thus, we decrease w_factor_delta to 
        // minimize the chances of overshooting the optimal range again. 
        new_w_factor_delta = did_overshoot ? w_factor_delta / 2 : w_factor_delta; 
        // It's possible that if we use the above value of new_w_factor_delta, then we 
        // might cause w_factor to be negative. We eliminate this possibility by doing the following. 
        while (w_factor - new_w_factor_delta <= 0) {
          new_w_factor_delta /= 2; 
        }
        sign = -1; 
      }
      dispatch({ 
        type: "resize", 
        width_paths,
        w_factor: w_factor + sign * new_w_factor_delta, 
        w_factor_delta: new_w_factor_delta, 
        w
      }); 
    } 
  });

  return <div ref={ref_wrapper} className="relative">
    <VegaLite spec={vega_lite_spec} data={data} height={height}></VegaLite>
    <div className="absolute top-0 left-0 w-full h-full bg-slate-300 opacity-50"></div>
  </div>;

}; 

export default VegaLiteChart; 
