import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
    ShieldCheckIcon,
    LockClosedIcon,
    ServerIcon,
    BoltIcon,
    DocumentMagnifyingGlassIcon,
    UserGroupIcon,
    ChartBarIcon,
    CheckCircleIcon,
    ArrowRightIcon,
    SparklesIcon
} from '@heroicons/react/24/outline';

const Landing = () => {
    const [scrollY, setScrollY] = useState(0);

    useEffect(() => {
        const handleScroll = () => setScrollY(window.scrollY);
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const features = [
        {
            icon: LockClosedIcon,
            title: 'Encryption-in-Use',
            description: 'Embeddings remain encrypted even during vector similarity search, ensuring maximum data protection.',
            color: 'from-purple-500 to-pink-500'
        },
        {
            icon: UserGroupIcon,
            title: 'Multi-Tenant Isolation',
            description: 'Cryptographic separation between tenants with zero data leakage. Each tenant\'s data is completely isolated.',
            color: 'from-blue-500 to-cyan-500'
        },
        {
            icon: ShieldCheckIcon,
            title: 'Compliance-Ready',
            description: 'Meets GDPR, HIPAA, and SOC2 requirements with enterprise-grade security and audit logging.',
            color: 'from-green-500 to-emerald-500'
        },
        {
            icon: BoltIcon,
            title: 'Privacy-Preserving',
            description: 'Local embedding generation with no third-party API calls. Your data never leaves your infrastructure.',
            color: 'from-yellow-500 to-orange-500'
        },
        {
            icon: DocumentMagnifyingGlassIcon,
            title: 'Semantic Search',
            description: 'AI-powered semantic search across your encrypted documents with lightning-fast results.',
            color: 'from-indigo-500 to-purple-500'
        },
        {
            icon: ServerIcon,
            title: 'Scalable Architecture',
            description: 'Docker-based microservices with horizontal scaling to handle enterprise workloads.',
            color: 'from-red-500 to-pink-500'
        }
    ];

    const benefits = [
        'Zero cross-tenant data leakage',
        'End-to-end encryption',
        'JWT authentication & RBAC',
        'Comprehensive audit logging',
        'Local embedding generation',
        'Enterprise-grade security',
        'GDPR & HIPAA compliant',
        'Scalable microservices'
    ];

    const stats = [
        { value: '256-bit', label: 'AES Encryption' },
        { value: '100%', label: 'Data Isolation' },
        { value: '<1s', label: 'Search Latency' },
        { value: '∞', label: 'Scalability' }
    ];

    return (
        <div className="min-h-screen bg-gradient-to-b from-[#0a0e1a] via-[#111827] to-[#0a0e1a] text-white overflow-hidden">
            {/* Animated Background */}
            <div className="fixed inset-0 bg-grid opacity-20 pointer-events-none" />
            <div
                className="fixed inset-0 pointer-events-none"
                style={{
                    background: `radial-gradient(circle at ${50 + scrollY * 0.1}% ${50 + scrollY * 0.05}%, rgba(99, 102, 241, 0.15), transparent 50%)`
                }}
            />

            {/* Navigation */}
            <nav className="relative z-50 glass-strong">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-20">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center glow">
                                <ShieldCheckIcon className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold gradient-text">CyborgDB</h1>
                                <p className="text-xs text-gray-400">Encrypted Document Search</p>
                            </div>
                        </div>
                        <div className="flex items-center space-x-4">
                            <Link
                                to="/login"
                                className="px-6 py-2.5 text-sm font-semibold text-gray-300 hover:text-white transition-colors"
                            >
                                Sign In
                            </Link>
                            <Link
                                to="/signup"
                                className="btn-primary flex items-center space-x-2"
                            >
                                <span>Get Started</span>
                                <ArrowRightIcon className="w-4 h-4" />
                            </Link>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="relative pt-20 pb-32 px-4 sm:px-6 lg:px-8">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center fade-in">
                        <div className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full mb-8">
                            <SparklesIcon className="w-5 h-5 text-indigo-400" />
                            <span className="text-sm font-medium text-indigo-300">Enterprise-Grade Encrypted Search Platform</span>
                        </div>

                        <h1 className="text-6xl md:text-7xl lg:text-8xl font-black mb-6 leading-tight">
                            Secure AI Search
                            <br />
                            <span className="gradient-text">Without Compromise</span>
                        </h1>

                        <p className="text-xl md:text-2xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed">
                            Multi-tenant SaaS platform enabling enterprises to run AI-powered semantic search
                            on encrypted embeddings with <span className="text-indigo-400 font-semibold">zero data leakage</span>
                        </p>

                        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
                            <Link
                                to="/signup"
                                className="btn-primary text-lg px-8 py-4 flex items-center space-x-2 glow-hover"
                            >
                                <span>Start Free Trial</span>
                                <ArrowRightIcon className="w-5 h-5" />
                            </Link>
                            <Link
                                to="/login"
                                className="btn-secondary text-lg px-8 py-4"
                            >
                                View Demo
                            </Link>
                        </div>

                        {/* Stats */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto">
                            {stats.map((stat, index) => (
                                <div
                                    key={index}
                                    className="card text-center scale-hover"
                                    style={{ animationDelay: `${index * 100}ms` }}
                                >
                                    <div className="text-4xl font-black gradient-text mb-2">{stat.value}</div>
                                    <div className="text-sm text-gray-400 font-medium">{stat.label}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Floating Elements */}
                <div className="absolute top-40 left-10 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl float" />
                <div className="absolute bottom-40 right-10 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl float" style={{ animationDelay: '2s' }} />
            </section>

            {/* Features Section */}
            <section className="relative py-24 px-4 sm:px-6 lg:px-8">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-5xl font-black mb-4">
                            Powerful <span className="gradient-text">Features</span>
                        </h2>
                        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                            Everything you need to build a secure, scalable document search platform
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {features.map((feature, index) => (
                            <div
                                key={index}
                                className="card scale-hover fade-in"
                                style={{ animationDelay: `${index * 100}ms` }}
                            >
                                <div className={`w-14 h-14 bg-gradient-to-br ${feature.color} rounded-xl flex items-center justify-center mb-6 glow`}>
                                    <feature.icon className="w-8 h-8 text-white" />
                                </div>
                                <h3 className="text-2xl font-bold mb-3">{feature.title}</h3>
                                <p className="text-gray-400 leading-relaxed">{feature.description}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Benefits Section */}
            <section className="relative py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-transparent via-indigo-500/5 to-transparent">
                <div className="max-w-7xl mx-auto">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                        <div className="slide-in-left">
                            <h2 className="text-5xl font-black mb-6">
                                Why Choose <span className="gradient-text">CyborgDB</span>?
                            </h2>
                            <p className="text-xl text-gray-400 mb-8 leading-relaxed">
                                Built from the ground up with security and compliance in mind.
                                CyborgDB ensures your sensitive data remains encrypted at all times,
                                even during AI-powered search operations.
                            </p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                {benefits.map((benefit, index) => (
                                    <div
                                        key={index}
                                        className="flex items-center space-x-3 fade-in"
                                        style={{ animationDelay: `${index * 50}ms` }}
                                    >
                                        <CheckCircleIcon className="w-6 h-6 text-green-400 flex-shrink-0" />
                                        <span className="text-gray-300">{benefit}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="slide-in-right">
                            <div className="relative">
                                <div className="card p-8 glow-lg">
                                    <div className="flex items-center space-x-3 mb-6">
                                        <LockClosedIcon className="w-8 h-8 text-indigo-400" />
                                        <h3 className="text-2xl font-bold">Security First</h3>
                                    </div>
                                    <div className="space-y-4">
                                        <div className="flex items-start space-x-3">
                                            <div className="w-2 h-2 bg-indigo-400 rounded-full mt-2" />
                                            <div>
                                                <p className="font-semibold text-gray-200">AES-256 Encryption</p>
                                                <p className="text-sm text-gray-400">Military-grade encryption for all data</p>
                                            </div>
                                        </div>
                                        <div className="flex items-start space-x-3">
                                            <div className="w-2 h-2 bg-purple-400 rounded-full mt-2" />
                                            <div>
                                                <p className="font-semibold text-gray-200">Zero-Knowledge Architecture</p>
                                                <p className="text-sm text-gray-400">We can't access your plaintext data</p>
                                            </div>
                                        </div>
                                        <div className="flex items-start space-x-3">
                                            <div className="w-2 h-2 bg-cyan-400 rounded-full mt-2" />
                                            <div>
                                                <p className="font-semibold text-gray-200">Compliance Ready</p>
                                                <p className="text-sm text-gray-400">GDPR, HIPAA, SOC2 compliant</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div className="absolute -bottom-4 -right-4 w-full h-full bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-2xl -z-10 blur-xl" />
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Architecture Section */}
            <section className="relative py-24 px-4 sm:px-6 lg:px-8">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-5xl font-black mb-4">
                            Modern <span className="gradient-text">Architecture</span>
                        </h2>
                        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                            Built with cutting-edge technologies for maximum performance and security
                        </p>
                    </div>

                    <div className="card p-12 text-center">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                            <div className="space-y-4">
                                <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center mx-auto glow">
                                    <ChartBarIcon className="w-10 h-10 text-white" />
                                </div>
                                <h3 className="text-2xl font-bold">React Frontend</h3>
                                <p className="text-gray-400">Modern, responsive UI with TailwindCSS</p>
                            </div>
                            <div className="space-y-4">
                                <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mx-auto glow">
                                    <ServerIcon className="w-10 h-10 text-white" />
                                </div>
                                <h3 className="text-2xl font-bold">FastAPI Backend</h3>
                                <p className="text-gray-400">High-performance async Python framework</p>
                            </div>
                            <div className="space-y-4">
                                <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl flex items-center justify-center mx-auto glow">
                                    <ShieldCheckIcon className="w-10 h-10 text-white" />
                                </div>
                                <h3 className="text-2xl font-bold">CyborgDB</h3>
                                <p className="text-gray-400">Encrypted vector database for secure search</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="relative py-24 px-4 sm:px-6 lg:px-8">
                <div className="max-w-4xl mx-auto">
                    <div className="card p-12 text-center glow-lg animated-gradient">
                        <h2 className="text-5xl font-black mb-6 text-white">
                            Ready to Get Started?
                        </h2>
                        <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
                            Join enterprises worldwide who trust CyborgDB for their secure document search needs
                        </p>
                        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                            <Link
                                to="/signup"
                                className="bg-white text-indigo-600 px-8 py-4 rounded-lg font-bold text-lg hover:bg-gray-100 transition-all transform hover:scale-105 shadow-xl"
                            >
                                Start Free Trial
                            </Link>
                            <Link
                                to="/login"
                                className="bg-white/10 backdrop-blur-sm text-white px-8 py-4 rounded-lg font-bold text-lg hover:bg-white/20 transition-all border border-white/20"
                            >
                                Sign In
                            </Link>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="relative py-12 px-4 sm:px-6 lg:px-8 border-t border-gray-800">
                <div className="max-w-7xl mx-auto">
                    <div className="flex flex-col md:flex-row justify-between items-center">
                        <div className="flex items-center space-x-3 mb-4 md:mb-0">
                            <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                                <ShieldCheckIcon className="w-5 h-5 text-white" />
                            </div>
                            <span className="text-xl font-bold gradient-text">CyborgDB</span>
                        </div>
                        <p className="text-gray-400 text-sm">
                            © 2025 CyborgDB. Built with ❤️ for secure enterprise search.
                        </p>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default Landing;
