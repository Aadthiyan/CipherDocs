import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { toast } from 'react-hot-toast';
import { ShieldCheckIcon, EnvelopeIcon, LockClosedIcon, BuildingOfficeIcon, ArrowLeftIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

const Signup = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [company, setCompany] = useState('');
    const { signup, login } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await signup(email, password, company);
            toast.success('Account created! Check your email for verification code.');
            // Store email in localStorage for verification page
            localStorage.setItem('verificationEmail', email);
            localStorage.setItem('verificationPassword', password);
            // Redirect to email verification page
            navigate('/verify-email');
        } catch (error) {
            console.error(error);
            const errorMsg = error.response?.data?.detail || 'Signup failed. Please try again.';
            toast.error(errorMsg);
        } finally {
            setLoading(false);
        }
    };

    const features = [
        'End-to-end encryption',
        'Multi-tenant isolation',
        'GDPR & HIPAA compliant',
        'Unlimited document storage'
    ];

    return (
        <div className="min-h-screen bg-gradient-to-br from-[#0a0e1a] via-[#111827] to-[#1a2234] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
            {/* Animated Background */}
            <div className="fixed inset-0 bg-grid opacity-10 pointer-events-none" />
            <div className="fixed top-0 right-1/4 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl animate-pulse" />
            <div className="fixed bottom-0 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />

            <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-2 gap-8 relative z-10">
                {/* Left Side - Features */}
                <div className="hidden lg:flex flex-col justify-center space-y-8 fade-in">
                    <div>
                        <Link
                            to="/"
                            className="inline-flex items-center space-x-2 text-gray-400 hover:text-white transition-colors mb-8"
                        >
                            <ArrowLeftIcon className="w-5 h-5" />
                            <span>Back to Home</span>
                        </Link>

                        <div className="flex items-center space-x-3 mb-6">
                            <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center glow">
                                <ShieldCheckIcon className="w-7 h-7 text-white" />
                            </div>
                            <h1 className="text-3xl font-bold gradient-text">CyborgDB</h1>
                        </div>

                        <h2 className="text-4xl font-black text-white mb-4">
                            Start Your Secure Journey
                        </h2>
                        <p className="text-xl text-gray-400 mb-8">
                            Join enterprises worldwide who trust CyborgDB for encrypted document search and AI-powered insights.
                        </p>
                    </div>

                    <div className="space-y-4">
                        {features.map((feature, index) => (
                            <div
                                key={index}
                                className="flex items-center space-x-3 slide-in-left"
                                style={{ animationDelay: `${index * 100}ms` }}
                            >
                                <div className="flex-shrink-0 w-6 h-6 bg-green-500/20 rounded-full flex items-center justify-center">
                                    <CheckCircleIcon className="w-5 h-5 text-green-400" />
                                </div>
                                <span className="text-gray-300 text-lg">{feature}</span>
                            </div>
                        ))}
                    </div>

                    <div className="card p-6 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border-indigo-500/20">
                        <p className="text-gray-300 italic">
                            "CyborgDB transformed how we handle sensitive documents. The encryption-in-use feature gives us peace of mind."
                        </p>
                        <div className="mt-4 flex items-center space-x-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full" />
                            <div>
                                <p className="text-white font-semibold">Sarah Johnson</p>
                                <p className="text-gray-400 text-sm">CTO, TechCorp</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Side - Signup Form */}
                <div className="flex flex-col justify-center">
                    <div className="lg:hidden mb-6">
                        <Link
                            to="/"
                            className="inline-flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
                        >
                            <ArrowLeftIcon className="w-5 h-5" />
                            <span>Back to Home</span>
                        </Link>
                    </div>

                    <div className="glass-strong rounded-2xl p-8 shadow-2xl fade-in">
                        <div className="text-center mb-8">
                            <div className="lg:hidden flex justify-center mb-6">
                                <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center glow-lg">
                                    <ShieldCheckIcon className="w-10 h-10 text-white" />
                                </div>
                            </div>
                            <h2 className="text-3xl font-black text-white mb-2">
                                Create Account
                            </h2>
                            <p className="text-gray-400">
                                Get started with your free trial
                            </p>
                        </div>

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
                                    placeholder="you@company.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                />
                            </div>

                            {/* Company Input */}
                            <div>
                                <label htmlFor="company" className="block text-sm font-semibold text-gray-300 mb-2">
                                    Company Name
                                </label>
                                <input
                                    id="company"
                                    name="company"
                                    type="text"
                                    required
                                    className="input-modern"
                                    placeholder="Your Company"
                                    value={company}
                                    onChange={(e) => setCompany(e.target.value)}
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
                                <p className="mt-2 text-xs text-gray-500">
                                    Must be at least 8 characters long
                                </p>
                            </div>

                            {/* Terms & Conditions */}
                            <div className="flex items-start">
                                <div className="flex items-center h-5">
                                    <input
                                        id="terms"
                                        name="terms"
                                        type="checkbox"
                                        required
                                        className="h-4 w-4 rounded border-gray-600 bg-gray-700 text-indigo-600 focus:ring-indigo-500"
                                    />
                                </div>
                                <div className="ml-3 text-sm">
                                    <label htmlFor="terms" className="text-gray-400">
                                        I agree to the{' '}
                                        <a href="#" className="text-indigo-400 hover:text-indigo-300">
                                            Terms of Service
                                        </a>{' '}
                                        and{' '}
                                        <a href="#" className="text-indigo-400 hover:text-indigo-300">
                                            Privacy Policy
                                        </a>
                                    </label>
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
                                        <span>Creating account...</span>
                                    </>
                                ) : (
                                    <span>Create Account</span>
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
                                    <span className="px-2 bg-[#111827] text-gray-400">Already have an account?</span>
                                </div>
                            </div>
                        </div>

                        {/* Sign In Link */}
                        <div className="mt-6 text-center">
                            <Link
                                to="/login"
                                className="btn-secondary w-full inline-block text-center"
                            >
                                Sign In Instead
                            </Link>
                        </div>
                    </div>

                    {/* Security Badge */}
                    <div className="text-center mt-6">
                        <div className="inline-flex items-center space-x-2 text-sm text-gray-500">
                            <LockClosedIcon className="w-4 h-4" />
                            <span>Your data is encrypted with 256-bit AES</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Signup;
