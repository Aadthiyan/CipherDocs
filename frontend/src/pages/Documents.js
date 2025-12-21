import React, { useState, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { format } from 'date-fns';
import { toast } from 'react-hot-toast';
import {
    TrashIcon,
    ArrowPathIcon,
    DocumentIcon,
    CloudArrowUpIcon,
    ExclamationCircleIcon,
    ShieldCheckIcon,
    CheckCircleIcon,
    ClockIcon,
    XCircleIcon,
    ArrowLeftIcon
} from '@heroicons/react/24/outline';
import api from '../api/client';
import { useNavigate } from 'react-router-dom';

const Documents = () => {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const navigate = useNavigate();

    // Fetch documents
    const fetchDocuments = useCallback(async () => {
        try {
            const response = await api.get('/api/v1/documents');
            if (response.data && Array.isArray(response.data.documents)) {
                setDocuments(response.data.documents);
            }
        } catch (error) {
            console.error('Failed to fetch documents', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchDocuments();
        // Poll for updates every 3 seconds to show real-time processing status
        const interval = setInterval(fetchDocuments, 3000);
        return () => clearInterval(interval);
    }, [fetchDocuments]);

    // Handle Upload
    const onDrop = useCallback(async (acceptedFiles) => {
        const file = acceptedFiles[0];
        if (!file) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            await api.post('/api/v1/documents/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            toast.success(`Started processing ${file.name}`);
            fetchDocuments();
        } catch (error) {
            console.error(error);
            const msg = error.response?.data?.detail || 'Upload failed';
            toast.error(msg);
        } finally {
            setUploading(false);
        }
    }, [fetchDocuments]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'text/plain': ['.txt'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
        },
        maxSize: 50 * 1024 * 1024, // 50MB
        multiple: false
    });

    // Handle Delete
    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure you want to delete this document?")) return;
        try {
            await api.delete(`/api/v1/documents/${id}`);
            toast.success("Document deleted");
            fetchDocuments();
        } catch (error) {
            toast.error("Failed to delete document");
        }
    };

    // Helper for status badge
    const getStatusBadge = (status) => {
        switch (status) {
            case 'completed':
                return (
                    <span className="flex items-center space-x-1 px-3 py-1 bg-green-500/20 text-green-400 border border-green-500/30 rounded-lg text-xs font-semibold">
                        <CheckCircleIcon className="w-4 h-4" />
                        <span>Completed</span>
                    </span>
                );
            case 'processing':
                return (
                    <span className="flex items-center space-x-1 px-3 py-1 bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 rounded-lg text-xs font-semibold animate-pulse">
                        <ClockIcon className="w-4 h-4" />
                        <span>Processing</span>
                    </span>
                );
            case 'failed':
                return (
                    <span className="flex items-center space-x-1 px-3 py-1 bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg text-xs font-semibold">
                        <XCircleIcon className="w-4 h-4" />
                        <span>Failed</span>
                    </span>
                );
            case 'uploaded':
                return (
                    <span className="flex items-center space-x-1 px-3 py-1 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-lg text-xs font-semibold">
                        <CloudArrowUpIcon className="w-4 h-4" />
                        <span>Uploaded</span>
                    </span>
                );
            default:
                return (
                    <span className="px-3 py-1 bg-gray-500/20 text-gray-400 border border-gray-500/30 rounded-lg text-xs font-semibold">
                        {status}
                    </span>
                );
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-[#0a0e1a] via-[#111827] to-[#0a0e1a]">
            {/* Background Effects */}
            <div className="fixed inset-0 bg-grid opacity-10 pointer-events-none" />
            <div className="fixed top-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
            <div className="fixed bottom-0 left-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />

            {/* Content */}
            <div className="relative max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="mb-8 fade-in">
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="inline-flex items-center space-x-2 text-gray-400 hover:text-white transition-colors mb-4"
                    >
                        <ArrowLeftIcon className="w-5 h-5" />
                        <span>Back to Dashboard</span>
                    </button>

                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-4xl font-black text-white mb-2">
                                Document Manager
                            </h2>
                            <p className="text-xl text-gray-400">
                                Upload and manage your encrypted knowledge base
                            </p>
                        </div>
                        <button
                            onClick={fetchDocuments}
                            className="btn-secondary flex items-center space-x-2"
                        >
                            <ArrowPathIcon className="h-5 w-5" />
                            <span>Refresh</span>
                        </button>
                    </div>
                </div>

                {/* Upload Zone */}
                <div className="mb-8 slide-in-left">
                    <div
                        {...getRootProps()}
                        className={`card p-12 text-center cursor-pointer transition-all border-2 border-dashed ${isDragActive
                                ? 'border-indigo-500 bg-indigo-500/10 scale-105'
                                : 'border-gray-700 hover:border-indigo-500/50'
                            }`}
                    >
                        <input {...getInputProps()} />
                        {uploading ? (
                            <div className="flex flex-col items-center py-8">
                                <div className="spinner mb-4"></div>
                                <p className="text-lg text-gray-300 font-semibold">Securely encrypting & uploading...</p>
                                <p className="text-sm text-gray-500 mt-2">Your document is being processed</p>
                            </div>
                        ) : (
                            <>
                                <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6 glow">
                                    <CloudArrowUpIcon className="w-12 h-12 text-white" />
                                </div>
                                <h3 className="text-2xl font-bold text-white mb-2">
                                    {isDragActive ? 'Drop your file here' : 'Upload Document'}
                                </h3>
                                <p className="text-gray-400 mb-4">
                                    Drag and drop or click to browse
                                </p>
                                <div className="flex items-center justify-center space-x-4 text-sm text-gray-500">
                                    <span className="flex items-center space-x-1">
                                        <DocumentIcon className="w-4 h-4" />
                                        <span>PDF, DOCX, TXT</span>
                                    </span>
                                    <span>•</span>
                                    <span>Up to 50MB</span>
                                </div>
                            </>
                        )}
                    </div>
                </div>

                {/* Security Notice */}
                <div className="card p-6 mb-8 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border-indigo-500/20 slide-in-right">
                    <div className="flex items-start space-x-4">
                        <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center flex-shrink-0">
                            <ShieldCheckIcon className="w-7 h-7 text-white" />
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-white mb-2">End-to-End Encryption</h3>
                            <p className="text-gray-300">
                                All uploaded documents are automatically encrypted with AES-256 encryption before storage.
                                Your data remains secure at rest and during AI-powered search operations.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Document List */}
                <div className="glass-strong rounded-2xl overflow-hidden fade-in">
                    <div className="px-6 py-4 border-b border-gray-700 flex justify-between items-center">
                        <h3 className="text-2xl font-bold text-white">Your Documents</h3>
                        <span className="text-sm text-gray-400">
                            {documents.length} {documents.length === 1 ? 'document' : 'documents'}
                        </span>
                    </div>

                    <div className="divide-y divide-gray-800">
                        {loading && documents.length === 0 ? (
                            <div className="px-6 py-12 text-center">
                                <div className="spinner mx-auto mb-4"></div>
                                <p className="text-gray-400">Loading documents...</p>
                            </div>
                        ) : documents.length === 0 ? (
                            <div className="px-6 py-16 text-center">
                                <div className="w-16 h-16 bg-gray-800 rounded-2xl flex items-center justify-center mx-auto mb-4">
                                    <DocumentIcon className="w-10 h-10 text-gray-600" />
                                </div>
                                <h3 className="text-xl font-bold text-white mb-2">No documents yet</h3>
                                <p className="text-gray-400">Upload your first document to get started</p>
                            </div>
                        ) : (
                            documents.map((doc) => (
                                <div
                                    key={doc.id}
                                    className="px-6 py-5 hover:bg-white/5 transition-all group"
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center space-x-4 flex-1 min-w-0">
                                            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center flex-shrink-0">
                                                <DocumentIcon className="w-7 h-7 text-white" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <h4 className="text-lg font-bold text-white truncate group-hover:text-indigo-400 transition-colors">
                                                    {doc.filename}
                                                </h4>
                                                <div className="flex items-center space-x-3 text-sm text-gray-500 mt-1">
                                                    <span>{(doc.file_size_bytes / 1024).toFixed(1)} KB</span>
                                                    <span>•</span>
                                                    <span>{format(new Date(doc.uploaded_at), 'MMM d, yyyy h:mm a')}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center space-x-4 ml-4">
                                            {getStatusBadge(doc.status)}
                                            <button
                                                onClick={() => handleDelete(doc.id)}
                                                className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-all"
                                                title="Delete Document"
                                            >
                                                <TrashIcon className="h-5 w-5" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Documents;
