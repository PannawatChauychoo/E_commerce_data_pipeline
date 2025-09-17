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
  const [data, setData] = useState<{
    transactions: any[];
    cust1: any[];
    cust2: any[];
    products: any[];
  }>({
    transactions: [],
    cust1: [],
    cust2: [],
    products: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Define fetchAllData outside useEffect so it can be used in return
  const fetchAllData = async () => {
    try {
      setLoading(true);
      const [transactions, cust1, cust2, products] = await Promise.all([
        simulationAPI.getTransactions(),
        simulationAPI.getCust1Data(),
        simulationAPI.getCust2Data(),
        simulationAPI.getProducts(),
      ]) as [any[], any[], any[], any[]];

      setData({
        transactions,
        cust1,
        cust2,
        products,
      });
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch simulation data');
      console.error('Failed to fetch simulation data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch all initial data
  useEffect(() => {
    fetchAllData();
  }, []);

  return { data, loading, error, refetch: fetchAllData };
}

// Custom hook specifically for running simulations
export function useRunSimulation() {
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const runSimulation = async (parameters: any) => {
    try {
      setIsRunning(true);
      setError(null);
      
      const simulationResult = await simulationAPI.runSimulation(parameters);
      setResult(simulationResult);
      
      return simulationResult;
    } catch (err: any) {
      setError(err?.message || 'Simulation failed');
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
