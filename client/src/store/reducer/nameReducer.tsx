import { createSlice } from "@reduxjs/toolkit";
import { getCompanyName } from "../action/action";

interface NameState {
  company: string | null;
  loading: boolean;
  error: string | null;
}

const initialState: NameState = {
  company: null,
  loading: false,
  error: null,
};

const companyNameSlice = createSlice({
  name: "name",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getCompanyName.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getCompanyName.fulfilled, (state, action) => {
        state.company = action.payload.result; // Assuming your backend returns { result: "CompanyName" }
        state.loading = false;
      })
      .addCase(getCompanyName.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export default companyNameSlice.reducer;
