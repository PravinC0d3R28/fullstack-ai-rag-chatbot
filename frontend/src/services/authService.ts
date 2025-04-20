import axios from 'axios';

const API_URL = 'http://localhost:8000'; // Make sure this matches your FastAPI server URL

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface User {
  username: string;
  isAdmin: boolean;
  token: string;
}

export const login = async (credentials: LoginCredentials): Promise<User> => {
  try {
    console.log('Attempting login with:', credentials.username);
    const response = await axios.post(`${API_URL}/api/login`, credentials);
    
    console.log('Login response:', response.data);
    
    if (response.data) {
      // Store user details in localStorage
      const user = {
        username: response.data.username,
        isAdmin: response.data.is_admin,
        token: response.data.access_token
      };
      
      localStorage.setItem('user', JSON.stringify(user));
      return user;
    }
    
    throw new Error('Login failed');
  } catch (error) {
    console.error('Login error:', error);
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'Login failed');
    }
    throw new Error('Network error or server not reachable');
  }
};

export const logout = (): void => {
  localStorage.removeItem('user');
};

export const getCurrentUser = (): User | null => {
  const userJson = localStorage.getItem('user');
  if (userJson) {
    return JSON.parse(userJson);
  }
  return null;
};

export const isAuthenticated = (): boolean => {
  return getCurrentUser() !== null;
};

export const isAdmin = (): boolean => {
  const user = getCurrentUser();
  return user !== null && user.isAdmin;
};

// Configure axios for authenticated requests
export const authAxios = axios.create({
  baseURL: API_URL
});

authAxios.interceptors.request.use(
  (config) => {
    const user = getCurrentUser();
    if (user && user.token) {
      config.headers.Authorization = `Bearer ${user.token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle 401 responses
authAxios.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API error:', error);
    if (error.response && error.response.status === 401) {
      logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
); 