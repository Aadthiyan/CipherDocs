import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const checkAuth = () => {
            const token = localStorage.getItem('token');
            if (token) {
                // In a real app, we would validate the token /api/v1/users/me
                // For now, we assume if token exists, user is logged in
                setUser({ token });
            }
            setLoading(false);
        };
        checkAuth();
    }, []);

    const login = async (email, password) => {
        // Backend expects JSON with email and password fields
        const response = await api.post('/api/v1/auth/login', {
            email,
            password
        });

        const { access_token } = response.data;
        localStorage.setItem('token', access_token);
        setUser({ token: access_token });
        return response.data;
    };

    const signup = async (email, password, companyName) => {
        const response = await api.post('/api/v1/auth/signup', {
            email,
            password,
            company_name: companyName
        });
        return response.data;
    };

    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, signup, logout, loading }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
