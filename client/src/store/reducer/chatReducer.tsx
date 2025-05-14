import { createSlice } from "@reduxjs/toolkit";
import { chat, getChatHistory, initSession } from "../action/action";

interface ChatState {
  messages: { sender: "user" | "bot"; text: string }[];
  session_id: string | null;
  loading: boolean;
  error: string | null;
}

const initialState: ChatState = {
  messages: [],
  session_id: null,
  loading: false,
  error: null,
};

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      // Init session actions
      .addCase(initSession.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(initSession.fulfilled, (state, action) => {
        state.loading = false;
        state.session_id = action.payload.session_id;
        state.messages = []; // Empty for new session, welcome message handled in frontend
      })
      .addCase(initSession.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Chat actions
      .addCase(chat.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(chat.fulfilled, (state, action) => {
        state.loading = false;
        state.session_id = action.payload.session_id;
        state.messages.push(
          { sender: "user", text: action.meta.arg.message },
          { sender: "bot", text: action.payload.result }
        );
      })
      .addCase(chat.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Chat history actions
      .addCase(getChatHistory.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getChatHistory.fulfilled, (state, action) => {
        state.loading = false;
        state.session_id = action.payload.result.session_id;
        state.messages = action.payload.result.messages.map((msg: any) => ({
          sender: msg.sender === "user" ? "user" : "bot",
          text: msg.text,
        }));
      })
      .addCase(getChatHistory.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export default chatSlice.reducer;
