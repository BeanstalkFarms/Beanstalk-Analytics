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
  // Counter for num iterations spent resizing 
  counter: number 
  // Status  
  status: "in-progress" | "applied" 
  // The width of the chart on the previous resize iteration. 
  w_start: number 
};

type State = {
  // Vega-lite spec 
  vega_lite_spec: Object 
  // State related to chart resizing 
  resize: ResizeState
}; 

type Action =
    { 
      type: "resize-reset", 
      width_paths: WidthPaths,
      w: number, 
      w_target: number 
    }
  | { 
      type: "resize-step-start", 
      width_paths: WidthPaths, 
      w_factor: number, 
      w_factor_delta: number, 
      w: number, 
    }
  | { 
      type: "resize-step-end", w: number, 
    };


const MAX_ITERATION_LIMIT = 50; 


function reducer(state: State, action: Action): State {

    switch (action.type) {
      case "resize-reset": 
        console.log(`Resize reset. New target width: ${action.w_target}`);
        return {
          vega_lite_spec: apply_w_factor(
            cloneDeep(state.vega_lite_spec), action.width_paths, w_factor_initial
          ),
          resize: {
            w_target: action.w_target,
            w_factor: w_factor_initial, 
            w_factor_delta: w_factor_delta_initial, 
            w_start: action.w, 
            counter: 0, 
            status: "in-progress", 
          }
        };
      case "resize-step-start":  
        const w_factor_delta = get(action, "w_factor_delta", state.resize.w_factor_delta); 
        if (action.w_factor < 0) {
          throw new Error("w_factor cannot be negative."); 
        } else if (w_factor_delta < 0) {
          throw new Error("w_factor_delta cannot be negative."); 
        } else if (state.resize.counter > MAX_ITERATION_LIMIT) {
          throw new Error(
            `Resizing algorithm exceeded max iteration limit of ${MAX_ITERATION_LIMIT}.`
          );
        }
        console.log(
          `Resize step start\n` +
          `Last Width: ${state.resize.w_start} Current Width: ${action.w} Target Width: ${state.resize.w_target}\n` + 
          `Current width ${state.resize.w_factor < action.w_factor ? "too small" : "too large"}\n` + 
          `w_factor: ${state.resize.w_factor} -> ${action.w_factor}\n` + 
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
            action.w_factor,
        ); 
        return {
          vega_lite_spec: new_spec, 
          resize: {
            w_target: state.resize.w_target, 
            w_factor: action.w_factor, 
            w_factor_delta, 
            w_start: action.w, 
            counter: state.resize.counter, 
            status: "in-progress", 
          }
        };
      case "resize-step-end": 
        console.log(`Resize step end.`);
        return {
          vega_lite_spec: state.vega_lite_spec, 
          resize: {
            ...state.resize, 
            status: "applied", 
            counter: state.resize.counter + 1, 
            w_start: -1,
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
  const [state, dispatch] = useReducer(reducer, { 
    vega_lite_spec: spec_no_data,
    resize: {
      w_target: target_width,
      w_factor: w_factor_initial, 
      w_factor_delta: w_factor_delta_initial, 
      w_start: w, 
      counter: 0, 
      status: "in-progress", 
    }
  });
  const { vega_lite_spec, resize } = state; 
  const { w_target, w_factor, w_factor_delta, w_start, status } = resize; 

  useEffect(() => {
    // for (let { path, value } of width_paths) {
    //   console.log(`effect ${path} ${get(vega_lite_spec, path)} ${value}`); 
    // }
    // console.log(vega_lite_spec)
    const is_parent_rendered = w_target > 0; 
    const is_self_rendered = w > 0; 
    const ready = vega_lite_spec && is_parent_rendered && is_self_rendered; 
    const width_stable = w_start == w; // don't resize when this is true 
    const too_small = w < (w_target - w_tol); 
    const too_large = w > (w_target + w_tol);
    console.log(`ready: ${ready} too small: ${too_small} too_large: ${too_large} width stable: ${width_stable}`)
    // console.log(vega_lite_spec);
    if (ready) {
      if (target_width !== w_target) {
        // Interrupt existing attempts to resize by updating target and resetting resize state. 
        dispatch({type: "resize-reset", width_paths, w_target: target_width, w });  
      } 
      else if (status === "applied" && (too_small || too_large)) {
        // Start a resize step since previous step was already applied 
        let sign; 
        let new_w_factor_delta;
        if (too_small) {
          // Need to increase size of chart 
          let did_overshoot = w_start > (w_target + w_tol);
          // If we are too small on current iteration but were too large on prior iteration, 
          // then we overshot the optimal width range. Thus, we decrease w_factor_delta to 
          // minimize the chances of overshooting the optimal range again. 
          new_w_factor_delta = did_overshoot ? w_factor_delta / 2 : w_factor_delta; 
          sign = 1; 
        } else {
          // Need to decrease size of chart 
          let did_overshoot = w_start < (w_target - w_tol);
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
          type: "resize-step-start", 
          width_paths,
          w_factor: w_factor + sign * new_w_factor_delta, 
          w_factor_delta: new_w_factor_delta, 
          w
        }); 
      } else if (ready && status === "in-progress" && !width_stable) {
        dispatch({type: "resize-step-end", w}); 
      }
    }
    
  });

  return <div ref={ref_wrapper} className="relative">
    <VegaLite spec={cloneDeep(vega_lite_spec)} data={data} height={height}></VegaLite>
    <div className="absolute top-0 left-0 w-full h-full bg-slate-300 opacity-50"></div>
  </div>;

}; 

export default VegaLiteChart; 
