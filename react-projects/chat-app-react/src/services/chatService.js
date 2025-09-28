import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000';

export const sendMessage = (question) => {
  return axios.post(`${API_URL}/chat`, { question });
};

export const fetchEmails = () => {
  return axios.get(`${API_URL}/fetch`);
};

export const buildVectorstore = () => {
  return axios.get(`${API_URL}/build`);
};
