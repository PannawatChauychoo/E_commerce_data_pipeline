// hooks.js
import { useState, useEffect } from 'react';
import { simulationAPI } from '../lib/api';

/*
Why important?
- State management
- Provides predictable behavior across components
- Benefit: Reusable logic, cleaner components
*/

// Custom hook for fetching and managing simulation data
export function useSimulationData() {
  const [data, setData] = useState({
    transactions: [],
    cust1: [],
    cust2: [],
    products: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch all initial data
  useEffect(() => {
    async function fetchAllData() {
      try {
        setLoading(true);
        const [transactions, cust1, cust2, products] = await Promise.all([
          simulationAPI.getTransactions(),
          simulationAPI.getCust1Data(),
          simulationAPI.getCust2Data(),
          simulationAPI.getProducts(),
        ]);

        setData({
          transactions,
          cust1,
          cust2,
          products,
        });
      } catch (err) {
        setError(err.message);
        console.error('Failed to fetch simulation data:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchAllData();
  }, []);

  return { data, loading, error, refetch: () => fetchAllData() };
}

// Custom hook specifically for running simulations
export function useRunSimulation() {
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const runSimulation = async (parameters) => {
    try {
      setIsRunning(true);
      setError(null);
      
      const simulationResult = await simulationAPI.runSimulation(parameters);
      setResult(simulationResult);
      
      return simulationResult;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsRunning(false);
    }
  };

  const resetSimulation = () => {
    setResult(null);
    setError(null);
  };

  return {
    runSimulation,
    resetSimulation,
    isRunning,
    result,
    error,
  };
}
