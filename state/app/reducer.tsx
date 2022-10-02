import Action, { PageName, ALL_PAGE_NAMES } from "./actions"; 

export type Page = {
    id: number 
    name: PageName 
    label: string 
}

const pageLabels: {[key in PageName]: string} = {
    "": "Beanstalk Credit Profile", 
    "FarmersMarket": "Farmer's Market", 
    "Barn": "Barn", 
    "Silo": "Silo", 
    "Field": "Field"
}
export const pages: Array<Page> = ALL_PAGE_NAMES.map((page_name: PageName, i: number) => ({
    id: i, name: page_name, label: pageLabels[page_name]
})); 

const initialPage: Page = pages[0]; 
if (initialPage.name !== "") {
    throw Error("Initial page should be index"); 
}

export type State = {
    currentPage: Page
} 

export const initialState: State = {
    currentPage: initialPage
}

const reducer = (state: State, action: Action): State => {
    switch(action.type) {
        case "select-page": 
            return {currentPage: action.page}; 
        default:
            return state
    }
}; 

export default reducer; 