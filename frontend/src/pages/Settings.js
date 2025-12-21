import React from 'react';

function Settings() {
    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="bg-white shadow rounded-lg p-6">
                    <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

                    <div className="space-y-6">
                        {/* Account Settings */}
                        <div>
                            <h2 className="text-lg font-medium text-gray-900 mb-4">Account Settings</h2>
                            <div className="bg-gray-50 p-4 rounded-md">
                                <p className="text-sm text-gray-600">
                                    Account settings and preferences will be available here.
                                </p>
                            </div>
                        </div>

                        {/* Tenant Settings */}
                        <div>
                            <h2 className="text-lg font-medium text-gray-900 mb-4">Tenant Settings</h2>
                            <div className="bg-gray-50 p-4 rounded-md">
                                <p className="text-sm text-gray-600">
                                    Tenant configuration and management options will be available here.
                                </p>
                            </div>
                        </div>

                        {/* API Configuration */}
                        <div>
                            <h2 className="text-lg font-medium text-gray-900 mb-4">API Configuration</h2>
                            <div className="bg-gray-50 p-4 rounded-md">
                                <p className="text-sm text-gray-600">
                                    CyborgDB API settings and credentials will be managed here.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Settings;
