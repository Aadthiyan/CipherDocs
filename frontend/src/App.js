import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Toaster } from 'react-hot-toast';

import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import VerifyEmail from './pages/VerifyEmail';
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import Search from './pages/Search';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import PrivateRoute from './components/PrivateRoute';

function App() {
    return (
        <Router>
            <AuthProvider>
                <Toaster position="top-right" />
                <Routes>
                    {/* Public Routes */}
                    <Route path="/" element={<Landing />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/signup" element={<Signup />} />
                    <Route path="/verify-email" element={<VerifyEmail />} />

                    {/* Protected Routes */}
                    <Route element={<PrivateRoute />}>
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/documents" element={<Documents />} />
                        <Route path="/search" element={<Search />} />
                        <Route path="/analytics" element={<Analytics />} />
                        <Route path="/settings" element={<Settings />} />
                    </Route>

                    {/* Catch all redirect */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </AuthProvider>
        </Router>
    );
}

export default App;
