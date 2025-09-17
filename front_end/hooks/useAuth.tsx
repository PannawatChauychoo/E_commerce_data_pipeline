'use client'

import { useState, useEffect } from 'react'

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)

  useEffect(() => {
    // Check if user is already authenticated
    const authStatus = sessionStorage.getItem('portfolio_authenticated')
    setIsAuthenticated(authStatus === 'true')
  }, [])

  const authenticate = () => {
    sessionStorage.setItem('portfolio_authenticated', 'true')
    setIsAuthenticated(true)
  }

  const logout = () => {
    sessionStorage.removeItem('portfolio_authenticated')
    setIsAuthenticated(false)
  }

  return {
    isAuthenticated,
    authenticate,
    logout,
    isLoading: isAuthenticated === null
  }
}