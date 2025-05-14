import { combineReducers } from "redux";
import nameReducer from "./nameReducer";
import chatReducer from "./chatReducer";

const appReducer = combineReducers({
  companyName: nameReducer,
  chat: chatReducer,
});

export type RootState = ReturnType<typeof appReducer>;

export default appReducer;
