import type { AppProps } from 'next/app'
import '../styles/globals.css'
import AppContext from '../components/AppContext';
import { useReducer } from 'react';
import reducer from '../state/app/reducer';
import { initialState, State } from '../state/app/reducer';


function MyApp({ Component, pageProps }: AppProps) {
  const [state, dispatch] = useReducer(reducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      <Component {...pageProps} />
    </AppContext.Provider>
  );
}

export default MyApp
