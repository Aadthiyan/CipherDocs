import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { toast } from 'react-hot-toast';
import api from '../api/client';
import { EnvelopeIcon, ArrowPathIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

const VerifyEmail = () => {
    const [code, setCode] = useState('');
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [resending, setResending] = useState(false);
    const [timer, setTimer] = useState(600); // 10 minutes in seconds
    const navigate = useNavigate();
    const { login } = useAuth();

    useEffect(() => {
        // Get email from localStorage (set during signup)
        const storedEmail = localStorage.getItem('verificationEmail');
        if (!storedEmail) {
            toast.error('No email found. Please sign up first.');
            navigate('/signup');
            return;
        }
        setEmail(storedEmail);

        // Countdown timer
        const interval = setInterval(() => {
            setTimer((prev) => (prev > 0 ? prev - 1 : 0));
        }, 1000);

        return () => clearInterval(interval);
    }, [navigate]);

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const handleVerify = async (e) => {
        e.preventDefault();
        if (code.length !== 6) {
            toast.error('Please enter a 6-digit code');
            return;
        }

        setLoading(true);
        try {
            // Verify email with OTP
            const response = await api.post('/api/v1/auth/verify-email', {
                email,
                code
            });

            toast.success('Email verified successfully!');

            // Store tokens
            const { access_token, refresh_token } = response.data;
            localStorage.setItem('token', access_token);
            if (refresh_token) {
                localStorage.setItem('refreshToken', refresh_token);
            }

            // Clean up verification data
            localStorage.removeItem('verificationEmail');
            localStorage.removeItem('verificationPassword');

            // Redirect to dashboard
            navigate('/dashboard');
        } catch (error) {
            console.error(error);
            const errorMsg = error.response?.data?.detail || 'Verification failed. Please try again.';
            toast.error(errorMsg);
        } finally {
            setLoading(false);
        }
    };

    const handleResend = async () => {
        setResending(true);
        try {
            await api.post('/api/v1/auth/resend-otp', { email });
            toast.success('Verification code sent! Check your email.');
            setTimer(600); // Reset timer
        } catch (error) {
            console.error(error);
            const errorMsg = error.response?.data?.detail || 'Failed to resend code.';
            toast.error(errorMsg);
        } finally {
            setResending(false);
        }
    };

    const handleCodeChange = (e) => {
        const value = e.target.value.replace(/\D/g, ''); // Only digits
        if (value.length <= 6) {
            setCode(value);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-[#0a0e1a] via-[#111827] to-[#1a2234] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md w-full">
                <div className="bg-[#1a2234]/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-indigo-500/20 p-8">
                    {/* Icon */}
                    <div className="flex justify-center mb-6">
                        <div className="bg-indigo-600/20 rounded-full p-4">
                            <EnvelopeIcon className="w-12 h-12 text-indigo-400" />
                        </div>
                    </div>

                    {/* Title */}
                    <div className="text-center mb-8">
                        <h2 className="text-3xl font-bold text-white mb-2">
                            Verify Your Email
                        </h2>
                        <p className="text-gray-400">
                            We sent a 6-digit code to
                        </p>
                        <p className="text-indigo-400 font-semibold mt-1">
                            {email}
                        </p>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleVerify} className="space-y-6">
                        {/* OTP Input */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Verification Code
                            </label>
                            <input
                                type="text"
                                value={code}
                                onChange={handleCodeChange}
                                placeholder="123456"
                                maxLength={6}
                                className="w-full px-4 py-3 bg-[#0a0e1a]/50 border border-indigo-500/30 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 text-center text-2xl tracking-widest font-mono"
                                required
                                autoFocus
                            />
                            <p className="text-sm text-gray-500 mt-2 text-center">
                                Enter the 6-digit code from your email
                            </p>
                        </div>

                        {/* Timer */}
                        <div className="text-center">
                            <p className="text-sm text-gray-400">
                                Code expires in:{' '}
                                <span className={`font-semibold ${timer < 60 ? 'text-red-400' : 'text-indigo-400'}`}>
                                    {formatTime(timer)}
                                </span>
                            </p>
                        </div>

                        {/* Verify Button */}
                        <button
                            type="submit"
                            disabled={loading || code.length !== 6}
                            className="w-full flex justify-center items-center gap-2 py-3 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold rounded-xl transition-all duration-200 shadow-lg shadow-indigo-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? (
                                <>
                                    <ArrowPathIcon className="w-5 h-5 animate-spin" />
                                    <span>Verifying...</span>
                                </>
                            ) : (
                                <>
                                    <CheckCircleIcon className="w-5 h-5" />
                                    <span>Verify Email</span>
                                </>
                            )}
                        </button>

                        {/* Resend Button */}
                        <div className="text-center">
                            <button
                                type="button"
                                onClick={handleResend}
                                disabled={resending || timer > 540} // Can resend after 1 minute
                                className="text-indigo-400 hover:text-indigo-300 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                {resending ? 'Sending...' : "Didn't receive code? Resend"}
                            </button>
                        </div>
                    </form>

                    {/* Security Note */}
                    <div className="mt-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
                        <p className="text-xs text-yellow-200 text-center">
                            🔒 Never share your verification code with anyone. CipherDocs will never ask for it.
                        </p>
                    </div>

                    {/* Back to Signup */}
                    <div className="mt-6 text-center">
                        <button
                            onClick={() => {
                                localStorage.removeItem('verificationEmail');
                                localStorage.removeItem('verificationPassword');
                                navigate('/signup');
                            }}
                            className="text-gray-400 hover:text-white text-sm transition-colors"
                        >
                            ← Back to Signup
                        </button>
                    </div>
                </div>

                {/* Help Text */}
                <div className="mt-6 text-center">
                    <p className="text-sm text-gray-500">
                        Check your spam folder if you don't see the email
                    </p>
                </div>
            </div>
        </div>
    );
};

export default VerifyEmail;
