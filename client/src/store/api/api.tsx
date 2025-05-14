import axios from "axios";
//
const isLocal = window.location.hostname === "localhost";

const API = axios.create({
  baseURL: isLocal
    ? "http://localhost:8080"
    : "https://helpdesk-0ovm.onrender.com",
});
console.log(process.env.REACT_APP_LOCAL_API_BASE_URL);
export const getCompanyName = async () => {
  try {
    return await API.get(`/getCompanyName`);
  } catch (error) {
    throw error;
  }
};

export const chat = async (data: { message: string; session_id?: string }) => {
  try {
    return await API.post(`/chat`, data);
  } catch (error) {
    throw error;
  }
};

export const getChatHistory = async (session_id: string) => {
  try {
    return await API.get(`/getChatHistory/${session_id}`);
  } catch (error) {
    throw error;
  }
};

export const initSession = async () => {
  try {
    return await API.post(`/initSession`);
  } catch (error) {
    throw error;
  }
};
