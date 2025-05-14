import { createAsyncThunk } from "@reduxjs/toolkit";
import * as api from "../api/api";

export const getCompanyName = createAsyncThunk(
  "GET_COMPANY_NAME",
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.getCompanyName();
      return response.data;
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.message || "Failed to fetch company name";
      return rejectWithValue(errorMessage);
    }
  }
);

export const chat = createAsyncThunk(
  "CHAT",
  async (
    data: { message: string; session_id?: string },
    { rejectWithValue }
  ) => {
    try {
      const response = await api.chat(data);
      return response.data;
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.message || "Failed to send message";
      return rejectWithValue(errorMessage);
    }
  }
);

export const getChatHistory = createAsyncThunk(
  "GET_CHAT_HISTORY",
  async (session_id: string, { rejectWithValue }) => {
    try {
      const response = await api.getChatHistory(session_id);
      return response.data;
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.message || "Failed to fetch chat history";
      return rejectWithValue(errorMessage);
    }
  }
);

export const initSession = createAsyncThunk(
  "INIT_SESSION",
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.initSession();
      return response.data;
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.message || "Failed to initialize session";
      return rejectWithValue(errorMessage);
    }
  }
);
