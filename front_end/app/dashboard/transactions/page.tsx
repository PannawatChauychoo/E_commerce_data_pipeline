"use client";

export default function MLAnalyticsPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <div className="text-center space-y-6">
        <div className="space-y-2">
          <h1 className="text-6xl font-bold text-gray-800 dark:text-gray-200">
            ML Analytics
          </h1>
          <div className="text-4xl font-semibold text-gray-600 dark:text-gray-400">
            Coming Soon
          </div>
        </div>

        <div className="max-w-2xl space-y-4">
          <p className="text-lg text-gray-600 dark:text-gray-400 leading-relaxed">
            Advanced machine learning analytics and insights are being developed to provide
            deeper understanding of customer behavior, predictive modeling, and automated
            pattern recognition from your simulation data.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
            <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
              <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">
                Predictive Models
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Customer lifetime value and purchase prediction algorithms
              </p>
            </div>

            <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
              <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">
                Pattern Recognition
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Automated anomaly detection and trend identification
              </p>
            </div>

            <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
              <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">
                Smart Insights
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                AI-powered recommendations and optimization suggestions
              </p>
            </div>
          </div>
        </div>

        <div className="mt-8">
          <div className="inline-flex items-center px-4 py-2 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm font-medium">
            <svg className="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            In Development
          </div>
        </div>
      </div>
    </div>
  );
}