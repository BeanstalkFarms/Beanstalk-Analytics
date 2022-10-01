import { createContext, Dispatch } from 'react';
import reducer, { State } from "../state/app/reducer"; 
import Action from "../state/app/actions"; 

export interface IAppContext {
    state: State 
    dispatch: Dispatch<Action>
}

const AppContext = createContext<IAppContext | null>(null); 

export default AppContext