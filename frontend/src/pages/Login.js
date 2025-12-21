import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { toast } from 'react-hot-toast';
import { ShieldCheckIcon, EnvelopeIcon, LockClosedIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await login(email, password);
            toast.success('Logged in successfully!');
            navigate('/dashboard');
        } catch (error) {
            console.error(error);
            toast.error('Login failed. Please check your credentials.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-[#0a0e1a] via-[#111827] to-[#1a2234] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
            {/* Animated Background */}
            <div className="fixed inset-0 bg-grid opacity-10 pointer-events-none" />
            <div className="fixed top-0 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse" />
            <div className="fixed bottom-0 right-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />

            <div className="max-w-md w-full space-y-8 relative z-10">
                {/* Back to Home */}
                <Link
                    to="/"
                    className="inline-flex items-center space-x-2 text-gray-400 hover:text-white transition-colors mb-4"
                >
                    <ArrowLeftIcon className="w-5 h-5" />
                    <span>Back to Home</span>
                </Link>

                {/* Header */}
                <div className="text-center fade-in">
                    <div className="flex justify-center mb-6">
                        <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center glow-lg">
                            <ShieldCheckIcon className="w-10 h-10 text-white" />
                        </div>
                    </div>
                    <h2 className="text-4xl font-black text-white mb-2">
                        Welcome Back
                    </h2>
                    <p className="text-gray-400 text-lg">
                        Sign in to access your secure workspace
                    </p>
                </div>

                {/* Login Form */}
                <div className="glass-strong rounded-2xl p-8 shadow-2xl">
                    <form className="space-y-6" onSubmit={handleSubmit}>
                        {/* Email Input */}
                        <div>
                            <label htmlFor="email" className="block text-sm font-semibold text-gray-300 mb-2">
                                Email Address
                            </label>
                            <input
                                id="email"
                                name="email"
                                type="email"
                                required
                                className="input-modern"
                                placeholder="you@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                            />
                        </div>

                        {/* Password Input */}
                        <div>
                            <label htmlFor="password" className="block text-sm font-semibold text-gray-300 mb-2">
                                Password
                            </label>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                required
                                className="input-modern"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>

                        {/* Remember Me & Forgot Password */}
                        <div className="flex items-center justify-between">
                            <div className="flex items-center">
                                <input
                                    id="remember-me"
                                    name="remember-me"
                                    type="checkbox"
                                    className="h-4 w-4 rounded border-gray-600 bg-gray-700 text-indigo-600 focus:ring-indigo-500"
                                />
                                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-400">
                                    Remember me
                                </label>
                            </div>
                            <div className="text-sm">
                                <a href="#" className="font-medium text-indigo-400 hover:text-indigo-300 transition-colors">
                                    Forgot password?
                                </a>
                            </div>
                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full btn-primary text-lg py-3 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                        >
                            {loading ? (
                                <>
                                    <div className="spinner w-5 h-5 border-2" />
                                    <span>Signing in...</span>
                                </>
                            ) : (
                                <span>Sign In</span>
                            )}
                        </button>
                    </form>

                    {/* Divider */}
                    <div className="mt-6">
                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-gray-700" />
                            </div>
                            <div className="relative flex justify-center text-sm">
                                <span className="px-2 bg-[#111827] text-gray-400">New to CyborgDB?</span>
                            </div>
                        </div>
                    </div>

                    {/* Sign Up Link */}
                    <div className="mt-6 text-center">
                        <Link
                            to="/signup"
                            className="btn-secondary w-full inline-block text-center"
                        >
                            Create an Account
                        </Link>
                    </div>
                </div>

                {/* Security Badge */}
                <div className="text-center">
                    <div className="inline-flex items-center space-x-2 text-sm text-gray-500">
                        <LockClosedIcon className="w-4 h-4" />
                        <span>Secured with 256-bit AES encryption</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
