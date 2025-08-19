const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`API request failed for ${endpoint}:`, error);
    throw error;
  }
}

export const simulationAPI = {
  // GET /api/transactions/ - Fetch all transactions
  getTransactions: () => apiRequest('/transactions/'),
  
  // POST /api/simulate/ - Run simulation with parameters
  runSimulation: (simulationParams) => apiRequest('/simulate/', {
    method: 'POST',
    body: JSON.stringify(simulationParams),
  }),
  
  // GET /api/cust1/ - Fetch customer type 1 data
  getCust1Data: () => apiRequest('/cust1/'),
  
  // GET /api/cust2/ - Fetch customer type 2 data
  getCust2Data: () => apiRequest('/cust2/'),
  
  // GET /api/products/ - Fetch product data
  getProducts: () => apiRequest('/products/'),
};
