// Frontend API Configuration Guide
// Configure these endpoints in your frontend

// Development
export const API_CONFIG_DEV = {
  baseURL: 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
};

// Production (Render)
export const API_CONFIG_PROD = {
  baseURL: process.env.REACT_APP_BACKEND_URL || 'https://cipherdocs.onrender.com',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
};

// Select based on environment
const isDevelopment = process.env.NODE_ENV === 'development';
export const API_CONFIG = isDevelopment ? API_CONFIG_DEV : API_CONFIG_PROD;

// API Endpoints
export const API_ENDPOINTS = {
  // Authentication
  AUTH_LOGIN: '/api/v1/auth/login',
  AUTH_REGISTER: '/api/v1/auth/register',
  AUTH_LOGOUT: '/api/v1/auth/logout',
  AUTH_REFRESH: '/api/v1/auth/refresh',
  AUTH_VERIFY: '/api/v1/auth/verify',

  // Users
  USERS_ME: '/api/v1/users/me',
  USERS_UPDATE: '/api/v1/users/me',
  USERS_CHANGE_PASSWORD: '/api/v1/users/me/password',

  // Documents
  DOCUMENTS_LIST: '/api/v1/documents',
  DOCUMENTS_UPLOAD: '/api/v1/documents/upload',
  DOCUMENTS_DELETE: (id) => `/api/v1/documents/${id}`,
  DOCUMENTS_GET: (id) => `/api/v1/documents/${id}`,

  // Search
  SEARCH: '/api/v1/search',
  SEARCH_ADVANCED: '/api/v1/search/advanced',

  // Health
  HEALTH: '/health',
};

/**
 * Create API client with authentication
 * @param token JWT token from login
 * @returns config object with headers
 */
export const createApiClient = (token) => {
  const headers = { ...API_CONFIG.headers };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return {
    ...API_CONFIG,
    headers,
  };
};

/**
 * Example API call with error handling
 */
export const apiCall = async (
  endpoint,
  method = 'GET',
  data,
  token
) => {
  try {
    const config = createApiClient(token);
    const url = `${config.baseURL}${endpoint}`;

    const response = await fetch(url, {
      method,
      headers: config.headers,
      body: data ? JSON.stringify(data) : undefined,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API call failed: ${endpoint}`, error);
    throw error;
  }
};
