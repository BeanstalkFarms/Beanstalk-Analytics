import { Page } from "./reducer"; 

// https://stackoverflow.com/questions/44480644/string-union-to-string-array
export const ALL_PAGE_NAMES = [
    '', 'FarmersMarket', 'Barn', 'Silo', 'Field'
] as const;
type PageNameTuple = typeof ALL_PAGE_NAMES; // readonly 
export type PageName = PageNameTuple[number]; 

type Action = { type: "select-page", page: Page }

export default Action; 