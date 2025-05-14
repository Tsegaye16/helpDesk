import { configureStore } from "@reduxjs/toolkit";
import appReducer from "./reducer/mainReducer";

const store = configureStore({
  reducer: appReducer,
});

export default store;
